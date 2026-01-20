
import os
import sys
from datetime import datetime, timedelta
import pandas as pd
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

def get_daily_traffic(property_id, credentials_path, days=4):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )],
        dimensions=[Dimension(name="date")],
        metrics=[Metric(name="sessions")],
        order_bys=[{'dimension': {'dimension_name': 'date'}, 'desc': False}]
    )
    
    try:
        response = client.run_report(request)
        data = []
        for row in response.rows:
            data.append({
                'date': row.dimension_values[0].value,
                'sessions': int(row.metric_values[0].value)
            })
        return pd.DataFrame(data)
    except Exception as e:
        return f"Error: {str(e)}"

def get_gsc_data(property_url, credentials_path, days=7):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )
    service = build('webmasters', 'v3', credentials=credentials)
    
    end_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days+3)).strftime('%Y-%m-%d')
    
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query'],
        'rowLimit': 10
    }
    
    try:
        response = service.searchanalytics().query(siteUrl=property_url, body=request).execute()
        return response.get('rows', [])
    except Exception as e:
        return f"Error: {str(e)}"

def get_gsc_history(property_url, credentials_path, days=30):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/webmasters.readonly']
    )
    service = build('webmasters', 'v3', credentials=credentials)
    
    end_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=days+3)).strftime('%Y-%m-%d')
    
    request = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['date'],
        'rowLimit': 100
    }
    
    try:
        response = service.searchanalytics().query(siteUrl=property_url, body=request).execute()
        return response.get('rows', [])
    except Exception as e:
        return f"Error: {str(e)}"

def get_traffic_sources(property_id, credentials_path, start_date_str, end_date_str):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/analytics.readonly']
    )
    client = BetaAnalyticsDataClient(credentials=credentials)
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(
            start_date=start_date_str,
            end_date=end_date_str
        )],
        dimensions=[Dimension(name="sessionSource"), Dimension(name="sessionMedium")],
        metrics=[Metric(name="sessions")],
        order_bys=[{'metric': {'metric_name': 'sessions'}, 'desc': True}]
    )
    
    try:
        response = client.run_report(request)
        data = []
        for row in response.rows:
            data.append({
                'source': row.dimension_values[0].value,
                'medium': row.dimension_values[1].value,
                'sessions': int(row.metric_values[0].value)
            })
        return pd.DataFrame(data)
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    load_dotenv()
    credentials_path = '/Users/comento/agent-product/unified-agent/config/gsc_credentials.json'
    qr_property_id = "517636540"
    
    print("\n--- QR Studio Traffic Sources (Jan 08 - Jan 12: Before Drop) ---")
    print(get_traffic_sources(qr_property_id, credentials_path, "2026-01-08", "2026-01-12"))
    
    print("\n--- QR Studio Traffic Sources (Jan 13 - Jan 19: After Drop) ---")
    print(get_traffic_sources(qr_property_id, credentials_path, "2026-01-13", "2026-01-19"))
