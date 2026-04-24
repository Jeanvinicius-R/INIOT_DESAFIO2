# INIOT_DESAFIO# 📡 IIoT Data Analysis Dashboard — Desafio 2

Projeto desenvolvido para monitoramento e análise de dados IIoT utilizando sensores DHT, MQTT, Node-RED e Python.

O sistema realiza:

- Coleta de dados em tempo real via MQTT
- Monitoramento de temperatura e umidade
- Armazenamento dos registros em CSV
- Exportação dos dados pelo dashboard Node-RED
- Importação do CSV em uma aplicação Python com interface gráfica
- Geração de dashboard analítico e relatório estatístico

---

# 🚀 Tecnologias utilizadas

## Backend / IIoT
- Node-RED
- MQTT
- Broker MQTT
- JSON
- CSV

## Análise de Dados
- Python 3
- Pandas
- Matplotlib
- Tkinter

---

# 📂 Estrutura do Projeto

```bash
├── analise_iiot.py          # Aplicação gráfica em Python
├── fluxo_nodered.json       # Fluxo do Node-RED
├── dados_exemplo.csv        # Dataset para testes
└── README.md
```

---

# ⚙️ Arquitetura do Projeto

## Fluxo de Dados

```text
Sensor DHT
   ↓
MQTT Publisher
   ↓
Broker MQTT
   ↓
Node-RED
 ├── Dashboard em tempo real
 ├── Armazenamento em memória
 └── Exportação CSV
          ↓
Python Dashboard Analítico
```

---

# 📊 Funcionalidades

## Monitoramento em Tempo Real (Node-RED)

- Gauge de temperatura
- Gauge de umidade
- Atualização a cada 2 segundos
- Exportação de histórico em CSV

### Dados armazenados:

- ID
- Data/Hora
- Timestamp ISO
- Temperatura
- Umidade

---

## Dashboard Analítico (Python)

Após importar o CSV:

### KPIs

✔ Média  
✔ Mínimo e máximo  
✔ Desvio padrão  
✔ Coeficiente de variação

---

### Visualizações

- Séries temporais com bandas ±1σ e ±2σ
- Desvio padrão móvel
- Boxplot para detecção de outliers
- Histogramas de frequência

---

### Relatório estatístico automático

Calcula:

- Média (μ)
- Mediana
- Desvio padrão (σ)
- Quartis (Q1 e Q3)
- IQR
- Outliers (1.5 × IQR)
- Faixas μ ± 1σ e μ ± 2σ

---

# ▶ Como Executar

## 1 — Node-RED

Importe o arquivo:

```bash
fluxo_nodered.json
```

Configure o broker MQTT:

```text
IP: 10.110.12.65
Porta: 1883
Tópico: iiot/desafio2
```

Abrir dashboard:

```bash
http://localhost:1880/ui
```

---

## 2 — Python

Instalar dependências:

```bash
pip install pandas matplotlib
```

Executar:

```bash
python analise_iiot.py
```

Importe o CSV exportado do Node-RED.

---

# 📈 Exemplo de Métricas

```text
Temperatura média: 26.3 °C
Desvio padrão: 0.72
Coeficiente de variação: 2.74 %

Umidade média: 61.8 %
Outliers detectados: 2
```

---

# 🔍 Conceitos Aplicados

Este projeto aplica conceitos de:

- IIoT (Industrial Internet of Things)
- Aquisição de Dados
- MQTT Publish/Subscribe
- Monitoramento em Tempo Real
- Análise Estatística
- Controle Estatístico de Processo (CEP)
- Visualização de Dados

---

# 💡 Melhorias Futuras

- Banco de dados para persistência histórica
- Alertas automáticos para desvios
- Detecção de anomalias com Machine Learning
- Dashboard Web em Streamlit ou React
- Integração com sensores reais ESP32

---

# 👨‍💻 Autor

Jean Vinicius Rodrigues

Projeto acadêmico — Desafio IIoT / Análise e Visualização de Dados
