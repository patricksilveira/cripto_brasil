import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from datetime import datetime
from utils import get_usd_rates, normalize_dataframe

from theme import apply_shadcn_theme, get_custom_css


# Page config
st.set_page_config(
    page_title="CryptoBrazil Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS styling
# CSS styling
st.markdown(get_custom_css(), unsafe_allow_html=True)

# Helper function to update chart fonts
# Helper function to update chart fonts - DEPRECATED / REPLACED BY THEME
# But we remove the definition to clean up.


# Load data
@st.cache_data
def load_data():
    base_path = Path(__file__).parent / "saida_csv"
    
    # Load raw data
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
    
    # Normalize to USD
    try:
        rates = get_usd_rates(base_path)
        if not rates.empty:
            # 1. Normalize Operacoes
            ops_cols = [
                "valor_total", "valor_exterior_pf", "valor_exterior_pj", 
                "valor_sem_ex_subtotal", "valor_exchanges", "valor_exterior_subtotal",
                "valor_sem_ex_pf", "valor_sem_ex_pj"
            ]
            data["operacoes"] = normalize_dataframe(data["operacoes"], ops_cols, rates)
            
            # 2. Normalize Criptoativos
            crypto_cols = ["valor_total_operacoes", "valor_medio_operacao"]
            data["criptoativos"] = normalize_dataframe(data["criptoativos"], crypto_cols, rates)
            
            # Store rates for visualization
            data["rates"] = rates
    except Exception as e:
        st.error(f"Error normalizing data to USD: {e}")
    
    return process_data(data)

def process_data(data):
    # 1. Merge Operations and Users for normalized metrics
    # We need to aggregate operations by date first to match users granularity
    
    # Base cols to aggregate
    agg_dict = {
        "valor_total": "sum",
        "valor_exterior_pf": "sum",
        "valor_exterior_pj": "sum",
        "valor_sem_ex_subtotal": "sum",
        "valor_exchanges": "sum"
    }
    
    # Check if USD cols exist and add them to aggregation
    if "valor_total_usd" in data["operacoes"].columns:
        usd_agg = {
            "valor_total_usd": "sum",
            "valor_exterior_pf_usd": "sum",
            "valor_exterior_pj_usd": "sum",
            "valor_sem_ex_subtotal_usd": "sum",
            "valor_exchanges_usd": "sum"
        }
        agg_dict.update(usd_agg)
        
    ops_monthly = data["operacoes"].groupby("data").agg(agg_dict).reset_index()
    
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
    
    if "valor_total_usd" in merged_metrics.columns:
        merged_metrics["vol_per_user_usd"] = merged_metrics["valor_total_usd"] * 1_000_000 / merged_metrics["total_users"]

    # 2. Calculate Ratios in Operations Data
    ops_df = data["operacoes"].copy()
    
    # Calculate Total PF and PJ
    ops_df["total_pf_known"] = ops_df["valor_exterior_pf"] + ops_df["valor_sem_ex_pf"]
    ops_df["total_pj_known"] = ops_df["valor_exterior_pj"] + ops_df["valor_sem_ex_pj"]
    
    if "valor_exterior_pf_usd" in ops_df.columns:
        ops_df["total_pf_known_usd"] = ops_df["valor_exterior_pf_usd"] + ops_df["valor_sem_ex_pf_usd"]
        ops_df["total_pj_known_usd"] = ops_df["valor_exterior_pj_usd"] + ops_df["valor_sem_ex_pj_usd"]
    
    # Calculate ratios for known segments (Use BRL cols as ratios are same)
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
st.sidebar.markdown("## ⚙️ Configuration")
currency = st.sidebar.radio("Currency / Moeda:", ["BRL", "USD"], index=0)
currency_suffix = "_usd" if currency == "USD" else ""
currency_symbol = "US$" if currency == "USD" else "R$"

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
    options=["By Year", "Date Range", "All Period"],
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

# Main header with logo
st.image('dashboard_criptobrasil_logo.png', width=250)
st.markdown('<p class="header">📊 CryptoBrazil Dashboard</p>', unsafe_allow_html=True)
st.markdown(f"*Filter: **{filter_label}** | Last updated: {datetime.now().strftime('%m/%d/%Y at %H:%M')}*")

# ============ TABS ============
tab_intro, tab1, tab3, tab4, tab5 = st.tabs([
    "Introduction", "Overview", "Users", "Gender", "Cryptocurrencies"
])

# Helper function to create title based on filter type
def get_title_suffix():
    if filter_type == "By Year":
        return f"- {int(filtered_op['ano'].unique()[0]) if not filtered_op.empty and filtered_op['ano'].unique()[0] > 0 else 'Selected Period'}"
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
    <strong>Data Analysis:</strong> Produced by <a href="https://pplx.ai/patrickds3872" target="_blank">Perplexity AI</a> in January 2026 <br>
    <strong>Official Data Sources:</strong> 
    <a href="https://www.gov.br/receitafederal/pt-br/assuntos/orientacao-tributaria/declaracoes-e-demonstrativos/criptoativos" target="_blank">Receita Federal - Crypto Assets</a>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
# 📊 Updated State of the Crypto Market in Brazil: 2025 Official Report

### 🚀 TL;DR
The Brazilian market has undergone a structural transformation. In 2023 and early 2024, the market was "inflated" by millions of micro-transactions (likely betting-related). Since the 2024/2025 regulatory purge, the number of operations has dropped, but the **Value per Transaction** has surged, indicating that the remaining base is more professional and high-value.

## 1. Growth & CAGR (2019–2025)
*   **Total Historical Volume**: R$ 1.55 Trillion.
*   **Past 12 Months Volume**: R$ 464.1 Billion (Approx. 30% of all-time volume).
*   **CAGR**: 33.6%.
*   **Trend**: The market is "trimming the fat." We are seeing fewer but larger operations compared to the chaotic 2023 period.

## 2. Market Share (Excluding BUSD)
**Brazil is now a Stablecoin-First economy.**
*   **USDT**: 82.5% share (Last 12 months).
*   **BTC**: 7.2%.
*   **ETH**: 2.7%.

*Insight*: USDT is the "Digital Rail" for the Brazilian economy. BTC and ETH have evolved into "Digital Gold," while USDT provides the daily liquidity.

## 3. The "BET Regulation" Purge
*   **CNPJ Peak**: 421,416 (Feb 2024).
*   **Current CNPJs**: 92,132 (Sep 2025) — **A 78% drop**.
*   **Impact on Ticket Size**: As the millions of betting micro-transactions disappeared, the **Average USDT Ticket jumped from R$ 3,693 (Jan) to over R$ 13,300 (Sep)**. This proves the market is now dominated by "Real" business and institutional volume.

## 4. User Profiles (2025 Averages)
*   **CPFs (Retail)**: 4.6 Million average monthly users. Retail is holding steady, using crypto for long-term savings and small transfers.
*   **CNPJs (Corporate)**: 90,054 average monthly entities. This group moves ~65% of the total value, focusing heavily on USDT for B2B settlements.

## 5. Why Brazil is Peculiar (Global Context)
*   **The "Purified" Market**: Unlike other markets where "wash trading" or gambling obscures data, Brazil's rapid regulatory response to BETs has "cleaned" the data. The current R$ 464B annual volume is high-quality, professional liquidity.
*   **Hyper-Velocity**: The integration with PIX means the Velocity of Money in the Brazilian crypto ecosystem is likely among the highest in the world.

### 📈 Summary Table (Sep 2025 Data)

| Metric | Value | 12-Month Trend |
| :--- | :--- | :--- |
| **Monthly Volume** | R$ 35.5 Billion | 📈 Growing Intensity |
| **USDT Ticket Size** | R$ 13,304 | 🚀 Significant Increase |
| **BTC Ticket Size** | R$ 1,142 | 📉 Retail Saturation |
| **Active Entities** | ~1 Million | ⚖️ Stabilizing |

**Conclusion**: The "Betting-Inflation" era is over. Brazil has entered the **Institutional Era**, where USDT is used as a functional currency for business, and the retail base is one of the most consistent and tax-compliant in the world.
    """)
    st.markdown("---")

# ============ TAB 1: OVERVIEW ============
with tab1:
    st.subheader(f"Main Metrics {get_title_suffix()}")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_operacoes = filtered_op[f"valor_total{currency_suffix}"].sum()
        st.metric("Total Value", f"{currency_symbol} {total_operacoes:,.0f}M")

    with col2:
        max_cpfs = filtered_users["cpfs_unicos"].max() if not filtered_users.empty else 0
        st.metric("Max Unique Individuals", f"{max_cpfs:,}")

    with col3:
        max_cnpjs = filtered_users["cnpjs_unicos"].max() if not filtered_users.empty else 0
        st.metric("Max Unique Companies", f"{max_cnpjs:,}")

    with col4:
        crypto_types = filtered_crypto["criptoativo"].nunique()
        st.metric("Cryptocurrencies", f"{crypto_types}")

    # Operations breakdown metrics
    st.markdown("---")
    st.subheader(f"Operations Breakdown {get_title_suffix()}")
    
    if not filtered_op.empty:
        # Calculate totals for the entire period
        total_pf_foreign = filtered_op[f'valor_exterior_pf{currency_suffix}'].sum()
        total_pj_foreign = filtered_op[f'valor_exterior_pj{currency_suffix}'].sum()
        total_domestic = filtered_op[f'valor_sem_ex_subtotal{currency_suffix}'].sum()
        total_exchanges = filtered_op[f'valor_exchanges{currency_suffix}'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Individual - Foreign",
                f"{currency_symbol} {total_pf_foreign:,.0f}M"
            )
        
        with col2:
            st.metric(
                "Company - Foreign",
                f"{currency_symbol} {total_pj_foreign:,.0f}M"
            )
        
        with col3:
            st.metric(
                "Ind/Co - Domestic",
                f"{currency_symbol} {total_domestic:,.0f}M"
            )
        
        with col4:
            st.metric(
                "Exchanges",
                f"{currency_symbol} {total_exchanges:,.0f}M"
            )

    # 1st Row: Total Operations Data (3 columns)
    st.markdown("---")
    st.subheader(f"Total Operations Data {get_title_suffix()}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Adoption Chart: Volume vs Users Overlay
        adoption_df = filtered_merged.sort_values("data")

        if not adoption_df.empty:
            fig_adoption = go.Figure()
            
            # Trace 1: Volume (Area)
            vol_col = f"valor_total{currency_suffix}" # normalized or BRL
            fig_adoption.add_trace(go.Scatter(
                x=adoption_df["data"],
                y=adoption_df[vol_col],
                name=f"Volume ({currency_symbol})",
                mode="lines",
                fill="tozeroy",
                line=dict(width=2),
                hovertemplate=f"<b>%{{x|%B %Y}}</b><br>Volume: {currency_symbol} %{{y:,.2f}}M<extra></extra>"
            ))
            
            fig_adoption.update_layout(
                title=f"Total Operations Value Timeline {get_title_suffix()}",
                xaxis_title="Month",
                yaxis_title=f"Value (Millions {currency_symbol})",
                template="plotly_white",
                hovermode="x unified"
            )
            
            fig_adoption = apply_shadcn_theme(fig_adoption)
            st.plotly_chart(fig_adoption, width="stretch", key="overview_adoption")
        else:
            st.info(f"ℹ️ No data available for {filter_label}")
    
    with col2:
        # Operations Composition Chart
        timeline_comp = filtered_op.sort_values("data").copy()
        
        if not timeline_comp.empty:
            fig_comp = go.Figure()
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp[f"valor_exterior_pf{currency_suffix}"],
                name="Individual - Foreign",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp[f"valor_exterior_pj{currency_suffix}"],
                name="Company - Foreign",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp[f"valor_sem_ex_subtotal{currency_suffix}"],
                name="Ind/Co - Domestic",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.add_trace(go.Scatter(
                x=timeline_comp["data"],
                y=timeline_comp[f"valor_exchanges{currency_suffix}"],
                name="Exchanges",
                mode="lines",
                stackgroup="one"
            ))
            
            fig_comp.update_layout(
                title=f"Operations Composition",
                xaxis_title="Month",
                yaxis_title=f"Value (Millions {currency_symbol})",
                hovermode="x unified",
                template="plotly_white"
            )
            fig_comp = apply_shadcn_theme(fig_comp)
            
            st.plotly_chart(fig_comp, width="stretch", key="overview_comp")
    
    with col3:
        # Domestic vs Foreign Volume Chart
        if not filtered_op.empty:
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
                title="Domestic vs Foreign Ratio",
                yaxis=dict(type='linear', range=[1, 100], ticksuffix='%'),
                hovermode="x unified",
                template="plotly_white"
            )
            fig_geo = apply_shadcn_theme(fig_geo)
            st.plotly_chart(fig_geo, width="stretch", key="overview_geo")

    # Exchange Rate & Volume Comparison
    st.markdown("---")
    st.subheader(f"Exchange Rate & Volume Comparison {get_title_suffix()}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # FX Rate Chart
        if "rates" in data and not data["rates"].empty:
            rates_df = data["rates"].copy()
            
            # Filter based on current selection if possible
            # We can use the start_date and end_date from filter logic if available, 
            # or just filter by the same range as filtered_op to keep it consistent.
            if not filtered_op.empty:
                min_op_date = filtered_op["data"].min()
                max_op_date = filtered_op["data"].max()
                rates_df = rates_df[(rates_df["data"] >= min_op_date) & 
                                    (rates_df["data"] <= max_op_date)]
            
            if not rates_df.empty:
                fig_fx = px.line(
                    rates_df,
                    x="data",
                    y="rate",
                    title="Monthly Average USD/BRL Exchange Rate",
                    labels={"data": "Month", "rate": "Rate (R$)"},
                    markers=True,
                    template="plotly_white"
                )
                fig_fx.update_traces(hovertemplate="<b>%{x|%B %Y}</b><br>R$ %{y:,.4f}<extra></extra>")
                fig_fx = apply_shadcn_theme(fig_fx)
                st.plotly_chart(fig_fx, width="stretch", key="overview_fx")
            else:
                st.info("No exchange rate data for the selected period.")
        else:
            st.info("Exchange rate data is not available.")
            
    with col2:
        # Volume Comparison (BRL vs USD)
        if not filtered_op.empty and "valor_total_usd" in data["operacoes"].columns:
            # We need to aggregate both BRL and USD values by date from the main df 
            # (or use filtered_op if it has the usd column, which it should if we updated load_data correctly)
            
            # Check if filtered_op has the USD column. 
            # In process_data, we enrich ops_enriched but filtered_op is slice of data["operacoes"] 
            # so it should have the normalized columns if they were added inplace or if filtered_op is taken from updated df.
            # Let's verify: In dashboard.py line 301/334/348, filtered_op = data["operacoes"][...]
            # data["operacoes"] was updated in load_data with normalize_dataframe which ADDS columns. 
            # So filtered_op HAS 'valor_total' and 'valor_total_usd'.
            
            comp_df = filtered_op.groupby("data").agg({
                "valor_total": "sum",
                "valor_total_usd": "sum"
            }).reset_index()
            
            if not comp_df.empty:
                fig_vol_comp = go.Figure()
                
                # BRL Bar (Left Axis)
                fig_vol_comp.add_trace(go.Bar(
                    x=comp_df["data"],
                    y=comp_df["valor_total"],
                    name="Volume (BRL)",
                    marker_color="#1f77b4",
                    yaxis="y"
                ))
                
                # USD Line (Right Axis)
                fig_vol_comp.add_trace(go.Scatter(
                    x=comp_df["data"],
                    y=comp_df["valor_total_usd"],
                    name="Volume (USD)",
                    marker_color="#2ca02c",
                    mode="lines+markers",
                    yaxis="y2"
                ))
                
                fig_vol_comp.update_layout(
                    title="Total Volume: Real (BRL) vs Dollar (USD)",
                    xaxis_title="Month",
                    yaxis=dict(
                        title="Volume (Millions R$)",
                        title_font=dict(color="#1f77b4"),
                        tickfont=dict(color="#1f77b4")
                    ),
                    yaxis2=dict(
                        title="Volume (Millions US$)",
                        title_font=dict(color="#2ca02c"),
                        tickfont=dict(color="#2ca02c"),
                        overlaying="y",
                        side="right"
                    ),
                    hovermode="x unified",
                    template="plotly_white",
                    legend=dict(x=0, y=-0.2, orientation="h")
                )
                fig_vol_comp = apply_shadcn_theme(fig_vol_comp)
                st.plotly_chart(fig_vol_comp, width="stretch", key="overview_vol_comp")
        else:
            st.info("Volume comparison data not available.")


    # Seasonality Analysis (Heatmap)
    st.markdown("---")
    st.subheader(f"Seasonality Analysis {get_title_suffix()}")
    
    if not filtered_op.empty:
        heatmap_data = filtered_op.copy()
        heatmap_data["Year"] = heatmap_data["data"].dt.year
        # heatmap_data["Month"] = heatmap_data["data"].dt.month_name() # Requires proper locale or just use English
        # Safe way for month names
        heatmap_data["Month_Num"] = heatmap_data["data"].dt.month
        
        # Pivot for heatmap: Month x Year
        heatmap_pivot = heatmap_data.pivot_table(
            index="Month_Num", 
            columns="Year", 
            values=f"valor_total{currency_suffix}", 
            aggfunc="sum"
        ).fillna(0)
        
        # Sort by Month Num then replace index with names
        month_names = {i: datetime(2000, i, 1).strftime('%B') for i in range(1, 13)}
        heatmap_pivot.index = heatmap_pivot.index.map(month_names)
        
        # Create Heatmap
        fig_heatmap = px.imshow(
            heatmap_pivot,
            labels=dict(x="Year", y="Month", color=f"Volume ({currency_symbol})"),
            x=heatmap_pivot.columns,
            y=heatmap_pivot.index,
            color_continuous_scale="Blues", # Clean blue scale fitting the theme
            aspect="auto",
            title="Monthly Volume Intensity"
        )
        
        fig_heatmap.update_traces(
            hovertemplate="<b>%{y} %{x}</b><br>Volume: " + currency_symbol + " %{z:,.2f}M<extra></extra>"
        )
        
        fig_heatmap = apply_shadcn_theme(fig_heatmap)
        st.plotly_chart(fig_heatmap, width="stretch", key="overview_heatmap")
    else:
        st.info("No data available for heatmap analysis.")

    # User Analytics Section
    st.markdown("---")
    st.subheader(f"User Analytics {get_title_suffix()}")
    
    # 2nd Row: Individuals Analytics (3 columns)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Statistical Data for Individuals
        st.markdown("**📊 Individuals Statistics**")
        
        if not filtered_op.empty and not filtered_users.empty:
            # Total Volume
            total_pf_volume = filtered_op[f"valor_exterior_pf{currency_suffix}"].sum() + filtered_op[f"valor_sem_ex_pf{currency_suffix}"].sum()
            
            # Average transaction for the period
            total_cpfs = filtered_users["cpfs_unicos"].sum()
            avg_transaction_period = (total_pf_volume * 1_000_000) / total_cpfs if total_cpfs > 0 else 0
            
            # Max and Min number of individuals
            max_cpfs = filtered_users["cpfs_unicos"].max()
            min_cpfs = filtered_users["cpfs_unicos"].min()
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(
                    "Avg Transaction (Period)",
                    f"{currency_symbol} {avg_transaction_period:,.2f}"
                )
                st.metric(
                    "Max Individuals",
                    f"{max_cpfs:,}"
                )
            with col_b:
                st.metric(
                    "Total Volume",
                    f"{currency_symbol} {total_pf_volume:,.0f}M"
                )
                st.metric(
                    "Min Individuals",
                    f"{min_cpfs:,}"
                )
    
    with col2:
        # Unique Individuals (CPF) Chart
        users_timeline = filtered_users.sort_values("data").groupby("data").agg({
            "cpfs_unicos": "sum"
        }).reset_index()
        
        if not users_timeline.empty:
            fig_users = px.area(
                users_timeline,
                x="data",
                y="cpfs_unicos",
                title=f"Unique Individuals (CPF)",
                labels={"data": "Month", "cpfs_unicos": "Unique CPFs"},
                template="plotly_white"
            )
            fig_users.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
            fig_users = apply_shadcn_theme(fig_users)
            st.plotly_chart(fig_users, width="stretch", key="overview_users")
    
    with col3:
        # Average Transaction per Individual
        if not filtered_op.empty and not filtered_users.empty:
            # Calculate average transaction per CPF
            avg_per_cpf_df = filtered_op.merge(
                filtered_users[["data", "cpfs_unicos"]], 
                on="data", 
                how="left"
            )
            avg_per_cpf_df["total_pf_volume"] = avg_per_cpf_df[f"valor_exterior_pf{currency_suffix}"] + avg_per_cpf_df[f"valor_sem_ex_pf{currency_suffix}"]
            # Convert from millions to actual R$ values
            avg_per_cpf_df["avg_per_cpf"] = (avg_per_cpf_df["total_pf_volume"] * 1_000_000) / avg_per_cpf_df["cpfs_unicos"]
            avg_per_cpf_df = avg_per_cpf_df.sort_values("data")
            
            fig_avg_cpf = px.line(
                avg_per_cpf_df,
                x="data",
                y="avg_per_cpf",
                title="Avg Transaction per Individual",
                labels={"data": "Month", "avg_per_cpf": f"Average ({currency_symbol})"},
                markers=True,
                template="plotly_white"
            )
            fig_avg_cpf.update_traces(line_color="#1f77b4", hovertemplate=f"<b>%{{x|%B}}</b><br>{currency_symbol} %{{y:,.2f}}<extra></extra>")
            fig_avg_cpf = apply_shadcn_theme(fig_avg_cpf)
            st.plotly_chart(fig_avg_cpf, width="stretch", key="overview_avg_cpf")
    
    # 3rd Row: Companies Analytics (3 columns)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Statistical Data for Companies
        st.markdown("**🏢 Companies Statistics**")
        
        if not filtered_op.empty and not filtered_users.empty:
            # Total Volume
            total_pj_volume = filtered_op[f"valor_exterior_pj{currency_suffix}"].sum() + filtered_op[f"valor_sem_ex_pj{currency_suffix}"].sum()
            
            # Average transaction for the period
            total_cnpjs = filtered_users["cnpjs_unicos"].sum()
            avg_transaction_period_pj = (total_pj_volume * 1_000_000) / total_cnpjs if total_cnpjs > 0 else 0
            
            # Max and Min number of companies
            max_cnpjs = filtered_users["cnpjs_unicos"].max()
            min_cnpjs = filtered_users["cnpjs_unicos"].min()
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(
                    "Avg Transaction (Period)",
                    f"{currency_symbol} {avg_transaction_period_pj:,.2f}"
                )
                st.metric(
                    "Max Companies",
                    f"{max_cnpjs:,}"
                )
            with col_b:
                st.metric(
                    "Total Volume",
                    f"{currency_symbol} {total_pj_volume:,.0f}M"
                )
                st.metric(
                    "Min Companies",
                    f"{min_cnpjs:,}"
                )
    
    with col2:
        # Unique Companies (CNPJ) Chart
        cnpjs_timeline = filtered_users.sort_values("data").groupby("data").agg({
            "cnpjs_unicos": "sum"
        }).reset_index()
        
        if not cnpjs_timeline.empty:
            fig_cnpjs = px.area(
                cnpjs_timeline,
                x="data",
                y="cnpjs_unicos",
                title=f"Unique Companies (CNPJ)",
                labels={"data": "Month", "cnpjs_unicos": "Unique CNPJs"},
                template="plotly_white",
                color_discrete_sequence=["#FF6B6B"]
            )
            fig_cnpjs.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
            fig_cnpjs = apply_shadcn_theme(fig_cnpjs)
            st.plotly_chart(fig_cnpjs, width="stretch", key="overview_cnpjs")
    
    with col3:
        # Average Transaction per Company
        if not filtered_op.empty and not filtered_users.empty:
            # Calculate average transaction per CNPJ
            avg_per_cnpj_df = filtered_op.merge(
                filtered_users[["data", "cnpjs_unicos"]], 
                on="data", 
                how="left"
            )
            avg_per_cnpj_df["total_pj_volume"] = avg_per_cnpj_df[f"valor_exterior_pj{currency_suffix}"] + avg_per_cnpj_df[f"valor_sem_ex_pj{currency_suffix}"]
            # Convert from millions to actual R$ values
            avg_per_cnpj_df["avg_per_cnpj"] = (avg_per_cnpj_df["total_pj_volume"] * 1_000_000) / avg_per_cnpj_df["cnpjs_unicos"]
            avg_per_cnpj_df = avg_per_cnpj_df.sort_values("data")
            
            fig_avg_cnpj = px.line(
                avg_per_cnpj_df,
                x="data",
                y="avg_per_cnpj",
                title="Avg Transaction per Company",
                labels={"data": "Month", "avg_per_cnpj": f"Average ({currency_symbol})"},
                markers=True,
                template="plotly_white"
            )
            fig_avg_cnpj.update_traces(line_color="#FF6B6B", hovertemplate=f"<b>%{{x|%B}}</b><br>{currency_symbol} %{{y:,.2f}}<extra></extra>")
            fig_avg_cnpj = apply_shadcn_theme(fig_avg_cnpj)
            st.plotly_chart(fig_avg_cnpj, width="stretch", key="overview_avg_cnpj")



# ============ TAB 3: USERS ============
with tab3:
    st.subheader(f"User Analysis (Unique Individuals and Companies) {get_title_suffix()}")
    
    # 2-Column Layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Unique Individuals (CPF) Bar Chart
        cpfs_df = filtered_users.sort_values("data")
        if not cpfs_df.empty:
            fig_cpf = px.bar(
                cpfs_df,
                x="data",
                y="cpfs_unicos",
                title=f"Unique Individuals (CPF)",
                labels={"data": "Month", "cpfs_unicos": "Unique CPFs"},
                template="plotly_white"
            )
            fig_cpf.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
            fig_cpf = apply_shadcn_theme(fig_cpf)
            st.plotly_chart(fig_cpf, width="stretch", key="users_cpf")
        
        # Company/Individual Ratio
        st.markdown("---")
        st.subheader("Company/Individual Ratio")
        
        with st.expander("ℹ️ About this Metric"):
            st.write("""
            **Company/Individual Ratio**: This metric shows the percentage distribution of unique companies (CNPJs) vs unique individuals (CPFs) trading cryptocurrencies.
            
            - Higher company percentage indicates more institutional participation
            - Higher individual percentage indicates more retail participation
            
            This helps understand the institutional vs retail composition of the market participants.
            """)
        
        ratio_df = filtered_users.sort_values("data").copy()
        if not ratio_df.empty:
            # Calculate percentages
            ratio_df["total_users"] = ratio_df["cnpjs_unicos"] + ratio_df["cpfs_unicos"]
            ratio_df["pct_companies"] = (ratio_df["cnpjs_unicos"] / ratio_df["total_users"]) * 100
            ratio_df["pct_individuals"] = (ratio_df["cpfs_unicos"] / ratio_df["total_users"]) * 100
            
            fig_ratio = go.Figure()
            fig_ratio.add_trace(go.Scatter(
                x=ratio_df["data"],
                y=ratio_df["pct_individuals"],
                name="Individuals (CPF)",
                mode="lines",
                stackgroup="one",
                fillcolor="#1f77b4",
                line=dict(color="#1f77b4"),
                hovertemplate="<b>%{x|%B}</b><br>Individuals: %{y:.2f}%<extra></extra>"
            ))
            fig_ratio.add_trace(go.Scatter(
                x=ratio_df["data"],
                y=ratio_df["pct_companies"],
                name="Companies (CNPJ)",
                mode="lines",
                stackgroup="one",
                fillcolor="#FF6B6B",
                line=dict(color="#FF6B6B"),
                hovertemplate="<b>%{x|%B}</b><br>Companies: %{y:.2f}%<extra></extra>"
            ))
            
            fig_ratio.update_layout(
                title=f"% of Users: Individuals vs Companies",
                xaxis_title="Month",
                yaxis_title="Percentage (%)",
                yaxis=dict(range=[0, 100]),
                hovermode="x unified",
                template="plotly_white"
            )
            fig_ratio = apply_shadcn_theme(fig_ratio)
            st.plotly_chart(fig_ratio, width="stretch", key="users_ratio")
        
        # Monthly User Growth (MoM)
        if not filtered_merged.empty:
            st.markdown("---")
            st.subheader("Monthly User Growth (MoM)")
            
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
            fig_growth = apply_shadcn_theme(fig_growth)
            st.plotly_chart(fig_growth, width="stretch", key="users_growth")
    
    with col2:
        # Unique Companies (CNPJ) Bar Chart
        cnpjs_df = filtered_users.sort_values("data")
        if not cnpjs_df.empty:
            fig_cnpj = px.bar(
                cnpjs_df,
                x="data",
                y="cnpjs_unicos",
                title=f"Unique Companies (CNPJ)",
                labels={"data": "Month", "cnpjs_unicos": "Unique CNPJs"},
                template="plotly_white",
                color_discrete_sequence=["#FF6B6B"]
            )
            fig_cnpj.update_traces(hovertemplate="<b>%{x|%B}</b><br>%{y:,}<extra></extra>")
            fig_cnpj = apply_shadcn_theme(fig_cnpj)
            st.plotly_chart(fig_cnpj, width="stretch", key="users_cnpj")
        
        # Trading Volume Breakdown by Entity Type
        st.markdown("---")
        st.subheader("Trading Volume Breakdown")
        
        with st.expander("ℹ️ About this Graph"):
            st.write("""
            **Trading Volume Breakdown**: This graph shows the percentage of total trading volume attributed to:
            - **Individuals (CPF)**: Sum of foreign and domestic operations by individuals
            - **Companies (CNPJ)**: Sum of foreign and domestic operations by companies
            
            Note: Exchange operations are excluded from this breakdown as they don't have entity type classification.
            """)
        
        volume_df = filtered_op.sort_values("data").copy()
        if not volume_df.empty:
            # Calculate total PF and PJ volumes
            volume_df["total_pf_volume"] = volume_df["valor_exterior_pf"] + volume_df["valor_sem_ex_pf"]
            volume_df["total_pj_volume"] = volume_df["valor_exterior_pj"] + volume_df["valor_sem_ex_pj"]
            volume_df["total_known_volume"] = volume_df["total_pf_volume"] + volume_df["total_pj_volume"]
            
            # Calculate percentages
            volume_df["pct_pf_volume"] = (volume_df["total_pf_volume"] / volume_df["total_known_volume"]) * 100
            volume_df["pct_pj_volume"] = (volume_df["total_pj_volume"] / volume_df["total_known_volume"]) * 100
            
            fig_volume = go.Figure()
            fig_volume.add_trace(go.Scatter(
                x=volume_df["data"],
                y=volume_df["pct_pf_volume"],
                name="Individuals (CPF)",
                mode="lines",
                stackgroup="one",
                fillcolor="#1f77b4",
                line=dict(color="#1f77b4"),
                hovertemplate="<b>%{x|%B}</b><br>Individuals: %{y:.2f}%<extra></extra>"
            ))
            fig_volume.add_trace(go.Scatter(
                x=volume_df["data"],
                y=volume_df["pct_pj_volume"],
                name="Companies (CNPJ)",
                mode="lines",
                stackgroup="one",
                fillcolor="#FF6B6B",
                line=dict(color="#FF6B6B"),
                hovertemplate="<b>%{x|%B}</b><br>Companies: %{y:.2f}%<extra></extra>"
            ))
            
            fig_volume.update_layout(
                title=f"% of Trading Volume: Individuals vs Companies",
                xaxis_title="Month",
                yaxis_title="Percentage (%)",
                yaxis=dict(range=[0, 100]),
                hovermode="x unified",
                template="plotly_white"
            )
            fig_volume = apply_shadcn_theme(fig_volume)
            st.plotly_chart(fig_volume, width="stretch", key="users_volume")


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
            fig_ops = apply_shadcn_theme(fig_ops)
            st.plotly_chart(fig_ops, width="stretch", key="gender_ops")
    
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
            fig_val = apply_shadcn_theme(fig_val)
            st.plotly_chart(fig_val, width="stretch", key="gender_val")
    
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
            width="stretch",
            hide_index=True
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
# ============ TAB 5: CRYPTOCURRENCIES ============
with tab5:
    st.subheader(f"Cryptocurrency Analysis {get_title_suffix()}")
    
    if not filtered_crypto.empty:
        # 1. Market Dominance at top
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
            fig_tree = apply_shadcn_theme(fig_tree)
            st.plotly_chart(fig_tree, width="stretch", key="crypto_tree")
        
        # 2. Volume vs Average Ticket below Market Dominance
        st.markdown("---")
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
            fig_scatter = apply_shadcn_theme(fig_scatter)
            st.plotly_chart(fig_scatter, width="stretch", key="crypto_scatter")
        
        # 3. Row with 3 columns: Top 10 charts
        st.markdown("---")
        st.subheader("Top 10 Cryptocurrencies")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Dominance Donut Chart (Top 5 + Others)
            dominance_series = filtered_crypto.groupby("criptoativo")[f"valor_total_operacoes{currency_suffix}"].sum().sort_values(ascending=False)
            
            if not dominance_series.empty:
                top_5 = dominance_series.head(5)
                others_val = dominance_series.iloc[5:].sum()
                
                donut_data = top_5.reset_index()
                if others_val > 0:
                    donut_data = pd.concat([
                        donut_data, 
                        pd.DataFrame({"criptoativo": ["Others"], f"valor_total_operacoes{currency_suffix}": [others_val]})
                    ], ignore_index=True)
                
                total_vol = dominance_series.sum()
                
                fig_donut = px.pie(
                    donut_data,
                    values=f"valor_total_operacoes{currency_suffix}",
                    names="criptoativo",
                    title=f"Market Dominance (Value)",
                    hole=0.6,
                    template="plotly_white"
                )
                
                fig_donut.update_traces(
                    textposition='inside', 
                    textinfo='percent+label',
                    hovertemplate=f"<b>%{{label}}</b><br>{currency_symbol} %{{value:,.2f}}<br>(%{{percent}})<extra></extra>"
                )
                
                fig_donut.update_layout(
                    annotations=[dict(text=f"Total<br>{currency_symbol}{total_vol/1e9:.1f}B", x=0.5, y=0.5, font_size=20, showarrow=False)]
                )
                
                fig_donut = apply_shadcn_theme(fig_donut)
                st.plotly_chart(fig_donut, width="stretch", key="crypto_dominance")
        
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
                    title=f"By Number of Operations",
                    labels={"num_operacoes": "Number of Operations", "criptoativo": "Crypto"},
                    template="plotly_white",
                    color_discrete_sequence=["#FF6B6B"]
                )
                fig_top_ops.update_traces(hovertemplate="<b>%{y}</b><br>%{x:,}<extra></extra>")
                fig_top_ops = apply_shadcn_theme(fig_top_ops)
                st.plotly_chart(fig_top_ops, width="stretch", key="crypto_top_ops")
        
        with col3:
            avg_value = (
                filtered_crypto.groupby("criptoativo")[f"valor_medio_operacao{currency_suffix}"]
                .mean()
                .nlargest(10)
                .reset_index()
                .sort_values(f"valor_medio_operacao{currency_suffix}")
            )
            
            if not avg_value.empty:
                fig_avg = px.bar(
                    avg_value,
                    x=f"valor_medio_operacao{currency_suffix}",
                    y="criptoativo",
                    orientation="h",
                    title=f"By Average Operation Value",
                    labels={f"valor_medio_operacao{currency_suffix}": f"Average Value ({currency_symbol})", "criptoativo": "Crypto"},
                    template="plotly_white",
                    color_discrete_sequence=["#2ca02c"]
                )
                fig_avg.update_traces(hovertemplate=f"<b>%{{y}}</b><br>{currency_symbol} %{{x:,.2f}}<extra></extra>")
                fig_avg = apply_shadcn_theme(fig_avg)
                st.plotly_chart(fig_avg, width="stretch", key="crypto_avg")
        
        # 4. Evolution of Top 5 Cryptocurrencies (no slider)
        st.markdown("---")
        st.subheader("Evolution of Top 5 Cryptocurrencies")
        
        # Get top 5 cryptocurrencies by total value
        top_5_crypto = (
            filtered_crypto.groupby("criptoativo")[f"valor_total_operacoes{currency_suffix}"]
            .sum()
            .nlargest(5)
            .index.tolist()
        )
        
        filtered_top_5 = filtered_crypto[filtered_crypto["criptoativo"].isin(top_5_crypto)]
        
        crypto_timeline = (
            filtered_top_5.sort_values("data")
            .groupby(["data", "criptoativo"])[f"valor_total_operacoes{currency_suffix}"]
            .sum()
            .reset_index()
        )
        
        if not crypto_timeline.empty:
            fig_crypto_line = px.line(
                crypto_timeline,
                x="data",
                y=f"valor_total_operacoes{currency_suffix}",
                color="criptoativo",
                title=f"Monthly Trading Volume - Top 5 Cryptocurrencies {get_title_suffix()}",
                labels={"data": "Month", f"valor_total_operacoes{currency_suffix}": f"Total Value ({currency_symbol})", "criptoativo": "Cryptocurrency"},
                template="plotly_white",
                markers=True
            )
            fig_crypto_line.update_traces(hovertemplate=f"<b>%{{x|%B}}</b><br>{currency_symbol} %{{y:,.2f}}<extra></extra>")
            fig_crypto_line = apply_shadcn_theme(fig_crypto_line)
            st.plotly_chart(fig_crypto_line, width="stretch", key="crypto_line")
        
        # 5. Cryptocurrency Search Feature
        st.markdown("---")
        st.subheader("Individual Cryptocurrency Analysis")
        
        # Get all available cryptocurrencies
        all_cryptos = sorted(filtered_crypto["criptoativo"].unique())
        
        # Search/Select cryptocurrency
        selected_crypto = st.selectbox(
            "Search and select a cryptocurrency:",
            options=all_cryptos,
            index=0 if len(all_cryptos) > 0 else None
        )
        
        if selected_crypto:
            # Filter data for selected cryptocurrency
            crypto_data = filtered_crypto[filtered_crypto["criptoativo"] == selected_crypto].sort_values("data")
            
            if not crypto_data.empty:
                # Summary metrics
                total_volume = crypto_data[f"valor_total_operacoes{currency_suffix}"].sum()
                total_ops = crypto_data["num_operacoes"].sum()
                avg_value = crypto_data[f"valor_medio_operacao{currency_suffix}"].mean()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Volume (Period)", f"{currency_symbol} {total_volume:,.2f}")
                
                with col2:
                    st.metric("Total Transactions", f"{total_ops:,}")
                
                with col3:
                    st.metric("Avg Transaction Value", f"{currency_symbol} {avg_value:,.2f}")
                
                # Charts for selected cryptocurrency
                col1, col2 = st.columns(2)
                
                with col1:
                    # Monthly trading volume
                    fig_volume = px.area(
                        crypto_data,
                        x="data",
                        y=f"valor_total_operacoes{currency_suffix}",
                        title=f"{selected_crypto} - Monthly Trading Volume",
                        labels={"data": "Month", f"valor_total_operacoes{currency_suffix}": f"Volume ({currency_symbol})"},
                        template="plotly_white"
                    )
                    fig_volume.update_traces(hovertemplate=f"<b>%{{x|%B %Y}}</b><br>{currency_symbol} %{{y:,.2f}}<extra></extra>")
                    fig_volume = apply_shadcn_theme(fig_volume)
                    st.plotly_chart(fig_volume, width="stretch", key=f"crypto_search_volume_{selected_crypto}")
                
                with col2:
                    # Number of transactions
                    fig_ops = px.bar(
                        crypto_data,
                        x="data",
                        y="num_operacoes",
                        title=f"{selected_crypto} - Number of Transactions",
                        labels={"data": "Month", "num_operacoes": "Transactions"},
                        template="plotly_white",
                        color_discrete_sequence=["#FF6B6B"]
                    )
                    fig_ops.update_traces(hovertemplate="<b>%{x|%B %Y}</b><br>%{y:,}<extra></extra>")
                    fig_ops = apply_shadcn_theme(fig_ops)
                    st.plotly_chart(fig_ops, width="stretch", key=f"crypto_search_ops_{selected_crypto}")
                
                # Detailed data table
                st.markdown("**Monthly Detailed Data**")
                display_crypto = crypto_data.copy()
                display_crypto["month_year"] = display_crypto["data"].dt.strftime("%B %Y")
                
                display_cols = display_crypto[["month_year", "valor_total_operacoes", "num_operacoes", "valor_medio_operacao"]]
                display_cols.columns = ["Month", "Total Volume (R$)", "Transactions", "Avg Value (R$)"]
                
                st.dataframe(
                    display_cols.sort_values("Month", ascending=False),
                    width="stretch",
                    hide_index=True
                )
            else:
                st.info(f"No data available for {selected_crypto} in the selected period")
        
    else:
        st.info(f"ℹ️ No data available for the selected period")
