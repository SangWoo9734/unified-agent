#!/bin/bash

# unified-agent GitHub 저장소 설정 스크립트

set -e  # 에러 발생 시 중단

echo "=========================================="
echo "🚀 unified-agent GitHub 저장소 설정"
echo "=========================================="
echo ""

# 1. GitHub 사용자명 입력
read -p "GitHub 사용자명을 입력하세요 (예: SangWoo9734): " GITHUB_USERNAME

if [ -z "$GITHUB_USERNAME" ]; then
    echo "❌ GitHub 사용자명이 필요합니다."
    exit 1
fi

echo ""
echo "✅ GitHub 저장소: https://github.com/$GITHUB_USERNAME/unified-agent"
echo ""

# 2. 확인
read -p "계속하시겠습니까? (y/n): " CONFIRM

if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
    echo "취소되었습니다."
    exit 0
fi

echo ""
echo "📝 Git 초기화 중..."

# 3. Git 초기화
git init

echo "✅ Git 초기화 완료"
echo ""

# 4. 현재 브랜치 확인 및 main으로 설정
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

if [ -z "$CURRENT_BRANCH" ]; then
    # 브랜치가 없으면 main 브랜치 생성
    echo "🌿 main 브랜치 생성 중..."
else
    echo "🌿 현재 브랜치: $CURRENT_BRANCH"
    if [ "$CURRENT_BRANCH" != "main" ]; then
        echo "   → main 브랜치로 변경"
        git branch -M main
    fi
fi

# 5. 파일 추가
echo ""
echo "📦 파일 추가 중..."
git add .

echo "✅ 파일 추가 완료"
echo ""

# 6. 첫 커밋
echo "💾 커밋 생성 중..."
git commit -m "Initial commit: Level 1 + Level 2 Agent with GitHub Actions

- Level 1: 데이터 수집 및 Claude AI 분석
- Level 2: 자동 PR 생성
- GitHub Actions 워크플로우
- 완전 자동화 구현"

echo "✅ 커밋 완료"
echo ""

# 7. 원격 저장소 추가
echo "🔗 원격 저장소 연결 중..."
git remote add origin "https://github.com/$GITHUB_USERNAME/unified-agent.git"

echo "✅ 원격 저장소 연결 완료"
echo ""

# 8. 최종 안내
echo "=========================================="
echo "✨ Git 설정 완료!"
echo "=========================================="
echo ""
echo "📋 다음 단계:"
echo ""
echo "1. GitHub에서 새 저장소 생성"
echo "   https://github.com/new"
echo "   Repository name: unified-agent"
echo "   Visibility: Private (추천)"
echo "   ⚠️ README, .gitignore 추가하지 않기"
echo ""
echo "2. 푸시 실행:"
echo "   git push -u origin main"
echo ""
echo "3. GitHub Secrets 설정:"
echo "   Settings → Secrets and variables → Actions"
echo "   - ANTHROPIC_API_KEY"
echo "   - GH_PAT (Personal Access Token)"
echo "   - GSC_CREDENTIALS"
echo ""
echo "4. 워크플로우 수동 실행 테스트"
echo "   Actions 탭 → Run workflow"
echo ""
echo "자세한 내용: SETUP_GITHUB_REPO.md"
echo ""
