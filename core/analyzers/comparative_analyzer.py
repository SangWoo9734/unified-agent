"""
Comparative Analyzer
여러 프로덕트의 데이터를 비교 분석하고 리소스 배분 추천을 제공합니다.
"""

from google import genai
import pandas as pd
from typing import List, Dict, Optional


class ComparativeAnalyzer:
    """여러 프로덕트를 비교 분석하는 클래스"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Google Gemini API 키
        """
        self.client = genai.Client(api_key=api_key)
        # Gemini 2.0 Flash - 최신 안정 모델
        self.model_id = 'gemini-2.0-flash'

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

        # 각 프로덕트의 지표 플래그 계산
        metrics_analysis = self._analyze_metrics(products_data)

        # Gemini에 분석 요청
        prompt = self._build_analysis_prompt(summary, products_data, metrics_analysis)

        try:
            print(f"   💬 Gemini AI 분석 요청 중... (프롬프트 크기: {len(prompt)}자)")
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt
            )
            print(f"   ✅ Gemini AI 분석 완료")
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

    def _analyze_metrics(self, products_data: List[Dict]) -> str:
        """
        각 프로덕트의 지표를 분석하고 플래그 생성

        Args:
            products_data: 프로덕트 데이터 리스트

        Returns:
            지표 분석 결과 문자열
        """
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("📊 지표 기반 자동 분석 (Metrics Analysis)")
        lines.append("=" * 60)

        for data in products_data:
            product_name = data.get('name', 'Unknown')
            config = data.get('config', {})

            # 목표와 임계값 가져오기
            goals = config.get('goals', {})
            thresholds = config.get('thresholds', {})
            health_weights = config.get('health_score_weights', {})

            lines.append(f"\n## {product_name}")

            # 실제 지표 수집
            actual_metrics = self._extract_actual_metrics(data)

            # 목표 대비 달성률
            if goals:
                lines.append("\n### 🎯 목표 대비 달성률")
                achievement = self._calculate_goal_achievement(actual_metrics, goals)
                for metric, info in achievement.items():
                    flag = info['flag']
                    lines.append(f"  {flag} {info['label']}: {info['actual']} / {info['target']} ({info['achievement_rate']:.1f}%)")

            # 임계값 기반 플래그
            if thresholds:
                lines.append("\n### 🚦 지표 상태 플래그")
                flags = self._calculate_threshold_flags(actual_metrics, thresholds)
                for metric, info in flags.items():
                    lines.append(f"  {info['flag']} {info['label']}: {info['value']} - {info['status']}")

            # Health Score 계산
            if health_weights:
                health_score = self._calculate_health_score(actual_metrics, thresholds, health_weights)
                lines.append(f"\n### 💯 Health Score: {health_score:.1f}/100")

                if health_score >= 70:
                    lines.append("  ✅ 상태: 양호 (Healthy)")
                elif health_score >= 40:
                    lines.append("  ⚠️ 상태: 주의 필요 (Needs Attention)")
                else:
                    lines.append("  🚨 상태: 위험 (Critical)")

        return "\n".join(lines)

    def _extract_actual_metrics(self, data: Dict) -> Dict:
        """실제 수집된 데이터에서 지표 추출"""
        metrics = {}

        # GSC 데이터
        gsc_data = data.get('gsc')
        if gsc_data and gsc_data.get('top_queries') is not None:
            top_queries = gsc_data['top_queries']
            if not top_queries.empty:
                metrics['gsc_clicks'] = int(top_queries['clicks'].sum())
                metrics['gsc_impressions'] = int(top_queries['impressions'].sum())
                metrics['ctr_percent'] = (metrics['gsc_clicks'] / metrics['gsc_impressions'] * 100) if metrics['gsc_impressions'] > 0 else 0
                metrics['avg_position'] = float(top_queries['position'].mean())

        # GA4 데이터
        ga4_data = data.get('ga4')
        if ga4_data:
            pages = ga4_data.get('pages')
            if pages is not None and not pages.empty:
                metrics['sessions'] = int(pages['sessions'].sum())
                metrics['engagement_rate'] = float(pages['engagement_rate'].mean()) if 'engagement_rate' in pages.columns else 0

        # AdSense 데이터
        adsense_data = data.get('adsense')
        if adsense_data:
            metrics['revenue'] = adsense_data.get('revenue', 0)
            metrics['adsense_rpm'] = adsense_data.get('rpm', 0)

        return metrics

    def _calculate_goal_achievement(self, actual: Dict, goals: Dict) -> Dict:
        """목표 대비 달성률 계산"""
        achievement = {}

        # 세션
        if 'sessions' in actual and 'weekly_sessions' in goals:
            rate = (actual['sessions'] / goals['weekly_sessions'] * 100) if goals['weekly_sessions'] > 0 else 0
            flag = "🟢" if rate >= 100 else "🟡" if rate >= 50 else "🔴"
            achievement['sessions'] = {
                'label': '주간 세션',
                'actual': f"{actual['sessions']:,}",
                'target': f"{goals['weekly_sessions']:,}",
                'achievement_rate': rate,
                'flag': flag
            }

        # GSC 클릭
        if 'gsc_clicks' in actual and 'weekly_gsc_clicks' in goals:
            rate = (actual['gsc_clicks'] / goals['weekly_gsc_clicks'] * 100) if goals['weekly_gsc_clicks'] > 0 else 0
            flag = "🟢" if rate >= 100 else "🟡" if rate >= 50 else "🔴"
            achievement['gsc_clicks'] = {
                'label': '주간 GSC 클릭',
                'actual': f"{actual['gsc_clicks']:,}",
                'target': f"{goals['weekly_gsc_clicks']:,}",
                'achievement_rate': rate,
                'flag': flag
            }

        # CTR
        if 'ctr_percent' in actual and 'target_ctr_percent' in goals:
            rate = (actual['ctr_percent'] / goals['target_ctr_percent'] * 100) if goals['target_ctr_percent'] > 0 else 0
            flag = "🟢" if rate >= 100 else "🟡" if rate >= 50 else "🔴"
            achievement['ctr'] = {
                'label': 'CTR',
                'actual': f"{actual['ctr_percent']:.2f}%",
                'target': f"{goals['target_ctr_percent']:.2f}%",
                'achievement_rate': rate,
                'flag': flag
            }

        # 참여율
        if 'engagement_rate' in actual and 'target_engagement_rate' in goals:
            rate = (actual['engagement_rate'] / goals['target_engagement_rate'] * 100) if goals['target_engagement_rate'] > 0 else 0
            flag = "🟢" if rate >= 100 else "🟡" if rate >= 50 else "🔴"
            achievement['engagement'] = {
                'label': '참여율',
                'actual': f"{actual['engagement_rate']:.1f}%",
                'target': f"{goals['target_engagement_rate']:.1f}%",
                'achievement_rate': rate,
                'flag': flag
            }

        # 수익 (AdSense가 있는 경우)
        if 'revenue' in actual and 'weekly_revenue_usd' in goals:
            rate = (actual['revenue'] / goals['weekly_revenue_usd'] * 100) if goals['weekly_revenue_usd'] > 0 else 0
            flag = "🟢" if rate >= 100 else "🟡" if rate >= 50 else "🔴"
            achievement['revenue'] = {
                'label': '주간 수익',
                'actual': f"${actual['revenue']:.2f}",
                'target': f"${goals['weekly_revenue_usd']:.2f}",
                'achievement_rate': rate,
                'flag': flag
            }

        return achievement

    def _calculate_threshold_flags(self, actual: Dict, thresholds: Dict) -> Dict:
        """임계값 기반 플래그 계산"""
        flags = {}

        for metric, threshold in thresholds.items():
            if metric not in actual:
                continue

            value = actual[metric]
            critical = threshold.get('critical', 0)
            warning = threshold.get('warning', 0)

            # avg_position은 낮을수록 좋음 (역방향)
            if metric == 'avg_position':
                if value >= critical:
                    flag = "🔴"
                    status = "위험"
                elif value >= warning:
                    flag = "🟡"
                    status = "주의"
                else:
                    flag = "🟢"
                    status = "양호"
            else:
                # 나머지는 높을수록 좋음
                if value < critical:
                    flag = "🔴"
                    status = "위험"
                elif value < warning:
                    flag = "🟡"
                    status = "주의"
                else:
                    flag = "🟢"
                    status = "양호"

            # 라벨 매핑
            labels = {
                'gsc_clicks': 'GSC 클릭',
                'ctr_percent': 'CTR',
                'engagement_rate': '참여율',
                'adsense_rpm': 'AdSense RPM',
                'avg_position': '평균 순위',
                'sessions': 'GA4 세션'
            }

            # 값 포맷팅
            if metric in ['ctr_percent', 'engagement_rate']:
                value_str = f"{value:.2f}%"
            elif metric == 'adsense_rpm':
                value_str = f"${value:.2f}"
            elif metric == 'avg_position':
                value_str = f"{value:.1f}위"
            else:
                value_str = f"{int(value):,}"

            flags[metric] = {
                'flag': flag,
                'label': labels.get(metric, metric),
                'value': value_str,
                'status': status
            }

        return flags

    def _calculate_health_score(self, actual: Dict, thresholds: Dict, weights: Dict) -> float:
        """가중치 기반 Health Score 계산 (0-100)"""
        score = 0.0
        total_weight = 0.0

        # Traffic Score (GSC 클릭 + GA4 세션)
        if 'traffic' in weights:
            weight = weights['traffic']
            traffic_score = 0.0

            if 'gsc_clicks' in actual and 'gsc_clicks' in thresholds:
                clicks = actual['gsc_clicks']
                if clicks >= thresholds['gsc_clicks'].get('warning', 0):
                    traffic_score += 50
                elif clicks >= thresholds['gsc_clicks'].get('critical', 0):
                    traffic_score += 25

            if 'sessions' in actual and 'sessions' in thresholds:
                sessions = actual['sessions']
                if sessions >= thresholds['sessions'].get('warning', 0):
                    traffic_score += 50
                elif sessions >= thresholds['sessions'].get('critical', 0):
                    traffic_score += 25

            score += (traffic_score / 100) * weight
            total_weight += weight

        # Engagement Score
        if 'engagement' in weights and 'engagement_rate' in actual and 'engagement_rate' in thresholds:
            weight = weights['engagement']
            engagement = actual['engagement_rate']

            if engagement >= thresholds['engagement_rate'].get('warning', 0):
                engagement_score = 100
            elif engagement >= thresholds['engagement_rate'].get('critical', 0):
                engagement_score = 50
            else:
                engagement_score = 20

            score += (engagement_score / 100) * weight
            total_weight += weight

        # SEO Score (CTR + 평균 순위)
        if 'seo' in weights:
            weight = weights['seo']
            seo_score = 0.0

            if 'ctr_percent' in actual and 'ctr_percent' in thresholds:
                ctr = actual['ctr_percent']
                if ctr >= thresholds['ctr_percent'].get('warning', 0):
                    seo_score += 50
                elif ctr >= thresholds['ctr_percent'].get('critical', 0):
                    seo_score += 25

            if 'avg_position' in actual and 'avg_position' in thresholds:
                pos = actual['avg_position']
                # 순위는 낮을수록 좋음
                if pos <= thresholds['avg_position'].get('warning', 0):
                    seo_score += 50
                elif pos <= thresholds['avg_position'].get('critical', 0):
                    seo_score += 25

            score += (seo_score / 100) * weight
            total_weight += weight

        # Revenue Score
        if 'revenue' in weights and 'adsense_rpm' in actual and 'adsense_rpm' in thresholds:
            weight = weights['revenue']
            rpm = actual['adsense_rpm']

            if rpm >= thresholds['adsense_rpm'].get('warning', 0):
                revenue_score = 100
            elif rpm >= thresholds['adsense_rpm'].get('critical', 0):
                revenue_score = 50
            else:
                revenue_score = 0

            score += (revenue_score / 100) * weight
            total_weight += weight

        # 정규화
        if total_weight > 0:
            return (score / total_weight) * 100
        return 0.0

    def _build_analysis_prompt(self, summary: str, products_data: List[Dict], metrics_analysis: str) -> str:
        """
        Gemini에게 보낼 분석 프롬프트 생성

        Args:
            summary: 데이터 요약 문자열
            products_data: 원본 데이터 (필요시 참조)
            metrics_analysis: 지표 기반 자동 분석 결과

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

# 지표 기반 자동 분석
{metrics_analysis}

# 요청사항
위 데이터와 **지표 기반 자동 분석**을 바탕으로 **실행 가능한 비교 분석 리포트**를 작성해주세요.

**중요: 지표 기반 분석의 활용**
- 각 프로덕트의 Health Score를 참고하여 우선순위 결정
- 🔴 위험 플래그가 있는 지표는 즉시 개선 필요
- 🟡 주의 플래그가 있는 지표는 모니터링 및 개선 계획 수립
- 목표 대비 달성률이 50% 미만인 지표는 특별 관리 필요

다음 형식을 정확히 따라주세요:

---

# Multi-Product Analysis Report

## 📊 Executive Summary (핵심 요약)
- 각 프로덕트의 현재 상태를 Health Score와 함께 요약
- 🔴 위험 지표와 🟡 주의 지표를 명시
- 목표 대비 달성률이 낮은 지표 강조
- 가장 주목할 만한 인사이트 2-3개
- 이번 주 최우선 과제 1개

## 🏆 Product Performance Comparison (프로덕트 성과 비교)

### Health Score & 목표 달성률
| 프로덕트 | Health Score | 세션 달성률 | CTR 달성률 | 참여율 달성률 | 우선순위 |
|---------|-------------|------------|-----------|-------------|----------|
| ... | .../100 | ...% | ...% | ...% | ... |

### 트래픽 비교
| 프로덕트 | GSC 클릭 | GSC 노출 | CTR | GA4 세션 | 지표 상태 |
|---------|----------|----------|-----|----------|----------|
| ... | ... | ... | ... | ... | 🔴/🟡/🟢 |

### 핵심 지표 분석
- 어느 프로덕트가 더 효율적인가? (Health Score 기준)
- 목표 대비 달성률이 가장 낮은 지표는?
- 🔴 위험 플래그를 받은 지표와 원인
- 성장/하락 트렌드
- 특이사항

## 💰 Revenue & ROI Analysis (수익 및 ROI 분석)
※ AdSense가 있는 프로덕트만 해당
- 현재 수익 구조
- 트래픽 대비 수익 효율
- 개선 가능 영역

## 🎯 Resource Allocation Recommendations (리소스 배분 추천)
**Health Score와 목표 달성률을 기반으로 리소스를 배분하세요.**

### SEO 에이전트 운영 전략
- **프로덕트 A**: [주간/격주/월간] + 이유 (Health Score: XX/100, 🔴 위험 지표: ...)
- **프로덕트 B**: [주간/격주/월간] + 이유 (Health Score: XX/100, 🟡 주의 지표: ...)

### 마케팅 예산 배분 (100% 기준)
**Health Score가 낮고 목표 달성률이 낮은 프로덕트에 집중 투자**
- **프로덕트 A**: XX% - 근거 (Health Score, 목표 달성률, 위험 지표)
- **프로덕트 B**: YY% - 근거 (Health Score, 목표 달성률, 위험 지표)

### 우선순위 조정 제안
- 현재 우선순위가 Health Score 및 목표 달성률과 일치하는가?
- 변경 제안이 있다면? (데이터 근거 명시)

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
**🔴 위험 플래그를 받은 지표부터 우선 처리하세요.**

### 🔴 High Priority (긴급 - 이번 주)
**🔴 위험 플래그 지표 개선에 집중**
1. [구체적 액션] - 담당: [프로덕트], 대상 지표: [🔴 지표명], 목표: [현재값 → 목표값], 예상 효과: [숫자]
2. ...

### 🟡 Medium Priority (중요 - 다음 주)
**🟡 주의 플래그 지표 모니터링 및 개선**
1. [구체적 액션] - 담당: [프로덕트], 대상 지표: [🟡 지표명], 목표: [현재값 → 목표값]
2. ...

### 🟢 Low Priority (장기 - 2주 후)
**🟢 양호 지표 유지 및 최적화**
1. [구체적 액션] - 담당: [프로덕트], 목표: [추가 개선]
2. ...

---

**중요 원칙:**
1. **지표 기반 분석을 최우선으로 활용**
   - Health Score가 낮은 프로덕트에 집중
   - 🔴 위험 플래그 지표는 즉시 개선 액션 제안
   - 🟡 주의 플래그 지표는 모니터링 계획 수립
   - 목표 대비 달성률 50% 미만 지표는 특별 관리
2. 모든 판단은 **데이터 근거**를 명시 (Health Score, 목표 달성률, 플래그 상태)
3. 추측성 발언 최소화
4. 숫자는 구체적으로 (예: "많다" ❌, "1,234회" ✅)
5. 실행 가능한 액션만 제안 (목표값과 현재값을 명시)
6. 프로덕트 간 비교는 공정하게 (Health Score 기준)
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
