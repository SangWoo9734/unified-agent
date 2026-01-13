# 🏗️ v2.0 Architecture - Repository Dispatch 방식

## 목차
- [개요](#개요)
- [v1.0 vs v2.0 비교](#v10-vs-v20-비교)
- [아키텍처 상세](#아키텍처-상세)
- [Dispatch Payload 형식](#dispatch-payload-형식)
- [새 프로덕트 추가 가이드](#새-프로덕트-추가-가이드)
- [트러블슈팅](#트러블슈팅)

---

## 개요

v2.0은 **Repository Dispatch** 패턴을 사용하여 확장성과 성능을 극대화합니다.

### 핵심 개념

**v1.0 (직접 방식)**:
- unified-agent가 모든 프로덕트를 clone
- 파일을 직접 수정하고 PR 생성
- 프로덕트마다 2분 소요 → 10개면 20분

**v2.0 (Dispatch 방식)**:
- unified-agent는 **Dispatch 이벤트만 전송** (10초)
- 각 프로덕트가 자체 GitHub Actions로 파일 수정 & PR 생성
- 프로덕트 개수 무관 → 100개여도 10초

---

## v1.0 vs v2.0 비교

| 항목 | v1.0 (직접 방식) | v2.0 (Dispatch 방식) |
|------|------------------|---------------------|
| **실행 시간** | 2분 × 프로덕트 수 | ~10초 (고정) |
| **확장성** | ❌ 선형 증가 | ✅ 무한 확장 |
| **프로덕트 독립성** | ❌ unified-agent에 종속 | ✅ 완전 독립 |
| **커스터마이징** | ❌ 중앙에서만 수정 | ✅ 각 프로덕트 자유 |
| **에러 격리** | ❌ 한 프로덕트 실패 시 전체 영향 | ✅ 완전 격리 |
| **GitHub Actions 비용** | 높음 (clone 시간) | 낮음 (이벤트만) |

### 성능 비교 예시

**프로덕트 3개일 때**:
- v1.0: ~6분 (clone 2분 × 3)
- v2.0: ~10초 ✨ **36배 빠름**

**프로덕트 10개일 때**:
- v1.0: ~20분
- v2.0: ~10초 ✨ **120배 빠름**

---

## 아키텍처 상세

### 전체 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                     unified-agent (Level 2 v2.0)                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. SEO Report에서 액션 추출                               │   │
│  │    - AI로 개선 사항 파싱                                  │   │
│  │    - 액션 타입별 분류 (update_meta_title, etc.)          │   │
│  └──────────────────┬───────────────────────────────────────┘   │
│                     ↓                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 2. 안전성 검증                                            │   │
│  │    - 화이트리스트 검증 (action_type, file_path)          │   │
│  │    - XSS/Injection 패턴 탐지                             │   │
│  │    - 경로 순회(Path Traversal) 방지                      │   │
│  └──────────────────┬───────────────────────────────────────┘   │
│                     ↓                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 3. Repository Dispatch 전송                               │   │
│  │    - GitHub API 호출                                      │   │
│  │    - event_type: "seo-improvements"                       │   │
│  │    - Payload 전송 (JSON)                                  │   │
│  └──────────────────┬───────────────────────────────────────┘   │
└────────────────────┼────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ↓                         ↓
┌───────────────────┐     ┌───────────────────┐
│  qr-generator     │     │  convert-image    │
│  ───────────────  │     │  ───────────────  │
│                   │     │                   │
│ 📡 Dispatch Event │     │ 📡 Dispatch Event │
│       ↓           │     │       ↓           │
│ ┌───────────────┐ │     │ ┌───────────────┐ │
│ │ seo-pr.yml    │ │     │ │ seo-pr.yml    │ │
│ │ 워크플로우     │ │     │ │ 워크플로우     │ │
│ └───────┬───────┘ │     │ └───────┬───────┘ │
│         ↓         │     │         ↓         │
│ ┌───────────────┐ │     │ ┌───────────────┐ │
│ │ apply_seo_    │ │     │ │ apply_seo_    │ │
│ │ actions.py    │ │     │ │ actions.py    │ │
│ │               │ │     │ │               │ │
│ │ - 파일 읽기   │ │     │ │ - 파일 읽기   │ │
│ │ - Regex 수정  │ │     │ │ - Regex 수정  │ │
│ │ - Git commit  │ │     │ │ - Git commit  │ │
│ └───────┬───────┘ │     │ └───────┬───────┘ │
│         ↓         │     │         ↓         │
│    PR 생성 ✅     │     │    PR 생성 ✅     │
└───────────────────┘     └───────────────────┘
```

### 컴포넌트 설명

#### unified-agent/core/level2_agent_v2.py

**역할**: 오케스트레이터 - 전체 플로우 관리

```python
class Level2AgentV2:
    def __init__(self, github_owner: str, gemini_api_key: Optional[str] = None):
        self.github_owner = github_owner
        self.extractor = ActionExtractor(api_key=gemini_api_key)  # Gemini AI
        self.validator = ActionValidator()
        self.dispatcher = RepositoryDispatcher(github_token)

    def process_report(self, report_path: str, products: List[str]):
        # 1. 액션 추출 (AI)
        actions = self.extractor.extract_actions(report_path)

        # 2. 프로덕트별 그룹화
        for product in products:
            product_actions = [a for a in actions if a.product == product]

            # 3. 안전성 검증
            safe_actions = [a for a in product_actions if self.validator.validate(a)]

            # 4. Dispatch 전송
            self.dispatcher.send_dispatch(product, safe_actions)
```

#### unified-agent/core/executors/repository_dispatcher.py

**역할**: GitHub Repository Dispatch 전송

```python
class RepositoryDispatcher:
    def send_dispatch(self, repo_name: str, actions: List[Action]):
        payload = {
            "event_type": "seo-improvements",
            "client_payload": {
                "actions": [action.to_dict() for action in actions],
                "timestamp": datetime.now().isoformat(),
                "source": "unified-agent-v2"
            }
        }

        response = requests.post(
            f"https://api.github.com/repos/{owner}/{repo_name}/dispatches",
            headers={"Authorization": f"token {self.github_token}"},
            json=payload
        )
```

#### 프로덕트/.github/workflows/seo-pr.yml

**역할**: Dispatch 이벤트 수신 및 PR 생성

```yaml
name: SEO PR Automation
on:
  repository_dispatch:
    types: [seo-improvements]  # unified-agent에서 전송한 이벤트

jobs:
  apply-seo-improvements:
    runs-on: ubuntu-latest
    permissions:
      contents: write        # Git push 권한
      pull-requests: write   # PR 생성 권한

    steps:
      - uses: actions/checkout@v4

      - name: Apply SEO Actions
        run: |
          python scripts/apply_seo_actions.py \
            '${{ toJson(github.event.client_payload.actions) }}'

      - name: Create Pull Request
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          git checkout -b seo/auto-improvements-${{ github.run_id }}
          git add .
          git commit -m "🤖 [SEO Agent] Apply SEO improvements"
          git push -u origin seo/auto-improvements-${{ github.run_id }}

          gh pr create --title "🤖 SEO Improvements" --body "..."
        env:
          GH_TOKEN: ${{ github.token }}
```

#### 프로덕트/scripts/apply_seo_actions.py

**역할**: 실제 파일 수정 (Regex 기반)

```python
import json
import re
import sys
from pathlib import Path

def apply_actions(actions_json: str):
    actions = json.loads(actions_json)

    for action in actions:
        action_type = action['action_type']
        file_path = action['target_file']
        new_value = action.get('new_value') or action['parameters'].get('new_value')

        full_path = Path(file_path)
        content = full_path.read_text(encoding='utf-8')

        if action_type == 'update_meta_title':
            if file_path.endswith('.html'):
                # HTML: Regex로 정확히 수정
                pattern = r'(<title>)([^<]+)(</title>)'
                modified = re.sub(pattern, rf'\1{new_value}\3', content)
            elif file_path.endswith('.tsx'):
                # Next.js: Metadata 객체 수정
                pattern = r'(title:\s*["\'])([^"\']+)(["\'])'
                modified = re.sub(pattern, rf'\g<1>{new_value}\g<3>', content)

            full_path.write_text(modified, encoding='utf-8')
            print(f"✅ Updated {file_path}: title = {new_value}")

if __name__ == '__main__':
    apply_actions(sys.argv[1])
```

---

## Dispatch Payload 형식

### Event 구조

```json
{
  "event_type": "seo-improvements",
  "client_payload": {
    "actions": [
      {
        "action_type": "update_meta_title",
        "product": "qr-generator",
        "target_file": "src/app/layout.tsx",
        "new_value": "Free QR Code Generator - Create QR Codes Online",
        "current_value": "QR Generator",
        "reason": "검색어 'free qr code' 포함하여 SEO 개선",
        "expected_impact": "검색 노출 +20%, CTR +15%"
      },
      {
        "action_type": "update_meta_description",
        "product": "qr-generator",
        "target_file": "src/app/layout.tsx",
        "new_value": "Create custom QR codes for free. Download as PNG, SVG. No signup required.",
        "current_value": "Generate QR codes online",
        "reason": "행동 유도 키워드(free, download) 추가",
        "expected_impact": "CTR +10%"
      }
    ],
    "timestamp": "2026-01-14T12:34:56.789Z",
    "source": "unified-agent-v2",
    "report_id": "2026-01-14_multi_product_analysis"
  }
}
```

### Action 필드 설명

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| `action_type` | string | ✅ | 액션 타입 (화이트리스트 검증됨) |
| `product` | string | ✅ | 대상 프로덕트 이름 |
| `target_file` | string | ✅ | 수정할 파일 경로 (상대 경로) |
| `new_value` | string | ✅ | 새로운 값 |
| `current_value` | string | ⚠️ | 현재 값 (참고용) |
| `reason` | string | ⚠️ | 변경 이유 (PR 본문용) |
| `expected_impact` | string | ⚠️ | 예상 효과 (PR 본문용) |

### 지원하는 action_type

현재 구현된 액션:
- ✅ `update_meta_title` - 메타 타이틀 변경
- ✅ `update_meta_description` - 메타 설명 변경

추가 예정 (Phase 3):
- ⏳ `add_internal_link` - 내부 링크 추가
- ⏳ `update_canonical_url` - Canonical URL 설정
- ⏳ `update_og_tags` - Open Graph 태그 업데이트

---

## 새 프로덕트 추가 가이드

새 프로덕트를 SEO Agent 시스템에 추가하는 단계별 가이드입니다.

### 1단계: unified-agent 설정

#### products.yaml에 프로덕트 추가

`unified-agent/config/products.yaml`:

```yaml
products:
  # 기존 프로덕트
  qr-generator:
    name: "QR Generator"
    gsc_property_url: "sc-domain:qr-generator.com"
    ga4_property_id: "123456789"
    analysis_days: 7

  # 새 프로덕트 추가 ⭐
  my-new-product:
    name: "My New Product"
    gsc_property_url: "sc-domain:my-product.com"    # GSC 속성 URL
    ga4_property_id: "987654321"                     # GA4 속성 ID
    analysis_days: 7                                  # 분석 기간 (일)
```

**GSC 속성 URL 찾는 방법**:
1. Google Search Console (https://search.google.com/search-console)
2. 속성 선택
3. URL 바에서 `resource_id=sc-domain:your-domain.com` 확인

**GA4 속성 ID 찾는 방법**:
1. Google Analytics (https://analytics.google.com)
2. 관리 → 속성 설정
3. "속성 ID" 숫자 (예: 123456789)

### 2단계: 프로덕트 저장소 설정

#### 2.1 GitHub Actions Workflow 추가

`.github/workflows/seo-pr.yml` 파일 생성:

```yaml
name: SEO PR Automation

on:
  repository_dispatch:
    types: [seo-improvements]

jobs:
  apply-seo-improvements:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Apply SEO Actions
        run: |
          python scripts/apply_seo_actions.py '${{ toJson(github.event.client_payload.actions) }}'

      - name: Create Pull Request
        run: |
          # Git 설정
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

          # 브랜치 생성
          BRANCH_NAME="seo/auto-improvements-${{ github.run_id }}"
          git checkout -b $BRANCH_NAME

          # 변경 사항 커밋
          git add .

          # Commit body를 heredoc으로 작성
          cat > /tmp/commit_body.txt << 'COMMIT_BODY'
          Generated by unified-agent v2.0

          Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
          COMMIT_BODY

          git commit -m "🤖 [SEO Agent] Apply SEO improvements" -m "$(cat /tmp/commit_body.txt)"

          # Push
          git push -u origin $BRANCH_NAME

          # PR 본문 작성
          cat > /tmp/pr_body.md << 'PRBODY'
          ## 🤖 SEO Agent - Automated Improvements

          이 PR은 unified-agent가 SEO 분석 결과를 바탕으로 자동 생성했습니다.

          ### 📋 Applied Actions

          ${{ toJson(github.event.client_payload.actions) }}

          ### ✅ Test Checklist

          - [ ] 메타 태그 확인
          - [ ] 페이지 렌더링 확인
          - [ ] 빌드 테스트 통과
          - [ ] SEO 도구로 검증 (Google Search Console, Lighthouse)

          ---

          🤖 Generated by [unified-agent v2.0](https://github.com/YOUR_USERNAME/unified-agent)
          PRBODY

          # PR 생성
          gh pr create \
            --title "🤖 SEO Improvements - $(date +'%Y-%m-%d')" \
            --body-file /tmp/pr_body.md
        env:
          GH_TOKEN: ${{ github.token }}
```

#### 2.2 Python 스크립트 추가

`scripts/apply_seo_actions.py` 파일 생성:

```python
#!/usr/bin/env python3
"""
SEO Actions Applier for Repository Dispatch v2.0

unified-agent에서 전송한 Dispatch payload를 받아 실제 파일을 수정합니다.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

def apply_update_meta_title(file_path: str, new_value: str) -> bool:
    """메타 타이틀 업데이트"""
    full_path = Path(file_path)

    if not full_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    content = full_path.read_text(encoding='utf-8')

    if file_path.endswith('.html'):
        # HTML 파일 (Vite 등)
        pattern = r'(<title>)([^<]+)(</title>)'
        modified = re.sub(pattern, rf'\1{new_value}\3', content)
    elif file_path.endswith('.tsx') or file_path.endswith('.ts'):
        # Next.js Metadata (src/app/layout.tsx)
        # title: "Old Title" → title: "New Title"
        pattern = r'(title:\s*["\'])([^"\']+)(["\'])'
        modified = re.sub(pattern, rf'\g<1>{new_value}\g<3>', content)
    else:
        print(f"❌ Unsupported file type: {file_path}")
        return False

    full_path.write_text(modified, encoding='utf-8')
    print(f"✅ Updated {file_path}: title = '{new_value}'")
    return True

def apply_update_meta_description(file_path: str, new_value: str) -> bool:
    """메타 설명 업데이트"""
    full_path = Path(file_path)

    if not full_path.exists():
        print(f"❌ File not found: {file_path}")
        return False

    content = full_path.read_text(encoding='utf-8')

    if file_path.endswith('.html'):
        # HTML: <meta name="description" content="...">
        pattern = r'(<meta[^>]*name=["\']description["\'][^>]*content=["\'])([^"\']*)(["\']\s*/?>'
        modified = re.sub(pattern, rf'\g<1>{new_value}\g<3>', content, flags=re.IGNORECASE)
    elif file_path.endswith('.tsx') or file_path.endswith('.ts'):
        # Next.js: description: "..."
        pattern = r'(description:\s*["\'])([^"\']+)(["\'])'
        modified = re.sub(pattern, rf'\g<1>{new_value}\g<3>', content)
    else:
        print(f"❌ Unsupported file type: {file_path}")
        return False

    full_path.write_text(modified, encoding='utf-8')
    print(f"✅ Updated {file_path}: description = '{new_value}'")
    return True

def apply_actions(actions_json: str):
    """액션 리스트를 순서대로 적용"""
    try:
        actions = json.loads(actions_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    if not actions:
        print("⚠️  No actions to apply")
        return

    print(f"📋 Applying {len(actions)} action(s)...")

    success_count = 0
    for i, action in enumerate(actions, 1):
        action_type = action.get('action_type')
        file_path = action.get('target_file')

        # new_value 추출 (두 가지 형식 지원)
        new_value = action.get('new_value')
        if not new_value and 'parameters' in action:
            new_value = action['parameters'].get('new_value')

        if not all([action_type, file_path, new_value]):
            print(f"❌ Action {i}: Missing required fields")
            continue

        print(f"\n[{i}/{len(actions)}] {action_type} → {file_path}")

        # 액션 타입별 처리
        if action_type == 'update_meta_title':
            success = apply_update_meta_title(file_path, new_value)
        elif action_type == 'update_meta_description':
            success = apply_update_meta_description(file_path, new_value)
        else:
            print(f"❌ Unknown action type: {action_type}")
            success = False

        if success:
            success_count += 1

    print(f"\n✅ Successfully applied {success_count}/{len(actions)} action(s)")

    if success_count == 0:
        print("❌ No actions were applied successfully")
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python apply_seo_actions.py '<JSON_ACTIONS>'")
        sys.exit(1)

    apply_actions(sys.argv[1])
```

#### 2.3 스크립트 실행 권한 부여

```bash
chmod +x scripts/apply_seo_actions.py
```

#### 2.4 GitHub Actions 권한 설정

**중요**: 다음 설정을 활성화해야 PR 생성이 가능합니다.

1. GitHub 저장소 → **Settings** → **Actions** → **General**
2. **Workflow permissions** 섹션:
   - ✅ "Read and write permissions" 선택
   - ✅ "Allow GitHub Actions to create and approve pull requests" 체크
3. **Save** 클릭

### 3단계: 테스트

#### 로컬 테스트 (unified-agent)

```bash
cd unified-agent

# v2.0 모드로 실행
ENABLE_AUTO_PR=true \
USE_DISPATCH_V2=true \
GITHUB_OWNER=your-username \
python main.py
```

**확인 사항**:
- ✅ "Dispatch 전송 성공" 로그 확인
- ✅ GitHub Actions가 트리거되었는지 확인
- ✅ PR이 자동 생성되었는지 확인

#### 수동 Dispatch 테스트

GitHub CLI로 수동으로 Dispatch 전송:

```bash
gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  /repos/YOUR_USERNAME/my-new-product/dispatches \
  -f event_type='seo-improvements' \
  -f 'client_payload[actions][0][action_type]=update_meta_title' \
  -f 'client_payload[actions][0][target_file]=index.html' \
  -f 'client_payload[actions][0][new_value]=Test Title'
```

### 4단계: 프로덕트별 커스터마이징

#### 파일 경로 변경

프로덕트마다 파일 구조가 다를 수 있습니다:

| 프레임워크 | 메타 태그 위치 |
|-----------|---------------|
| **Vite** | `index.html` |
| **Next.js (App Router)** | `src/app/layout.tsx` |
| **Next.js (Pages)** | `pages/_app.tsx` 또는 `pages/_document.tsx` |
| **CRA** | `public/index.html` |

`apply_seo_actions.py`에서 파일 경로 처리를 수정하세요.

#### 추가 액션 타입 구현

프로덕트 특화 액션을 추가할 수 있습니다:

```python
def apply_custom_action(file_path: str, params: Dict[str, Any]) -> bool:
    """프로덕트 전용 커스텀 액션"""
    # 구현...
    pass

# apply_actions() 함수에 추가:
elif action_type == 'my_custom_action':
    success = apply_custom_action(file_path, action.get('parameters', {}))
```

---

## 트러블슈팅

### 문제 1: Dispatch 이벤트가 전송되지 않음

**증상**:
```
❌ Failed to send dispatch to my-product: 404
```

**원인**: GitHub Token 권한 부족 또는 저장소 이름 오류

**해결**:
1. GitHub Token에 `repo` + `workflow` 권한 확인
2. `products.yaml`의 프로덕트 이름이 실제 저장소 이름과 일치하는지 확인
3. `GITHUB_OWNER` 환경변수 확인

### 문제 2: GitHub Actions가 트리거되지 않음

**증상**: Dispatch 전송 성공했지만 워크플로우가 실행되지 않음

**원인**: 워크플로우 파일 오류 또는 `event_type` 불일치

**해결**:
1. `.github/workflows/seo-pr.yml` 파일이 `main` 브랜치에 있는지 확인
2. `on.repository_dispatch.types`가 `[seo-improvements]`인지 확인
3. GitHub Actions 탭에서 워크플로우가 활성화되었는지 확인

### 문제 3: PR 생성 실패 (Permission denied)

**증상**:
```
Error: GraphQL: GitHub Actions is not permitted to create or approve pull requests
```

**원인**: Workflow permissions 설정 필요

**해결**:
1. Settings → Actions → General
2. "Allow GitHub Actions to create and approve pull requests" 체크
3. 워크플로우 재실행

### 문제 4: 파일 수정이 적용되지 않음

**증상**: PR은 생성되지만 파일 내용이 변경되지 않음

**원인**: 파일 경로 불일치 또는 Regex 패턴 오류

**해결**:
1. `apply_seo_actions.py` 로그 확인:
   ```
   ❌ File not found: src/app/layout.tsx
   ```
2. 실제 파일 경로와 `target_file` 일치 여부 확인
3. 로컬에서 스크립트 직접 실행:
   ```bash
   python scripts/apply_seo_actions.py '[{"action_type":"update_meta_title","target_file":"index.html","new_value":"Test"}]'
   ```

### 문제 5: HTML 포맷이 깨짐

**증상**: BeautifulSoup 사용 시 HTML 속성 순서 변경, 값 손실

**원인**: BeautifulSoup의 HTML 직렬화 문제

**해결**: ✅ **Regex 사용 (현재 구현)**
```python
# ❌ BeautifulSoup (깨짐)
soup = BeautifulSoup(content, 'html.parser')
title_tag.string = new_value
html = str(soup)  # 포맷 손실!

# ✅ Regex (포맷 유지)
pattern = r'(<title>)([^<]+)(</title>)'
modified = re.sub(pattern, rf'\1{new_value}\3', content)
```

### 문제 6: YAML 워크플로우 문법 오류

**증상**:
```
Invalid workflow file: .github/workflows/seo-pr.yml#L67
```

**원인**: Bash 멀티라인 변수를 YAML에서 잘못 사용

**해결**: Heredoc 또는 별도 `-m` 플래그 사용
```yaml
# ❌ 잘못된 방법
- run: |
    MSG="line1

    line2"
    git commit -m "$MSG"

# ✅ 올바른 방법 1 (heredoc)
- run: |
    cat > /tmp/msg.txt << 'EOF'
    line1

    line2
    EOF
    git commit -F /tmp/msg.txt

# ✅ 올바른 방법 2 (separate -m)
- run: git commit -m "line1" -m "" -m "line2"
```

### 문제 7: Git push 실패 (Exit code 128)

**증상**:
```
Error: Process completed with exit code 128
```

**원인**: Workflow permissions 부족

**해결**: 워크플로우에 permissions 추가
```yaml
jobs:
  apply-seo-improvements:
    permissions:
      contents: write        # ✅ 필수
      pull-requests: write   # ✅ 필수
```

---

## 추가 리소스

- **[README.md](../README.md)** - 프로젝트 개요
- **[ARCHITECTURE_DECISIONS.md](./ARCHITECTURE_DECISIONS.md)** - ADR 문서
- **[GitHub Actions 공식 문서](https://docs.github.com/en/actions)**
- **[Repository Dispatch API](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)**

---

**질문이나 이슈가 있다면** GitHub Issues에 남겨주세요! 🙋‍♂️
