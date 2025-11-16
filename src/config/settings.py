import os

required_vars = ["S3_BUCKET", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
missing = [var for var in required_vars if not os.environ.get(var)]
if missing:
    raise EnvironmentError(f"❌ Variáveis de ambiente faltando: {', '.join(missing)}")

SYMBOLS = os.environ.get("SYMBOLS", "BTCUSDT").split(",")

S3_BUCKET = os.environ["S3_BUCKET"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

ALERTS = os.environ.get("ALERTS", "")
VARIATION_ALERTS = os.environ.get("VARIATION_ALERTS", "")

def parse_alerts(raw: str):
    if not raw:
        return {}
    parts = raw.split(",")
    result = {}
    for p in parts:
        if ':' not in p:
            continue
        symbol, value = p.split(":")
        result[symbol] = float(value)
    return result

ALERT_DICT = parse_alerts(ALERTS)
VARIATION_DICT = parse_alerts(VARIATION_ALERTS)
