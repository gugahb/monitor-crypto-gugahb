import json
import urllib.request

def get_price(symbol):
    """Busca preço via Binance API pública."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    with urllib.request.urlopen(url, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    return float(data["price"])
