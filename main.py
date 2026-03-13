#!/usr/bin/env python3
"""
Unified Multi-Product Agent
여러 프로덕트의 SEO/마케팅 데이터를 통합 분석합니다.

실행 방법:
    python main.py
"""

import os
import sys
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(__file__))

from core.collectors.gsc_collector import GSCCollector
from core.collectors.ga4_collector import GA4Collector
from core.collectors.trends_collector import TrendsCollector
from core.collectors.adsense_collector import AdSenseCollector
from core.analyzers.comparative_analyzer import ComparativeAnalyzer
from core.utils.formatter import format_report_header, format_report_footer, save_report
from core.level2_agent import Level2Agent
from core.level2_agent_v2 import Level2AgentV2


def load_products_config():
    """products.yaml 설정 파일 로드"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'products.yaml')

    if not os.path.exists(config_path):
        print(f"❌ 설정 파일을 찾을 수 없습니다: {config_path}")
        print("   config/products.yaml 파일을 생성해주세요.")
        sys.exit(1)

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def collect_product_data(product_id: str, product_config: dict, credentials_path: str):
    """
    단일 프로덕트의 데이터 수집

    Args:
        product_id: 프로덕트 식별자 (예: 'qr-generator')
        product_config: 프로덕트 설정
        credentials_path: Google 인증 파일 경로

    Returns:
        수집된 데이터 딕셔너리
    """
    product_name = product_config.get('name', product_id)
    days = product_config.get('analysis_days', 7)

    print(f"\n{'='*60}")
    print(f"📊 {product_name} ({product_id}) 데이터 수집 중...")
    print(f"{'='*60}")

    data = {
        'id': product_id,
        'name': product_name,
        'config': product_config,
        'gsc': None,
        'ga4': None,
        'trends': None,
        'adsense': None
    }

    # 1. Google Search Console 데이터
    gsc_url = product_config.get('gsc_property_url')
    if gsc_url and not gsc_url.startswith('REPLACE'):
        try:
            print(f"\n  🔍 GSC 데이터 수집...")
            collector = GSCCollector(credentials_path, gsc_url)
            df_all = collector.fetch_search_analytics(days=days)

            if not df_all.empty:
                data['gsc'] = {
                    'top_queries': collector.get_top_queries(df_all, limit=20),
                    'opportunities': collector.get_opportunity_keywords(df_all, limit=10),
                    'page_performance': collector.get_page_performance(df_all)
                }
                print(f"     ✓ {len(df_all)}개 검색어 수집 완료")
            else:
                print(f"     ⚠️  수집된 데이터 없음")

        except Exception as e:
            print(f"     ❌ GSC 수집 실패: {str(e)}")
    else:
        print(f"  ⏭️  GSC 수집 건너뜀 (설정 필요)")

    # 2. Google Analytics 4 데이터
    ga4_id = product_config.get('ga4_property_id')
    if ga4_id and not str(ga4_id).startswith('REPLACE'):
        try:
            print(f"\n  📈 GA4 데이터 수집...")
            ga4_collector = GA4Collector(credentials_path, str(ga4_id))

            data['ga4'] = {
                'pages': ga4_collector.fetch_page_performance(days=days),
                'traffic': ga4_collector.fetch_traffic_sources(days=days),
                'devices': ga4_collector.fetch_device_breakdown(days=days),
                'events': ga4_collector.get_conversion_events(days=days)
            }
            print(f"     ✓ GA4 데이터 수집 완료")

        except Exception as e:
            print(f"     ❌ GA4 수집 실패: {str(e)}")
    else:
        print(f"  ⏭️  GA4 수집 건너뜀 (설정 필요)")

    # 3. Google Trends 데이터
    if data['gsc'] and data['gsc']['top_queries'] is not None:
        try:
            print(f"\n  📊 Google Trends 데이터 수집...")
            trends_collector = TrendsCollector()

            top_keywords = data['gsc']['top_queries']['query'].head(10).tolist()
            if top_keywords:
                data['trends'] = trends_collector.analyze_keyword_trends(
                    top_keywords,
                    timeframe='today 3-m'
                )
                print(f"     ✓ {len(top_keywords)}개 키워드 트렌드 분석 완료")

        except Exception as e:
            print(f"     ⚠️  Trends 수집 실패 (건너뜀): {str(e)}")

    # 4. AdSense 데이터 (있는 경우)
    if product_config.get('has_adsense'):
        try:
            print(f"\n  💰 AdSense 데이터 수집...")
            client_id = product_config.get('adsense_client_id', '')
            adsense_collector = AdSenseCollector(client_id)
            data['adsense'] = adsense_collector.get_revenue_data(days=days)

            if data['adsense']['source'] == 'manual':
                print(f"     ℹ️  환경변수에서 읽음 (ADSENSE_REVENUE, ADSENSE_IMPRESSIONS, ADSENSE_CLICKS)")
            print(f"     ✓ 수익: ${data['adsense']['revenue']:.2f}, RPM: ${data['adsense']['rpm']:.2f}")

        except Exception as e:
            print(f"     ❌ AdSense 수집 실패: {str(e)}")

    return data


def main():
    """메인 실행 함수"""
    print("=" * 60)
    print("🚀 Unified Multi-Product Agent 시작")
    print("=" * 60)

    # 1. 환경변수 로드
    load_dotenv()

    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("❌ GOOGLE_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   .env 파일을 생성하고 Gemini API 키를 입력해주세요.")
        return 1

    # 2. 설정 파일 로드
    config = load_products_config()
    products = config.get('products', {})

    if not products:
        print("❌ products.yaml에 프로덕트가 정의되지 않았습니다.")
        return 1

    print(f"\n📦 발견된 프로덕트: {len(products)}개")
    for product_id, product_config in products.items():
        print(f"   - {product_config.get('name', product_id)} ({product_id})")

    # 3. Google 인증 파일 확인
    credentials_path = os.path.join(
        os.path.dirname(__file__),
        'config',
        'gsc_credentials.json'
    )

    if not os.path.exists(credentials_path):
        print(f"\n❌ Google 인증 파일을 찾을 수 없습니다: {credentials_path}")
        print("   README.md의 설정 가이드를 참고해주세요.")
        return 1

    # 4. 각 프로덕트 데이터 수집
    all_data = []
    for product_id, product_config in products.items():
        try:
            product_data = collect_product_data(product_id, product_config, credentials_path)
            all_data.append(product_data)
        except Exception as e:
            print(f"\n❌ {product_id} 데이터 수집 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()

    if not all_data:
        print("\n❌ 수집된 데이터가 없습니다.")
        return 1

    # 5. 비교 분석
    print("\n" + "=" * 60)
    print("🤖 Gemini AI 통합 비교 분석 중...")
    print("=" * 60)

    analyzer = ComparativeAnalyzer(google_api_key)
    comparison_report = analyzer.analyze_products(all_data)

    # 6. 리포트 저장
    print("\n📝 리포트 저장 중...")

    # 통합 리포트
    timestamp = datetime.now().strftime('%Y-%m-%d')
    comparison_dir = os.path.join(os.path.dirname(__file__), 'reports', 'comparison')
    os.makedirs(comparison_dir, exist_ok=True)

    comparison_path = os.path.join(comparison_dir, f'{timestamp}_multi_product_analysis.md')

    # 리포트 헤더 추가
    product_names = ", ".join([d['name'] for d in all_data])
    end_date = datetime.now() - timedelta(days=3)
    start_date = end_date - timedelta(days=7)
    date_range = f"{start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}"

    full_report = f"""# Multi-Product Analysis Report
생성일: {timestamp}
분석 프로덕트: {product_names}
데이터 기간: {date_range}

---

{comparison_report}

---

*Generated by Unified Multi-Product Agent*
"""

    with open(comparison_path, 'w', encoding='utf-8') as f:
        f.write(full_report)

    print(f"✅ 통합 리포트 저장: {comparison_path}")

    # 개별 프로덕트 리포트도 저장 (선택사항)
    for data in all_data:
        product_dir = os.path.join(os.path.dirname(__file__), 'reports', data['id'])
        os.makedirs(product_dir, exist_ok=True)
        # 개별 리포트는 나중에 구현 가능

    # 7. 요약 출력
    print("\n" + "=" * 60)
    print("✨ 분석 완료!")
    print("=" * 60)
    print(f"\n📄 통합 리포트: {comparison_path}")
    print(f"📅 분석 기간: {date_range}")
    print(f"\n📊 수집된 프로덕트:")

    for data in all_data:
        gsc_count = len(data['gsc']['top_queries']) if data['gsc'] and data['gsc']['top_queries'] is not None else 0
        ga4_count = len(data['ga4']['pages']) if data['ga4'] and data['ga4']['pages'] is not None else 0
        print(f"   • {data['name']}: GSC {gsc_count}개, GA4 {ga4_count}개 페이지")

    print(f"\n💡 다음 실행 권장: {config.get('global', {}).get('report_frequency', 'biweekly')}")

    # 8. Level 2 Agent - 자동 PR 생성 (선택사항)
    enable_auto_pr = os.getenv('ENABLE_AUTO_PR', 'false').lower() == 'true'
    use_dispatch_v2 = os.getenv('USE_DISPATCH_V2', 'false').lower() == 'true'

    if enable_auto_pr:
        print("\n" + "=" * 60)
        if use_dispatch_v2:
            print("🤖 Level 2 Agent v2.0 - Repository Dispatch 시작")
        else:
            print("🤖 Level 2 Agent v1.0 - 자동 PR 생성 시작")
        print("=" * 60)

        try:
            github_token = os.getenv('GITHUB_TOKEN')
            if not github_token:
                print("⚠️  GITHUB_TOKEN이 설정되지 않아 PR 생성을 건너뜁니다.")
            else:
                if use_dispatch_v2:
                    # v2.0: Repository Dispatch 방식
                    print("📡 v2.0 모드: Repository Dispatch 이벤트 전송")

                    level2_agent = Level2AgentV2(
                        gemini_api_key=google_api_key,
                        github_token=github_token,
                        github_owner=os.getenv('GITHUB_OWNER', 'SangWoo9734'),
                        dry_run=False
                    )

                    # 생성된 리포트 처리
                    result = level2_agent.process_report(comparison_path)

                    # 결과 출력
                    if result['success']:
                        print(f"\n✅ Level 2 Agent v2.0 실행 완료!")
                        print(f"   추출된 액션: {result['actions_extracted']}개")
                        print(f"   안전한 액션: {result['actions_safe']}개")
                        print(f"   Dispatch 전송: {result['dispatched_success']}개 프로덕트")

                        if result.get('dispatched'):
                            print(f"\n📡 Dispatch 결과:")
                            for product, success in result['dispatched'].items():
                                status = "✅" if success else "❌"
                                print(f"   {status} {product}")

                        print(f"\n💡 각 프로덕트의 워크플로우에서 PR이 생성됩니다.")
                    else:
                        print(f"\n❌ Level 2 Agent v2.0 실행 실패: {result.get('error', 'Unknown error')}")

                else:
                    # v1.0: 직접 PR 생성 방식 (기존)
                    print("🔧 v1.0 모드: 직접 파일 수정 및 PR 생성")

                    level2_agent = Level2Agent(
                        workspace_root=os.path.dirname(__file__),
                        gemini_api_key=google_api_key,  # v1.0도 Gemini 사용
                        github_token=github_token,
                        base_branch="main",
                        dry_run=False
                    )

                    # 생성된 리포트 처리
                    result = level2_agent.process_report(comparison_path)

                    # 결과 출력
                    if result['success']:
                        print(f"\n✅ Level 2 Agent v1.0 실행 완료!")
                        print(f"   추출된 액션: {result['actions_extracted']}개")
                        print(f"   안전한 액션: {result['actions_safe']}개")
                        print(f"   실행된 액션: {result['actions_executed']}개")

                        if result.get('pr_url'):
                            print(f"\n🎉 GitHub PR 생성 완료:")
                            print(f"   {result['pr_url']}")
                        else:
                            print(f"\n⚠️  PR을 생성하지 못했습니다 (성공한 액션 없음)")
                    else:
                        print(f"\n❌ Level 2 Agent v1.0 실행 실패: {result.get('error', 'Unknown error')}")

        except Exception as e:
            version = "v2.0" if use_dispatch_v2 else "v1.0"
            print(f"\n❌ Level 2 Agent {version} 실행 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            # Level 2 실패는 전체 실행을 중단시키지 않음
    else:
        print(f"\n💡 Tip: ENABLE_AUTO_PR=true로 설정하면 자동으로 PR을 생성합니다.")
        print(f"   - USE_DISPATCH_V2=true: Repository Dispatch 방식 (v2.0)")
        print(f"   - USE_DISPATCH_V2=false: 직접 PR 생성 방식 (v1.0, 기본값)")

    return 0


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  사용자가 실행을 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
