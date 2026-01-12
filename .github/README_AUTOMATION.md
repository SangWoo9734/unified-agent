# 🤖 SEO Agent - 완전 자동화 가이드

이 문서는 SEO Agent의 **완전 자동화 설정**을 위한 통합 가이드입니다.

## 📊 자동화 개요

```
매주 월요일 오전 9시
       ↓
 GitHub Actions 실행
       ↓
┌─────────────────────┐
│  Level 1: 분석      │
│  - GSC 데이터 수집   │
│  - GA4 데이터 수집   │
│  - Trends 분석      │
│  - Claude AI 분석   │
│  - 리포트 생성      │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  Level 2: 자동화    │
│  - 액션 추출        │
│  - 안전성 검증      │
│  - 파일 수정        │
│  - Git commit       │
│  - PR 자동 생성     │
└─────────────────────┘
           ↓
    PR 생성 완료! 🎉
```

---

## 🚀 빠른 시작

### 1. GitHub Secrets 설정

**Settings** → **Secrets and variables** → **Actions**에서:

| Secret 이름 | 설명 | 필수 |
|------------|------|-----|
| `ANTHROPIC_API_KEY` | Claude API 키 | ✅ |
| `GH_PAT` | GitHub Personal Access Token | ✅ |
| `GSC_CREDENTIALS` | Google Search Console 인증 JSON | ✅ |

자세한 설정: [GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md)

### 2. 워크플로우 활성화

```bash
# 이 파일들을 main 브랜치에 커밋
git add .github/workflows/seo-agent.yml
git commit -m "Add GitHub Actions workflow for SEO Agent"
git push origin main
```

### 3. 수동 실행 테스트

1. GitHub → **Actions** 탭
2. **SEO Agent - Automated Analysis & PR** 선택
3. **Run workflow** 클릭

---

## 📁 프로젝트 구조

```
agent-product/
├── .github/
│   ├── workflows/
│   │   └── seo-agent.yml          # GitHub Actions 워크플로우
│   ├── GITHUB_ACTIONS_SETUP.md    # Secrets 설정 가이드
│   └── README_AUTOMATION.md       # 이 문서
│
├── unified-agent/                  # Level 1 + Level 2 Agent
│   ├── main.py                     # 메인 실행 파일
│   ├── core/
│   │   ├── collectors/             # Level 1: 데이터 수집
│   │   ├── analyzers/              # Level 1: Claude 분석
│   │   ├── level2_agent.py         # Level 2: 오케스트레이터
│   │   └── executors/              # Level 2: 액션 실행
│   │       ├── action_extractor.py
│   │       ├── action_validator.py
│   │       ├── meta_updater.py
│   │       └── pr_creator.py
│   ├── config/
│   │   ├── products.yaml           # 프로덕트 설정
│   │   └── gsc_credentials.json    # Google 인증 (로컬)
│   ├── reports/                    # 생성된 리포트
│   └── .agent_backups/             # 파일 백업
│
├── qr-generator/                   # 프로덕트 1
├── convert-image/                  # 프로덕트 2
└── ...                             # 기타 프로덕트
```

---

## ⚙️ 실행 모드

### 로컬 실행

```bash
cd unified-agent

# Level 1만 (리포트 생성)
python main.py

# Level 1 + Level 2 (PR 자동 생성)
ENABLE_AUTO_PR=true python main.py

# Dry-run (시뮬레이션)
python test_level2_live.py
```

### GitHub Actions 실행

**자동**:
- 매주 월요일 오전 9시 (KST)

**수동**:
- Actions 탭 → Run workflow

---

## 🛡️ 안전장치

Level 2 Agent는 다음 안전장치를 포함합니다:

### 1. 화이트리스트 기반 검증
```python
SAFE_ACTION_TYPES = {
    "update_meta_title",
    "update_meta_description",
    "add_internal_link",
    "update_canonical_url",
    "update_og_tags"
}

SAFE_FILE_PATTERNS = [
    r".*layout\.tsx$",
    r".*index\.html$",
    r".*Header\.tsx$",
    ...
]
```

### 2. 보안 패턴 감지
- XSS 패턴 (`<script>`, `javascript:`)
- Code Injection (`eval()`, `innerHTML`)
- Path Traversal (`..`, 절대 경로)

### 3. 자동 백업
- 모든 파일 수정 전 자동 백업
- `.agent_backups/` 디렉토리에 저장
- GitHub Actions에서 아티팩트로 업로드 (7일 보관)

### 4. Git 롤백
- PR 생성 실패 시 자동 브랜치 삭제
- 로컬 변경 사항 롤백

---

## 📊 모니터링

### 실행 로그
- **GitHub Actions** → 워크플로우 실행 클릭
- 각 step별 상세 로그 확인

### 생성된 아티팩트
| 아티팩트 | 내용 | 보관 기간 |
|---------|------|----------|
| `seo-reports-*` | 분석 리포트 | 30일 |
| `agent-backups-*` | 파일 백업 | 7일 |

### 생성된 PR
- 각 프로덕트 저장소의 Pull Requests 탭
- 제목: `[SEO Agent] {product}: N Improvements - YYYY-MM-DD`
- 라벨: `seo`, `automated`

---

## 🔧 커스터마이징

### 실행 주기 변경

`.github/workflows/seo-agent.yml`:

```yaml
on:
  schedule:
    # 매주 월요일 오전 9시 (기본)
    - cron: '0 0 * * 1'

    # 매일 오전 9시
    # - cron: '0 0 * * *'

    # 매월 1일 오전 9시
    # - cron: '0 0 1 * *'
```

### 지원 액션 타입 추가

`unified-agent/core/executors/action_validator.py`:

```python
SAFE_ACTION_TYPES = {
    "update_meta_title",
    "update_meta_description",
    # 새로운 액션 타입 추가
    "add_structured_data",
    "optimize_images",
}
```

### 프로덕트 추가

`unified-agent/config/products.yaml`:

```yaml
products:
  new-product:
    name: "New Product"
    gsc_property_url: "https://new-product.com"
    ga4_property_id: "123456789"
```

---

## 📈 성과 측정

### Level 1 리포트
- `unified-agent/reports/comparison/`
- 주간/격주 비교 분석
- Claude AI 인사이트

### Level 2 PR
- 실행된 액션 수
- 변경된 파일 목록
- 예상 SEO 효과

### 실제 효과
- **GSC**: 검색 노출 증가
- **GA4**: 트래픽 증가
- **Conversion**: 전환율 개선

---

## 🎯 로드맵

### 완료 ✅
- Level 1: 데이터 수집 및 분석
- Level 2: PR 자동화
- GitHub Actions 통합
- 안전장치 구현

### 예정 🚧
- **TODO-11**: LinkInjector (내부 링크 자동 추가)
- **CanonicalUpdater**: Canonical URL 설정
- **OGTagUpdater**: Open Graph 태그 업데이트
- **이미지 최적화**: Alt text, 압축
- **구조화된 데이터**: Schema.org 자동 생성

---

## 💡 팁

### 1. 처음 실행 시
- Dry-run으로 먼저 테스트
- 생성된 PR을 직접 리뷰
- 문제 없으면 머지

### 2. 정기 실행 시
- 매주 월요일 오전에 PR 확인
- 변경 사항 검토
- 빌드 및 테스트 통과 확인
- 문제 없으면 자동 머지 설정 가능

### 3. 롤백이 필요한 경우
```bash
# 백업에서 복구
cp .agent_backups/TIMESTAMP_filename .../filename

# Git으로 되돌리기
git checkout main path/to/file
```

---

## 🆘 문제 해결

자세한 트러블슈팅: [GITHUB_ACTIONS_SETUP.md](./GITHUB_ACTIONS_SETUP.md#-트러블슈팅)

### 빠른 체크리스트

- [ ] GitHub Secrets 모두 설정됨
- [ ] 워크플로우 파일이 main 브랜치에 있음
- [ ] `products.yaml` 설정 완료
- [ ] Google 인증 파일 유효함
- [ ] 각 프로덕트가 Git 저장소임
- [ ] GitHub PAT 권한 충분함 (repo + workflow)

---

## 📞 지원

- **Issues**: GitHub Issues에 문제 보고
- **문서**: `.github/GITHUB_ACTIONS_SETUP.md` 참고
- **로그**: Actions 탭에서 실행 로그 확인

---

## 🎉 결론

**SEO Agent가 이제 완전히 자동화되었습니다!**

- ✅ 매주 자동 데이터 수집 및 분석
- ✅ Claude AI 기반 인사이트 생성
- ✅ 안전한 자동 파일 수정
- ✅ GitHub PR 자동 생성
- ✅ 백업 및 롤백 기능

**단 한 번의 설정으로, 앞으로는 PR만 리뷰하면 됩니다!** 🚀
