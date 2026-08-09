"""
Rebtel Telecom — Full BI Dashboard
====================================
Streamlit equivalent of the Looker Studio dashboard spec in looker_dashboard_setup.md.
Covers ALL 5 BigQuery mart tables:
  - mart_fraud_prevention
  - mart_customer_360
  - mart_revenue_analytics
  - mart_network_quality
  - mart_corridor_analytics

Run with:
    python -m streamlit run src/dashboard.py

Charts (matching Looker Studio spec):
  1. Fraud Risk Distribution        (Pie/Donut)
  2. Customer Segments              (Bar)
  3. Customer Health Score          (Column + Breakdown)
  4. Revenue by Subscription Plan   (Bar)
  5. Top Remittance Corridors       (Table + Heatmap)
  6. Network SLA Scorecards         (4 KPI Cards)
  7. Churn Risk Distribution        (Donut)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rebtel Telecom — Business Intelligence Dashboard",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ID = "telecom-project-504210"
DATASET    = "rebtel_analytics"

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117;
    }

    /* ── Main header ── */
    .dash-header {
        background: linear-gradient(135deg, #0d1117 0%, #161b27 50%, #0d1117 100%);
        border-bottom: 1px solid #21262d;
        padding: 24px 0 16px 0;
        margin-bottom: 8px;
    }
    .dash-title {
        font-size: 2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #bc8cff, #ff7b72);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
    }
    .dash-subtitle {
        font-size: 0.9rem;
        color: #8b949e;
        margin: 4px 0 0 0;
    }

    /* ── KPI Scorecard cards ── */
    .kpi-card {
        background: linear-gradient(145deg, #161b27 0%, #1c2333 100%);
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 22px 18px;
        text-align: center;
        transition: border-color 0.25s ease, transform 0.25s ease;
        height: 100%;
    }
    .kpi-card:hover {
        border-color: #58a6ff;
        transform: translateY(-2px);
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 700;
        color: #58a6ff;
        line-height: 1.1;
    }
    .kpi-value.green  { color: #3fb950; }
    .kpi-value.yellow { color: #d29922; }
    .kpi-value.red    { color: #f85149; }
    .kpi-value.purple { color: #bc8cff; }
    .kpi-label {
        font-size: 0.78rem;
        color: #8b949e;
        font-weight: 500;
        margin-top: 6px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .kpi-target {
        font-size: 0.72rem;
        color: #484f58;
        margin-top: 4px;
    }

    /* ── Section headers ── */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: #c9d1d9;
        border-left: 3px solid #58a6ff;
        padding-left: 10px;
        margin: 20px 0 12px 0;
    }

    /* ── Chart containers ── */
    .chart-card {
        background: #161b27;
        border: 1px solid #21262d;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: #161b27 !important;
        border-right: 1px solid #21262d !important;
    }
    [data-testid="stSidebar"] .stMarkdown p { color: #8b949e; }
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: #c9d1d9; }

    /* ── Tables ── */
    .stDataFrame { border-radius: 10px; overflow: hidden; }

    /* ── Risk badges ── */
    .badge-critical { color: #f85149; font-weight: 700; }
    .badge-high     { color: #ff9f43; font-weight: 700; }
    .badge-medium   { color: #d29922; font-weight: 700; }
    .badge-low      { color: #3fb950; font-weight: 700; }
    .badge-safe     { color: #58a6ff; font-weight: 700; }

    /* ── Divider ── */
    hr { border-color: #21262d !important; }

    /* ── Streamlit metric override ── */
    [data-testid="metric-container"] {
        background: #161b27;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ── Helper: BQ Client ─────────────────────────────────────────────────────────
@st.cache_resource
def get_bq_client():
    return bigquery.Client(project=PROJECT_ID)

# ── Data Loaders ──────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_fraud_prevention():
    client = get_bq_client()
    sql = f"""
        SELECT user_id, fraud_risk_level,
               total_calls, failed_calls, call_failure_rate_pct,
               total_transfers, total_transfer_usd, fraud_transfers,
               support_tickets, fraud_tickets
        FROM `{PROJECT_ID}.{DATASET}.mart_fraud_prevention`
        ORDER BY fraud_risk_level, COALESCE(total_transfer_usd, 0) DESC
    """
    return client.query(sql).to_dataframe()

@st.cache_data(ttl=300)
def load_customer_360():
    client = get_bq_client()
    sql = f"""
        SELECT user_id, customer_segment, customer_health_score, churn_risk
        FROM `{PROJECT_ID}.{DATASET}.mart_customer_360`
    """
    return client.query(sql).to_dataframe()

@st.cache_data(ttl=300)
def load_revenue_analytics():
    client = get_bq_client()
    sql = f"""
        SELECT user_id, total_revenue, estimated_ltv
        FROM `{PROJECT_ID}.{DATASET}.mart_revenue_analytics`
    """
    return client.query(sql).to_dataframe()

@st.cache_data(ttl=300)
def load_payments_plan():
    """Join revenue mart with payments staging to get subscription plan."""
    client = get_bq_client()
    sql = f"""
        SELECT
            p.latest_subscription_plan,
            COUNT(r.user_id) AS users,
            ROUND(SUM(r.total_revenue), 2)  AS total_revenue,
            ROUND(AVG(r.estimated_ltv), 2)  AS avg_ltv
        FROM `{PROJECT_ID}.{DATASET}.mart_revenue_analytics` r
        LEFT JOIN `{PROJECT_ID}.{DATASET}.fct_payments` p ON r.user_id = p.user_id
        GROUP BY p.latest_subscription_plan
        ORDER BY total_revenue DESC
    """
    try:
        return client.query(sql).to_dataframe()
    except Exception:
        # Fallback — aggregate from revenue mart directly
        sql_fallback = f"""
            SELECT
                COALESCE(subscription_plan, 'Unknown') AS latest_subscription_plan,
                COUNT(user_id) AS users,
                ROUND(SUM(total_revenue), 2) AS total_revenue,
                ROUND(AVG(estimated_ltv), 2)  AS avg_ltv
            FROM `{PROJECT_ID}.{DATASET}.mart_revenue_analytics`
            GROUP BY subscription_plan
            ORDER BY total_revenue DESC
        """
        return client.query(sql_fallback).to_dataframe()

@st.cache_data(ttl=300)
def load_network_quality():
    client = get_bq_client()
    sql = f"""
        SELECT total_calls, connection_success_rate_pct,
               avg_mos_score, avg_delivery_rate_pct, sla_quality_met_pct,
               sla_connection_met_pct
        FROM `{PROJECT_ID}.{DATASET}.mart_network_quality`
        LIMIT 1
    """
    return client.query(sql).to_dataframe()

@st.cache_data(ttl=300)
def load_corridor_analytics():
    client = get_bq_client()
    sql = f"""
        SELECT corridor, corridor_risk, total_transfers,
               total_volume_usd, fraud_rate_pct
        FROM `{PROJECT_ID}.{DATASET}.mart_corridor_analytics`
        ORDER BY total_volume_usd DESC
        LIMIT 20
    """
    return client.query(sql).to_dataframe()

# ── Color palettes ────────────────────────────────────────────────────────────
FRAUD_COLORS = {
    "CRITICAL":       "#f85149",
    "HIGH_RISK":      "#ff9f43",
    "HIGH_RISK_FRAUD":"#ff9f43",
    "MEDIUM_RISK":    "#d29922",
    "LOW_RISK":       "#3fb950",
    "SAFE":           "#58a6ff",
}
CHURN_COLORS = {
    "HIGH":   "#f85149",
    "MEDIUM": "#d29922",
    "LOW":    "#3fb950",
}
CORRIDOR_RISK_COLORS = {
    "HIGH":   "#f85149",
    "MEDIUM": "#d29922",
    "LOW":    "#3fb950",
}
SEGMENT_COLORS = {
    "PLATINUM": "#bc8cff",
    "GOLD":     "#d29922",
    "SILVER":   "#8b949e",
    "STANDARD": "#58a6ff",
    "AT_RISK":  "#f85149",
}
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c9d1d9", family="Inter"),
    # NOTE: legend is intentionally NOT set here — each chart sets it explicitly
    # to avoid 'multiple values for keyword argument legend' on update_layout(**PLOTLY_LAYOUT, legend=...)
    margin=dict(t=30, b=10, l=0, r=0),
    hoverlabel=dict(bgcolor="#21262d", font_color="#c9d1d9", bordercolor="#30363d"),
)
# Base legend style — merge this manually into charts that need it
_LEGEND = dict(font=dict(color="#c9d1d9"), bgcolor="rgba(0,0,0,0)")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 20px 0;">
        <div style="font-size:1.6rem; font-weight:800;
                    background: linear-gradient(90deg,#58a6ff,#bc8cff);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    background-clip:text;">
            📡 REBTEL
        </div>
        <div style="font-size:0.75rem; color:#484f58; margin-top:2px;">
            Business Intelligence Dashboard
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🔍 Filters")

    seg_options = ["ALL", "PLATINUM", "GOLD", "SILVER", "STANDARD", "AT_RISK"]
    seg_filter = st.selectbox("Customer Segment", seg_options, index=0)

    fraud_options = ["HIGH_RISK_FRAUD", "MEDIUM_RISK", "LOW_RISK"]
    fraud_filter = st.multiselect(
        "Fraud Risk Level",
        options=fraud_options,
        default=fraud_options,
    )

    churn_options = ["ALL", "HIGH", "MEDIUM", "LOW"]
    churn_filter = st.selectbox("Churn Risk", churn_options, index=0)

    corridor_risk_options = ["ALL", "HIGH", "MEDIUM", "LOW"]
    corridor_filter = st.selectbox("Corridor Risk", corridor_risk_options, index=0)

    st.markdown("---")
    st.markdown("**🗄️ BigQuery Source**")
    st.markdown(f"`{PROJECT_ID}`")
    st.markdown(f"Dataset: `{DATASET}`")
    st.markdown("---")
    st.markdown("""
    **Tables Connected**
    - `mart_fraud_prevention`
    - `mart_customer_360`
    - `mart_revenue_analytics`
    - `mart_network_quality`
    - `mart_corridor_analytics`
    """)

# ══════════════════════════════════════════════════════════════════════════════
# MAIN PAGE HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="dash-header">
  <p class="dash-title">📡 Rebtel Telecom — Business Intelligence Dashboard</p>
  <p class="dash-subtitle">
    Real-time analytics powered by GCP BigQuery + dbt | Project: telecom-project-504210
  </p>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LOAD ALL DATA
# ══════════════════════════════════════════════════════════════════════════════
with st.spinner("🔄 Loading live data from BigQuery..."):
    try:
        df_fraud   = load_fraud_prevention()
        df_cust    = load_customer_360()
        df_rev     = load_revenue_analytics()
        df_pay     = load_payments_plan()
        df_network = load_network_quality()
        df_corridor= load_corridor_analytics()
        data_ok    = True
    except Exception as e:
        data_ok = False
        st.error(f"⚠️ Failed to connect to BigQuery: `{e}`")
        st.info("Make sure the full data pipeline (Steps 1–4) has been executed, "
                "and GCP credentials are configured correctly.")
        st.stop()

# ── Apply filters ─────────────────────────────────────────────────────────────
df_fraud_f = df_fraud[df_fraud["fraud_risk_level"].isin(fraud_filter)] if fraud_filter else df_fraud

df_cust_f = df_cust.copy()
if seg_filter != "ALL":
    df_cust_f = df_cust_f[df_cust_f["customer_segment"] == seg_filter]
if churn_filter != "ALL":
    df_cust_f = df_cust_f[df_cust_f["churn_risk"] == churn_filter]

df_corridor_f = df_corridor.copy()
if corridor_filter != "ALL":
    df_corridor_f = df_corridor_f[df_corridor_f["corridor_risk"] == corridor_filter]

# ══════════════════════════════════════════════════════════════════════════════
# ROW 0 — NETWORK SLA SCORECARDS (Chart 6 from spec)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">📶 Network SLA Scorecards</div>', unsafe_allow_html=True)

def _val(df, col, fmt="{:.2f}"):
    if df.empty or col not in df.columns:
        return "N/A"
    v = df[col].iloc[0]
    try:
        return fmt.format(float(v))
    except Exception:
        return str(v)

conn_rate  = _val(df_network, "connection_success_rate_pct", "{:.2f}%")
mos_score  = _val(df_network, "avg_mos_score",               "{:.2f}")
sla_qual   = _val(df_network, "sla_quality_met_pct",         "{:.2f}%")
del_rate   = _val(df_network, "avg_delivery_rate_pct",       "{:.2f}%")

kpi1, kpi2, kpi3, kpi4 = st.columns(4)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-value">{conn_rate}</div>
      <div class="kpi-label">Connection Success Rate</div>
      <div class="kpi-target">Target: 98%</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-value purple">{mos_score}</div>
      <div class="kpi-label">Avg MOS Score</div>
      <div class="kpi-target">Target: 4.0</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-value green">{sla_qual}</div>
      <div class="kpi-label">SLA Quality Met</div>
      <div class="kpi-target">Target: 95%</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    st.markdown(f"""
    <div class="kpi-card">
      <div class="kpi-value yellow">{del_rate}</div>
      <div class="kpi-label">Avg Delivery Rate</div>
      <div class="kpi-target">Target: 95%</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Secondary KPI row from fraud / customer data ──────────────────────────────
total_users   = len(df_fraud)
high_risk_cnt = len(df_fraud[df_fraud["fraud_risk_level"] == "HIGH_RISK_FRAUD"])
total_calls   = int(df_fraud["total_calls"].sum())   if "total_calls" in df_fraud.columns else 0
total_usd     = round(df_fraud["total_transfer_usd"].sum(), 2) if "total_transfer_usd" in df_fraud.columns else 0
total_revenue = round(df_rev["total_revenue"].sum(), 2) if not df_rev.empty and "total_revenue" in df_rev.columns else 0

m1, m2, m3, m4, m5 = st.columns(5)
with m1: st.metric("👥 Total Users",        f"{total_users:,}")
with m2: st.metric("🔴 High Risk Users",    f"{high_risk_cnt:,}",
                   delta=f"{high_risk_cnt/max(total_users,1)*100:.1f}%",
                   delta_color="inverse")
with m3: st.metric("📞 Total Calls",        f"{total_calls:,}")
with m4: st.metric("💸 Total Transferred",  f"${total_usd:,.0f}")
with m5: st.metric("💰 Total Revenue",      f"${total_revenue:,.0f}")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ROW 1 — FRAUD RISK PIE + CUSTOMER SEGMENTS BAR (Charts 1 & 2)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🎯 Fraud Risk &amp; Customer Segments</div>',
            unsafe_allow_html=True)

col_a, col_b = st.columns([1, 1.4])

# ── Chart 1: Fraud Risk Distribution (Donut) ──────────────────────────────────
with col_a:
    st.markdown("**📊 Fraud Risk Distribution**")
    risk_counts = df_fraud["fraud_risk_level"].value_counts().reset_index()
    risk_counts.columns = ["Risk Level", "Users"]
    color_seq = [FRAUD_COLORS.get(r, "#58a6ff") for r in risk_counts["Risk Level"]]

    fig_pie = go.Figure(go.Pie(
        labels=risk_counts["Risk Level"],
        values=risk_counts["Users"],
        hole=0.50,
        marker=dict(colors=color_seq,
                    line=dict(color="#0d1117", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#c9d1d9", size=12),
        hovertemplate="<b>%{label}</b><br>Users: %{value:,}<br>Share: %{percent}<extra></extra>",
    ))
    fig_pie.update_layout(
        **{**PLOTLY_LAYOUT,
           "legend": dict(orientation="h", y=-0.15, font=dict(color="#c9d1d9"))},
        height=300,
        showlegend=True,
        annotations=[dict(text=f"<b>{total_users}</b><br>Users",
                          x=0.5, y=0.5, font_size=16,
                          font_color="#c9d1d9", showarrow=False)],
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Chart 2: Customer Segments Bar ────────────────────────────────────────────
with col_b:
    st.markdown("**📊 Customer Segments**")
    if not df_cust.empty and "customer_segment" in df_cust.columns:
        seg_agg = (
            df_cust.groupby("customer_segment")
            .agg(users=("user_id", "count"),
                 avg_health=("customer_health_score", "mean"))
            .reset_index()
            .sort_values("users", ascending=False)
        )
        seg_agg["avg_health"] = seg_agg["avg_health"].round(1)
        color_seq_seg = [SEGMENT_COLORS.get(s, "#58a6ff") for s in seg_agg["customer_segment"]]

        fig_seg = go.Figure()
        fig_seg.add_trace(go.Bar(
            x=seg_agg["customer_segment"],
            y=seg_agg["users"],
            name="Users",
            marker=dict(color=color_seq_seg, opacity=0.85),
            text=seg_agg["users"],
            textposition="outside",
            textfont=dict(color="#c9d1d9"),
            hovertemplate="<b>%{x}</b><br>Users: %{y:,}<br>Avg Health: %{customdata:.1f}<extra></extra>",
            customdata=seg_agg["avg_health"],
        ))
        fig_seg.update_layout(
            **PLOTLY_LAYOUT,
            height=300,
            xaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d"),
            yaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d", title="Users"),
            bargap=0.25,
        )
        st.plotly_chart(fig_seg, use_container_width=True)
    else:
        st.info("No customer segment data available.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ROW 2 — HEALTH SCORE BY SEGMENT + CHURN DONUT (Charts 3 & 7)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">💚 Customer Health &amp; Churn Risk</div>',
            unsafe_allow_html=True)

col_c, col_d = st.columns([1.6, 1])

# ── Chart 3: Customer Health Score Distribution ────────────────────────────────
with col_c:
    st.markdown("**📊 Customer Health Score by Segment & Churn Risk**")
    if not df_cust.empty and "customer_segment" in df_cust.columns and "churn_risk" in df_cust.columns:
        health_agg = (
            df_cust_f.groupby(["customer_segment", "churn_risk"])
            .agg(avg_health=("customer_health_score", "mean"),
                 users=("user_id", "count"))
            .reset_index()
        )
        health_agg["avg_health"] = health_agg["avg_health"].round(1)

        fig_health = px.bar(
            health_agg,
            x="customer_segment",
            y="avg_health",
            color="churn_risk",
            barmode="group",
            color_discrete_map=CHURN_COLORS,
            labels={"avg_health": "Avg Health Score", "customer_segment": "Segment",
                    "churn_risk": "Churn Risk"},
            text_auto=".1f",
        )
        fig_health.update_layout(
            **{**PLOTLY_LAYOUT,
               "legend": dict(orientation="h", y=-0.25, font=dict(color="#c9d1d9"))},
            height=300,
            xaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d"),
            yaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d",
                       title="Avg Health Score"),
        )
        fig_health.update_traces(textfont_color="#c9d1d9")
        st.plotly_chart(fig_health, use_container_width=True)
    else:
        st.info("No customer health data available.")

# ── Chart 7: Churn Risk Donut ──────────────────────────────────────────────────
with col_d:
    st.markdown("**📊 Churn Risk Distribution**")
    if not df_cust.empty and "churn_risk" in df_cust.columns:
        churn_counts = df_cust["churn_risk"].value_counts().reset_index()
        churn_counts.columns = ["Churn Risk", "Users"]
        churn_colors_list = [CHURN_COLORS.get(r, "#58a6ff") for r in churn_counts["Churn Risk"]]

        fig_churn = go.Figure(go.Pie(
            labels=churn_counts["Churn Risk"],
            values=churn_counts["Users"],
            hole=0.50,
            marker=dict(colors=churn_colors_list,
                        line=dict(color="#0d1117", width=2)),
            textinfo="label+percent",
            textfont=dict(color="#c9d1d9", size=12),
            hovertemplate="<b>%{label}</b><br>Users: %{value:,}<br>%{percent}<extra></extra>",
        ))
        fig_churn.update_layout(
            **{**PLOTLY_LAYOUT,
               "legend": dict(orientation="h", y=-0.15, font=dict(color="#c9d1d9"))},
            height=300,
            showlegend=True,
            annotations=[dict(text="<b>Churn</b><br>Risk",
                              x=0.5, y=0.5, font_size=13,
                              font_color="#c9d1d9", showarrow=False)],
        )
        st.plotly_chart(fig_churn, use_container_width=True)
    else:
        st.info("No churn data available.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ROW 3 — REVENUE BY PLAN + CALL FAILURE HIGH RISK (Chart 4 + Bonus)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">💰 Revenue Analytics</div>', unsafe_allow_html=True)

col_e, col_f = st.columns(2)

# ── Chart 4: Revenue by Subscription Plan ─────────────────────────────────────
with col_e:
    st.markdown("**📊 Revenue by Subscription Plan**")
    if not df_pay.empty and "latest_subscription_plan" in df_pay.columns:
        df_pay_clean = df_pay.dropna(subset=["latest_subscription_plan"])
        if not df_pay_clean.empty:
            fig_rev = go.Figure()
            fig_rev.add_trace(go.Bar(
                x=df_pay_clean["latest_subscription_plan"],
                y=df_pay_clean["total_revenue"],
                name="Total Revenue",
                marker=dict(color="#58a6ff", opacity=0.85),
                text=df_pay_clean["total_revenue"].apply(lambda v: f"${v:,.0f}"),
                textposition="outside",
                textfont=dict(color="#c9d1d9"),
                hovertemplate="<b>%{x}</b><br>Revenue: $%{y:,.2f}<extra></extra>",
            ))
            fig_rev.add_trace(go.Scatter(
                x=df_pay_clean["latest_subscription_plan"],
                y=df_pay_clean["avg_ltv"],
                name="Avg LTV",
                mode="lines+markers",
                line=dict(color="#bc8cff", width=2),
                marker=dict(size=8, color="#bc8cff"),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>Avg LTV: $%{y:,.2f}<extra></extra>",
            ))
            fig_rev.update_layout(
                **{**PLOTLY_LAYOUT,
                   "legend": dict(orientation="h", y=-0.25, font=dict(color="#c9d1d9"))},
                height=320,
                xaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d"),
                yaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d",
                           title="Total Revenue ($)"),
                yaxis2=dict(overlaying="y", side="right",
                            tickfont=dict(color="#bc8cff"),
                            title="Avg LTV ($)",
                            showgrid=False),
                bargap=0.3,
            )
            st.plotly_chart(fig_rev, use_container_width=True)
        else:
            st.info("No revenue plan data available.")
    else:
        # Fallback — show revenue mart aggregated by LTV bucket
        if not df_rev.empty:
            df_rev["ltv_bucket"] = pd.cut(
                df_rev["estimated_ltv"].fillna(0),
                bins=[0, 50, 150, 300, float("inf")],
                labels=["<$50", "$50–150", "$150–300", "$300+"]
            )
            rev_agg = df_rev.groupby("ltv_bucket").agg(
                users=("user_id", "count"),
                total_revenue=("total_revenue", "sum")
            ).reset_index()
            fig_rev2 = px.bar(
                rev_agg, x="ltv_bucket", y="total_revenue",
                color="ltv_bucket",
                labels={"total_revenue": "Total Revenue ($)", "ltv_bucket": "LTV Bucket"},
                color_discrete_sequence=["#3fb950", "#58a6ff", "#bc8cff", "#f85149"],
            )
            fig_rev2.update_layout(**PLOTLY_LAYOUT, height=320,
                                   xaxis=dict(gridcolor="#21262d"),
                                   yaxis=dict(gridcolor="#21262d"))
            st.plotly_chart(fig_rev2, use_container_width=True)
        else:
            st.info("No revenue data available.")

# ── Bonus: Call Failure Rate (High Risk Users) ────────────────────────────────
with col_f:
    st.markdown("**📊 Call Failure Rate — Top 15 High-Risk Users**")
    df_high = df_fraud[df_fraud["fraud_risk_level"] == "HIGH_RISK_FRAUD"].nlargest(
        15, "call_failure_rate_pct"
    )
    if not df_high.empty:
        fig_fail = px.bar(
            df_high, x="user_id", y="call_failure_rate_pct",
            color="call_failure_rate_pct",
            color_continuous_scale=["#d29922", "#ff9f43", "#f85149"],
            labels={"call_failure_rate_pct": "Failure Rate (%)", "user_id": "User"},
            text_auto=".1f",
        )
        fig_fail.update_layout(
            **PLOTLY_LAYOUT,
            height=320,
            xaxis=dict(tickangle=45, tickfont=dict(color="#c9d1d9"), gridcolor="#21262d"),
            yaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d",
                       title="Call Failure Rate (%)"),
            coloraxis_showscale=False,
        )
        fig_fail.update_traces(textfont_color="#c9d1d9")
        st.plotly_chart(fig_fail, use_container_width=True)
    else:
        st.info("No HIGH_RISK_FRAUD users in current filter.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ROW 4 — TOP CORRIDORS TABLE (Chart 5)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🌍 Top Money Transfer Corridors</div>',
            unsafe_allow_html=True)

if not df_corridor_f.empty:
    col_g, col_h = st.columns([2, 1])

    with col_g:
        st.markdown("**📊 Top Corridors — Volume & Fraud Rate**")
        # Heatmap-style scatter: size = volume, color = fraud_rate
        fig_corr = px.scatter(
            df_corridor_f,
            x="corridor",
            y="total_volume_usd",
            size="total_transfers",
            color="fraud_rate_pct",
            color_continuous_scale=["#3fb950", "#d29922", "#f85149"],
            labels={
                "corridor":         "Corridor",
                "total_volume_usd": "Volume (USD)",
                "total_transfers":  "Transfer Count",
                "fraud_rate_pct":   "Fraud Rate %",
            },
            hover_data={"corridor": True, "total_volume_usd": ":,.0f",
                        "total_transfers": True, "fraud_rate_pct": ":.2f"},
        )
        fig_corr.update_layout(
            **PLOTLY_LAYOUT,
            height=360,
            xaxis=dict(tickangle=45, tickfont=dict(color="#c9d1d9", size=10),
                       gridcolor="#21262d"),
            yaxis=dict(tickfont=dict(color="#c9d1d9"), gridcolor="#21262d",
                       title="Total Volume (USD)"),
            coloraxis_colorbar=dict(
                title=dict(text="Fraud %", font=dict(color="#c9d1d9")),
                tickfont=dict(color="#c9d1d9"),
            ),
        )
        st.plotly_chart(fig_corr, use_container_width=True)

    with col_h:
        st.markdown("**📋 Corridor Detail Table**")
        display_corr = df_corridor_f[
            ["corridor", "corridor_risk", "total_transfers",
             "total_volume_usd", "fraud_rate_pct"]
        ].rename(columns={
            "corridor":         "Corridor",
            "corridor_risk":    "Risk",
            "total_transfers":  "Transfers",
            "total_volume_usd": "Volume (USD)",
            "fraud_rate_pct":   "Fraud %",
        })
        display_corr["Volume (USD)"] = display_corr["Volume (USD)"].apply(
            lambda v: f"${v:,.0f}" if pd.notna(v) else "N/A"
        )
        display_corr["Fraud %"] = display_corr["Fraud %"].apply(
            lambda v: f"{v:.2f}%" if pd.notna(v) else "N/A"
        )
        st.dataframe(display_corr, use_container_width=True, height=360, hide_index=True)
else:
    st.info("No corridor data available for the selected filter.")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# ROW 5 — FRAUD DETAIL TABLE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="section-header">🔎 Detailed Fraud Risk Report</div>',
            unsafe_allow_html=True)

display_cols = [
    "user_id", "fraud_risk_level", "total_calls", "call_failure_rate_pct",
    "total_transfer_usd", "fraud_transfers", "support_tickets", "fraud_tickets",
]
available_cols = [c for c in display_cols if c in df_fraud_f.columns]
st.dataframe(
    df_fraud_f[available_cols].rename(columns={
        "user_id":               "User ID",
        "fraud_risk_level":      "Risk Level",
        "total_calls":           "Total Calls",
        "call_failure_rate_pct": "Call Fail %",
        "total_transfer_usd":    "Transfer USD",
        "fraud_transfers":       "Fraud Transfers",
        "support_tickets":       "Tickets",
        "fraud_tickets":         "Fraud Tickets",
    }),
    use_container_width=True,
    height=380,
    hide_index=True,
)

# ══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#484f58; font-size:0.8rem; padding: 8px 0 16px 0;">
  📡 Rebtel Telecom Business Intelligence — Powered by
  <span style="color:#58a6ff;">GCP BigQuery</span> +
  <span style="color:#bc8cff;">dbt</span> +
  <span style="color:#3fb950;">Streamlit</span> +
  <span style="color:#d29922;">Plotly</span>
  &nbsp;|&nbsp; Data refreshes every 5 minutes
</div>
""", unsafe_allow_html=True)
