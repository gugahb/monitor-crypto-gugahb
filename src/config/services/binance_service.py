import json
import urllib.request

SYMBOL_MAP = {
    'BTCUSDT': 'bitcoin',
    'ETHUSDT': 'ethereum',
    'SOLUSDT': 'solana'
}

def get_price(symbol):
    """Busca preço via CoinGecko API (sem bloqueios geográficos)."""
    coin_id = SYMBOL_MAP.get(symbol)
    if not coin_id:
        raise ValueError(f"Símbolo {symbol} não suportado")
    
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CryptoMonitor/1.0)'
    }
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    
    return float(data[coin_id]["usd"])
