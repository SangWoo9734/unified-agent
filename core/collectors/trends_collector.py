"""
Google Trends Data Collector

Google Trends를 사용하여 검색어 트렌드 데이터를 수집합니다.
"""

import time
from typing import List, Optional
import pandas as pd
from pytrends.request import TrendReq


class TrendsCollector:
    """Google Trends 데이터 수집기"""

    def __init__(self):
        """
        pytrends 클라이언트 초기화
        """
        self.pytrends = TrendReq(hl='en-US', tz=360)

    def get_interest_over_time(
        self,
        keywords: List[str],
        timeframe: str = 'today 3-m'
    ) -> pd.DataFrame:
        """
        검색어의 시간별 인기도 추이

        Args:
            keywords: 검색어 리스트 (최대 5개)
            timeframe: 기간 ('today 3-m', 'today 12-m', 'today 5-y')

        Returns:
            시간별 인기도 DataFrame
        """
        if not keywords:
            return pd.DataFrame()

        # Google Trends는 한 번에 최대 5개까지만
        keywords = keywords[:5]

        try:
            self.pytrends.build_payload(
                keywords,
                cat=0,
                timeframe=timeframe,
                geo='',  # 전 세계
                gprop=''
            )

            df = self.pytrends.interest_over_time()

            if df.empty:
                print(f"⚠️  Trends: '{keywords}' 데이터 없음")
                return pd.DataFrame()

            # 'isPartial' 컬럼 제거
            if 'isPartial' in df.columns:
                df = df.drop(columns=['isPartial'])

            print(f"✅ Trends: {len(keywords)}개 키워드 시간별 추이 수집")
            return df

        except Exception as e:
            print(f"❌ Trends 수집 실패 ({keywords}): {str(e)}")
            return pd.DataFrame()

    def get_related_queries(self, keyword: str) -> dict:
        """
        관련 검색어 및 급상승 검색어

        Args:
            keyword: 메인 검색어

        Returns:
            {'rising': DataFrame, 'top': DataFrame}
        """
        try:
            self.pytrends.build_payload([keyword], cat=0, timeframe='today 3-m')
            related = self.pytrends.related_queries()

            result = related.get(keyword, {})

            rising = result.get('rising', pd.DataFrame())
            top = result.get('top', pd.DataFrame())

            if not rising.empty:
                print(f"✅ Trends: '{keyword}' 관련 급상승 검색어 {len(rising)}개")
            if not top.empty:
                print(f"✅ Trends: '{keyword}' 관련 인기 검색어 {len(top)}개")

            return {'rising': rising, 'top': top}

        except Exception as e:
            print(f"❌ Trends 관련 검색어 실패 ({keyword}): {str(e)}")
            return {'rising': pd.DataFrame(), 'top': pd.DataFrame()}

    def analyze_keyword_trends(
        self,
        keywords: List[str],
        timeframe: str = 'today 3-m'
    ) -> pd.DataFrame:
        """
        여러 키워드의 트렌드를 분석하여 요약

        Args:
            keywords: 분석할 키워드 리스트
            timeframe: 기간

        Returns:
            키워드별 트렌드 요약 DataFrame
        """
        all_trends = []

        # 5개씩 나누어 처리 (Google Trends 제한)
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i+5]
            df = self.get_interest_over_time(batch, timeframe)

            if df.empty:
                continue

            # 각 키워드별 통계 계산
            for keyword in batch:
                if keyword not in df.columns:
                    continue

                series = df[keyword]

                # 최근 값과 과거 값 비교하여 트렌드 계산
                recent_avg = series.tail(4).mean()  # 최근 4주
                past_avg = series.head(8).mean()    # 과거 8주

                if past_avg > 0:
                    trend_change = ((recent_avg - past_avg) / past_avg) * 100
                else:
                    trend_change = 0

                all_trends.append({
                    'keyword': keyword,
                    'recent_avg': recent_avg,
                    'past_avg': past_avg,
                    'trend_change_pct': trend_change,
                    'max_interest': series.max(),
                    'current_interest': series.iloc[-1] if len(series) > 0 else 0
                })

            # API 제한 방지를 위한 딜레이
            time.sleep(1)

        if not all_trends:
            return pd.DataFrame()

        result_df = pd.DataFrame(all_trends)
        result_df = result_df.sort_values('trend_change_pct', ascending=False)

        print(f"✅ Trends: {len(result_df)}개 키워드 트렌드 분석 완료")
        return result_df

    def get_regional_interest(self, keyword: str) -> pd.DataFrame:
        """
        지역별 인기도

        Args:
            keyword: 검색어

        Returns:
            지역별 인기도 DataFrame
        """
        try:
            self.pytrends.build_payload([keyword], cat=0, timeframe='today 3-m')
            df = self.pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True, inc_geo_code=False)

            if df.empty:
                return pd.DataFrame()

            # 상위 10개 국가만
            df = df.sort_values(by=keyword, ascending=False).head(10)

            print(f"✅ Trends: '{keyword}' 지역별 인기도 수집 ({len(df)}개 국가)")
            return df

        except Exception as e:
            print(f"❌ Trends 지역별 인기도 실패 ({keyword}): {str(e)}")
            return pd.DataFrame()


if __name__ == '__main__':
    """테스트용 실행 코드"""

    collector = TrendsCollector()

    # 테스트 키워드
    test_keywords = [
        'heic to jpg',
        'image converter',
        'pdf converter',
        'compress image',
        'webp converter'
    ]

    print("\n📈 검색어 트렌드 분석:")
    trends = collector.analyze_keyword_trends(test_keywords, timeframe='today 3-m')
    print(trends)

    print("\n🔥 'heic to jpg' 관련 검색어:")
    related = collector.get_related_queries('heic to jpg')
    if not related['rising'].empty:
        print("\n급상승:")
        print(related['rising'].head())
    if not related['top'].empty:
        print("\n인기:")
        print(related['top'].head())

    print("\n🌍 'heic to jpg' 지역별 인기도:")
    regional = collector.get_regional_interest('heic to jpg')
    print(regional)
