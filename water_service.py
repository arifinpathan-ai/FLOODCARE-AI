import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# สร้างเป็นฟังก์ชันธรรมดา เพื่อให้ app.py เรียกใช้
def update_thaiwater_data():
    print("🚀 กำลังเริ่มกระบวนการดึงข้อมูลน้ำและอัปเดต Google Sheets...")
    try:
        # 1. ตั้งค่า Google Sheets (ใช้โค้ดเดิมของคุณที่ตั้งค่าจาก Environment Variables)
        credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if not credentials_json:
            return "❌ ไม่พบกุญแจ Google Credentials"
        
        creds_dict = json.loads(credentials_json)
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # 2. เริ่มดึงข้อมูลจาก Thaiwater API v3
        url = "https://api-v3.thaiwater.net/api/v3/001/vicinity_waterlevel?locale=th"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return f"❌ ไม่สามารถเชื่อมต่อ API ได้ Status Code: {response.status_code}"
            
        json_data = response.json()
        station_list = json_data.get('data', [])
        
        if not station_list:
            return "❌ ไม่พบข้อมูลสถานีวัดน้ำจาก API"

        # 3. อัปเดตลง Google Sheets
        # *** อย่าลืมเปลี่ยนชื่อตรงนี้ให้ตรงกับไฟล์ชีทของคุณ ***
        sheet = client.open('YOUR_SHEET_NAME').worksheet('WaterLevel')
        
        new_rows = []
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for station in station_list:
            station_id = station.get('station', {}).get('id', 'N/A')
            station_name = station.get('station', {}).get('station_name', 'N/A')
            province = station.get('station', {}).get('province_name', 'N/A')
            water_value = station.get('waterlevel', 'N/A')
            situation = station.get('situation', 'N/A') 
            
            new_rows.append([current_time, station_id, station_name, province, water_value, situation])
            
        if new_rows:
            sheet.resize(1) # เคลียร์ข้อมูลเก่า
            sheet.append_rows(new_rows) # ใส่ข้อมูลใหม่
            
        return f"✅ ดึงข้อมูลและอัปเดตลง Google Sheets จำนวน {len(new_rows)} สถานี สำเร็จเรียบร้อย!"

    except Exception as e:
        return f"❌ เกิดข้อผิดพลาดของระบบ: {str(e)}"
