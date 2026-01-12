"""
Level 2 Agent Data Models

Action과 ExecutionResult 데이터 클래스를 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime


@dataclass
class Action:
    """
    리포트에서 추출된 액션을 나타내는 데이터 클래스

    Attributes:
        id: 액션 고유 ID (예: "action-1")
        priority: 우선순위 ("high", "medium", "low")
        description: 액션 설명 (예: "QR Generator 메타 타이틀 변경")
        product_id: 대상 프로덕트 ID (예: "qr-generator", "convert-image")
        action_type: 액션 타입 (예: "update_meta_title", "add_internal_link")
        target_file: 대상 파일 경로 (선택사항)
        parameters: 액션 실행에 필요한 파라미터 (예: {"new_title": "..."})
        expected_impact: 예상 효과 (선택사항)
        is_automatable: 자동화 가능 여부
        automation_reason: 자동화 가능/불가능 이유 (선택사항)
    """

    id: str
    priority: str
    description: str
    product_id: str
    action_type: str
    target_file: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_impact: Optional[str] = None
    is_automatable: bool = True
    automation_reason: Optional[str] = None

    def __post_init__(self):
        """유효성 검증"""
        valid_priorities = ["high", "medium", "low"]
        if self.priority.lower() not in valid_priorities:
            raise ValueError(f"Invalid priority: {self.priority}. Must be one of {valid_priorities}")

        valid_action_types = [
            "update_meta_title",
            "update_meta_description",
            "add_internal_link",
            "update_canonical_url",
            "update_og_tags"
        ]
        if self.action_type not in valid_action_types:
            raise ValueError(f"Invalid action_type: {self.action_type}. Must be one of {valid_action_types}")


@dataclass
class ExecutionResult:
    """
    액션 실행 결과를 나타내는 데이터 클래스

    Attributes:
        action_id: 실행된 액션 ID
        success: 성공 여부
        message: 실행 결과 메시지
        changed_files: 변경된 파일 목록
        backup_path: 백업 파일 경로 (선택사항)
        error: 에러 정보 (실패 시)
        execution_time: 실행 시간 (초)
        timestamp: 실행 시각
    """

    action_id: str
    success: bool
    message: str
    changed_files: list[str] = field(default_factory=list)
    backup_path: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        """문자열 표현"""
        status = "✅ SUCCESS" if self.success else "❌ FAILED"
        return f"{status} | Action: {self.action_id} | {self.message}"
