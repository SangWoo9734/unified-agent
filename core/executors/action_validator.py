"""
ActionValidator

액션의 안전성을 검증합니다.
"""

import re
from typing import Tuple
from .models import Action


class ActionValidator:
    """
    액션이 자동화 가능한지 안전성을 검증하는 클래스

    검증 항목:
    - action_type 화이트리스트
    - target_file 화이트리스트
    - 위험 패턴 감지 (XSS, Code Injection)
    """

    # 안전한 action_type 화이트리스트
    SAFE_ACTION_TYPES = {
        "update_meta_title",
        "update_meta_description",
        "add_internal_link",
        "update_canonical_url",
        "update_og_tags"
    }

    # 안전한 파일 패턴
    SAFE_FILE_PATTERNS = [
        r".*layout\.tsx$",
        r".*index\.html$",
        r".*Header\.tsx$",
        r".*Footer\.tsx$",
        r".*Layout\.tsx$",
        r".*metadata\.ts$",
        r".*head\.tsx$",
    ]

    # 위험 패턴 (XSS, Code Injection)
    DANGEROUS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"eval\s*\(",
        r"innerHTML",
        r"outerHTML",
        r"document\.write",
        r"on\w+\s*=",  # onclick, onload 등
        r"__proto__",
        r"constructor\s*\[",
    ]

    def validate(self, action: Action) -> Tuple[bool, str]:
        """
        액션이 자동화 가능한지 검증합니다.

        Args:
            action: 검증할 액션

        Returns:
            (is_valid, reason) 튜플
            - is_valid: 자동화 가능 여부
            - reason: 가능/불가 이유
        """
        # 1. action_type 화이트리스트 검증
        if action.action_type not in self.SAFE_ACTION_TYPES:
            return False, f"Unsafe action_type: {action.action_type}"

        # 2. target_file 검증
        if action.target_file:
            if not self._is_safe_file(action.target_file):
                return False, f"Unsafe target_file: {action.target_file}"

        # 3. parameters 안전성 검증
        for key, value in action.parameters.items():
            if isinstance(value, str):
                if self._contains_dangerous_pattern(value):
                    return False, f"Dangerous pattern detected in {key}: {value[:50]}..."

        # 4. description 검증 (추가 안전장치)
        if self._contains_dangerous_pattern(action.description):
            return False, f"Dangerous pattern in description"

        # 모든 검증 통과
        return True, "Safe for automation"

    def _is_safe_file(self, file_path: str) -> bool:
        """
        파일 경로가 안전한지 검증합니다.

        Args:
            file_path: 파일 경로

        Returns:
            안전 여부
        """
        # Path Traversal 공격 방지
        if ".." in file_path or file_path.startswith("/"):
            return False

        # 화이트리스트 패턴 매칭
        for pattern in self.SAFE_FILE_PATTERNS:
            if re.match(pattern, file_path, re.IGNORECASE):
                return True

        return False

    def _contains_dangerous_pattern(self, text: str) -> bool:
        """
        텍스트에 위험 패턴이 있는지 검사합니다.

        Args:
            text: 검사할 텍스트

        Returns:
            위험 패턴 포함 여부
        """
        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True

        return False

    def filter_safe_actions(self, actions: list[Action]) -> list[Action]:
        """
        안전한 액션만 필터링합니다.

        Args:
            actions: 액션 리스트

        Returns:
            안전한 액션 리스트
        """
        safe_actions = []

        for action in actions:
            is_valid, reason = self.validate(action)

            if is_valid:
                action.is_automatable = True
                action.automation_reason = reason
                safe_actions.append(action)
            else:
                action.is_automatable = False
                action.automation_reason = reason
                print(f"⚠️  Skipping unsafe action: {action.id} - {reason}")

        return safe_actions
