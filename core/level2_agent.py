"""
Level 2 Agent

리포트를 자동으로 분석하고 GitHub PR을 생성하는 Agent입니다.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from .executors.models import Action, ExecutionResult
from .executors.action_extractor import ActionExtractor
from .executors.action_validator import ActionValidator
from .executors.meta_updater import MetaUpdater
from .executors.pr_creator import PRCreator


class Level2Agent:
    """
    Level 2 Agent - 자동화 실행 Agent

    리포트를 읽고 → 액션 추출 → 검증 → 실행 → PR 생성까지 전체 파이프라인을 조율합니다.
    """

    def __init__(
        self,
        workspace_root: str = ".",
        gemini_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        base_branch: str = "main",
        dry_run: bool = False
    ):
        """
        Args:
            workspace_root: 작업 루트 디렉토리 (unified-agent 디렉토리)
            gemini_api_key: Google Gemini API Key (ActionExtractor fallback용, 선택사항)
            github_token: GitHub Personal Access Token (PRCreator용)
            base_branch: PR의 base 브랜치 (기본: "main")
            dry_run: True면 실제로 파일 변경/PR 생성하지 않음
        """
        self.workspace_root = Path(workspace_root)
        self.dry_run = dry_run

        # API Keys
        self.gemini_api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

        # 컴포넌트 초기화
        self.extractor = ActionExtractor(api_key=self.gemini_api_key)
        self.validator = ActionValidator()
        self.meta_updater = MetaUpdater(workspace_root=str(self.workspace_root))

        # PRCreator는 실제 사용 시점에 초기화 (프로덕트별로 다름)
        self.base_branch = base_branch

        print(f"🤖 Level 2 Agent 초기화 완료")
        print(f"   Workspace: {self.workspace_root}")
        print(f"   Dry-run: {self.dry_run}")
        print()

    def process_report(self, report_path: str, product_id: Optional[str] = None) -> Dict[str, Any]:
        """
        리포트를 처리하여 자동으로 PR을 생성합니다.

        전체 파이프라인:
        1. 리포트 로드
        2. 액션 추출 (ActionExtractor)
        3. 액션 검증 (ActionValidator)
        4. 액션 실행 (MetaUpdater)
        5. PR 생성 (PRCreator)

        Args:
            report_path: 리포트 파일 경로 (Markdown)
            product_id: 프로덕트 ID (선택, 리포트에서 자동 추출 가능)

        Returns:
            처리 결과 딕셔너리
            {
                "success": bool,
                "product_id": str,
                "actions_extracted": int,
                "actions_safe": int,
                "actions_executed": int,
                "pr_url": Optional[str],
                "execution_results": List[ExecutionResult],
                "error": Optional[str]
            }
        """
        print(f"📄 리포트 처리 시작: {report_path}\n")

        try:
            # 1. 액션 추출 (리포트 로드 + 파싱)
            print("🔍 액션 추출 중...")
            actions = self.extractor.extract_from_report(report_path)
            print(f"   추출된 액션: {len(actions)}개\n")

            if not actions:
                return {
                    "success": False,
                    "error": "리포트에서 액션을 추출하지 못했습니다.",
                    "actions_extracted": 0,
                    "actions_safe": 0,
                    "actions_executed": 0,
                    "pr_url": None,
                    "execution_results": []
                }

            # product_id 자동 감지 (첫 액션에서)
            if not product_id:
                product_id = actions[0].product_id
                print(f"🏷️  Product ID 자동 감지: {product_id}\n")

            # 3. 액션 검증
            print("🛡️  액션 안전성 검증 중...")
            for action in actions:
                is_valid, reason = self.validator.validate(action)
                status = "✅ Safe" if is_valid else "❌ Unsafe"
                print(f"   - {status}: {action.description[:60]}... (Reason: {reason})")
            
            safe_actions = self.validator.filter_safe_actions(actions)
            print(f"   안전한 액션: {len(safe_actions)}개\n")

            if not safe_actions:
                return {
                    "success": False,
                    "product_id": product_id,
                    "error": "안전한 액션이 없습니다.",
                    "actions_extracted": len(actions),
                    "actions_safe": 0,
                    "actions_executed": 0,
                    "pr_url": None,
                    "execution_results": []
                }

            # 4. 액션 실행
            print("⚙️  액션 실행 중...")
            execution_results = self._execute_actions(safe_actions)

            successful_count = sum(1 for r in execution_results if r.success)
            print(f"   실행 완료: {successful_count}/{len(execution_results)}개 성공\n")

            # 실행 결과 출력
            for result in execution_results:
                print(f"   {result}")

            print()

            # 5. PR 생성
            pr_url = None
            if not self.dry_run:
                print("📤 GitHub PR 생성 중...")
                pr_url = self._create_pr(execution_results, product_id)

                if pr_url:
                    print(f"   ✅ PR 생성 완료: {pr_url}\n")
                else:
                    print(f"   ⚠️  PR을 생성하지 못했습니다\n")
            else:
                print("🔍 [DRY-RUN] PR 생성 건너뜀\n")

            return {
                "success": True,
                "product_id": product_id,
                "actions_extracted": len(actions),
                "actions_safe": len(safe_actions),
                "actions_executed": successful_count,
                "pr_url": pr_url,
                "execution_results": execution_results,
                "error": None
            }

        except Exception as e:
            print(f"❌ 에러 발생: {e}\n")
            return {
                "success": False,
                "error": str(e),
                "actions_extracted": 0,
                "actions_safe": 0,
                "actions_executed": 0,
                "pr_url": None,
                "execution_results": []
            }

    def _load_report(self, report_path: str) -> str:
        """
        리포트 파일을 로드합니다.

        Args:
            report_path: 리포트 파일 경로

        Returns:
            리포트 내용

        Raises:
            FileNotFoundError: 파일이 없을 때
        """
        path = Path(report_path)

        if not path.exists():
            raise FileNotFoundError(f"리포트 파일을 찾을 수 없습니다: {report_path}")

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        print(f"✅ 리포트 로드 완료: {path.name} ({len(content)} 글자)\n")
        return content

    def _execute_actions(self, actions: List[Action]) -> List[ExecutionResult]:
        """
        액션 목록을 실행합니다.

        Args:
            actions: 실행할 액션 리스트

        Returns:
            실행 결과 리스트
        """
        results = []

        for idx, action in enumerate(actions, start=1):
            print(f"   [{idx}/{len(actions)}] {action.description}...", end=" ")

            # Dry-run 모드
            if self.dry_run:
                print("🔍 [DRY-RUN]")
                results.append(ExecutionResult(
                    action_id=action.id,
                    success=True,
                    message=f"[DRY-RUN] {action.description}",
                    changed_files=[],
                    execution_time=0.0
                ))
                continue

            # action_type에 따라 적절한 executor 선택
            if action.action_type in ["update_meta_title", "update_meta_description"]:
                executor = self.meta_updater
            else:
                # 아직 구현되지 않은 액션 타입
                print("⚠️  [NOT IMPLEMENTED]")
                results.append(ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message=f"Not implemented: {action.action_type}",
                    error="Not implemented",
                    execution_time=0.0
                ))
                continue

            # 실행
            try:
                result = executor.execute(action)
                results.append(result)

                if result.success:
                    print("✅")
                else:
                    print(f"❌ {result.error}")

            except Exception as e:
                print(f"❌ {e}")
                results.append(ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message=f"실행 중 에러: {str(e)}",
                    error=str(e),
                    execution_time=0.0
                ))

        return results

    def _create_pr(self, execution_results: List[ExecutionResult], product_id: str) -> Optional[str]:
        """
        실행 결과를 바탕으로 GitHub PR을 생성합니다.

        Args:
            execution_results: 실행 결과 리스트
            product_id: 프로덕트 ID

        Returns:
            PR URL (성공 시) 또는 None (실패 시)
        """
        # 프로덕트 디렉토리 찾기
        product_path = self._find_product_path(product_id)

        if not product_path:
            print(f"⚠️  프로덕트 디렉토리를 찾을 수 없습니다: {product_id}")
            return None

        # PRCreator 초기화
        try:
            pr_creator = PRCreator(
                repo_path=str(product_path),
                github_token=self.github_token,
                base_branch=self.base_branch
            )

            # PR 생성
            pr_url = pr_creator.create_pr(
                execution_results=execution_results,
                product_id=product_id,
                dry_run=self.dry_run
            )

            return pr_url

        except Exception as e:
            print(f"❌ PR 생성 중 에러: {e}")
            return None

    def _find_product_path(self, product_id: str) -> Optional[Path]:
        """
        프로덕트 ID로 프로덕트 디렉토리를 찾습니다.

        Args:
            product_id: 프로덕트 ID

        Returns:
            프로덕트 디렉토리 경로 (없으면 None)
        """
        # workspace_root가 unified-agent면 부모에서 찾기
        if self.workspace_root.name in ["unified-agent", ".", ""]:
            product_path = self.workspace_root.parent / product_id
        else:
            product_path = self.workspace_root / product_id

        if product_path.exists() and product_path.is_dir():
            return product_path

        return None

    def process_multiple_reports(self, report_paths: List[str]) -> List[Dict[str, Any]]:
        """
        여러 리포트를 순차적으로 처리합니다.

        Args:
            report_paths: 리포트 파일 경로 리스트

        Returns:
            처리 결과 리스트
        """
        results = []

        print(f"📋 총 {len(report_paths)}개 리포트 처리 시작\n")
        print("=" * 60)
        print()

        for idx, report_path in enumerate(report_paths, start=1):
            print(f"[{idx}/{len(report_paths)}] {report_path}")
            print("-" * 60)

            result = self.process_report(report_path)
            results.append(result)

            print("=" * 60)
            print()

        # 요약 출력
        print("📊 처리 요약:")
        successful = sum(1 for r in results if r["success"])
        print(f"   성공: {successful}/{len(results)}")

        total_actions = sum(r["actions_executed"] for r in results)
        print(f"   총 실행된 액션: {total_actions}개")

        pr_count = sum(1 for r in results if r.get("pr_url"))
        print(f"   생성된 PR: {pr_count}개")

        return results
