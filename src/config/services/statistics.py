"""
Módulo de estatísticas para análise de preços de criptomoedas.
Implementa média móvel, desvio padrão e detecção de topos/fundos históricos.
"""
import statistics
from typing import List, Dict, Optional, Tuple


def calculate_moving_average(prices: List[float]) -> float:
    """Calcula média simples dos preços."""
    if not prices:
        return 0.0
    return statistics.mean(prices)


def calculate_std_deviation(prices: List[float]) -> float:
    """Calcula desvio padrão dos preços."""
    if len(prices) < 2:
        return 0.0
    return statistics.stdev(prices)


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


def check_anomaly(current_price: float, mean: float, std_dev: float, threshold: float = 2.0) -> Tuple[bool, float]:
    """
    Verifica se preço atual é uma anomalia estatística.
    
    Args:
        current_price: Preço atual
        mean: Média histórica
        std_dev: Desvio padrão histórico
        threshold: Número de desvios padrão para considerar anomalia (default: 2.0)
    
    Returns:
        (is_anomaly, z_score) - True se anomalia, z-score calculado
    """
    if std_dev == 0:
        return False, 0.0
    
    z_score = (current_price - mean) / std_dev
    is_anomaly = abs(z_score) >= threshold
    
    return is_anomaly, z_score


def update_records(stats: Dict, current_price: float) -> Tuple[Dict, bool, bool]:
    """
    Atualiza recordes históricos e verifica se há novo topo ou fundo.
    
    Args:
        stats: Dict com 'all_time_high' e 'all_time_low'
        current_price: Preço atual
    
    Returns:
        (updated_stats, is_new_high, is_new_low)
    """
    all_time_high = stats.get('all_time_high', 0.0)
    all_time_low = stats.get('all_time_low', float('inf'))
    
    is_new_high = current_price > all_time_high
    is_new_low = current_price < all_time_low and all_time_low != float('inf')
    
    if is_new_high:
        stats['all_time_high'] = current_price
    
    if is_new_low or all_time_low == float('inf'):
        stats['all_time_low'] = current_price
    
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
    
    # Pega timestamp mais recente
    latest_ts = max(h['timestamp'] for h in history)
    cutoff_ts = latest_ts - (hours * 3600)
    
    return [h for h in history if h['timestamp'] >= cutoff_ts]
