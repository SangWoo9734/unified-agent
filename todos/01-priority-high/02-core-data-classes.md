# TODO-02: Core Data Classes

**Status**: 🔴 Not Started
**Priority**: HIGH
**Complexity**: Low
**Estimated Time**: 20 min

---

## Business Value

**Goal**: Action, ExecutionResult 데이터 모델 정의

**Impact**:
- 모든 컴포넌트 간 타입 안전성 확보
- 명확한 데이터 계약
- IDE 자동완성 지원

---

## Description

Level 2 Agent의 핵심 데이터 구조를 정의합니다.

---

## Tasks

- [ ] `core/executors/` 디렉토리 생성
- [ ] `core/executors/__init__.py` 생성
- [ ] `core/executors/models.py` 생성
- [ ] `Action` dataclass 작성:
  ```python
  @dataclass
  class Action:
      id: str
      priority: str
      description: str
      product_id: str
      action_type: str
      target_file: Optional[str]
      parameters: Dict[str, Any]
      expected_impact: Optional[str]
      is_automatable: bool
      automation_reason: Optional[str]
  ```
- [ ] `ExecutionResult` dataclass 작성
- [ ] `__init__.py`에서 export
- [ ] Type hints 검증
- [ ] Docstring 작성

---

## Acceptance Criteria

- [ ] Action 클래스 모든 필드 정의
- [ ] ExecutionResult 클래스 정의
- [ ] Type hints 올바름 (`mypy` 통과)
- [ ] Docstring 작성
- [ ] `from core.executors.models import Action` 동작

---

## Dependencies

**Depends on**: TODO-01
**Blocks**: TODO-03, TODO-04, TODO-05, TODO-06, TODO-07, TODO-08, TODO-09

---

## Related Files

- `core/executors/models.py` (NEW)
- `core/executors/__init__.py` (NEW)

---

## Spec Reference

- Plan: [specs/pr-automation/plan.md](../../specs/pr-automation/plan.md#31-action-data-class)
