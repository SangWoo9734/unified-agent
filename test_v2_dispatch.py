#!/usr/bin/env python3
"""
v2.0 Dispatch 테스트 스크립트
"""
import os
from dotenv import load_dotenv
from core.level2_agent_v2 import Level2AgentV2

load_dotenv()

def main():
    print("=" * 60)
    print("🧪 Level 2 Agent v2.0 테스트")
    print("=" * 60)
    
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    github_token = os.getenv('GITHUB_TOKEN')
    github_owner = os.getenv('GITHUB_OWNER', 'SangWoo9734')
    
    if not github_token:
        print("❌ GITHUB_TOKEN 환경변수가 필요합니다.")
        return 1
    
    # Level2AgentV2 초기화
    agent = Level2AgentV2(
        anthropic_api_key=anthropic_api_key,
        github_token=github_token,
        github_owner=github_owner,
        dry_run=True  # Dry-run 모드
    )
    
    # 테스트 리포트 처리
    report_path = 'reports/comparison/2026-01-13_test_v2_dispatch.md'
    result = agent.process_report(report_path)
    
    # 결과 출력
    print("\n" + "=" * 60)
    print("📊 테스트 결과")
    print("=" * 60)
    
    if result['success']:
        print(f"✅ 성공!")
        print(f"   추출된 액션: {result['actions_extracted']}개")
        print(f"   안전한 액션: {result['actions_safe']}개")
        print(f"   Dispatch 전송: {result.get('dispatches_sent', 0)}개 프로덕트")
        
        if result.get('dispatch_results'):
            print(f"\n📡 Dispatch 결과:")
            for product, success in result['dispatch_results'].items():
                status = "✅" if success else "❌"
                print(f"   {status} {product}")
    else:
        print(f"❌ 실패: {result.get('error', 'Unknown error')}")
    
    return 0

if __name__ == '__main__':
    exit(main())
