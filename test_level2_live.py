"""
Level 2 Agent 실제 테스트

실제 리포트와 프로덕트로 테스트합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from core.level2_agent import Level2Agent

def main():
    print("=" * 60)
    print("🧪 Level 2 Agent 실제 테스트")
    print("=" * 60)
    print()

    # 테스트 리포트 경로
    report_path = "/Users/comento/agent-product/unified-agent/reports/comparison/2026-01-13_test_report.md"

    print(f"📄 리포트: {report_path}")
    print(f"🎯 프로덕트: qr-generator")
    print(f"📁 대상 파일: /Users/comento/agent-product/qr-generator/src/app/layout.tsx")
    print()

    # 현재 메타 정보 출력
    print("📋 현재 메타 정보:")
    with open("/Users/comento/agent-product/qr-generator/src/app/layout.tsx", "r") as f:
        content = f.read()
        for line in content.split("\n")[10:14]:
            print(f"   {line}")
    print()

    # Level2Agent 초기화 (Dry-run 모드)
    print("🤖 Level2Agent 초기화 중... (Dry-run 모드)")
    agent = Level2Agent(
        workspace_root="/Users/comento/agent-product/unified-agent",
        dry_run=True  # 실제로 파일을 변경하지 않음
    )
    print()

    # 리포트 처리
    result = agent.process_report(report_path)

    # 결과 출력
    print()
    print("=" * 60)
    print("📊 테스트 결과")
    print("=" * 60)
    print()
    print(f"✅ 성공: {result['success']}")
    print(f"📦 Product ID: {result.get('product_id')}")
    print(f"📋 추출된 액션: {result['actions_extracted']}개")
    print(f"🛡️  안전한 액션: {result['actions_safe']}개")
    print(f"⚙️  실행된 액션: {result['actions_executed']}개")
    print(f"🔗 PR URL: {result.get('pr_url')}")
    print()

    if result['execution_results']:
        print("📝 실행 결과 상세:")
        for idx, exec_result in enumerate(result['execution_results'], 1):
            status = "✅" if exec_result.success else "❌"
            print(f"   {idx}. {status} {exec_result.message}")
        print()

    # Dry-run이므로 파일은 변경되지 않음
    print("💡 Dry-run 모드이므로 실제 파일은 변경되지 않았습니다.")
    print()

    return 0

if __name__ == "__main__":
    try:
        exit(main())
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
