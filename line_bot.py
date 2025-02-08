from fastapi import FastAPI, Request, HTTPException
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from get_rate import Rate
import os


LINE_CHANNEL_ACCESS_TOKEN = "RxKzZQcN6l+Sf9RBNvdQid+IPWWqdnP+LYPjzIZ1mh0UinTdoMlonCy8gLsU7QyEYJRpwzXXFoSfjhI2+POzJargqG3dtgcj6Pucb484jE/RvV8nMgYzUrj44I+o5evoEnLiU6pzV4PM7YqbOWlnawdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "7dfa3675eeb0e6119901f69a2140e699"

app = FastAPI()
rate = Rate()

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.post("/callback")
async def callback(request: Request):
    """ 接收 LINE Webhook 並處理訊息 """
    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        raise HTTPException(status_code=400, details = "X-Line-Signature header is missing")
    body = await request.body()
    
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        return HTTPException(status_code=400, detail="Invalid signature")


    return {"message": "OK"}


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """回覆使用者傳送的訊息"""
    reply_text = rate.main(f"{event.message.text}")
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))