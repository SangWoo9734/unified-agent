# TODO-01: Setup & Dependencies

**Status**: 🔴 Not Started
**Priority**: HIGH
**Complexity**: Low
**Estimated Time**: 30 min
**Assigned**: Level 2 Agent Implementation

---

## Business Value

**Goal**: Level 2 Agent 구현을 위한 기본 인프라 구축

**Impact**:
- 모든 후속 작업의 기반
- 의존성 충돌 사전 방지
- 프로덕션 환경 설정 표준화

**Why This Matters**:
Level 2 Agent는 PyGithub, GitPython, LibCST 등 새로운 라이브러리에 의존합니다. 이 작업을 먼저 완료해야 이후 모든 구현 작업이 원활하게 진행됩니다.

---

## Description

프로젝트에 필요한 Python 라이브러리를 설치하고, 환경 설정 파일을 업데이트합니다.

**Core Libraries**:
- PyGithub: GitHub API 통합
- GitPython: Git 작업 자동화
- libcst: TypeScript/JavaScript AST 파싱
- beautifulsoup4 + lxml: HTML 파싱

---

## Tasks

### 1. requirements.txt 업데이트
- [ ] `requirements.txt` 파일 열기
- [ ] 다음 라이브러리 추가:
  ```
  # Level 2 Agent Dependencies
  PyGithub>=2.1.1          # GitHub API
  GitPython>=3.1.40        # Git operations
  libcst>=1.1.0            # Code AST parsing
  beautifulsoup4>=4.12.0   # HTML parsing
  lxml>=5.0.0              # BeautifulSoup backend
  ```
- [ ] 파일 저장

### 2. 의존성 설치
- [ ] 터미널에서 실행:
  ```bash
  cd /Users/comento/agent-product/unified-agent
  pip install -r requirements.txt
  ```
- [ ] 설치 완료 확인

### 3. Import 테스트
- [ ] Python 인터프리터에서 테스트:
  ```python
  import github
  import git
  import libcst
  from bs4 import BeautifulSoup
  print("All imports successful!")
  ```
- [ ] 에러 없이 import 성공 확인

### 4. .env.example 업데이트
- [ ] `.env.example` 파일 열기
- [ ] 다음 환경변수 추가:
  ```bash
  # GitHub Token (Level 2 Agent)
  # Permissions: repo (full), workflow
  GITHUB_TOKEN=ghp_your_github_personal_access_token

  # Level 2 Agent 활성화
  ENABLE_AUTO_PR=true  # false로 설정 시 리포트만 생성
  ```
- [ ] 주석으로 설정 방법 안내 추가

### 5. .gitignore 업데이트
- [ ] `.gitignore` 파일 열기
- [ ] 백업 디렉토리 추가:
  ```
  # Level 2 Agent backups
  .agent_backups/
  ```
- [ ] 저장

---

## Acceptance Criteria

- [x] requirements.txt에 5개 라이브러리 추가됨
- [ ] `pip install -r requirements.txt` 성공
- [ ] 모든 라이브러리 import 가능
- [ ] .env.example에 GITHUB_TOKEN, ENABLE_AUTO_PR 문서화
- [ ] .gitignore에 .agent_backups/ 추가
- [ ] 설치 확인 스크린샷 또는 로그

---

## Dependencies

**Depends on**: None (첫 작업)
**Blocks**: TODO-02, TODO-03, TODO-05, TODO-06, TODO-07, TODO-08

---

## Technical Notes

### PyGithub vs gh CLI
- PyGithub 선택 이유: Python 코드 내 직접 통합, API 전체 제어
- gh CLI는 사용하지 않음

### LibCST vs AST
- LibCST: Concrete Syntax Tree, 포매팅 유지
- AST: Abstract Syntax Tree, 포매팅 손실
- TSX 파일 수정 시 포매팅 유지가 중요하므로 LibCST 선택

### 버전 정책
- `>=`로 최소 버전만 지정
- 이유: 최신 버그 픽스 자동 적용

---

## Related Files

- `/Users/comento/agent-product/unified-agent/requirements.txt`
- `/Users/comento/agent-product/unified-agent/.env.example`
- `/Users/comento/agent-product/unified-agent/.gitignore`

---

## Spec Reference

- Spec: [specs/pr-automation/spec.md](../../specs/pr-automation/spec.md#7-dependencies)
- Plan: [specs/pr-automation/plan.md](../../specs/pr-automation/plan.md#9-dependencies)
- Tasks: [specs/pr-automation/tasks.md](../../specs/pr-automation/tasks.md#task-01)

---

## Notes

- 설치 후 `pip list | grep -E "PyGithub|GitPython|libcst|beautifulsoup4|lxml"` 로 확인
- 가상환경 사용 권장: `python -m venv venv && source venv/bin/activate`

---

**Created**: 2026-01-11
**Last Updated**: 2026-01-11
