# ไฟล์: water_service.py
import gspread
import requests
import os
import json
from oauth2client.service_account import ServiceAccountCredentials

def update_water_levels_sheet():
    try:
        # 1. โหลดข้อมูล Service Account จาก Environment Variable
        creds_dict = json.loads(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON"))
        
        # 2. เชื่อมต่อ Google Sheets
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        sheet = client.open("FLOODCARE_DB").worksheet("Water_Levels")

        # 3. ดึงข้อมูลจาก API ของ สสน.
        api_url = "https://opendata.haii.or.th/api/v2/tele_waterlevel/latest"
        headers = {"Apikey": os.environ.get("HAII_API_KEY")}
        
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json().get('data', [])
            
            rows = []
            for item in data:
                station_info = item.get('station', {})
                rows.append([
                    station_info.get('tele_station_name', '-'),
                    item.get('waterlevel_mmsl', '-'),
                    item.get('waterlevel_datetime', '-'),
                    item.get('waterlevel_situation', '-')
                ])
            
            # 4. อัปเดตลงชีต
            sheet.clear() 
            sheet.append_row(["สถานี", "ระดับน้ำ(ม.)", "เวลา", "สถานการณ์"])
            sheet.append_rows(rows)
            return True
        return False
    except Exception as e:
        print(f"Error updating water levels: {e}")
        return False
