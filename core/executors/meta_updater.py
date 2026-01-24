"""
MetaUpdater

TSX 및 HTML 파일의 메타 타이틀/설명을 안전하게 변경합니다.
"""

import time
from pathlib import Path
from typing import Optional
import libcst as cst
from bs4 import BeautifulSoup

from .action_executor import ActionExecutor
from .models import Action, ExecutionResult


class MetadataTransformer(cst.CSTTransformer):
    """
    LibCST를 사용하여 TSX 파일의 metadata 객체를 변경하는 Transformer
    """

    def __init__(self, new_title: Optional[str] = None, new_description: Optional[str] = None):
        """
        Args:
            new_title: 새 메타 타이틀
            new_description: 새 메타 설명
        """
        super().__init__()
        self.new_title = new_title
        self.new_description = new_description
        self.modified = False

    def leave_SimpleStatementLine(
        self, original_node: cst.SimpleStatementLine, updated_node: cst.SimpleStatementLine
    ) -> cst.SimpleStatementLine:
        """
        export const metadata 구문을 찾아 수정합니다.
        """
        # 단일 statement인 경우만 처리
        if len(updated_node.body) != 1:
            return updated_node

        statement = updated_node.body[0]

        # AssignmentStatement인지 확인
        if not isinstance(statement, cst.Assign):
            return updated_node

        # metadata 변수 찾기
        if not self._is_metadata_assignment(statement):
            return updated_node

        # metadata 객체 수정
        new_statement = self._update_metadata_object(statement)
        if new_statement:
            self.modified = True
            return updated_node.with_changes(body=[new_statement])

        return updated_node

    def _is_metadata_assignment(self, node: cst.Assign) -> bool:
        """
        export const metadata = {...} 형태인지 확인
        """
        # 좌변이 Name("metadata")인지 확인
        for target in node.targets:
            if isinstance(target.target, cst.Name):
                if target.target.value == "metadata":
                    return True
        return False

    def _update_metadata_object(self, node: cst.Assign) -> Optional[cst.Assign]:
        """
        metadata 객체의 title/description을 변경
        """
        value = node.value

        # Dict가 아니면 무시
        if not isinstance(value, (cst.Dict, cst.Call)):
            return None

        # Dict인 경우만 처리 (간단한 경우)
        if isinstance(value, cst.Dict):
            new_elements = []
            title_updated = False
            description_updated = False

            for element in value.elements:
                if isinstance(element, cst.DictElement):
                    key = element.key
                    if isinstance(key, cst.SimpleString) or isinstance(key, cst.Name):
                        key_value = key.value if isinstance(key, cst.SimpleString) else key.value

                        # title 변경
                        if ("title" in key_value) and self.new_title:
                            new_elements.append(
                                element.with_changes(
                                    value=cst.SimpleString(f'"{self.new_title}"')
                                )
                            )
                            title_updated = True
                        # description 변경
                        elif ("description" in key_value) and self.new_description:
                            new_elements.append(
                                element.with_changes(
                                    value=cst.SimpleString(f'"{self.new_description}"')
                                )
                            )
                            description_updated = True
                        else:
                            new_elements.append(element)
                else:
                    new_elements.append(element)

            if title_updated or description_updated:
                new_dict = value.with_changes(elements=new_elements)
                return node.with_changes(value=new_dict)

        return None


class MetaUpdater(ActionExecutor):
    """
    메타 타이틀/설명을 변경하는 실행자

    지원 파일 형식:
    - TSX: src/app/layout.tsx (Next.js metadata 객체)
    - HTML: index.html (<title>, <meta description>)
    """

    def execute(self, action: Action) -> ExecutionResult:
        """
        메타 타이틀/설명 변경 액션을 실행합니다.

        Args:
            action: 실행할 액션
                - action_type: "update_meta_title" 또는 "update_meta_description"
                - parameters: {"new_title": "...", "new_description": "..."}
                - target_file: 대상 파일 경로

        Returns:
            실행 결과
        """
        start_time = time.time()

        try:
            # 파일 경로 확인
            if not action.target_file:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message="target_file이 지정되지 않았습니다",
                    error="Missing target_file"
                )

            file_path = self._resolve_file_path(action.product_id, action.target_file)

            if not file_path.exists():
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message=f"파일을 찾을 수 없습니다: {file_path}",
                    error="File not found"
                )

            # 파라미터 추출
            new_title = action.parameters.get("new_title")
            new_description = action.parameters.get("new_description")

            if not new_title and not new_description:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message="new_title 또는 new_description이 필요합니다",
                    error="Missing parameters"
                )

            # 파일 타입에 따라 처리
            if file_path.suffix in [".tsx", ".ts", ".jsx", ".js"]:
                result = self._update_tsx_meta(action, file_path, new_title, new_description, action.parameters.get("canonical_url"), action.parameters.get("og_image"))
            elif file_path.suffix in [".html", ".htm"]:
                result = self._update_html_meta(action, file_path, new_title, new_description, action.parameters.get("canonical_url"))
            else:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message=f"지원하지 않는 파일 형식: {file_path.suffix}",
                    error="Unsupported file type"
                )

            execution_time = time.time() - start_time
            result.execution_time = execution_time

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            return ExecutionResult(
                action_id=action.id,
                success=False,
                message=f"실행 중 에러 발생: {str(e)}",
                error=str(e),
                execution_time=execution_time
            )

    def _update_tsx_meta(
        self, action: Action, file_path: Path, new_title: Optional[str], new_description: Optional[str]
    ) -> ExecutionResult:
        """
        TSX 파일의 metadata 객체를 변경합니다.

        LibCST는 TypeScript를 파싱하지 못하므로, 정규식으로 간단하게 치환합니다.

        Args:
            file_path: 대상 파일 경로
            new_title: 새 타이틀
            new_description: 새 설명

        Returns:
            실행 결과
        """
        import re

        # Context Manager로 자동 백업 및 롤백
        with self.backup_manager.backup_context(str(file_path)) as backup_path:
            # 파일 읽기
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            modified_code = source_code
            changed = False

            # title 변경
            if new_title:
                # 1. Next.js metadata 객체: title: "..."
                # (더 유연한 매칭: 대소문자 무시, 여러 줄 무시)
                title_pattern_obj = r'(title:\s*["\'])([^"\']+)(["\'])'
                # 2. React 컴포넌트 Props: title="..."
                title_pattern_prop = r'(title\s*=\s*["\'])([^"\']+)(["\'])'
                
                if re.search(title_pattern_obj, modified_code, re.IGNORECASE):
                    modified_code = re.sub(title_pattern_obj, rf'\1{new_title}\3', modified_code, flags=re.IGNORECASE)
                    changed = True
                elif re.search(title_pattern_prop, modified_code, re.IGNORECASE):
                    modified_code = re.sub(title_pattern_prop, rf'\1{new_title}\3', modified_code, flags=re.IGNORECASE)
                    changed = True

            # description 변경
            if new_description:
                # 1. Next.js metadata 객체: description: "..."
                desc_pattern_obj = r'(description:\s*["\'])([^"\']+)(["\'])'
                # 2. React 컴포넌트 Props: description="..."
                desc_pattern_prop = r'(description\s*=\s*["\'])([^"\']+)(["\'])'
                
                if re.search(desc_pattern_obj, modified_code, re.IGNORECASE):
                    modified_code = re.sub(desc_pattern_obj, rf'\1{new_description}\3', modified_code, flags=re.IGNORECASE)
                    changed = True
                elif re.search(desc_pattern_prop, modified_code, re.IGNORECASE):
                    modified_code = re.sub(desc_pattern_prop, rf'\1{new_description}\3', modified_code, flags=re.IGNORECASE)
                    changed = True

            # canonical 변경
            canonical_url = action.parameters.get("canonical_url")
            if canonical_url:
                canonical_pattern = r'(canonical:\s*["\'])([^"\']+)(["\'])'
                if re.search(canonical_pattern, modified_code, re.IGNORECASE):
                    modified_code = re.sub(canonical_pattern, rf'\1{canonical_url}\3', modified_code, flags=re.IGNORECASE)
                    changed = True
            
            # OG Image 변경
            og_image = action.parameters.get("og_image")
            if og_image:
                og_pattern = r'((?:url|images|ogImage):\s*["\'])([^"\']+)(["\'])'
                if re.search(og_pattern, modified_code, re.IGNORECASE):
                    modified_code = re.sub(og_pattern, rf'\1{og_image}\3', modified_code, flags=re.IGNORECASE)
                    changed = True

            if not changed:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message="metadata 또는 title/description 태그를 찾을 수 없습니다",
                    error="Metadata not found"
                )

            # 파일 저장
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(modified_code)

            return ExecutionResult(
                action_id=action.id,
                success=True,
                message=f"TSX 메타데이터 필수 항목 변경 완료: {file_path.name}",
                changed_files=[str(file_path)],
                backup_path=backup_path
            )

    def _update_html_meta(
        self, action: Action, file_path: Path, new_title: Optional[str], new_description: Optional[str]
    ) -> ExecutionResult:
        """
        HTML 파일의 <title>과 <meta description>을 변경합니다.

        Args:
            file_path: 대상 파일 경로
            new_title: 새 타이틀
            new_description: 새 설명

        Returns:
            실행 결과
        """
        # Context Manager로 자동 백업 및 롤백
        with self.backup_manager.backup_context(str(file_path)) as backup_path:
            # 파일 읽기
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            # BeautifulSoup로 파싱
            soup = BeautifulSoup(html_content, "html.parser")

            changed = False

            # <title> 변경
            if new_title:
                title_tag = soup.find("title")
                if title_tag:
                    title_tag.string = new_title
                    changed = True

            # <meta description> 변경
            if new_description:
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    meta_desc["content"] = new_description
                    changed = True

            if not changed:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message="<title> 또는 <meta description>을 찾을 수 없습니다",
                    error="Tags not found"
                )

            # 파일 저장 (원본 포맷 유지)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(soup))

            return ExecutionResult(
                action_id=action.id,
                success=True,
                message=f"HTML 메타데이터 변경 완료: {file_path.name}",
                changed_files=[str(file_path)],
                backup_path=backup_path
            )
