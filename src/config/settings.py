import os

required_vars = ["S3_BUCKET", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
missing = [var for var in required_vars if not os.environ.get(var)]
if missing:
    raise EnvironmentError(f"❌ Variáveis de ambiente faltando: {', '.join(missing)}")

SYMBOLS = os.environ.get("SYMBOLS", "BTCUSDT").split(",")

S3_BUCKET = os.environ["S3_BUCKET"]

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

# Configurações de alertas legados (variação percentual simples)
ALERTS = os.environ.get("ALERTS", "")
VARIATION_ALERTS = os.environ.get("VARIATION_ALERTS", "")

# Configurações estatísticas (preço)
ALERT_STRATEGY = os.environ.get("ALERT_STRATEGY", "both")  # moving_average, records, both
HISTORY_DAYS = int(os.environ.get("HISTORY_DAYS", "7"))
MOVING_AVERAGE_HOURS = int(os.environ.get("MOVING_AVERAGE_HOURS", "24"))
STDDEV_THRESHOLD = float(os.environ.get("STDDEV_THRESHOLD", "2.0"))

# Configurações de volume (novas)
MIN_VOLUME_Z = float(os.environ.get("MIN_VOLUME_Z", "1.0"))  # Mínimo z-score de volume para confirmar anomalia
EXTREME_THRESHOLD = float(os.environ.get("EXTREME_THRESHOLD", "3.0"))  # Threshold para eventos extremos
ALERT_COOLDOWN_MINUTES = int(os.environ.get("ALERT_COOLDOWN_MINUTES", "30"))  # Cooldown entre alertas

# Configurações de lateralização (sideways movement)
SIDEWAYS_THRESHOLD = float(os.environ.get("SIDEWAYS_THRESHOLD", "1.0"))  # % máxima de oscilação para considerar lateral
SIDEWAYS_MIN_DURATION = int(os.environ.get("SIDEWAYS_MIN_DURATION", "30"))  # Minutos mínimos para alertar lateral
SIDEWAYS_ALERT_INTERVAL = int(os.environ.get("SIDEWAYS_ALERT_INTERVAL", "30"))  # Intervalo entre alertas de lateral (min)
BREAKOUT_MIN_PCT = float(os.environ.get("BREAKOUT_MIN_PCT", "1.0"))  # % mínima para considerar rompimento

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
