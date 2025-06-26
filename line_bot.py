from fastapi import FastAPI, Request, HTTPException
from fastapi import FastAPI, Request, HTTPException
from contextlib import asynccontextmanager
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage,  ButtonsTemplate, PostbackAction, URIAction, MessageAction, PostbackEvent
from linebot.exceptions import InvalidSignatureError
import os
import re
import requests
import asyncio
from sqlalchemy import create_engine, Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from get_rate import Rate


LINE_CHANNEL_ACCESS_TOKEN = "RxKzZQcN6l+Sf9RBNvdQid+IPWWqdnP+LYPjzIZ1mh0UinTdoMlonCy8gLsU7QyEYJRpwzXXFoSfjhI2+POzJargqG3dtgcj6Pucb484jE/RvV8nMgYzUrj44I+o5evoEnLiU6pzV4PM7YqbOWlnawdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "7dfa3675eeb0e6119901f69a2140e699"

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(check_rates_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)


rate = Rate()

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://finance:7fJE57GwKfqEeZA9A5AYsihD@192.168.1.40:3306/linebot")
engine = create_engine(DATABASE_URL, echo=False)
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 匯率提醒模型
class RateTarget(Base):
    __tablename__ = 'rate_targets'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), index=True)
    pair = Column(String(10))
    target = Column(Float)

Base.metadata.create_all(bind=engine)

def get_all_targets_text(db, user_id: str) -> str:
    targets = db.query(RateTarget).filter(RateTarget.user_id == user_id).all()
    if not targets:
        return "目前沒有任何匯率提醒設定"
    return "📋 目前設定提醒：\n" + "\n".join([f"• {t.pair} >= {t.target}" for t in targets])

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    text: str = event.message.text.strip()
    db = SessionLocal()

    # 匯率設定格式：USDJPY150
    match = re.match(r"([A-Za-z]{6})(\d+(\.\d+)?)", text.replace(" ", ""))
    if match:
        pair = match.group(1).upper()
        target_rate = float(match.group(2))
        db.add(RateTarget(user_id=user_id, pair=pair, target=target_rate))
        db.commit()
        reply_text = f"✅ 已設定匯率提醒：當 {pair} >= {target_rate} 時通知您"

    elif text.upper() == "HI":
        buttons_template = ButtonsTemplate(
            title='查詢匯率或操作說明',
            text='請選擇以下操作',
            actions=[
                PostbackAction(label='查詢目前匯率設定', data='action=query_records'),
                MessageAction(label='設定匯率', text='Help Setting'),
                MessageAction(label='取消設定', text='Help Cancel'),
                MessageAction(label='如何查詢匯率', text='Help Search')
            ]
        )
        line_bot_api.reply_message(
            event.reply_token,
            TemplateSendMessage(alt_text='功能選單', template=buttons_template)
        )
        db.close()
        return

    # 取消設定：CANCEL USDJPY150 或 CANCELALL USDJPY
    elif text.lower().startswith("cancel"):
        content = text.lower().replace("cancel", "").strip().replace(" ", "")
        if content.startswith("all"):
            currency = content.replace("all", "").upper()
            deleted = db.query(RateTarget).filter(RateTarget.user_id == user_id, RateTarget.pair == currency).delete()
            db.commit()
            reply_text = f"✅ 已取消所有 {currency} 提醒" if deleted else f"❌ 找不到 {currency} 的提醒"
        else:
            match = re.match(r"([A-Z]{6})(\d+(\.\d+)?)", content.upper())
            if match:
                currency = match.group(1)
                target_rate = float(match.group(2))
                deleted = db.query(RateTarget).filter(
                    RateTarget.user_id == user_id,
                    RateTarget.pair == currency,
                    RateTarget.target == target_rate
                ).delete()
                db.commit()
                reply_text = f"✅ 已取消 {currency} >= {target_rate} 的提醒" if deleted else f"❌ 找不到 {currency} >= {target_rate} 的設定"
            else:
                reply_text = "請輸入正確格式(可忽略大小寫)，例如 Cancel USDJPY 150 或 Cancel All usdjpy"

    elif len(text) == 3:
        reply_text = Rate().main(curr = text)
    
    elif len(text) == 6:
        reply_text = Rate().currency_conversion(text = text)

    elif text.lower() == "help setting":
        reply_text = "請輸入幣別及匯率(可忽略大小寫)\n舉例:\n  USDJPY 150\n  USD JPY 150"

    elif text.lower() == "help cancel":
        reply_text = "取消某個設定(可忽略大小寫)\n舉例:\n  Cancel USDJPY 150\n  Cancel USDJPY 150\n\n取消全部設定(可忽略大小寫)\n舉例:\n  Cancel All USDJPY"
    
    elif text.lower() == "help search":
        reply_text = "方法1:\n輸入單一幣別與USD換算(可忽略大小寫)\n舉例:\n  輸入EUR\n回覆:\n  USD -> EUR: 0.9\n  EUR -> USD: 1.1\n\n方法2:\n輸入兩個幣別進行換算(可忽略大小寫)\n舉例:\n  輸入EURJPY\n回覆:\n  EUR -> JPY: 160\n  JPY -> EUR: 0.006"
    
    else:
        reply_text = "請輸入 Hi 查看操作選單"

    db.close()
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

@handler.add(PostbackEvent)
def handle_postback(event):
    db = SessionLocal()
    user_id = event.source.user_id
    data = event.postback.data

    if data == 'action=query_records':
        reply_text = get_all_targets_text(db, user_id)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )

    db.close()

@app.post("/callback")
async def callback(request: Request):
    signature = request.headers.get("X-Line-Signature")
    if signature is None:
        raise HTTPException(status_code=400, detail="X-Line-Signature header is missing")
    body = await request.body()
    try:
        handler.handle(body.decode("utf-8"), signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    return {"message": "OK"}


async def check_rates_loop():
    while True:
        db = SessionLocal()
        try:
            all_targets = db.query(RateTarget).all()
            for target in all_targets:
                try:
                    rate = Rate().compare_currency(target.pair)
                    if rate and rate >= target.target:
                        line_bot_api.push_message(
                            target.user_id,
                            TextSendMessage(text=f"📢 {target.pair} 匯率已達 {rate}（目標：{target.target}）")
                        )
                        db.delete(target)
                        db.commit()
                except Exception as e:
                    print(e)
        finally:
            db.close()

        await asyncio.sleep(60)  # 每分鐘檢查一次

