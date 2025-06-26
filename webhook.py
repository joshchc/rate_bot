from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

user_targets = {}  # 暫存資料格式：{user_id: {'pair': 'USDJPY', 'target_rate': 150}}


LINE_CHANNEL_ACCESS_TOKEN = "RxKzZQcN6l+Sf9RBNvdQid+IPWWqdnP+LYPjzIZ1mh0UinTdoMlonCy8gLsU7QyEYJRpwzXXFoSfjhI2+POzJargqG3dtgcj6Pucb484jE/RvV8nMgYzUrj44I+o5evoEnLiU6pzV4PM7YqbOWlnawdB04t89/1O/w1cDnyilFU="
LINE_CHANNEL_SECRET = "7dfa3675eeb0e6119901f69a2140e699"


# LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

def reply_message(user_id, text):
    url = 'https://api.line.me/v2/bot/message/push'
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    body = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}]
    }
    requests.post(url, headers=headers, json=body)


@app.route('/webhook', methods=['POST'])
def line_webhook():
    body = request.json
    events = body.get('events', [])

    for event in events:
        if event['type'] == 'message':
            user_id = event['source']['userId']
            message = event['message']['text'].replace(" ", "").upper()

            # 解析幣別與匯率，例如 USDJPY150
            import re
            match = re.match(r"([A-Z]{6})(\d+(\.\d+)?)", message)
            if match:
                pair = match.group(1)
                target = float(match.group(2))
                user_targets[user_id] = {'pair': pair, 'target_rate': target}
                reply = f"已設定匯率提醒：{pair} 當匯率到 {target} 時通知您。"
            else:
                reply = "請輸入格式，例如 USDJPY150"

            # 回覆用戶
            reply_message(user_id, reply)

    return jsonify({"status": "ok"})

if __name__ == '__main__':

    app.run(port=5000)
