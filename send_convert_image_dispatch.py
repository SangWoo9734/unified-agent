#!/usr/bin/env python3
"""
Send dispatch to convert-image with correct parameters
"""
import os
from dotenv import load_dotenv
from core.dispatchers.repository_dispatcher import RepositoryDispatcher
from core.executors.models import Action

load_dotenv()

def main():
    github_token = os.getenv('GITHUB_TOKEN')
    if not github_token:
        print("❌ GITHUB_TOKEN required")
        return 1

    dispatcher = RepositoryDispatcher(github_token=github_token)

    # convert-image action with CORRECT target_file
    action = Action(
        id="20260114-convert-meta-desc",
        priority="high",
        description="Update meta description for convert-image",
        product_id="convert-image",
        action_type="update_meta_description",
        target_file="index.html",  # CORRECT: Vite uses index.html
        parameters={
            "new_value": "Professional 100% private online image and PDF tools - convert, compress, resize with AI powered processing locally in your browser. No upload required."
        },
        expected_impact="SEO improvement and better CTR"
    )

    print("📤 Sending dispatch to convert-image...")
    print(f"   Action: {action.action_type}")
    print(f"   Target: {action.target_file}")

    try:
        result = dispatcher.dispatch("SangWoo9734", "convert-image", [action])
        if result:
            print("✅ Dispatch sent successfully!")
            print("🔗 Check: https://github.com/SangWoo9734/convert-image/actions")
        else:
            print("❌ Failed to send dispatch")
            return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == '__main__':
    exit(main())
