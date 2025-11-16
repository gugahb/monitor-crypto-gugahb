import time
from src.config.settings import SYMBOLS, S3_BUCKET, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, VARIATION_DICT
from src.config.services.binance_service import get_price
from src.config.services.s3_service import save_price, get_last_price
from src.config.services.telegram_service import send_message

def lambda_handler(event, context):
    ts = time.time()
    print(f"\n{'='*60}")
    print(f"Monitor de Criptomoedas - {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    for symbol in SYMBOLS:
        print(f"\n📊 Buscando preço de {symbol}...")
        print(f"\n📊 Buscando preço de {symbol}...")
        try:
            price = get_price(symbol)
            print(f"   💰 Preço atual: ${price:,.2f}")
        except Exception as e:
            print(f"   ❌ Erro: {e}")
            send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                         f"⚠️ Erro ao buscar {symbol}: {e}")
            continue

        # IMPORTANTE: Busca último preço ANTES de salvar o novo
        last_data = get_last_price(S3_BUCKET, symbol) if symbol in VARIATION_DICT else None
        
        # Agora salva o novo preço
        save_price(S3_BUCKET, symbol, price, ts)
        
        # Verifica alerta de variação percentual
        if symbol in VARIATION_DICT:
            variation_threshold = VARIATION_DICT[symbol]
            
            if last_data:
                last_price = last_data['price']
                variation = ((price - last_price) / last_price) * 100
                
                print(f"   📊 Variação desde última: {variation:+.2f}% (limite: ±{variation_threshold}%)")
                
                if abs(variation) >= variation_threshold:
                    emoji = "📈" if variation > 0 else "📉"
                    direction = "subiu" if variation > 0 else "caiu"
                    print(f"   {emoji} VARIAÇÃO SIGNIFICATIVA detectada!")
                    send_message(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
                                 f"{emoji} *Variação {symbol}*\n"
                                 f"Preço {direction}: `{variation:+.2f}%`\n"
                                 f"De `${last_price:,.2f}` para `${price:,.2f}`")
                else:
                    print(f"   ✅ Variação dentro do normal")
            else:
                print(f"   ℹ️  Primeira leitura - salvando referência...")

    print(f"\n{'='*60}")
    print("✅ Execução concluída com sucesso!")
    print(f"{'='*60}\n")
    return {"status": "ok"}
