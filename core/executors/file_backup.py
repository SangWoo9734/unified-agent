"""
FileBackupManager

파일 변경 전 자동 백업 및 롤백 기능을 제공합니다.
"""

import os
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from contextlib import contextmanager


class FileBackupManager:
    """
    파일 백업 및 롤백을 관리하는 클래스

    Usage:
        # 기본 사용
        backup_manager = FileBackupManager()
        backup_path = backup_manager.backup("src/app/layout.tsx")
        # ... 파일 변경 ...
        # 실패 시: backup_manager.restore(backup_path)

        # Context Manager 사용 (권장)
        with backup_manager.backup_context("src/app/layout.tsx") as backup_path:
            # 파일 변경 작업
            # 에러 발생 시 자동 롤백
            pass
    """

    def __init__(self, backup_dir: str = ".agent_backups"):
        """
        Args:
            backup_dir: 백업 파일을 저장할 디렉토리 (기본: .agent_backups)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True, parents=True)

    def backup(self, file_path: str) -> str:
        """
        파일을 백업합니다.

        Args:
            file_path: 백업할 파일 경로

        Returns:
            백업 파일 경로

        Raises:
            FileNotFoundError: 파일이 존재하지 않을 때
        """
        source = Path(file_path)

        if not source.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 백업 파일명: {timestamp}_{original_filename}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"{timestamp}_{source.name}"
        backup_path = self.backup_dir / backup_filename

        # 파일 복사
        shutil.copy2(source, backup_path)

        # 원본 파일 경로를 메타데이터로 저장 (복원용)
        meta_path = backup_path.with_suffix(backup_path.suffix + ".meta")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(str(source.absolute()))

        return str(backup_path)

    def restore(self, backup_path: str, target_path: Optional[str] = None) -> str:
        """
        백업 파일에서 복원합니다.

        Args:
            backup_path: 백업 파일 경로
            target_path: 복원할 대상 경로 (None이면 메타데이터에서 읽음)

        Returns:
            복원된 파일 경로

        Raises:
            FileNotFoundError: 백업 파일이 존재하지 않을 때
        """
        backup = Path(backup_path)

        if not backup.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_path}")

        # 대상 경로 결정
        if target_path is None:
            meta_path = backup.with_suffix(backup.suffix + ".meta")
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    target_path = f.read().strip()
            else:
                raise ValueError("No target path specified and no metadata found")

        target = Path(target_path)

        # 부모 디렉토리 생성
        target.parent.mkdir(exist_ok=True, parents=True)

        # 파일 복원
        shutil.copy2(backup, target)

        return str(target)

    @contextmanager
    def backup_context(self, file_path: str):
        """
        Context Manager로 자동 백업 및 롤백을 지원합니다.

        Args:
            file_path: 백업할 파일 경로

        Yields:
            백업 파일 경로

        Example:
            with backup_manager.backup_context("src/app/layout.tsx") as backup:
                # 파일 변경 작업
                modify_file("src/app/layout.tsx")
                # 에러 발생 시 자동으로 백업에서 복원됨
        """
        backup_path = self.backup(file_path)

        try:
            yield backup_path
        except Exception as e:
            # 에러 발생 시 자동 롤백
            self.restore(backup_path)
            raise  # 에러를 다시 발생시켜 상위에서 처리하도록

    def cleanup_old_backups(self, days: int = 7) -> int:
        """
        오래된 백업 파일을 삭제합니다.

        Args:
            days: 보관할 일수 (기본: 7일)

        Returns:
            삭제된 파일 수
        """
        if not self.backup_dir.exists():
            return 0

        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for backup_file in self.backup_dir.iterdir():
            if backup_file.is_file() and backup_file.stat().st_mtime < cutoff_time:
                backup_file.unlink()
                deleted_count += 1

                # .meta 파일도 삭제
                meta_file = backup_file.with_suffix(backup_file.suffix + ".meta")
                if meta_file.exists():
                    meta_file.unlink()

        return deleted_count

    def list_backups(self) -> list[dict]:
        """
        백업 파일 목록을 반환합니다.

        Returns:
            백업 파일 정보 리스트 [{"path": str, "original": str, "created_at": str}, ...]
        """
        backups = []

        if not self.backup_dir.exists():
            return backups

        for backup_file in self.backup_dir.iterdir():
            if backup_file.suffix == ".meta":
                continue

            meta_file = backup_file.with_suffix(backup_file.suffix + ".meta")
            original_path = "Unknown"

            if meta_file.exists():
                with open(meta_file, "r", encoding="utf-8") as f:
                    original_path = f.read().strip()

            created_at = datetime.fromtimestamp(backup_file.stat().st_mtime)

            backups.append({
                "path": str(backup_file),
                "original": original_path,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # 최신순 정렬
        backups.sort(key=lambda x: x["created_at"], reverse=True)

        return backups
