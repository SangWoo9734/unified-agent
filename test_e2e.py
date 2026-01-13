#!/usr/bin/env python3
"""
End-to-End Test for Level 2 Agent v2.0

이 스크립트는 v2.0 Repository Dispatch 방식의 전체 플로우를 테스트합니다:
1. SEO 리포트에서 액션 추출 (Gemini AI)
2. 안전성 검증
3. Repository Dispatch 이벤트 전송
4. (프로덕트 워크플로우는 GitHub Actions에서 자동 실행됨)
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from core.level2_agent_v2 import Level2AgentV2

def main():
    # .env 파일 로드
    load_dotenv()

    print("=" * 60)
    print("🧪 End-to-End Test: Level 2 Agent v2.0")
    print("=" * 60)

    # 환경변수 확인
    github_token = os.getenv("GITHUB_TOKEN")
    gemini_api_key = os.getenv("GOOGLE_API_KEY")

    if not github_token:
        print("❌ GITHUB_TOKEN not found in .env")
        return

    if not gemini_api_key:
        print("❌ GOOGLE_API_KEY not found in .env")
        return

    print(f"✅ GITHUB_TOKEN: {github_token[:10]}...")
    print(f"✅ GOOGLE_API_KEY: {gemini_api_key[:10]}...")
    print()

    # Level 2 Agent 초기화
    print("🤖 Initializing Level 2 Agent v2.0...")
    agent = Level2AgentV2(
        github_owner="SangWoo9734",
        gemini_api_key=gemini_api_key,
        github_token=github_token,
        dry_run=False
    )
    print("✅ Agent initialized\n")

    # 테스트 리포트 경로
    report_path = Path("reports/comparison/2026-01-13_test_v2_dispatch.md")

    if not report_path.exists():
        print(f"❌ Report not found: {report_path}")
        return

    print(f"📄 Report: {report_path}\n")

    # 프로세스 실행
    print("🚀 Starting end-to-end test...")
    print("-" * 60)

    try:
        result = agent.process_report(report_path=str(report_path))

        print("-" * 60)
        print("✅ End-to-end test completed!")
        print()
        print("📊 Results:")
        print(f"  - Dispatched events: {len(result.get('dispatched', []))}")
        for product in result.get('dispatched', []):
            print(f"    ✅ {product}")

        if result.get('failed'):
            print(f"  - Failed: {len(result.get('failed', []))}")
            for product in result.get('failed', []):
                print(f"    ❌ {product}")

        print()
        print("🎯 Next Steps:")
        print("  1. GitHub Actions에서 워크플로우 실행 확인:")
        print("     - https://github.com/SangWoo9734/qr-generator/actions")
        print("     - https://github.com/SangWoo9734/convert-image/actions")
        print("  2. PR이 자동 생성되었는지 확인:")
        print("     - https://github.com/SangWoo9734/qr-generator/pulls")
        print("     - https://github.com/SangWoo9734/convert-image/pulls")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
