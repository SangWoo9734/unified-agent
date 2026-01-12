"""
PRCreator

GitHub PR을 자동으로 생성합니다.
"""

import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

import git
from github import Github, GithubException

from .models import ExecutionResult


class PRCreator:
    """
    GitHub PR을 자동으로 생성하는 클래스

    GitPython으로 브랜치 생성/커밋/푸시하고,
    PyGithub로 PR을 생성합니다.
    """

    def __init__(
        self,
        repo_path: str,
        github_token: Optional[str] = None,
        base_branch: str = "main"
    ):
        """
        Args:
            repo_path: Git 저장소 경로
            github_token: GitHub Personal Access Token (환경변수에서 가져올 수도 있음)
            base_branch: PR의 base 브랜치 (기본: "main")
        """
        self.repo_path = Path(repo_path)
        self.base_branch = base_branch

        # GitHub Token
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN env var or pass github_token parameter.")

        # GitPython Repo
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Not a valid Git repository: {self.repo_path}")

        # PyGithub Client
        self.gh = Github(self.github_token)

        # 현재 remote 이름 (기본: origin)
        self.remote_name = "origin"

    def create_pr(
        self,
        execution_results: List[ExecutionResult],
        product_id: str,
        dry_run: bool = False
    ) -> Optional[str]:
        """
        실행 결과를 바탕으로 GitHub PR을 생성합니다.

        Args:
            execution_results: 실행 완료된 액션 결과 리스트
            product_id: 대상 프로덕트 ID
            dry_run: True면 실제로 푸시/PR 생성하지 않음

        Returns:
            PR URL (dry_run이면 None)
        """
        # 1. 성공한 결과만 필터링
        successful_results = [r for r in execution_results if r.success]

        if not successful_results:
            print("⚠️  성공한 액션이 없어 PR을 생성하지 않습니다.")
            return None

        # 2. 변경된 파일 목록 수집
        changed_files = []
        for result in successful_results:
            changed_files.extend(result.changed_files)

        if not changed_files:
            print("⚠️  변경된 파일이 없어 PR을 생성하지 않습니다.")
            return None

        # 3. Git 브랜치 생성 및 커밋
        branch_name = self._generate_branch_name(product_id)
        pr_title = self._generate_pr_title(successful_results, product_id)
        pr_body = self._generate_pr_body(successful_results, product_id)

        print(f"📝 PR 생성 준비:")
        print(f"   브랜치: {branch_name}")
        print(f"   제목: {pr_title}")
        print(f"   변경된 파일: {len(changed_files)}개")

        if dry_run:
            print("🔍 [DRY-RUN] PR을 생성하지 않고 종료합니다.")
            return None

        # Context Manager로 브랜치 생성/푸시/PR 생성
        with self._git_context(branch_name):
            # 파일 add & commit
            self._commit_changes(changed_files, pr_title)

            # Push to remote
            self._push_branch(branch_name)

            # GitHub PR 생성
            pr_url = self._create_github_pr(branch_name, pr_title, pr_body)

            print(f"✅ PR 생성 완료: {pr_url}")
            return pr_url

    @contextmanager
    def _git_context(self, branch_name: str):
        """
        Git 브랜치를 생성하고, 에러 발생 시 롤백하는 Context Manager

        Args:
            branch_name: 생성할 브랜치 이름
        """
        original_branch = self.repo.active_branch.name
        branch_created = False

        try:
            # 현재 base 브랜치에 있는지 확인
            if self.repo.active_branch.name != self.base_branch:
                print(f"⚠️  현재 브랜치가 {self.base_branch}가 아닙니다. 체크아웃합니다.")
                self.repo.git.checkout(self.base_branch)

            # 최신 상태로 pull
            print(f"🔄 {self.base_branch} 브랜치를 최신 상태로 업데이트 중...")
            self.repo.remotes[self.remote_name].pull()

            # 새 브랜치 생성
            print(f"🌿 브랜치 생성: {branch_name}")
            new_branch = self.repo.create_head(branch_name)
            new_branch.checkout()
            branch_created = True

            yield

        except Exception as e:
            print(f"❌ Git 작업 중 에러 발생: {e}")

            # 롤백: 원래 브랜치로 돌아가고 생성한 브랜치 삭제
            if branch_created:
                print(f"🔄 롤백: {original_branch} 브랜치로 복귀 중...")
                self.repo.git.checkout(original_branch)

                print(f"🗑️  생성한 브랜치 삭제: {branch_name}")
                self.repo.delete_head(branch_name, force=True)

            raise

    def _commit_changes(self, changed_files: List[str], commit_message: str):
        """
        변경된 파일을 커밋합니다.

        Args:
            changed_files: 변경된 파일 경로 리스트
            commit_message: 커밋 메시지
        """
        print(f"📝 파일 추가 중: {len(changed_files)}개")

        # 파일을 상대 경로로 변환 (repo root 기준)
        relative_files = []
        for file_path in changed_files:
            abs_path = Path(file_path).absolute()
            try:
                rel_path = abs_path.relative_to(self.repo_path.absolute())
                relative_files.append(str(rel_path))
            except ValueError:
                # repo 외부 파일은 무시
                print(f"⚠️  저장소 외부 파일 무시: {file_path}")

        # Git add
        self.repo.index.add(relative_files)

        # Git commit
        print(f"💾 커밋 생성: {commit_message[:50]}...")
        self.repo.index.commit(commit_message)

    def _push_branch(self, branch_name: str):
        """
        브랜치를 원격 저장소에 푸시합니다.

        Args:
            branch_name: 푸시할 브랜치 이름
        """
        print(f"🚀 브랜치 푸시 중: {branch_name}")
        remote = self.repo.remotes[self.remote_name]
        remote.push(refspec=f"{branch_name}:{branch_name}")

    def _create_github_pr(self, branch_name: str, title: str, body: str) -> str:
        """
        GitHub PR을 생성합니다.

        Args:
            branch_name: PR의 head 브랜치
            title: PR 제목
            body: PR 본문

        Returns:
            PR URL
        """
        # 저장소 정보 추출 (remote URL에서)
        remote_url = self.repo.remotes[self.remote_name].url

        # SSH 또는 HTTPS URL에서 owner/repo 추출
        # git@github.com:owner/repo.git → owner/repo
        # https://github.com/owner/repo.git → owner/repo
        if "github.com" in remote_url:
            if remote_url.startswith("git@"):
                # SSH: git@github.com:owner/repo.git
                repo_path = remote_url.split(":")[-1].replace(".git", "")
            else:
                # HTTPS: https://github.com/owner/repo.git
                repo_path = "/".join(remote_url.split("/")[-2:]).replace(".git", "")

            owner, repo_name = repo_path.split("/")
        else:
            raise ValueError(f"GitHub URL이 아닙니다: {remote_url}")

        print(f"🔗 GitHub PR 생성 중: {owner}/{repo_name}")

        # PyGithub로 PR 생성
        try:
            gh_repo = self.gh.get_repo(f"{owner}/{repo_name}")
            pr = gh_repo.create_pull(
                title=title,
                body=body,
                head=branch_name,
                base=self.base_branch
            )

            # 라벨 추가 (있으면)
            try:
                pr.add_to_labels("seo", "automated")
            except GithubException:
                print("⚠️  라벨을 추가하지 못했습니다 (라벨이 없을 수 있음)")

            return pr.html_url

        except GithubException as e:
            raise RuntimeError(f"GitHub PR 생성 실패: {e}")

    def _generate_branch_name(self, product_id: str) -> str:
        """
        브랜치 이름을 생성합니다.

        Format: agent/seo-{product_id}-YYYYMMDD-HHMMSS

        Args:
            product_id: 프로덕트 ID

        Returns:
            브랜치 이름
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"agent/seo-{product_id}-{timestamp}"

    def _generate_pr_title(self, results: List[ExecutionResult], product_id: str) -> str:
        """
        PR 제목을 생성합니다.

        Format: [SEO Agent] {product_id}: {N} Improvement(s) - YYYY-MM-DD

        Args:
            results: 실행 결과 리스트
            product_id: 프로덕트 ID

        Returns:
            PR 제목
        """
        count = len(results)
        date_str = datetime.now().strftime("%Y-%m-%d")
        improvement_text = "Improvement" if count == 1 else "Improvements"

        return f"[SEO Agent] {product_id}: {count} {improvement_text} - {date_str}"

    def _generate_pr_body(self, results: List[ExecutionResult], product_id: str) -> str:
        """
        PR 본문을 생성합니다.

        Args:
            results: 실행 결과 리스트
            product_id: 프로덕트 ID

        Returns:
            PR 본문 (Markdown)
        """
        lines = []

        # 헤더
        lines.append(f"## 🤖 SEO Agent - Automated Improvements")
        lines.append("")
        lines.append(f"**Product**: `{product_id}`")
        lines.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # 액션 목록
        lines.append("## 📋 Applied Actions")
        lines.append("")
        for idx, result in enumerate(results, start=1):
            lines.append(f"### {idx}. {result.message}")
            lines.append("")
            if result.changed_files:
                lines.append("**Changed Files:**")
                for file_path in result.changed_files:
                    lines.append(f"- `{file_path}`")
                lines.append("")

        # 테스트 체크리스트
        lines.append("## ✅ Test Checklist")
        lines.append("")
        lines.append("- [ ] 메타 태그가 올바르게 변경되었는지 확인")
        lines.append("- [ ] 페이지가 정상적으로 렌더링되는지 확인")
        lines.append("- [ ] 빌드 오류가 없는지 확인")
        lines.append("- [ ] SEO 점수 개선 효과 확인")
        lines.append("")

        # 푸터
        lines.append("---")
        lines.append("🤖 *This PR was automatically generated by SEO Agent*")

        return "\n".join(lines)
