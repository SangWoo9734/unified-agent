# TODO-07: MetaUpdater Implementation

**Status**: 🔴 Not Started
**Priority**: HIGH
**Complexity**: High
**Estimated Time**: 3 hours

---

## Business Value

**Goal**: 메타 타이틀/설명 자동 변경으로 SEO 개선

**Impact**:
- CTR 직접 개선 (메타 타이틀/설명 최적화)
- 수동 작업 제거 (30분 → 0분)
- 일관된 품질 (사람 실수 방지)

**Why This Matters**:
메타 타이틀과 설명은 SEO에서 가장 중요한 요소입니다. 이 작업을 자동화하면 Claude의 추천을 즉시 적용할 수 있어 검색 엔진 순위 개선이 빨라집니다.

---

## Description

TSX와 HTML 파일의 메타 타이틀/설명을 안전하게 변경합니다.

**Target Files**:
- qr-generator: `src/app/layout.tsx` (metadata 객체)
- convert-image: `index.html` (<title>, <meta description>)

**Core Challenge**:
- LibCST로 TSX 파일 파싱 (포매팅 유지)
- BeautifulSoup로 HTML 파싱
- 구문 오류 방지
- 백업 및 롤백

---

## Tasks

### 1. ActionExecutor Base Class
- [ ] `core/executors/action_executor.py` 생성
- [ ] ActionExecutor 추상 클래스 작성:
  ```python
  from abc import ABC, abstractmethod

  class ActionExecutor(ABC):
      def __init__(self, workspace_root: str):
          self.workspace_root = workspace_root
          self.backup_manager = FileBackupManager()

      @abstractmethod
      def execute(self, action: Action) -> ExecutionResult:
          pass
  ```

### 2. MetaUpdater Class
- [ ] `core/executors/meta_updater.py` 생성
- [ ] MetaUpdater 클래스 작성 (ActionExecutor 상속)
- [ ] `execute()` 메서드 구현:
  - 파일 타입 판별 (.tsx vs .html)
  - 백업 생성 호출
  - 파일 변경 로직 분기
  - ExecutionResult 반환

### 3. TSX Meta Update (LibCST)
- [ ] `_update_tsx_meta()` 프라이빗 메서드 구현
- [ ] LibCST Transformer 클래스 작성:
  ```python
  class MetadataTransformer(cst.CSTTransformer):
      def __init__(self, new_title, new_description):
          ...

      def leave_Assign(self, original_node, updated_node):
          # metadata 객체 찾기 및 변경
          ...
  ```
- [ ] 파일 읽기 → 파싱 → 변환 → 저장 흐름
- [ ] 에러 처리 (파싱 실패 시)

### 4. HTML Meta Update (BeautifulSoup)
- [ ] `_update_html_meta()` 프라이빗 메서드 구현
- [ ] BeautifulSoup로 HTML 파싱:
  ```python
  soup = BeautifulSoup(content, 'html.parser')
  title_tag = soup.find('title')
  meta_desc = soup.find('meta', attrs={'name': 'description'})
  ```
- [ ] 값 변경 및 저장
- [ ] 에러 처리

### 5. Rollback Logic
- [ ] 실패 시 백업 복원 로직
- [ ] ExecutionResult에 에러 정보 포함

### 6. Testing
- [ ] 임시 TSX 파일로 테스트
- [ ] 임시 HTML 파일로 테스트
- [ ] 구문 검증 (변경 후 파일이 유효한지)
- [ ] 백업/롤백 테스트

---

## Acceptance Criteria

- [ ] qr-generator/src/app/layout.tsx의 metadata.title 변경 동작
- [ ] qr-generator/src/app/layout.tsx의 metadata.description 변경 동작
- [ ] convert-image/index.html의 <title> 변경 동작
- [ ] convert-image/index.html의 <meta description> 변경 동작
- [ ] 변경 전 백업 자동 생성
- [ ] 변경 후 구문 오류 없음 (LibCST/BeautifulSoup 보장)
- [ ] 포매팅 유지 (들여쓰기, 줄바꿈 등)
- [ ] 실패 시 백업에서 복원
- [ ] ExecutionResult 올바르게 반환

---

## Dependencies

**Depends on**: TODO-02 (models), TODO-03 (FileBackup)
**Blocks**: TODO-09 (Level2Agent)

---

## Technical Notes

### LibCST 사용 예제

```python
import libcst as cst

# 파일 읽기
with open('layout.tsx', 'r') as f:
    source = f.read()

# 파싱
module = cst.parse_module(source)

# 변환
transformer = MetadataTransformer(new_title="New Title", new_description="New Desc")
modified_tree = module.visit(transformer)

# 저장 (포매팅 유지)
with open('layout.tsx', 'w') as f:
    f.write(modified_tree.code)
```

### metadata 객체 찾기

qr-generator/src/app/layout.tsx의 구조:
```typescript
export const metadata: Metadata = {
  title: "QR Studio - Free QR Code Generator | Instant & Private",
  description: "Create URL, WiFi, Text, Email, and Phone codes instantly...",
};
```

LibCST로 `metadata` 변수를 찾고, 객체 속성 중 `title`, `description` 값을 변경합니다.

### BeautifulSoup 사용 예제

```python
from bs4 import BeautifulSoup

# HTML 파싱
soup = BeautifulSoup(html_content, 'html.parser')

# title 변경
title_tag = soup.find('title')
if title_tag:
    title_tag.string = new_title

# meta description 변경
meta_desc = soup.find('meta', attrs={'name': 'description'})
if meta_desc:
    meta_desc['content'] = new_description

# 저장
with open('index.html', 'w') as f:
    f.write(str(soup))
```

### Gotchas
- LibCST는 TypeScript를 직접 파싱 못 함 → TSX 파일이지만 JavaScript로 취급
- BeautifulSoup는 HTML 구조 변경 가능 → 원본과 최대한 유사하게 유지
- 파일 인코딩: UTF-8 사용

---

## Related Files

- `core/executors/action_executor.py` (NEW - Base Class)
- `core/executors/meta_updater.py` (NEW)
- `qr-generator/src/app/layout.tsx` (MODIFY)
- `convert-image/index.html` (MODIFY)

---

## Spec Reference

- Spec: [specs/pr-automation/spec.md](../../specs/pr-automation/spec.md#fr-3-파일-변경-실행)
- Plan: [specs/pr-automation/plan.md](../../specs/pr-automation/plan.md#22-metaupdater)
- Tasks: [specs/pr-automation/tasks.md](../../specs/pr-automation/tasks.md#task-05)

---

## Notes

- LibCST 학습 곡선 있음: 공식 문서 참고 https://libcst.readthedocs.io/
- 테스트 파일로 먼저 연습 추천
- 실제 파일 변경 전 백업 필수!

---

**Created**: 2026-01-11
