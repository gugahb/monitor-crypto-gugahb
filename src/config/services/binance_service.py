import json
import urllib.request

SYMBOL_MAP = {
    'BTCUSDT': 'bitcoin',
    'ETHUSDT': 'ethereum',
    'SOLUSDT': 'solana'
}

def get_price_and_volume(symbol):
    """
    Busca preço E volume via CoinGecko API (sem bloqueios geográficos).
    
    Returns:
        dict: {'price': float, 'volume': float}
    """
    coin_id = SYMBOL_MAP.get(symbol)
    if not coin_id:
        raise ValueError(f"Símbolo {symbol} não suportado")
    
    # Usa endpoint /coins/markets para obter preço + volume
    url = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; CryptoMonitor/1.0)'
    }
    
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        data = json.loads(response.read().decode("utf-8"))
    
    if not data or len(data) == 0:
        raise ValueError(f"Nenhum dado retornado para {coin_id}")
    
    market_data = data[0]
    
    return {
        'price': float(market_data["current_price"]),
        'volume': float(market_data["total_volume"])
    }

def get_price(symbol):
    """
    Mantém compatibilidade com código legado.
    Retorna apenas o preço (sem volume).
    """
    data = get_price_and_volume(symbol)
    return data['price']
