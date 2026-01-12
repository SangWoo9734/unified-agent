"""
AdSense Collector (스켈레톤)
Google AdSense 수익 데이터를 수집합니다.

참고:
- AdSense Management API는 복잡하고 승인 과정이 필요합니다
- 현재는 수동 입력 또는 CSV 파일 업로드 방식을 권장합니다
- 향후 API 통합을 원하면 아래 TODO 참고
"""

from typing import Dict, Optional
import os


class AdSenseCollector:
    """AdSense 데이터 수집기 (수동 입력 기반)"""

    def __init__(self, client_id: str):
        """
        Args:
            client_id: AdSense 클라이언트 ID (예: ca-pub-1234567890)
        """
        self.client_id = client_id

    def get_revenue_data(self, days: int = 7) -> Dict:
        """
        AdSense 수익 데이터 가져오기

        현재는 환경변수나 수동 입력으로 대체합니다.
        실제 API 연동을 원하면 TODO 섹션 참고하세요.

        Args:
            days: 수집 기간 (일)

        Returns:
            {
                'revenue': float,  # 총 수익 (USD)
                'impressions': int,  # 광고 노출 수
                'clicks': int,  # 광고 클릭 수
                'ctr': float,  # 클릭률 (%)
                'rpm': float,  # 1000회 노출당 수익
            }
        """
        # 방법 1: 환경변수에서 읽기 (간단)
        revenue = float(os.getenv('ADSENSE_REVENUE', '0'))
        impressions = int(os.getenv('ADSENSE_IMPRESSIONS', '0'))
        clicks = int(os.getenv('ADSENSE_CLICKS', '0'))

        # 계산된 지표
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        rpm = (revenue / impressions * 1000) if impressions > 0 else 0

        return {
            'revenue': revenue,
            'impressions': impressions,
            'clicks': clicks,
            'ctr': ctr,
            'rpm': rpm,
            'source': 'manual'  # 수동 입력임을 표시
        }

    # TODO: AdSense Management API 통합
    # def get_revenue_from_api(self, credentials_path: str, days: int = 7):
    #     """
    #     실제 AdSense API를 사용하여 데이터 수집
    #
    #     설정 방법:
    #     1. Google Cloud Console에서 AdSense Management API 활성화
    #     2. OAuth 2.0 클라이언트 ID 생성
    #     3. 승인 절차 완료
    #     4. pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
    #
    #     참고: https://developers.google.com/adsense/management/
    #     """
    #     pass


class ManualAdSenseInput:
    """
    AdSense 데이터 수동 입력 헬퍼

    사용 예시:
        manual = ManualAdSenseInput()
        data = manual.input_from_console()
    """

    @staticmethod
    def input_from_console() -> Dict:
        """콘솔에서 수동 입력 받기"""
        print("\n📊 AdSense 데이터를 수동으로 입력하세요")
        print("(AdSense 대시보드에서 확인 가능)")
        print("-" * 40)

        try:
            revenue = float(input("수익 (USD): $"))
            impressions = int(input("광고 노출 수: "))
            clicks = int(input("광고 클릭 수: "))

            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            rpm = (revenue / impressions * 1000) if impressions > 0 else 0

            return {
                'revenue': revenue,
                'impressions': impressions,
                'clicks': clicks,
                'ctr': ctr,
                'rpm': rpm,
                'source': 'manual_console'
            }

        except (ValueError, KeyboardInterrupt):
            print("\n⚠️  입력이 취소되었습니다. AdSense 데이터는 0으로 설정됩니다.")
            return {
                'revenue': 0,
                'impressions': 0,
                'clicks': 0,
                'ctr': 0,
                'rpm': 0,
                'source': 'skipped'
            }


# 테스트용 메인 함수
if __name__ == '__main__':
    print("AdSense Collector 테스트")
    print("=" * 60)

    # 방법 1: 환경변수 (권장)
    print("\n방법 1: 환경변수에서 읽기")
    print("다음 환경변수를 설정하세요:")
    print("  ADSENSE_REVENUE=18.50")
    print("  ADSENSE_IMPRESSIONS=12450")
    print("  ADSENSE_CLICKS=89")

    collector = AdSenseCollector("ca-pub-example")
    data = collector.get_revenue_data()
    print(f"\n결과: {data}")

    # 방법 2: 수동 입력
    print("\n" + "=" * 60)
    print("방법 2: 콘솔에서 직접 입력")
    manual_data = ManualAdSenseInput.input_from_console()
    print(f"\n결과: {manual_data}")
