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
        """
        product_names = [data.get('name', 'Unknown') for data in products_data]
        product_list = ", ".join(product_names)
        
        # 프레임워크 정보 포함한 상세 설명 생성
        product_contexts = []
        for data in products_data:
            name = data.get('name', 'Unknown')
            id = data.get('id', 'Unknown')
            framework = data.get('config', {}).get('framework', 'unknown')
            
            path_hint = "src/app/layout.tsx" if framework == "nextjs" else "pages/Home.tsx (or layouts/MainLayout.tsx)"
            product_contexts.append(f"- {name} ({id}): Framework={framework}, Best path example={path_hint}")
        
        context_str = "\n".join(product_contexts)

        prompt = f"""
당신은 여러 웹 프로덕트를 운영하는 마케팅 팀의 데이터 분석가이자 시니어 개발자입니다.
현재 운영 중인 프로덕트와 그 환경 정보:
{context_str}

# 수집된 데이터
{summary}

# 지표 기반 자동 분석
{metrics_analysis}

# 요청사항
위 데이터와 **지표 기반 자동 분석**을 바탕으로 **실행 가능한 비교 분석 리포트**를 작성해주세요.

**중요: 개선점(Action Plan) 작성 원칙**
1. **반드시 구체적인 코드 수정 사항을 제안**해야 합니다.
2. **반드시 실제 프로젝트 구조(Framework)에 맞는 파일 경로를 백틱으로 포함**하세요.
   - Next.js (qr-generator): `src/app/layout.tsx`, `src/app/page.tsx` 등 사용
   - Vite (convert-image): `pages/Home.tsx`, `src/App.tsx`, `Header.tsx` 등 사용 (Vite 프로젝트는 src/app 구조가 아님에 주의)
3. **최우선 과제(🔴 High Priority)는 프로덕트별로 최소 1-2개씩 반드시 생성**하세요.
4. **Action 리스트는 반드시 아래 형식을 정확히 유지**하세요 (Regex 파서용).

형식 예시:
1. **[QR Studio]** 메타 타이틀 수정 - File: `src/app/layout.tsx`
2. **[ConvertKits]** 랜딩 페이지 참여율 개선 - File: `pages/Home.tsx`

---

# Multi-Product Analysis Report

## 📊 Executive Summary (핵심 요약)
- 각 프로덕트의 현재 상태를 Health Score와 함께 요약
- 🔴 위험 지표와 🟡 주의 지표를 명시
- 가장 주목할 만한 인사이트 2-3개
- 이번 주 최우선 과제 1개

## 🏆 Product Performance Comparison (프로덕트 성과 비교)

### Health Score & 목표 달성률
| 프로덕트 | Health Score | 세션 달성률 | CTR 달성률 | 참여율 달성률 | 우선순위 |
|---------|-------------|------------|-----------|-------------|----------|
| ... | .../100 | ...% | ...% | ...% | ... |

### 핵심 지표 분석
- Health Score와 🔴 위험/🟡 주의 플래그를 기반으로 현 상태 진단
- 성장/하락 트렌드 및 원인 분석

## 🎯 Resource Allocation Recommendations (리소스 배분 추천)
- **프로덕트 A**: [주간/격주/월간] + 데이터 근거 (Health Score 등)
- **프로덕트 B**: [주간/격주/월간] + 데이터 근거

## ✅ This Week's Action Plan (이번 주 실행 계획)

### 🔴 High Priority (긴급 - 즉시 실행)
1. **[프로덕트명]** 액션내용 - File: `파일경로`
   - 대상 지표: 지표명, 현재: [값], 목표: [값]
   - 예상 효과: 구체적인 기대 효과

---

## 🤖 Machine-Readable Actions (DO NOT MODIFY)
아래는 자동화를 위한 데이터입니다. 반드시 정확한 JSON 형식을 유지하세요.
- **new_value**: 반드시 15자 이상의 구체적이고 매력적인 SEO 문구여야 합니다. (예: "이미지 변환 도구 | 온라인에서 무료로 JPG를 PNG로")
- "white", "btn", "click" 같이 짧거나 의미 없는 단어는 절대 금지입니다.

```json
[
  {{
    "product_id": "qr-generator",
    "action_type": "update_meta_title",
    "target_file": "src/app/layout.tsx",
    "parameters": {{"new_title": "QR 코드 생성기 | 쉽고 빠른 무료 온라인 서비스", "new_value": "QR 코드 생성기 | 쉽고 빠른 무료 온라인 서비스"}},
    "description": "메인 페이지 메타 타이틀 최적화"
  }},
  {{
    "product_id": "convert-image",
    "action_type": "update_meta_title",
    "target_file": "pages/Home.tsx",
    "parameters": {{"new_title": "이미지 변환 도구 | JPG PNG 변환 및 압축 무료 서비스", "new_value": "이미지 변환 도구 | JPG PNG 변환 및 압축 무료 서비스"}},
    "description": "랜딩 페이지 SEO 타이틀 강화"
  }}
]
```

### 🟡 Medium Priority (중요 - 다음 주)
1. [액션 내용] - 담당: [프로덕트]

### 🟢 Low Priority (건의 - 장기)
1. [액션 내용] - 담당: [프로덕트]

---

**중요 원칙:**
1. **파일 경로(`path/to/file`)가 없는 액션은 파서가 무시합니다. 반드시 포함하세요.**
2. 제안하는 메타 태그(Title, Description)는 실제 검색어 데이터를 기반으로 가장 효과적인 키워드를 포함해야 합니다.
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
