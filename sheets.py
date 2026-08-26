import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_water_data():
    """ฟังก์ชันสำหรับดึงข้อมูลระดับน้ำจาก Google Sheet"""
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    # อ่านกุญแจจาก Environment Variable บน Render
    json_str = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not json_str:
        print("❌ ไม่พบกุญแจ GOOGLE_APPLICATION_CREDENTIALS")
        return []

    try:
        info = json.loads(json_str)
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        gc = gspread.authorize(creds)
        
        SPREADSHEET_ID = '1QDn8Dx3FJeb7as03aWm04W8212HrjuNJa7rssJu1lE0'
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.get_worksheet(0)
        
        return worksheet.get_all_records()
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
        return []

        
