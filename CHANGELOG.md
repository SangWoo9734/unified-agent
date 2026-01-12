# Changelog

## [Unreleased] - Repository Dispatch 마이그레이션 계획

### 🎯 의사결정: Clone 방식 → Repository Dispatch 방식

**배경:**
- 현재 방식: unified-agent가 매번 모든 프로덕트를 clone
- 문제점: 프로덕트 증가 시 clone 시간 급증 (2개 → 2분, 10개 → 10분)

**검토한 대안:**
1. ✅ Shallow Clone (fetch-depth: 1) - 50% 개선, 간단
2. ✅ Sparse Checkout - 90% 개선, 파일 미리 알아야 함
3. ⭐ **Repository Dispatch** - 100% 개선, 확장 가능
4. ✅ GitHub App - 오버엔지니어링

**선택:** Repository Dispatch

**이유:**
- Clone 시간 0초 (불필요)
- 프로덕트 독립적 관리
- 무한 확장 가능 (100개도 OK)
- 각 프로덕트 커스터마이징 가능

**구현 계획:**
1. unified-agent: 리포트 생성 → Dispatch 이벤트 전송
2. 각 프로덕트: Dispatch 수신 → 파일 수정 → PR 생성
3. 테스트 및 배포

---

## [2026-01-13] - Level 2 Agent 구현 완료 🎉

### Added - Level 2: PR 자동화

#### Core Components
- **ActionExtractor**: 리포트에서 액션 자동 추출
  - Regex 기반 파싱 (primary)
  - Claude API fallback (optional)

- **ActionValidator**: 안전성 검증
  - 화이트리스트 기반 (action_type, file patterns)
  - XSS/Code Injection 패턴 감지
  - Path Traversal 방지

- **MetaUpdater**: 파일 자동 수정
  - TSX 파일: Regex 기반 (LibCST는 TypeScript 미지원)
  - HTML 파일: BeautifulSoup
  - 자동 백업 및 롤백

- **PRCreator**: GitHub PR 자동 생성
  - GitPython: 브랜치 생성, commit, push
  - PyGithub: PR 생성, 라벨 추가
  - Context Manager로 Git 롤백

- **Level2Agent**: 오케스트레이터
  - 전체 파이프라인 조율
  - Dry-run 모드 지원
  - 여러 리포트 일괄 처리

#### GitHub Actions Integration
- **워크플로우**: `.github/workflows/seo-agent.yml`
  - 매주 월요일 오전 9시 자동 실행
  - 수동 실행 지원 (dry_run 옵션)
  - 아티팩트 업로드 (리포트 30일, 백업 7일)

- **Secrets 설정**:
  - `ANTHROPIC_API_KEY`: Claude API
  - `GH_PAT`: Personal Access Token (repo + workflow)
  - `GSC_CREDENTIALS`: Google Search Console 인증

#### Documentation
- `README.md`: Level 2 Agent 통합 가이드
- `SETUP_GITHUB_REPO.md`: 저장소 설정 가이드
- `.github/GITHUB_ACTIONS_SETUP.md`: Secrets 설정 가이드
- `.github/README_AUTOMATION.md`: 자동화 통합 가이드
- `LEVEL2_IMPLEMENTATION_SUMMARY.md`: 구현 상세
- `setup_git.sh`: Git 초기화 자동화 스크립트

### Changed

#### Main Integration
- `main.py`: Level 2 Agent 통합
  - `ENABLE_AUTO_PR` 환경변수 체크
  - 리포트 생성 후 자동으로 Level2Agent 실행
  - PR 생성 결과 출력

#### Dependencies
- `requirements.txt`: Level 2 의존성 추가
  - PyGithub>=2.1.1
  - GitPython>=3.1.40
  - libcst>=1.1.0
  - beautifulsoup4>=4.12.0
  - lxml>=5.0.0

#### Configuration
- `.env.example`: Level 2 환경변수 추가
  - `GITHUB_TOKEN`
  - `ENABLE_AUTO_PR`

- `.gitignore`: 백업 디렉토리 추가
  - `.agent_backups/`

### Fixed

#### GitHub Actions 워크플로우
- **[2026-01-13 01:20]** Clone 방식 변경
  - ❌ Before: `git clone https://...` (실패)
  - ✅ After: `actions/checkout@v4` (성공)

- **[2026-01-13 01:26]** Private 저장소 접근
  - Issue: exit code 128, authentication 실패
  - Solution: `token: ${{ secrets.GH_PAT }}` 추가

### Technical Decisions

#### 1. LibCST → Regex (TSX 파싱)
- **Issue**: LibCST는 TypeScript를 파싱하지 못함
- **Decision**: TSX는 Regex, HTML은 BeautifulSoup
- **Trade-off**:
  - ✅ 실제로 동작함
  - ⚠️ 복잡한 코드는 파싱 어려움 (향후 개선)

#### 2. Regex Primary, Claude Fallback (리포트 파싱)
- **Decision**: 비용 절감 및 성능 향상
- **Fallback**: 복잡한 리포트는 Claude API 사용 가능

#### 3. 화이트리스트 기반 보안
- **Approach**: Deny by default
- **Benefit**: 안전하게 시작, 점진적 확대

#### 4. Context Manager 패턴
- **Usage**: FileBackupManager, PRCreator
- **Benefit**: 자동 백업/롤백, 안전한 리소스 관리

### Testing

#### Live Test Results
- ✅ Dry-run 테스트: 2개 액션 추출 및 시뮬레이션
- ✅ 전체 플로우 테스트: 실제 파일 수정 및 PR 생성
- ✅ PR 생성 성공: https://github.com/SangWoo9734/qr-generator/pull/1

#### Test Coverage
- FileBackupManager: 백업/복구/Context Manager
- ActionExtractor: Regex 파싱
- ActionValidator: 화이트리스트, XSS 탐지
- MetaUpdater: TSX/HTML 파일 수정
- PRCreator: Git 작업, PR 생성
- Level2Agent: 전체 통합

### Completed TODOs (Critical Path)

- ✅ TODO-01: Setup & Dependencies
- ✅ TODO-02: Core Data Classes
- ✅ TODO-03: FileBackupManager
- ✅ TODO-05: ActionExtractor
- ✅ TODO-06: ActionValidator
- ✅ TODO-07: MetaUpdater
- ✅ TODO-08: PRCreator
- ✅ TODO-09: Level2Agent Orchestrator
- ✅ TODO-10: main.py Integration

### Remaining TODOs (Optional)

- ⏳ TODO-11: LinkInjector (Medium Priority)
- ⏳ TODO-12: Unit Tests (Medium Priority)
- ⏳ TODO-13: Integration Test (Medium Priority)
- ⏳ TODO-14: Dry-run Mode (Low Priority)
- ⏳ TODO-15: Documentation (Low Priority)

---

## [2026-01-11] - Level 1: 초기 구현

### Added - Level 1: 데이터 수집 및 분석

#### Data Collectors
- `GSCCollector`: Google Search Console 데이터 수집
- `GA4Collector`: Google Analytics 4 데이터 수집
- `TrendsCollector`: Google Trends 데이터 수집
- `AdSenseCollector`: AdSense 수익 데이터 (환경변수 기반)

#### Analyzers
- `ComparativeAnalyzer`: Claude AI 기반 비교 분석
  - 프로덕트 간 성과 비교
  - 리소스 배분 추천
  - 교차 프로모션 기회 발견

#### Configuration
- `config/products.yaml`: 프로덕트 설정
- `config/gsc_credentials.json`: Google 인증
- `.env`: 환경변수 설정

#### Reports
- `reports/comparison/`: 통합 비교 리포트
- Markdown 형식, Claude AI 분석 포함

---

## 다음 단계

### Repository Dispatch 마이그레이션 (계획 중)

**Phase 1: unified-agent 수정**
- [ ] Clone 로직 제거
- [ ] Repository Dispatch 전송 로직 추가
- [ ] 액션 데이터 JSON 포맷 정의

**Phase 2: 프로덕트 워크플로우**
- [ ] qr-generator: `.github/workflows/seo-pr.yml` 추가
- [ ] convert-image: `.github/workflows/seo-pr.yml` 추가
- [ ] Dispatch 이벤트 수신 로직
- [ ] 파일 수정 및 PR 생성 로직

**Phase 3: 테스트 및 배포**
- [ ] 전체 플로우 테스트
- [ ] 문서 업데이트
- [ ] 마이그레이션 가이드 작성

---

## 버전 히스토리

- **v2.0.0** (계획): Repository Dispatch 방식
- **v1.0.0** (2026-01-13): Level 2 Agent (PR 자동화) + GitHub Actions
- **v0.1.0** (2026-01-11): Level 1 Agent (데이터 수집 및 분석)
