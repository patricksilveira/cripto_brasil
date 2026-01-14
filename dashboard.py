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
    /* Increase base font size */
    html, body, [class*="css"] {
        font-size: 16px;
    }
    
    /* Increase Streamlit default text */
    .stMarkdown, .stText {
        font-size: 16px;
    }
    
    /* Increase metric labels and values */
    [data-testid="stMetricLabel"] {
        font-size: 18px !important;
        font-weight: 600;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: 700;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 16px !important;
    }
    
    /* Increase tab text size */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 18px;
        font-weight: 600;
    }
    
    /* Increase subheader size */
    h2, h3 {
        font-size: 26px !important;
        font-weight: 700 !important;
    }
    
    /* Increase selectbox and input labels */
    .stSelectbox label, .stSlider label, .stDateInput label, .stRadio label {
        font-size: 17px !important;
        font-weight: 600;
    }
    
    /* Increase expander text */
    .streamlit-expanderHeader {
        font-size: 17px !important;
        font-weight: 600;
    }
    
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    
    .header {
        color: #1f77b4;
        font-size: 36px;
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
        font-size: 16px;
    }
    
    /* Increase dataframe text */
    .dataframe {
        font-size: 15px !important;
    }
    
    /* Increase sidebar text */
    .css-1d391kg, [data-testid="stSidebar"] {
        font-size: 16px;
    }
    
    /* Increase sidebar header */
    [data-testid="stSidebar"] h2 {
        font-size: 22px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Helper function to update chart fonts
def update_chart_fonts(fig):
    """Apply larger fonts to Plotly charts for better readability"""
    fig.update_layout(
        title_font_size=20,
        font=dict(size=14),
        xaxis=dict(
            title_font_size=16,
            tickfont_size=14
        ),
        yaxis=dict(
            title_font_size=16,
            tickfont_size=14
        ),
        legend=dict(
            font_size=14
        ),
        hoverlabel=dict(
            font_size=14
        )
    )
    return fig

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
    <strong>Data Analysis:</strong> Produced by <a href="https://pplx.ai/patrickds3872" target="_blank">Perplexity AI</a> in November 2025 <br>
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

    # Operations breakdown metrics
    st.markdown("---")
    st.subheader(f"Operations Breakdown {get_title_suffix()}")
    
    if not filtered_op.empty:
        # Calculate totals for the entire period
        total_pf_foreign = filtered_op['valor_exterior_pf'].sum()
        total_pj_foreign = filtered_op['valor_exterior_pj'].sum()
        total_domestic = filtered_op['valor_sem_ex_subtotal'].sum()
        total_exchanges = filtered_op['valor_exchanges'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Individual - Foreign",
                f"R$ {total_pf_foreign:,.0f}M"
            )
        
        with col2:
            st.metric(
                "Company - Foreign",
                f"R$ {total_pj_foreign:,.0f}M"
            )
        
        with col3:
            st.metric(
                "Ind/Co - Domestic",
                f"R$ {total_domestic:,.0f}M"
            )
        
        with col4:
            st.metric(
                "Exchanges",
                f"R$ {total_exchanges:,.0f}M"
            )

    # 1st Row: Total Operations Data (3 columns)
    st.markdown("---")
    st.subheader(f"Total Operations Data {get_title_suffix()}")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Total Operations Value Timeline
        timeline_df = filtered_op.sort_values("data").groupby("data").agg({
            "valor_total": "sum"
        }).reset_index()

        if not timeline_df.empty:
            fig_timeline = px.line(
                timeline_df,
                x="data",
                y="valor_total",
                title=f"Total Operations Value",
                labels={"data": "Month", "valor_total": "Value (Millions R$)"},
                markers=True,
                template="plotly_white"
            )
            fig_timeline.update_traces(hovertemplate="<b>%{x|%B}</b><br>R$ %{y:,.2f}M<extra></extra>")
            fig_timeline = update_chart_fonts(fig_timeline)
            st.plotly_chart(fig_timeline, use_container_width=True, key="overview_timeline")
        else:
            st.info(f"ℹ️ No data available for {filter_label}")
    
    with col2:
        # Operations Composition Chart
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
                title=f"Operations Composition",
                xaxis_title="Month",
                yaxis_title="Value (Millions R$)",
                hovermode="x unified",
                template="plotly_white"
            )
            fig_comp = update_chart_fonts(fig_comp)
            
            st.plotly_chart(fig_comp, use_container_width=True, key="overview_comp")
    
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
            fig_geo = update_chart_fonts(fig_geo)
            st.plotly_chart(fig_geo, use_container_width=True, key="overview_geo")

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
            total_pf_volume = filtered_op["valor_exterior_pf"].sum() + filtered_op["valor_sem_ex_pf"].sum()
            
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
                    f"R$ {avg_transaction_period:,.2f}"
                )
                st.metric(
                    "Max Individuals",
                    f"{max_cpfs:,}"
                )
            with col_b:
                st.metric(
                    "Total Volume",
                    f"R$ {total_pf_volume:,.0f}M"
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
            fig_users = update_chart_fonts(fig_users)
            st.plotly_chart(fig_users, use_container_width=True, key="overview_users")
    
    with col3:
        # Average Transaction per Individual
        if not filtered_op.empty and not filtered_users.empty:
            # Calculate average transaction per CPF
            avg_per_cpf_df = filtered_op.merge(
                filtered_users[["data", "cpfs_unicos"]], 
                on="data", 
                how="left"
            )
            avg_per_cpf_df["total_pf_volume"] = avg_per_cpf_df["valor_exterior_pf"] + avg_per_cpf_df["valor_sem_ex_pf"]
            # Convert from millions to actual R$ values
            avg_per_cpf_df["avg_per_cpf"] = (avg_per_cpf_df["total_pf_volume"] * 1_000_000) / avg_per_cpf_df["cpfs_unicos"]
            avg_per_cpf_df = avg_per_cpf_df.sort_values("data")
            
            fig_avg_cpf = px.line(
                avg_per_cpf_df,
                x="data",
                y="avg_per_cpf",
                title="Avg Transaction per Individual",
                labels={"data": "Month", "avg_per_cpf": "Average (R$)"},
                markers=True,
                template="plotly_white"
            )
            fig_avg_cpf.update_traces(line_color="#1f77b4", hovertemplate="<b>%{x|%B}</b><br>R$ %{y:,.2f}<extra></extra>")
            fig_avg_cpf = update_chart_fonts(fig_avg_cpf)
            st.plotly_chart(fig_avg_cpf, use_container_width=True, key="overview_avg_cpf")
    
    # 3rd Row: Companies Analytics (3 columns)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Statistical Data for Companies
        st.markdown("**🏢 Companies Statistics**")
        
        if not filtered_op.empty and not filtered_users.empty:
            # Total Volume
            total_pj_volume = filtered_op["valor_exterior_pj"].sum() + filtered_op["valor_sem_ex_pj"].sum()
            
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
                    f"R$ {avg_transaction_period_pj:,.2f}"
                )
                st.metric(
                    "Max Companies",
                    f"{max_cnpjs:,}"
                )
            with col_b:
                st.metric(
                    "Total Volume",
                    f"R$ {total_pj_volume:,.0f}M"
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
            fig_cnpjs = update_chart_fonts(fig_cnpjs)
            st.plotly_chart(fig_cnpjs, use_container_width=True, key="overview_cnpjs")
    
    with col3:
        # Average Transaction per Company
        if not filtered_op.empty and not filtered_users.empty:
            # Calculate average transaction per CNPJ
            avg_per_cnpj_df = filtered_op.merge(
                filtered_users[["data", "cnpjs_unicos"]], 
                on="data", 
                how="left"
            )
            avg_per_cnpj_df["total_pj_volume"] = avg_per_cnpj_df["valor_exterior_pj"] + avg_per_cnpj_df["valor_sem_ex_pj"]
            # Convert from millions to actual R$ values
            avg_per_cnpj_df["avg_per_cnpj"] = (avg_per_cnpj_df["total_pj_volume"] * 1_000_000) / avg_per_cnpj_df["cnpjs_unicos"]
            avg_per_cnpj_df = avg_per_cnpj_df.sort_values("data")
            
            fig_avg_cnpj = px.line(
                avg_per_cnpj_df,
                x="data",
                y="avg_per_cnpj",
                title="Avg Transaction per Company",
                labels={"data": "Month", "avg_per_cnpj": "Average (R$)"},
                markers=True,
                template="plotly_white"
            )
            fig_avg_cnpj.update_traces(line_color="#FF6B6B", hovertemplate="<b>%{x|%B}</b><br>R$ %{y:,.2f}<extra></extra>")
            fig_avg_cnpj = update_chart_fonts(fig_avg_cnpj)
            st.plotly_chart(fig_avg_cnpj, use_container_width=True, key="overview_avg_cnpj")



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
            fig_cpf = update_chart_fonts(fig_cpf)
            st.plotly_chart(fig_cpf, use_container_width=True, key="users_cpf")
        
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
            fig_ratio = update_chart_fonts(fig_ratio)
            st.plotly_chart(fig_ratio, use_container_width=True, key="users_ratio")
        
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
            fig_growth = update_chart_fonts(fig_growth)
            st.plotly_chart(fig_growth, use_container_width=True, key="users_growth")
    
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
            fig_cnpj = update_chart_fonts(fig_cnpj)
            st.plotly_chart(fig_cnpj, use_container_width=True, key="users_cnpj")
        
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
            fig_volume = update_chart_fonts(fig_volume)
            st.plotly_chart(fig_volume, use_container_width=True, key="users_volume")


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
            fig_ops = update_chart_fonts(fig_ops)
            st.plotly_chart(fig_ops, use_container_width=True, key="gender_ops")
    
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
            fig_val = update_chart_fonts(fig_val)
            st.plotly_chart(fig_val, use_container_width=True, key="gender_val")
    
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
            fig_tree = update_chart_fonts(fig_tree)
            st.plotly_chart(fig_tree, use_container_width=True, key="crypto_tree")
        
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
            fig_scatter = update_chart_fonts(fig_scatter)
            st.plotly_chart(fig_scatter, use_container_width=True, key="crypto_scatter")
        
        # 3. Row with 3 columns: Top 10 charts
        st.markdown("---")
        st.subheader("Top 10 Cryptocurrencies")
        
        col1, col2, col3 = st.columns(3)
        
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
                    title=f"By Total Value",
                    labels={"valor_total_operacoes": "Total Value (R$)", "criptoativo": "Crypto"},
                    template="plotly_white"
                )
                fig_top_value.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
                fig_top_value = update_chart_fonts(fig_top_value)
                st.plotly_chart(fig_top_value, use_container_width=True, key="crypto_top_value")
        
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
                fig_top_ops = update_chart_fonts(fig_top_ops)
                st.plotly_chart(fig_top_ops, use_container_width=True, key="crypto_top_ops")
        
        with col3:
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
                    title=f"By Average Operation Value",
                    labels={"valor_medio_operacao": "Average Value (R$)", "criptoativo": "Crypto"},
                    template="plotly_white",
                    color_discrete_sequence=["#2ca02c"]
                )
                fig_avg.update_traces(hovertemplate="<b>%{y}</b><br>R$ %{x:,.2f}<extra></extra>")
                fig_avg = update_chart_fonts(fig_avg)
                st.plotly_chart(fig_avg, use_container_width=True, key="crypto_avg")
        
        # 4. Evolution of Top 5 Cryptocurrencies (no slider)
        st.markdown("---")
        st.subheader("Evolution of Top 5 Cryptocurrencies")
        
        # Get top 5 cryptocurrencies by total value
        top_5_crypto = (
            filtered_crypto.groupby("criptoativo")["valor_total_operacoes"]
            .sum()
            .nlargest(5)
            .index.tolist()
        )
        
        filtered_top_5 = filtered_crypto[filtered_crypto["criptoativo"].isin(top_5_crypto)]
        
        crypto_timeline = (
            filtered_top_5.sort_values("data")
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
                title=f"Monthly Trading Volume - Top 5 Cryptocurrencies {get_title_suffix()}",
                labels={"data": "Month", "valor_total_operacoes": "Total Value (R$)", "criptoativo": "Cryptocurrency"},
                template="plotly_white",
                markers=True
            )
            fig_crypto_line.update_traces(hovertemplate="<b>%{x|%B}</b><br>R$ %{y:,.2f}<extra></extra>")
            fig_crypto_line = update_chart_fonts(fig_crypto_line)
            st.plotly_chart(fig_crypto_line, use_container_width=True, key="crypto_line")
        
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
                total_volume = crypto_data["valor_total_operacoes"].sum()
                total_ops = crypto_data["num_operacoes"].sum()
                avg_value = crypto_data["valor_medio_operacao"].mean()
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Volume (Period)", f"R$ {total_volume:,.2f}")
                
                with col2:
                    st.metric("Total Transactions", f"{total_ops:,}")
                
                with col3:
                    st.metric("Avg Transaction Value", f"R$ {avg_value:,.2f}")
                
                # Charts for selected cryptocurrency
                col1, col2 = st.columns(2)
                
                with col1:
                    # Monthly trading volume
                    fig_volume = px.area(
                        crypto_data,
                        x="data",
                        y="valor_total_operacoes",
                        title=f"{selected_crypto} - Monthly Trading Volume",
                        labels={"data": "Month", "valor_total_operacoes": "Volume (R$)"},
                        template="plotly_white"
                    )
                    fig_volume.update_traces(hovertemplate="<b>%{x|%B %Y}</b><br>R$ %{y:,.2f}<extra></extra>")
                    fig_volume = update_chart_fonts(fig_volume)
                    st.plotly_chart(fig_volume, use_container_width=True, key=f"crypto_search_volume_{selected_crypto}")
                
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
                    fig_ops = update_chart_fonts(fig_ops)
                    st.plotly_chart(fig_ops, use_container_width=True, key=f"crypto_search_ops_{selected_crypto}")
                
                # Detailed data table
                st.markdown("**Monthly Detailed Data**")
                display_crypto = crypto_data.copy()
                display_crypto["month_year"] = display_crypto["data"].dt.strftime("%B %Y")
                
                display_cols = display_crypto[["month_year", "valor_total_operacoes", "num_operacoes", "valor_medio_operacao"]]
                display_cols.columns = ["Month", "Total Volume (R$)", "Transactions", "Avg Value (R$)"]
                
                st.dataframe(
                    display_cols.sort_values("Month", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info(f"No data available for {selected_crypto} in the selected period")
        
    else:
        st.info(f"ℹ️ No data available for the selected period")
