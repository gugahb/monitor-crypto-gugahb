import time
from src.config.settings import (
    SYMBOLS, S3_BUCKET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, 
    VARIATION_DICT, ALERT_STRATEGY, MOVING_AVERAGE_HOURS, STDDEV_THRESHOLD,
    MIN_VOLUME_Z, ALERT_COOLDOWN_MINUTES, EXTREME_THRESHOLD,
    SIDEWAYS_THRESHOLD, SIDEWAYS_MIN_DURATION, SIDEWAYS_ALERT_INTERVAL, BREAKOUT_MIN_PCT
)
from src.config.services.binance_service import get_price_and_volume
from src.config.services.s3_service import (
    save_price_to_history, get_last_price, get_price_history, 
    get_stats, save_stats
)
from src.config.services.telegram_service import send_message
from src.config.services.statistics import (
    get_price_statistics, get_volume_statistics, check_anomaly, 
    evaluate_combined_anomaly, update_records, filter_recent_history,
    calculate_trend_score, check_record_recency, detect_higher_lows, calculate_momentum,
    detect_sideways_movement, detect_breakout,
    calculate_rsi, calculate_vwap
)
from src.config.services.alert_state import get_alert_state, save_alert_state
from src.config.services.sentiment_service import get_sentiment_data, calculate_pump_score
from src.config.coin_mappings import get_coingecko_id
import urllib.request
import json




def lambda_handler(event, context):
    ts = time.time()
    print(f"\n{'='*60}")
    print(f"Monitor de Criptomoedas - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    for symbol in SYMBOLS:
        print(f"\n📊 Buscando preço de {symbol}...")
        try:
            data = get_price_and_volume(symbol)
            price = data['price']
            volume = data['volume']
            print(f"   💰 Preço atual: ${price:,.2f}")
            print(f"   📊 Volume 24h: ${volume:,.0f}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                         f"⚠️ Erro ao buscar {symbol}: {e}")
            continue

        last_data = get_last_price(S3_BUCKET, symbol)
        
        save_price_to_history(S3_BUCKET, symbol, price, volume, ts)
        
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
        
        if ALERT_STRATEGY in ['moving_average', 'both']:
            history = get_price_history(S3_BUCKET, symbol)
            
            if len(history) >= 10:
                recent = filter_recent_history(history, MOVING_AVERAGE_HOURS)
                
                if len(recent) >= 10:
                    price_stats = get_price_statistics(recent)
                    volume_stats = get_volume_statistics(recent)
                    
                    _, price_z = check_anomaly(price, price_stats['mean'], price_stats['std_dev'], 2.0)
                    _, volume_z = check_anomaly(volume, volume_stats['mean'], volume_stats['std_dev'], 1.5)
                    
                    print(f"   📈 Média preço {MOVING_AVERAGE_HOURS}h: ${price_stats['mean']:,.2f} (±${price_stats['std_dev']:,.2f})")
                    print(f"   📊 Preço z-score: {price_z:+.2f}σ | Volume z-score: {volume_z:+.2f}σ")
                    
                    trend = calculate_trend_score(history, minutes=60)
                    print(f"   📊 Tendência 1h: {trend['positive_percentage']:.0f}% positivo ({trend['trend_direction']})")
                    
                    stats_data = get_stats(S3_BUCKET, symbol)
                    recency = check_record_recency(stats_data, ts, window_hours=2)
                    
                    pattern = detect_higher_lows(history, minutes=60)
                    if pattern['pattern'] != 'neutral':
                        print(f"   🔍 Padrão: {pattern['pattern']}")
                    
                    momentum = calculate_momentum(history, minutes=60)
                    if momentum['strength'] != 'weak':
                        print(f"   ⚡ Momentum: {momentum['rate_of_change']:+.2f}% ({momentum['strength']})")
                    
                    sideways = detect_sideways_movement(history, minutes=60, threshold_pct=SIDEWAYS_THRESHOLD)
                    if sideways['is_sideways']:
                        print(f"   ⏸️  Lateral: {sideways['volatility_pct']:.2f}% oscilação, {sideways['duration_minutes']:.0f}min")
                    
                    breakout = detect_breakout(
                        current_price=price,
                        sideways_data=sideways,
                        volume_z=volume_z,
                        min_breakout_pct=BREAKOUT_MIN_PCT,
                        min_volume_z=MIN_VOLUME_Z
                    )
                    
                    alert_state = get_alert_state(S3_BUCKET, symbol)
                    
                    current_ts = ts
                    was_sideways = alert_state.get('was_sideways', False)
                    sideways_start_ts = alert_state.get('sideways_start_ts', 0)
                    last_sideways_alert_ts = alert_state.get('last_sideways_alert_ts', 0)
                    
                    if sideways['is_sideways'] and not was_sideways:
                        sideways_start_ts = current_ts
                        print(f"   🔔 Início de lateralização detectado")
                    
                    if was_sideways and not sideways['is_sideways']:
                        sideways_duration = (current_ts - sideways_start_ts) / 60
                        
                        if breakout['is_breakout']:
                            direction_emoji = "📈" if breakout['direction'] == 'up' else "📉"
                            direction_text = "ALTA" if breakout['direction'] == 'up' else "BAIXA"
                            
                            if breakout['breakout_type'] == 'confirmed':
                                alert_msg = (
                                    f"{direction_emoji} *ROMPIMENTO DE {direction_text}!*\n"
                                    f"Preço rompeu: `${price:,.2f}` ({breakout['breakout_pct']:+.1f}%)\n"
                                    f"Volume: `${volume:,.0f}` ({volume_z:+.1f}σ) - CONFIRMADO\n"
                                    f"Estava lateral há: {sideways_duration:.0f} minutos\n"
                                    f"\n✅ *Ação:* ENTRADA VÁLIDA (breakout confirmado)"
                                )
                            else: 
                                alert_msg = (
                                    f"⚠️ *Rompimento SEM volume*\n"
                                    f"Preço: `${price:,.2f}` ({breakout['breakout_pct']:+.1f}%)\n"
                                    f"Volume: `${volume:,.0f}` ({volume_z:+.1f}σ) - FRACO\n"
                                    f"Estava lateral há: {sideways_duration:.0f} minutos\n"
                                    f"\n💡 *Ação:* NÃO entrar (possível bull/bear trap)"
                                )
                            
                            context_lines = []
                            if trend['trend_direction'] == 'bullish':
                                context_lines.append(f"📈 Tendência: {trend['positive_percentage']:.0f}% alta")
                            elif trend['trend_direction'] == 'bearish':
                                context_lines.append(f"📉 Tendência: {trend['positive_percentage']:.0f}% baixa")
                            
                            if pattern['pattern'] == 'bullish_reversal':
                                context_lines.append(f"✅ Higher lows confirmados")
                            elif pattern['pattern'] == 'bearish_continuation':
                                context_lines.append(f"⚠️ Lower highs confirmados")
                            
                            if context_lines:
                                alert_msg += "\n\n📊 *Contexto:*\n" + "\n".join(context_lines)
                            
                            print(f"   🚨 BREAKOUT {direction_text}!")
                            send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"{symbol}\n{alert_msg}")
                        else:
                            print(f"   🔄 Fim de lateralização (voltou a oscilar normalmente)")
                        
                        alert_state['was_sideways'] = False
                        alert_state['sideways_start_ts'] = 0
                        alert_state['last_sideways_alert_ts'] = 0
                    
                    elif sideways['is_sideways']:
                        sideways_duration = (current_ts - sideways_start_ts) / 60 if sideways_start_ts > 0 else 0
                        time_since_last_sideways_alert = (current_ts - last_sideways_alert_ts) / 60 if last_sideways_alert_ts > 0 else 999
                        
                        if sideways_duration >= SIDEWAYS_MIN_DURATION and time_since_last_sideways_alert >= SIDEWAYS_ALERT_INTERVAL:
                            alert_msg = (
                                f"⏸️ *LATERALIZAÇÃO DETECTADA*\n"
                                f"Preço oscilando: `${sideways['price_min']:,.2f}` - `${sideways['price_max']:,.2f}` ({sideways['volatility_pct']:.1f}%)\n"
                                f"Duração: {sideways_duration:.0f} minutos\n"
                                f"Volume: `${volume:,.0f}` ({volume_z:+.1f}σ)\n"
                                f"\n💡 *Ação:* AGUARDAR rompimento com volume"
                            )
                            
                            print(f"   ⏸️  ALERTA DE LATERALIZAÇÃO ({sideways_duration:.0f}min)")
                            send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"{symbol}\n{alert_msg}")
                            
                            alert_state['last_sideways_alert_ts'] = current_ts
                        
                        alert_state['was_sideways'] = True
                        if sideways_start_ts == 0:
                            alert_state['sideways_start_ts'] = current_ts
                        
                        save_alert_state(S3_BUCKET, symbol, alert_state)
                        
                        print(f"   ⏸️  Alertas normais pausados (em lateralização)")
                        continue  
                    
                    should_alert, alert_msg, new_state = evaluate_combined_anomaly(
                        price_z=price_z,
                        volume_z=volume_z,
                        current_price=price,
                        current_volume=volume,
                        mean_price=price_stats['mean'],
                        mean_volume=volume_stats['mean'],
                        std_price=price_stats['std_dev'],
                        std_volume=volume_stats['std_dev'],
                        alert_state=alert_state,
                        min_volume_z=MIN_VOLUME_Z,
                        extreme_threshold=EXTREME_THRESHOLD,
                        cooldown_minutes=ALERT_COOLDOWN_MINUTES
                    )
                    
                    if should_alert:
                        print(f"   🚨 ALERTA COMBINADO!")
                        
                        context_lines = []
                        
                        if trend['trend_direction'] == 'bullish':
                            context_lines.append(f"📈 Tendência: {trend['positive_percentage']:.0f}% alta (últimos 60min)")
                        elif trend['trend_direction'] == 'bearish':
                            context_lines.append(f"📉 Tendência: {trend['positive_percentage']:.0f}% baixa (últimos 60min)")
                        
                        if recency['atl_recent']:
                            context_lines.append(f"🔄 Saindo de ATL (há {recency['atl_minutes_ago']:.0f}min)")
                        elif recency['ath_recent']:
                            context_lines.append(f"🔄 Saindo de ATH (há {recency['ath_minutes_ago']:.0f}min)")
                        
                        if pattern['pattern'] == 'bullish_reversal':
                            context_lines.append(f"✅ Higher lows confirmados (reversão de alta)")
                        elif pattern['pattern'] == 'bearish_continuation':
                            context_lines.append(f"⚠️ Lower highs confirmados (continuação de baixa)")
                        
                        if momentum['strength'] != 'weak':
                            emoji_mom = "⚡" if momentum['direction'] == 'positive' else "⚡"
                            context_lines.append(f"{emoji_mom} Momentum {momentum['strength']}: {momentum['rate_of_change']:+.2f}%")
                        
                        if context_lines:
                            context_section = "\n\n📊 *Contexto:*\n" + "\n".join(context_lines)
                            alert_msg += context_section
                        
                        send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"{symbol}\n{alert_msg}")
                        save_alert_state(S3_BUCKET, symbol, new_state)
                    else:
                        print(f"   ✅ Normal ou em cooldown")

                    if abs(price_z) >= 1.5 or volume_z >= 1.0:
                        print(f"   🤖 Iniciando análise de sentimento (CoinGecko)...")
                        
                        rsi = calculate_rsi([h['price'] for h in recent])
                        vwap = calculate_vwap(recent, period_hours=1)
                        
                        tech_metrics = {
                            "volume_change_1h": 0, 
                            "rsi": rsi if rsi else 50
                        }
                        
                        sentiment_data = get_sentiment_data(symbol, previous_volume=volume_stats['mean'])
                        
                        pump_analysis = calculate_pump_score(sentiment_data, tech_metrics)
                        
                        if pump_analysis:
                            score = pump_analysis.get('score_pump_15_60min', 0)
                            reason = pump_analysis.get('razao_curta', 'Sem razão')
                            rec = pump_analysis.get('recomendacao', 'N/A')
                            
                            print(f"   🤖 Score Pump: {score}/100 - {reason}")
                            
                            if score >= 75:
                                emoji_ai = "🧠"
                                alert_msg_ai = (
                                    f"{emoji_ai} *ALERTA DE SENTIMENTO*\n"
                                    f"Score de Pump: *{score}/100*\n"
                                    f"💡 {reason}\n"
                                    f"🎯 Recomendação: {rec}\n"
                                    f"\n📊 *Dados Sociais:*\n"
                                    f"Menções 30min: {sentiment_data['menções_30min']}\n"
                                    f"Sentimento: {sentiment_data['sentimento_atual']}/100"
                                )
                                send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"{symbol}\n{alert_msg_ai}")
                        
                        if abs(price_z) >= 2.5 and volume_z >= 2.0:
                            direction = "ALTA" if price_z > 0 else "BAIXA"
                            emoji_extreme = "🔥" if price_z > 0 else "❄️"
                            extreme_msg = (
                                f"{emoji_extreme} *MOVIMENTO EXTREMO DE {direction}!*\n"
                                f"Preço: `{price_z:+.1f}σ` | Volume: `{volume_z:+.1f}σ`\n"
                                f"Preço atual: `${price:,.2f}`\n"
                                f"Volume 24h: `${volume:,.0f}`\n"
                                f"\n⚠️ *AÇÃO IMEDIATA RECOMENDADA*\n"
                                f"Movimento {direction.lower()} muito forte detectado!"
                            )
                            send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, f"{symbol}\n{extreme_msg}")
                            print(f"   🔥 MOVIMENTO EXTREMO DE {direction}!")
            
        
        if ALERT_STRATEGY in ['records', 'both']:

            stats_data = get_stats(S3_BUCKET, symbol)
            
            previous_high = stats_data.get('all_time_high', 0)
            previous_low = stats_data.get('all_time_low', float('inf'))
            
            updated_stats, is_new_high, is_new_low = update_records(stats_data, price, ts)
            
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
            
            if is_new_high or is_new_low:
                save_stats(S3_BUCKET, symbol, updated_stats)

    print(f"\n{'='*60}")
    print("✅ Execução concluída com sucesso!")
    print(f"{'='*60}\n")
    return {"status": "ok"}


def get_price_and_volume(symbol):
    """
    Busca preço e volume via CoinGecko, com fallback para CryptoCompare.
    """
    coin_id = get_coingecko_id(symbol)
    url_cg = f"https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids={coin_id}"
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; CryptoMonitor/1.0)'}

    try:
        req = urllib.request.Request(url_cg, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        if not data:
            raise ValueError("CoinGecko retornou vazio")
        market_data = data[0]
        return {
            'price': float(market_data["current_price"]),
            'volume': float(market_data["total_volume"])
        }
    except Exception as e:
        print(f"⚠️ Erro CoinGecko: {e} — tentando fallback...")

        # Fallback: CryptoCompare
        try:
            url_cc = f"https://min-api.cryptocompare.com/data/pricemultifull?fsyms={symbol.replace('USDT','')}&tsyms=USD"
            req_cc = urllib.request.Request(url_cc, headers=headers)
            with urllib.request.urlopen(req_cc, timeout=10) as response:
                data_cc = json.loads(response.read().decode("utf-8"))
            coin = symbol.replace('USDT','')
            price = data_cc["RAW"][coin]["USD"]["PRICE"]
            volume = data_cc["RAW"][coin]["USD"]["TOTALVOLUME24H"]
            return {
                'price': float(price),
                'volume': float(volume)
            }
        except Exception as e2:
            print(f"❌ Erro no fallback CryptoCompare: {e2}")
            return None
