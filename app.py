import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
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
# ใช้โมเดลรุ่นปัจจุบัน
model = genai.GenerativeModel('gemini-2.5-flash')

# ==========================================
# ส่วนที่ 1: เตรียมข้อความตอบกลับอัตโนมัติ (ไม่ต้องใช้ AI)
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
# ส่วนที่ 2: ระบบคัดกรองข้อความ (ดักคีย์เวิร์ด)
# ==========================================
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip() # รับข้อความที่ผู้ใช้พิมพ์มา
    
    # ดักจับคำทักทาย
    if user_text in ["สวัสดี", "สวัสดีครับ", "สวัสดีค่ะ", "เริ่มการใช้งาน"]:
        reply_message = TextSendMessage(text=GREETING_MSG)
        line_bot_api.reply_message(event.reply_token, reply_message)
        
    # ดักจับคำขอดูเบอร์ฉุกเฉิน
    elif user_text in ["เบอร์โทรฉุกเฉิน", "เบอร์โทรศัพท์ฉุกเฉิน", "1"]:
        reply_message = TextSendMessage(text=EMERGENCY_MSG)
        line_bot_api.reply_message(event.reply_token, reply_message)
        
    # ถ้าพิมพ์คำอื่นๆ ที่ไม่ได้กำหนดไว้ ให้ส่งไปถาม AI Gemini
    else:
        if not GEMINI_API_KEY:
            reply_text = "❌ ระบบยังไม่ได้ตั้งค่า GEMINI_API_KEY"
        else:
            try:
                response = model.generate_content(user_text)
                if response.parts:
                    reply_text = response.text
                else:
                    reply_text = "⚠️ Gemini ไม่สามารถตอบข้อความนี้ได้เนื่องจากติดตัวกรองความปลอดภัย"
            except Exception as e:
                reply_text = f"❌ Gemini API Error:\n{str(e)}"

        # ส่งข้อความจาก AI กลับไปที่ LINE
        try:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
        except Exception as line_error:
            print(f"Error sending LINE message: {line_error}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)



