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
            self.model_id = 'gemini-2.0-flash'
        else:
            self.client = None

    def extract_from_report(self, report_path: str) -> List[Action]:
        """
        리포트 파일에서 액션을 추출합니다.
        """
        report_file = Path(report_path)

        if not report_file.exists():
            raise FileNotFoundError(f"Report file not found: {report_path}")

        # 파일 읽기
        with open(report_file, "r", encoding="utf-8") as f:
            content = f.read()

        # 1. JSON 블록 추출 시도 (가장 정확함)
        actions = self._parse_json_block(content)
        if actions:
            print(f"✅ 리포트에서 JSON 액션 추출 성공 ({len(actions)}개)")
            return actions

        # 2. 정규식으로 파싱 시도 (하위 호환)
        actions = self._parse_with_regex(content)

        # 3. 파싱 실패 시 Gemini API fallback
        if not actions and self.client:
            actions = self._parse_with_gemini(content)

        return actions

    def _parse_json_block(self, content: str) -> List[Action]:
        """리포트 내부의 JSON 코드 블록을 파싱합니다."""
        import json
        json_pattern = r'```json\s*(\[.*?\])\s*```'
        match = re.search(json_pattern, content, re.DOTALL)
        
        if not match:
            return []
            
        try:
            print(f"📊 JSON 블록 발견, 파싱 시도 중...")
            actions_data = json.loads(match.group(1))
            actions = []
            for idx, data in enumerate(actions_data, start=1):
                product_id = data.get("product_id")
                target_file = data.get("target_file")
                description = data.get("description", "SEO Update")
                
                # parameters 및 new_value 추출
                params = data.get("parameters", {})
                new_value = data.get("new_value") or params.get("new_value")
                
                # fallback: 만약 new_title/new_description만 있고 new_value가 없으면 복사
                if not new_value:
                    new_value = params.get("new_title") or params.get("new_description")
                
                print(f"   [DEBUG] Action {idx} | Product: {product_id} | File: {target_file} | Value: {new_value}")

                # 파일 경로 보정 (Vite 대응)
                if target_file and product_id == 'convert-image':
                    if 'src/app/page.tsx' in target_file:
                        target_file = 'pages/Home.tsx'
                    elif 'src/app/layout.tsx' in target_file:
                        target_file = 'src/App.tsx'

                # new_value를 parameters에 확실히 주입
                if new_value:
                    if "new_value" not in params:
                        params["new_value"] = new_value
                    if data.get("action_type") == "update_meta_title" and "new_title" not in params:
                        params["new_title"] = new_value
                    if data.get("action_type") == "update_meta_description" and "new_description" not in params:
                        params["new_description"] = new_value

                action = Action(
                    id=f"action-json-{idx}",
                    priority="high",
                    description=description,
                    product_id=product_id or "unknown",
                    action_type=data.get("action_type") or "update_meta_title",
                    target_file=target_file,
                    parameters=params,
                    expected_impact=data.get("expected_impact"),
                    is_automatable=True
                )
                
                # 필수 필드 체크 (중요!)
                if action.target_file and action.parameters.get("new_value") and len(str(action.parameters.get("new_value"))) > 2:
                    actions.append(action)
                else:
                    print(f"   ⚠️  Action {idx} 스킵: 필수 데이터 누락 또는 너무 짧은 값 ({new_value})")
                    
            return actions
        except Exception as e:
            print(f"⚠️  JSON 블록 파싱 에러: {e}")
            return []

    def _parse_with_regex(self, content: str) -> List[Action]:
        """
        정규식으로 리포트를 파싱합니다.

        Args:
            content: 리포트 내용

        Returns:
            액션 리스트
        """
        actions = []

        # ComparativeAnalyzer가 생성하는 "### 🔴 High Priority (긴급 - 즉시 실행)" 및 기타 변종 지원
        # (헤더 뒤의 텍스트가 줄바꿈 없이 바로 시작하는 경우도 고려)
        # 구체적인 헤더 형식을 우선 매칭하여 Summary 섹션의 텍스트와 혼동되지 않도록 함
        # 특히 "### 🔴 High Priority"와 같은 형식을 선호
        high_priority_head_pattern = r'(?:###|##)\s*(?:🔴\s*)?(?:High Priority|최우선 과제|긴급).*?$'
        
        # 먼저 리포트에서 섹션 위치 찾기
        matches = list(re.finditer(high_priority_head_pattern, content, re.MULTILINE | re.IGNORECASE))
        
        if not matches:
            print(f"⚠️  High Priority 섹션 헤더를 찾지 못했습니다.")
            return actions

        # 여러 개가 매칭될 경우, 보통 리포트 하단의 실행 계획(Action Plan) 섹션에 있는 것을 선택
        # (Summary에 있는 "이번 주 최우선 과제"와 같은 일반 텍스트와 구분하기 위함)
        target_match = matches[-1] # 마지막 매칭 선택
        start_pos = target_match.end()
        
        # 다음 섹션(##) 혹은 파일 끝까지 내용 추출
        next_section_match = re.search(r'^##\s+', content[start_pos:], re.MULTILINE)
        if next_section_match:
            high_priority_section = content[start_pos : start_pos + next_section_match.start()]
        else:
            high_priority_section = content[start_pos:]
        print(f"DEBUG: High Priority Section Content (first 100 chars):\n{high_priority_section[:100]}...")

        # 각 액션 파싱
        # 형식 1: 1. **[Product]** Description
        # 형식 2: 1. [액션 요약] - 담당: [Product], ...
        # (주의: 소수점에 반응하지 않도록 줄 시작에서 숫자. 형태만 매칭. 공백 허용)
        action_pattern = r'^[ \t]*\d+\.\s*(.*?)(?=^[ \t]*\d+\.\s*|\Z)'
        action_matches = re.finditer(action_pattern, high_priority_section, re.DOTALL | re.MULTILINE)

        for idx, action_match in enumerate(action_matches, start=1):
            action_text = action_match.group(1).strip()
            if not action_text:
                continue

            # Product ID 추출 시도 (강력한 패턴 매칭)
            product_id = "unknown"
            
            # 1. 명시적 키워드 우선 체크 (가장 확실함)
            text_lower = action_text.lower()
            if any(kw in text_lower for kw in ['qr studio', 'qr-studio', 'qr generator', 'qr-generator']):
                product_id = 'qr-generator'
                print(f"DEBUG: 키워드 매칭 성공 (qr-generator)")
            elif any(kw in text_lower for kw in ['convertkits', 'convert-image', 'convert image']):
                product_id = 'convert-image'
                print(f"DEBUG: 키워드 매칭 성공 (convert-image)")
            
            # 2. 키워드로 못 찾았다면 정규식 시도
            if product_id == "unknown":
                # [Product Name] 또는 **[Product Name]** 등 추출
                product_match = re.search(r'(?:\[|\*\*\[|\[\*\*)+([^\]\*]+)(?:\]|\*\*|\]\*\*)+', action_text)
                if product_match:
                    product_name = product_match.group(1).strip()
                    print(f"DEBUG: 정규식으로 감지된 프로덕트 이름: '{product_name}'")
                    pn_lower = product_name.lower()
                    if any(kw in pn_lower for kw in ['qr studio', 'qr-studio', 'qr generator', 'qr-generator']):
                        product_id = 'qr-generator'
                    elif any(kw in pn_lower for kw in ['convertkits', 'convert-image', 'convert image']):
                        product_id = 'convert-image'
                    else:
                        product_id = pn_lower.replace(' ', '-')

            # 설명 추출: 제품명이 있는 줄을 제외한 첫 번째 의미 있는 줄 찾기
            lines = [line.strip() for line in action_text.split('\n') if line.strip()]
            description = ""
            for line in lines:
                # 제품명 대괄호 구문 제외
                if re.search(r'(?:\[|\*\*\[|\[\*\*)+([^\]\*]+)(?:\]|\*\*|\]\*\*)+', line):
                    # 만약 줄 전체가 제품명 관련이라면 패스, 아니면 내용만 추출
                    clean_line = re.sub(r'(?:\[|\*\*\[|\[\*\*)+[^\]\*]+(?:\]|\*\*|\]\*\*)+', '', line).strip()
                    if not clean_line:
                        continue
                    description = clean_line
                    break
                
                if line.startswith('- ') or line.startswith('* '):
                    description = re.sub(r'^[-*]\s*', '', line)
                    break
                description = line
                break
            
            if not description and lines:
                description = lines[0]
            
            # 파일 경로 추출 (마크다운 백틱 `file_path` 찾기)
            file_match = re.search(r'`([^`]+\.(?:tsx|ts|jsx|js|html|py))`', action_text)
            target_file = file_match.group(1) if file_match else None

            # Fallback: 백틱이 없을 경우 "File: path" 또는 "파일: path" 검색
            if not target_file:
                file_hint_match = re.search(r'(?:File|파일|대상\s파일):\s*([^\s\n]+\.(?:tsx|ts|jsx|js|html|py))', action_text, re.IGNORECASE)
                if file_hint_match:
                    target_file = file_hint_match.group(1).strip()
            
            # target_file이 여전히 없으면 텍스트 전체에서 파일 경로 패턴 찾기
            if not target_file:
                path_match = re.search(r'([^\s\n]+\.(?:tsx|ts|jsx|js|html|py))', action_text)
                if path_match:
                    target_file = path_match.group(1).strip()
            
            # target_file 청소 (마침표 등 제거)
            if target_file:
                target_file = target_file.strip('.,; ')
                if target_file.lower() == "none":
                    target_file = None

            # Path Correction Heuristic (Framework Mismatch Fix)
            if target_file and product_id == 'convert-image':
                if 'src/app/page.tsx' in target_file:
                    target_file = 'pages/Home.tsx'
                elif 'src/app/layout.tsx' in target_file:
                    target_file = 'src/App.tsx'

            print(f"DEBUG: Action {idx} | Product: {product_id} | File: {target_file} | Desc: {description[:50]}...")

            # 예상 효과 추출
            impact_match = re.search(r'예상 효과:\s*(.+)', action_text)
            expected_impact = impact_match.group(1).strip() if impact_match else None

            # action_type 추론
            action_type = self._infer_action_type(description)

            # parameters 추출
            parameters = self._extract_parameters(description, action_text)

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

        # 한국어 키워드 포함
        if any(kw in desc_lower for kw in ["meta title", "title", "타이틀", "제목"]):
            return "update_meta_title"
        elif any(kw in desc_lower for kw in ["meta description", "description", "설명"]):
            return "update_meta_description"
        elif any(kw in desc_lower for kw in ["internal link", "link", "링크", "연결"]):
            return "add_internal_link"
        elif any(kw in desc_lower for kw in ["canonical", "캐노니컬", "표준"]):
            return "update_canonical_url"
        elif any(kw in desc_lower for kw in ["og tag", "open graph", "오픈그래프"]):
            return "update_og_tags"
        else:
            # 기본값
            return "update_meta_title"

    def _extract_parameters(self, description: str, full_block: str) -> dict:
        """
        설명 및 전체 블록에서 parameters를 추출합니다.
        """
        parameters = {}
        action_type = self._infer_action_type(description)

        # 1. 따옴표 찾기 (가장 긴 것을 우선 선택하여 'SEO' 같은 짧은 단어 방지)
        all_quotes = re.findall(r'["\']([^"\']+)["\']', full_block)
        quoted_text = None
        if all_quotes:
            # "File:", "URL:" 등 지표성 텍스트 제외하고 가장 적절한 후보 선택
            candidates = [q for q in all_quotes if len(q) > 2 and not q.endswith('.tsx') and not q.endswith('.ts')]
            if candidates:
                # 메타 타이틀/설명은 보통 가장 긴 텍스트임
                quoted_text = max(candidates, key=len)

        if not quoted_text:
            # 2. 한국어 조사 전의 내용 추출 ( ~로, ~으로 )
            ko_match = re.search(r'([a-zA-Z0-9\s가-힣]{3,})(?:으로|로)\s+(?:변경|업데이트|추가|교체)', full_block)
            quoted_text = ko_match.group(1).strip() if ko_match else None

        # 3. 데이터 정제 및 유효성 검사
        if quoted_text:
            cleaned = quoted_text.strip('.,; ')
            if cleaned.lower() != "none" and len(cleaned) >= 2:
                if action_type == "update_meta_title":
                    parameters["new_title"] = cleaned
                    parameters["new_value"] = cleaned
                elif action_type == "update_meta_description":
                    parameters["new_description"] = cleaned
                    parameters["new_value"] = cleaned
                elif action_type == "add_internal_link":
                    parameters["link_url"] = cleaned
                    parameters["link_text"] = cleaned
                    parameters["new_value"] = cleaned

        return parameters

    def _parse_with_gemini(self, content: str) -> List[Action]:
        """
        Gemini API를 사용하여 리포트를 파싱합니다.

        Args:
            content: 리포트 내용

        Returns:
            액션 리스트
        """
        if not self.client:
            return []

        # Gemini에게 구조화된 JSON으로 액션 추출 요청
        prompt = f"""다음은 프로덕트 분석 리포트입니다. "High Priority" 섹션의 액션들을 JSON 배열로 추출해주세요.

**중요: action_type은 반드시 아래 리스트에 정의된 영문 식별자만 사용해야 합니다 (한국어 금지).**
정의된 action_type 리스트:
- update_meta_title
- update_meta_description
- add_internal_link
- update_canonical_url
- update_og_tags

리포트:
```
{content}
```

출력 형식 (JSON):
[
  {{
    "product_id": "qr-generator",
    "description": "메타 타이틀 업데이트 내용",
    "action_type": "update_meta_title",
    "target_file": "src/app/layout.tsx",
    "parameters": {{"new_title": "New English Title"}},
    "expected_impact": "검색 노출 개선"
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
                # 1. action_type 매핑 (한국어 대항)
                raw_type = str(data.get("action_type") or "").lower()
                if any(kw in raw_type for kw in ["title", "타이틀", "제목"]):
                    action_type = "update_meta_title"
                elif any(kw in raw_type for kw in ["description", "설명"]):
                    action_type = "update_meta_description"
                elif any(kw in raw_type for kw in ["link", "링크"]):
                    action_type = "add_internal_link"
                elif any(kw in raw_type for kw in ["canonical", "캐노니컬"]):
                    action_type = "update_canonical_url"
                elif any(kw in raw_type for kw in ["og", "graph", "오픈그래프"]):
                    action_type = "update_og_tags"
                else:
                    action_type = "update_meta_title" # 기본값

                # 2. product_id 매핑
                raw_pid = str(data.get("product_id") or "").lower()
                if any(kw in raw_pid for kw in ["qr", "generator", "studio"]):
                    product_id = "qr-generator"
                elif any(kw in raw_pid for kw in ["convert", "kits", "image"]):
                    product_id = "convert-image"
                else:
                    product_id = raw_pid.replace(" ", "-") or "unknown"

                action = Action(
                    id=f"action-{idx}",
                    priority="high",
                    description=data.get("description", ""),
                    product_id=product_id,
                    action_type=action_type,
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
