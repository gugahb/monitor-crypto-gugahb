import json
import datetime
import boto3
import os
from pathlib import Path

ENABLE_S3 = os.getenv("ENABLE_S3", "true").lower() == "true"
HISTORY_DAYS = int(os.getenv("HISTORY_DAYS", "7"))

if ENABLE_S3:
    s3 = boto3.client("s3")
else:
    s3 = None

LOCAL_CACHE_FILE = Path("/tmp/last_prices.json") if ENABLE_S3 else Path("local_data/last_prices.json")
LOCAL_HISTORY_DIR = Path("/tmp") if ENABLE_S3 else Path("local_data")

def save_price_to_history(bucket, symbol, price, volume, ts):
    """
    Salva preço E volume no histórico móvel (janela de N dias).
    
    Args:
        bucket: Nome do bucket S3
        symbol: Símbolo da moeda
        price: Preço atual
        volume: Volume atual
        ts: Timestamp
    """
    key = f"history/{symbol}.json"
    
    # Busca histórico existente
    history = get_price_history(bucket, symbol)
    
    # Adiciona novo registro COM VOLUME
    history.append({
        "price": price,
        "volume": volume,
        "timestamp": ts
    })
    
    # Filtra para manter apenas últimos N dias
    cutoff_ts = ts - (HISTORY_DAYS * 24 * 3600)
    history = [h for h in history if h['timestamp'] >= cutoff_ts]
    
    # Salva histórico atualizado
    if not ENABLE_S3:
        local_file = LOCAL_HISTORY_DIR / f"{symbol}_history.json"
        LOCAL_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        local_file.write_text(json.dumps(history, indent=2))
        print(f"💾 [LOCAL] Histórico salvo: {len(history)} registros")
    else:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(history),
            ContentType="application/json",
        )
        print(f"💾 Histórico S3 atualizado: {len(history)} registros")
    
    # Atualiza cache rápido (apenas preço para compatibilidade)
    _save_to_local_cache(symbol, price, ts)

def get_price_history(bucket, symbol):
    """Recupera histórico completo de preços (últimos N dias)."""
    if not ENABLE_S3:
        local_file = LOCAL_HISTORY_DIR / f"{symbol}_history.json"
        if local_file.exists():
            try:
                return json.loads(local_file.read_text())
            except:
                return []
        return []
    
    key = f"history/{symbol}.json"
    
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        history = json.loads(obj['Body'].read().decode('utf-8'))
        print(f"📂 Histórico recuperado: {len(history)} registros")
        return history
    except s3.exceptions.NoSuchKey:
        print(f"ℹ️  Nenhum histórico para {symbol} (primeira execução)")
        return []
    except Exception as e:
        print(f"⚠️  Erro ao buscar histórico: {e}")
        return []

def get_last_price(bucket, symbol):
    """Recupera o último preço salvo (cache rápido)."""
    return _get_from_local_cache(symbol)

def save_stats(bucket, symbol, stats):
    """Salva estatísticas de topos/fundos históricos."""
    key = f"stats/{symbol}.json"
    
    if not ENABLE_S3:
        local_file = LOCAL_HISTORY_DIR / f"{symbol}_stats.json"
        LOCAL_HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        local_file.write_text(json.dumps(stats, indent=2))
    else:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(stats),
            ContentType="application/json",
        )

def get_stats(bucket, symbol):
    """Recupera estatísticas de topos/fundos históricos."""
    if not ENABLE_S3:
        local_file = LOCAL_HISTORY_DIR / f"{symbol}_stats.json"
        if local_file.exists():
            try:
                return json.loads(local_file.read_text())
            except:
                return {'all_time_high': 0.0, 'all_time_low': float('inf')}
        return {'all_time_high': 0.0, 'all_time_low': float('inf')}
    
    key = f"stats/{symbol}.json"
    
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        return json.loads(obj['Body'].read().decode('utf-8'))
    except s3.exceptions.NoSuchKey:
        return {'all_time_high': 0.0, 'all_time_low': float('inf')}
    except Exception as e:
        print(f"⚠️  Erro ao buscar stats: {e}")
        return {'all_time_high': 0.0, 'all_time_low': float('inf')}

def _save_to_local_cache(symbol, price, ts):
    """Salva preço no cache local (/tmp na Lambda, local_data localmente)."""
    try:
        if not ENABLE_S3:
            LOCAL_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        cache = {}
        if LOCAL_CACHE_FILE.exists():
            try:
                cache = json.loads(LOCAL_CACHE_FILE.read_text())
            except:
                pass
        
        cache[symbol] = {
            'price': price,
            'timestamp': ts
        }
        
        LOCAL_CACHE_FILE.write_text(json.dumps(cache, indent=2))
    except Exception as e:
        print(f"⚠️  Erro ao salvar cache local: {e}")

def _get_from_local_cache(symbol):
    """Recupera preço do cache local."""
    if not LOCAL_CACHE_FILE.exists():
        return None
    
    try:
        cache = json.loads(LOCAL_CACHE_FILE.read_text())
        return cache.get(symbol)
    except:
        return None
