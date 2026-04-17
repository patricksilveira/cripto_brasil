# CriptoBrasil Dashboard - System Specification

## Overview
A Streamlit-based interactive dashboard to visualize monthly cryptoasset operations in Brazil. It processes public data from the Receita Federal (RFB) and enhances it with monetary history from the Brazilian Central Bank (Bacen) to provide insights into volume, user adoption (CPF/CNPJ), gender distributions, and asset preferences.

## Architecture & Technology Stack
- **Core Framework:** Streamlit (v1.28.0+)
- **Data Manipulation:** Pandas (v2.0.0+)
- **Visualization:** Plotly Express & Graph Objects (v5.17.0+)
- **Excel Parsing:** xlrd/openpyxl (for reading old .xls files/latest xlsx)

## Data Flow
### 1. Data Ingestion
- **Input:** Raw Excel data from Receita Federal (`Criptoativos_Dados_Abertos_*.xls`).
- The Excel file contains multiple sheets (e.g., Relatorio1, Relatorio2, Relatório3, Relatorio4).

### 2. Data Cleaning & Normalization (`data_clean.py`)
- Reads raw Excel file.
- Cleans headers, normalizes date columns to standard "Month" and "Year", parses numeric text representations.
- Outputs standardized CSVs directly to the `saida_csv/` directory:
  - `relatorio1_operacoes_por_tipo.csv` (Operation values)
  - `relatorio2_cpfs_cnpjs_unicos.csv` (Unique entities)
  - `relatorio3_genero_operacoes.csv` (Gender breakdown)
  - `relatorio4_criptoativos_mensal.csv` (Crypto Asset specific flow)

### 3. API Integration (`utils.py`)
- Fetches daily USD/BRL rates from the Brazilian Central Bank (Bacen) open API.
- Resamples rates to a monthly mean to align with RFB's reporting structure.
- Caches the data locally in `saida_csv/usd_brl_monthly.csv` to avoid rate limits and improve speed.
- Normalizes BRL values into USD equivalents for cross-border and long-term analysis.

### 4. Presentation Layer (`dashboard.py`)
- **Theme (`theme.py`):** Supplies a custom lightweight UI theme inspired by Shadcn using `st.markdown`, injecting CSS for container styling. Modifies standard Plotly charts for a cohesive aesthetic.
- **Data Model:** Aggregates metrics to show Year-over-Year, Month-over-Month, Domestic vs. Foreign volumes, and market sentiment.
- **Tab Structure:**
  - *Introduction*: High-level summary of the market's state.
  - *Overview*: Broad metrics, historical adoption volumes, and seasonality heatmaps.
  - *Users*: Deep dives into Retail (CPFs) vs. Institutional (CNPJs).
  - *Gender*: Breakdown of trading volumes.
  - *Cryptocurrencies*: Focus on top currencies (e.g., USDT, BTC, ETH flow).

## Directory Map
```
cripto_brasil/
├── dashboard.py                           # Main Streamlit App
├── requirements.txt                       # Project dependencies
├── data_clean.py                          # Data preparation python script
├── utils.py                               # Bacen API and generic data utilities
├── theme.py                               # UI and Plotly themer
├── init.sh                                # Startup bash script
└── saida_csv/                             # Output directory for parsed CSVs
```
