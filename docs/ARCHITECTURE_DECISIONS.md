# 아키텍처 의사결정 기록 (ADR)

이 문서는 unified-agent 개발 과정에서의 주요 기술 의사결정을 기록합니다.

---

## ADR-001: Level 2 Agent - PR 자동화 구현

**날짜**: 2026-01-13
**상태**: ✅ 완료
**결정자**: 개발팀

### 컨텍스트

Level 1 Agent는 데이터를 수집하고 분석 리포트를 생성합니다. 하지만 리포트만 생성하는 것은 진정한 "Agent"가 아닙니다. 개선 사항을 자동으로 실행할 수 있어야 합니다.

**요구사항:**
- 리포트에서 실행 가능한 액션 자동 추출
- 안전하게 파일 수정
- GitHub PR 자동 생성
- 백업 및 롤백 기능

### 검토한 대안

#### 대안 1: 수동 실행
- 사람이 리포트 읽고 → 직접 코드 수정 → PR 생성
- ❌ 시간 소모, 확장 불가

#### 대안 2: 단순 스크립트
- Bash 스크립트로 sed/awk 사용
- ❌ 복잡한 로직 처리 어려움, 안전장치 없음

#### 대안 3: Level 2 Agent (선택 ⭐)
- Python으로 구조화된 Agent
- 안전성 검증, 백업/롤백, PR 자동화
- ✅ 확장 가능, 안전, 유지보수 쉬움

### 결정

**Level 2 Agent 구현**

**핵심 컴포넌트:**
1. ActionExtractor: 리포트 파싱
2. ActionValidator: 안전성 검증
3. MetaUpdater: 파일 수정
4. PRCreator: PR 생성
5. Level2Agent: 오케스트레이터

### 결과

- ✅ 전체 플로우 자동화 달성
- ✅ 실제 PR 생성 성공 (qr-generator/pull/1)
- ✅ 안전장치 작동 (화이트리스트, XSS 탐지)
- ✅ 백업 및 롤백 기능 검증

---

## ADR-002: TSX 파싱 - LibCST vs Regex

**날짜**: 2026-01-13
**상태**: ✅ 완료
**결정자**: 개발팀

### 컨텍스트

메타 태그를 수정하려면 TSX 파일을 파싱해야 합니다. 원래 계획은 LibCST를 사용하는 것이었습니다.

### 문제

```python
import libcst as cst

# TypeScript 코드 파싱 시도
code = "export const metadata: Metadata = { ... }"
tree = cst.parse_module(code)  # ❌ SyntaxError!
```

**LibCST는 Python만 파싱 가능. TypeScript는 불가능.**

### 검토한 대안

#### 대안 1: TypeScript AST 파서 (ts-morph, @babel/parser)
- Node.js 기반
- ❌ Python 프로젝트에 Node 의존성 추가 복잡

#### 대안 2: Regex 기반 치환 (선택 ⭐)
```python
title_pattern = r'(title:\s*["\'])([^"\']+)(["\'])'
modified = re.sub(title_pattern, rf'\1{new_title}\3', code)
```
- ✅ 간단, 빠름, 의존성 없음
- ⚠️ 복잡한 코드는 처리 어려움

#### 대안 3: Template 기반 전체 교체
- metadata 객체 전체를 템플릿으로 교체
- ❌ 기존 설정 손실 위험

### 결정

**Regex 기반 치환 사용**

**이유:**
- TSX는 Regex로 처리
- HTML은 BeautifulSoup로 처리 (안전)
- 현재 요구사항(메타 태그)에 충분
- 복잡해지면 향후 Node.js 파서 추가 가능

### 결과

- ✅ TSX 메타 태그 수정 성공
- ✅ 테스트 통과 (title, description)
- ⚠️ 제한사항: 복잡한 JSX 표현식은 미지원

### 향후 개선

복잡한 파싱이 필요하면:
- Option 1: Python에서 Node.js 호출
- Option 2: Rust 기반 파서 (swc)
- Option 3: AI 기반 코드 수정 (Claude API)

---

## ADR-003: 리포트 파싱 - Regex vs Claude API

**날짜**: 2026-01-13
**상태**: ✅ 완료
**결정자**: 개발팀

### 컨텍스트

리포트에서 액션을 추출할 때 두 가지 방법 가능:
1. Regex로 마크다운 파싱
2. Claude API로 자연어 이해

### 비교

| 측면 | Regex | Claude API |
|------|-------|-----------|
| 속도 | 0.001초 | 2-5초 |
| 비용 | 무료 | $0.01-0.02 |
| 정확도 | 95% (형식 지켜야) | 99% (유연) |
| 의존성 | 없음 | API 키 필요 |

### 결정

**Regex Primary + Claude API Fallback**

```python
def extract(self, content: str) -> List[Action]:
    # 1. Regex로 시도 (빠르고 저렴)
    actions = self._parse_with_regex(content)

    # 2. 실패 시 Claude API (정확하고 유연)
    if not actions and self.client:
        actions = self._parse_with_claude(content)

    return actions
```

**이유:**
- 95% 케이스는 Regex로 충분
- 비용 절감 (주 1회 실행, 연 $0.50 vs $50)
- Claude API는 백업용

### 결과

- ✅ Regex 파싱 성공률 95%+
- ✅ 비용 최소화
- ✅ Claude API fallback 준비됨

---

## ADR-004: GitHub Actions 통합 - Monorepo vs Multi-Repo

**날짜**: 2026-01-13
**상태**: ✅ 완료
**결정자**: 개발팀

### 컨텍스트

GitHub Actions로 자동화할 때 두 가지 구조 가능:

#### 옵션 1: Monorepo
```
agent-product/
├── .github/workflows/
├── unified-agent/
├── qr-generator/
└── convert-image/
```

#### 옵션 2: Multi-Repo (선택 ⭐)
```
github.com/user/unified-agent
github.com/user/qr-generator
github.com/user/convert-image
```

### 결정

**Multi-Repo 구조**

**이유:**
1. **독립적 배포**: 프로덕트별로 독립적으로 배포 가능
2. **권한 관리**: 프로덕트별로 다른 권한 설정 가능
3. **기존 구조**: qr-generator, convert-image 이미 별도 저장소
4. **확장성**: 프로덕트 추가 시 새 저장소만 생성

**Trade-off:**
- ❌ 프로덕트를 clone해야 함 (시간 소요)
- ✅ 하지만 Repository Dispatch로 해결 예정

### 결과

- ✅ unified-agent 별도 저장소로 생성
- ✅ GitHub Actions 정상 동작
- ⏳ Repository Dispatch 마이그레이션 계획 중

---

## ADR-005: Clone 방식 → Repository Dispatch 방식 전환

**날짜**: 2026-01-13
**상태**: ⏳ 계획 중
**결정자**: 개발팀

### 컨텍스트

현재 방식의 문제점:

```yaml
# 현재: 매번 모든 프로덕트 clone
- name: Checkout qr-generator
  uses: actions/checkout@v4
  with:
    repository: SangWoo9734/qr-generator
    token: ${{ secrets.GH_PAT }}

- name: Checkout convert-image
  uses: actions/checkout@v4
  with:
    repository: SangWoo9734/convert-image
    token: ${{ secrets.GH_PAT }}
```

**문제:**
- 프로덕트 2개 → clone 2분
- 프로덕트 10개 → clone 10분
- 불필요한 파일까지 모두 clone

### 검토한 대안

#### 대안 1: Shallow Clone
```yaml
fetch-depth: 1  # 최신 커밋만
```
- ✅ 50% 개선
- ❌ 여전히 전체 파일 clone

#### 대안 2: Sparse Checkout
```yaml
sparse-checkout: |
  src/app/layout.tsx
  src/components/
```
- ✅ 90% 개선
- ❌ 수정할 파일 미리 알아야 함

#### 대안 3: Repository Dispatch (선택 ⭐)
```
unified-agent: 리포트 생성 → Dispatch 이벤트
각 프로덕트: 이벤트 수신 → 자체 워크플로우 실행
```
- ✅ Clone 0초
- ✅ 독립적 관리
- ✅ 무한 확장 가능

#### 대안 4: GitHub App
- ✅ 더 세밀한 권한
- ❌ 오버엔지니어링

### 결정

**Repository Dispatch 방식으로 마이그레이션**

### 새로운 아키텍처

```
┌──────────────────────┐
│  unified-agent       │
│  (GitHub Actions)    │
│                      │
│  1. 데이터 수집      │
│  2. 분석 및 리포트   │
│  3. 액션 추출        │
│  4. Dispatch 전송    │
└───────┬──────────────┘
        │
        ├─ dispatch event (qr-generator) ──→ ┌──────────────────┐
        │  payload: { actions: [...] }        │  qr-generator    │
        │                                      │  (워크플로우)    │
        │                                      │  1. 파일 수정    │
        │                                      │  2. PR 생성      │
        │                                      └──────────────────┘
        │
        └─ dispatch event (convert-image) ──→ ┌──────────────────┐
           payload: { actions: [...] }         │  convert-image   │
                                               │  (워크플로우)    │
                                               │  1. 파일 수정    │
                                               │  2. PR 생성      │
                                               └──────────────────┘
```

### 장점

1. **성능**: Clone 시간 0초
2. **확장성**: 프로덕트 100개도 OK
3. **독립성**: 각 프로덕트가 자기 코드만 관리
4. **커스터마이징**: 프로덕트별로 다른 로직 가능
5. **보안**: 각 프로덕트의 토큰만 사용

### 구현 계획

**Phase 1: unified-agent 수정**
- Level2Agent에서 PR 생성 제거
- Repository Dispatch 전송 로직 추가
- 액션 데이터 JSON 직렬화

**Phase 2: 프로덕트 워크플로우 추가**
- `.github/workflows/seo-pr.yml` 생성
- `repository_dispatch` 이벤트 수신
- 액션 실행 및 PR 생성

**Phase 3: 테스트 및 배포**
- 전체 플로우 end-to-end 테스트
- 문서 업데이트
- 점진적 마이그레이션 (qr-generator → convert-image → ...)

### 예상 결과

| 메트릭 | Before | After | 개선 |
|--------|--------|-------|------|
| Clone 시간 (2개) | 2분 | 0초 | 100% |
| Clone 시간 (10개) | 10분 | 0초 | 100% |
| 확장성 | 제한적 | 무한 | ∞ |
| 독립성 | 낮음 | 높음 | +++ |

### 다음 단계

1. ✅ 의사결정 문서화 (현재)
2. ⏳ 구현 시작
3. ⏳ qr-generator 테스트
4. ⏳ convert-image 적용
5. ⏳ 문서 업데이트

---

## 의사결정 원칙

이 프로젝트의 의사결정 시 고려하는 원칙:

1. **실용성 우선**: 완벽한 것보다 동작하는 것
2. **점진적 개선**: 작게 시작, 반복적 개선
3. **확장 가능성**: 프로덕트 10개, 100개 고려
4. **안전 제일**: 화이트리스트, 백업, 롤백
5. **비용 효율**: API 호출 최소화
6. **문서화**: 결정 과정 기록

---

## 참고 자료

- [ADR (Architecture Decision Records)](https://adr.github.io/)
- [GitHub Actions Best Practices](https://docs.github.com/en/actions/learn-github-actions/best-practices-for-github-actions)
- [Repository Dispatch Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch)
