# GitHub Actions 설정 가이드

이 문서는 SEO Agent를 GitHub Actions로 자동 실행하기 위한 설정 가이드입니다.

## 📋 사전 준비

1. ✅ `.github/workflows/seo-agent.yml` 파일 생성 완료
2. ✅ Level 2 Agent 구현 완료
3. ⏳ GitHub Secrets 설정 필요

---

## 🔐 GitHub Secrets 설정

GitHub Secrets는 민감한 정보(API 키, 인증 정보 등)를 안전하게 저장하는 곳입니다.

### 설정 방법

1. GitHub 저장소로 이동
2. **Settings** → **Secrets and variables** → **Actions** 클릭
3. **New repository secret** 클릭하여 아래 Secrets 추가

---

### 필수 Secrets

#### 1. `ANTHROPIC_API_KEY`
- **설명**: Claude API 키
- **값**: `sk-ant-...` (현재 .env에 있는 키 복사)
- **획득 방법**: https://console.anthropic.com/settings/keys

#### 2. `GH_PAT` (GitHub Personal Access Token)
- **설명**: PR 생성용 GitHub 토큰
- **값**: `ghp_...` (현재 .env의 GITHUB_TOKEN)
- **획득 방법**:
  1. https://github.com/settings/tokens
  2. **Generate new token (classic)** 클릭
  3. 권한 선택:
     - ✅ `repo` (전체)
     - ✅ `workflow`
  4. 토큰 생성 및 복사

**⚠️ 주의**: `GITHUB_TOKEN`은 워크플로우 자체 권한만 있어 PR 생성 불가. 반드시 PAT(Personal Access Token) 사용!

#### 3. `GSC_CREDENTIALS`
- **설명**: Google Search Console 인증 JSON
- **값**: 현재 `unified-agent/config/gsc_credentials.json` 파일 내용 전체 복사
- **포맷**:
  ```json
  {
    "type": "service_account",
    "project_id": "...",
    "private_key_id": "...",
    "private_key": "...",
    ...
  }
  ```

---

### 선택 Secrets (AdSense 사용 시)

#### 4. `ADSENSE_REVENUE`
- **설명**: AdSense 수익 (수동 입력용)
- **값**: 예) `125.50`

#### 5. `ADSENSE_IMPRESSIONS`
- **설명**: AdSense 노출 수
- **값**: 예) `50000`

#### 6. `ADSENSE_CLICKS`
- **설명**: AdSense 클릭 수
- **값**: 예) `250`

---

## ⚙️ 워크플로우 설정 확인

### 1. 스케줄 설정

기본: **매주 월요일 오전 9시 (KST)**

변경하려면 `.github/workflows/seo-agent.yml` 수정:

```yaml
on:
  schedule:
    # 매주 월요일 오전 0시 (UTC) = 오전 9시 (KST)
    - cron: '0 0 * * 1'

    # 격주 월요일: 아래로 변경
    # - cron: '0 0 * * 1'
    #   # + 격주 체크 로직 추가 필요
```

### 2. Dry-run 모드

수동 실행 시 Dry-run 옵션 제공:
- `dry_run: true` → 파일 변경 없이 시뮬레이션만
- `dry_run: false` → 실제 PR 생성 (기본값)

---

## 🚀 실행 방법

### 자동 실행
- 매주 월요일 오전 9시에 자동 실행
- GitHub Actions 탭에서 실행 로그 확인

### 수동 실행
1. GitHub 저장소 → **Actions** 탭
2. **SEO Agent - Automated Analysis & PR** 선택
3. **Run workflow** 클릭
4. Dry-run 여부 선택 후 **Run workflow**

---

## 📊 실행 결과 확인

### 1. 실행 로그
- **Actions** 탭 → 최신 워크플로우 실행 클릭
- 각 step별 로그 확인 가능

### 2. 생성된 아티팩트
다음 파일들이 자동 저장됩니다:

- **seo-reports-{run_number}**: 생성된 리포트 (30일 보관)
- **agent-backups-{run_number}**: 파일 백업 (7일 보관)

다운로드:
1. 워크플로우 실행 페이지
2. **Artifacts** 섹션에서 다운로드

### 3. 생성된 PR
- PR이 성공적으로 생성되면 각 프로덕트 저장소에 PR 생성
- 예: `https://github.com/{owner}/qr-generator/pulls`
- PR 제목: `[SEO Agent] qr-generator: N Improvements - YYYY-MM-DD`

---

## 🔧 트러블슈팅

### 문제 1: "ANTHROPIC_API_KEY not found"
- **원인**: Secret이 설정되지 않음
- **해결**: Settings → Secrets에서 `ANTHROPIC_API_KEY` 추가

### 문제 2: "GITHUB_TOKEN has insufficient permissions"
- **원인**: 기본 GITHUB_TOKEN은 PR 생성 권한 없음
- **해결**: `GH_PAT` Secret에 Personal Access Token 설정

### 문제 3: "GSC credentials file not found"
- **원인**: `GSC_CREDENTIALS` Secret 미설정
- **해결**: gsc_credentials.json 내용을 `GSC_CREDENTIALS` Secret에 추가

### 문제 4: 워크플로우가 실행되지 않음
- **원인**:
  - 워크플로우 파일이 main 브랜치에 없음
  - cron 시간이 아직 안 됨
  - 워크플로우가 비활성화됨
- **해결**:
  - main 브랜치에 `.github/workflows/seo-agent.yml` 커밋
  - 수동 실행으로 테스트
  - Actions 탭에서 워크플로우 활성화 확인

---

## ✅ 설정 체크리스트

다음 항목들을 확인하세요:

- [ ] `ANTHROPIC_API_KEY` Secret 추가
- [ ] `GH_PAT` Secret 추가 (repo + workflow 권한)
- [ ] `GSC_CREDENTIALS` Secret 추가
- [ ] `.github/workflows/seo-agent.yml` 파일이 main 브랜치에 있음
- [ ] `unified-agent/config/products.yaml` 설정 완료
- [ ] 수동 실행으로 테스트 완료
- [ ] 첫 PR 생성 확인 및 리뷰 완료

---

## 📝 다음 단계

1. **Secrets 설정** (위 가이드 참고)
2. **수동 실행 테스트**
   ```bash
   # 로컬에서도 테스트 가능
   cd unified-agent
   ENABLE_AUTO_PR=true python main.py
   ```
3. **첫 자동 실행 대기** (다음 월요일 오전 9시)
4. **PR 리뷰 및 머지**
5. **모니터링**: 매주 Actions 탭에서 실행 로그 확인

---

## 🎉 완료!

이제 SEO Agent가 매주 자동으로:
1. 데이터 수집 (GSC, GA4, Trends)
2. Claude AI 분석
3. 리포트 생성
4. 액션 추출 및 실행
5. **GitHub PR 자동 생성**

까지 완전 자동화됩니다! 🚀
