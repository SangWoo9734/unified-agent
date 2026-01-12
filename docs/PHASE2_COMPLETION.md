# Phase 2 완료: 프로덕트 워크플로우 구현

**날짜**: 2026-01-13
**상태**: ✅ 완료

---

## 🎯 목표

각 프로덕트(qr-generator, convert-image)에 repository_dispatch 이벤트를 수신하고 PR을 생성하는 워크플로우 추가

---

## ✅ 완료된 작업

### 1. qr-generator 워크플로우

**파일**: `qr-generator/.github/workflows/seo-pr.yml`

**기능**:
1. `repository_dispatch` 이벤트 수신 (event_type: `seo-improvements`)
2. Python 환경 설정
3. `scripts/apply_seo_actions.py` 실행
4. Git commit & push
5. GitHub PR 자동 생성

**핵심 로직**:
```yaml
on:
  repository_dispatch:
    types: [seo-improvements]

steps:
  - name: Apply SEO actions
    env:
      ACTIONS_JSON: ${{ toJson(github.event.client_payload.actions) }}
    run: python scripts/apply_seo_actions.py

  - name: Create Pull Request
    run: |
      git checkout -b "seo/improvements-${TIMESTAMP}"
      git commit -m "🤖 [SEO Agent] Apply SEO improvements"
      git push -u origin "$BRANCH_NAME"
      gh pr create --title "🔍 [SEO Agent] Auto improvements"
```

---

### 2. qr-generator Python 스크립트

**파일**: `qr-generator/scripts/apply_seo_actions.py`

**기능**:
- 환경변수에서 `ACTIONS_JSON` 읽기
- JSON 파싱 → Action 객체 리스트
- 각 액션 타입별 파일 수정:
  - `update_meta_title`: TSX/HTML 메타 타이틀 변경
  - `update_meta_description`: TSX/HTML 메타 설명 변경
- 적용 결과를 `/tmp/applied_actions.md`에 저장

**지원 파일 타입**:
- TSX/TS: Regex 기반 패턴 매칭
- HTML: BeautifulSoup 파싱

**예시 (TSX 메타 타이틀)**:
```python
# Pattern: title: "..." 또는 title: '...'
pattern = r'(title:\s*["\'])([^"\']+)(["\'])'
modified = re.sub(pattern, rf'\g<1>{new_value}\g<3>', content)
```

---

### 3. convert-image 워크플로우

**파일**: `convert-image/.github/workflows/seo-pr.yml`

qr-generator와 동일한 구조. Product 이름만 `convert-image`로 변경.

---

### 4. convert-image Python 스크립트

**파일**: `convert-image/scripts/apply_seo_actions.py`

qr-generator와 동일한 로직.

---

## 📊 Phase 2 완료 요약

| 프로덕트 | 워크플로우 | Python 스크립트 | 상태 |
|---------|-----------|----------------|------|
| qr-generator | ✅ | ✅ | 완료 |
| convert-image | ✅ | ✅ | 완료 |

---

## 🔄 전체 플로우 (v2.0)

```
1. unified-agent (GitHub Actions)
   ↓
   데이터 수집 → 분석 → 리포트 생성 → 액션 추출
   ↓
   Level2AgentV2.process_report()
   ↓
   RepositoryDispatcher.send_dispatch()
   ↓
   📡 repository_dispatch 이벤트 전송

2. qr-generator (GitHub Actions)
   ↓
   이벤트 수신 → apply_seo_actions.py 실행
   ↓
   파일 수정 → Git commit → PR 생성 ✅

3. convert-image (GitHub Actions)
   ↓
   이벤트 수신 → apply_seo_actions.py 실행
   ↓
   파일 수정 → Git commit → PR 생성 ✅
```

---

## 🧪 테스트 방법

### 로컬 테스트 (Python 스크립트만)

```bash
cd qr-generator

# 테스트 데이터
export ACTIONS_JSON='[
  {
    "action_type": "update_meta_title",
    "target_file": "src/app/layout.tsx",
    "new_value": "Test Title"
  }
]'

# 실행
python scripts/apply_seo_actions.py
```

**예상 출력**:
```
📦 총 1개 액션 수신

[1/1] 🔧 액션 적용: update_meta_title → src/app/layout.tsx
✅ [src/app/layout.tsx] 메타 타이틀 변경: Test Title

============================================================
✅ 적용 완료: 1/1
============================================================

📄 리포트 저장: /tmp/applied_actions.md
✅ SEO 개선 사항이 성공적으로 적용되었습니다!
```

### End-to-End 테스트 (v2.0)

```bash
# 1. unified-agent 실행 (v2.0 모드)
cd unified-agent
export USE_DISPATCH_V2=true
export ENABLE_AUTO_PR=true
export GITHUB_OWNER=SangWoo9734
python main.py
```

**예상 결과**:
1. unified-agent: Dispatch 이벤트 전송 완료
2. qr-generator: 워크플로우 트리거 → PR 생성
3. convert-image: 워크플로우 트리거 → PR 생성

---

## 🎯 Phase 2 핵심 성과

1. ✅ **독립적 워크플로우**: 각 프로덕트가 자체적으로 PR 생성
2. ✅ **Clone 제거**: unified-agent는 Dispatch만 전송
3. ✅ **재사용 가능한 스크립트**: `apply_seo_actions.py`
4. ✅ **확장 가능**: 새 프로덕트 추가 시 파일 2개만 복사
5. ✅ **완전 자동화**: repository_dispatch → 파일 수정 → PR

---

## 🔍 제한사항 및 향후 개선

### 현재 제한사항

1. **지원 액션 타입**: `update_meta_title`, `update_meta_description`만 지원
2. **파일 타입**: TSX, HTML만 지원
3. **패턴 매칭**: Regex 기반 (복잡한 코드는 처리 어려움)

### 향후 개선 방안

1. **추가 액션 타입**:
   - `add_structured_data`: Schema.org JSON-LD
   - `update_og_tags`: Open Graph 태그
   - `add_canonical`: Canonical URL
   - `inject_internal_link`: 내부 링크 자동 추가

2. **더 강력한 파싱**:
   - TypeScript AST 파서 (ts-morph)
   - 또는 Claude API 기반 코드 수정

3. **안전장치**:
   - Dry-run 모드
   - 자동 백업
   - 롤백 기능

---

## ⏭️ 다음 단계: Phase 3

Phase 3에서는 전체 플로우를 테스트하고 문서를 업데이트합니다:

1. **End-to-End 테스트**
   - [ ] unified-agent v2.0 실행
   - [ ] Dispatch 이벤트 전송 확인
   - [ ] qr-generator PR 생성 확인
   - [ ] convert-image PR 생성 확인

2. **문서 업데이트**
   - [ ] README.md: v2.0 사용법
   - [ ] CHANGELOG.md: Phase 2 완료 기록
   - [ ] 마이그레이션 가이드 (v1.0 → v2.0)

3. **GitHub 설정**
   - [ ] qr-generator: 워크플로우 파일 push
   - [ ] convert-image: 워크플로우 파일 push
   - [ ] unified-agent: v2.0 워크플로우 활성화

---

**이전**: [Phase 1 - unified-agent v2.0 구현](./PHASE1_COMPLETION.md)
**다음**: [Phase 3 - 테스트 및 배포](./PHASE3_TESTING.md) (작성 예정)
