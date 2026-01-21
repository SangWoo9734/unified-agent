"""
ActionExtractor

리포트 파일에서 High Priority 액션을 추출합니다.
"""

import re
from pathlib import Path
from typing import List, Optional
from google import genai

from .models import Action


class ActionExtractor:
    """
    마크다운 리포트에서 액션을 추출하는 클래스

    리포트 형식 예시:
    ```
    ## High Priority Actions

    1. **[QR Generator]** Update meta title to "Free QR Code Generator"
       - File: `src/app/layout.tsx`
       - Expected Impact: Improve SEO

    2. **[Convert Image]** Add internal link to QR Generator
       - File: `components/Layout.tsx`
    ```
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Args:
            api_key: Google Gemini API Key (Gemini API fallback용, 선택사항)
        """
        self.api_key = api_key
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.model_id = 'gemini-1.5-flash'
        else:
            self.client = None

    def extract_from_report(self, report_path: str) -> List[Action]:
        """
        리포트 파일에서 액션을 추출합니다.

        Args:
            report_path: 리포트 파일 경로

        Returns:
            추출된 액션 리스트

        Raises:
            FileNotFoundError: 리포트 파일이 없을 때
        """
        report_file = Path(report_path)

        if not report_file.exists():
            raise FileNotFoundError(f"Report file not found: {report_path}")

        # 파일 읽기
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 정규식으로 파싱 시도
        actions = self._parse_with_regex(content)

        # 파싱 실패 시 Gemini API fallback (선택사항)
        if not actions and self.client:
            actions = self._parse_with_gemini(content)

        return actions

    def _parse_with_regex(self, content: str) -> List[Action]:
        """
        정규식으로 리포트를 파싱합니다.

        Args:
            content: 리포트 내용

        Returns:
            액션 리스트
        """
        actions = []

        # High Priority 섹션 찾기
        # ComparativeAnalyzer가 생성하는 "### 🔴 High Priority (긴급 - 이번 주)" 및 기본 형식을 모두 지원
        high_priority_pattern = r'##+.*?(?:High Priority|최우선 과제|🔴 High Priority).*?(.*?)(?=##|\Z)'
        match = re.search(high_priority_pattern, content, re.DOTALL | re.IGNORECASE)

        if not match:
            return actions

        high_priority_section = match.group(1)

        # 각 액션 파싱
        # 형식: 1. **[Product]** Description 또는 1. [액션] - 담당: [프로덕트] 등 유연하게 대응
        action_pattern = r'\d+\.\s*(?:\*\*\[|\[)([^\]\-\n]+)(?:\]\*\*|\])\s*(.+?)(?=\d+\.\s*(?:\*\*\[|\[)|\Z)'
        action_matches = re.finditer(action_pattern, high_priority_section, re.DOTALL)

        for idx, action_match in enumerate(action_matches, start=1):
            product_id = action_match.group(1).strip().lower().replace(' ', '-')
            description_block = action_match.group(2).strip()

            # 설명 첫 줄
            description_lines = description_block.split('\n')
            description = description_lines[0].strip()

            # 파일 경로 추출
            file_match = re.search(r'File:\s*`([^`]+)`', description_block)
            target_file = file_match.group(1) if file_match else None

            # 예상 효과 추출
            impact_match = re.search(r'Expected Impact:\s*(.+)', description_block)
            expected_impact = impact_match.group(1).strip() if impact_match else None

            # action_type 추론
            action_type = self._infer_action_type(description)

            # parameters 추출
            parameters = self._extract_parameters(description, description_block)

            # Action 객체 생성
            action = Action(
                id=f"action-{idx}",
                priority="high",
                description=description,
                product_id=product_id,
                action_type=action_type,
                target_file=target_file,
                parameters=parameters,
                expected_impact=expected_impact,
                is_automatable=True
            )

            actions.append(action)

        return actions

    def _infer_action_type(self, description: str) -> str:
        """
        설명에서 action_type을 추론합니다.

        Args:
            description: 액션 설명

        Returns:
            action_type
        """
        desc_lower = description.lower()

        if "meta title" in desc_lower or "title" in desc_lower:
            return "update_meta_title"
        elif "meta description" in desc_lower or "description" in desc_lower:
            return "update_meta_description"
        elif "internal link" in desc_lower or "link" in desc_lower:
            return "add_internal_link"
        elif "canonical" in desc_lower:
            return "update_canonical_url"
        elif "og tag" in desc_lower or "open graph" in desc_lower:
            return "update_og_tags"
        else:
            # 기본값
            return "update_meta_title"

    def _extract_parameters(self, description: str, full_block: str) -> dict:
        """
        설명에서 parameters를 추출합니다.

        Args:
            description: 액션 설명
            full_block: 전체 액션 블록

        Returns:
            parameters dict
        """
        parameters = {}

        # 따옴표 안의 내용 추출
        quote_match = re.search(r'["\']([^"\']+)["\']', description)
        if quote_match:
            quoted_text = quote_match.group(1)

            # action_type에 따라 파라미터 매핑
            if "title" in description.lower():
                parameters["new_title"] = quoted_text
            elif "description" in description.lower():
                parameters["new_description"] = quoted_text
            elif "link" in description.lower():
                parameters["link_url"] = quoted_text
                parameters["link_text"] = quoted_text

        return parameters

    def _parse_with_gemini(self, content: str) -> List[Action]:
        """
        Gemini API를 사용하여 리포트를 파싱합니다.

        Args:
            content: 리포트 내용

        Returns:
            액션 리스트
        """
        if not self.model:
            return []

        # Gemini에게 구조화된 JSON으로 액션 추출 요청
        prompt = f"""다음은 프로덕트 분석 리포트입니다. "High Priority" 섹션의 액션들을 JSON 배열로 추출해주세요.

리포트:
```
{content}
```

출력 형식 (JSON):
[
  {{
    "product_id": "qr-generator",
    "description": "Update meta title to 'Free QR Code Generator'",
    "action_type": "update_meta_title",
    "target_file": "src/app/layout.tsx",
    "parameters": {{"new_title": "Free QR Code Generator"}},
    "expected_impact": "Improve SEO"
  }}
]

JSON만 출력하세요."""

        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )

            # JSON 파싱
            import json
            json_text = response.text.strip()
            # ```json ... ``` 제거
            json_text = re.sub(r'^```json\s*|\s*```$', '', json_text, flags=re.MULTILINE)

            actions_data = json.loads(json_text)

            # Action 객체로 변환
            actions = []
            for idx, data in enumerate(actions_data, start=1):
                action = Action(
                    id=f"action-{idx}",
                    priority="high",
                    description=data.get("description", ""),
                    product_id=data.get("product_id", ""),
                    action_type=data.get("action_type", "update_meta_title"),
                    target_file=data.get("target_file"),
                    parameters=data.get("parameters", {}),
                    expected_impact=data.get("expected_impact"),
                    is_automatable=True
                )
                actions.append(action)

            return actions

        except Exception as e:
            print(f"Gemini API 파싱 실패: {str(e)}")
            return []
