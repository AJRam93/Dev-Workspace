import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Marketing Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)

# ─────────────────────────────────────────
# THEME / COLORS
# ─────────────────────────────────────────
CHANNEL_COLORS = {
    "Google Ads":   "#3D76AF",
    "Email":        "#0F6E56",
    "Meta Ads":     "#EF9F27",
    "LinkedIn Ads": "#7F77DD",
    "TikTok Ads":   "#D85A30",
}
NAVY   = "#1A3C5E"
GREEN  = "#0F6E56"
GRAY   = "#6B7A8D"
BG     = "#E9A107"

# ─────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #F8FAFC; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1A3C5E; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stMultiSelect label { color: #CBD5E1 !important; font-size: 13px; }

    /* Sidebar toggle button */
    [data-testid="collapsedControl"] {
        display: flex !important;
        visibility: visible !important;
        color: #1A3C5E !important;
        background-color: white !important;
        border-radius: 0 6px 6px 0 !important;
        box-shadow: 2px 0 4px rgba(0,0,0,0.1) !important;
    }
    [data-testid="collapsedControl"] svg {
        fill: #1A3C5E !important;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    [data-testid="stMetricValue"] { color: #1A3C5E !important; font-size: 28px !important; }
    [data-testid="stMetricLabel"] { color: #6B7A8D !important; font-size: 13px !important; }

    /* Section headers */
    .section-header {
        font-size: 11px;
        font-weight: 600;
        color: #6B7A8D;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin: 24px 0 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid #E2E8F0;
    }

    /* AI insight box */
    .insight-box {
        background: linear-gradient(135deg, #EEF3F8 0%, #E8F0E8 100%);
        border-left: 4px solid #1A3C5E;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin: 12px 0;
        font-size: 14px;
        color: #1A3C5E;
        line-height: 1.6;
    }

    /* Chart containers */
    .chart-card {
        background: white;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# DATA LOADER
# ─────────────────────────────────────────
@st.cache_data
def load_data():
    try:
        # Auto-detect the correct header row by trying both 0 and 1
        for header_row in [1, 0]:
            df = pd.read_excel(
                "Marketing_Analytics_Dataset_2023_2024.xlsx",
                sheet_name="All Data (2023-2024)",
                header=header_row
            )
            df.columns = df.columns.astype(str).str.strip()
            if "Date" in df.columns:
                break
        else:
            # Neither worked — show what columns we actually got
            st.error(f"Could not find 'Date' column. Columns found: {df.columns.tolist()}")
            st.stop()

    except FileNotFoundError:
        st.error("⚠️ Data file not found. Make sure Marketing_Analytics_Dataset_2023_2024.xlsx is in the same folder as this script.")
        st.stop()

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])  # drop any rows where date didn't parse
    df["Month"]     = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["Year"]      = df["Date"].dt.year.astype(str)
    df["YearMonth"] = df["Date"].dt.strftime("%b %Y")

    # Normalize ALL column names — handles spaces, $, (), etc.
    df.columns = (
        df.columns
        .str.strip()
        .str.replace(r"[^\w]", "_", regex=True)
        .str.replace(r"_+", "_", regex=True)
        .str.strip("_")
    )

    # Rename to clean short names by keyword detection
    rename_map = {}
    for col in df.columns:
        low = col.lower()
        if "spend" in low:                rename_map[col] = "Ad_Spend"
        elif "revenue" in low:            rename_map[col] = "Revenue"
        elif low.startswith("cpa"):       rename_map[col] = "CPA"
        elif low.startswith("ctr"):       rename_map[col] = "CTR"
        elif low.startswith("cvr"):       rename_map[col] = "CVR"
        elif low.startswith("roas"):      rename_map[col] = "ROAS"
    df = df.rename(columns=rename_map)

    return df

df = load_data()


# ─────────────────────────────────────────
# SIDEBAR — FILTERS
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Dashboard Filters")
    st.markdown("---")

    # Year filter
    years = sorted(df["Year"].unique(), reverse=True)
    selected_years = st.multiselect(
        "Year", years, default=years,
        help="Select one or both years"
    )

    # Channel filter
    channels = sorted(df["Channel"].unique())
    selected_channels = st.multiselect(
        "Channel", channels, default=channels
    )

    # Campaign filter
    campaigns = sorted(df["Campaign"].unique())
    selected_campaigns = st.multiselect(
        "Campaign", campaigns, default=campaigns
    )

    st.markdown("---")
    st.markdown("### 🎨 Chart style")
    show_data_labels = st.toggle("Show data labels", value=True)
    show_gridlines   = st.toggle("Show gridlines",   value=False)

    st.markdown("---")
    st.caption("Built with Streamlit + Plotly")


# ─────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────
mask = (
    df["Year"].isin(selected_years) &
    df["Channel"].isin(selected_channels) &
    df["Campaign"].isin(selected_campaigns)
)
filtered = df[mask].copy()

if filtered.empty:
    st.warning("No data matches your filters. Try selecting more options.")
    st.stop()


# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────
st.markdown(f"""
<div style="background:linear-gradient(135deg,#1A3C5E,#0F6E56);
            border-radius:12px; padding:20px 28px; margin-bottom:8px;">
    <h1 style="color:white;margin:0;font-size:22px;font-weight:600;">
        📊 Marketing Performance Dashboard
    </h1>
    <p style="color:#CBD5E1;margin:4px 0 0;font-size:13px;">
        {", ".join(selected_years)} &nbsp;·&nbsp;
        {len(selected_channels)} channel(s) &nbsp;·&nbsp;
        {len(filtered):,} data rows
    </p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SECTION 1 — EXECUTIVE SUMMARY SCORECARDS
# ─────────────────────────────────────────
st.markdown('<p class="section-header">Section 1 — Executive Summary</p>', unsafe_allow_html=True)

total_spend       = filtered["Ad_Spend"].sum()
total_revenue     = filtered["Revenue"].sum()
total_conversions = filtered["Conversions"].sum()
blended_roas      = total_revenue / total_spend if total_spend > 0 else 0
avg_cpa           = filtered["Ad_Spend"].sum() / total_conversions if total_conversions > 0 else 0

# Prior year delta helpers
def get_delta(col, agg="sum"):
    if len(selected_years) < 2:
        return None
    years_sorted = sorted([int(y) for y in selected_years])
    cur  = filtered[filtered["Year"] == str(years_sorted[-1])][col]
    prev = filtered[filtered["Year"] == str(years_sorted[-2])][col]
    c = cur.sum()  if agg == "sum" else cur.mean()
    p = prev.sum() if agg == "sum" else prev.mean()
    return f"{((c - p) / p * 100):+.1f}% vs {years_sorted[-2]}" if p > 0 else None

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Ad Spend",    f"${total_spend:,.0f}",       get_delta("Ad_Spend"))
c2.metric("Total Revenue",     f"${total_revenue:,.0f}",     get_delta("Revenue"))
c3.metric("Blended ROAS",      f"{blended_roas:.1f}x")
c4.metric("Total Conversions", f"{total_conversions:,.0f}",  get_delta("Conversions"))
c5.metric("Avg CPA",           f"${avg_cpa:.2f}")


# ─────────────────────────────────────────
# SECTION 2 — CHANNEL PERFORMANCE
# ─────────────────────────────────────────
st.markdown('<p class="section-header">Section 2 — Channel Performance</p>', unsafe_allow_html=True)

channel_summary = (
    filtered.groupby("Channel")
    .agg(Ad_Spend=("Ad_Spend","sum"), Revenue=("Revenue","sum"),
         Conversions=("Conversions","sum"), Clicks=("Clicks","sum"))
    .reset_index()
)
channel_summary["ROAS"] = (channel_summary["Revenue"] / channel_summary["Ad_Spend"]).round(2)
channel_summary["CPA"]  = (channel_summary["Ad_Spend"] / channel_summary["Conversions"]).round(2)
channel_summary["Color"] = channel_summary["Channel"].map(CHANNEL_COLORS)

col_a, col_b = st.columns(2)

with col_a:
    fig_spend = px.bar(
        channel_summary.sort_values("Ad_Spend"),
        x="Ad_Spend", y="Channel", orientation="h",
        color="Channel", color_discrete_map=CHANNEL_COLORS,
        text="Ad_Spend" if show_data_labels else None,
        title="Ad Spend by Channel",
        labels={"Ad_Spend": "Ad Spend ($)", "Channel": ""}
    )
    fig_spend.update_traces(
    texttemplate="$%{text:,.0f}", textposition="outside",
    marker_line_width=0,
    textfont=dict(color="#1E293B", size=11)
)
    
    fig_spend.update_layout(
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=show_gridlines, showticklabels=False, title=""),
        yaxis=dict(showgrid=False, tickfont=dict(color= "#080808", size=12)),
        margin=dict(l=0, r=60, t=40, b=0),
        title_font=dict(size=14, color="#1E293B")
    )
    st.plotly_chart(fig_spend, width="stretch")

with col_b:
    # Filter out Email outlier for readability (show as annotation instead)
    roas_df = channel_summary[channel_summary["Channel"] != "Email"].sort_values("ROAS")
    email_roas = channel_summary[channel_summary["Channel"] == "Email"]["ROAS"].values[0]

    fig_roas = px.bar(
        roas_df,
        x="ROAS", y="Channel", orientation="h",
        color="Channel", color_discrete_map=CHANNEL_COLORS,
        text="ROAS" if show_data_labels else None,
        title="ROAS by Channel (excl. Email)",
        labels={"ROAS": "Return on Ad Spend", "Channel": ""}
    )
    fig_roas.update_traces(
    texttemplate="%{text:.1f}x", textposition="outside",
    marker_line_width=0,
    textfont=dict(color="#1E293B", size=11)
)
    
    fig_roas.update_layout(
        showlegend=False, plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=show_gridlines, showticklabels=False, title=""),
        yaxis=dict(showgrid=False,tickfont=dict(color="#080808",size=12)),
        margin=dict(l=0, r=60, t=40, b=0),
        title_font=dict(size=14, color=NAVY)
    )
    st.plotly_chart(fig_roas, width="stretch")
    st.markdown(f"<p style='font-size:12px; color:#1E293B;'>💡 Email excluded — ROAS of <strong>{email_roas:.1f}x</strong> would compress all other bars</p>", unsafe_allow_html=True)


# ─────────────────────────────────────────
# SECTION 3 — TREND OVER TIME
# ─────────────────────────────────────────
st.markdown('<p class="section-header">Section 3 — Trend Over Time</p>', unsafe_allow_html=True)

monthly = (
    filtered.groupby(["Month", "Channel"])
    .agg(Ad_Spend=("Ad_Spend","sum"), Conversions=("Conversions","sum"),
         Revenue=("Revenue","sum"))
    .reset_index()
)
monthly_total = (
    monthly.groupby("Month")
    .agg(Ad_Spend=("Ad_Spend","sum"), Conversions=("Conversions","sum"))
    .reset_index()
)

col_c, col_d = st.columns([2, 1])

with col_c:
    fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
    fig_trend.add_trace(
        go.Bar(
            x=monthly_total["Month"], y=monthly_total["Ad_Spend"],
            name="Ad Spend", marker_color=NAVY, opacity=0.85,
            hovertemplate="<b>%{x|%b %Y}</b><br>Spend: $%{y:,.0f}<extra></extra>"
        ),
        secondary_y=False
    )
    fig_trend.add_trace(
        go.Scatter(
            x=monthly_total["Month"], y=monthly_total["Conversions"],
            name="Conversions", line=dict(color="#4ADDB8", width=3),
            mode="lines+markers", marker=dict(size=6),
            hovertemplate="<b>%{x|%b %Y}</b><br>Conversions: %{y:,.0f}<extra></extra>"
        ),
        secondary_y=True
    )
    fig_trend.update_layout(
        title="Monthly Spend    vs Conversions",
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(
            orientation="v",
            x=1.08,
            y=1,
            font=dict(color="#1E293B", size=12),
            bgcolor="white",
            bordercolor="#E2E8F0",
            borderwidth=1
        ),
        margin=dict(l=0, r=120, t=50, b=80),
        hovermode="x unified",
        title_font=dict(size=14, color=NAVY)
    )
    fig_trend.update_yaxes(
        title_text="Ad Spend ($)", secondary_y=False,
        showgrid=show_gridlines, gridcolor="#F0F0F0",
        title_font=dict(color="#1E293B"),
        tickfont=dict(color="#1E293B")
    )
    fig_trend.update_yaxes(
        title_text="Conversions", secondary_y=True,
        showgrid=False,
        title_font=dict(color="#1E293B"),
        tickfont=dict(color="#1E293B")
    )
    fig_trend.update_xaxes(
        tickfont=dict(color="#1E293B", size=11),
        tickangle=-45,
        showgrid=False,
        tickformat="%b %Y"
    )
    st.plotly_chart(fig_trend, width="stretch")
with col_d:
    conv_by_channel = (
        filtered.groupby("Channel")["Conversions"].sum().reset_index()
    )
    fig_donut = px.pie(
        conv_by_channel, values="Conversions", names="Channel",
        color="Channel", color_discrete_map=CHANNEL_COLORS,
        hole=0.5, title="Conversions by Channel"
    )
    fig_donut.update_traces(
        textposition="inside", textinfo="percent",
        textfont=dict(color="#F8F9FA",size=12),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} conversions<br>%{percent}<extra></extra>"
    )
    fig_donut.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(
            orientation="v",
            x=1, y=0.5,
            font=dict(color="#1E293B", size=12)
        ),
        margin=dict(l=0, r=0, t=40, b=0),
        title_font=dict(size=14, color=NAVY),
        font=dict(color="#1E293B")
    )
    st.plotly_chart(fig_donut, width="stretch")


# ─────────────────────────────────────────
# SECTION 4 — CAMPAIGN DETAIL TABLE
# ─────────────────────────────────────────
st.markdown('<p class="section-header">Section 4 — Campaign Detail</p>', unsafe_allow_html=True)

campaign_table = (
    filtered.groupby(["Campaign", "Channel"])
    .agg(Ad_Spend=("Ad_Spend","sum"), Conversions=("Conversions","sum"),
         Revenue=("Revenue","sum"), Clicks=("Clicks","sum"))
    .reset_index()
)
campaign_table["ROAS"] = (campaign_table["Revenue"] / campaign_table["Ad_Spend"]).round(2)
campaign_table["CPA"]  = (campaign_table["Ad_Spend"] / campaign_table["Conversions"]).round(2)

def efficiency_label(roas):
    if roas >= 15: return "✅ Strong"
    if roas >= 5:  return "🟡 OK"
    return "🔴 Review"

campaign_table["Efficiency"] = campaign_table["ROAS"].apply(efficiency_label)
campaign_table = campaign_table.sort_values("ROAS", ascending=False)

display_table = campaign_table[[
    "Campaign", "Channel", "Ad_Spend", "Conversions", "CPA", "ROAS", "Efficiency"
]].copy()
display_table.columns = [
    "Campaign", "Channel", "Ad Spend ($)", "Conversions", "CPA ($)", "ROAS", "Efficiency"
]
display_table["Ad Spend ($)"] = display_table["Ad Spend ($)"].apply(lambda x: f"${x:,.0f}")
display_table["Conversions"]  = display_table["Conversions"].apply(lambda x: f"{x:,.0f}")
display_table["CPA ($)"]      = display_table["CPA ($)"].apply(lambda x: f"${x:.2f}")
display_table["ROAS"]         = display_table["ROAS"].apply(lambda x: f"{x:.1f}x")

st.dataframe(
    display_table,
    width="stretch",
    hide_index=True,
    column_config={
        "Campaign":    st.column_config.TextColumn(width="medium"),
        "Channel":     st.column_config.TextColumn(width="medium"),
        "Efficiency":  st.column_config.TextColumn(width="small"),
    }
)


# ─────────────────────────────────────────
# SECTION 5 — EFFICIENCY VIEW
# ─────────────────────────────────────────
st.markdown('<p class="section-header">Section 5 — Efficiency View</p>', unsafe_allow_html=True)

eff_channel = (
    filtered.groupby("Channel")
    .agg(Ad_Spend=("Ad_Spend","sum"), Revenue=("Revenue","sum"),
         Conversions=("Conversions","sum"),
         Clicks=("Clicks","sum"), Impressions=("Impressions","sum"))
    .reset_index()
)
eff_channel["ROAS"] = (eff_channel["Revenue"] / eff_channel["Ad_Spend"]).round(2)
eff_channel["CPA"]  = (eff_channel["Ad_Spend"] / eff_channel["Conversions"]).round(2)
eff_channel["CTR"]  = (eff_channel["Clicks"] / eff_channel["Impressions"] * 100).round(2)
eff_channel["CVR"]  = (eff_channel["Conversions"] / eff_channel["Clicks"] * 100).round(2)

fig_eff = go.Figure()
metrics = ["CTR", "CVR", "ROAS"]
colors  = [NAVY, GREEN, "#EF9F27"]

for metric, color in zip(metrics, colors):
    fig_eff.add_trace(go.Bar(
    name=metric,
    x=eff_channel["Channel"],
    y=eff_channel[metric],
    marker_color=color,
    text=eff_channel[metric] if show_data_labels else None,
    texttemplate="%{text:.1f}",
    textposition="outside",
    textfont=dict(color="#1E293B", size=11)
))

fig_eff.update_layout(
    title="Efficiency Metrics by Channel (CTR %, CVR %, ROAS)",
    barmode="group",
    plot_bgcolor="white", paper_bgcolor="white",
    legend=dict(
        orientation="v",
        x=1.02,
        y=1,
        font=dict(color="#1E293B", size=12),
        bgcolor="white",
        bordercolor="#E2E8F0",
        borderwidth=1
    ),
    xaxis=dict(showgrid=False, tickfont=dict(color="#1E293B", size=12)),
    yaxis=dict(showgrid=show_gridlines, gridcolor="#F0F0F0", tickfont=dict(color="#1E293B", size=12)),
    margin=dict(l=0, r=120, t=50, b=0),
    title_font=dict(size=14, color=NAVY),
    font=dict(color="#1E293B")
)
st.plotly_chart(fig_eff, width="stretch")


# ─────────────────────────────────────────
# AI RECOMMENDATIONS — CLAUDE API
# ─────────────────────────────────────────
st.markdown('<p class="section-header">🤖 AI Recommendations & Action Items</p>', unsafe_allow_html=True)

# Build channel breakdown string for the prompt
channel_breakdown = "\n".join([
    f"  - {row['Channel']}: ${row['Ad_Spend']:,.0f} spend | "
    f"{row['Conversions']:,.0f} conversions | "
    f"{row['ROAS']:.1f}x ROAS | "
    f"${row['CPA']:.2f} CPA"
    for _, row in channel_summary.iterrows()
])

# Build campaign breakdown (top 5 by spend)
top_campaigns = campaign_table.nlargest(5, "Ad_Spend")
campaign_breakdown = "\n".join([
    f"  - {row['Campaign']} ({row['Channel']}): "
    f"${row['Ad_Spend']:,.0f} spend | {row['ROAS']:.1f}x ROAS | {row['Efficiency']}"
    for _, row in top_campaigns.iterrows()
])

# Year context
year_context = f"Years selected: {', '.join(selected_years)}"
yoy_context  = ""
if len(selected_years) == 2:
    years_sorted = sorted([int(y) for y in selected_years])
    rev_cur  = filtered[filtered["Year"] == str(years_sorted[-1])]["Revenue"].sum()
    rev_prev = filtered[filtered["Year"] == str(years_sorted[-2])]["Revenue"].sum()
    yoy_pct  = ((rev_cur - rev_prev) / rev_prev * 100) if rev_prev > 0 else 0
    yoy_context = f"Revenue YoY change: {yoy_pct:+.1f}% vs {years_sorted[-2]}"

def get_claude_recommendations():
    """Call Claude API and return 3 action item recommendations."""
    import urllib.request
    import json
    import os

    api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY", ""))
    if not api_key:
        return None, "no_key"

    prompt = f"""You are a senior marketing analyst reviewing a client's campaign performance dashboard.
Based on the data below, provide exactly 3 specific, actionable recommendations the marketing team should implement in the next 30 days to improve overall ROAS and reduce wasted spend.

PERFORMANCE DATA:
{year_context}
{yoy_context}
- Total Ad Spend: ${total_spend:,.0f}
- Total Revenue: ${total_revenue:,.0f}
- Blended ROAS: {blended_roas:.1f}x
- Total Conversions: {total_conversions:,.0f}
- Average CPA: ${avg_cpa:.2f}

CHANNEL BREAKDOWN:
{channel_breakdown}

TOP CAMPAIGNS BY SPEND:
{campaign_breakdown}

FORMAT YOUR RESPONSE EXACTLY LIKE THIS — no intro, no outro, just the 3 items:

1. [ACTION TITLE]
WHAT: [One sentence on exactly what to do]
WHY: [One sentence on why — reference specific numbers from the data]
IMPACT: [Expected outcome — be specific, e.g. "could improve ROAS by ~2x" or "save ~$X/month"]

2. [ACTION TITLE]
WHAT: [One sentence on exactly what to do]
WHY: [One sentence on why — reference specific numbers from the data]
IMPACT: [Expected outcome]

3. [ACTION TITLE]
WHAT: [One sentence on exactly what to do]
WHY: [One sentence on why — reference specific numbers from the data]
IMPACT: [Expected outcome]"""

    payload = json.dumps({
        "model": "claude-sonnet-4-6",
        "max_tokens": 600,
        "messages": [{"role": "user", "content": prompt}]
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=payload,
        headers={
            "Content-Type":      "application/json",
            "x-api-key":         api_key,
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return result["content"][0]["text"], "ok"
    except Exception as e:
        return None, str(e)


def parse_recommendations(text):
    """Parse Claude's response into structured recommendation cards."""
    recs = []
    blocks = [b.strip() for b in text.strip().split("\n\n") if b.strip()]
    current = {}
    for block in blocks:
        lines = block.strip().splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line and line[0].isdigit() and ". " in line:
                if current:
                    recs.append(current)
                current = {"title": line.split(". ", 1)[1].strip(), "what": "", "why": "", "impact": ""}
            elif line.upper().startswith("WHAT:"):
                current["what"] = line[5:].strip()
            elif line.upper().startswith("WHY:"):
                current["why"] = line[4:].strip()
            elif line.upper().startswith("IMPACT:"):
                current["impact"] = line[7:].strip()
    if current:
        recs.append(current)
    return recs


# ── Generate button + caching per filter state ──
filter_key = f"{'-'.join(sorted(selected_years))}|{'-'.join(sorted(selected_channels))}|{'-'.join(sorted(selected_campaigns))}"

if "rec_text" not in st.session_state:
    st.session_state.rec_text    = None
    st.session_state.rec_key     = None
    st.session_state.rec_status  = None

col_btn, col_note = st.columns([1, 3])
with col_btn:
    generate = st.button("⚡ Generate Recommendations", type="primary", width="stretch")
with col_note:
    st.caption("Powered by Claude AI · Updates when you change filters and regenerate · ~5 seconds")

if generate:
    with st.spinner("Analyzing your campaign data..."):
        text, status = get_claude_recommendations()
        st.session_state.rec_text   = text
        st.session_state.rec_key    = filter_key
        st.session_state.rec_status = status

# ── Display recommendations ──
if st.session_state.rec_text and st.session_state.rec_status == "ok":
    recs = parse_recommendations(st.session_state.rec_text)

    if st.session_state.rec_key != filter_key:
        st.info("💡 Filters changed — click **Generate Recommendations** to refresh.")

    if recs:
        icons   = ["🎯", "📈", "💰"]
        colors  = ["#1A3C5E", "#0F6E56", "#7F77DD"]
        cols    = st.columns(len(recs))
        for i, (col, rec) in enumerate(zip(cols, recs)):
            with col:
                st.markdown(f"""
<div style="background:white; border:1px solid #E2E8F0; border-top: 4px solid {colors[i % len(colors)]};
            border-radius:10px; padding:18px; height:100%; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
    <div style="font-size:22px; margin-bottom:8px;">{icons[i % len(icons)]}</div>
    <div style="font-size:13px; font-weight:600; color:{colors[i % len(colors)]};
                margin-bottom:12px; line-height:1.3;">{rec['title']}</div>
    <div style="margin-bottom:8px;">
        <span style="font-size:10px; font-weight:600; color:#6B7A8D;
                     text-transform:uppercase; letter-spacing:0.05em;">What to do</span>
        <p style="font-size:12px; color:#1E293B; margin:3px 0 0; line-height:1.5;">{rec['what']}</p>
    </div>
    <div style="margin-bottom:8px;">
        <span style="font-size:10px; font-weight:600; color:#6B7A8D;
                     text-transform:uppercase; letter-spacing:0.05em;">Why</span>
        <p style="font-size:12px; color:#1E293B; margin:3px 0 0; line-height:1.5;">{rec['why']}</p>
    </div>
    <div style="background:#F0F4F8; border-radius:6px; padding:8px 10px; margin-top:10px;">
        <span style="font-size:10px; font-weight:600; color:#0F6E56;
                     text-transform:uppercase; letter-spacing:0.05em;">Expected impact</span>
        <p style="font-size:12px; color:#0F6E56; margin:3px 0 0; font-weight:500;
                  line-height:1.5;">{rec['impact']}</p>
    </div>
</div>
""", unsafe_allow_html=True)
    else:
        # Fallback: show raw text if parsing fails
        st.markdown(f"""
<div class="insight-box">
    🤖 <strong>AI Recommendations:</strong><br><br>
    {st.session_state.rec_text.replace(chr(10), '<br>')}
</div>
""", unsafe_allow_html=True)

elif st.session_state.rec_status == "no_key":
    st.warning("""
**API key not found.** To enable Claude AI recommendations:

**Running locally:** Create a `.streamlit/secrets.toml` file in your project folder:
```toml
**Deploying to Streamlit Cloud:** Go to your app settings → Secrets → add:
```
ANTHROPIC_API_KEY = "sk-ant-your-key-here"
```
               
""")

elif st.session_state.rec_status and st.session_state.rec_status != "ok":
    st.error(f"API error: {st.session_state.rec_status}. Check your API key and try again.")

elif not generate and not st.session_state.rec_text:
    st.markdown("""
<div style="background:#F8FAFC; border:1px dashed #CBD5E1; border-radius:10px;
            padding:24px; text-align:center; color:#6B7A8D;">
    <div style="font-size:32px; margin-bottom:8px;">🤖</div>
    <div style="font-size:14px; font-weight:500; margin-bottom:4px;">AI Recommendations Ready</div>
    <div style="font-size:12px;">Click <strong>Generate Recommendations</strong> above to get
    3 specific action items based on your current filter selection.</div>
</div>
""", unsafe_allow_html=True)