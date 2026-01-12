"""
Utility functions for formatting data
"""

from datetime import datetime


def format_report_header(site_url: str, date_range: str) -> str:
    """리포트 헤더 생성"""
    today = datetime.now().strftime('%Y-%m-%d')

    header = f"""# ConvertKits SEO Weekly Report
Generated: {today}
Site: {site_url}
Data Period: {date_range}

---

"""
    return header


def format_report_footer() -> str:
    """리포트 푸터 생성"""
    footer = """
---

*이 리포트는 Claude AI 에이전트가 자동 생성했습니다.*
*실행 방법: `cd agent && python main.py`*
"""
    return footer


def save_report(content: str, output_dir: str = 'reports') -> str:
    """
    리포트를 파일로 저장

    Args:
        content: 리포트 내용
        output_dir: 저장할 디렉토리

    Returns:
        저장된 파일 경로
    """
    import os
    from datetime import datetime

    os.makedirs(output_dir, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    filename = f"{today}_seo_report.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    return filepath
