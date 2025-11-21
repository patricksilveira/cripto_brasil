import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(
    page_title="CryptoBrazil Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
st.markdown("""
    <style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .header {
        color: #1f77b4;
        font-size: 28px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .logo-container {
        display: flex;
        align-items: left;
        gap: 20px;
        margin-bottom: 20px;
    }
    .disclaimer {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #1f77b4;
        margin: 20px 0;
        font-size: 14px;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    base_path = Path(__file__).parent / "saida_csv"
    
    data = {
        "operacoes": pd.read_csv(base_path / "relatorio1_operacoes_por_tipo.csv"),
        "usuarios": pd.read_csv(base_path / "relatorio2_cpfs_cnpjs_unicos.csv"),
        "genero": pd.read_csv(base_path / "relatorio3_genero_operacoes.csv"),
        "criptoativos": pd.read_csv(base_path / "relatorio4_criptoativos_mensal.csv")
    }
    
    # Create date column for sorting
    for key in ["operacoes", "usuarios", "genero"]:
        data[key]["data"] = pd.to_datetime(
            data[key]["ano"].astype(str) + "-" + data[key]["mes"].astype(str) + "-01"
        )
    
    data["criptoativos"]["data"] = pd.to_datetime(
        data["criptoativos"]["ano"].astype(str) + "-" + 
        data["criptoativos"]["mes"].astype(str) + "-01"
    )
    
    return process_data(data)

def process_data(data):
    # 1. Merge Operations and Users for normalized metrics
    # We need to aggregate operations by date first to match users granularity
    ops_monthly = data["operacoes"].groupby("data").agg({
        "valor_total": "sum",
        "valor_exterior_pf": "sum",
        "valor_exterior_pj": "sum",
        "valor_sem_ex_subtotal": "sum",
        "valor_exchanges": "sum"
    }).reset_index()
    
    users_monthly = data["usuarios"][["data", "cpfs_unicos", "cnpjs_unicos"]].copy()
    users_monthly["total_users"] = users_monthly["cpfs_unicos"] + users_monthly["cnpjs_unicos"]
    
    # Calculate User Growth (MoM)
    users_monthly = users_monthly.sort_values("data")
    users_monthly["user_growth_pct"] = users_monthly["total_users"].pct_change() * 100
    users_monthly["cpf_growth_pct"] = users_monthly["cpfs_unicos"].pct_change() * 100
    users_monthly["cnpj_growth_pct"] = users_monthly["cnpjs_unicos"].pct_change() * 100
    
    # Merge for "Volume per User"
    merged_metrics = pd.merge(ops_monthly, users_monthly, on="data", how="left")
    merged_metrics["vol_per_user"] = merged_metrics["valor_total"] * 1_000_000 / merged_metrics["total_users"] # Convert M to units
    
    # 2. Calculate Ratios in Operations Data
    # PF vs PJ Ratio (Approximation using available columns)
    # Note: The dataset has 'valor_exterior_pf', 'valor_exterior_pj'. 
    # For 'valor_sem_ex' and 'valor_exchanges', we don't have the split in the main columns shown in load_data,
    # but let's check if we can derive it or if we only use the exterior split for now.
    # Looking at the CSV columns: valor_exterior_pf, valor_exterior_pj, valor_sem_ex_pf, valor_sem_ex_pj
    # We can calculate total PF and total PJ if we assume 'valor_exchanges' is mixed or mostly retail? 
    # Actually, let's use the explicit columns we have.
    
    ops_df = data["operacoes"].copy()
    
    # Calculate Total PF and PJ (excluding the generic 'valor_exchanges' if it doesn't have a split)
    # Based on CSV header: valor_sem_ex_pf, valor_sem_ex_pj exist.
    ops_df["total_pf_known"] = ops_df["valor_exterior_pf"] + ops_df["valor_sem_ex_pf"]
    ops_df["total_pj_known"] = ops_df["valor_exterior_pj"] + ops_df["valor_sem_ex_pj"]
    
    # Calculate ratios for known segments
    ops_df["ratio_pf"] = ops_df["total_pf_known"] / (ops_df["total_pf_known"] + ops_df["total_pj_known"])
    ops_df["ratio_pj"] = ops_df["total_pj_known"] / (ops_df["total_pf_known"] + ops_df["total_pj_known"])
    
    # Domestic vs Foreign (Cross-border)
    ops_df["total_volume_check"] = ops_df["valor_total"]
    ops_df["pct_foreign"] = (ops_df["valor_exterior_subtotal"] / ops_df["valor_total"]) * 100
    ops_df["pct_domestic"] = 100 - ops_df["pct_foreign"]
    
    # Store processed data back
    data["merged_metrics"] = merged_metrics
    data["operacoes_enriched"] = ops_df
    
    return data

try:
    data = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

# Sidebar filters
st.sidebar.markdown("## 🎯 Filters")

# Get available years from all datasets
all_years = sorted(set(
    list(data["operacoes"]["ano"].unique()) +
    list(data["usuarios"]["ano"].unique()) +
    list(data["genero"]["ano"].unique()) +
    list(data["criptoativos"]["ano"].unique())
))

# Get date range from all datasets
min_date = min(
    data["operacoes"]["data"].min(),
    data["usuarios"]["data"].min(),
    data["genero"]["data"].min(),
    data["criptoativos"]["data"].min()
)

max_date = max(
    data["operacoes"]["data"].max(),
    data["usuarios"]["data"].max(),
    data["genero"]["data"].max(),
    data["criptoativos"]["data"].max()
)

# Filter type selector
filter_type = st.sidebar.radio(
    "Filter Type:",
    options=["By Year", "Date Range", "All Period", "Total Data"],
    index=0
)

st.sidebar.markdown("---")

# Apply filters based on type
if filter_type == "By Year":
    selected_year = st.sidebar.selectbox(
        "Select Year:",
        options=all_years,
        index=len(all_years) - 1  # Default to latest year
    )

    filtered_op = data["operacoes"][data["operacoes"]["ano"] == selected_year].copy()
    filtered_users = data["usuarios"][data["usuarios"]["ano"] == selected_year].copy()
    filtered_gender = data["genero"][data["genero"]["ano"] == selected_year].copy()
    filtered_crypto = data["criptoativos"][data["criptoativos"]["ano"] == selected_year].copy()

    # Filter merged metrics
    filtered_merged = data["merged_metrics"][data["merged_metrics"]["data"].dt.year == selected_year].copy()

    filter_label = f"Year: {selected_year}"

elif filter_type == "Date Range":
    col1, col2 = st.sidebar.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date:",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )

    with col2:
        end_date = st.date_input(
            "End Date:",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )

    # Convert to datetime for comparison
    start_date = pd.Timestamp(start_date)
    end_date = pd.Timestamp(end_date)

    filtered_op = data["operacoes"][(data["operacoes"]["data"] >= start_date) &
                                     (data["operacoes"]["data"] <= end_date)].copy()
    filtered_users = data["usuarios"][(data["usuarios"]["data"] >= start_date) &
                                       (data["usuarios"]["data"] <= end_date)].copy()
    filtered_gender = data["genero"][(data["genero"]["data"] >= start_date) &
                                      (data["genero"]["data"] <= end_date)].copy()
    filtered_crypto = data["criptoativos"][(data["criptoativos"]["data"] >= start_date) &
                                            (data["criptoativos"]["data"] <= end_date)].copy()
    filtered_merged = data["merged_metrics"][(data["merged_metrics"]["data"] >= start_date) &
                                              (data["merged_metrics"]["data"] <= end_date)].copy()

    filter_label = f"From {start_date.strftime('%m/%d/%Y')} to {end_date.strftime('%m/%d/%Y')}"

elif filter_type == "All Period":
    filtered_op = data["operacoes"].copy()
    filtered_users = data["usuarios"].copy()
    filtered_gender = data["genero"].copy()
    filtered_crypto = data["criptoativos"].copy()
    filtered_merged = data["merged_metrics"].copy()

    filter_label = f"All period ({min_date.strftime('%m/%Y')} to {max_date.strftime('%m/%Y')})"

else:  # Total Data
    # Aggregate all data
    filtered_op = data["operacoes"].groupby(level=0, sort=False).sum(numeric_only=True).reset_index(drop=True)
    filtered_op["data"] = pd.NaT
    filtered_op["mes"] = 0
    filtered_op["ano"] = 0

    filtered_users = data["usuarios"].groupby(level=0, sort=False).sum(numeric_only=True).reset_index(drop=True)
    filtered_users["data"] = pd.NaT
    filtered_users["mes"] = 0
    filtered_users["ano"] = 0

    filtered_gender = data["genero"].groupby(level=0, sort=False).sum(numeric_only=True).reset_index(drop=True)
    filtered_gender["data"] = pd.NaT
    filtered_gender["mes"] = 0
    filtered_gender["ano"] = 0

    filtered_crypto = data["criptoativos"].copy()

    # For merged metrics in "Total Data", we need to aggregate
    filtered_merged = data["merged_metrics"].copy()
    # We can't easily aggregate "per user" metrics for the whole period without re-calculating
    # So for "Total Data" we might show the average of the period

    filter_label = "Total Data (Aggregated)"

# Main header with logo
st.image('dashboard_criptobrasil_logo.png', width=250)
st.markdown('<p class="header">📊 CryptoBrazil Dashboard</p>', unsafe_allow_html=True)
st.markdown(f"*Filter: **{filter_label}** | Last updated: {datetime.now().strftime('%m/%d/%Y at %H:%M')}*")

# ============ TABS ============
tab_intro, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Introduction", "Overview", "Operations", "Users", "Gender", "Cryptocurrencies"
])

# Helper function to create title based on filter type
def get_title_suffix():
    if filter_type == "By Year":
        return f"- {int(filtered_op['ano'].unique()[0]) if not filtered_op.empty and filtered_op['ano'].unique()[0] > 0 else 'Selected Period'}"
    elif filter_type == "Total Data":
        return "- Aggregated Data"
    else:
        return "- Selected Period"

# ============ TAB INTRO: INTRODUCTION ============
with tab_intro:
    st.title("Brazilian Crypto Market Analysis (2024-2025)")
    
    # Data source disclaimer
    st.markdown("""
    <div class="disclaimer">
    📊 <strong>Data Source Disclaimer</strong><br>
    This dashboard uses <strong>open source data from Receita Federal Brasil</strong> (Brazilian Federal Revenue Service).<br>
    <strong>Data Analysis:</strong> Produced by Perplexity AI in November 2025 
    (<a href="https://pplx.ai/patrickds3872" target="_blank">View Analysis</a>)<br>
    <strong>Official Data Sources:</strong> 
    <a href="https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/criptoativos" target="_blank">Receita Federal - Crypto Assets</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
## 1. Overall Market Size and Transaction Patterns

Brazil's cryptocurrency market, measured through Receita Federal's comprehensive tracking, processed **R\$ 1.334 trillion** in total transaction volume across **453 million individual transactions** over the 72-month measurement period. This equates to an **average transaction size of R\$ 2,944.25**, revealing a market dominated by small to medium retail transactions punctuated by large institutional settlements.

The market exhibits steady growth, with August 2019 opening at R\$ 4.04 billion monthly and peak monthly volumes reaching R\$ 12+ billion in late 2024. The data confirms Brazil's position as Latin America's largest crypto market, representing approximately 31% of regional volume according to Chainalysis.[1][2]

## 2. Extreme Asset Concentration: 

### Concentration Breakdown
| Asset Class | Share of Market | Cumulative % |
|---|---|---|
| USDT (Tether) | 62.19% | 62.19% |
| BTC | 18.38% | 80.57% |
| USDC + ETH + XRP | 11.16% | 91.72% |
| Top 10 assets | 97.18% | 97.18% |
| Remaining 56 assets | 2.82% | 100.00% |

**The market is functionally a duopoly**: USDT and BTC together command **80.57% of all Brazilian crypto transaction volume**. The next closest competitor, USDC, captures only 4.22%—a 14.7x gap from the #1 player.

### Asset Diversification Paradox
While Receita Federal tracks 66 distinct cryptocurrencies, the distribution is dramatically skewed:
- **6 assets** have >1% market share
- **14 assets** occupy the 0.1-1% band
- **46 assets** comprise <0.1% each (averaging 0.06% market share)

The 56 smallest assets collectively represent only **2.82% of all transactions**, suggesting these serve niche use cases or function primarily as speculative instruments rather than payment infrastructure.

## 3. Stablecoin-Dominated Payment Infrastructure
Stablecoins account for **69.89% of Brazil's entire crypto transaction volume** (R\$ 932.1 billion), with the breakdown:

- **USDT **: R\$ 829.4 billion (62.19%) — 35.9 million transactions, avg R\$ 58,337
- **USDC**: R\$ 56.3 billion (4.22%) — 26.2 million transactions, avg R\$ 19,085
- **BRZ** (Brazilian stablecoin): R\$ 37.4 billion (2.80%) — 90.8 million transactions, avg R\$ 40,666
- **BUSD**: R\$ 8.6 billion (0.64%) — 187.6k transactions, avg R\$ 582,214

This concentration in dollar-pegged assets reflects **macroeconomic drivers specific to Latin America**: persistent inflation, BRL currency devaluation (the Real depreciated 40%+ from 2019-2025), capital controls, and remittance corridors. USDT serves as infrastructure for corporate dollar hedging and international B2B payments rather than speculation.[2][5][6][7][8]

## 4. Dual Transaction Size Markets: Institutional vs Retail
The data reveals a **bifurcated market structure** with distinct participant types operating at different scales:

### High-Value Institutional Transactions
- **BUSD**: R\$ 582,214 average (possible corporate treasury operations)
- **USDT**: R\$ 58,337 average (possible B2B payments, institutional)
- **BRZ**: R\$ 40,666 average (possible Brazilian corporate payments)
- **USDC**: R\$ 19,085 average (possible cross-border settlements)

These large average transaction sizes with relatively modest operation counts (187k-35M) suggest institutional actors—banks, fintech platforms, corporate treasuries—using crypto for genuine payment and hedging functions rather than trading.[2][9]

### Retail-Oriented Transactions
- **XRP**: R\$ 5,287 average (90.8M transactions)
- **ETH**: R\$ 1,050 average (51.8M transactions)
- **BTC **: R\$ 2,598 average (135M transactions)
- **XLM**: R\$ 341 average (5.2M transactions)

The massive operation counts with modest average sizes for BTC  and ETH  indicate retail investment/trading activity, while XRP 's pattern (high ops, mid-range transaction size) suggests remittance corridors.[5][6][7]

## 5. Market Concentration Implications
### Systemic Risk Concentration
The HHI of 4,258 and USDT 's 62% dominance create several vulnerabilities:

1. **Regulatory Shock Risk**: A regulatory action against Tether or domestic USDT distribution platforms could instantly collapse 62% of Brazilian transaction infrastructure[1][9]

2. **Operational Risk**: System failures at major Brazilian exchange operators (Mercado Bitcoin, Foxbit) would cascade through the concentrated market structure, affecting the disproportionate volume flowing through these platforms[2]

3. **Liquidity Concentration**: Large outflows from institutional actors could trigger cascading liquidations in the thin altcoin markets (which collectively represent only 2.8% of volume)[3][10]

### Market Maturity Signal
Conversely, the concentration reflects positive maturation signals:
- **Regulatory Compliance**: USDT , BTC , and USDC  (80.57% combined) are the three most-regulated, compliant cryptocurrencies globally
- **Institutional Adoption**: Large transaction sizes indicate Fortune 500 companies and major Brazilian banks may custody and transact crypto operationally[2][9]
- **Payment Infrastructure Replacement**: The 69.9% stablecoin share suggests crypto is displacing traditional remittance rails, SWIFT correspondent banking, and informal dollar markets in Brazilian commerce[5][6][7][8]

## 6. Detailed Market Share Rankings
The top 20 assets demonstrate the extreme concentration gradient:

| Rank | Asset | Volume (R\$) | Market Share | Operations |
|---|---|---|---|---|
| 1 | USDT | 829.4B | 62.19% | 35.9M |
| 2 | BTC | 245.1B | 18.38% | 134.9M |
| 3 | USDC | 56.3B | 4.22% | 26.2M |
| 4 | ETH | 51.9B | 3.89% | 51.8M |
| 5 | XRP | 40.5B | 3.04% | 16.1M |
| 6 | BRZ | 37.4B | 2.80% | 90.8M |
| 7-10 | SOL, CHZ, BUSD, LTC | 12.2B | 0.92% | 4.4M |
| 11-20 | LINK, XLM, ADA, BCH, DOGE, AAVE, MATIC, UNI, DCR, WBX | 8.5B | 0.64% | 7.2M |

Assets ranked 21-66 collectively hold **0.69% market share**, averaging R\$ 20.7 million each—minuscule in a R\$ 1.3 trillion market.

## 7. Cross-Analysis with Market Dynamics
### Regulatory Catalysts
The November 2025 BCB resolutions designating the Central Bank as crypto regulator and requiring foreign exchange registration by February 2026 will likely **increase concentration** further by consolidating around compliant major players. Smaller altcoins lacking regulatory sophistication may face practical trading limitations.[1][9]

### Macro-Economic Drivers
The persistent USDT dominance reflects the Brazilian macroeconomic environment:
- **BRL Depreciation**: The Brazilian Real weakened from ~1.80 BRL/USD (2019) to 5.5+ BRL/USD (2025)
- **Inflation Hedging**: IPCA inflation averaging 5-7% annually pushes capital into dollar-pegged assets[5][6]
- **Capital Flight Concerns**: Brazil's fiscal deficit and interest rate environment create demand for crypto-facilitated dollar transfer (though exchange controls limit formal options)[6][11]

### Institutional Market Share Growth
Data suggests institutional CNPJ participants' share of volume is increasing, with 2024-2025 showing larger average transaction sizes in USDT and BRZ stablecoins. This indicates successful integration into corporate treasury workflows.[2][9]

## Corrected Summary and Analytical Takeaways
### Key Findings
1. **USDT Duopoly Verified**: The R\$ 1.334 trillion market is genuinely dominated by a single asset (USDT at 62.19%), with no secondary competitor exceeding 18.4% share

2. **Stablecoin Infrastructure Dominance**: Nearly 70% of all transactions use stablecoins, confirming crypto's function as **payment infrastructure rather than investment vehicle** in Brazil

3. **Institutional-Retail Bifurcation**: Transaction size patterns reveal two distinct markets operating in parallel—institutional settlement (avg R\$ 40k-580k) and retail payments/trading (avg R\$ 300-5k)

4. **Long-Tail Irrelevance**: 56 altcoins share only 2.82% of volume despite comprising 85% of tracked assets, suggesting limited economic relevance outside niche use cases

5. **Market Maturity via Concentration**: The HHI of 4,258 and regulatory focus on top-3 assets (80.6%) reflects post-hype-cycle maturity where market participants have selected proven, compliant infrastructure


The corrected unit analysis demonstrates that **Brazil's crypto market is a highly concentrated, institutionalized payment and hedging system dominated by stablecoins**, not a diverse speculative trading venue as surface-level metrics might suggest.

References: 
[1](https://www.chainalysis.com/blog/brazil-crypto-asset-regulatory-framework-2025/)
[2](https://newsletter.brazilcrypto.io/p/210-brazil-crypto-volumes-at-319)
[3](https://forklog.com/en/what-the-herfindahl-hirschman-index-hhi-says-about-the-crypto-market/)
[4](https://www.investopedia.com/terms/h/hhi.asp)
[5](https://futswap.io/usdt-latin-america-stablecoins-business/)
[6](https://finance.yahoo.com/news/brazil-318b-crypto-boom-stablecoins-144257383.html)
[7](https://en.cryptonomist.ch/2025/03/13/adoption-of-stablecoin-in-latin-america-usdc-and-usdt-dominate-transactions-on-bitso-in-2024/)
[8](https://coingeek.com/latin-america-a-natural-vanguard-for-stablecoin-revolution/)
[9](https://www.ainvest.com/news/brazil-crypto-crackdown-strategic-opportunities-regulated-market-2511/)
[10](https://www.esma.europa.eu/sites/default/files/2024-04/ESMA50-524821-3153_risk_article_crypto_assets_market_structures_and_eu_relevance.pdf)
[11](https://finance.yahoo.com/news/brazil-considers-tax-crypto-cross-150223632.html)
    """)
    st.markdown("---")

# ============ TAB 1: OVERVIEW ============
with tab1:
    st.subheader(f"Main Metrics {get_title_suffix()}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_operacoes = filtered_op["valor_total"].sum()
        st.metric("Total Value", f"R$ {total_operacoes:,.0f}M")

    with col2:
        max_cpfs = filtered_users["cpfs_unicos"].max() if not filtered_users.empty else 0
        st.metric("Max Unique Individuals", f"{max_cpfs:,}")

    with col3:
        max_cnpjs = filtered_users["cnpjs_unicos"].max() if not filtered_users.empty else 0
        st.metric("Max Unique Companies", f"{max_cnpjs:,}")

    with col4:
        crypto_types = filtered_crypto["criptoativo"].nunique()
        st.metric("Cryptocurrencies", f"{crypto_types}")

    # Timeline chart
    st.subheader(f"Total Value Evolution Over Time {get_title_suffix()}")

    if filter_type != "Total Data":
        timeline_df = filtered_op.sort_values("data").groupby("data").agg({
            "valor_total": "sum"
        }).reset_index()

        if not timeline_df.empty:
            fig_timeline = px.line(
                timeline_df,
                x="data",
                y="valor_total",
                title=f"Total Operations Value {get_title_suffix()} (Millions R$)",
                labels={"data": "Month", "valor_total": "Value (Millions R$)"},
                markers=True,
                template="plotly_white"
            )
            fig_timeline.update_traces(hovertemplate="<b>%{x|%B}</b><br>R$ %{y:,.2f}M<extra></extra>")
            st.plotly_chart(fig_timeline, use_container_width=True)
        else:
            st.info(f"ℹ️ No data available for {filter_label}")
    else:
        col1, col2 = st.columns(2)
        with col1:
            total_val = filtered_op["valor_total"].sum()
            st.metric("Aggregated Total Value", f"R$ {total_val:,.0f}M")
        with col2:
            avg_val = filtered_op["valor_total"].mean() if len(filtered_op) > 0 else 0
            st.metric("Average Monthly Value", f"R$ {avg_val:,.0f}M")

    # Normalized Volume per User (New Analysis)
    if filter_type != "Total Data" and not filtered_merged.empty:
        st.subheader(f"Average Volume per Active User {get_title_suffix()}")

        fig_norm = px.line(
            filtered_merged,
            x="data",
            y="vol_per_user",
            title=f"Average Volume per Unique Individual/Company (R$)",
            labels={"data": "Month", "vol_per_user": "Average Value (R$)"},
            markers=True,
            template="plotly_white"
        )
        fig_norm.update_traces(line_color="#2ca02c", hovertemplate="<b>%{x|%B}</b><br>R$ %{y:,.2f}<extra></extra>")
        st.plotly_chart(fig_norm, use_container_width=True)

        with st.expander("ℹ️ About this metric"):
            st.write("""
            **Normalized Volume**: Represents the total transaction value divided by the total number of unique users (Individuals + Companies) in that month.
            This helps understand whether volume growth is driven by more users or by users transacting larger amounts (intensity).
            """)
    
    # Users and CNPJs timeline
    if filter_type != "Total Data":
        col1, col2 = st.columns(2)
        
        with col1:
            users_timeline = filtered_users.sort_values("data").groupby("data").agg({
                "cpfs_unicos": "sum"
            }).reset_index()
            
            if not users_timeline.empty:
                fig_users = px.area(
                    users_timeline,
                    x="data",
                    y="cpfs_unicos",
                    title=f"Unique Individuals (CPF) {get_title_suffix()}",
                    labels={"data": "Month", "cpfs_unicos": "Unique CPFs"},
                    template="plotly_white"
                )
                fig_users.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
                st.plotly_chart(fig_users, use_container_width=True)
        
        with col2:
            cnpjs_timeline = filtered_users.sort_values("data").groupby("data").agg({
                "cnpjs_unicos": "sum"
            }).reset_index()
            
            if not cnpjs_timeline.empty:
                fig_cnpjs = px.area(
                    cnpjs_timeline,
                    x="data",
                    y="cnpjs_unicos",
                    title=f"Unique Companies (CNPJ) {get_title_suffix()}",
                    labels={"data": "Month", "cnpjs_unicos": "Unique CNPJs"},
                    template="plotly_white",
                    color_discrete_sequence=["#FF6B6B"]
                )
                fig_cnpjs.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
                st.plotly_chart(fig_cnpjs, use_container_width=True)
    else:
        col1, col2 = st.columns(2)
        with col1:
            total_cpf = filtered_users["cpfs_unicos"].max()
            st.metric("Max Unique Individuals", f"{total_cpf:,}")
        with col2:
            total_cnpj = filtered_users["cnpjs_unicos"].max()
            st.metric("Max Unique Companies", f"{total_cnpj:,}")

# ============ TAB 2: OPERATIONS ============
with tab2:
    st.subheader(f"Operations Analysis by Type {get_title_suffix()}")
    
    if filter_type == "Total Data":
        # Show aggregated totals
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Individual - Foreign Total", f"R$ {filtered_op['valor_exterior_pf'].sum():,.0f}M")
        
        with col2:
            st.metric("Company - Foreign Total", f"R$ {filtered_op['valor_exterior_pj'].sum():,.0f}M")
        
        with col3:
            st.metric("Ind/Co - Domestic Total", f"R$ {filtered_op['valor_sem_ex_subtotal'].sum():,.0f}M")
        
        with col4:
            st.metric("Exchanges Total", f"R$ {filtered_op['valor_exchanges'].sum():,.0f}M")
    else:
        # Latest month breakdown
        if not filtered_op.empty:
            latest_month = filtered_op.sort_values("data").iloc[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Individual - Foreign",
                    f"R$ {latest_month['valor_exterior_pf']:,.0f}M"
                )
            
            with col2:
                st.metric(
                    "Company - Foreign",
                    f"R$ {latest_month['valor_exterior_pj']:,.0f}M"
                )
            
            with col3:
                st.metric(
                    "Ind/Co - Domestic",
                    f"R$ {latest_month['valor_sem_ex_subtotal']:,.0f}M"
                )
            
            with col4:
                st.metric(
                    "Exchanges",
                    f"R$ {latest_month['valor_exchanges']:,.0f}M"
                )
    
    # Stacked area chart (only for time-based filters)
    if filter_type != "Total Data":
        st.subheader("Operations Composition Throughout the Year")
        
        timeline_comp = filtered_op.sort_values("data").copy()
        
        if not timeline_comp.empty:
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp["valor_exterior_pf"],
                name="Individual - Foreign",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp["valor_exterior_pj"],
                name="Company - Foreign",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp["valor_sem_ex_subtotal"],
                name="Ind/Co - Domestic",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp["valor_exchanges"],
                name="Exchanges",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.update_layout(
                title=f"Operations Composition {get_title_suffix()}",
                xaxis_title="Month",
                yaxis_title="Value (Millions R$)",
                hovermode="x unified",
                template="plotly_white"
            )
            
            st.plotly_chart(fig_comp, use_container_width=True)
            
        # New Ratio Analysis
        st.markdown("---")
        st.subheader("Ratio Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # PF vs PJ Ratio Chart
            # We need to recalculate ratios for the filtered period
            # Since we can't easily filter the pre-calculated enriched df if it wasn't filtered above
            # Let's just calculate on the fly for the filtered_op
            
            ratio_df = filtered_op.copy()
            ratio_df["total_pf_known"] = ratio_df["valor_exterior_pf"] + ratio_df["valor_sem_ex_pf"]
            ratio_df["total_pj_known"] = ratio_df["valor_exterior_pj"] + ratio_df["valor_sem_ex_pj"]
            
            # Avoid division by zero
            total_known = ratio_df["total_pf_known"] + ratio_df["total_pj_known"]
            ratio_df["pct_pf"] = (ratio_df["total_pf_known"] / total_known) * 100
            ratio_df["pct_pj"] = (ratio_df["total_pj_known"] / total_known) * 100
            
            fig_ratio = go.Figure()
            fig_ratio.add_trace(go.Scatter(
                x=ratio_df["data"], y=ratio_df["pct_pf"],
                mode='lines', name='Individual', stackgroup='one',
                groupnorm='percent'
            ))
            fig_ratio.add_trace(go.Scatter(
                x=ratio_df["data"], y=ratio_df["pct_pj"],
                mode='lines', name='Company', stackgroup='one'
            ))
            
            fig_ratio.update_layout(
                title="Individual vs Company Ratio (Volume)",
                yaxis=dict(type='linear', range=[1, 100], ticksuffix='%'),
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig_ratio, use_container_width=True)
            
        with col2:
            # Domestic vs Foreign Ratio
            geo_df = filtered_op.copy()
            geo_df["pct_foreign"] = (geo_df["valor_exterior_subtotal"] / geo_df["valor_total"]) * 100
            geo_df["pct_domestic"] = 100 - geo_df["pct_foreign"]
            
            fig_geo = go.Figure()
            fig_geo.add_trace(go.Scatter(
                x=geo_df["data"], y=geo_df["pct_domestic"],
                mode='lines', name='Domestic/Exchange', stackgroup='one',
                groupnorm='percent', line=dict(color='#1f77b4')
            ))
            fig_geo.add_trace(go.Scatter(
                x=geo_df["data"], y=geo_df["pct_foreign"],
                mode='lines', name='Foreign/Cross-Border', stackgroup='one',
                line=dict(color='#ff7f0e')
            ))
            
            fig_geo.update_layout(
                title="Domestic vs Foreign (Volume)",
                yaxis=dict(type='linear', range=[1, 100], ticksuffix='%'),
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig_geo, use_container_width=True)
    
    # Detailed table
    st.subheader("Detailed Data")
    if not filtered_op.empty:
        display_df = filtered_op.sort_values("data", ascending=False).copy()
        display_df["mes_ano"] = display_df["data"].dt.strftime("%B")
        
        cols_to_show = ["mes_ano", "valor_exterior_pf", "valor_exterior_pj", 
                        "valor_sem_ex_subtotal", "valor_exchanges", "valor_total"]
        st.dataframe(
            display_df[cols_to_show],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"ℹ️ No data available for the selected period")

# ============ TAB 3: USERS ============
with tab3:
    st.subheader(f"User Analysis (Unique Individuals and Companies) {get_title_suffix()}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        cpfs_df = filtered_users.sort_values("data")
        if not cpfs_df.empty:
            fig_cpf = px.bar(
                cpfs_df,
                x="data",
                y="cpfs_unicos",
                title=f"Unique Individuals (CPF) {get_title_suffix()}",
                labels={"data": "Month", "cpfs_unicos": "Unique CPFs"},
                template="plotly_white"
            )
            fig_cpf.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
            st.plotly_chart(fig_cpf, use_container_width=True)
    
    with col2:
        cnpjs_df = filtered_users.sort_values("data")
        if not cnpjs_df.empty:
            fig_cnpj = px.bar(
                cnpjs_df,
                x="data",
                y="cnpjs_unicos",
                title=f"Unique Companies (CNPJ) {get_title_suffix()}",
                labels={"data": "Month", "cnpjs_unicos": "Unique CNPJs"},
                template="plotly_white",
                color_discrete_sequence=["#FF6B6B"]
            )
            fig_cnpj.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
            st.plotly_chart(fig_cnpj, use_container_width=True)
    
    # Ratio analysis
    st.subheader("Company/Individual Ratio")
    ratio_df = filtered_users.sort_values("data").copy()
    if not ratio_df.empty:
        ratio_df["ratio_pj_pf"] = ratio_df["cnpjs_unicos"] / (ratio_df["cpfs_unicos"] + 1)
        
        fig_ratio = px.line(
            ratio_df,
            x="data",
            y="ratio_pj_pf",
            title=f"Company/Individual Ratio Over Time {get_title_suffix()}",
            labels={"data": "Month", "ratio_pj_pf": "CNPJ/CPF Ratio"},
            markers=True,
            template="plotly_white"
        )
        st.plotly_chart(fig_ratio, use_container_width=True)
        
    # Growth Rate Analysis
    if filter_type != "Total Data" and not filtered_merged.empty:
        st.subheader("Monthly User Growth (MoM)")
        
        # Filter merged metrics again to match view if needed, but filtered_merged should be correct
        growth_df = filtered_merged.sort_values("data").copy()
        
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Bar(
            x=growth_df["data"],
            y=growth_df["cpf_growth_pct"],
            name="Individual Growth %",
            marker_color="#1f77b4"
        ))
        fig_growth.add_trace(go.Bar(
            x=growth_df["data"],
            y=growth_df["cnpj_growth_pct"],
            name="Company Growth %",
            marker_color="#FF6B6B"
        ))
        
        fig_growth.update_layout(
            title="Monthly Growth Rate (%)",
            yaxis_title="Growth (%)",
            barmode='group',
            template="plotly_white",
            hovermode="x unified"
        )
        st.plotly_chart(fig_growth, use_container_width=True)
    
    # Table
    st.subheader("Detailed Data")
    if not filtered_users.empty:
        display_users = filtered_users.sort_values("data", ascending=False).copy()
        display_users["mes_ano"] = display_users["data"].dt.strftime("%B")
        display_users["ratio"] = (display_users["cnpjs_unicos"] / 
                                  (display_users["cpfs_unicos"] + 1)).round(3)
        
        cols_to_show = ["mes_ano", "cpfs_unicos", "cnpjs_unicos", "ratio"]
        st.dataframe(
            display_users[cols_to_show],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"ℹ️ No data available for the selected period")

# ============ TAB 4: GENDER ============
with tab4:
    st.subheader(f"Gender Analysis in Operations {get_title_suffix()}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        gender_ops = filtered_gender.sort_values("data")
        
        if not gender_ops.empty:
            fig_ops = go.Figure()
            fig_ops.add_trace(go.Scatter(
                x=gender_ops["data"],
                y=gender_ops["perc_num_oper_feminino"],
                name="Female",
                mode="lines",
                fill="tozeroy",
                hovertemplate="<b>%{x|%B}</b><br>Female: %{y:.2f}%<extra></extra>"
            ))
            fig_ops.add_trace(go.Scatter(
                x=gender_ops["data"],
                y=gender_ops["perc_num_oper_masculino"],
                name="Male",
                mode="lines",
                fill="tonexty",
                hovertemplate="<b>%{x|%B}</b><br>Male: %{y:.2f}%<extra></extra>"
            ))
            
            fig_ops.update_layout(
                title=f"Percentage of Operations by Gender {get_title_suffix()}",
                xaxis_title="Month",
                yaxis_title="Percentage (%)",
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig_ops, use_container_width=True)
    
    with col2:
        gender_val = filtered_gender.sort_values("data")
        
        if not gender_val.empty:
            fig_val = go.Figure()
            fig_val.add_trace(go.Scatter(
                x=gender_val["data"],
                y=gender_val["perc_valor_oper_feminino"],
                name="Female",
                mode="lines",
                fill="tozeroy",
                hovertemplate="<b>%{x|%B}</b><br>Female: %{y:.2f}%<extra></extra>"
            ))
            fig_val.add_trace(go.Scatter(
                x=gender_val["data"],
                y=gender_val["perc_valor_oper_masculino"],
                name="Male",
                mode="lines",
                fill="tonexty",
                hovertemplate="<b>%{x|%B}</b><br>Male: %{y:.2f}%<extra></extra>"
            ))
            
            fig_val.update_layout(
                title=f"Percentage of Operation Value by Gender {get_title_suffix()}",
                xaxis_title="Month",
                yaxis_title="Percentage (%)",
                hovermode="x unified",
                template="plotly_white"
            )
            st.plotly_chart(fig_val, use_container_width=True)
    
    # Latest month snapshot
    if not filtered_gender.empty:
        latest = filtered_gender.sort_values("data").iloc[-1]
        st.subheader("Latest Period")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("% Female Ops.", f"{latest['perc_num_oper_feminino']:.1f}%")
        
        with col2:
            st.metric("% Male Ops.", f"{latest['perc_num_oper_masculino']:.1f}%")
        
        with col3:
            st.metric("% Female Value", f"{latest['perc_valor_oper_feminino']:.1f}%")
        
        with col4:
            st.metric("% Male Value", f"{latest['perc_valor_oper_masculino']:.1f}%")
    else:
        st.info(f"ℹ️ No data available for the selected period")
    
    # Detailed table
    st.subheader("Detailed Data")
    if not filtered_gender.empty:
        display_gender = filtered_gender.sort_values("data", ascending=False).copy()
        display_gender["mes_ano"] = display_gender["data"].dt.strftime("%B")
        
        cols_to_show = ["mes_ano", "perc_num_oper_feminino", "perc_num_oper_masculino",
                        "perc_valor_oper_feminino", "perc_valor_oper_masculino"]
        st.dataframe(
            display_gender[cols_to_show],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(f"ℹ️ No data available for the selected period")

# ============ TAB 5: CRYPTOCURRENCIES ============
with tab5:
    st.subheader(f"Cryptocurrency Analysis {get_title_suffix()}")
    
    if not filtered_crypto.empty:
        # Top cryptocurrencies filter
        top_n = st.slider("Show top N cryptocurrencies", 5, 30, 10)
        
        # Get top cryptocurrencies by total value
        top_crypto = (
            filtered_crypto.groupby("criptoativo")["valor_total_operacoes"]
            .sum()
            .nlargest(top_n)
            .index.tolist()
        )
        
        filtered_top = filtered_crypto[filtered_crypto["criptoativo"].isin(top_crypto)]
        
        # Top cryptocurrencies by value
        col1, col2 = st.columns(2)
        
        with col1:
            top_by_value = (
                filtered_crypto.groupby("criptoativo")["valor_total_operacoes"]
                .sum()
                .nlargest(10)
                .reset_index()
                .sort_values("valor_total_operacoes")
            )
            
            if not top_by_value.empty:
                fig_top_value = px.bar(
                    top_by_value,
                    x="valor_total_operacoes",
                    y="criptoativo",
                    orientation="h",
                    title=f"Top 10 Cryptocurrencies by Total Value {get_title_suffix()}",
                    labels={"valor_total_operacoes": "Total Value (R$)", "criptoativo": "Cryptocurrency"},
                    template="plotly_white"
                )
                fig_top_value.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
                st.plotly_chart(fig_top_value, use_container_width=True)
        
        with col2:
            top_by_ops = (
                filtered_crypto.groupby("criptoativo")["num_operacoes"]
                .sum()
                .nlargest(10)
                .reset_index()
                .sort_values("num_operacoes")
            )
            
            if not top_by_ops.empty:
                fig_top_ops = px.bar(
                    top_by_ops,
                    x="num_operacoes",
                    y="criptoativo",
                    orientation="h",
                    title=f"Top 10 Cryptocurrencies by Number of Operations {get_title_suffix()}",
                    labels={"num_operacoes": "Number of Operations", "criptoativo": "Cryptocurrency"},
                    template="plotly_white",
                    color_discrete_sequence=["#FF6B6B"]
                )
                fig_top_ops.update_traces(hovertemplate="<b>%{y}</b><br>%{x:,}<extra></extra>")
                st.plotly_chart(fig_top_ops, use_container_width=True)
        
        # Cryptocurrencies timeline
        st.subheader("Top Cryptocurrencies Evolution")
        
        crypto_timeline = (
            filtered_top.sort_values("data")
            .groupby(["data", "criptoativo"])["valor_total_operacoes"]
            .sum()
            .reset_index()
        )
        
        if not crypto_timeline.empty:
            fig_crypto_line = px.line(
                crypto_timeline,
                x="data",
                y="valor_total_operacoes",
                color="criptoativo",
                title=f"Evolution of Top {top_n} Cryptocurrencies {get_title_suffix()}",
                labels={"data": "Month", "valor_total_operacoes": "Total Value", "criptoativo": "Cryptocurrency"},
                template="plotly_white",
                markers=True
            )
            fig_crypto_line.update_traces(hovertemplate="<b>%{x|%B}</b><br>R$ %{y:,.2f}<extra></extra>")
            st.plotly_chart(fig_crypto_line, use_container_width=True)
        
        # Average value per operation
        st.subheader("Average Value per Operation")
        
        avg_value = (
            filtered_crypto.groupby("criptoativo")["valor_medio_operacao"]
            .mean()
            .nlargest(10)
            .reset_index()
            .sort_values("valor_medio_operacao")
        )
        
        if not avg_value.empty:
            fig_avg = px.bar(
                avg_value,
                x="valor_medio_operacao",
                y="criptoativo",
                orientation="h",
                title=f"Top 10 Cryptocurrencies by Average Operation Value {get_title_suffix()}",
                labels={"valor_medio_operacao": "Average Value (R$)", "criptoativo": "Cryptocurrency"},
                template="plotly_white",
                color_discrete_sequence=["#2ca02c"]
            )
            fig_avg.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
            st.plotly_chart(fig_avg, use_container_width=True)
        
        # Market dominance (treemap)
        st.subheader("Market Dominance (Top 30)")
        
        dominance = (
            filtered_crypto.groupby("criptoativo")["valor_total_operacoes"]
            .sum()
            .nlargest(30)
            .reset_index()
        )
        
        if not dominance.empty:
            fig_tree = px.treemap(
                dominance,
                path=["criptoativo"],
                values="valor_total_operacoes",
                title=f"Market Share - Top 30 Cryptocurrencies {get_title_suffix()}",
                template="plotly_white"
            )
            fig_tree.update_traces(
                hovertemplate="<b>%{label}</b><br>R$ %{value:,.2f}<extra></extra>",
                textinfo="label+percent parent"
            )
            st.plotly_chart(fig_tree, use_container_width=True)
        
        # Volume vs Average Ticket
        st.subheader("Total Volume vs Average Ticket (Top 50)")
        
        scatter_data = (
            filtered_crypto.groupby("criptoativo")
            .agg({
                "valor_total_operacoes": "sum",
                "valor_medio_operacao": "mean",
                "num_operacoes": "sum"
            })
            .nlargest(50, "valor_total_operacoes")
            .reset_index()
        )
        
        if not scatter_data.empty:
            fig_scatter = px.scatter(
                scatter_data,
                x="valor_total_operacoes",
                y="valor_medio_operacao",
                size="num_operacoes",
                hover_name="criptoativo",
                title=f"Volume vs Average Ticket - Top 50 Cryptocurrencies {get_title_suffix()}",
                labels={
                    "valor_total_operacoes": "Total Volume (R$)",
                    "valor_medio_operacao": "Average Ticket (R$)",
                    "num_operacoes": "Number of Operations"
                },
                template="plotly_white",
                log_x=True,
                log_y=True
            )
            fig_scatter.update_traces(
                hovertemplate="<b>%{hovertext}</b><br>Volume: R$ %{x:,.2f}<br>Avg Ticket: R$ %{y:,.2f}<extra></extra>"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Detailed table
        st.subheader("Detailed Cryptocurrency Data")
        
        detailed_crypto = (
            filtered_crypto.groupby("criptoativo")
            .agg({
                "valor_total_operacoes": "sum",
                "num_operacoes": "sum",
                "valor_medio_operacao": "mean"
            })
            .sort_values("valor_total_operacoes", ascending=False)
            .reset_index()
        )
        
        if not detailed_crypto.empty:
            st.dataframe(
                detailed_crypto,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "criptoativo": "Cryptocurrency",
                    "valor_total_operacoes": "Total Value (R$)",
                    "num_operacoes": "Number of Operations",
                    "valor_medio_operacao": "Average Value (R$)"
                }
            )
    else:
        st.info(f"ℹ️ No data available for the selected period")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #999; font-size: 12px;'>
    💡 Created by <a href='https://www.linkedin.com/in/patricksilveira/' target='_blank'>Patrick Silveira</a>.
    </div>
""", unsafe_allow_html=True)

# Force reload comment
