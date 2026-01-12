# Specification: PR Automation for Level 2 Agent

**Feature**: pr-automation
**Created**: 2026-01-11
**Status**: Draft
**Priority**: P0 (Critical)

---

## 1. Problem Statement

### Current State

unified-agent는 현재 다음과 같이 동작합니다:

1. GSC, GA4, Trends, AdSense 데이터 수집
2. Claude API로 비교 분석
3. 마크다운 리포트 생성 (예: "QR Generator의 메타 타이틀을 변경하세요")
4. **사용자가 리포트를 읽고 수동으로 파일 변경**

### The Problem

- **Level 1 (분석만)**: 리포트는 잘 생성되지만, 실제 액션(파일 변경, PR 생성)은 사용자가 수동으로 해야 함
- **수동 작업의 문제점**:
  - 시간 소요 (리포트 읽기 → 파일 찾기 → 수정 → 커밋 → PR 생성)
  - 일관성 부족 (사람에 따라 구현 방식 다름)
  - 실행률 낮음 (바쁘면 리포트만 보고 실행 안 함)
  - 지표 개선 속도 느림

### The Goal

**Level 2 Agent**: 리포트 생성 → **자동으로 PR 생성** → 사용자는 리뷰/머지만

**핵심**:

- "Act"가 없으면 Agent가 아님
- 최소한 PR 자동 생성까지는 해야 진짜 Agent
- Level 3 (완전 자동 머지)는 여러 주 검증 후 고려

---

## 2. User Stories

### Primary User Stories

**US-1: 자동 메타 타이틀 변경**

- **As a** Product Owner
- **I want** 리포트의 "메타 타이틀 변경" 액션이 자동으로 PR로 생성되도록
- **So that** 수동 작업 없이 SEO 개선을 빠르게 적용할 수 있다

**US-2: 자동 내부 링크 추가**

- **As a** Marketing Manager
- **I want** 교차 프로모션 링크가 자동으로 추가되도록
- **So that** 프로덕트 간 트래픽 흐름을 개선할 수 있다

**US-3: 안전한 롤백**

- **As a** Developer
- **I want** 자동 변경이 실패하면 자동으로 롤백되도록
- **So that** 프로덕션 코드가 망가지지 않는다

### Secondary User Stories

**US-4: 선택적 자동화**

- **As a** Product Owner
- **I want** 어떤 액션 타입을 자동화할지 설정할 수 있도록
- **So that** 위험한 변경은 수동으로 제어할 수 있다

**US-5: PR 리뷰 편의성**

- **As a** Code Reviewer
- **I want** 자동 생성된 PR에 명확한 설명과 체크리스트가 있도록
- **So that** 빠르게 리뷰하고 머지할 수 있다

---

## 3. Functional Requirements

### Core Requirements (MVP)

**FR-1: 액션 추출**

- 리포트 파일(`reports/comparison/{date}_multi_product_analysis.md`)에서 "High Priority" 섹션 파싱
- 각 액션을 구조화된 데이터로 변환 (Action 객체)
- 정규식 파싱 + Claude API fallback

**FR-2: 액션 검증**

- 자동화 가능한 액션만 필터링
- 안전한 액션 타입: `update_meta_title`, `update_meta_description`, `add_internal_link`
- 안전한 파일: `layout.tsx`, `index.html`, `Header.tsx`, `Layout.tsx`
- 위험 패턴 감지: `<script>`, `eval()`, `innerHTML` 등

**FR-3: 파일 변경 실행**

- **메타 타이틀/설명 변경**:
  - qr-generator: `src/app/layout.tsx` (metadata 객체)
  - convert-image: `index.html` (`<title>`, `<meta description>`)
- **내부 링크 추가**:
  - qr-generator: `src/components/layout/Header.tsx`
  - convert-image: `components/Layout.tsx`
- 변경 전 백업 생성

**FR-4: PR 생성**

- GitPython으로 새 브랜치 생성 + 커밋
- PyGithub으로 GitHub PR 생성
- PR 제목: `[SEO Agent] {N} Improvement(s) - {date}`
- PR 본문: 액션 목록, 예상 효과, 테스트 체크리스트

**FR-5: 에러 처리 및 롤백**

- Context Manager 패턴으로 Git 작업 보호
- 변경 실패 시 백업에서 자동 복원
- 프로덕트별 독립 실행 (하나 실패해도 다른 건 계속)

### Extended Requirements (Post-MVP)

**FR-6: Dry-run 모드**

- `--dry-run` 플래그로 실제 PR 생성 없이 미리보기

**FR-7: Slack 알림**

- PR 생성 완료 시 Slack 채널에 알림

**FR-8: 변경 전 Syntax Validation**

- TSX: `npx tsc --noEmit` 실행
- HTML: BeautifulSoup 파싱 검증

---

## 4. Non-Functional Requirements

### NFR-1: 안전성

- 로직 변경 없음 (메타데이터, 링크만 변경)
- 백업 + 롤백 보장
- 구문 오류 방지 (LibCST, BeautifulSoup 사용)

### NFR-2: 신뢰성

- 실패 시 부분 롤백 (프로덕트 단위)
- 로그 파일 생성 (`logs/level2_agent_{timestamp}.log`)
- GitHub API Rate Limit 대응

### NFR-3: 유지보수성

- 모듈화된 구조 (`core/executors/`)
- 설정 파일로 제어 (`products.yaml`, `automation_rules.yaml`)
- 명확한 에러 메시지

### NFR-4: 확장성

- 새 액션 타입 추가 용이 (ActionExecutor 상속)
- 새 프로덕트 추가 용이 (products.yaml에만 추가)

### NFR-5: 성능

- 리포트 생성 시간에 +30초 이내 추가
- 프로덕트당 1개 PR (여러 액션 묶음)

---

## 5. Acceptance Criteria

### AC-1: 기본 흐름 성공

```gherkin
Given unified-agent가 리포트를 생성했고
  And 리포트에 "High Priority" 액션이 2개 있고
  And 두 액션 모두 자동화 가능할 때
When main.py를 실행하면
Then 2개 액션이 하나의 PR로 생성되고
  And PR이 GitHub에 존재하고
  And 로컬 브랜치는 원래 상태로 복구된다
```

### AC-2: 메타 타이틀 변경

```gherkin
Given 액션이 "QR Generator 메타 타이틀을 'Free QR Code Generator'로 변경"이고
When ActionExecutor가 실행되면
Then qr-generator/src/app/layout.tsx의 metadata.title이 변경되고
  And 구문 오류가 없고
  And 백업 파일이 생성된다
```

### AC-3: 실패 시 롤백

```gherkin
Given 액션 실행 중 에러가 발생했을 때
When 롤백이 트리거되면
Then 변경된 파일이 백업에서 복원되고
  And Git 브랜치가 삭제되고
  And 원래 브랜치로 체크아웃된다
```

### AC-4: 자동화 불가 액션 필터링

```gherkin
Given 액션이 "JavaScript 로직 변경"이고
When ActionValidator가 검증하면
Then 자동화 불가로 판정되고
  And 사용자에게 경고 메시지가 출력되고
  And 해당 액션은 건너뛴다
```

### AC-5: PR 형식

```gherkin
Given PR이 생성되었을 때
Then PR 제목이 "[SEO Agent] {N} Improvement(s) - {date}" 형식이고
  And PR 본문에 액션 목록이 포함되고
  And PR 본문에 테스트 체크리스트가 포함되고
  And PR 라벨에 "seo", "automated"가 추가된다
```

---

## 6. Scope

### In Scope

✅ **자동화 대상**:

- 메타 타이틀/설명 변경 (`<title>`, `<meta description>`, `metadata` 객체)
- 내부 링크 추가 (네비게이션 메뉴)
- Canonical URL 업데이트
- OG 태그 변경

✅ **프로덕트**:

- qr-generator
- convert-image

✅ **안전장치**:

- 백업/롤백
- Syntax Validation
- ActionValidator 필터링

✅ **설정**:

- products.yaml 확장 (GitHub repo 정보)
- .env 확장 (GITHUB_TOKEN)
- automation_rules.yaml 신규 생성

### Out of Scope

❌ **자동화 제외**:

- 컴포넌트 로직 변경
- API 엔드포인트 수정
- 데이터베이스 스키마
- CSS 대규모 변경
- 서드파티 스크립트 추가

❌ **Level 3 기능** (향후):

- 자동 머지
- A/B 테스트
  sd- 자동 이미지 최적화

❌ **비기능**:

- 웹 대시보드
- 실시간 모니터링
- 다국어 지원

---

## 7. Dependencies

### External Dependencies

**Python Libraries**:

- PyGithub >= 2.1.1 (GitHub API)
- GitPython >= 3.1.40 (Git 작업)
- libcst >= 1.1.0 (TypeScript/JavaScript AST 파싱)
- beautifulsoup4 >= 4.12.0 (HTML 파싱)
- lxml >= 5.0.0 (BeautifulSoup 백엔드)

**System Requirements**:

- Git 설치
- Node.js + npm (Syntax Validation용, 선택사항)

**GitHub**:

- Personal Access Token (권한: `repo`)
- qr-generator, convert-image 레포지토리 Write 권한

### Internal Dependencies

**기존 모듈**:

- `main.py` (통합 지점)
- `core/analyzers/comparative_analyzer.py` (리포트 생성)
- `config/products.yaml` (설정 읽기)

**신규 모듈**:

- `core/executors/action_extractor.py`
- `core/executors/action_validator.py`
- `core/executors/action_executor.py`
- `core/executors/meta_updater.py`
- `core/executors/link_injector.py`
- `core/executors/pr_creator.py`
- `core/executors/level2_agent.py`

---

## 8. Risks & Mitigations

### Risk 1: 프로덕션 코드 손상

**Impact**: High
**Probability**: Medium
**Mitigation**:

- 백업 자동 생성
- Context Manager로 롤백 보장
- Syntax Validation
- 안전한 파일만 변경 (ActionValidator)
- PR 생성만, 자동 머지는 안 함

### Risk 2: GitHub API Rate Limit

**Impact**: Medium
**Probability**: Low
**Mitigation**:

- 프로덕트당 1개 PR (여러 액션 묶음)
- Rate Limit 체크 후 대기
- 에러 로깅 및 다음 실행 시 재시도

### Risk 3: Git Conflict

**Impact**: Medium
**Probability**: Medium
**Mitigation**:

- 브랜치 생성 전 원격 최신 pull
- Conflict 발생 시 자동 롤백
- 사용자에게 수동 해결 요청

### Risk 4: 잘못된 메타데이터

**Impact**: Medium
**Probability**: Low (Claude가 생성)
**Mitigation**:

- Claude 프롬프트에 "정확하고 SEO 친화적인 메타데이터" 명시
- 길이 제한 (title: 60자, description: 160자)
- 사용자가 PR 리뷰 시 최종 확인

### Risk 5: LibCST 파싱 실패

**Impact**: Low
**Probability**: Low
**Mitigation**:

- Try-catch로 에러 처리
- 파싱 실패 시 해당 액션 건너뛰기
- 문자열 치환 fallback (간단한 경우)

---

## 9. Open Questions

### Q1: 프로덕트당 1개 PR vs 액션당 1개 PR?

**Current Decision**: 프로덕트당 1개 PR (one_per_product)
**Reason**: 리뷰 부담 감소, CI/CD 빌드 횟수 최소화
**Open**: 사용자 피드백에 따라 `products.yaml`에서 설정 가능하게

### Q2: Claude API 재호출 비용?

**Current Decision**: 정규식 우선, 실패 시 Claude fallback
**Reason**: 비용 절감
**Open**: 정규식 파싱 정확도가 낮으면 Claude 우선으로 변경

### Q3: Syntax Validation 필수인가?

**Current Decision**: 선택사항 (Extended Requirements)
**Reason**: 추가 시간 소요 (+10초), LibCST로 이미 구문 안전
**Open**: 실제 사용 후 필요성 판단

### Q4: 자동 머지는 언제?

**Current Decision**: Level 3 (Out of Scope)
**Reason**: 여러 주 검증 필요
**Open**: PR 리뷰 통과율이 95% 이상이면 고려

### Q5: 다른 액션 타입은?

**Examples**: JSON-LD 스키마, robots.txt, sitemap.xml
**Current Decision**: MVP 제외
**Open**: 사용자 요청 시 확장

---

## 10. Success Metrics

### Primary Metrics

**M-1: 실행률**

- **Baseline**: 리포트 액션 중 50% 실행됨 (수동)
- **Target**: 80% 자동 실행 (나머지는 자동화 불가)

**M-2: PR 성공률**

- **Target**: 95% 이상 (에러 없이 PR 생성)

**M-3: 리뷰 통과율**

- **Target**: 90% 이상 (사용자가 머지함)

### Secondary Metrics

**M-4: 시간 절약**

- **Baseline**: 리포트당 수동 작업 30분
- **Target**: 5분 (리뷰만)

**M-5: 지표 개선 속도**

- **Baseline**: 리포트 → 액션 실행까지 3일
- **Target**: 리포트 → PR 생성 즉시, 머지까지 1일

---

## 11. References

- [spec-flow](../../spec-flow/.claude/commands/spec-flow.md) - 워크플로우 가이드
- [Explore Agent Report](../../.exploration/github-pr-automation.md) - 기술 조사 결과
- [Plan Agent Report](../../.exploration/implementation-plan.md) - 상세 구현 계획

---

**Next Steps**:

1. ✅ spec.md 작성 완료
2. ⏭️ plan.md 작성 (기술 설계)
3. ⏭️ tasks.md 작성 (구현 분해)
4. ⏭️ TODO 파일 생성

---

_Spec-Flow: What & Why First, How Later_
