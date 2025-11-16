import json
import datetime
import boto3
import os
from pathlib import Path

ENABLE_S3 = os.getenv("ENABLE_S3", "true").lower() == "true"

if ENABLE_S3:
    s3 = boto3.client("s3")
else:
    s3 = None

LOCAL_CACHE_FILE = Path("local_data") / "last_prices.json"

def save_price(bucket, symbol, price, ts):
    """Salva log do preço no S3."""
    dt = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).replace(tzinfo=None)
    key = f"logs/{dt.year}/{dt.month:02d}/{dt.day:02d}/{symbol}-{int(ts)}.json"

    body = {
        "symbol": symbol,
        "price": price,
        "timestamp": ts,
        "datetime_utc": dt.isoformat() + "Z",
    }

    if not ENABLE_S3:
        print(f"[LOCAL MODE] Salvaria em S3: {key}")
        print(f"[LOCAL MODE] Dados: {json.dumps(body, indent=2)}")
        _save_to_local_cache(symbol, price, ts)
        return

    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps(body),
        ContentType="application/json",
    )
    _save_to_local_cache(symbol, price, ts)

def get_last_price(bucket, symbol):
    """Recupera o último preço salvo (S3 ou cache local)."""
    if not ENABLE_S3:
        return _get_from_local_cache(symbol)
    
    cached = _get_from_local_cache(symbol)
    if cached:
        return cached
    
    try:
        today = datetime.datetime.now(tz=datetime.timezone.utc)
        prefix = f"logs/{today.year}/{today.month:02d}/{today.day:02d}/{symbol}-"
        
        response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=1)
        if 'Contents' not in response or not response['Contents']:
            return None
        
        latest = sorted(response['Contents'], key=lambda x: x['LastModified'], reverse=True)[0]
        obj = s3.get_object(Bucket=bucket, Key=latest['Key'])
        data = json.loads(obj['Body'].read().decode('utf-8'))
        
        return {
            'price': data['price'],
            'timestamp': data['timestamp']
        }
    except Exception as e:
        print(f"⚠️  Erro ao buscar último preço do S3: {e}")
        return None

def _save_to_local_cache(symbol, price, ts):
    """Salva preço no cache local."""
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

def _get_from_local_cache(symbol):
    """Recupera preço do cache local."""
    if not LOCAL_CACHE_FILE.exists():
        return None
    
    try:
        cache = json.loads(LOCAL_CACHE_FILE.read_text())
        return cache.get(symbol)
    except:
        return None
