"""
Módulo de estatísticas para análise de preços de criptomoedas.
Implementa média móvel, desvio padrão, detecção de topos/fundos históricos
e análise de volume para reduzir falsos positivos.
"""
import statistics
from typing import List, Dict, Optional, Tuple


def calculate_moving_average(values: List[float]) -> float:
    """Calcula média simples de uma lista de valores."""
    if not values:
        return 0.0
    return statistics.mean(values)


def calculate_std_deviation(values: List[float]) -> float:
    """Calcula desvio padrão de uma lista de valores."""
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def get_price_statistics(history: List[Dict]) -> Dict:
    """
    Calcula estatísticas completas do histórico de preços.
    
    Args:
        history: Lista de dicts com 'price' e 'timestamp'
    
    Returns:
        Dict com média, std_dev, min, max, count
    """
    if not history:
        return {
            'mean': 0.0,
            'std_dev': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0
        }
    
    prices = [h['price'] for h in history]
    
    return {
        'mean': calculate_moving_average(prices),
        'std_dev': calculate_std_deviation(prices),
        'min': min(prices),
        'max': max(prices),
        'count': len(prices)
    }


def get_volume_statistics(history: List[Dict]) -> Dict:
    """
    Calcula estatísticas completas do histórico de volumes.
    
    Args:
        history: Lista de dicts com 'volume' e 'timestamp'
    
    Returns:
        Dict com mean, std_dev, min, max, count
    """
    if not history:
        return {
            'mean': 0.0,
            'std_dev': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0
        }
    
    volumes = [h.get('volume', 0) for h in history if 'volume' in h]
    
    if not volumes:
        return {
            'mean': 0.0,
            'std_dev': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0
        }
    
    return {
        'mean': calculate_moving_average(volumes),
        'std_dev': calculate_std_deviation(volumes),
        'min': min(volumes),
        'max': max(volumes),
        'count': len(volumes)
    }


def check_anomaly(current_value: float, mean: float, std_dev: float, threshold: float = 2.0) -> Tuple[bool, float]:
    """
    Verifica se valor atual é uma anomalia estatística.
    
    Args:
        current_value: Valor atual (preço ou volume)
        mean: Média histórica
        std_dev: Desvio padrão histórico
        threshold: Número de desvios padrão para considerar anomalia (default: 2.0)
    
    Returns:
        (is_anomaly, z_score) - True se anomalia, z-score calculado
    """
    if std_dev == 0:
        return False, 0.0
    
    z_score = (current_value - mean) / std_dev
    is_anomaly = abs(z_score) >= threshold
    
    return is_anomaly, z_score


def check_volume_anomaly(current_volume: float, volume_mean: float, volume_std: float, threshold: float = 1.5) -> Tuple[bool, float]:
    """
    Verifica se volume atual indica movimento significativo.
    
    Args:
        current_volume: Volume atual
        volume_mean: Média histórica de volume
        volume_std: Desvio padrão do volume
        threshold: Threshold mais baixo que preço (default: 1.5σ)
    
    Returns:
        (is_volume_spike, volume_z_score)
    """
    return check_anomaly(current_volume, volume_mean, volume_std, threshold)


def evaluate_combined_anomaly(
    price_z: float,
    volume_z: float,
    current_price: float,
    current_volume: float,
    mean_price: float,
    mean_volume: float,
    std_price: float,
    std_volume: float,
    alert_state: Dict,
    min_volume_z: float = 1.0,
    extreme_threshold: float = 3.0,
    cooldown_minutes: int = 30
) -> Tuple[bool, str, Dict]:
    """
    Avalia anomalia combinada de preço + volume para reduzir falsos positivos.
    
    REGRAS:
    1. Anomalia de preço (|price_z| >= 2σ) + volume confirmado (volume_z >= min_volume_z) → ALERTA
    2. Preço extremo (|price_z| >= 3σ) → ALERTA mesmo sem volume
    3. Volume spike (volume_z >= 2σ) sem preço → ALERTA de pré-movimento
    4. Cooldown: não alertar novamente dentro de N minutos
    
    Args:
        price_z: Z-score do preço
        volume_z: Z-score do volume
        current_price: Preço atual
        current_volume: Volume atual
        mean_price: Média de preço
        mean_volume: Média de volume
        std_price: Desvio padrão do preço
        std_volume: Desvio padrão do volume
        alert_state: Estado anterior {last_alert_ts, last_price_z}
        min_volume_z: Mínimo z-score de volume para confirmar (default: 1.0)
        extreme_threshold: Threshold para eventos extremos (default: 3.0σ)
        cooldown_minutes: Minutos de cooldown entre alertas (default: 30)
    
    Returns:
        (should_alert, message, new_state)
    """
    import time
    
    should_alert = False
    alert_message = ""
    current_ts = time.time()
    
    last_alert_ts = alert_state.get('last_alert_ts', 0)
    time_since_last = (current_ts - last_alert_ts) / 60 
    
    if time_since_last < cooldown_minutes:
        return False, "", alert_state
    
    if abs(price_z) >= 2.0 and volume_z >= min_volume_z:
        direction = "alta" if price_z > 0 else "baixa"
        emoji = "📈" if price_z > 0 else "📉"
        
        alert_message = (
            f"{emoji} *ANOMALIA CONFIRMADA*\n"
            f"Preço: `${current_price:,.2f}` ({price_z:+.1f}σ)\n"
            f"Volume: `${current_volume:,.0f}` ({volume_z:+.1f}σ)\n"
            f"Movimento de {direction} com volume elevado\n"
            f"Média preço: `${mean_price:,.2f}` (±`${std_price:,.2f}`)"
        )
        should_alert = True
    
    elif abs(price_z) >= extreme_threshold:
        direction = "ALTA EXTREMA" if price_z > 0 else "QUEDA EXTREMA"
        emoji = "🚀" if price_z > 0 else "💥"
        
        alert_message = (
            f"{emoji} *EVENTO EXTREMO*\n"
            f"Preço: `${current_price:,.2f}` ({price_z:+.1f}σ)\n"
            f"{direction} detectada!\n"
            f"Média: `${mean_price:,.2f}` (±`${std_price:,.2f}`)\n"
            f"Volume: `${current_volume:,.0f}` ({volume_z:+.1f}σ)"
        )
        should_alert = True
    
    elif volume_z >= 2.0 and abs(price_z) < 2.0:
        alert_message = (
            f"⚡ *PRÉ-MOVIMENTO DETECTADO*\n"
            f"Volume spike: `${current_volume:,.0f}` ({volume_z:+.1f}σ)\n"
            f"Preço ainda estável: `${current_price:,.2f}` ({price_z:+.1f}σ)\n"
            f"Possível reversão ou movimento iminente"
        )
        should_alert = True
    
    new_state = alert_state.copy()
    if should_alert:
        new_state['last_alert_ts'] = current_ts
        new_state['last_price_z'] = price_z
        new_state['last_volume_z'] = volume_z
    
    return should_alert, alert_message, new_state


def update_records(stats: Dict, current_price: float, current_timestamp: float = None) -> Tuple[Dict, bool, bool]:
    """
    Atualiza recordes históricos e verifica se há novo topo ou fundo.
    
    Args:
        stats: Dict com 'all_time_high', 'all_time_low', 'last_ath_timestamp', 'last_atl_timestamp'
        current_price: Preço atual
        current_timestamp: Timestamp atual (opcional, usa time.time() se None)
    
    Returns:
        (updated_stats, is_new_high, is_new_low)
    """
    import time
    
    if current_timestamp is None:
        current_timestamp = time.time()
    
    all_time_high = stats.get('all_time_high', 0.0)
    all_time_low = stats.get('all_time_low', float('inf'))
    
    is_new_high = current_price > all_time_high
    is_new_low = current_price < all_time_low and all_time_low != float('inf')
    
    if is_new_high:
        stats['all_time_high'] = current_price
        stats['last_ath_timestamp'] = current_timestamp
    
    if is_new_low or all_time_low == float('inf'):
        stats['all_time_low'] = current_price
        stats['last_atl_timestamp'] = current_timestamp
    
    return stats, is_new_high, is_new_low


def filter_recent_history(history: List[Dict], hours: int) -> List[Dict]:
    """
    Filtra histórico para manter apenas últimas N horas.
    
    Args:
        history: Lista completa de registros
        hours: Número de horas a manter
    
    Returns:
        Lista filtrada
    """
    if not history:
        return []
    
    latest_ts = max(h['timestamp'] for h in history)
    cutoff_ts = latest_ts - (hours * 3600)
    
    return [h for h in history if h['timestamp'] >= cutoff_ts]


def calculate_trend_score(history: List[Dict], minutes: int = 60) -> Dict:
    """
    Calcula score de tendência baseado em movimentos positivos/negativos.
    
    Args:
        history: Lista completa de registros
        minutes: Janela de tempo em minutos (default: 60 = última hora)
    
    Returns:
        Dict com: {
            'positive_count': int,
            'negative_count': int,
            'neutral_count': int,
            'total_count': int,
            'positive_percentage': float,
            'trend_direction': str  # 'bullish', 'bearish', 'neutral'
        }
    """
    if not history or len(history) < 2:
        return {
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'total_count': 0,
            'positive_percentage': 0.0,
            'trend_direction': 'neutral'
        }
    
    recent = filter_recent_history(history, minutes / 60)
    
    if len(recent) < 2:
        return {
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'total_count': 0,
            'positive_percentage': 0.0,
            'trend_direction': 'neutral'
        }
    
    sorted_history = sorted(recent, key=lambda x: x['timestamp'])
    
    positive = 0
    negative = 0
    neutral = 0
    
    for i in range(1, len(sorted_history)):
        prev_price = sorted_history[i-1]['price']
        curr_price = sorted_history[i]['price']
        
        if curr_price > prev_price:
            positive += 1
        elif curr_price < prev_price:
            negative += 1
        else:
            neutral += 1
    
    total = positive + negative + neutral
    positive_pct = (positive / total * 100) if total > 0 else 0.0
    
    if positive_pct >= 60:
        direction = 'bullish'
    elif positive_pct <= 40:
        direction = 'bearish'
    else:
        direction = 'neutral'
    
    return {
        'positive_count': positive,
        'negative_count': negative,
        'neutral_count': neutral,
        'total_count': total,
        'positive_percentage': positive_pct,
        'trend_direction': direction
    }


def check_record_recency(stats: Dict, current_timestamp: float, window_hours: int = 2) -> Dict:
    """
    Verifica se ATH ou ATL foram atingidos recentemente.
    
    Args:
        stats: Dict com 'last_ath_timestamp' e 'last_atl_timestamp'
        current_timestamp: Timestamp atual
        window_hours: Janela de tempo em horas (default: 2h)
    
    Returns:
        Dict com: {
            'ath_recent': bool,
            'atl_recent': bool,
            'ath_minutes_ago': float,
            'atl_minutes_ago': float
        }
    """
    window_seconds = window_hours * 3600
    
    last_ath_ts = stats.get('last_ath_timestamp', 0)
    last_atl_ts = stats.get('last_atl_timestamp', 0)
    
    ath_recent = (current_timestamp - last_ath_ts) <= window_seconds if last_ath_ts > 0 else False
    atl_recent = (current_timestamp - last_atl_ts) <= window_seconds if last_atl_ts > 0 else False
    
    ath_minutes = (current_timestamp - last_ath_ts) / 60 if last_ath_ts > 0 else float('inf')
    atl_minutes = (current_timestamp - last_atl_ts) / 60 if last_atl_ts > 0 else float('inf')
    
    return {
        'ath_recent': ath_recent,
        'atl_recent': atl_recent,
        'ath_minutes_ago': ath_minutes,
        'atl_minutes_ago': atl_minutes
    }


def detect_higher_lows(history: List[Dict], minutes: int = 60, min_points: int = 3) -> Dict:
    """
    Detecta padrão de higher lows (fundos crescentes) ou lower highs (topos decrescentes).
    
    Args:
        history: Lista completa de registros
        minutes: Janela de tempo (default: 60 min)
        min_points: Mínimo de pontos para análise (default: 3)
    
    Returns:
        Dict com: {
            'has_higher_lows': bool,
            'has_lower_highs': bool,
            'lows': List[float],
            'highs': List[float],
            'pattern': str  # 'bullish_reversal', 'bearish_continuation', 'neutral'
        }
    """
    if not history or len(history) < min_points * 2:
        return {
            'has_higher_lows': False,
            'has_lower_highs': False,
            'lows': [],
            'highs': [],
            'pattern': 'neutral'
        }
    
    recent = filter_recent_history(history, minutes / 60)
    
    if len(recent) < min_points * 2:
        return {
            'has_higher_lows': False,
            'has_lower_highs': False,
            'lows': [],
            'highs': [],
            'pattern': 'neutral'
        }
    
    sorted_history = sorted(recent, key=lambda x: x['timestamp'])
    prices = [h['price'] for h in sorted_history]
    
    chunk_size = max(3, len(prices) // min_points)
    lows = []
    highs = []
    
    for i in range(0, len(prices), chunk_size):
        chunk = prices[i:i+chunk_size]
        if chunk:
            lows.append(min(chunk))
            highs.append(max(chunk))
    
    has_higher_lows = len(lows) >= min_points and all(lows[i] < lows[i+1] for i in range(len(lows)-1))
    has_lower_highs = len(highs) >= min_points and all(highs[i] > highs[i+1] for i in range(len(highs)-1))
    
    if has_higher_lows and not has_lower_highs:
        pattern = 'bullish_reversal'
    elif has_lower_highs and not has_higher_lows:
        pattern = 'bearish_continuation'
    else:
        pattern = 'neutral'
    
    return {
        'has_higher_lows': has_higher_lows,
        'has_lower_highs': has_lower_highs,
        'lows': lows[-3:] if lows else [], 
        'highs': highs[-3:] if highs else [], 
        'pattern': pattern
    }


def calculate_momentum(history: List[Dict], minutes: int = 60) -> Dict:
    """
    Calcula momentum (taxa de mudança de preço).
    
    Args:
        history: Lista completa de registros
        minutes: Janela de tempo (default: 60 min = 1 hora)
    
    Returns:
        Dict com: {
            'rate_of_change': float,  # Percentual de mudança
            'direction': str,  # 'positive', 'negative', 'neutral'
            'strength': str,  # 'strong', 'moderate', 'weak'
            'price_start': float,
            'price_end': float
        }
    """
    if not history or len(history) < 2:
        return {
            'rate_of_change': 0.0,
            'direction': 'neutral',
            'strength': 'weak',
            'price_start': 0.0,
            'price_end': 0.0
        }
    
    recent = filter_recent_history(history, minutes / 60)
    
    if len(recent) < 2:
        return {
            'rate_of_change': 0.0,
            'direction': 'neutral',
            'strength': 'weak',
            'price_start': 0.0,
            'price_end': 0.0
        }
    
    sorted_history = sorted(recent, key=lambda x: x['timestamp'])
    
    price_start = sorted_history[0]['price']
    price_end = sorted_history[-1]['price']
    
    rate = ((price_end - price_start) / price_start * 100) if price_start > 0 else 0.0
    
    if rate > 1:
        direction = 'positive'
        strength = 'strong' if rate > 3 else 'moderate'
    elif rate < -1:
        direction = 'negative'
        strength = 'strong' if rate < -3 else 'moderate'
    else:
        direction = 'neutral'
        strength = 'weak'
    
    return {
        'rate_of_change': rate,
        'direction': direction,
        'strength': strength,
        'price_start': price_start,
        'price_end': price_end
    }


def calculate_rsi(prices, period=14):
    """
    Calcula o RSI (Relative Strength Index) para uma lista de preços.
    
    Args:
        prices (list): Lista de preços (float), ordenados do mais antigo para o mais recente.
        period (int): Período para cálculo (padrão 14).
        
    Returns:
        float: Valor do RSI (0-100) ou None se dados insuficientes.
    """
    if len(prices) < period + 1:
        return None
        
    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0
    
    if avg_loss == 0:
        return 100.0
        
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def calculate_vwap(history, period_hours=1):
    """
    Calcula o VWAP (Volume Weighted Average Price).
    
    Args:
        history (list): Lista de dicts {price, volume, timestamp}.
        period_hours (int): Janela de tempo em horas.
        
    Returns:
        float: Valor do VWAP ou None.
    """
    if not history:
        return None
        
    now = history[-1]['timestamp']
    start_time = now - (period_hours * 3600)
    
    relevant_data = [h for h in history if h['timestamp'] >= start_time]
    
    if not relevant_data:
        return None
        
    total_pv = sum(h['price'] * h['volume'] for h in relevant_data)
    total_volume = sum(h['volume'] for h in relevant_data)
    
    if total_volume == 0:
        return None
        
    return total_pv / total_volume


def detect_sideways_movement(history: List[Dict], minutes: int = 60, threshold_pct: float = 1.0) -> Dict:
    """
    Detecta movimento lateral (baixa volatilidade, preço estável).
    
    Args:
        history: Lista completa de registros
        minutes: Janela de tempo para análise (default: 60 min)
        threshold_pct: % máxima de oscilação para considerar lateral (default: 1.0%)
    
    Returns:
        Dict com: {
            'is_sideways': bool,
            'volatility_pct': float,  # Oscilação em %
            'price_min': float,
            'price_max': float,
            'price_range': float,
            'duration_minutes': float,  # Quanto tempo está lateral
            'sample_count': int
        }
    """
    if not history or len(history) < 2:
        return {
            'is_sideways': False,
            'volatility_pct': 0.0,
            'price_min': 0.0,
            'price_max': 0.0,
            'price_range': 0.0,
            'duration_minutes': 0.0,
            'sample_count': 0
        }
    
    recent = filter_recent_history(history, minutes / 60)
    
    if len(recent) < 6: 
        return {
            'is_sideways': False,
            'volatility_pct': 0.0,
            'price_min': 0.0,
            'price_max': 0.0,
            'price_range': 0.0,
            'duration_minutes': 0.0,
            'sample_count': len(recent)
        }
    
    sorted_history = sorted(recent, key=lambda x: x['timestamp'])
    prices = [h['price'] for h in sorted_history]
    
    price_min = min(prices)
    price_max = max(prices)
    price_avg = sum(prices) / len(prices)
    price_range = price_max - price_min
    
    volatility_pct = (price_range / price_avg * 100) if price_avg > 0 else 0.0
    
    duration_minutes = (sorted_history[-1]['timestamp'] - sorted_history[0]['timestamp']) / 60
    
    is_sideways = volatility_pct < threshold_pct
    
    return {
        'is_sideways': is_sideways,
        'volatility_pct': volatility_pct,
        'price_min': price_min,
        'price_max': price_max,
        'price_range': price_range,
        'duration_minutes': duration_minutes,
        'sample_count': len(prices)
    }


def detect_breakout(
    current_price: float,
    sideways_data: Dict,
    volume_z: float,
    min_breakout_pct: float = 1.0,
    min_volume_z: float = 1.0
) -> Dict:
    """
    Detecta rompimento de movimento lateral (breakout).
    
    Args:
        current_price: Preço atual
        sideways_data: Dict retornado por detect_sideways_movement
        volume_z: Z-score do volume atual
        min_breakout_pct: % mínima para considerar rompimento (default: 1.0%)
        min_volume_z: Z-score mínimo de volume para confirmar (default: 1.0σ)
    
    Returns:
        Dict com: {
            'is_breakout': bool,
            'direction': str,  # 'up', 'down', 'none'
            'breakout_pct': float,
            'volume_confirmed': bool,
            'breakout_type': str  # 'confirmed', 'weak', 'none'
        }
    """
    if not sideways_data.get('is_sideways', False):
        return {
            'is_breakout': False,
            'direction': 'none',
            'breakout_pct': 0.0,
            'volume_confirmed': False,
            'breakout_type': 'none'
        }
    
    price_max = sideways_data['price_max']
    price_min = sideways_data['price_min']
    price_avg = (price_max + price_min) / 2
    
    if current_price > price_max:
        breakout_pct = ((current_price - price_max) / price_avg * 100)
        direction = 'up'
    elif current_price < price_min:
        breakout_pct = ((price_min - current_price) / price_avg * 100)
        direction = 'down'
    else:
        return {
            'is_breakout': False,
            'direction': 'none',
            'breakout_pct': 0.0,
            'volume_confirmed': False,
            'breakout_type': 'none'
        }
    
    is_breakout = breakout_pct >= min_breakout_pct
    
    volume_confirmed = volume_z >= min_volume_z
    
    if is_breakout and volume_confirmed:
        breakout_type = 'confirmed'
    elif is_breakout and not volume_confirmed:
        breakout_type = 'weak'
    else:
        breakout_type = 'none'
    
    return {
        'is_breakout': is_breakout,
        'direction': direction,
        'breakout_pct': breakout_pct,
        'volume_confirmed': volume_confirmed,
        'breakout_type': breakout_type
    }
