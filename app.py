import os
from sheets import get_water_data

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

import google.generativeai as genai

app = Flask(__name__)

# ดึงค่าคอนฟิกจาก Environment Variables
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ตั้งค่า LINE SDK
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ตั้งค่า Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 🎯 คำสั่งควบคุมพฤติกรรมของ AI
FLOODCARE_SYSTEM_PROMPT = """
คุณคือ "FLOODCARE AI" ผู้ช่วยอัจฉริยะที่เชี่ยวชาญและอุทิศตนเพื่อช่วยเหลือประชาชนในด้านการเฝ้าระวังน้ำท่วม สภาพอากาศ และความปลอดภัยจากภัยพิบัติ

[กฎเหล็กการตอบคำถามนอกขอบเขต (Out-of-Scope)]
- หากผู้ใช้ถามคำถามทั่วไปที่ไม่เกี่ยวข้องกับเรื่องน้ำท่วม สภาพอากาศ หรือความปลอดภัยโดยสิ้นเชิง (เช่น การหาอาหาร, เรื่องบันเทิง, มุกตลก) คุณต้อง "ปฏิเสธอย่างสุภาพและนุ่มนวล"
- ห้ามพยายามตอบคำถามนั้นเด็ดขาด แต่ให้แสดงความห่วงใยและดึงผู้ใช้กลับเข้าสู่เรื่องความปลอดภัย
- น้ำเสียงในการตอบ: เป็นมิตร สุภาพ มีความเห็นอกเห็นใจ

[ตัวอย่างแนวทางการปฏิเสธ]
"ขออภัยด้วยนะครับ/ค่ะ FLOODCARE AI เป็นผู้ช่วยเฉพาะทางด้านการเฝ้าระวังน้ำท่วมและสภาพอากาศเพื่อความปลอดภัย จึงอาจจะไม่สามารถแนะนำเรื่องนี้ได้โดยตรง... แต่ถ้าตอนนี้ในพื้นที่ของคุณมีปัญหาน้ำท่วม หรือต้องการเช็กระดับน้ำ พิมพ์บอกได้เลยนะครับ!"
"""

model = genai.GenerativeModel(
    model_name='gemini-2.5-flash',
    system_instruction=FLOODCARE_SYSTEM_PROMPT
)

# ==========================================
# ข้อความตอบกลับอัตโนมัติ
# ==========================================
GREETING_MSG = """สวัสดีครับ
ผมคือ FLOODCARE AI
น้องบอทผู้ช่วยอัจฉริยะสำหรับติดตามสถานการณ์น้ำ แจ้งเหตุฉุกเฉิน และช่วยเหลือผู้ประสบภัยครับ

🔍 ผมช่วยคุณได้ดังนี้ครับ:
1. 📞 เบอร์โทรฉุกเฉิน
2. 🚨 SOS แจ้งเหตุกู้ภัย
3. 🏠 ค้นหาศูนย์อพยพ
4. 🌊 ตรวจสอบระดับน้ำจริง
5. 📦 ขอความช่วยเหลือสิ่งของ
6. 🤖 สอบถามข้อมูลภัยพิบัติ สภาพอากาศ หรืออาการเจ็บป่วย

ยินดีช่วยเหลือเคียงข้างคุณตลอด 24 ชั่วโมงครับ 💧"""

EMERGENCY_MSG = """📞 เบอร์โทรฉุกเฉิน:

🚨 ปภ. (กรมป้องกันและบรรเทาสาธารณภัย)
📞 1784
📝 รับแจ้งเหตุเตือนภัยและช่วยเหลืออุทกภัย สายด่วน

🚨 สพฉ. (สถาบันการแพทย์ฉุกเฉินแห่งชาติ)
📞 1669
📝 รับส่งต่อผู้ป่วยและเจ็บป่วยฉุกเฉินทางการแพทย์

🚨 ตำรวจทางหลวง
📞 1193
📝 ประสานงานความช่วยเหลือเส้นทางน้ำท่วมและดินถล่ม

🚨 ศูนย์รับเรื่องร้องเรียนน้ำท่วมรัฐบาล
📞 1111
📝 ร้องเรียนและขอความช่วยเหลือทั่วไปส่วนกลาง"""

@app.route("/")
def index():
    return "FLOODCARE-AI Bot is running perfectly!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ==========================================
# ระบบจัดการข้อความจากผู้ใช้
# ==========================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    
    # ดักจับคำทักทาย
    if user_text in ["สวัสดี", "สวัสดีครับ", "สวัสดีค่ะ", "เริ่มการใช้งาน"]:
        reply_message = TextSendMessage(text=GREETING_MSG)
        line_bot_api.reply_message(event.reply_token, reply_message)
        
    # ดักจับคำขอดูเบอร์ฉุกเฉิน
    elif user_text in ["เบอร์โทรฉุกเฉิน", "เบอร์โทรศัพท์ฉุกเฉิน", "1"]:
        reply_message = TextSendMessage(text=EMERGENCY_MSG)
        line_bot_api.reply_message(event.reply_token, reply_message)
        
    # ถ้าเป็นข้อความอื่นๆ ส่งให้ Gemini ประมวลผลร่วมกับข้อมูลจาก Google Sheets
    else:
        if not GEMINI_API_KEY:
            reply_text = "❌ ระบบยังไม่ได้ตั้งค่า GEMINI_API_KEY"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        else:
            try:
                # ดึงข้อมูลจาก Google Sheets ผ่าน sheets.py
                water_data = get_water_data()

                full_prompt = f"""
                คำถามจากผู้ใช้: {user_text}

                ข้อมูลระดับน้ำล่าสุดจากระบบ (Google Sheet):
                {water_data}

                โปรดนำข้อมูลระดับน้ำข้างต้นมาสรุปตอบผู้ใช้ให้เข้าใจง่าย
                """

                response = model.generate_content(full_prompt)

                if response.parts:
                    reply_text = response.text

                    # แปลงคำตอบเป็น Flex Message
                    flex_reply = FlexSendMessage(
                        alt_text="คำตอบจาก FLOODCARE AI",
                        contents={
                            "type": "bubble",
                            "body": {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "🤖 FLOODCARE AI",
                                        "weight": "bold",
                                        "color": "#1E40AF"
                                    },
                                    {"type": "separator", "margin": "md"},
                                    {
                                        "type": "text",
                                        "text": reply_text,
                                        "wrap": True,
                                        "margin": "lg",
                                        "color": "#374151"
                                    }
                                ]
                            }
                        }
                    )
                    line_bot_api.reply_message(event.reply_token, flex_reply)
                else:
                    reply_text = "⚠️ Gemini ไม่สามารถตอบข้อความนี้ได้"
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
            except Exception as e:
                reply_text = f"❌ Gemini API Error:\n{str(e)}"
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

@app.route("/update-water-data", methods=["GET"])
def trigger_update():
    return "Update Success", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)








