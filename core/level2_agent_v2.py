"""
Level 2 Agent v2.0 - Repository Dispatch 방식

리포트를 분석하고 각 프로덕트에 Dispatch 이벤트를 전송합니다.
프로덕트는 자체 워크플로우로 파일을 수정하고 PR을 생성합니다.
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

from .executors.models import Action
from .executors.action_extractor import ActionExtractor
from .executors.action_validator import ActionValidator
from .dispatchers.repository_dispatcher import RepositoryDispatcher


class Level2AgentV2:
    """
    Level 2 Agent v2.0 - Repository Dispatch 방식

    v1.0과의 차이점:
    - v1.0: unified-agent가 직접 파일 수정 및 PR 생성
    - v2.0: unified-agent는 Dispatch만, 각 프로덕트가 자체 워크플로우 실행
    """

    def __init__(
        self,
        github_owner: str,
        gemini_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        dry_run: bool = False
    ):
        """
        Args:
            github_owner: GitHub 저장소 소유자 (예: "SangWoo9734")
            gemini_api_key: Google Gemini API Key (ActionExtractor fallback용)
            github_token: GitHub Personal Access Token
            dry_run: True면 실제로 Dispatch 전송 안 함
        """
        self.github_owner = github_owner
        self.dry_run = dry_run

        # API Keys
        self.gemini_api_key = gemini_api_key or os.getenv("GOOGLE_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")

        # 컴포넌트 초기화
        self.extractor = ActionExtractor(api_key=self.gemini_api_key)
        self.validator = ActionValidator()
        self.dispatcher = RepositoryDispatcher(github_token=self.github_token)

        print(f"🤖 Level 2 Agent v2.0 초기화 완료 (Powered by Gemini)")
        print(f"   GitHub Owner: {self.github_owner}")
        print(f"   Dry-run: {self.dry_run}")
        print()

    def process_report(self, report_path: str) -> Dict[str, Any]:
        """
        리포트를 처리하여 각 프로덕트에 Dispatch 이벤트를 전송합니다.

        전체 파이프라인:
        1. 리포트 로드
        2. 액션 추출 (ActionExtractor)
        3. 액션 검증 (ActionValidator)
        4. 프로덕트별 그룹화
        5. Dispatch 이벤트 전송 (RepositoryDispatcher)

        Args:
            report_path: 리포트 파일 경로 (Markdown)

        Returns:
            처리 결과 딕셔너리
        """
        print(f"📄 리포트 처리 시작: {report_path}\n")

        try:
            # 1. 액션 추출
            print("🔍 액션 추출 중...")
            actions = self.extractor.extract_from_report(report_path)
            print(f"   추출된 액션: {len(actions)}개\n")

            if not actions:
                return {
                    "success": False,
                    "error": "리포트에서 액션을 추출하지 못했습니다.",
                    "actions_extracted": 0,
                    "actions_safe": 0,
                    "dispatched": {}
                }

            # 2. 액션 검증
            print("🛡️  액션 안전성 검증 중...")
            safe_actions = self.validator.filter_safe_actions(actions)
            print(f"   안전한 액션: {len(safe_actions)}개\n")

            if not safe_actions:
                return {
                    "success": False,
                    "error": "안전한 액션이 없습니다.",
                    "actions_extracted": len(actions),
                    "actions_safe": 0,
                    "dispatched": {}
                }

            # 3. 프로덕트별 그룹화
            print("📦 프로덕트별 그룹화 중...")
            actions_by_product = RepositoryDispatcher.group_actions_by_product(safe_actions)

            for product_id, product_actions in actions_by_product.items():
                print(f"   {product_id}: {len(product_actions)}개 액션")
            print()

            # 4. Dispatch 전송
            if not self.dry_run:
                dispatch_results = self.dispatcher.dispatch_to_products(
                    owner=self.github_owner,
                    actions_by_product=actions_by_product
                )
            else:
                print("🔍 [DRY-RUN] Dispatch 전송 건너뜀\n")
                dispatch_results = {
                    product_id: True
                    for product_id in actions_by_product.keys()
                }

            # 5. 결과 반환
            success_count = sum(1 for v in dispatch_results.values() if v)

            return {
                "success": True,
                "actions_extracted": len(actions),
                "actions_safe": len(safe_actions),
                "products_count": len(actions_by_product),
                "dispatched": dispatch_results,
                "dispatched_success": success_count,
                "error": None
            }

        except Exception as e:
            print(f"❌ 에러 발생: {e}\n")
            return {
                "success": False,
                "error": str(e),
                "actions_extracted": 0,
                "actions_safe": 0,
                "dispatched": {}
            }

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

        total_dispatched = sum(
            r.get("dispatched_success", 0)
            for r in results
        )
        print(f"   총 Dispatch 성공: {total_dispatched}개 프로덕트")

        return results
