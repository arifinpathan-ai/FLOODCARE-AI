import os
import json
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def update_water_levels_sheet():
    print("🚀 กำลังเริ่มกระบวนการดึงข้อมูลน้ำและอัปเดต Google Sheets...")
    
    # 1. ดึงค่า Config และสิทธิ์ต่างๆ จาก Environment Variables บน Render
    api_key = os.environ.get("HAII_API_KEY")
    credentials_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS_JSON")
    
    if not credentials_json:
        print("❌ ไม่พบกุญแจ Google Credentials (GOOGLE_APPLICATION_CREDENTIALS_JSON)")
        return False

    # 2. เริ่มการดึงข้อมูลจาก Thaiwater API (/Runoff สำหรับข้อมูลน้ำท่า/ระดับน้ำ)
    base_url = "https://api.hii.or.th/twsapi/v1.0"
    endpoint = f"{base_url}/Runoff"
    
    params = {
        'latest': 'true',
        'interval': 'C-15'
    }
    
    headers = {
        'Accept': 'application/json',
        'User-Agent': 'Thaiwater-Python-Client/1.0'
    }
    if api_key:
        headers['X-API-KEY'] = api_key

    try:
        print(f"กำลังดึงข้อมูลจาก API: {endpoint}...")
        response = requests.get(endpoint, params=params, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ API Error: HTTP {response.status_code}")
            return False
            
        api_data = response.json()
        observations = api_data.get('timeSeriesObservation', [])
        print(f"✅ ดึงข้อมูลสำเร็จ! พบข้อมูลทั้งหมด {len(observations)} สถานี")

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการเชื่อมต่อ API: {e}")
        return False

    # 3. เชื่อมต่อกับ Google Sheets
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_dict = json.loads(credentials_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # เปิดไฟล์และแท็บที่ต้องการ
        sheet = client.open("FLOODCARE_DB").worksheet("Water_Levels")
        
        # เตรียมหัวตาราง (Headers)
        sheet_data = [["รหัสสถานี", "ประเภทข้อมูล", "ค่าวัดได้", "หน่วย", "เวลาที่บันทึกข้อมูล"]]
        
        # 4. แปลงข้อมูล JSON จาก API เพื่อเตรียมใส่ตาราง
        for obs in observations:
            station = obs.get('station', {})
            station_code = station.get('stationCode', 'N/A')
            results = obs.get('measurementResults', [])
            
            for res in results:
                variable = res.get('variable', 'N/A')
                value = res.get('value', 'N/A')
                uom = res.get('uom', 'N/A')
                measure_time = res.get('measureTime', 'N/A')
                
                # เพิ่มแถวข้อมูลเข้าลิสต์
                sheet_data.append([station_code, variable, value, uom, measure_time])
        
        # 5. ล้างข้อมูลเก่าในชีท แล้วเขียนข้อมูลใหม่ลงไปทั้งหมดทีเดียว (รวดเร็วและไม่ติดลิมิต)
        sheet.clear()
        sheet.update('A1', sheet_data)
        print("🎉 อัปเดตข้อมูลลง Google Sheets เรียบร้อยแล้ว!")
        return True

    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาดในการบันทึกข้อมูลลง Google Sheets: {e}")
        return False
