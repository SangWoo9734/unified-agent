"""
RepositoryDispatcher

각 프로덕트 저장소에 repository_dispatch 이벤트를 전송합니다.
"""

import os
from typing import List, Dict, Any, Optional
from github import Github, GithubException

from ..executors.models import Action


class RepositoryDispatcher:
    """
    GitHub Repository Dispatch 이벤트를 전송하는 클래스

    unified-agent가 리포트를 생성하고 액션을 추출한 후,
    각 프로덕트 저장소에 이벤트를 전송하여 프로덕트가 자체적으로
    파일을 수정하고 PR을 생성하도록 합니다.
    """

    def __init__(self, github_token: Optional[str] = None):
        """
        Args:
            github_token: GitHub Personal Access Token
        """
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GITHUB_TOKEN env var.")

        self.gh = Github(self.github_token)

    def dispatch(
        self,
        owner: str,
        repo_name: str,
        actions: List[Action],
        event_type: str = "seo-improvements"
    ) -> bool:
        """
        프로덕트 저장소에 repository_dispatch 이벤트를 전송합니다.

        Args:
            owner: GitHub 저장소 소유자 (예: "SangWoo9734")
            repo_name: 저장소 이름 (예: "qr-generator")
            actions: 실행할 액션 리스트
            event_type: 이벤트 타입 (기본: "seo-improvements")

        Returns:
            성공 여부 (bool)
        """
        if not actions:
            print(f"⚠️  {repo_name}: 전송할 액션이 없습니다.")
            return False

        print(f"📤 {repo_name}: Repository Dispatch 이벤트 전송 중...")

        try:
            # 저장소 가져오기
            repo = self.gh.get_repo(f"{owner}/{repo_name}")

            # 액션 데이터를 JSON 직렬화 가능한 형태로 변환
            actions_data = [self._serialize_action(action) for action in actions]

            # client_payload 구성
            payload = {
                "actions": actions_data,
                "timestamp": actions[0].id.split("-")[0] if actions else "",  # 타임스탬프 추출
                "source": "unified-agent"
            }

            # repository_dispatch 이벤트 전송
            repo.create_repository_dispatch(
                event_type=event_type,
                client_payload=payload
            )

            print(f"   ✅ {repo_name}: {len(actions)}개 액션 전송 완료")
            return True

        except GithubException as e:
            print(f"   ❌ {repo_name}: Dispatch 실패 - {e}")
            return False

    def dispatch_to_products(
        self,
        owner: str,
        actions_by_product: Dict[str, List[Action]]
    ) -> Dict[str, bool]:
        """
        여러 프로덕트에 일괄 전송합니다.

        Args:
            owner: GitHub 저장소 소유자
            actions_by_product: 프로덕트별 액션 딕셔너리
                예: {
                    "qr-generator": [action1, action2],
                    "convert-image": [action3]
                }

        Returns:
            프로덕트별 성공 여부 딕셔너리
        """
        results = {}

        print(f"\n📤 총 {len(actions_by_product)}개 프로덕트에 Dispatch 전송")
        print("=" * 60)

        for product_id, actions in actions_by_product.items():
            success = self.dispatch(owner, product_id, actions)
            results[product_id] = success

        print("=" * 60)

        # 요약
        success_count = sum(1 for v in results.values() if v)
        print(f"\n✅ Dispatch 완료: {success_count}/{len(results)}")

        return results

    def _serialize_action(self, action: Action) -> Dict[str, Any]:
        """
        Action 객체를 JSON 직렬화 가능한 딕셔너리로 변환합니다.

        Args:
            action: Action 객체

        Returns:
            직렬화된 딕셔너리
        """
        return {
            "id": action.id,
            "priority": action.priority,
            "description": action.description,
            "product_id": action.product_id,
            "action_type": action.action_type,
            "target_file": action.target_file,
            "parameters": action.parameters,
            "expected_impact": action.expected_impact,
            "is_automatable": action.is_automatable,
            "automation_reason": action.automation_reason
        }

    @staticmethod
    def group_actions_by_product(actions: List[Action]) -> Dict[str, List[Action]]:
        """
        액션 리스트를 프로덕트별로 그룹화합니다.

        Args:
            actions: 전체 액션 리스트

        Returns:
            프로덕트별 액션 딕셔너리
        """
        grouped = {}

        for action in actions:
            product_id = action.product_id
            if product_id not in grouped:
                grouped[product_id] = []
            grouped[product_id].append(action)

        return grouped
