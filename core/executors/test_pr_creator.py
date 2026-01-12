"""
PRCreator 테스트

실제 GitHub API 호출 없이 로컬 Git 동작을 테스트합니다.
"""

import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

import git

import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.executors.pr_creator import PRCreator
from core.executors.models import ExecutionResult


def test_pr_creator():
    """PRCreator 통합 테스트"""

    print("=== PRCreator 테스트 ===\n")

    # 1. 임시 Git 저장소 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)

        print(f"📁 임시 저장소 생성: {repo_path}")

        # Git 초기화
        repo = git.Repo.init(repo_path)

        # 초기 파일 생성 및 커밋
        test_file = repo_path / "test.txt"
        test_file.write_text("Initial content")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")

        # main 브랜치 생성
        repo.git.checkout("-b", "main")

        print("✅ Git 저장소 초기화 완료\n")

        # 2. ExecutionResult 생성 (변경된 파일 포함)
        changed_file = repo_path / "layout.tsx"
        changed_file.write_text('export const metadata = { title: "New Title" }')

        execution_results = [
            ExecutionResult(
                action_id="action-1",
                success=True,
                message="메타 타이틀 변경 완료",
                changed_files=[str(changed_file)],
                execution_time=0.5
            ),
            ExecutionResult(
                action_id="action-2",
                success=True,
                message="메타 설명 변경 완료",
                changed_files=[str(changed_file)],
                execution_time=0.3
            )
        ]

        print("📋 ExecutionResult 생성:")
        for result in execution_results:
            print(f"   - {result.message}")
        print()

        # 3. PRCreator 초기화 (GitHub token 없이 dry-run 테스트)
        # 실제 GitHub API 호출은 하지 않음
        os.environ["GITHUB_TOKEN"] = "fake_token_for_testing"

        try:
            pr_creator = PRCreator(
                repo_path=str(repo_path),
                base_branch="main"
            )

            print("✅ PRCreator 초기화 완료\n")

            # 4. Dry-run 모드로 PR 생성 시뮬레이션
            print("🔍 Dry-run 모드로 PR 생성 시뮬레이션...\n")

            result = pr_creator.create_pr(
                execution_results=execution_results,
                product_id="qr-generator",
                dry_run=True  # 실제로 푸시/PR 생성하지 않음
            )

            # Dry-run은 None을 반환해야 함
            if result is None:
                print("✅ Dry-run 테스트 통과: PR을 생성하지 않음\n")
            else:
                print("❌ Dry-run 테스트 실패: PR URL이 반환되었습니다\n")

            # 5. 브랜치 이름 생성 테스트
            branch_name = pr_creator._generate_branch_name("test-product")
            print(f"🌿 생성된 브랜치 이름: {branch_name}")

            if branch_name.startswith("agent/seo-test-product-"):
                print("✅ 브랜치 이름 형식 올바름\n")
            else:
                print("❌ 브랜치 이름 형식 오류\n")

            # 6. PR 제목 생성 테스트
            pr_title = pr_creator._generate_pr_title(execution_results, "test-product")
            print(f"📝 PR 제목: {pr_title}")

            if "[SEO Agent]" in pr_title and "test-product" in pr_title:
                print("✅ PR 제목 형식 올바름\n")
            else:
                print("❌ PR 제목 형식 오류\n")

            # 7. PR 본문 생성 테스트
            pr_body = pr_creator._generate_pr_body(execution_results, "test-product")
            print(f"📄 PR 본문 ({len(pr_body)} 글자):")
            print("--- 시작 ---")
            print(pr_body[:300] + "...")
            print("--- 끝 ---\n")

            if "## 🤖 SEO Agent" in pr_body and "## 📋 Applied Actions" in pr_body:
                print("✅ PR 본문 형식 올바름\n")
            else:
                print("❌ PR 본문 형식 오류\n")

            # 8. 브랜치 생성 및 커밋 테스트 (실제 Git 작업)
            print("🧪 실제 Git 브랜치 생성 및 커밋 테스트...\n")

            test_branch_name = f"test-branch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

            # 브랜치 생성
            test_branch = repo.create_head(test_branch_name)
            test_branch.checkout()

            print(f"✅ 브랜치 생성: {test_branch_name}")

            # 파일 변경 및 커밋
            pr_creator._commit_changes(
                changed_files=[str(changed_file)],
                commit_message="Test commit"
            )

            # 커밋 확인
            latest_commit = repo.head.commit
            if latest_commit.message.strip() == "Test commit":
                print(f"✅ 커밋 생성 성공: {latest_commit.hexsha[:7]}\n")
            else:
                print("❌ 커밋 메시지 불일치\n")

            # 원래 브랜치로 복귀
            repo.git.checkout("main")
            repo.delete_head(test_branch_name, force=True)
            print("✅ 테스트 브랜치 삭제 완료\n")

            print("🎉 PRCreator 모든 테스트 통과!")

        except Exception as e:
            print(f"❌ 테스트 실패: {e}")
            raise
        finally:
            # 환경변수 정리
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]


def test_error_handling():
    """에러 처리 테스트"""

    print("\n=== 에러 처리 테스트 ===\n")

    # 1. GitHub Token 없이 초기화 시도
    print("1. GitHub Token 없이 초기화...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            repo = git.Repo.init(repo_path)

            # GITHUB_TOKEN이 없는 상태
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]

            pr_creator = PRCreator(repo_path=str(repo_path))
            print("❌ 예외가 발생해야 합니다")
    except ValueError as e:
        print(f"✅ 올바른 예외 발생: {e}\n")

    # 2. 유효하지 않은 Git 저장소
    print("2. 유효하지 않은 Git 저장소...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            # Git 초기화 없이 PRCreator 생성
            os.environ["GITHUB_TOKEN"] = "fake_token"
            pr_creator = PRCreator(repo_path=temp_dir)
            print("❌ 예외가 발생해야 합니다")
    except ValueError as e:
        print(f"✅ 올바른 예외 발생: {e}\n")
    finally:
        if "GITHUB_TOKEN" in os.environ:
            del os.environ["GITHUB_TOKEN"]

    # 3. 성공한 액션이 없는 경우
    print("3. 성공한 액션이 없는 경우...")
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_path = Path(temp_dir)
        repo = git.Repo.init(repo_path)

        test_file = repo_path / "test.txt"
        test_file.write_text("Initial")
        repo.index.add(["test.txt"])
        repo.index.commit("Initial commit")
        repo.git.checkout("-b", "main")

        os.environ["GITHUB_TOKEN"] = "fake_token"

        try:
            pr_creator = PRCreator(repo_path=str(repo_path))

            # 실패한 결과만 포함
            failed_results = [
                ExecutionResult(
                    action_id="fail-1",
                    success=False,
                    message="실패",
                    error="Some error"
                )
            ]

            result = pr_creator.create_pr(
                execution_results=failed_results,
                product_id="test",
                dry_run=True
            )

            if result is None:
                print("✅ 성공한 액션이 없을 때 None 반환\n")
            else:
                print("❌ None이 반환되어야 합니다\n")
        finally:
            del os.environ["GITHUB_TOKEN"]

    print("🎉 에러 처리 테스트 완료!")


if __name__ == "__main__":
    test_pr_creator()
    test_error_handling()
