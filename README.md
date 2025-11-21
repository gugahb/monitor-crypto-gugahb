# 🪙 Crypto Price Monitor – Análise Estatística + Alertas Inteligentes com Contexto Temporal

Monitoramento avançado de preços de criptomoedas com **análise combinada de preço + volume** e **contexto temporal inteligente**:

- 📊 **Anomalia Confirmada** - Preço ≥2σ + Volume ≥1σ (probabilidade ~0,8%)
- 🚀 **Evento Extremo** - Preço ≥3σ independente de volume (~0,3%)
- ⚡ **Pré-Movimento** - Volume ≥2σ com preço estável (acumulação)
- 🎯 **Contexto Temporal** - Tendência, ATL/ATH recente, higher lows, momentum
- 🏆 **Recordes Históricos** - Novos topos/fundos (ATH/ATL)
- 📈 **Variação Simples** - Mudança >5% desde último candle

**Stack:**
- AWS Lambda (Python 3.11)
- EventBridge (cron a cada 5 min)
- S3 (histórico 7 dias + estatísticas + estado de alertas)
- Telegram (notificações com contexto rico)
- CoinGecko API (preço + volume 24h, sem bloqueio geográfico)

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

**Exemplo:**
```env
TELEGRAM_BOT_TOKEN=1234567890:AMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

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
S3_BUCKET=seu-bucket-crypto-monitor
SYMBOLS=BTCUSDT,ETHUSDT,SOLUSDT
TELEGRAM_BOT_TOKEN=12347890:ABCdeOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123789

# Estratégias de alerta
ALERT_STRATEGY=both                # moving_average, records, both
VARIATION_ALERTS=BTCUSDT:3,ETHUSDT:4,SOLUSDT:5

# Análise estatística de preço
HISTORY_DAYS=7                     # Janela móvel (7 dias)
MOVING_AVERAGE_HOURS=24            # Período para média (24h)
STDDEV_THRESHOLD=2.0               # Threshold z-score preço (2σ = 95%)

# Análise de volume (redução de falsos positivos)
MIN_VOLUME_Z=1.0                   # Mínimo z-score volume para confirmar (1σ = 84%)
EXTREME_THRESHOLD=3.0              # Threshold eventos extremos (3σ = 99.7%)
ALERT_COOLDOWN_MINUTES=30          # Cooldown entre alertas (30 min = 6 execuções)

# Operação
ENABLE_S3=false                    # true na AWS, false local
```

**Total: 12 variáveis** (9 originais + 3 de volume)

---

## 📊 Estratégias de Alerta

### 1. Anomalia Confirmada (Preço + Volume)
**Regra:** |price_z| ≥ 2σ AND volume_z ≥ 1σ  
**Probabilidade:** ~0,8% (altamente confiável)

```
📈 ANOMALIA CONFIRMADA
Preço: $95,000 (+2.3σ)
Volume: $1.2B (+1.8σ)
Movimento de alta com volume elevado
Média preço: $92,000 (±$1,200)

📊 Contexto:
📈 Tendência: 75% alta (últimos 60min)
🔄 Saindo de ATL (há 45min)
✅ Higher lows confirmados (reversão de alta)
⚡ Momentum strong: +5.2%
```

### 2. Evento Extremo
**Regra:** |price_z| ≥ 3σ (independente de volume)  
**Probabilidade:** ~0,3% (raríssimo)

```
💥 EVENTO EXTREMO
Preço: $88,200 (-3.5σ)
QUEDA EXTREMA detectada!
Média: $92,000 (±$1,100)
Volume: $1.2B (+0.8σ)

📊 Contexto:
📉 Tendência: 30% alta (últimos 60min)
⚠️ Lower highs confirmados (continuação de baixa)
```

### 3. Pré-Movimento (Volume Spike)
**Regra:** volume_z ≥ 2σ AND |price_z| < 2σ  
**Probabilidade:** ~2,5% (acumulação/distribuição)

```
⚡ PRÉ-MOVIMENTO DETECTADO
Volume spike: $450M (+2.3σ)
Preço ainda estável: $3,100 (+0.5σ)
Possível reversão ou movimento iminente

📊 Contexto:
📈 Tendência: 65% alta (últimos 60min)
✅ Higher lows confirmados
```

### 4. Recordes Históricos (ATH/ATL)
Alerta em novos topos ou fundos:
```
🚀 RECORDE BTCUSDT
Novo topo histórico: $98,500
Anterior: $96,200
```

### 5. Variação Simples (Legado)
Alerta quando preço varia ±X% desde última leitura:
```
📈 Variação SOLUSDT
Preço subiu: +5.3%
De $130.00 para $136.89
```

---

## 📁 Estrutura S3

```
bucket/
├── history/
│   ├── BTCUSDT.json      # [{price, volume, timestamp}, ...] - 7 dias
│   ├── ETHUSDT.json
│   └── SOLUSDT.json
├── stats/
│   ├── BTCUSDT.json      # {all_time_high, all_time_low, last_ath_timestamp, last_atl_timestamp}
│   ├── ETHUSDT.json
│   └── SOLUSDT.json
└── alert_state/
    ├── BTCUSDT.json      # {last_alert_ts, last_price_z, last_volume_z}
    ├── ETHUSDT.json
    └── SOLUSDT.json
```

**Volumes:**
- history: ~2.000 registros/símbolo (5min × 12/h × 24h × 7d)
- stats: 4 campos por símbolo
- alert_state: 3 campos por símbolo
- **Total:** ~10 MB para 3 símbolos

---

## 🏗️ Arquitetura

```
src/
├── main.py                          # Entry point (local)
├── handlers/
│   └── price_monitor.py             # Lambda handler + orquestração
├── config/
│   ├── settings.py                  # Variáveis de ambiente (12 vars)
│   └── services/
│       ├── binance_service.py       # CoinGecko API (preço + volume)
│       ├── s3_service.py            # Persistência (history/stats/alert_state)
│       ├── telegram_service.py      # Notificações Telegram
│       ├── statistics.py            # Análise estatística + contexto temporal
│       └── alert_state.py           # Cooldown management
```

**Fluxo de Execução:**
1. EventBridge aciona Lambda a cada 5 min
2. `price_monitor.py` busca preço + volume (CoinGecko)
3. Salva histórico no S3 (janela móvel 7 dias)
4. Calcula estatísticas: μ, σ, z-scores (preço e volume)
5. **NOVO:** Calcula contexto temporal (trend, recency, patterns, momentum)
6. Avalia 3 regras de alerta com cooldown de 30 min
7. Envia mensagem Telegram com contexto rico
8. Atualiza alert_state e stats no S3

---

## 🚀 Deploy na AWS

Ver [DEPLOY.md](DEPLOY.md) para instruções completas.

**Resumo:**
```bash
# 1. Criar pacote
./deploy.sh

# 2. Upload na Lambda
# Console AWS → Lambda → crypto-price-monitor → Upload .zip

# 3. Configurar 12 variáveis de ambiente (9 originais + 3 volume)

# 4. EventBridge cron: */5 * * * ? *
```

**Variáveis obrigatórias:**
- S3_BUCKET, SYMBOLS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
- ALERT_STRATEGY, VARIATION_ALERTS
- HISTORY_DAYS, MOVING_AVERAGE_HOURS, STDDEV_THRESHOLD
- MIN_VOLUME_Z, EXTREME_THRESHOLD, ALERT_COOLDOWN_MINUTES

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

- **[DEPLOY.md](DEPLOY.md)** - Guia completo de deploy AWS
- **[CONTEXT_ANALYSIS.md](CONTEXT_ANALYSIS.md)** - Análise de contexto temporal (trend, recency, patterns, momentum)
- **[cenarios_possiveis.md](cenarios_possiveis.md)** - 12 cenários de alerta com interpretações
- **[statistics.py](src/config/services/statistics.py)** - Funções estatísticas e análise temporal

### 🎓 Conceitos Importantes
- **Z-score:** Normaliza valores de ativos diferentes (BTC $90k vs SOL $130)
- **2σ:** 95% de confiança (só 5% de chance natural)
- **3σ:** 99,7% de confiança (evento extremo)
- **Volume confirmation:** Reduz falsos positivos de ~5% para ~0,8%
- **Cooldown:** Evita spam (30 min = 6 execuções)
- **Trend Score:** % de movimentos positivos (60 min)
- **Higher Lows:** Fundos crescentes = reversão de alta
- **Momentum:** Taxa de mudança 1h (strong >3%)

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