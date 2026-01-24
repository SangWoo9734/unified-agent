"""
LinkInjector

TSX 및 HTML 파일에 내부 링크를 삽입합니다.
"""

import re
import time
from pathlib import Path
from .action_executor import ActionExecutor
from .models import Action, ExecutionResult


class LinkInjector(ActionExecutor):
    """
    내부 링크를 삽입하는 실행자
    """

    def execute(self, action: Action) -> ExecutionResult:
        """
        내부 링크 삽입 액션을 실행합니다.
        """
        start_time = time.time()

        try:
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

            link_url = action.parameters.get("link_url")
            link_text = action.parameters.get("link_text", "관련 링크")

            if not link_url:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message="link_url이 필요합니다",
                    error="Missing parameters"
                )

            # 파일 타입에 따라 처리
            if file_path.suffix in [".tsx", ".jsx", ".js", ".ts"]:
                result = self._inject_tsx_link(action, file_path, link_url, link_text)
            elif file_path.suffix in [".html", ".htm"]:
                result = self._inject_html_link(action, file_path, link_url, link_text)
            else:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message=f"지원하지 않는 파일 형식: {file_path.suffix}",
                    error="Unsupported file type"
                )

            result.execution_time = time.time() - start_time
            return result

        except Exception as e:
            return ExecutionResult(
                action_id=action.id,
                success=False,
                message=f"링크 삽입 중 에러: {str(e)}",
                error=str(e),
                execution_time=time.time() - start_time
            )

    def _inject_tsx_link(self, action: Action, file_path: Path, url: str, text: str) -> ExecutionResult:
        """
        TSX 파일에 링크를 삽입합니다. 
        보통 푸터나 특정 섹션의 끝에 추가하는 것이 안전합니다.
        """
        with self.backup_manager.backup_context(str(file_path)) as backup_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # <a> 태그 또는 <Link> 컴포넌트 생성 (Next.js 가정이므로 Link 사용 시도)
            # 여기서는 안전하게 <a> 태그로 삽입
            link_tag = f'\n      <div className="mt-4 text-sm text-gray-500">\n        <a href="{url}" className="hover:underline text-blue-600">🔗 {text}</a>\n      </div>'

            # 마지막 </div> 앞에 삽입하거나, main 섹션 끝에 삽입 시도
            if "</main>" in content:
                new_content = content.replace("</main>", f"{link_tag}\n        </main>")
            elif "</footer>" in content:
                new_content = content.replace("</footer>", f"{link_tag}\n        </footer>")
            else:
                # 마지막 </div> 앞에 삽입 (단순화된 휴리스틱)
                last_div_idx = content.rfind("</div>")
                if last_div_idx != -1:
                    new_content = content[:last_div_idx] + link_tag + content[last_div_idx:]
                else:
                    new_content = content + link_tag

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return ExecutionResult(
                action_id=action.id,
                success=True,
                message=f"TSX 링크 삽입 완료: {url}",
                changed_files=[str(file_path)],
                backup_path=backup_path
            )

    def _inject_html_link(self, action: Action, file_path: Path, url: str, text: str) -> ExecutionResult:
        """
        HTML 파일에 링크를 삽입합니다.
        """
        from bs4 import BeautifulSoup

        with self.backup_manager.backup_context(str(file_path)) as backup_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            soup = BeautifulSoup(content, "html.parser")
            
            # 링크 태그 생성
            new_div = soup.new_tag("div", attrs={"style": "margin-top: 20px; font-size: 0.9em;"})
            new_link = soup.new_tag("a", href=url, target="_blank")
            new_link.string = f"🔗 {text}"
            new_div.append(new_link)

            # body 끝에 추가
            if soup.body:
                soup.body.append(new_div)
                changed = True
            else:
                changed = False

            if not changed:
                return ExecutionResult(
                    action_id=action.id,
                    success=False,
                    message="body 태그를 찾을 수 없습니다",
                    error="Body not found"
                )

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(soup))

            return ExecutionResult(
                action_id=action.id,
                success=True,
                message=f"HTML 링크 삽입 완료: {url}",
                changed_files=[str(file_path)],
                backup_path=backup_path
            )
