"""
Google Analytics 4 Data Collector

GA4 API를 사용하여 사용자 행동 데이터를 수집합니다.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2 import service_account
import pandas as pd


class GA4Collector:
    """Google Analytics 4 데이터 수집기"""

    def __init__(self, credentials_path: str, property_id: str):
        """
        Args:
            credentials_path: 서비스 계정 JSON 키 파일 경로
            property_id: GA4 속성 ID (예: 123456789)
        """
        self.property_id = property_id
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )
        self.client = BetaAnalyticsDataClient(credentials=credentials)

    def fetch_page_performance(self, days: int = 7) -> pd.DataFrame:
        """
        페이지별 성과 데이터 가져오기

        Args:
            days: 가져올 일수

        Returns:
            페이지별 성과 DataFrame
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )],
            dimensions=[
                Dimension(name="pagePath"),
                Dimension(name="pageTitle")
            ],
            metrics=[
                Metric(name="screenPageViews"),
                Metric(name="sessions"),
                Metric(name="averageSessionDuration"),
                Metric(name="bounceRate"),
                Metric(name="engagementRate")
            ],
            limit=50,
            order_bys=[{
                'metric': {'metric_name': 'screenPageViews'},
                'desc': True
            }]
        )

        try:
            response = self.client.run_report(request)

            rows = []
            for row in response.rows:
                data = {
                    'page_path': row.dimension_values[0].value,
                    'page_title': row.dimension_values[1].value,
                    'pageviews': int(row.metric_values[0].value),
                    'sessions': int(row.metric_values[1].value),
                    'avg_session_duration': float(row.metric_values[2].value),
                    'bounce_rate': float(row.metric_values[3].value),
                    'engagement_rate': float(row.metric_values[4].value)
                }
                rows.append(data)

            df = pd.DataFrame(rows)
            print(f"✅ GA4: {len(df)}개 페이지 성과 데이터 수집")
            return df

        except Exception as e:
            print(f"❌ GA4 데이터 수집 실패: {str(e)}")
            return pd.DataFrame()

    def fetch_traffic_sources(self, days: int = 7) -> pd.DataFrame:
        """
        트래픽 소스별 데이터 가져오기

        Args:
            days: 가져올 일수

        Returns:
            트래픽 소스 DataFrame
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )],
            dimensions=[
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium")
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="engagementRate"),
                Metric(name="averageSessionDuration")
            ],
            limit=20,
            order_bys=[{
                'metric': {'metric_name': 'sessions'},
                'desc': True
            }]
        )

        try:
            response = self.client.run_report(request)

            rows = []
            for row in response.rows:
                data = {
                    'source': row.dimension_values[0].value,
                    'medium': row.dimension_values[1].value,
                    'sessions': int(row.metric_values[0].value),
                    'engagement_rate': float(row.metric_values[1].value),
                    'avg_session_duration': float(row.metric_values[2].value)
                }
                rows.append(data)

            df = pd.DataFrame(rows)
            print(f"✅ GA4: {len(df)}개 트래픽 소스 수집")
            return df

        except Exception as e:
            print(f"❌ GA4 트래픽 소스 수집 실패: {str(e)}")
            return pd.DataFrame()

    def fetch_device_breakdown(self, days: int = 7) -> pd.DataFrame:
        """
        디바이스별 데이터 가져오기

        Args:
            days: 가져올 일수

        Returns:
            디바이스별 DataFrame
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )],
            dimensions=[
                Dimension(name="deviceCategory")
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="engagementRate"),
                Metric(name="bounceRate")
            ]
        )

        try:
            response = self.client.run_report(request)

            rows = []
            for row in response.rows:
                data = {
                    'device': row.dimension_values[0].value,
                    'sessions': int(row.metric_values[0].value),
                    'engagement_rate': float(row.metric_values[1].value),
                    'bounce_rate': float(row.metric_values[2].value)
                }
                rows.append(data)

            df = pd.DataFrame(rows)
            print(f"✅ GA4: 디바이스 데이터 수집 ({len(df)}개 카테고리)")
            return df

        except Exception as e:
            print(f"❌ GA4 디바이스 데이터 수집 실패: {str(e)}")
            return pd.DataFrame()

    def get_conversion_events(self, days: int = 7) -> pd.DataFrame:
        """
        전환 이벤트 데이터 가져오기 (파일 다운로드 등)

        Args:
            days: 가져올 일수

        Returns:
            이벤트 DataFrame
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        request = RunReportRequest(
            property=f"properties/{self.property_id}",
            date_ranges=[DateRange(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )],
            dimensions=[
                Dimension(name="eventName")
            ],
            metrics=[
                Metric(name="eventCount"),
                Metric(name="eventCountPerUser")
            ],
            limit=20,
            order_bys=[{
                'metric': {'metric_name': 'eventCount'},
                'desc': True
            }]
        )

        try:
            response = self.client.run_report(request)

            rows = []
            for row in response.rows:
                data = {
                    'event_name': row.dimension_values[0].value,
                    'event_count': int(row.metric_values[0].value),
                    'events_per_user': float(row.metric_values[1].value)
                }
                rows.append(data)

            df = pd.DataFrame(rows)
            print(f"✅ GA4: {len(df)}개 이벤트 데이터 수집")
            return df

        except Exception as e:
            print(f"❌ GA4 이벤트 데이터 수집 실패: {str(e)}")
            return pd.DataFrame()


if __name__ == '__main__':
    """테스트용 실행 코드"""
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    credentials_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'gsc_credentials.json')
    property_id = os.getenv('GA4_PROPERTY_ID')

    if not property_id:
        print("❌ GA4_PROPERTY_ID 환경변수가 설정되지 않았습니다.")
        sys.exit(1)

    if not os.path.exists(credentials_path):
        print(f"❌ 인증 파일을 찾을 수 없습니다: {credentials_path}")
        sys.exit(1)

    collector = GA4Collector(credentials_path, property_id)

    print("\n📊 페이지 성과:")
    print(collector.fetch_page_performance(days=7).head())

    print("\n📈 트래픽 소스:")
    print(collector.fetch_traffic_sources(days=7))

    print("\n📱 디바이스 분석:")
    print(collector.fetch_device_breakdown(days=7))

    print("\n🎯 이벤트 추적:")
    print(collector.fetch_conversion_events(days=7).head(10))
