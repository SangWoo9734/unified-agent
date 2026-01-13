#!/usr/bin/env python3
"""
convert-image에 올바른 경로로 Dispatch 전송
"""
import os
from dotenv import load_dotenv
from core.dispatchers.repository_dispatcher import RepositoryDispatcher
from core.executors.models import Action

load_dotenv()

def main():
    print("=" * 60)
    print("📡 convert-image에 Dispatch 이벤트 재전송")
    print("=" * 60)
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN 환경변수가 필요합니다.")
        return 1
    
    dispatcher = RepositoryDispatcher(github_token=github_token)
    owner = "SangWoo9734"
    
    # convert-image 액션 (올바른 경로: index.html)
    convert_actions = [
        Action(
            id="20260113-005",
            priority="high",
            description="Update meta title in index.html",
            product_id="convert-image",
            action_type="update_meta_title",
            target_file="index.html",  # 올바른 경로!
            parameters={
                "old_value": "ConvertKits - Professional Image & PDF Tools",
                "new_value": "Free Image Converter - Convert Images to Any Format Online"
            },
            expected_impact="검색 노출 30% 증가 예상"
        ),
        Action(
            id="20260113-006",
            priority="high",
            description="Update meta description in index.html",
            product_id="convert-image",
            action_type="update_meta_description",
            target_file="index.html",  # 올바른 경로!
            parameters={
                "old_value": "Professional 100% private online image and PDF tools processing locally in your browser. Convert, compress, and resize for free.",
                "new_value": "Free online image converter supporting 50+ formats. Convert JPG, PNG, WebP, HEIC, and more. Fast, secure, and easy to use. No installation required."
            },
            expected_impact="CTR 25% 증가 예상"
        )
    ]
    
    # convert-image 전송
    print(f"\n📤 convert-image에 Dispatch 이벤트 전송 중...")
    print(f"   대상 파일: index.html")
    try:
        result = dispatcher.dispatch(owner, "convert-image", convert_actions)
        if result:
            print(f"   ✅ 성공! 2개 액션 전송 완료")
            print(f"   📍 Actions: https://github.com/{owner}/convert-image/actions")
            print(f"   💡 PRs: https://github.com/{owner}/convert-image/pulls")
        else:
            print(f"   ❌ 실패")
    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Dispatch 전송 완료!")
    print("=" * 60)
    print("\n⏰ 약 1-2분 후 PR을 확인하세요:")
    print(f"   https://github.com/{owner}/convert-image/pulls")
    
    return 0

if __name__ == '__main__':
    exit(main())
