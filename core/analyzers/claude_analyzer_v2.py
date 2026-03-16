"""
Claude SEO Analyzer v2

GSC, GA4, Google Trends 데이터를 통합 분석합니다.
"""

import os
from typing import Dict, List, Optional
import pandas as pd
from anthropic import Anthropic


class ClaudeAnalyzerV2:
    """Claude를 사용한 통합 SEO 데이터 분석기"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Anthropic API Key
        """
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-3-5-sonnet-20241022"

    def analyze_comprehensive(
        self,
        # GSC 데이터
        gsc_top_queries: pd.DataFrame,
        gsc_opportunities: pd.DataFrame,
        gsc_page_performance: pd.DataFrame,
        # GA4 데이터
        ga4_pages: Optional[pd.DataFrame] = None,
        ga4_traffic: Optional[pd.DataFrame] = None,
        ga4_devices: Optional[pd.DataFrame] = None,
        ga4_events: Optional[pd.DataFrame] = None,
        # Trends 데이터
        trends_analysis: Optional[pd.DataFrame] = None,
        trends_related: Optional[Dict] = None
    ) -> str:
        """
        모든 데이터를 통합하여 종합 분석

        Returns:
            Claude의 종합 분석 결과 (마크다운)
        """
        # 데이터를 Claude가 읽기 좋은 형태로 변환
        data_summary = self._format_comprehensive_data(
            gsc_top_queries, gsc_opportunities, gsc_page_performance,
            ga4_pages, ga4_traffic, ga4_devices, ga4_events,
            trends_analysis, trends_related
        )

        prompt = f"""당신은 글로벌 웹 프로젝트의 SEO 및 웹 분석 전문가입니다.

우리의 프로덕트는 **전 세계 다양한 국가의 글로벌 사용자**를 타겟으로 하는 웹 서비스입니다.
다음 데이터를 종합 분석하여, 다양한 지역으로부터의 다국적 트래픽 유입을 겨냥한 실행 가능한 SEO 및 트래픽 개선 전략을 제시해주세요:
- Google Search Console (검색 성과)
- Google Analytics 4 (사용자 행동)
- Google Trends (검색 트렌드)

# 수집된 데이터
{data_summary}

# 분석 요청사항

다음 형식으로 종합 분석 결과를 작성해주세요:

## 📊 Executive Summary (핵심 요약)
- 전체적인 SEO 건강 상태 (1-10점 척도)
- 이번 주 가장 주목할 만한 변화 3가지
- 즉각 조치가 필요한 긴급 이슈 1~2개

## 🔥 Top Performing Content (최고 성과 콘텐츠)
- GSC와 GA4 데이터를 교차 분석하여 실제로 성과가 좋은 페이지 3개 선정
- 각 페이지가 성공한 이유 (검색 순위, 참여도, 전환율 종합)
- 성공 요인을 다른 페이지에 적용하는 방법

## 📈 Trend Insights (트렌드 인사이트)
- Google Trends에서 발견한 검색량 급상승 키워드
- 계절성 또는 최근 이벤트로 인한 변화
- 선제적으로 대응해야 할 트렌드

## 💎 Opportunity Keywords (기회 키워드)
- GSC 노출 多 + CTR 低 + Trends 상승세 = 최우선 타겟
- 각 키워드별 구체적 개선 방안:
  - 메타 타이틀/설명 수정안
  - 콘텐츠 보강 방향
  - 예상 효과

## 📱 User Behavior Analysis (사용자 행동 분석)
- GA4 데이터로 본 사용자 여정
- 디바이스별 차이점 (Mobile vs Desktop)
- 이탈률이 높은 페이지와 원인
- 참여도가 높은 페이지의 공통점

## 🚨 Issues & Red Flags (문제점 및 경고)
- GSC 순위 하락 페이지 + GA4 이탈률 증가 = 시급
- 트래픽은 많지만 전환이 낮은 페이지
- 모바일 성능 이슈
- 경쟁사 대비 약점

## 🎯 Prioritized Action Plan (우선순위 실행 계획)
다음 2주간 실행할 구체적인 과제를 우선순위별로 3단계로 제시:

### High Priority (긴급 - 이번 주)
1. ...
2. ...

### Medium Priority (중요 - 다음 주)
1. ...
2. ...

### Low Priority (장기 - 2주 후)
1. ...

## 💡 Strategic Recommendations (전략적 제언)
- 장기적인 SEO 전략 방향
- 콘텐츠 확장 아이디어
- 기술적 SEO 개선사항

---

**중요:** 모든 제안은 데이터에 근거하고, 구체적이며, 즉시 실행 가능해야 합니다.
리포트 본문은 한국어로 작성하되, 제안하는 메타 타이틀/설명 등 실제 SEO 문구는 전 세계 사용자가 검색하고 이해하기 쉬운 범용적인 **영문(English)**으로 작성해주세요."""

        try:
            print("🤖 Claude에게 종합 분석 요청 중...")

            message = self.client.messages.create(
                model=self.model,
                max_tokens=8192,  # 더 긴 분석을 위해 증가
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = message.content[0].text

            print("✅ Claude 종합 분석 완료!")
            return analysis

        except Exception as e:
            print(f"❌ Claude 분석 실패: {str(e)}")
            raise

    def _format_comprehensive_data(
        self,
        gsc_top_queries, gsc_opportunities, gsc_page_performance,
        ga4_pages, ga4_traffic, ga4_devices, ga4_events,
        trends_analysis, trends_related
    ) -> str:
        """모든 데이터를 Claude가 읽기 좋은 텍스트로 변환"""
        sections = []

        # === Google Search Console ===
        sections.append("# Google Search Console 데이터\n")

        if not gsc_top_queries.empty:
            sections.append("## 상위 검색어 (클릭 많은 순)")
            sections.append("| 검색어 | 클릭 | 노출 | CTR | 평균 순위 |")
            sections.append("|--------|------|------|-----|-----------|")
            for _, row in gsc_top_queries.head(10).iterrows():
                sections.append(
                    f"| {row['query']} | {row['clicks']:.0f} | {row['impressions']:.0f} | "
                    f"{row['ctr']*100:.1f}% | {row['position']:.1f} |"
                )
            sections.append("")

        if not gsc_opportunities.empty:
            sections.append("## 기회 키워드 (노출 多, CTR 低)")
            sections.append("| 검색어 | 클릭 | 노출 | CTR | 평균 순위 |")
            sections.append("|--------|------|------|-----|-----------|")
            for _, row in gsc_opportunities.head(10).iterrows():
                sections.append(
                    f"| {row['query']} | {row['clicks']:.0f} | {row['impressions']:.0f} | "
                    f"{row['ctr']*100:.1f}% | {row['position']:.1f} |"
                )
            sections.append("")

        # === Google Analytics 4 ===
        if ga4_pages is not None and not ga4_pages.empty:
            sections.append("# Google Analytics 4 데이터\n")
            sections.append("## 페이지별 사용자 행동")
            sections.append("| 페이지 | 조회수 | 세션 | 평균 세션(초) | 이탈률 | 참여율 |")
            sections.append("|--------|--------|------|---------------|--------|--------|")
            for _, row in ga4_pages.head(10).iterrows():
                path = row['page_path'][:50]  # URL 길이 제한
                sections.append(
                    f"| {path} | {row['pageviews']:.0f} | {row['sessions']:.0f} | "
                    f"{row['avg_session_duration']:.0f} | {row['bounce_rate']*100:.1f}% | "
                    f"{row['engagement_rate']*100:.1f}% |"
                )
            sections.append("")

        if ga4_traffic is not None and not ga4_traffic.empty:
            sections.append("## 트래픽 소스")
            sections.append("| 소스 | 매체 | 세션 | 참여율 | 평균 세션(초) |")
            sections.append("|------|------|------|--------|---------------|")
            for _, row in ga4_traffic.head(10).iterrows():
                sections.append(
                    f"| {row['source']} | {row['medium']} | {row['sessions']:.0f} | "
                    f"{row['engagement_rate']*100:.1f}% | {row['avg_session_duration']:.0f} |"
                )
            sections.append("")

        if ga4_devices is not None and not ga4_devices.empty:
            sections.append("## 디바이스 분석")
            sections.append("| 디바이스 | 세션 | 참여율 | 이탈률 |")
            sections.append("|----------|------|--------|--------|")
            for _, row in ga4_devices.iterrows():
                sections.append(
                    f"| {row['device']} | {row['sessions']:.0f} | "
                    f"{row['engagement_rate']*100:.1f}% | {row['bounce_rate']*100:.1f}% |"
                )
            sections.append("")

        if ga4_events is not None and not ga4_events.empty:
            sections.append("## 주요 이벤트 (전환 추적)")
            sections.append("| 이벤트명 | 발생 횟수 | 사용자당 평균 |")
            sections.append("|----------|-----------|---------------|")
            for _, row in ga4_events.head(10).iterrows():
                sections.append(
                    f"| {row['event_name']} | {row['event_count']:.0f} | "
                    f"{row['events_per_user']:.2f} |"
                )
            sections.append("")

        # === Google Trends ===
        if trends_analysis is not None and not trends_analysis.empty:
            sections.append("# Google Trends 데이터\n")
            sections.append("## 키워드 트렌드 변화 (최근 3개월)")
            sections.append("| 키워드 | 현재 인기도 | 과거 평균 | 변화율 | 최고점 |")
            sections.append("|--------|-------------|----------|--------|--------|")
            for _, row in trends_analysis.head(15).iterrows():
                trend_emoji = "📈" if row['trend_change_pct'] > 10 else "📉" if row['trend_change_pct'] < -10 else "➡️"
                sections.append(
                    f"| {row['keyword']} | {row['current_interest']:.0f} | "
                    f"{row['past_avg']:.0f} | {trend_emoji} {row['trend_change_pct']:+.1f}% | "
                    f"{row['max_interest']:.0f} |"
                )
            sections.append("")

        if trends_related and 'rising' in trends_related and not trends_related['rising'].empty:
            sections.append("## 급상승 관련 검색어")
            df = trends_related['rising'].head(10)
            sections.append("| 검색어 | 상승률 |")
            sections.append("|--------|--------|")
            for _, row in df.iterrows():
                value = row.get('value', 'N/A')
                query = row.get('query', 'N/A')
                sections.append(f"| {query} | {value} |")
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

    # 더미 데이터로 테스트
    gsc_queries = pd.DataFrame({
        'query': ['heic to jpg', 'image converter'],
        'clicks': [100, 80],
        'impressions': [2000, 1500],
        'ctr': [0.05, 0.053],
        'position': [5.2, 6.8]
    })

    ga4_pages = pd.DataFrame({
        'page_path': ['/heic-to-jpg', '/compress-image'],
        'page_title': ['HEIC to JPG', 'Compress Image'],
        'pageviews': [500, 400],
        'sessions': [300, 250],
        'avg_session_duration': [120, 90],
        'bounce_rate': [0.4, 0.5],
        'engagement_rate': [0.6, 0.5]
    })

    analyzer = ClaudeAnalyzerV2(api_key)
    result = analyzer.analyze_comprehensive(
        gsc_top_queries=gsc_queries,
        gsc_opportunities=pd.DataFrame(),
        gsc_page_performance=pd.DataFrame(),
        ga4_pages=ga4_pages
    )

    print("\n" + "="*60)
    print(result)
