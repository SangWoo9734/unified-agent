# Level 2 Agent Implementation TODOs

**Feature**: pr-automation
**Phase**: PR Automation for Multi-Product Agent
**Created**: 2026-01-11

---

## Overview

이 디렉토리는 Level 2 Agent (PR 자동화) 구현을 위한 실행 단위 TODO 파일들을 포함합니다.

**Total Tasks**: 15
**Completed**: 0
**In Progress**: 0
**Blocked**: 0

---

## Phase: PR Automation Implementation

### Objective
unified-agent가 리포트를 생성한 후, High Priority 액션을 자동으로 파일 변경 + GitHub PR 생성까지 수행하도록 구현합니다.

### Success Criteria
- [ ] 리포트에서 액션 자동 추출
- [ ] 메타 타이틀/설명 자동 변경
- [ ] 내부 링크 자동 추가
- [ ] GitHub PR 자동 생성
- [ ] 실패 시 자동 롤백
- [ ] PR 성공률 > 95%

---

## Todo List

### 🔴 Priority: HIGH (Critical Path)

| ID | Title | Status | Complexity | Time | Dependencies |
|----|-------|--------|------------|------|--------------|
| [01](01-priority-high/01-setup-dependencies.md) | Setup & Dependencies | 🔴 Not Started | Low | 30 min | None |
| [02](01-priority-high/02-core-data-classes.md) | Core Data Classes | 🔴 Not Started | Low | 20 min | 01 |
| 03 | FileBackupManager | 🔴 Not Started | Low | 30 min | 02 |
| 04 | Configuration Files | 🔴 Not Started | Low | 30 min | None |
| 05 | ActionExtractor | 🔴 Not Started | Medium | 1.5 hrs | 02 |
| 06 | ActionValidator | 🔴 Not Started | Low | 45 min | 02 |
| [07](01-priority-high/07-meta-updater.md) | MetaUpdater | 🔴 Not Started | High | 3 hrs | 02, 03 |
| 08 | PRCreator | 🔴 Not Started | High | 3 hrs | 02 |
| 09 | Level2Agent Orchestrator | 🔴 Not Started | Medium | 2 hrs | 05, 06, 07, 08 |
| 10 | main.py Integration | 🔴 Not Started | Medium | 1 hr | 09, 04 |

### 🟡 Priority: MEDIUM

| ID | Title | Status | Complexity | Time | Dependencies |
|----|-------|--------|------------|------|--------------|
| 11 | LinkInjector | 🔴 Not Started | Medium | 2 hrs | 02, 03 |
| 12 | Unit Tests | 🔴 Not Started | Medium | 2 hrs | 05, 06, 07, 11 |
| 13 | Integration Test | 🔴 Not Started | High | 2 hrs | 10, 12 |

### 🟢 Priority: LOW

| ID | Title | Status | Complexity | Time | Dependencies |
|----|-------|--------|------------|------|--------------|
| 14 | Dry-run Mode | 🔴 Not Started | Low | 30 min | 10 |
| 15 | Documentation | 🔴 Not Started | Low | 1 hr | 13, 14 |

---

## Execution Strategy

### Week 1: Infrastructure (Jan 11-15)
**Goal**: 기본 인프라 구축

```
Day 1-2: Setup & Data Models
  ├─ TODO-01: Setup & Dependencies ✓
  ├─ TODO-02: Core Data Classes ✓
  ├─ TODO-03: FileBackupManager ✓
  └─ TODO-04: Configuration Files ✓

Day 3-5: Core Logic Foundation
  ├─ TODO-05: ActionExtractor ✓
  └─ TODO-06: ActionValidator ✓
```

**Deliverable**: 리포트 파싱 + 검증 동작

### Week 2: File Operations (Jan 16-22)
**Goal**: 파일 변경 로직 완성

```
Day 1-3: MetaUpdater (Critical)
  └─ TODO-07: MetaUpdater ✓

Day 4-5: LinkInjector
  └─ TODO-11: LinkInjector ✓
```

**Deliverable**: 메타 타이틀/설명 변경, 링크 추가 동작

### Week 3: Git & PR Integration (Jan 23-29)
**Goal**: PR 자동 생성 완성

```
Day 1-3: PRCreator
  └─ TODO-08: PRCreator ✓

Day 4-5: Level2Agent + main.py
  ├─ TODO-09: Level2Agent Orchestrator ✓
  └─ TODO-10: main.py Integration ✓
```

**Deliverable**: 전체 시스템 통합, PR 자동 생성 동작

### Week 4: Testing & Polish (Jan 30 - Feb 5)
**Goal**: 프로덕션 준비

```
Day 1-2: Tests
  ├─ TODO-12: Unit Tests ✓
  └─ TODO-13: Integration Test ✓

Day 3-4: Polish
  ├─ TODO-14: Dry-run Mode ✓
  └─ TODO-15: Documentation ✓
```

**Deliverable**: 프로덕션 배포 준비 완료

---

## Critical Path

```
TODO-01 (Setup)
  ↓
TODO-02 (Data Classes)
  ↓
TODO-05 (ActionExtractor)
  ↓
TODO-07 (MetaUpdater)
  ↓
TODO-08 (PRCreator)
  ↓
TODO-09 (Level2Agent)
  ↓
TODO-10 (main.py Integration)
  ↓
TODO-13 (Integration Test)
```

**Total Critical Path Time**: ~12-14 hours

---

## Quick Start

### 1. Start with Infrastructure
```bash
# Read and execute
cat todos/01-priority-high/01-setup-dependencies.md
# Follow tasks one by one
```

### 2. Complete in Order
- 의존성 그래프를 따라 순서대로 진행
- 각 TODO 완료 시 체크박스 업데이트
- Git 커밋 (TODO 단위)

### 3. Status Updates
각 TODO 파일의 Status를 업데이트:
- 🔴 Not Started
- 🟡 In Progress
- 🟢 Completed
- 🔵 Blocked

---

## Definition of Done

각 TODO는 다음 조건을 모두 만족해야 완료:

- [ ] 모든 Tasks 체크박스 완료
- [ ] Acceptance Criteria 모두 만족
- [ ] 코드 작성 + Type hints
- [ ] Docstring 작성
- [ ] 유닛 테스트 작성 (해당 시)
- [ ] 테스트 통과
- [ ] 에러 처리 완료
- [ ] Git 커밋 (TODO 단위)

---

## Blocked Tasks

현재 블로킹된 작업 없음.

**Potential Blockers**:
- GitHub Token 권한 부족
- Git 설정 문제
- 프로덕트 레포지토리 접근 권한

---

## Notes

### 중요 파일 위치
- Spec: [../specs/pr-automation/spec.md](../specs/pr-automation/spec.md)
- Plan: [../specs/pr-automation/plan.md](../specs/pr-automation/plan.md)
- Tasks: [../specs/pr-automation/tasks.md](../specs/pr-automation/tasks.md)

### 헬프
- LibCST 문서: https://libcst.readthedocs.io/
- PyGithub 문서: https://pygithub.readthedocs.io/
- GitPython 문서: https://gitpython.readthedocs.io/

---

## Progress Tracking

**Last Updated**: 2026-01-11

### Week 1 (Jan 11-15)
- [ ] TODO-01
- [ ] TODO-02
- [ ] TODO-03
- [ ] TODO-04
- [ ] TODO-05
- [ ] TODO-06

### Week 2 (Jan 16-22)
- [ ] TODO-07
- [ ] TODO-11

### Week 3 (Jan 23-29)
- [ ] TODO-08
- [ ] TODO-09
- [ ] TODO-10

### Week 4 (Jan 30 - Feb 5)
- [ ] TODO-12
- [ ] TODO-13
- [ ] TODO-14
- [ ] TODO-15

---

**Phase Status**: 🔴 Not Started
**Estimated Completion**: Feb 5, 2026
**Actual Completion**: TBD

---

*Generated by spec-flow workflow*
