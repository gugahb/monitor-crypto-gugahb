import time
from src.config.settings import (
    SYMBOLS, S3_BUCKET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, 
    VARIATION_DICT, ALERT_STRATEGY, MOVING_AVERAGE_HOURS, STDDEV_THRESHOLD
)
from src.config.services.binance_service import get_price
from src.config.services.s3_service import (
    save_price_to_history, get_last_price, get_price_history, 
    get_stats, save_stats
)
from src.config.services.telegram_service import send_message
from src.config.services.statistics import (
    get_price_statistics, check_anomaly, update_records, filter_recent_history
)

def lambda_handler(event, context):
    ts = time.time()
    print(f"\n{'='*60}")
    print(f"Monitor de Criptomoedas - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    for symbol in SYMBOLS:
        print(f"\n📊 Buscando preço de {symbol}...")
        try:
            price = get_price(symbol)
            print(f"   💰 Preço atual: ${price:,.2f}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                         f"⚠️ Erro ao buscar {symbol}: {e}")
            continue

        # Busca último preço (cache rápido)
        last_data = get_last_price(S3_BUCKET, symbol)
        
        # Salva novo preço no histórico móvel
        save_price_to_history(S3_BUCKET, symbol, price, ts)
        
        # === ESTRATÉGIA 1: Variação simples (mantém compatibilidade) ===
        if symbol in VARIATION_DICT and last_data:
            variation_threshold = VARIATION_DICT[symbol]
            last_price = last_data['price']
            variation = ((price - last_price) / last_price) * 100
            
            print(f"   📊 Variação desde última: {variation:+.2f}% (limite: ±{variation_threshold}%)")
            
            if abs(variation) >= variation_threshold:
                emoji = "📈" if variation > 0 else "📉"
                direction = "subiu" if variation > 0 else "caiu"
                print(f"   {emoji} VARIAÇÃO SIMPLES detectada!")
                send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                             f"{emoji} *Variação {symbol}*\n"
                             f"Preço {direction}: `{variation:+.2f}%`\n"
                             f"De `${last_price:,.2f}` para `${price:,.2f}`")
        
        # === ESTRATÉGIA 2: Média Móvel + Desvio Padrão ===
        if ALERT_STRATEGY in ['moving_average', 'both']:
            history = get_price_history(S3_BUCKET, symbol)
            
            if len(history) >= 10:  # Mínimo de dados para análise
                recent = filter_recent_history(history, MOVING_AVERAGE_HOURS)
                
                if len(recent) >= 10:
                    stats = get_price_statistics(recent)
                    is_anomaly, z_score = check_anomaly(price, stats['mean'], stats['std_dev'], STDDEV_THRESHOLD)
                    
                    print(f"   📈 Média {MOVING_AVERAGE_HOURS}h: ${stats['mean']:,.2f} (±${stats['std_dev']:,.2f})")
                    print(f"   📊 Z-score: {z_score:.2f}σ")
                    
                    if is_anomaly:
                        direction = "acima" if z_score > 0 else "abaixo"
                        emoji = "⚠️" if z_score > 0 else "🔻"
                        print(f"   {emoji} ANOMALIA ESTATÍSTICA detectada!")
                        send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                                     f"{emoji} *Anomalia {symbol}*\n"
                                     f"Preço `${price:,.2f}` está *{abs(z_score):.1f}σ {direction}* da média\n"
                                     f"Média {MOVING_AVERAGE_HOURS}h: `${stats['mean']:,.2f}` (±`${stats['std_dev']:,.2f}`)\n"
                                     f"Faixa normal: `${stats['mean'] - 2*stats['std_dev']:,.2f}` - `${stats['mean'] + 2*stats['std_dev']:,.2f}`")
                    else:
                        print(f"   ✅ Dentro da faixa normal (< {STDDEV_THRESHOLD}σ)")
        
        # === ESTRATÉGIA 3: Topos e Fundos Históricos ===
        if ALERT_STRATEGY in ['records', 'both']:
            stats_data = get_stats(S3_BUCKET, symbol)
            
            # Guarda valores ANTES de atualizar
            previous_high = stats_data.get('all_time_high', 0)
            previous_low = stats_data.get('all_time_low', float('inf'))
            
            updated_stats, is_new_high, is_new_low = update_records(stats_data, price)
            
            if is_new_high:
                print(f"   🚀 NOVO RECORDE HISTÓRICO!")
                send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                             f"🚀 *RECORDE {symbol}*\n"
                             f"Novo topo histórico: `${price:,.2f}`\n"
                             f"Anterior: `${previous_high:,.2f}`")
            
            if is_new_low:
                print(f"   📉 NOVO FUNDO HISTÓRICO!")
                previous_low_display = "N/A" if previous_low == float('inf') else f"${previous_low:,.2f}"
                send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                             f"📉 *FUNDO {symbol}*\n"
                             f"Menor preço histórico: `${price:,.2f}`\n"
                             f"Anterior: `{previous_low_display}`")
            
            # Salva estatísticas atualizadas
            if is_new_high or is_new_low:
                save_stats(S3_BUCKET, symbol, updated_stats)

    print(f"\n{'='*60}")
    print("✅ Execução concluída com sucesso!")
    print(f"{'='*60}\n")
    return {"status": "ok"}
