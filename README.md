# 🪙 Crypto Price Monitor – Análise Estatística + Alertas Inteligentes

Monitoramento avançado de preços de criptomoedas com **3 estratégias de alerta**:

- 📊 **Média Móvel + Desvio Padrão** - Detecta anomalias estatísticas
- 🚀 **Recordes Históricos** - Alerta em novos topos/fundos
- 📈 **Variação Simples** - Alertas de mudança percentual

**Stack:**
- AWS Lambda (Python 3.11)
- EventBridge (cron a cada 5 min)
- S3 (histórico de 7 dias + estatísticas)
- Telegram (notificações)
- CoinGecko API (preços sem bloqueio geográfico)

---

## 🚀 Teste Local (SEM AWS)

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Telegram
Edite `.env`:
- `TELEGRAM_BOT_TOKEN` - crie com [@BotFather](https://t.me/botfather)
- `TELEGRAM_CHAT_ID` - obtenha com [@userinfobot](https://t.me/userinfobot)

### 3. Executar
```bash
python src/main.py
```

Busca preços reais e salva em `local_data/` 🎯

---

## ⚙️ Configuração

### Variáveis de Ambiente

```env
# Básicas
S3_BUCKET=crypto-price-monitor-logs-gugahb
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
TELEGRAM_BOT_TOKEN=seu_token
TELEGRAM_CHAT_ID=seu_chat_id

# Estratégias de alerta
ALERT_STRATEGY=both                # moving_average, records, both
VARIATION_ALERTS=BTCUSDT:3,ETHUSDT:4,SOLUSDT:5

# Análise estatística
HISTORY_DAYS=7                     # Janela móvel
MOVING_AVERAGE_HOURS=24            # Período para média
STDDEV_THRESHOLD=2.0               # Sensibilidade (2σ)

# Operação
ENABLE_S3=false                    # true na AWS
```

---

## 📊 Estratégias de Alerta

### 1. Variação Simples (Legado)
Alerta quando preço varia ±X% desde última leitura:
```
BTC: ±3% | ETH: ±4% | SOL: ±5%
```

### 2. Média Móvel + Desvio Padrão
Detecta anomalias estatísticas usando últimas 24h:
```
⚠️ Anomalia BTC
Preço $95,000 está 2.3σ acima da média
Média 24h: $92,000 (±$1,200)
```

### 3. Recordes Históricos
Alerta em novos topos ou fundos:
```
🚀 RECORDE BTC
Novo topo histórico: $98,500
Anterior: $96,200
```

---

## 📁 Estrutura S3

```
bucket/
├── history/
│   ├── BTCUSDT.json      # Janela móvel 7 dias (~2k registros)
│   ├── ETHUSDT.json
│   └── SOLUSDT.json
└── stats/
    ├── BTCUSDT.json      # {all_time_high, all_time_low}
    ├── ETHUSDT.json
    └── SOLUSDT.json
```

---

## 🏗️ Arquitetura

```
src/
├── main.py                          # Entry point
├── handlers/
│   └── price_monitor.py             # Lambda handler + lógica
├── config/
│   ├── settings.py                  # Variáveis de ambiente
│   └── services/
│       ├── binance_service.py       # API CoinGecko
│       ├── s3_service.py            # Histórico + stats
│       ├── telegram_service.py      # Notificações
│       └── statistics.py            # Média, σ, z-score
```

---

## 🚀 Deploy na AWS

Ver [DEPLOY.md](DEPLOY.md) para instruções completas.

**Resumo:**
```bash
# 1. Criar pacote
./deploy.sh

# 2. Upload na Lambda
# Console AWS → Lambda → crypto-price-monitor → Upload .zip

# 3. Configurar 9 variáveis de ambiente

# 4. EventBridge cron: */5 * * * ? *
```

---

## 📊 Monitoramento

### CloudWatch Logs
```bash
aws logs tail /aws/lambda/crypto-price-monitor --follow
```

### Arquivos S3
```bash
aws s3 ls s3://crypto-price-monitor-logs-gugahb/history/
aws s3 ls s3://crypto-price-monitor-logs-gugahb/stats/
```

---

## 💰 Custos

- Lambda: ~8.640 exec/mês → **$0,00** (free tier)
- S3: ~10 MB → **$0,00** (free tier)
- **Total: $0,00/mês** 🎉

---

## 🧪 Testes

```bash
# Local (sem AWS)
python src/main.py

# Lambda (manual)
aws lambda invoke --function-name crypto-price-monitor response.json

# Ver últimos alertas
grep "ALERTA\|ANOMALIA\|RECORDE" logs.txt
```

---

## 📚 Documentação

- [DEPLOY.md](DEPLOY.md) - Guia completo de deploy
- [src/config/services/statistics.py](src/config/services/statistics.py) - Cálculos estatísticos

---

## 🔧 Desenvolvimento

```bash
# Instalar deps
pip install -r requirements.txt

# Rodar testes locais
ENABLE_S3=false python src/main.py

# Gerar pacote Lambda
./deploy.sh
```