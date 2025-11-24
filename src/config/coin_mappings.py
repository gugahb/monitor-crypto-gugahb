"""
Mapeamento centralizado de símbolos de criptomoedas para IDs do CoinGecko.
"""

COINGECKO_ID_MAP = {
    'BTC': 'bitcoin',
    'BTCUSDT': 'bitcoin',
    'ETH': 'ethereum',
    'ETHUSDT': 'ethereum',
    'SOL': 'solana',
    'SOLUSDT': 'solana',
    'DOGE': 'dogecoin',
    'BNB': 'binancecoin',
    'XRP': 'ripple',
    'ADA': 'cardano'
}

def get_coingecko_id(symbol: str) -> str:
    """
    Retorna o ID do CoinGecko para um símbolo.
    
    Args:
        symbol: Símbolo da moeda (ex: 'BTC', 'BTCUSDT', 'SOL')
        
    Returns:
        ID do CoinGecko (ex: 'bitcoin', 'solana')
    """
    symbol_clean = symbol.upper().replace('USDT', '')
    return COINGECKO_ID_MAP.get(symbol_clean, COINGECKO_ID_MAP.get(symbol.upper(), 'bitcoin'))
