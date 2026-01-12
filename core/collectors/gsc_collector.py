"""
Google Search Console Data Collector

이 모듈은 Google Search Console API를 사용하여 검색 데이터를 수집합니다.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd


class GSCCollector:
    """Google Search Console 데이터 수집기"""

    def __init__(self, credentials_path: str, property_url: str):
        """
        Args:
            credentials_path: 서비스 계정 JSON 키 파일 경로
            property_url: GSC 속성 URL (예: https://convertkits.org)
        """
        self.property_url = property_url
        self.credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/webmasters.readonly']
        )
        self.service = build('searchconsole', 'v1', credentials=self.credentials)

    def fetch_search_analytics(
        self,
        days: int = 7,
        dimensions: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        검색 분석 데이터 가져오기

        Args:
            days: 가져올 일수 (기본: 7일)
            dimensions: 차원 목록 (기본: ['query', 'page'])

        Returns:
            pandas DataFrame with search analytics data
        """
        if dimensions is None:
            dimensions = ['query', 'page']

        # 날짜 범위 계산 (GSC는 3일 전 데이터까지만 안정적)
        end_date = datetime.now() - timedelta(days=3)
        start_date = end_date - timedelta(days=days)

        request_body = {
            'startDate': start_date.strftime('%Y-%m-%d'),
            'endDate': end_date.strftime('%Y-%m-%d'),
            'dimensions': dimensions,
            'rowLimit': 1000,  # 최대 1000개 행
            'startRow': 0
        }

        try:
            response = self.service.searchanalytics().query(
                siteUrl=self.property_url,
                body=request_body
            ).execute()

            if 'rows' not in response:
                print(f"⚠️  데이터가 없습니다 ({start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')})")
                return pd.DataFrame()

            # 데이터를 DataFrame으로 변환
            rows = []
            for row in response['rows']:
                data = {
                    'query': row['keys'][0] if len(dimensions) > 0 else None,
                    'page': row['keys'][1] if len(dimensions) > 1 else None,
                    'clicks': row['clicks'],
                    'impressions': row['impressions'],
                    'ctr': row['ctr'],
                    'position': row['position']
                }
                rows.append(data)

            df = pd.DataFrame(rows)

            print(f"✅ {len(df)}개의 검색 데이터를 수집했습니다.")
            print(f"   기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

            return df

        except Exception as e:
            print(f"❌ GSC 데이터 수집 실패: {str(e)}")
            raise

    def get_top_queries(self, df: pd.DataFrame, limit: int = 20) -> pd.DataFrame:
        """클릭수 상위 검색어 추출"""
        return df.nlargest(limit, 'clicks')

    def get_opportunity_keywords(self, df: pd.DataFrame, limit: int = 10) -> pd.DataFrame:
        """
        기회 키워드 찾기 (노출은 많지만 클릭률이 낮은 키워드)

        Args:
            df: 검색 데이터 DataFrame
            limit: 반환할 키워드 수

        Returns:
            기회 키워드 DataFrame
        """
        # 최소 노출 수 조건 (노출 100 이상)
        df_filtered = df[df['impressions'] >= 100].copy()

        # CTR이 낮은 순서로 정렬
        opportunities = df_filtered.nsmallest(limit, 'ctr')

        return opportunities

    def get_page_performance(self, df: pd.DataFrame) -> pd.DataFrame:
        """페이지별 성과 집계"""
        if df.empty:
            return pd.DataFrame()

        page_stats = df.groupby('page').agg({
            'clicks': 'sum',
            'impressions': 'sum',
            'position': 'mean'
        }).reset_index()

        page_stats['ctr'] = page_stats['clicks'] / page_stats['impressions']
        page_stats = page_stats.sort_values('clicks', ascending=False)

        return page_stats


if __name__ == '__main__':
    """테스트용 실행 코드"""
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'gsc_credentials.json')
    property_url = os.getenv('GSC_PROPERTY_URL', 'https://convertkits.org')

    if not os.path.exists(credentials_path):
        print(f"❌ 인증 파일을 찾을 수 없습니다: {credentials_path}")
        sys.exit(1)

    collector = GSCCollector(credentials_path, property_url)
    df = collector.fetch_search_analytics(days=7)

    if not df.empty:
        print("\n📊 상위 10개 검색어:")
        print(collector.get_top_queries(df, limit=10))

        print("\n💎 기회 키워드:")
        print(collector.get_opportunity_keywords(df, limit=5))
