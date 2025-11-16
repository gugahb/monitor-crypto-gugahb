import urllib.parse
import urllib.request
import os

def send_message(bot_token, chat_id, text):
    if not bot_token or os.getenv("LOCAL_MODE", "false").lower() == "true":
        print(f"[TELEGRAM] Para: {chat_id}")
        print(f"[TELEGRAM] Mensagem: {text}")
        return
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(url, data=body)
    with urllib.request.urlopen(req, timeout=10):
        pass
