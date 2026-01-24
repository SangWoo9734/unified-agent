import re

def _infer_action_type(description: str) -> str:
    desc_lower = description.lower()
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
        return "update_meta_title"

def _extract_parameters(description: str) -> dict:
    parameters = {}
    quote_match = re.search(r'["\']([^"\']+)["\']', description)
    if quote_match:
        quoted_text = quote_match.group(1)
    else:
        ko_match = re.search(r'([a-zA-Z0-9\s가-힣]+)(?:으로|로)\s+(?:변경|업데이트|추가|교체)', description)
        quoted_text = ko_match.group(1).strip() if ko_match else None

    if quoted_text:
        action_type = _infer_action_type(description)
        if action_type == "update_meta_title":
            parameters["new_title"] = quoted_text
        elif action_type == "update_meta_description":
            parameters["new_description"] = quoted_text
        elif action_type == "add_internal_link":
            parameters["link_url"] = quoted_text
            parameters["link_text"] = quoted_text
    return parameters

content = """
## 🔴 High Priority (긴급 - 즉시 실행)
**반드시 아래 형식을 지켜주세요: "번호. [프로덕트명] 액션내용 - File: `파일경로`"**

1. **[QR Studio]** 메타 타이틀을 "새로운 타이틀"로 업데이트하여 CTR 개선 - File: `src/app/layout.tsx`
   - 대상 지표: [🔴 CTR], 현재: [0.5%], 목표: [1.5%]
   - 예상 효과: 검색 노출 클릭률 2배 증가

2. **[ConvertKits]** 메타 설명을 "새로운 설명"으로 교체하여 이탈률 감소 - File: `components/SEO.tsx`
   - 대상 지표: [🟡 참여율], 현재: [1%], 목표: [3%]
   - 예상 효과: 검색 결과에서의 명확한 정보 제공으로 유입 질 개선
"""

high_priority_pattern = r'##+.*?(?:High Priority|최우선 과제|🔴 High Priority).*?(.*?)(?=##|\Z)'
match = re.search(high_priority_pattern, content, re.DOTALL | re.IGNORECASE)
if match:
    section = match.group(1)
    # Corrected pattern
    action_pattern = r'^\d+\.\s*(.*?)(?=^\d+\.\s*|\Z)'
    action_matches = re.finditer(action_pattern, section, re.DOTALL | re.MULTILINE)
    for idx, m in enumerate(action_matches, start=1):
        text = m.group(1).strip()
        print(f"--- Action {idx} ---")
        print(f"Text: {text}")
        
        product_match = re.search(r'담당:\s*(?:\[|\*\*\[)([^\]]+)(?:\]|\)\*\*)', text)
        if not product_match:
            product_match = re.search(r'^(?:\[|\*\*\[)([^\]]+)(?:\]|\)\*\*)', text)
        
        if product_match:
            print(f"Product: {product_match.group(1)}")
        else:
            print("Product: Not found")
            
        file_match = re.search(r'`([^`]+\.(?:tsx|ts|jsx|js|html|py))`', text)
        print(f"File: {file_match.group(1) if file_match else 'Not found'}")
        
        desc = text.split('\n')[0].strip()
        print(f"Desc: {desc}")
        print(f"Params: {_extract_parameters(desc)}")
else:
    print("Section not found")
