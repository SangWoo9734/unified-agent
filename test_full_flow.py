"""
전체 플로우 테스트

파일 수정 + Git commit + PR 생성까지 전체 플로우를 테스트합니다.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, str(Path(__file__).parent))

# .env 파일 로드
load_dotenv()

from core.level2_agent import Level2Agent

def main():
    print("=" * 60)
    print("🚀 Level 2 Agent 전체 플로우 테스트")
    print("=" * 60)
    print()

    # 환경변수 확인
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN 환경변수가 설정되지 않았습니다.")
        print("   .env 파일에 GITHUB_TOKEN을 추가하거나")
        print("   export GITHUB_TOKEN=your_token 으로 설정해주세요.")
        return 1

    print("✅ GITHUB_TOKEN 설정됨")
    print()

    # 테스트 리포트 경로
    report_path = "/Users/comento/agent-product/unified-agent/reports/comparison/2026-01-13_test_report.md"

    print(f"📄 리포트: {report_path}")
    print(f"🎯 프로덕트: qr-generator")
    print(f"📁 대상 파일: src/app/layout.tsx")
    print()

    # 현재 메타 정보 출력
    print("📋 현재 메타 정보:")
    layout_path = "/Users/comento/agent-product/qr-generator/src/app/layout.tsx"
    with open(layout_path, "r") as f:
        content = f.read()
        for line in content.split("\n")[10:14]:
            print(f"   {line}")
    print()

    # 사용자 확인
    print("⚠️  주의: 이 테스트는 실제로 다음을 수행합니다:")
    print("   1. layout.tsx 파일 수정 (백업 자동 생성)")
    print("   2. Git 브랜치 생성 (agent/seo-qr-generator-...)")
    print("   3. Git commit")
    print("   4. GitHub에 브랜치 push")
    print("   5. GitHub PR 생성")
    print()

    response = input("계속하시겠습니까? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\n테스트 취소됨")
        return 0

    print()
    print("=" * 60)
    print("🤖 Level2Agent 실행 중...")
    print("=" * 60)
    print()

    # Level2Agent 초기화 (실제 실행 모드)
    agent = Level2Agent(
        workspace_root="/Users/comento/agent-product/unified-agent",
        github_token=github_token,
        base_branch="main",
        dry_run=False  # 실제로 파일 변경 및 PR 생성
    )

    # 리포트 처리
    result = agent.process_report(report_path)

    # 결과 출력
    print()
    print("=" * 60)
    print("📊 실행 결과")
    print("=" * 60)
    print()

    if result['success']:
        print(f"✅ 성공!")
        print(f"📦 Product ID: {result.get('product_id')}")
        print(f"📋 추출된 액션: {result['actions_extracted']}개")
        print(f"🛡️  안전한 액션: {result['actions_safe']}개")
        print(f"⚙️  실행된 액션: {result['actions_executed']}개")
        print()

        if result['execution_results']:
            print("📝 실행 결과 상세:")
            for idx, exec_result in enumerate(result['execution_results'], 1):
                status = "✅" if exec_result.success else "❌"
                print(f"   {idx}. {status} {exec_result.message}")
                if exec_result.changed_files:
                    for f in exec_result.changed_files:
                        print(f"      📄 {f}")
            print()

        if result.get('pr_url'):
            print("🎉 GitHub PR 생성 완료!")
            print(f"   {result['pr_url']}")
            print()
            print("💡 다음 단계:")
            print("   1. PR 확인 및 리뷰")
            print("   2. 테스트 실행")
            print("   3. PR 머지")
        else:
            print("⚠️  PR이 생성되지 않았습니다.")
            if result['actions_executed'] == 0:
                print("   (실행된 액션이 없음)")
            print()

        # 변경된 파일 확인
        print("📝 변경된 layout.tsx 확인:")
        with open(layout_path, "r") as f:
            content = f.read()
            for line in content.split("\n")[10:14]:
                print(f"   {line}")
        print()

        # 백업 파일 정보
        print("💾 백업 파일:")
        backup_dir = Path("/Users/comento/agent-product/unified-agent/.agent_backups")
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("*.tsx"), reverse=True)
            if backups:
                latest = backups[0]
                print(f"   최신 백업: {latest.name}")
                print(f"   복구: cp {latest} {layout_path}")
        print()

        return 0
    else:
        print(f"❌ 실패: {result.get('error', 'Unknown error')}")
        return 1

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 실행을 중단했습니다.")
        exit(1)
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
