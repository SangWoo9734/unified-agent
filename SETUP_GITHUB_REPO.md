# unified-agent GitHub 저장소 설정 가이드

## 📋 개요

unified-agent를 독립된 GitHub 저장소로 만들고 GitHub Actions를 설정합니다.

---

## 🚀 1단계: GitHub 저장소 생성

### 1. GitHub에서 새 저장소 생성

https://github.com/new

- **Repository name**: `unified-agent`
- **Description**: `Multi-Product SEO Agent with automated PR generation`
- **Visibility**: Private (추천) 또는 Public
- ⚠️ **중요**: README, .gitignore, license 추가하지 않기 (빈 저장소로)

### 2. 로컬 Git 초기화

```bash
cd /Users/comento/agent-product/unified-agent

# Git 초기화
git init

# .gitignore 확인 (.env, __pycache__ 등 제외되어 있는지)
# 이미 있음

# 모든 파일 추가
git add .

# 첫 커밋
git commit -m "Initial commit: Level 1 + Level 2 Agent with GitHub Actions"

# 기본 브랜치 이름 설정
git branch -M main

# 원격 저장소 연결
git remote add origin https://github.com/YOUR_USERNAME/unified-agent.git

# 푸시
git push -u origin main
```

---

## 🔐 2단계: GitHub Secrets 설정

**Settings** → **Secrets and variables** → **Actions**

### 필수 Secrets

| Secret 이름 | 값 | 설명 |
|------------|-----|------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | 현재 .env의 ANTHROPIC_API_KEY |
| `GH_PAT` | `ghp_...` | [Personal Access Token 생성](#github-pat-생성) |
| `GSC_CREDENTIALS` | `{...}` | config/gsc_credentials.json 전체 내용 |

#### GitHub PAT 생성

1. https://github.com/settings/tokens
2. **Generate new token (classic)**
3. 권한 선택:
   - ✅ `repo` (전체)
   - ✅ `workflow`
4. 생성 후 토큰 복사 → `GH_PAT` Secret에 추가

---

## ⚙️ 3단계: GitHub Actions 워크플로우 수정

현재 워크플로우는 agent-product 전체 체크아웃을 가정합니다.
unified-agent 단독 저장소에 맞게 수정이 필요합니다.

### 3-1. 워크플로우 파일 위치 이동

```bash
# 이미 .github/workflows/seo-agent.yml이 있음
# (agent-product/.github에서 unified-agent/로 복사됨)
```

### 3-2. 워크플로우 수정

`.github/workflows/seo-agent.yml` 수정:

```yaml
name: SEO Agent - Automated Analysis & PR

on:
  schedule:
    - cron: '0 0 * * 1'  # 매주 월요일 오전 9시 (KST)
  workflow_dispatch:
    inputs:
      dry_run:
        description: 'Dry-run mode (true/false)'
        required: false
        default: 'false'

jobs:
  run-seo-agent:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout unified-agent
      uses: actions/checkout@v4

    # 프로덕트 체크아웃 (qr-generator, convert-image)
    - name: Checkout products
      run: |
        cd ..
        git clone https://github.com/SangWoo9734/qr-generator.git
        git clone https://github.com/SangWoo9734/convert-image.git
        ls -la

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
        cache: 'pip'

    - name: Install dependencies
      run: pip install -r requirements.txt

    - name: Setup Google credentials
      run: |
        mkdir -p config
        echo '${{ secrets.GSC_CREDENTIALS }}' > config/gsc_credentials.json

    - name: Run SEO Agent
      env:
        ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        GITHUB_TOKEN: ${{ secrets.GH_PAT }}
        ENABLE_AUTO_PR: ${{ github.event.inputs.dry_run == 'true' && 'false' || 'true' }}
      run: python main.py

    - name: Upload reports
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: seo-reports-${{ github.run_number }}
        path: reports/
        retention-days: 30

    - name: Upload backups
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: agent-backups-${{ github.run_number }}
        path: .agent_backups/
        retention-days: 7
```

### 3-3. action_executor.py 수정

프로덕트 경로 해석 로직을 수정합니다:

`core/executors/action_executor.py`:

```python
def _resolve_file_path(self, product_id: str, relative_path: str) -> Path:
    """
    프로덕트 ID와 상대 경로를 절대 경로로 변환합니다.
    """
    # workspace_root가 unified-agent인 경우
    if self.workspace_root.name in ["unified-agent", ".", ""]:
        # 부모 디렉토리(agent-product 또는 GitHub Actions runner)에서 프로덕트 찾기
        product_root = self.workspace_root.parent / product_id
    else:
        # 테스트 환경
        product_root = self.workspace_root / product_id

    file_path = product_root / relative_path
    return file_path
```

이미 올바르게 구현되어 있으므로 수정 불필요! ✅

---

## ✅ 4단계: 테스트

### 로컬 테스트

```bash
cd /Users/comento/agent-product/unified-agent

# Dry-run
python test_level2_live.py

# 실제 실행 (현재 로컬 구조에서)
ENABLE_AUTO_PR=true python main.py
```

### GitHub Actions 수동 실행

1. https://github.com/YOUR_USERNAME/unified-agent/actions
2. **SEO Agent - Automated Analysis & PR** 선택
3. **Run workflow** 클릭
4. `dry_run: true` 선택 (첫 테스트)
5. **Run workflow**

### 결과 확인

- **Actions 탭**: 실행 로그
- **Artifacts**: 리포트 및 백업 다운로드
- **qr-generator/convert-image 저장소**: 생성된 PR 확인

---

## 📊 구조 정리

### Before (현재)
```
agent-product/ (로컬)
├── unified-agent/
├── qr-generator/ (Git)
└── convert-image/ (Git)
```

### After (목표)
```
github.com/YOUR_USERNAME/unified-agent (새 Git 저장소)
└── GitHub Actions에서 실행
    ↓ (프로덕트 clone)
../qr-generator/ (체크아웃)
../convert-image/ (체크아웃)
```

---

## 🎯 체크리스트

- [ ] GitHub에 unified-agent 저장소 생성
- [ ] 로컬 Git 초기화 및 푸시
- [ ] GitHub Secrets 3개 추가
- [ ] 워크플로우 파일 확인 (프로덕트 clone 추가)
- [ ] 수동 실행 테스트 (dry-run)
- [ ] 실제 실행 및 PR 확인
- [ ] 자동 스케줄 대기 (월요일 오전 9시)

---

## 💡 대안: 로컬 구조 유지

만약 로컬 구조(`agent-product/` 아래 모두 유지)를 선호한다면:

1. **agent-product 전체를 모노레포로** (복잡함)
2. **symbolic link 사용** (GitHub Actions에서 복잡함)
3. **현재 구조 유지 + 수동 배포** (자동화 불가)

→ **추천: unified-agent를 별도 저장소로**

---

## 🆘 문제 해결

### "프로덕트를 찾을 수 없습니다"
- GitHub Actions에서 프로덕트 clone 단계 확인
- 경로가 `../qr-generator`인지 확인

### "GITHUB_TOKEN has insufficient permissions"
- `GH_PAT` Secret 확인
- Personal Access Token 권한 확인 (repo + workflow)

### 로컬에서는 잘 되는데 Actions에서 실패
- 경로 차이 확인
- `workspace_root` 로직 확인
- 로그에서 실제 경로 출력 추가

---

## 🎉 완료

unified-agent가 독립 저장소로 관리되고, GitHub Actions로 완전 자동화됩니다!
