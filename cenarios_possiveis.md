# 📊 Estratégia Matemática e Cenários de Alertas

## 📐 Fundamento Matemático

### **Distribuição Normal (Gaussiana)**

Assumimos que os preços e volumes seguem uma **distribuição normal** ao longo do tempo. Isso nos permite usar **desvio padrão (σ)** para detectar anomalias.

---

### **1. Cálculo do Z-Score**

**Fórmula:**
```
z = (valor_atual - média) / desvio_padrão
```

**Interpretação:**
- `z = 0` → valor está na média
- `z = +1` → 1 desvio padrão acima da média
- `z = -2` → 2 desvios padrão abaixo da média

**Probabilidade (distribuição normal):**
- 68% dos dados ficam entre `-1σ` e `+1σ`
- 95% dos dados ficam entre `-2σ` e `+2σ`
- 99.7% dos dados ficam entre `-3σ` e `+3σ`

---

### **2. Detecção de Anomalias (Preço)**

**Threshold padrão: ±2σ**

Se `|price_z| ≥ 2.0`:
- Preço está fora dos **95% normais**
- Apenas **5% de chance** de ocorrer naturalmente
- **Anomalia estatística detectada**

**Exemplo:**
```
Média: $93,000
Desvio: $1,500

Preço atual: $96,000
z = (96000 - 93000) / 1500 = +2.0σ ← ANOMALIA!
```

---

### **3. Confirmação com Volume**

**Problema:** Preço pode oscilar por ruído estatístico (falso positivo)

**Solução:** Exigir volume elevado para confirmar movimento real

**Threshold volume: ±1.0σ** (mais sensível que preço)

**Lógica combinada:**
```python
if |price_z| >= 2.0 AND volume_z >= 1.0:
    # Movimento confirmado!
    # Preço subiu/desceu E teve volume anormal
```

**Por que volume mais baixo (1σ)?**
- Volume 1σ = top 16% de volume
- Já indica interesse significativo no ativo
- Threshold 2σ seria muito rígido (só top 2.5%)

---

### **4. As 3 Regras de Alerta**

#### **REGRA 1: Anomalia Confirmada**
```
|price_z| ≥ 2σ  AND  volume_z ≥ 1σ
```
**Matemática:**
- Preço fora de 95% normal
- Volume no top 16%
- Probabilidade combinada: ~0.8% (raro!)

**Exemplo:**
```
BTC: $96,000 (+2.1σ) com volume $35B (+1.8σ)
→ Alta real confirmada, não é ruído
```

---

#### **REGRA 2: Evento Extremo**
```
|price_z| ≥ 3σ
```
**Matemática:**
- Fora de 99.7% dos dados normais
- Probabilidade: 0.3% (extremamente raro)
- Tão raro que **ignora volume** (sempre alerta)

**Exemplo:**
```
BTC cai de $93k para $88k = -3.3σ
→ Crash! Alerta imediato
```

---

#### **REGRA 3: Pré-Movimento (Volume Spike)**
```
volume_z ≥ 2σ  AND  |price_z| < 2σ
```
**Matemática:**
- Volume no top 2.5% (muito alto)
- Preço ainda normal
- **Indicador antecipado**: traders movimentando antes da volatilidade

**Exemplo:**
```
BTC em $93k (+0.5σ) mas volume $40B (+2.5σ)
→ Acumulação/distribuição antes de movimento grande
```

---

### **5. Janela Móvel (24 horas)**

**Por que 24h?**
- Remove sazonalidade diária (horário comercial vs madrugada)
- Captura 288 amostras (5 min × 12 × 24)
- Dados suficientes para estatística robusta (n > 30)

**Fórmula da média móvel:**
```
μ₂₄ₕ = (∑ preços últimas 24h) / n
```

**Fórmula do desvio padrão:**
```
σ = √[(∑(x - μ)²) / (n-1)]
```

---

### **6. Cooldown (30 minutos)**

**Problema:** Se preço fica em 2.5σ por 1 hora = 12 alertas repetidos

**Solução:** Cooldown matemático

```python
if (tempo_atual - último_alerta) < 30min:
    return False  # Bloqueia alerta
```

**Justificativa:**
- 30 min = 6 execuções (5min cada)
- Evita spam sem perder informação relevante
- Se preço continua anormal após 30min = novo alerta válido

---

### **7. Exemplo Completo**

**Histórico 24h:**
```
Média preço: $93,000
Desvio preço: $1,200
Média volume: $28B
Desvio volume: $3B
```

**Situação atual:**
```
Preço: $95,600 → z = (95600-93000)/1200 = +2.17σ
Volume: $31B → z = (31000-28000)/3000 = +1.0σ
```

**Avaliação:**
```python
# REGRA 1: |2.17| ≥ 2.0 AND 1.0 ≥ 1.0 ✅
# Volume confirma movimento!

→ 📈 ANOMALIA CONFIRMADA
  Preço: $95,600 (+2.2σ)
  Volume: $31B (+1.0σ)
  Movimento de alta com volume elevado
```

---

### **8. Vantagens Estatísticas**

✅ **Auto-ajustável**: σ se adapta à volatilidade de cada ativo  
✅ **Normalizado**: z-score compara BTC ($90k) com SOL ($130)  
✅ **Robusto**: 95% de confiança (2σ) é padrão científico  
✅ **Reduz ruído**: Volume como segunda dimensão  
✅ **Cooldown**: Evita over-trading  

---

### **📈 Resumo Visual**

```
Distribuição Normal de Preços:

       -3σ    -2σ    -1σ     μ     +1σ    +2σ    +3σ
        |      |      |      |      |      |      |
   💥━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━🚀
   Crash                Normal               ATH
         ←── 95% ──→
   
   Se preço sai dessa zona + volume alto = ALERTA!
```

---

## 📊 Todos os Cenários Possíveis de Alertas

### **1. ANOMALIA CONFIRMADA - Alta com Volume** 📈
```
Situação:
- Preço: $96,000 (+2.3σ)
- Volume: $32B (+1.5σ)

Alerta:
📈 ANOMALIA CONFIRMADA
Preço: $96,000 (+2.3σ)
Volume: $32,000,000,000 (+1.5σ)
Movimento de alta com volume elevado
Média preço: $93,000 (±$1,200)

Interpretação:
✅ Alta forte e confirmada
✅ Interesse crescente no ativo
⚠️ Pode continuar subindo (FOMO, rompimento)
```

---

### **2. ANOMALIA CONFIRMADA - Queda com Volume** 📉
```
Situação:
- Preço: $89,000 (-2.5σ)
- Volume: $35B (+2.0σ)

Alerta:
📉 ANOMALIA CONFIRMADA
Preço: $89,000 (-2.5σ)
Volume: $35,000,000,000 (+2.0σ)
Movimento de baixa com volume elevado
Média preço: $93,000 (±$1,600)

Interpretação:
⚠️ Queda forte com convicção
⚠️ Capitulação ou início de bear market
⚠️ Pode continuar caindo
```

**⚠️ Volume alto em queda = sinal bearish forte**

**Análise técnica:**
- **Capitulação**: Holders vendendo em pânico
- **Stop-loss em cascata**: Ordens automáticas disparando
- **Momentum bearish**: Traders seguindo a tendência
- **Liquidação de posições longas**: Alavancagem forçando vendas

**Contextos:**
- **-2σ**: Queda significativa, pode continuar
- **-3σ**: Possível capitulação/fundo (chance de reversão)
- Volume 4σ acima = volume MUITO alto (capitulação extrema)

---

### **3. EVENTO EXTREMO - Alta Explosiva** 🚀
```
Situação:
- Preço: $98,500 (+3.8σ)
- Volume: $29B (+0.3σ) ← volume normal!

Alerta:
🚀 EVENTO EXTREMO
Preço: $98,500 (+3.8σ)
ALTA EXTREMA detectada!
Média: $93,000 (±$1,450)
Volume: $29,000,000,000 (+0.3σ)

Interpretação:
🚨 Movimento MUITO raro (0.01% de chance)
🚨 Alerta mesmo sem volume (evento extremo)
⚠️ Possível: pump, notícia positiva, squeeze
⚠️ Risco de correção rápida
```

---

### **4. EVENTO EXTREMO - Crash** 💥
```
Situação:
- Preço: $86,000 (-4.2σ)
- Volume: $27B (-0.2σ) ← volume normal!

Alerta:
💥 EVENTO EXTREMO
Preço: $86,000 (-4.2σ)
QUEDA EXTREMA detectada!
Média: $93,000 (±$1,667)
Volume: $27,000,000,000 (-0.2σ)

Interpretação:
🚨 Crash severo (extremamente raro)
🚨 Alerta independente de volume
⚠️ Possível: hack, regulação, FUD massivo
✅ Oportunidade de compra? (fundo potencial)
```

---

### **5. PRÉ-MOVIMENTO - Volume Spike sem Preço** ⚡
```
Situação:
- Preço: $93,500 (+0.4σ) ← ainda normal
- Volume: $38B (+3.3σ) ← volume altíssimo!

Alerta:
⚡ PRÉ-MOVIMENTO DETECTADO
Volume spike: $38,000,000,000 (+3.3σ)
Preço ainda estável: $93,500 (+0.4σ)
Possível reversão ou movimento iminente

Interpretação:
🔍 Acumulação ou distribuição
🔍 Baleias movimentando antes do público
⚠️ Pode romper para cima ou para baixo em breve
✅ Fique atento nas próximas horas
```

---

### **6. SEM ALERTA - Preço Alto mas Volume Baixo** 🤔
```
Situação:
- Preço: $95,500 (+2.1σ) ← anomalia!
- Volume: $27B (+0.2σ) ← volume normal

Resultado:
✅ Normal ou em cooldown
(Bot NÃO alerta)

Interpretação:
❌ Preço subiu mas sem volume confirmando
❌ Pode ser ruído estatístico
❌ Movimento fraco, provável correção
✅ Bot evita falso positivo
```

---

### **7. SEM ALERTA - Volume Alto mas Preço Normal** 📊
```
Situação:
- Preço: $93,200 (+0.2σ) ← normal
- Volume: $33B (+1.7σ) ← alto mas < 2σ

Resultado:
✅ Normal ou em cooldown
(Bot NÃO alerta)

Interpretação:
ℹ️ Volume aumentou mas não suficiente (< 2σ)
ℹ️ Preço não reagiu ainda
✅ Aguardando confirmação
✅ Se volume >= 2σ → alerta de pré-movimento
```

---

### **8. SEM ALERTA - Cooldown Ativo** ⏰
```
Situação:
- Preço: $96,200 (+2.6σ)
- Volume: $34B (+2.0σ)
- Último alerta: há 15 minutos

Resultado:
✅ Normal ou em cooldown
(Bot NÃO alerta)

Interpretação:
🕒 Ainda em cooldown (30 min)
🕒 Evita spam de alertas repetidos
✅ Se preço continuar alto após 30min → novo alerta
```

---

### **9. RECORDES - Novo Topo Histórico** 🚀
```
Situação:
- Preço: $98,500
- All-Time High anterior: $96,200

Alerta:
🚀 RECORDE BTCUSDT
Novo topo histórico: $98,500
Anterior: $96,200

Interpretação:
🎉 Novo ATH!
✅ Rompeu resistência histórica
⚠️ Pode continuar (price discovery)
⚠️ Ou correção (profit taking)
```

---

### **10. RECORDES - Novo Fundo Histórico** 📉
```
Situação:
- Preço: $85,000
- All-Time Low anterior: $87,500

Alerta:
📉 FUNDO BTCUSDT
Menor preço histórico: $85,000
Anterior: $87,500

Interpretação:
⚠️ Novo fundo (desde que começou a monitorar)
⚠️ Possível capitulação
✅ Oportunidade de compra? (fundo técnico)
```

---

### **11. VARIAÇÃO SIMPLES - Compatibilidade** 📊
```
Situação:
- Preço atual: $95,790
- Preço anterior: $93,000 (5 min atrás)
- Variação: +3.0% (threshold: ±3%)

Alerta:
📈 Variação BTCUSDT
Preço subiu: +3.00%
De $93,000 para $95,790

Interpretação:
ℹ️ Alerta legado (mantém compatibilidade)
ℹ️ Não considera volume
ℹ️ Mais sensível (pode gerar mais alertas)
```

---

### **12. NENHUM ALERTA - Tudo Normal** ✅
```
Situação:
- Preço: $93,200 (+0.17σ)
- Volume: $28B (+0.0σ)

Resultado:
✅ Dentro da faixa normal (< 2σ)

Interpretação:
✅ Mercado estável
✅ Nenhuma anomalia detectada
✅ Bot em modo de observação
```

---

## 📋 Resumo de Probabilidades

| Cenário | Probabilidade | Ação do Bot |
|---------|---------------|-------------|
| Normal (dentro 2σ) | 95% | Sem alerta |
| Anomalia 2σ + volume | ~0.8% | 🚨 Alerta confirmado |
| Evento extremo 3σ | ~0.3% | 🚨 Alerta sempre |
| Volume spike 2σ | ~2.5% | ⚡ Pré-movimento |
| Preço alto sem volume | ~2.5% | ❌ Sem alerta (falso positivo) |
| Cooldown ativo | Variável | ⏰ Sem alerta (spam) |
| ATH/ATL | Único | 🎉 Alerta de recorde |

---

## 🎯 Tipos de Emoji por Contexto

- 📈 Alta confirmada
- 📉 Queda confirmada
- 🚀 Alta extrema (>3σ)
- 💥 Queda extrema (>3σ)
- ⚡ Pré-movimento (volume spike)
- 🎉 Novo recorde (ATH)
- ⚠️ Novo fundo (ATL)
- ✅ Normal / Sem alerta

---

## 🧠 Como Usar a Informação

### ⚖️ O Bot Não Diz "Compre" ou "Venda"

**O que o bot FAZ:**
```
✅ Detecta: "Movimento estatisticamente anormal confirmado"
✅ Informa: Magnitude (z-score) e direção
```

**O que o bot NÃO faz:**
```
❌ Prever: "Vai cair mais 10%"
❌ Recomendar: "Venda agora!"
```

### **Análise Complementar Recomendada:**
1. **Checar notícias**: Regulação? Hack? FUD? Notícia positiva?
2. **Ver gráfico**: Rompeu suporte/resistência importante?
3. **Comparar com mercado**: S&P500 caindo também? Correlação?
4. **Histórico**: Última vez que teve -3σ, recuperou em quanto tempo?

### **Possíveis Ações por Perfil:**
- **Trader**: Stop-loss / Short / Take profit
- **Holder**: DCA (compra gradual no fundo) / Hold
- **Cautela**: Aguardar estabilização

---

## 📊 Volume 24h - Detalhes Técnicos

**O que o bot usa:**
- Volume total negociado nas últimas 24 horas (USD)
- Padrão do mercado crypto (Binance, CoinMarketCap, CoinGecko)

**Por que 24h e não horário?**
✅ Remove sazonalidade diária (horário comercial vs madrugada)  
✅ Filtra ruído de curto prazo  
✅ Mostra tendência real de interesse no ativo  
✅ Padrão da indústria  

**Limitação:**
- Não captura volume instantâneo de 5 minutos
- Para volume mais granular precisaria API diferente (Binance WebSocket)

---

**Matemática garante: alertas apenas quando estatisticamente significativo!** 🎯

**Total: 12 cenários possíveis de alertas!**