# Análise de Contexto Temporal

## 📊 Visão Geral

O sistema agora inclui **análise de contexto temporal** que adiciona informações cruciais aos alertas, ajudando a identificar reversões de tendência, confirmar movimentos sustentados e detectar quando ativos estão saindo de fundos (ATL) ou topos (ATH) históricos.

**Zero impacto na frequência:** Continua rodando a cada 5 minutos, usando os mesmos dados históricos já coletados.

---

## 🆕 Novos Indicadores

### 1️⃣ **Trend Score** (Score de Tendência)
**O que é:** Percentual de movimentos positivos nos últimos 60 minutos (aproximadamente 12 candles de 5 min).

**Como funciona:**
- Compara cada preço com o anterior
- Conta quantos foram positivos vs negativos
- Calcula percentual de movimentos de alta

**Classificação:**
- ≥60% positivo → **Bullish** (tendência de alta) 📈
- ≤40% positivo → **Bearish** (tendência de baixa) 📉
- 40-60% → **Neutral** (sem tendência clara)

**Uso no alerta:**
```
📈 Tendência: 75% alta (últimos 60min)
```

---

### 2️⃣ **ATL/ATH Recency** (Proximidade de Recordes)
**O que é:** Detecta se o ativo atingiu ATH ou ATL recentemente (últimas 2 horas).

**Como funciona:**
- Rastreia timestamp quando ATH/ATL foram atingidos
- Verifica se foi há menos de 2 horas (120 minutos)
- Mostra há quantos minutos aconteceu

**Uso no alerta:**
```
🔄 Saindo de ATL (há 45min)
```

**Importância:** Se preço está subindo E saiu de ATL recentemente, indica **reversão de alta confirmada**.

---

### 3️⃣ **Higher Lows / Lower Highs** (Padrões de Topos e Fundos)
**O que é:** Detecta se fundos estão ficando mais altos (bullish) ou topos ficando mais baixos (bearish).

**Como funciona:**
- Divide últimos 60 minutos em 3-4 chunks
- Encontra mínimo e máximo local em cada chunk
- Compara progressão: fundo₁ < fundo₂ < fundo₃? → Higher lows!

**Padrões detectados:**
- **Bullish Reversal:** Fundos crescentes (cada fundo mais alto que anterior) ✅
- **Bearish Continuation:** Topos decrescentes (cada topo mais baixo que anterior) ⚠️
- **Neutral:** Sem padrão claro

**Uso no alerta:**
```
✅ Higher lows confirmados (reversão de alta)
```

**Importância:** Higher lows + movimento de alta + volume elevado = **reversão forte**.

---

### 4️⃣ **Momentum** (Taxa de Mudança)
**O que é:** Velocidade de mudança de preço na última hora.

**Como funciona:**
- Compara preço atual com preço de 1 hora atrás
- Calcula percentual de mudança
- Classifica força do movimento

**Classificação:**
- **Strong:** >3% ou <-3%
- **Moderate:** 1-3% ou -1% a -3%
- **Weak:** -1% a 1%

**Uso no alerta:**
```
⚡ Momentum strong: +4.5%
```

---

## 📨 Exemplos de Alertas com Contexto

### ✅ Exemplo 1: Reversão de Alta Confirmada
```
SOLUSDT
📈 *ANOMALIA CONFIRMADA*
Preço: `$142.50` (+2.3σ)
Volume: `$85.5M` (+1.8σ)
Movimento de alta com volume elevado
Média preço: `$135.20` (±`$3.10`)

📊 *Contexto:*
📈 Tendência: 75% alta (últimos 60min)
🔄 Saindo de ATL (há 45min)
✅ Higher lows confirmados (reversão de alta)
⚡ Momentum strong: +5.2%
```

**Interpretação:** **COMPRA FORTE** - Todos indicadores apontam reversão sustentada após fundo.

---

### ⚠️ Exemplo 2: Evento Extremo com Contexto Misto
```
BTCUSDT
💥 *EVENTO EXTREMO*
Preço: `$88,200` (-3.5σ)
QUEDA EXTREMA detectada!
Média: `$92,000` (±`$1,100`)
Volume: `$1.2B` (+0.8σ)

📊 *Contexto:*
📉 Tendência: 30% alta (últimos 60min)
⚠️ Lower highs confirmados (continuação de baixa)
⚡ Momentum strong: -3.8%
```

**Interpretação:** **CUIDADO** - Queda extrema com padrão de continuação de baixa.

---

### 🔄 Exemplo 3: Saindo do Fundo
```
ETHUSDT
⚡ *PRÉ-MOVIMENTO DETECTADO*
Volume spike: `$450M` (+2.3σ)
Preço ainda estável: `$3,100` (+0.5σ)
Possível reversão ou movimento iminente

📊 *Contexto:*
📈 Tendência: 65% alta (últimos 60min)
🔄 Saindo de ATL (há 90min)
✅ Higher lows confirmados (reversão de alta)
```

**Interpretação:** **ACUMULAÇÃO** - Volume alto sugere entrada de grandes players antes de alta.

---

## 🎯 Casos de Uso Específicos

### Detectar Reversão Após ATL
**Pergunta:** "Após atingir novo fundo, como sei se está subindo?"

**Resposta do Sistema:**
1. ✅ Detecta ATL quando acontece (estratégia de records)
2. ✅ Marca timestamp do ATL
3. ✅ Quando preço sobe com volume, alerta mostra:
   - "Saindo de ATL (há Xmin)" 
   - Trend Score mostrando % de candles positivos
   - Higher lows se fundos estiverem subindo
   - Momentum positivo confirmando força

**Exemplo real:**
- 12:00 → ATL em $130
- 12:45 → Preço $135 (+2.1σ), volume alto
- Alerta: "Saindo de ATL (há 45min) + 70% alta + higher lows + momentum +3.8%"

---

## ⚙️ Configurações

Todas as análises usam janelas de tempo fixas (não requerem variáveis de ambiente):

| Indicador | Janela de Tempo | Threshold |
|-----------|----------------|-----------|
| Trend Score | 60 minutos | 60% (bullish) / 40% (bearish) |
| ATL/ATH Recency | 2 horas | - |
| Higher Lows | 60 minutos | 3 pontos mínimos |
| Momentum | 60 minutos | 1% (moderate) / 3% (strong) |

**Não precisa configurar nada** - funciona automaticamente com os dados existentes.

---

## 🔬 Como Funciona (Técnico)

### Fluxo de Execução
```python
# 1. Coleta preço e volume (já existente)
data = get_price_and_volume(symbol)
price, volume = data['price'], data['volume']

# 2. Calcula z-scores (já existente)
price_z = (price - mean) / std_dev
volume_z = (volume - vol_mean) / vol_std

# 3. NOVO: Calcula contexto temporal
trend = calculate_trend_score(history, minutes=60)
recency = check_record_recency(stats, timestamp, window_hours=2)
pattern = detect_higher_lows(history, minutes=60)
momentum = calculate_momentum(history, minutes=60)

# 4. Avalia anomalia (já existente)
should_alert, message = evaluate_combined_anomaly(...)

# 5. NOVO: Adiciona contexto ao alerta
if should_alert:
    message += build_context_section(trend, recency, pattern, momentum)
    send_telegram(message)
```

---

## 📈 Impacto nos Alertas

### Antes (sem contexto):
```
📈 ANOMALIA CONFIRMADA
Preço: $142.50 (+2.3σ)
Volume: $85.5M (+1.8σ)
```
**Problema:** Não sabemos se é início de alta, topo, ou ruído.

### Depois (com contexto):
```
📈 ANOMALIA CONFIRMADA
Preço: $142.50 (+2.3σ)
Volume: $85.5M (+1.8σ)

📊 Contexto:
📈 Tendência: 75% alta (últimos 60min)
🔄 Saindo de ATL (há 45min)
✅ Higher lows confirmados
⚡ Momentum strong: +5.2%
```
**Solução:** Agora sabemos que é **reversão de alta forte e sustentada**.

---

## 🎓 Glossário

- **Trend Score:** Percentual de movimentos positivos
- **ATL:** All-Time Low (menor preço histórico)
- **ATH:** All-Time High (maior preço histórico)
- **Higher Lows:** Fundos crescentes (bullish)
- **Lower Highs:** Topos decrescentes (bearish)
- **Momentum:** Taxa de mudança de preço
- **Bullish Reversal:** Padrão de inversão para alta
- **Bearish Continuation:** Padrão de continuação de baixa

---

## 🚀 Próximos Passos

1. **Testar localmente:** `python main.py`
2. **Verificar logs:** Confirmar que contexto está sendo calculado
3. **Aguardar alertas:** Ver contexto nas mensagens do Telegram
4. **Validar eficácia:** Comparar alertas com/sem contexto
5. **Ajustar thresholds:** Se necessário (trend 60% → 65%, etc.)

---

**Resumo:** Sistema agora fornece **contexto inteligente** que transforma alertas simples em **sinais acionáveis** com alta confiança. 🎯
