import requests
from src.config.coin_mappings import get_coingecko_id

def get_sentiment_data(coin_symbol: str, previous_volume: float = None):
    """
    Busca dados sociais via CoinGecko API (Free, sem Auth).
    Substitui a análise do Twitter para evitar rate limits.
    """
    coin_id = get_coingecko_id(coin_symbol)
    
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}?localization=false&tickers=false&market_data=true&community_data=true&developer_data=false"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"⚠️ Erro CoinGecko ({response.status_code}): {response.text}")
            return _get_mock_sentiment_data(coin_symbol, reason=f"Erro API {response.status_code}")
            
        data = response.json()
        
        market_data = data.get('market_data', {})
        community_data = data.get('community_data', {})
        
        total_volume = market_data.get('total_volume', {}).get('usd', 0)
        social_proxy_mentions = int(total_volume / 1000000) 
        
        sentiment_votes_up = data.get('sentiment_votes_up_percentage')
        if sentiment_votes_up is None:
            sentiment_votes_up = 50.0 
            
        public_interest = data.get('public_interest_score', 0)
        
        twitter_followers = community_data.get('twitter_followers', 0)
        reddit_subscribers = community_data.get('reddit_subscribers', 0)
        
        if previous_volume and previous_volume > 0:
            percent_aumento = ((total_volume - previous_volume) / previous_volume) * 100
            percent_aumento = max(0, min(100, percent_aumento))
        else:
            percent_aumento = 0 
        
        return {
            "menções_30min": social_proxy_mentions, 
            "menções_5min": int(social_proxy_mentions / 6),
            "percent_aumento": percent_aumento,
            "lista_kols": ["CoinGecko Community"], 
            "sentimento_atual": sentiment_votes_up,
            "posts_virais": f"Score Interesse: {public_interest:.1f}",
            "twitter_followers": twitter_followers
        }
        
    except Exception as e:
        print(f"❌ Erro na análise CoinGecko: {e}")
        return _get_mock_sentiment_data(coin_symbol, reason=str(e))

def calculate_pump_score(sentiment_data, technical_metrics):
    """
    Calcula score de pump baseado em dados do CoinGecko + Técnica.
    """
    sentimento = sentiment_data.get("sentimento_atual", 50)
    aumento_social = sentiment_data.get("percent_aumento", 0)
    
    var_volume = technical_metrics.get("volume_change_1h", 0)
    rsi = technical_metrics.get("rsi", 50)
    if rsi == "N/A": rsi = 50
    
    sentimento_score = 0
    if sentimento > 50:
        sentimento_score = (sentimento - 50) * 2 
    rsi_score = 100 - abs(rsi - 60) * 2
    tecnico_score = (min(100, max(0, var_volume)) * 0.5 + max(0, rsi_score) * 0.5)
    
    hype_score = min(100, aumento_social * 3)
    
    score = int(sentimento_score * 0.4 + tecnico_score * 0.4 + hype_score * 0.2)
    
    if rsi > 80: score -= 20
    if sentimento < 40: score -= 30
    
    score = max(0, min(100, score))
    
    recomendacao = "COMPRA" if score >= 80 else "ESPERA" if score >= 50 else "VENDA"
    risco_alto = rsi > 80 or sentimento < 30
    
    razao = (f"Sentimento {sentimento:.0f}% (CG) | "
             f"Técnica: Vol {var_volume}% RSI {rsi}")
    
    return {
        "score_pump_15_60min": score,
        "razao_curta": razao,
        "recomendacao": recomendacao,
        "risco_alto": risco_alto
    }

def _get_mock_sentiment_data(symbol, reason="Mock"):
    return {
        "menções_30min": 100,
        "menções_5min": 15,
        "percent_aumento": 10,
        "lista_kols": ["Mock"],
        "sentimento_atual": 50,
        "posts_virais": f"Mock data ({reason})",
        "twitter_followers": 0
    }