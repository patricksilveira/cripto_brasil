# CriptoBrasil Dashboard — CLAUDE.md

## Project Overview

An interactive dashboard for Brazilian crypto asset market data sourced from the Receita Federal (RFB). Processes raw monthly Excel reports into cleaned CSVs and visualizes them via Streamlit + Plotly with a Shadcn-inspired UI theme.

**Live at:** Streamlit local server `http://localhost:8501`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Streamlit ≥ 1.28.0 |
| Charts | Plotly Express + Graph Objects ≥ 5.17.0 |
| Data | Pandas ≥ 2.0.0 |
| Excel parsing | xlrd / openpyxl |
| FX API | Bacen open API (series 1, USD/BRL daily → monthly avg) |
| Language | Python 3.11 (venv at `./venv`) |

---

## File Map

```
cripto_brasil/
├── dashboard.py                  # Main Streamlit app (entry point)
├── data_clean.py                 # XLS → CSV ETL script
├── utils.py                      # Bacen FX API + DataFrame normalization helpers
├── theme.py                      # Shadcn-inspired Plotly theme + CSS injector
├── init.sh                       # First-run setup script (venv + deps + ETL)
├── requirements.txt              # Python dependencies
├── spec.md                       # Original product specification
│
├── criptoativos_dados_abertos_20260415.xls   # Latest RFB raw data (Apr 2026)
├── Criptoativos_Dados_Abertos_20251112.xls   # Nov 2025 snapshot
├── criptoativos_dados_abertos_20250822.xls   # Aug 2025 snapshot
│
├── saida_csv/                    # Active CSVs loaded by dashboard
│   ├── relatorio1_operacoes_por_tipo.csv
│   ├── relatorio2_cpfs_cnpjs_unicos.csv
│   ├── relatorio3_genero_operacoes.csv
│   ├── relatorio4_criptoativos_mensal.csv
│   └── usd_brl_monthly.csv       # Cached FX rates
│
└── saida_csv_archive_20251112/   # Historical snapshot (Nov 2025)
```

---

## Running the App

```bash
# First time
bash init.sh

# Subsequent runs
source venv/bin/activate
streamlit run dashboard.py
```

---

## Data Update Workflow

When the RFB publishes a new monthly report:

1. Drop the new `.xls` file in the project root.
2. Update `ARQUIVO_XLS` in `data_clean.py` to point to the new file.
3. Run `python data_clean.py` — outputs to `saida_csv/`.
4. Archive the old CSVs to a `saida_csv_archive_YYYYMMDD/` folder if needed.
5. Delete `saida_csv/usd_brl_monthly.csv` to force a fresh FX rate fetch.
6. Update the README date header.

---

## Dashboard Structure

### Sidebar
- **Currency toggle:** BRL / USD (all monetary values re-scale on toggle)
- **Date range filter:** Slices all charts simultaneously

### Tabs
1. **Introduction** — High-level market summary, disclaimer
2. **Overview** — Total volume, user adoption, seasonality heatmaps, YoY comparison
3. **Users** — CPF (retail) vs. CNPJ (institutional) unique entity counts and growth
4. **Gender** — % of operations and values by gender over time
5. **Cryptocurrencies** — Top-N assets by volume, op count, and average ticket

---

## Key Conventions

- **Currency columns:** BRL columns are named as-is (e.g. `valor_total`); USD equivalents are suffixed `_usd` (e.g. `valor_total_usd`). Never rename this pattern.
- **Date column:** Always stored as `datetime` in a column called `data`; year and month also stored separately as `ano` / `mes` integers.
- **FX normalization:** `utils.normalize_dataframe()` merges on `ym` (Period M) — keep this merge key logic intact when adding new value columns.
- **Theme:** `theme.apply_shadcn_theme(fig)` must be called on every Plotly figure. `theme.get_custom_css()` injects global CSS at app startup.
- **Caching:** `@st.cache_data` on `load_data()` — clear with `streamlit cache clear` or `R` in the browser when CSVs change.
- **Values scale:** Monetary values from RFB are in millions of BRL. The dashboard multiplies by `1_000_000` only when computing per-user metrics.

---

## Backlog / Next Tasks

### 1. ⚡ shadcn/ui Migration (NEXT — PRIORITY)
The current theme is a CSS approximation of shadcn/ui injected via `st.markdown`. 

**Decision needed:** The user wants to adopt the real [shadcn/ui](https://ui.shadcn.com/) component library.  
Since shadcn/ui is a React component library, this likely means one of:

- **Option A — Full migration to Next.js + shadcn/ui:** Replace Streamlit with a Next.js frontend (React), keep Python as a data API layer (FastAPI or static JSON export). Full design fidelity, proper component library.
- **Option B — Improve the CSS approximation:** Stay on Streamlit, improve `theme.py` CSS to more closely match shadcn/ui tokens (colors, radius, shadows, typography) using the [shadcn/ui design tokens](https://ui.shadcn.com/themes).

**Clarify with user before starting.**

### 2. Data Update — Next RFB Release
- Watch for new `.xls` from Receita Federal after each month's report.
- Follow the update workflow above.

### 3. Potential Enhancements (not started)
- Search / filter by specific crypto asset in the Cryptocurrencies tab
- Export charts as PNG/PDF button
- Dark mode toggle (theme already has the palette defined)
- Mobile-responsive layout improvements
- Deploy to Streamlit Community Cloud or a VPS
