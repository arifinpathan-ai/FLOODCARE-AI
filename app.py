import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai

app = Flask(__name__)

# ดึงค่าคอนฟิกจาก Environment Variables บน Render
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ตั้งค่า LINE SDK
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ตั้งค่า Gemini API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
# เปลี่ยนมาใช้โมเดลรุ่นเสถียรตัวปัจจุบัน
model = genai.GenerativeModel('gemini-2.5-flash')

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

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text
    
    if not GEMINI_API_KEY:
        reply_text = "❌ ระบบยังไม่ได้ตั้งค่า GEMINI_API_KEY"
    else:
        try:
            # ส่งข้อความไปถาม AI
            response = model.generate_content(user_message)
            if response.parts:
                reply_text = response.text
            else:
                reply_text = "⚠️ Gemini ไม่สามารถตอบข้อความนี้ได้เนื่องจากติดตัวกรองความปลอดภัย"
        except Exception as e:
            # หากเกิดข้อผิดพลาด จะส่งสาเหตุจริงกลับมาใน LINE ทันทีเพื่อความง่ายในการแก้
            reply_text = f"❌ Gemini API Error:\n{str(e)}"

    # ส่งข้อความตอบกลับไปยัง LINE
    try:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))
    except Exception as line_error:
        print(f"Error sending LINE message: {line_error}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

