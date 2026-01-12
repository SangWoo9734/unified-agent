"""
Claude SEO Analyzer

Claude AI를 사용하여 GSC 데이터를 분석하고 SEO 인사이트를 제공합니다.
"""

import os
from typing import Dict, List, Optional
import pandas as pd
from anthropic import Anthropic


class ClaudeAnalyzer:
    """Claude를 사용한 SEO 데이터 분석기"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Anthropic API Key
        """
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def analyze_search_performance(
        self,
        top_queries: pd.DataFrame,
        opportunity_keywords: pd.DataFrame,
        page_performance: pd.DataFrame
    ) -> str:
        """
        GSC 데이터를 Claude에게 분석 요청

        Args:
            top_queries: 상위 검색어 DataFrame
            opportunity_keywords: 기회 키워드 DataFrame
            page_performance: 페이지별 성과 DataFrame

        Returns:
            Claude의 분석 결과 (마크다운)
        """
        # 데이터를 Claude가 읽기 좋은 형태로 변환
        data_summary = self._format_data_for_claude(
            top_queries,
            opportunity_keywords,
            page_performance
        )

        prompt = f"""당신은 SEO 전문가입니다. 아래 ConvertKits.org의 최근 7일간 Google Search Console 데이터를 분석하고, 실행 가능한 SEO 개선 제안을 해주세요.

# 데이터 요약
{data_summary}

# 분석 요청사항

다음 형식으로 분석 결과를 작성해주세요:

## 🔥 Top Performing Content (상위 성과)
- 클릭수가 많은 상위 3개 페이지/키워드 분석
- 왜 이 콘텐츠가 잘 되고 있는지 가설 제시

## 💎 Opportunity Keywords (기회 키워드)
- 노출은 많지만 CTR이 낮은 키워드 3~5개 선정
- 각 키워드별로:
  - 현재 문제점 진단
  - 개선 방안 (메타 타이틀/설명 수정, 콘텐츠 보강 등)

## 📉 Issues & Warnings (문제점)
- 평균 검색 순위가 낮은 페이지
- CTR이 업계 평균(약 2~3%)보다 낮은 페이지
- 즉각적인 조치가 필요한 항목

## 🎯 Action Items (실행 과제)
우선순위별로 구체적인 실행 과제 3~5개 제시
(예: "HEIC to JPG 페이지 메타 설명에 '무료' 키워드 추가")

각 섹션은 구체적이고 실행 가능한 조언이어야 하며, 한국어로 작성해주세요."""

        try:
            print("🤖 Claude에게 데이터 분석 요청 중...")

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,  # 일관성을 위해 낮은 temperature
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = message.content[0].text

            print("✅ Claude 분석 완료!")
            return analysis

        except Exception as e:
            print(f"❌ Claude 분석 실패: {str(e)}")
            raise

    def _format_data_for_claude(
        self,
        top_queries: pd.DataFrame,
        opportunity_keywords: pd.DataFrame,
        page_performance: pd.DataFrame
    ) -> str:
        """데이터를 Claude가 읽기 좋은 텍스트로 변환"""
        sections = []

        # 1. 상위 검색어
        if not top_queries.empty:
            sections.append("## 상위 검색어 (Top Queries)")
            sections.append("| 검색어 | 클릭 | 노출 | CTR | 평균 순위 |")
            sections.append("|--------|------|------|-----|-----------|")
            for _, row in top_queries.head(10).iterrows():
                sections.append(
                    f"| {row['query']} | {row['clicks']:.0f} | {row['impressions']:.0f} | "
                    f"{row['ctr']*100:.1f}% | {row['position']:.1f} |"
                )
            sections.append("")

        # 2. 기회 키워드
        if not opportunity_keywords.empty:
            sections.append("## 기회 키워드 (노출 多 + CTR 低)")
            sections.append("| 검색어 | 클릭 | 노출 | CTR | 평균 순위 |")
            sections.append("|--------|------|------|-----|-----------|")
            for _, row in opportunity_keywords.head(10).iterrows():
                sections.append(
                    f"| {row['query']} | {row['clicks']:.0f} | {row['impressions']:.0f} | "
                    f"{row['ctr']*100:.1f}% | {row['position']:.1f} |"
                )
            sections.append("")

        # 3. 페이지별 성과
        if not page_performance.empty:
            sections.append("## 페이지별 성과")
            sections.append("| 페이지 URL | 클릭 | 노출 | CTR | 평균 순위 |")
            sections.append("|------------|------|------|-----|-----------|")
            for _, row in page_performance.head(10).iterrows():
                # URL 줄임 (너무 길면 Claude 토큰 낭비)
                url = row['page'].replace('https://convertkits.org', '')
                sections.append(
                    f"| {url} | {row['clicks']:.0f} | {row['impressions']:.0f} | "
                    f"{row['ctr']*100:.1f}% | {row['position']:.1f} |"
                )
            sections.append("")

        return "\n".join(sections)


if __name__ == '__main__':
    """테스트용 실행 코드"""
    from dotenv import load_dotenv

    load_dotenv()

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.")
        exit(1)

    # 테스트 데이터
    test_top_queries = pd.DataFrame({
        'query': ['heic to jpg converter', 'free image converter', 'png to webp'],
        'clicks': [150, 120, 90],
        'impressions': [3000, 2500, 2000],
        'ctr': [0.05, 0.048, 0.045],
        'position': [5.2, 6.1, 7.3]
    })

    test_opportunities = pd.DataFrame({
        'query': ['convert heic online free', 'image compressor tool'],
        'clicks': [10, 8],
        'impressions': [800, 600],
        'ctr': [0.0125, 0.0133],
        'position': [12.5, 15.2]
    })

    test_pages = pd.DataFrame({
        'page': ['https://convertkits.org/heic-to-jpg', 'https://convertkits.org/compress-image'],
        'clicks': [200, 150],
        'impressions': [4000, 3000],
        'ctr': [0.05, 0.05],
        'position': [5.5, 6.8]
    })

    analyzer = ClaudeAnalyzer(api_key)
    result = analyzer.analyze_search_performance(
        test_top_queries,
        test_opportunities,
        test_pages
    )

    print("\n" + "="*60)
    print(result)
