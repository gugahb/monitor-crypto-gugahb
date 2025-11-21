"""
Módulo para gerenciar estado de alertas e evitar notificações repetidas.
Implementa cooldown entre alertas e tracking de últimas anomalias.
"""
import json
import boto3
import os
from pathlib import Path
from typing import Dict

ENABLE_S3 = os.getenv("ENABLE_S3", "true").lower() == "true"

if ENABLE_S3:
    s3 = boto3.client("s3")
else:
    s3 = None

LOCAL_STATE_DIR = Path("/tmp") if ENABLE_S3 else Path("local_data")


def get_alert_state(bucket: str, symbol: str) -> Dict:
    """
    Recupera estado de alertas para um símbolo.
    
    Returns:
        Dict com last_alert_ts, last_price_z, last_volume_z, 
        sideways_start_ts, last_sideways_alert_ts, was_sideways
    """
    default_state = {
        'last_alert_ts': 0,
        'last_price_z': 0.0,
        'last_volume_z': 0.0,
        'sideways_start_ts': 0,
        'last_sideways_alert_ts': 0,
        'was_sideways': False
    }
    
    if not ENABLE_S3:
        local_file = LOCAL_STATE_DIR / f"{symbol}_alert_state.json"
        if local_file.exists():
            try:
                state = json.loads(local_file.read_text())
                # Adiciona campos novos se não existirem (migração)
                for key in default_state:
                    if key not in state:
                        state[key] = default_state[key]
                return state
            except:
                return default_state
        return default_state
    
    key = f"alert_state/{symbol}.json"
    
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        state = json.loads(obj['Body'].read().decode('utf-8'))
        # Adiciona campos novos se não existirem (migração)
        for key in default_state:
            if key not in state:
                state[key] = default_state[key]
        return state
    except s3.exceptions.NoSuchKey:
        return default_state
    except Exception as e:
        print(f"⚠️  Erro ao buscar estado de alerta: {e}")
        return default_state


def save_alert_state(bucket: str, symbol: str, state: Dict):
    """
    Salva estado de alertas para um símbolo.
    
    Args:
        bucket: Nome do bucket S3
        symbol: Símbolo da moeda
        state: Dict com last_alert_ts, last_price_z, last_volume_z
    """
    if not ENABLE_S3:
        local_file = LOCAL_STATE_DIR / f"{symbol}_alert_state.json"
        LOCAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
        local_file.write_text(json.dumps(state, indent=2))
        return
    
    key = f"alert_state/{symbol}.json"
    
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(state),
            ContentType="application/json",
        )
    except Exception as e:
        print(f"⚠️  Erro ao salvar estado de alerta: {e}")
