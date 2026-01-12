"""
Level2Agent 통합 테스트

전체 파이프라인을 테스트합니다.
"""

import os
import sys
import tempfile
from pathlib import Path

import git

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.level2_agent import Level2Agent


# 샘플 리포트 (ActionExtractor 테스트에서 사용한 것과 동일)
SAMPLE_REPORT = """
# SEO Agent 분석 리포트

날짜: 2026-01-13

## 분석 개요

본 리포트는 QR Generator와 Convert Image 프로덕트의 SEO 분석 결과입니다.

## High Priority Actions

1. **[QR Generator]** Update meta title to "QR Code Generator - Free & Fast"

- File: `src/app/layout.tsx`
- Expected Impact: 검색 노출 20% 증가 예상

2. **[QR Generator]** Update meta description to "Create QR codes instantly. Free, fast, and easy to use."

- File: `src/app/layout.tsx`
- Expected Impact: CTR 15% 증가 예상

3. **[QR Generator]** Add canonical URL "https://qr-generator.com"

- File: `src/app/layout.tsx`
- Expected Impact: SEO 중복 문제 해결

## Medium Priority Actions

4. **[QR Generator]** 내부 링크 추가

Convert Image로의 내부 링크를 추가합니다.

- File: `src/components/Footer.tsx`
- Action Type: `add_internal_link`
- Parameters:
  - `target_url`: "/convert-image"
  - `anchor_text`: "Try our Image Converter"
- Expected Impact: 내부 링크 구조 개선

## 결론

총 4개의 액션 아이템이 제안되었습니다.
"""


def test_level2_agent_dry_run():
    """Level2Agent Dry-run 테스트"""

    print("=== Level2Agent Dry-run 테스트 ===\n")

    # 1. 임시 리포트 파일 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 리포트 저장
        report_path = temp_path / "test_report.md"
        report_path.write_text(SAMPLE_REPORT, encoding="utf-8")

        print(f"📄 테스트 리포트 생성: {report_path}\n")

        # 2. Level2Agent 초기화 (dry-run 모드)
        agent = Level2Agent(
            workspace_root=".",
            dry_run=True  # 실제 파일 변경/PR 생성 안 함
        )

        # 3. 리포트 처리
        result = agent.process_report(str(report_path))

        # 4. 결과 검증
        print("\n=== 처리 결과 ===\n")
        print(f"성공: {result['success']}")
        print(f"Product ID: {result.get('product_id')}")
        print(f"추출된 액션: {result['actions_extracted']}개")
        print(f"안전한 액션: {result['actions_safe']}개")
        print(f"실행된 액션: {result['actions_executed']}개")
        print(f"PR URL: {result.get('pr_url')}")
        print(f"에러: {result.get('error')}")
        print()

        # 테스트 검증
        assert result["success"] is True, "처리가 실패했습니다"
        assert result["actions_extracted"] >= 3, "액션 추출 실패"
        assert result["actions_safe"] >= 2, "안전한 액션 필터링 실패"
        assert result["actions_executed"] >= 2, "액션 실행 실패"
        assert result["pr_url"] is None, "Dry-run 모드에서 PR URL이 반환되면 안 됩니다"

        print("✅ Dry-run 테스트 통과!\n")


def test_level2_agent_with_mock_repo():
    """Level2Agent + Mock Git 저장소 테스트"""

    print("=== Level2Agent + Mock Git 저장소 테스트 ===\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 1. Mock 프로덕트 디렉토리 생성
        product_id = "qr-generator"
        product_path = temp_path / product_id
        product_path.mkdir()

        # Git 초기화
        repo = git.Repo.init(product_path)

        # 대상 파일 생성 (src/app/layout.tsx)
        src_app = product_path / "src" / "app"
        src_app.mkdir(parents=True)

        layout_file = src_app / "layout.tsx"
        layout_file.write_text("""
export const metadata = {
  title: "Old Title",
  description: "Old Description"
};
""", encoding="utf-8")

        # 초기 커밋
        repo.index.add(["src/app/layout.tsx"])
        repo.index.commit("Initial commit")
        repo.git.checkout("-b", "main")

        print(f"📁 Mock 프로덕트 생성: {product_path}\n")

        # 2. 테스트 리포트 생성
        report_path = temp_path / "test_report.md"
        report_path.write_text(SAMPLE_REPORT, encoding="utf-8")

        # 3. Level2Agent 초기화
        # workspace_root를 temp_path로 설정 (테스트 환경)
        agent = Level2Agent(
            workspace_root=str(temp_path),
            dry_run=False  # 실제 파일 변경 (PR은 생성 안 함, GitHub token 없음)
        )

        # GitHub token 설정 (fake)
        os.environ["GITHUB_TOKEN"] = "fake_token_for_test"

        try:
            # 4. 리포트 처리 (PR 생성은 실패할 것, 파일 변경까지만)
            result = agent.process_report(str(report_path), product_id=product_id)

            # 5. 결과 검증
            print("\n=== 처리 결과 ===\n")
            print(f"성공: {result['success']}")
            print(f"Product ID: {result.get('product_id')}")
            print(f"추출된 액션: {result['actions_extracted']}개")
            print(f"안전한 액션: {result['actions_safe']}개")
            print(f"실행된 액션: {result['actions_executed']}개")
            print()

            # 파일이 실제로 변경되었는지 확인
            modified_content = layout_file.read_text(encoding="utf-8")
            print("📝 변경된 layout.tsx:")
            print(modified_content)
            print()

            # 검증
            assert result["success"] is True, "처리가 실패했습니다"
            assert result["actions_extracted"] >= 3, "액션 추출 실패"
            assert result["actions_safe"] >= 2, "안전한 액션 필터링 실패"
            # canonical_url은 아직 구현 안 됨, 2개만 성공
            assert result["actions_executed"] >= 2, "액션 실행 실패 (2개 이상 성공해야 함)"

            # 파일 내용 검증
            assert "QR Code Generator - Free & Fast" in modified_content, "타이틀이 변경되지 않았습니다"
            assert "Create QR codes instantly" in modified_content, "설명이 변경되지 않았습니다"

            print("✅ Mock 저장소 테스트 통과!\n")

        finally:
            # 환경변수 정리
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]


def test_multiple_reports():
    """여러 리포트 처리 테스트"""

    print("=== 여러 리포트 처리 테스트 ===\n")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 3개의 리포트 생성
        report_paths = []
        for i in range(3):
            report_path = temp_path / f"report_{i+1}.md"
            report_path.write_text(SAMPLE_REPORT, encoding="utf-8")
            report_paths.append(str(report_path))

        # Level2Agent 초기화
        agent = Level2Agent(workspace_root=".", dry_run=True)

        # 여러 리포트 처리
        results = agent.process_multiple_reports(report_paths)

        # 결과 검증
        assert len(results) == 3, "3개의 결과가 반환되어야 합니다"
        successful = sum(1 for r in results if r["success"])

        print(f"\n✅ 여러 리포트 처리 테스트 통과! ({successful}/3 성공)\n")


if __name__ == "__main__":
    test_level2_agent_dry_run()
    test_level2_agent_with_mock_repo()
    test_multiple_reports()

    print("🎉 Level2Agent 모든 테스트 통과!")
