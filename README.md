# Crypto Price Monitor – AWS Lambda + S3 + Telegram

Monitoramento automático de preços de criptomoedas usando:

- AWS Lambda (Python)
- EventBridge (cron)
- S3 (logs históricos)
- Telegram (alertas)

## 🚀 Teste Local (SEM AWS)

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Telegram (opcional)
No arquivo `.env`, atualize:
- `TELEGRAM_BOT_TOKEN` - crie um bot com [@BotFather](https://t.me/botfather)
- `TELEGRAM_CHAT_ID` - obtenha com [@userinfobot](https://t.me/userinfobot)

**Obs**: O `.env` já está configurado com `ENABLE_S3=false` para rodar sem AWS

### 3. Executar
```bash
python src/main.py
```

Vai buscar preços reais da Binance e mostrar no terminal! 🚀

## Estrutura do projeto
(ver estrutura no início)

## Desenvolvimento local
```bash
cp .env.example .env
python3 src/main.py
```