# Technical Plan: PR Automation

**Feature**: pr-automation
**Created**: 2026-01-11
**Status**: Design
**Spec**: [spec.md](./spec.md)

---

## 1. Architecture Overview

### 1.1 System Flow

```
main.py (existing)
  ├─> [Level 1] Data Collection + Analysis + Report Generation
  │   └─> reports/comparison/{date}_multi_product_analysis.md
  │
  └─> [Level 2] PR Automation (NEW)
      ├─> ActionExtractor: 리포트 파싱 → Action 객체
      ├─> ActionValidator: 자동화 가능 여부 검증
      ├─> ActionExecutor: 파일 변경 실행
      │   ├─> MetaUpdater (HTML, TSX)
      │   └─> LinkInjector (TSX, Layout)
      └─> PRCreator: Git + GitHub PR 생성
```

### 1.2 Key Architectural Decisions

**AD-1: Modular Executors**
- **Decision**: 액션 타입별로 Executor 클래스 분리
- **Rationale**: 확장 용이, 단일 책임 원칙
- **Trade-off**: 클래스 수 증가 vs 유지보수성 향상

**AD-2: Context Manager for Safety**
- **Decision**: `@contextmanager`로 Git 작업 보호
- **Rationale**: 자동 롤백 보장, 예외 안전성
- **Trade-off**: 추가 코드 vs 안전성 확보

**AD-3: Hybrid Parsing (Regex + Claude)**
- **Decision**: 정규식 우선, 실패 시 Claude API
- **Rationale**: 비용 절감, 정확도 보장
- **Trade-off**: 복잡도 증가 vs 비용/정확도 균형

**AD-4: LibCST for TSX, BeautifulSoup for HTML**
- **Decision**: 파일 타입별 전문 파서 사용
- **Rationale**: 구문 안전성, 포매팅 유지
- **Trade-off**: 의존성 증가 vs 안전성

**AD-5: One PR per Product**
- **Decision**: 프로덕트당 1개 PR (여러 액션 묶음)
- **Rationale**: 리뷰 부담 감소, CI 빌드 최소화
- **Trade-off**: 롤백 단위 증가 vs 운영 효율

---

## 2. Component Design

### 2.1 Module Structure

```
unified-agent/
└── core/
    └── executors/              # NEW MODULE
        ├── __init__.py
        ├── action_extractor.py   # 리포트 파싱
        ├── action_validator.py   # 안전성 검증
        ├── action_executor.py    # Base Class
        ├── meta_updater.py       # 메타 타이틀/설명
        ├── link_injector.py      # 내부 링크
        ├── pr_creator.py         # Git + GitHub PR
        └── level2_agent.py       # Orchestrator
```

### 2.2 Core Classes

#### ActionExtractor
```python
class ActionExtractor:
    """리포트에서 액션 추출"""

    def __init__(self, anthropic_client: Optional[anthropic.Anthropic] = None):
        self.client = anthropic_client

    def extract_from_report(self, report_path: str) -> List[Action]:
        """
        1. 리포트 파일 읽기
        2. "### 🔴 High Priority" 섹션 찾기
        3. 정규식으로 파싱
        4. 실패 시 Claude API 재호출
        5. Action 객체 리스트 반환
        """
```

**Parsing Strategy**:
- **Pattern**: `r"(\d+)\.\s+(.+?)\s+-\s+담당:\s+(\S+),\s+예상 효과:\s+(.+)"`
- **Fallback**: Claude API에 JSON 변환 요청

#### ActionValidator
```python
class ActionValidator:
    """자동화 가능 여부 검증"""

    SAFE_ACTION_TYPES = {
        "update_meta_title",
        "update_meta_description",
        "add_internal_link",
    }

    SAFE_FILES = {
        "qr-generator": ["src/app/layout.tsx", "src/components/layout/Header.tsx"],
        "convert-image": ["index.html", "components/Layout.tsx"],
    }

    UNSAFE_PATTERNS = [
        "<script>", "eval(", "dangerouslySetInnerHTML",
        "innerHTML", "__proto__"
    ]

    def validate(self, action: Action) -> Tuple[bool, Optional[str]]:
        """검증 로직"""
```

#### ActionExecutor (Base Class)
```python
from abc import ABC, abstractmethod

class ActionExecutor(ABC):
    """모든 Executor의 Base Class"""

    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root
        self.backup_manager = FileBackupManager()

    @abstractmethod
    def execute(self, action: Action) -> Dict[str, Any]:
        """
        Returns:
            {
                "success": bool,
                "files_changed": List[str],
                "backup_path": Optional[str],
                "error": Optional[str]
            }
        """
```

#### MetaUpdater
```python
class MetaUpdater(ActionExecutor):
    """메타 타이틀/설명 변경"""

    def execute(self, action: Action) -> Dict[str, Any]:
        # 파일 타입 판별
        if action.target_file.endswith('.tsx'):
            return self._update_tsx_meta(...)
        elif action.target_file.endswith('.html'):
            return self._update_html_meta(...)

    def _update_tsx_meta(self, file_path, params, backup_path):
        """
        LibCST 사용:
        1. TSX 파일 파싱
        2. metadata 객체 찾기
        3. title/description 값 변경
        4. 포매팅 유지하며 저장
        """

    def _update_html_meta(self, file_path, params, backup_path):
        """
        BeautifulSoup 사용:
        1. HTML 파싱
        2. <title>, <meta name="description"> 찾기
        3. 값 변경
        4. 저장
        """
```

**LibCST Transformer Example**:
```python
class MetadataTransformer(cst.CSTTransformer):
    def __init__(self, new_title: str, new_description: str):
        self.new_title = new_title
        self.new_description = new_description

    def leave_Assign(self, original_node, updated_node):
        # metadata 객체 찾기
        if self._is_metadata_export(updated_node):
            # title, description 변경
            return self._update_metadata(updated_node)
        return updated_node
```

#### LinkInjector
```python
class LinkInjector(ActionExecutor):
    """내부 링크 추가"""

    def execute(self, action: Action) -> Dict[str, Any]:
        # Header.tsx 또는 Layout.tsx에 링크 추가
        if "Header.tsx" in action.target_file:
            return self._add_nav_link(...)
        elif "Layout.tsx" in action.target_file:
            return self._add_layout_link(...)

    def _add_nav_link(self, file_path, params, backup_path):
        """
        문자열 치환 방식:
        1. navItems 배열 찾기
        2. 새 링크 삽입
        3. Syntax Validation
        """
```

#### PRCreator
```python
class PRCreator:
    """Git + GitHub PR 생성"""

    def __init__(self, github_token: str):
        self.github = Github(github_token)

    @contextmanager
    def safe_git_operation(self, repo_path: str):
        """Git 작업 보호 Context Manager"""
        repo = git.Repo(repo_path)
        original_branch = repo.active_branch.name

        try:
            yield repo
        except Exception as e:
            # 롤백: 원래 브랜치로, 변경사항 폐기
            repo.git.checkout(original_branch)
            repo.git.reset('--hard')
            raise

    def create_pr_for_actions(
        self,
        product_id: str,
        repo_path: str,
        actions: List[Action],
        execution_results: List[Dict]
    ) -> str:
        """
        1. 새 브랜치 생성 (agent/seo-{timestamp})
        2. 변경된 파일 스테이징
        3. 커밋 (메시지 자동 생성)
        4. 원격 푸시
        5. GitHub PR 생성
        6. 원래 브랜치로 복귀

        Returns:
            PR URL
        """
```

#### Level2Agent (Orchestrator)
```python
class Level2Agent:
    """Level 2 Agent Orchestrator"""

    def __init__(self, anthropic_api_key, github_token, workspace_root, config):
        self.extractor = ActionExtractor(anthropic.Anthropic(api_key=anthropic_api_key))
        self.validator = ActionValidator()
        self.executors = {
            'update_meta_title': MetaUpdater(workspace_root),
            'update_meta_description': MetaUpdater(workspace_root),
            'add_internal_link': LinkInjector(workspace_root),
        }
        self.pr_creator = PRCreator(github_token)
        self.config = config

    def process_report(self, report_path: str) -> List[Dict]:
        """
        1. 액션 추출
        2. 검증 및 필터링
        3. 프로덕트별 그룹화
        4. 각 프로덕트별 실행 + PR 생성

        Returns:
            [{"product_id": "qr-generator", "pr_url": "https://..."}]
        """
```

---

## 3. Data Model

### 3.1 Action Data Class

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any

@dataclass
class Action:
    """단일 액션 정의"""
    id: str                          # "action_001"
    priority: str                    # "high" | "medium" | "low"
    description: str                 # "QR Generator 메타 타이틀 변경"
    product_id: str                  # "qr-generator" | "convert-image"
    action_type: str                 # "update_meta_title" | "add_internal_link"
    target_file: Optional[str]       # "src/app/layout.tsx"
    parameters: Dict[str, Any]       # {"title": "New Title"}
    expected_impact: Optional[str]   # "CTR +5%"
    is_automatable: bool             # True/False
    automation_reason: Optional[str] # 불가 시 이유
```

### 3.2 Execution Result

```python
@dataclass
class ExecutionResult:
    """실행 결과"""
    success: bool
    files_changed: List[str]
    backup_path: Optional[str]
    error: Optional[str]
```

---

## 4. API Design (Internal)

### 4.1 Public APIs

```python
# main.py → Level2Agent
agent = Level2Agent(api_key, github_token, workspace, config)
pr_results = agent.process_report(report_path)

# Level2Agent → ActionExtractor
actions = extractor.extract_from_report(report_path)

# Level2Agent → ActionValidator
is_valid, reason = validator.validate(action)

# Level2Agent → ActionExecutor
result = executor.execute(action)

# Level2Agent → PRCreator
pr_url = pr_creator.create_pr_for_actions(product_id, repo_path, actions, results)
```

### 4.2 Configuration API

```yaml
# products.yaml
products:
  qr-generator:
    github:
      repo: "SangWoo9734/qr-generator"
      default_branch: "main"
    local_path: "../qr-generator"

global:
  level2_agent:
    enabled: true
    pr_strategy: "one_per_product"
    auto_merge: false
```

```bash
# .env
GITHUB_TOKEN=ghp_xxxx
ENABLE_AUTO_PR=true
```

---

## 5. Integration Points

### 5.1 main.py Integration

```python
# /Users/comento/agent-product/unified-agent/main.py
# Line ~242 (리포트 저장 후)

if os.getenv('ENABLE_AUTO_PR', 'false').lower() == 'true':
    print("\n🤖 Level 2 Agent 실행 중...")

    try:
        from core.executors.level2_agent import Level2Agent

        agent = Level2Agent(
            anthropic_api_key=anthropic_api_key,
            github_token=os.getenv('GITHUB_TOKEN'),
            workspace_root=os.path.dirname(__file__),
            config=config
        )

        pr_results = agent.process_report(comparison_path)

        if pr_results:
            print("✅ PR 생성 완료:")
            for result in pr_results:
                print(f"   • {result['product_id']}: {result['pr_url']}")

    except Exception as e:
        print(f"⚠️ Level 2 Agent 실패: {str(e)}")
        # 리포트는 정상 생성됨, 에이전트만 실패
```

### 5.2 External Integrations

**GitHub API** (PyGithub):
- Repository: `gh_repo.create_pull(...)`
- Labels: `pr.add_to_labels(...)`
- Rate Limit: `github.get_rate_limit()`

**Git** (GitPython):
- Branch: `repo.create_head(name)`
- Commit: `repo.index.commit(message)`
- Push: `origin.push(branch_name)`

---

## 6. Error Handling

### 6.1 Error Categories

| Category | Examples | Handling |
|----------|----------|----------|
| **Parsing** | 리포트 형식 불일치 | Claude fallback, 로그 |
| **Validation** | 위험한 액션 타입 | 필터링, 경고 출력 |
| **File I/O** | 파일 없음, 권한 없음 | 롤백, 다음 액션 계속 |
| **Syntax** | LibCST 파싱 실패 | 롤백, 에러 로그 |
| **Git** | Conflict, push 실패 | 브랜치 삭제, 롤백 |
| **GitHub API** | Rate limit, auth 실패 | 재시도, 에러 메시지 |

### 6.2 Rollback Strategy

```python
@contextmanager
def temporary_git_branch(repo_path, branch_name):
    """브랜치 생성 + 자동 정리"""
    original_branch = None
    created_branch = False

    try:
        repo = git.Repo(repo_path)
        original_branch = repo.active_branch.name

        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        created_branch = True

        yield repo

    except Exception as e:
        # 실패 시 롤백
        if created_branch and original_branch:
            repo.heads[original_branch].checkout()
            repo.delete_head(branch_name, force=True)
        raise

    finally:
        # 정상 완료 후에도 원래 브랜치로
        if original_branch:
            repo.heads[original_branch].checkout()
```

### 6.3 Logging

```python
# logs/level2_agent_{timestamp}.log

[2026-01-11 10:30:00] INFO: Extracted 3 actions from report
[2026-01-11 10:30:01] INFO: Validated 2 actions (1 skipped: unsafe type)
[2026-01-11 10:30:02] INFO: Executing action_001: update_meta_title
[2026-01-11 10:30:03] SUCCESS: File changed: qr-generator/src/app/layout.tsx
[2026-01-11 10:30:04] INFO: Creating PR for qr-generator
[2026-01-11 10:30:06] SUCCESS: PR created: https://github.com/SangWoo9734/qr-generator/pull/123
```

---

## 7. Security

### 7.1 Threat Model

**Threat-1: 악의적 리포트 내용**
- **Attack**: 리포트에 `<script>alert('xss')</script>` 포함
- **Mitigation**: ActionValidator의 UNSAFE_PATTERNS 필터링

**Threat-2: 파일 경로 탐색**
- **Attack**: `target_file: "../../../etc/passwd"`
- **Mitigation**: SAFE_FILES 화이트리스트 검증

**Threat-3: GitHub Token 노출**
- **Attack**: 로그 파일에 토큰 기록
- **Mitigation**: `.gitignore`, 환경변수 사용, 로그에서 제외

**Threat-4: Code Injection**
- **Attack**: 메타 타이틀에 악의적 JavaScript
- **Mitigation**: LibCST/BeautifulSoup 사용 (HTML 이스케이프 자동)

### 7.2 Security Checklist

- ✅ `.env` 파일 `.gitignore`에 추가
- ✅ GitHub Token 권한 최소화 (`repo`만)
- ✅ 백업 디렉토리 `.gitignore`에 추가
- ✅ 사용자 입력 검증 (UNSAFE_PATTERNS)
- ✅ 파일 경로 화이트리스트
- ✅ 민감한 정보 로그 제외
- ✅ PR 자동 머지 비활성화 (Level 2)

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/test_action_extractor.py
def test_extract_high_priority_actions():
    sample_report = """
    ### 🔴 High Priority
    1. QR Generator 메타 타이틀 변경 - 담당: qr-generator, 예상 효과: CTR +5%
    """

    extractor = ActionExtractor()
    actions = extractor.extract_from_report(sample_report)

    assert len(actions) == 1
    assert actions[0].product_id == "qr-generator"
    assert actions[0].action_type == "update_meta_title"

# tests/test_action_validator.py
def test_unsafe_action_rejected():
    action = Action(action_type="modify_javascript", ...)
    validator = ActionValidator()

    is_valid, reason = validator.validate(action)

    assert is_valid == False
    assert "Unsafe action type" in reason

# tests/test_meta_updater.py
def test_update_tsx_meta():
    updater = MetaUpdater('/tmp')
    action = Action(
        action_type="update_meta_title",
        target_file="layout.tsx",
        parameters={"title": "New Title"}
    )

    result = updater.execute(action)

    assert result['success'] == True
    assert "layout.tsx" in result['files_changed']
```

### 8.2 Integration Tests

```python
# tests/test_level2_agent_integration.py
@pytest.mark.integration
def test_end_to_end_pr_creation():
    """실제 Git 레포 사용 (테스트 fork)"""
    agent = Level2Agent(...)

    # 임시 리포트 생성
    report_path = create_test_report()

    # 실행
    pr_results = agent.process_report(report_path)

    # 검증
    assert len(pr_results) == 1
    assert "github.com" in pr_results[0]['pr_url']

    # 정리: PR 닫기
    close_test_pr(pr_results[0]['pr_url'])
```

### 8.3 Dry-run Tests

```bash
# Dry-run 모드로 테스트
python main.py --dry-run

# 출력:
# 🤖 Level 2 Agent 실행 중 (DRY-RUN)
#    📋 2개 액션 추출됨
#    ✅ 2개 액션 자동화 가능
#    🔧 [DRY-RUN] qr-generator: 2개 액션 실행
#       ✅ [DRY-RUN] update_meta_title: src/app/layout.tsx
#       ✅ [DRY-RUN] add_internal_link: src/components/layout/Header.tsx
#    📤 [DRY-RUN] PR 생성 (실제 생성 안 함)
```

---

## 9. Migration Plan

### Phase 1: Infrastructure (Week 1-2)
1. 모듈 구조 생성 (`core/executors/`)
2. Action 데이터 클래스
3. ActionExtractor (정규식)
4. ActionValidator
5. 유닛 테스트

**Deliverable**: 리포트 파싱 + 검증 동작

### Phase 2: File Operations (Week 2-3)
1. MetaUpdater (HTML: BeautifulSoup)
2. MetaUpdater (TSX: LibCST)
3. LinkInjector (문자열 치환)
4. FileBackupManager
5. 통합 테스트

**Deliverable**: 파일 변경 동작

### Phase 3: Git & PR (Week 3-4)
1. PRCreator (GitPython)
2. PRCreator (PyGithub)
3. Context Manager 패턴
4. E2E 테스트

**Deliverable**: PR 자동 생성 동작

### Phase 4: Integration (Week 4)
1. Level2Agent Orchestrator
2. main.py 통합
3. products.yaml, .env 업데이트
4. automation_rules.yaml 생성

**Deliverable**: 전체 시스템 통합

### Phase 5: Testing & Docs (Week 5)
1. Dry-run 모드
2. 실제 레포 테스트
3. README.md 업데이트
4. 사용자 가이드

**Deliverable**: 프로덕션 준비 완료

---

## 10. Monitoring

### 10.1 Metrics

```python
class Level2AgentMetrics:
    """실행 통계"""
    metrics = {
        'actions_extracted': 0,
        'actions_validated': 0,
        'actions_executed': 0,
        'actions_failed': 0,
        'prs_created': 0,
        'execution_time': 0.0
    }
```

### 10.2 Log Files

- `logs/level2_agent_{timestamp}.log` - 상세 실행 로그
- `logs/level2_agent_errors.log` - 에러만 모음
- `reports/comparison/` - 생성된 리포트

### 10.3 Alerts

```yaml
# config/automation_rules.yaml (선택사항)
notifications:
  slack_webhook: "https://hooks.slack.com/..."
  notify_on_success: true
  notify_on_failure: true
```

---

## 11. Performance

### 11.1 Expected Performance

- **리포트 파싱**: < 1초
- **액션 검증**: < 0.5초
- **파일 변경**: 1-2초/액션
- **PR 생성**: 3-5초/프로덕트
- **총 추가 시간**: < 30초

### 11.2 Optimization

- 프로덕트별 병렬 실행 (독립적)
- GitHub API 호출 최소화 (batch)
- LibCST 캐싱 (동일 파일 반복 수정 시)

---

## 12. Extensibility

### 12.1 Adding New Action Types

```python
# 1. 새 Executor 생성
class ImageOptimizer(ActionExecutor):
    def execute(self, action):
        # alt 태그 추가, WebP 변환 등
        pass

# 2. Level2Agent에 등록
self.executors = {
    ...
    'optimize_image': ImageOptimizer(workspace_root),
}

# 3. ActionValidator에 추가
SAFE_ACTION_TYPES.add('optimize_image')
```

### 12.2 Adding New Products

```yaml
# products.yaml에만 추가
products:
  new-product:
    github:
      repo: "owner/new-product"
    local_path: "../new-product"
```

---

## Critical Files

**Implementation Priority**:
1. `core/executors/action_extractor.py` (액션 추출)
2. `core/executors/action_validator.py` (검증)
3. `core/executors/meta_updater.py` (메타 변경)
4. `core/executors/pr_creator.py` (PR 생성)
5. `core/executors/level2_agent.py` (Orchestrator)
6. `main.py` (통합)

**Configuration**:
- `config/products.yaml` (GitHub repo 정보 추가)
- `.env` (GITHUB_TOKEN 추가)
- `requirements.txt` (의존성 추가)

---

**Next Steps**:
1. ✅ spec.md 완료
2. ✅ plan.md 완료
3. ⏭️ tasks.md (구현 분해)
4. ⏭️ TODO 파일 생성

---

*Technical design ready for implementation*
