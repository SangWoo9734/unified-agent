"""
Comparative Analyzer
여러 프로덕트의 데이터를 비교 분석하고 리소스 배분 추천을 제공합니다.
"""

import google.generativeai as genai
import pandas as pd
from typing import List, Dict, Optional


class ComparativeAnalyzer:
    """여러 프로덕트를 비교 분석하는 클래스"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Google Gemini API 키
        """
        genai.configure(api_key=api_key)
        # Gemini 2.5 Flash - 최신 무료 모델
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def analyze_products(self, products_data: List[Dict]) -> str:
        """
        여러 프로덕트를 비교 분석하고 통합 리포트 생성

        Args:
            products_data: 각 프로덕트의 수집된 데이터 리스트
                [{
                    'name': 'product-name',
                    'config': {...},
                    'gsc': {...},
                    'ga4': {...},
                    'trends': {...},
                    'adsense': {...}
                }]

        Returns:
            마크다운 형식의 비교 분석 리포트
        """
        # 데이터 요약
        summary = self._build_summary(products_data)

        # Gemini에 분석 요청
        prompt = self._build_analysis_prompt(summary, products_data)

        try:
            response = self.model.generate_content(prompt)
            return response.text

        except Exception as e:
            return f"❌ 분석 중 오류 발생: {str(e)}\n\n수집된 데이터:\n{summary}"

    def _build_summary(self, products_data: List[Dict]) -> str:
        """
        수집된 데이터를 요약 문자열로 변환

        Args:
            products_data: 프로덕트 데이터 리스트

        Returns:
            요약 문자열
        """
        lines = []

        for data in products_data:
            product_name = data.get('name', 'Unknown')
            config = data.get('config', {})

            lines.append(f"\n{'='*60}")
            lines.append(f"## {product_name}")
            lines.append(f"우선순위: {config.get('priority', 'N/A')}")
            lines.append(f"AdSense: {'있음' if config.get('has_adsense') else '없음'}")
            lines.append(f"{'='*60}\n")

            # GSC 데이터
            gsc_data = data.get('gsc')
            if gsc_data and gsc_data.get('top_queries') is not None:
                top_queries = gsc_data['top_queries']
                if not top_queries.empty:
                    total_clicks = int(top_queries['clicks'].sum())
                    total_impressions = int(top_queries['impressions'].sum())
                    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
                    avg_position = float(top_queries['position'].mean())

                    lines.append("### Google Search Console")
                    lines.append(f"- 총 클릭: {total_clicks:,}")
                    lines.append(f"- 총 노출: {total_impressions:,}")
                    lines.append(f"- 평균 CTR: {avg_ctr:.2f}%")
                    lines.append(f"- 평균 순위: {avg_position:.1f}")

                    # 상위 5개 검색어
                    lines.append("\n상위 검색어:")
                    for idx, row in top_queries.head(5).iterrows():
                        lines.append(f"  {idx+1}. '{row['query']}' - {int(row['clicks'])}회 클릭, 순위 {row['position']:.1f}")

                    # 기회 키워드
                    opportunities = gsc_data.get('opportunities')
                    if opportunities is not None and not opportunities.empty:
                        lines.append("\n기회 키워드 (노출 많지만 순위 낮음):")
                        for idx, row in opportunities.head(3).iterrows():
                            lines.append(f"  - '{row['query']}' - {int(row['impressions'])}회 노출, 순위 {row['position']:.1f}")

            # GA4 데이터
            ga4_data = data.get('ga4')
            if ga4_data:
                pages = ga4_data.get('pages')
                if pages is not None and not pages.empty:
                    total_sessions = int(pages['sessions'].sum())
                    avg_engagement_rate = float(pages['engagement_rate'].mean()) if 'engagement_rate' in pages.columns else 0

                    lines.append("\n### Google Analytics 4")
                    lines.append(f"- 총 세션: {total_sessions:,}")
                    lines.append(f"- 평균 참여율: {avg_engagement_rate:.1f}%")

                    # 상위 페이지
                    lines.append("\n상위 페이지:")
                    for idx, row in pages.head(5).iterrows():
                        sessions = int(row['sessions'])
                        lines.append(f"  {idx+1}. {row['page_path']} - {sessions:,} 세션")

                # 디바이스 분석
                devices = ga4_data.get('devices')
                if devices is not None and not devices.empty:
                    lines.append("\n디바이스 분석:")
                    for idx, row in devices.iterrows():
                        sessions = int(row['sessions'])
                        # 'device' 또는 'device_category' 컬럼 사용
                        device_name = row.get('device', row.get('device_category', 'Unknown'))
                        lines.append(f"  - {device_name}: {sessions:,} 세션")

            # Google Trends
            trends_data = data.get('trends')
            if trends_data is not None and not trends_data.empty:
                lines.append("\n### Google Trends")
                # 관심도가 높은 키워드
                top_trends = trends_data.nlargest(3, trends_data.columns[-1])
                lines.append("최근 관심도 높은 키워드:")
                for keyword in top_trends.index:
                    lines.append(f"  - {keyword}")

            # AdSense (있는 경우)
            adsense_data = data.get('adsense')
            if adsense_data:
                revenue = adsense_data.get('revenue', 0)
                rpm = adsense_data.get('rpm', 0)
                lines.append(f"\n### AdSense")
                lines.append(f"- 예상 수익: ${revenue:.2f}")
                lines.append(f"- RPM: ${rpm:.2f}")

            lines.append("")  # 빈 줄 추가

        return "\n".join(lines)

    def _build_analysis_prompt(self, summary: str, products_data: List[Dict]) -> str:
        """
        Claude에게 보낼 분석 프롬프트 생성

        Args:
            summary: 데이터 요약 문자열
            products_data: 원본 데이터 (필요시 참조)

        Returns:
            분석 프롬프트
        """
        product_names = [data.get('name', 'Unknown') for data in products_data]
        product_list = ", ".join(product_names)

        prompt = f"""
당신은 여러 웹 프로덕트를 운영하는 마케팅 팀의 데이터 분석가입니다.
현재 운영 중인 프로덕트: {product_list}

# 수집된 데이터
{summary}

# 요청사항
위 데이터를 바탕으로 **실행 가능한 비교 분석 리포트**를 작성해주세요.
다음 형식을 정확히 따라주세요:

---

# Multi-Product Analysis Report

## 📊 Executive Summary (핵심 요약)
- 각 프로덕트의 현재 상태를 3줄로 요약
- 가장 주목할 만한 인사이트 2-3개
- 이번 주 최우선 과제 1개

## 🏆 Product Performance Comparison (프로덕트 성과 비교)

### 트래픽 비교
| 프로덕트 | GSC 클릭 | GSC 노출 | CTR | GA4 세션 | 우선순위 |
|---------|----------|----------|-----|----------|----------|
| ... | ... | ... | ... | ... | ... |

### 핵심 지표 분석
- 어느 프로덕트가 더 효율적인가?
- 성장/하락 트렌드
- 특이사항

## 💰 Revenue & ROI Analysis (수익 및 ROI 분석)
※ AdSense가 있는 프로덕트만 해당
- 현재 수익 구조
- 트래픽 대비 수익 효율
- 개선 가능 영역

## 🎯 Resource Allocation Recommendations (리소스 배분 추천)

### SEO 에이전트 운영 전략
- **프로덕트 A**: [주간/격주/월간] + 이유
- **프로덕트 B**: [주간/격주/월간] + 이유

### 마케팅 예산 배분 (100% 기준)
- **프로덕트 A**: XX% - 근거
- **프로덕트 B**: YY% - 근거

### 우선순위 조정 제안
- 현재 우선순위가 적절한가?
- 변경 제안이 있다면?

## 🔄 Cross-Promotion Opportunities (교차 프로모션 기회)
- 프로덕트 간 사용자 흐름 추정
- 내부 링크 추가 제안 (구체적 페이지 명시)
- 예상 효과

## 📈 Growth Opportunities (성장 기회)
각 프로덕트별:
- 기회 키워드 활용 방안
- Google Trends 기반 선제 대응 전략
- Quick Wins (빠르게 성과 낼 수 있는 것)

## 🚨 Issues & Risks (문제점 및 위험 요소)
- 현재 직면한 문제
- 방치 시 예상되는 리스크
- 해결 방안

## ✅ This Week's Action Plan (이번 주 실행 계획)

### 🔴 High Priority (긴급 - 이번 주)
1. [구체적 액션] - 담당: [프로덕트], 예상 효과: [숫자]
2. ...

### 🟡 Medium Priority (중요 - 다음 주)
1. ...

### 🟢 Low Priority (장기 - 2주 후)
1. ...

---

**중요 원칙:**
1. 모든 판단은 **데이터 근거**를 명시
2. 추측성 발언 최소화
3. 숫자는 구체적으로 (예: "많다" ❌, "1,234회" ✅)
4. 실행 가능한 액션만 제안
5. 프로덕트 간 비교는 공정하게
"""

        return prompt

    def generate_individual_report(self, product_data: Dict) -> str:
        """
        개별 프로덕트에 대한 상세 리포트 생성
        (기존 claude_analyzer_v2와 유사하지만 단일 프로덕트 전용)

        Args:
            product_data: 단일 프로덕트 데이터

        Returns:
            개별 프로덕트 리포트
        """
        # 기존 claude_analyzer_v2의 로직을 재사용하거나
        # 여기서 간단한 버전을 구현
        product_name = product_data.get('name', 'Unknown Product')

        return f"# {product_name} Detailed Report\n\n(상세 분석 내용)"
