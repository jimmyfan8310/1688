import os
import re
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))

products = {
    "剝皮辣椒": 160,
    "山豬皮": 190,
    "皇帝菜": 150,
    "小魚乾": 170,
    "蘿蔔辣醬": 200,
    "蒜味辣醬": 200,
}

valid_counts = [6, 12, 18, 24, 32]

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    lines = user_text.split('\n')
    items, total_qty = {}, 0
    name = phone = address = payment = ''


    for line in lines:
        match = re.match(r"(剝皮辣椒|山豬皮|皇帝菜|小魚乾|蘿蔔辣醬|蒜味辣醬)\s*(\d+)瓶", line)
        if match:
            product = match.group(1)
            qty = int(match.group(2))
            items[product] = items.get(product, 0) + qty
            total_qty += qty
            continue
        if re.match(r"^09\d{8}$", line) or re.match(r"^0\d{1,2}-\d{6,8}$", line):  # 支援市話
            phone = line
        elif "市" in line or "縣" in line:
            address = line
        elif len(line) <= 5 and any(c.isalpha() == False for c in line):
            name = line
        elif "轉帳" in line or "貨到付款" in line:
            payment = line.strip()

    if total_qty not in valid_counts:
        reply = f"總瓶數為 {total_qty}，但需為 6, 12, 18, 24 或 32 瓶，請重新確認。"
    elif not (name and phone and address and payment):
        reply = "請確認已填寫：姓名、電話、地址、付款方式（轉帳 / 貨到付款）"
    else:
        shipping_fee = 0 if total_qty == 32 else 200
        reply = (
            f"✅ 訂單成立
"
            f"商品明細：
" +
            "\n".join([f"{k} {v}瓶" for k, v in items.items()]) + "\n" +
            f"總瓶數：{total_qty} 瓶
"
            f"收件人：{name}（{phone}）
"
            f"地址：{address}
"
            f"付款方式：{payment}
"
            f"{'免運費' if shipping_fee == 0 else '運費：200元'}"
        )

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))