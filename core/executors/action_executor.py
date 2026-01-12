"""
ActionExecutor Base Class

모든 액션 실행자의 추상 base class입니다.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from .models import Action, ExecutionResult
from .file_backup import FileBackupManager


class ActionExecutor(ABC):
    """
    액션 실행자의 추상 base class

    모든 구체적인 실행자(MetaUpdater, LinkInjector 등)는 이 클래스를 상속받아야 합니다.
    """

    def __init__(self, workspace_root: str = "."):
        """
        Args:
            workspace_root: 작업 루트 디렉토리
        """
        self.workspace_root = Path(workspace_root)
        self.backup_manager = FileBackupManager()

    @abstractmethod
    def execute(self, action: Action) -> ExecutionResult:
        """
        액션을 실행합니다.

        Args:
            action: 실행할 액션

        Returns:
            실행 결과

        Raises:
            NotImplementedError: 하위 클래스에서 반드시 구현해야 함
        """
        pass

    def _resolve_file_path(self, product_id: str, relative_path: str) -> Path:
        """
        프로덕트 ID와 상대 경로를 절대 경로로 변환합니다.

        Args:
            product_id: 프로덕트 ID (예: "qr-generator")
            relative_path: 상대 경로 (예: "src/app/layout.tsx")

        Returns:
            절대 경로
        """
        # workspace_root 디렉토리에서 프로덕트 찾기
        # 만약 workspace_root가 unified-agent라면, 부모 디렉토리에서 찾기
        workspace_name = self.workspace_root.name

        if workspace_name in ["unified-agent", ".", ""]:
            # unified-agent면 부모에서 프로덕트 찾기
            product_root = self.workspace_root.parent / product_id
        else:
            # 테스트 환경 등: workspace_root 자체에서 프로덕트 찾기
            product_root = self.workspace_root / product_id

        file_path = product_root / relative_path
        return file_path
