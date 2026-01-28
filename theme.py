import plotly.graph_objects as go
import plotly.io as pio

# Helper function to return custom CSS

# Define the custom LIGHT theme inspired by Shadcn UI (Zinc/Signal White)
# Define the custom LIGHT theme inspired by Shadcn UI (Zinc/Signal White)
# Updated to match "Lines and Points" color palette from user image
SHADCN_COLORS = {
    "background": "#ffffff",      # white
    "paper": "#ffffff",          # white
    "text": "#09090b",           # zinc-950
    "grid": "#e4e4e7",           # zinc-200
    "primary": "#396AB1",        # Blue (Lines)
    "secondary": "#535154",      # Gray (Lines) - Used for axes/secondary text
    "accent": "#CC2529",         # Red (Lines)
    "success": "#3E9651",        # Green (Lines)
    "card": "#ffffff"            # white
}

SHADCN_THEME = {
    "layout": go.Layout(
        paper_bgcolor="rgba(0,0,0,0)", 
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=SHADCN_COLORS["text"]),
        xaxis=dict(
            showgrid=False, 
            zeroline=False, 
            color=SHADCN_COLORS["secondary"],
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            showgrid=True, 
            gridcolor=SHADCN_COLORS["grid"], 
            zeroline=False, 
            color=SHADCN_COLORS["secondary"],
            tickfont=dict(size=12)
        ),
        margin=dict(t=40, b=40, l=20, r=20),
        hovermode="x unified",
        template="plotly_white", # Switch to white template
        colorway=[
            "#396AB1", # Blue
            "#DA7C30", # Orange
            "#3E9651", # Green
            "#CC2529", # Red
            "#535154", # Gray
            "#6B4C9A", # Purple
            "#922428", # Brown
            "#948B3D"  # Yellow
        ]
    )
}

def apply_shadcn_theme(fig):
    """
    Applies the Shadcn-inspired theme to a Plotly figure.
    Updates layout, font sizes, and hover effects.
    """
    fig.update_layout(SHADCN_THEME["layout"])
    
    # Update traces for spline "flow" effect ONLY for lines (not pure markers)
    # Using 'getattr' safely because 'Bar' and others don't have 'mode'
    fig.for_each_trace(lambda t: t.update(line_shape="spline", line_width=3) 
                       if hasattr(t, 'mode') and t.mode and "lines" in t.mode else None)
    
    # Specific adjustments for Bar charts to look cleaner
    if fig.data and fig.data[0].type == 'bar':
        fig.update_traces(marker_line_width=0)
        
    return fig

def get_custom_css():
    """
    Returns the Shadcn-style CSS for the Streamlit app (Light Mode).
    """
    return """
    <style>
    /* Shadcn Light Mode Base */
    .stApp {
        background-color: #ffffff;
    }
    
    html, body, [class*="css"] {
        font-size: 16px;
        color: #09090b; /* Zinc-950 */
        font-family: 'Inter', sans-serif;
    }
    
    /* Increase Streamlit default text */
    .stMarkdown, .stText {
        font-size: 16px;
        color: #09090b;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6, .header {
        color: #18181b !important; /* Zinc-900 */
    }
    
    /* Metric styling to look like Cards */
    [data-testid="stMetricLabel"] {
        font-size: 15px !important;
        font-weight: 500;
        color: #71717a; /* Zinc-500 */
    }
    
    [data-testid="stMetricValue"] {
        font-size: 28px !important;
        font-weight: 700;
        color: #09090b; /* Zinc-950 */
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 14px !important;
    }
    
    /* Increase tab text size */
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 500;
        color: #71717a;
    }
    
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        color: #2563eb; /* Blue-600 */
        border-bottom-color: #2563eb;
    }
    
    /* Input widgets */
    .stSelectbox label, .stSlider label, .stDateInput label, .stRadio label {
        font-size: 15px !important;
        font-weight: 500;
        color: #52525b !important; /* Zinc-600 */
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-size: 16px !important;
        font-weight: 600;
        color: #18181b !important;
    }
    
    /* Custom containers */
    .metric-container {
        background-color: #ffffff; 
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e4e4e7; /* Zinc-200 */
        margin: 10px 0;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .header {
        font-size: 36px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    
    .disclaimer {
        background-color: #f4f4f5; /* Zinc-100 */
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #e4e4e7;
        border-left: 4px solid #2563eb;
        margin: 20px 0;
        font-size: 16px;
        color: #52525b;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8fafc; /* Slate-50 */
        border-right: 1px solid #e2e8f0;
    }
    
    .css-1d391kg, [data-testid="stSidebar"] {
        font-size: 16px;
        color: #334155;
    }
    </style>
    """
