#!/usr/bin/env python3
"""
Dispatch 이벤트 전송 (수정 버전)
"""
import os
from dotenv import load_dotenv
from core.dispatchers.repository_dispatcher import RepositoryDispatcher
from core.executors.models import Action

load_dotenv()

def main():
    print("=" * 60)
    print("📡 Repository Dispatch 이벤트 전송")
    print("=" * 60)
    
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN 환경변수가 필요합니다.")
        return 1
    
    dispatcher = RepositoryDispatcher(github_token=github_token)
    owner = "SangWoo9734"
    
    # qr-generator 액션 (Action 객체로 생성)
    qr_actions = [
        Action(
            id="20260113-001",
            action_type="update_meta_title",
            target_file="src/app/layout.tsx",
            current_value="QR Generator",
            new_value="Free Online QR Code Generator - Create Custom QR Codes Instantly",
            reasoning="검색 노출 25% 증가 예상",
            product="qr-generator"
        ),
        Action(
            id="20260113-002",
            action_type="update_meta_description",
            target_file="src/app/layout.tsx",
            current_value="Create QR codes",
            new_value="Generate free QR codes for URLs, text, WiFi, and more. Professional QR code generator with customization options. No signup required.",
            reasoning="CTR 20% 증가 예상",
            product="qr-generator"
        )
    ]
    
    # qr-generator 전송
    print(f"\n📤 qr-generator에 Dispatch 이벤트 전송 중...")
    try:
        result = dispatcher.dispatch(owner, "qr-generator", qr_actions)
        if result:
            print(f"   ✅ 성공! 2개 액션 전송 완료")
            print(f"   📍 확인: https://github.com/{owner}/qr-generator/actions")
        else:
            print(f"   ❌ 실패")
    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # convert-image 액션
    convert_actions = [
        Action(
            id="20260113-003",
            action_type="update_meta_title",
            target_file="src/app/layout.tsx",
            current_value="Image Converter",
            new_value="Free Image Converter - Convert Images to Any Format Online",
            reasoning="검색 노출 30% 증가 예상",
            product="convert-image"
        ),
        Action(
            id="20260113-004",
            action_type="update_meta_description",
            target_file="src/app/layout.tsx",
            current_value="Convert images",
            new_value="Free online image converter supporting 50+ formats. Convert JPG, PNG, WebP, HEIC, and more. Fast, secure, and easy to use. No installation required.",
            reasoning="CTR 25% 증가 예상",
            product="convert-image"
        )
    ]
    
    # convert-image 전송
    print(f"\n📤 convert-image에 Dispatch 이벤트 전송 중...")
    try:
        result = dispatcher.dispatch(owner, "convert-image", convert_actions)
        if result:
            print(f"   ✅ 성공! 2개 액션 전송 완료")
            print(f"   📍 확인: https://github.com/{owner}/convert-image/actions")
        else:
            print(f"   ❌ 실패")
    except Exception as e:
        print(f"   ❌ 오류: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Dispatch 전송 완료")
    print("=" * 60)
    print("\n⏰ 약 1-2분 후 다음 페이지에서 워크플로우 실행을 확인하세요:")
    print(f"   • https://github.com/{owner}/qr-generator/actions")
    print(f"   • https://github.com/{owner}/convert-image/actions")
    print("\n💡 PR 확인:")
    print(f"   • https://github.com/{owner}/qr-generator/pulls")
    print(f"   • https://github.com/{owner}/convert-image/pulls")
    
    return 0

if __name__ == '__main__':
    exit(main())
