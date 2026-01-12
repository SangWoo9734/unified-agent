# 🤖 Unified Multi-Product SEO Agent

자동화된 SEO 분석 및 PR 생성 시스템

## 🎯 개요

Unified Agent는 여러 프로덕트(QR Generator, Convert Image 등)의 SEO 데이터를 자동으로 수집, 분석하고 **개선 사항을 자동으로 실행**하는 AI 에이전트입니다.

### 주요 기능

#### 🔍 Level 1: 데이터 수집 및 분석
- **통합 데이터 수집**: GSC, GA4, Google Trends, AdSense
- **AI 비교 분석**: Claude가 프로덕트 간 성과 비교 및 인사이트 제공
- **리소스 배분 추천**: 데이터 기반 마케팅 리소스 배분 제안
- **교차 프로모션 발견**: 프로덕트 간 시너지 기회 식별
- **자동 리포트 생성**: 주간/격주 통합 분석 리포트

#### ⚡ Level 2: PR 자동화 (NEW!)
- **액션 자동 추출**: 리포트에서 실행 가능한 개선 사항 추출
- **안전성 검증**: 화이트리스트 + XSS 탐지
- **파일 자동 수정**: 메타 태그 등 자동 업데이트 (백업 포함)
- **GitHub PR 자동 생성**: Git commit, push, PR 생성까지 완전 자동화

#### 🤖 GitHub Actions: 완전 자동화
- **스케줄 실행**: 매주 자동 실행
- **아티팩트 저장**: 리포트 및 백업 자동 저장
- **실패 알림**: 에러 발생 시 알림

---

## 🚀 빠른 시작

### 로컬 실행

```bash
# 1. 의존성 설치
cd unified-agent
pip install -r requirements.txt

# 2. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 API 키 입력

# 3. Google 인증 설정
cp ../convert-image/agent/config/gsc_credentials.json config/

# 4. 프로덕트 설정
# config/products.yaml 파일 수정

# 5. 실행
# Level 1만 (리포트 생성)
python main.py

# Level 1 + Level 2 (PR 자동 생성)
ENABLE_AUTO_PR=true python main.py
```

### GitHub Actions로 자동화

```bash
# 1. Git 저장소 설정
./setup_git.sh

# 2. GitHub에 푸시
git push -u origin main

# 3. GitHub Secrets 설정 (웹에서)
# - ANTHROPIC_API_KEY
# - GH_PAT (Personal Access Token)
# - GSC_CREDENTIALS

# 4. 워크플로우 활성화
# Actions 탭 → Run workflow
```

자세한 가이드: **[SETUP_GITHUB_REPO.md](./SETUP_GITHUB_REPO.md)**

---

## 📊 실행 플로우

```
매주 월요일 오전 9시 (GitHub Actions)
    ↓
┌──────────────────────┐
│  Level 1: 분석       │
│  - GSC 데이터 수집   │
│  - GA4 데이터 수집   │
│  - Trends 분석       │
│  - Claude AI 분석    │
│  - 리포트 생성       │
└───────────┬──────────┘
            ↓
┌──────────────────────┐
│  Level 2: 자동화     │
│  - 액션 추출         │
│  - 안전성 검증       │
│  - 파일 자동 수정    │
│  - Git commit        │
│  - PR 자동 생성      │
└──────────────────────┘
            ↓
       PR 완성! 🎉
```

---

## 🛡️ 안전장치

Level 2 Agent는 다음 안전장치를 포함합니다:

### 1. 화이트리스트 기반
- 허용된 액션 타입만 실행
- 허용된 파일 패턴만 수정

### 2. 보안 패턴 감지
- XSS: `<script>`, `javascript:`
- Code Injection: `eval()`, `innerHTML`
- Path Traversal: `..`, 절대 경로

### 3. 자동 백업
- 모든 파일 수정 전 자동 백업
- `.agent_backups/` 디렉토리에 저장
- 롤백 기능 제공

---

## 📁 프로젝트 구조

```
unified-agent/
├── .github/
│   └── workflows/
│       └── seo-agent.yml          # GitHub Actions 워크플로우
├── core/
│   ├── collectors/                 # Level 1: 데이터 수집
│   │   ├── gsc_collector.py
│   │   ├── ga4_collector.py
│   │   ├── trends_collector.py
│   │   └── adsense_collector.py
│   ├── analyzers/                  # Level 1: 분석
│   │   └── comparative_analyzer.py
│   ├── executors/                  # Level 2: 액션 실행
│   │   ├── models.py
│   │   ├── action_extractor.py
│   │   ├── action_validator.py
│   │   ├── meta_updater.py
│   │   └── pr_creator.py
│   ├── level2_agent.py             # Level 2: 오케스트레이터
│   └── utils/
├── config/
│   ├── products.yaml               # 프로덕트 설정
│   └── gsc_credentials.json        # Google 인증 (gitignore)
├── reports/                        # 생성된 리포트
├── .agent_backups/                 # 파일 백업 (gitignore)
├── main.py                         # 메인 실행 파일
├── requirements.txt
├── .env.example
├── setup_git.sh                    # Git 초기화 스크립트
└── README.md
```

---

## 📝 환경변수 설정

### .env

```bash
# Anthropic API (필수)
ANTHROPIC_API_KEY=sk-ant-...

# GitHub (Level 2)
GITHUB_TOKEN=ghp_...              # Personal Access Token (repo + workflow 권한)
ENABLE_AUTO_PR=false              # true로 변경 시 PR 자동 생성

# AdSense (선택)
ADSENSE_REVENUE=125.50
ADSENSE_IMPRESSIONS=50000
ADSENSE_CLICKS=250
```

### config/products.yaml

```yaml
products:
  qr-generator:
    name: "QR Generator"
    gsc_property_url: "https://qr-generator.com"
    ga4_property_id: "123456789"
    analysis_days: 7

  convert-image:
    name: "Image Converter"
    gsc_property_url: "https://convert-image.com"
    ga4_property_id: "987654321"
    analysis_days: 7
```

---

## 🧪 테스트

### 로컬 테스트

```bash
# Dry-run (파일 변경 없음)
python test_level2_live.py

# 전체 플로우 (실제 PR 생성)
python test_full_flow.py
```

### GitHub Actions 테스트

1. https://github.com/YOUR_USERNAME/unified-agent/actions
2. "SEO Agent - Automated Analysis & PR" 선택
3. Run workflow 클릭
4. dry_run: true 선택 (첫 테스트)

---

## 📊 생성되는 리포트 예시

### 통합 리포트

`reports/comparison/YYYY-MM-DD_multi_product_analysis.md`

```markdown
# Multi-Product Analysis Report

## 📊 Executive Summary
- QR Generator: 12,450 클릭, 광고 수익 $18.50
- Convert Image: 8,230 클릭

## High Priority Actions

1. **[qr-generator]** Update meta title to "Free QR Code Generator"
   - File: `src/app/layout.tsx`
   - Expected Impact: 검색 노출 20% 증가

2. **[convert-image]** Update meta description
   - File: `src/app/layout.tsx`
   - Expected Impact: CTR 15% 증가
```

### 생성된 PR

**제목**: `[SEO Agent] qr-generator: 2 Improvements - 2026-01-13`

**본문**:
```markdown
## 🤖 SEO Agent - Automated Improvements

**Product**: `qr-generator`

## 📋 Applied Actions
1. 메타 타이틀 변경 완료
2. 메타 설명 변경 완료

## ✅ Test Checklist
- [ ] 메타 태그 확인
- [ ] 페이지 렌더링 확인
- [ ] 빌드 테스트
```

**실제 PR 예시**: https://github.com/SangWoo9734/qr-generator/pull/1

---

## 🔧 커스터마이징

### 실행 주기 변경

`.github/workflows/seo-agent.yml`:

```yaml
on:
  schedule:
    # 매주 월요일 (기본)
    - cron: '0 0 * * 1'

    # 매일
    # - cron: '0 0 * * *'

    # 매월 1일
    # - cron: '0 0 1 * *'
```

### 지원 액션 타입 추가

`core/executors/action_validator.py`:

```python
SAFE_ACTION_TYPES = {
    "update_meta_title",
    "update_meta_description",
    # 새 액션 추가
    "add_structured_data",
}
```

---

## 🆘 문제 해결

### "ANTHROPIC_API_KEY not found"
- `.env` 파일에 API 키 추가
- GitHub Secrets 확인 (Actions 사용 시)

### "GITHUB_TOKEN has insufficient permissions"
- Personal Access Token 사용 (`GH_PAT`)
- repo + workflow 권한 확인

### "프로덕트를 찾을 수 없습니다"
- GitHub Actions: 프로덕트 clone step 확인
- 로컬: 프로덕트 경로 확인

자세한 가이드: [SETUP_GITHUB_REPO.md](./SETUP_GITHUB_REPO.md)

---

## 📈 비용

- **Google APIs**: 무료 (할당량 내)
- **Claude API**: 실행당 약 $0.10~0.20
- **GitHub Actions**: 무료 (Public 저장소) 또는 무료 할당량 내
- **매주 실행 시**: 월 $0.80~1.60

---

## 🎯 로드맵

### 완료 ✅
- Level 1: 데이터 수집 및 분석
- Level 2: PR 자동화
- GitHub Actions 통합
- 안전장치 구현

### 계획 중 🚧
- LinkInjector: 내부 링크 자동 추가
- CanonicalUpdater: Canonical URL 설정
- OGTagUpdater: Open Graph 태그 업데이트
- 이미지 최적화: Alt text, 압축
- 구조화된 데이터: Schema.org

---

## 📄 문서

- **[SETUP_GITHUB_REPO.md](./SETUP_GITHUB_REPO.md)** - GitHub 저장소 설정 가이드
- **[.github/GITHUB_ACTIONS_SETUP.md](./.github/GITHUB_ACTIONS_SETUP.md)** - GitHub Actions Secrets 설정
- **[.github/README_AUTOMATION.md](./.github/README_AUTOMATION.md)** - 자동화 통합 가이드
- **[LEVEL2_IMPLEMENTATION_SUMMARY.md](./LEVEL2_IMPLEMENTATION_SUMMARY.md)** - Level 2 구현 상세

---

## 🙏 기여

이슈 및 PR 환영합니다!

---

**Made with ❤️ and Claude AI** 🚀
