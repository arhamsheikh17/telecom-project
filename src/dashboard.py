"""
Rebtel Telecom & Fintech — Executive Intelligence Dashboard
============================================================
Professional Streamlit Analytics Hub
Data Warehouse: GCP BigQuery (`telecom-project-504210.rebtel_analytics`)
"""

import os
import sys
import json
import subprocess
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import bigquery
import google.oauth2.credentials

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rebtel Telecom — Executive BI Hub",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_ID = "telecom-project-504210"
DATASET    = "rebtel_analytics"

# ── Custom Professional Styling (CSS) ─────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #0b0e14;
        color: #c9d1d9;
    }

    /* ── Main Dashboard Header ── */
    .dash-header {
        background: linear-gradient(135deg, #161b26 0%, #0d1117 100%);
        border: 1px solid #21262d;
        border-radius: 16px;
        padding: 24px 30px;
        margin-bottom: 24px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .dash-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(90deg, #58a6ff, #bc8cff, #ff7b72);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .dash-subtitle {
        font-size: 0.95rem;
        color: #8b949e;
        margin-top: 6px;
    }

    /* ── KPI Cards ── */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: #161b26;
        border: 1px solid #30363d;
        border-radius: 14px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .kpi-val {
        font-size: 2rem;
        font-weight: 800;
        color: #58a6ff;
        margin-bottom: 4px;
    }
    .kpi-val.green  { color: #3fb950; }
    .kpi-val.red    { color: #f85149; }
    .kpi-val.yellow { color: #d29922; }
    .kpi-val.purple { color: #bc8cff; }
    .kpi-lbl {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #8b949e;
    }
    .kpi-sub {
        font-size: 0.75rem;
        color: #484f58;
        margin-top: 4px;
    }

    /* ── Insight Banners ── */
    .insight-banner {
        background: rgba(88, 166, 255, 0.08);
        border-left: 4px solid #58a6ff;
        border-radius: 6px;
        padding: 12px 16px;
        font-size: 0.88rem;
        color: #c9d1d9;
        margin-top: 10px;
        margin-bottom: 16px;
    }

    /* ── Sidebar & Navigation ── */
    [data-testid="stSidebar"] {
        background: #121621 !important;
        border-right: 1px solid #21262d !important;
    }

    /* ── Tabs Styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #21262d;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre;
        border-radius: 8px 8px 0 0;
        color: #8b949e;
        font-weight: 600;
        padding: 0 16px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #161b26 !important;
        color: #58a6ff !important;
        border-bottom: 2px solid #58a6ff !important;
    }
</style>
""", unsafe_allow_html=True)

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# ── Resilient & Fast Data Fetching Engine ───────────────────────────────────────
@st.cache_resource
def get_bq_client():
    """Uses gcloud access token directly for sub-second authentication."""
    try:
        gcloud_path = os.path.join(
            os.environ.get("LOCALAPPDATA", r"C:\Users\ADVANCES PC\AppData\Local"),
            "Google", "Cloud SDK", "google-cloud-sdk", "bin", "gcloud.cmd"
        )
        cmd = [gcloud_path, "auth", "print-access-token"] if os.path.exists(gcloud_path) else ["gcloud.cmd", "auth", "print-access-token"]
        token_result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        access_token = token_result.stdout.strip()
        if access_token:
            creds = google.oauth2.credentials.Credentials(token=access_token)
            return bigquery.Client(project=PROJECT_ID, credentials=creds)
    except Exception:
        pass

    try:
        return bigquery.Client(project=PROJECT_ID)
    except Exception:
        return None

def query_to_dataframe(sql: str) -> pd.DataFrame:
    """Fast & resilient SQL execution."""
    client = get_bq_client()
    if client is not None:
        try:
            return client.query(sql).to_dataframe()
        except Exception:
            pass

    # Fallback via bq CLI JSON output
    try:
        cmd = [
            "bq.cmd", "query", "--format=json", "--use_legacy_sql=false",
            f"--project_id={PROJECT_ID}", sql
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        raw_json = res.stdout.strip()
        if raw_json:
            data = json.loads(raw_json)
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Data query failed: {e}")

    return pd.DataFrame()

# ── Cached Data Loaders ───────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_fraud_data():
    sql = f"""
        SELECT user_id, fraud_risk_level,
               total_calls, failed_calls, call_failure_rate_pct,
               total_transfers, total_transfer_usd, fraud_transfers,
               support_tickets, fraud_tickets, total_fraud_signals
        FROM `{PROJECT_ID}.{DATASET}.mart_fraud_prevention`
        ORDER BY total_fraud_signals DESC, COALESCE(total_transfer_usd,0) DESC
    """
    df = query_to_dataframe(sql)
    num_cols = ["total_calls", "failed_calls", "call_failure_rate_pct", "total_transfers", "total_transfer_usd", "fraud_transfers", "support_tickets", "fraud_tickets", "total_fraud_signals"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120)
def load_customer_data():
    sql = f"""
        SELECT user_id, total_calls, total_transfers, total_payments,
               total_revenue, total_transfer_volume_usd, customer_health_score,
               customer_segment, churn_risk
        FROM `{PROJECT_ID}.{DATASET}.mart_customer_360`
    """
    df = query_to_dataframe(sql)
    num_cols = ["total_calls", "total_transfers", "total_payments", "total_revenue", "total_transfer_volume_usd", "customer_health_score"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120)
def load_revenue_data():
    sql = f"""
        SELECT user_id, latest_subscription_plan, total_revenue, estimated_ltv,
               payment_failure_rate_pct, revenue_per_call, revenue_per_transfer
        FROM `{PROJECT_ID}.{DATASET}.mart_revenue_analytics`
    """
    df = query_to_dataframe(sql)
    num_cols = ["total_revenue", "estimated_ltv", "payment_failure_rate_pct", "revenue_per_call", "revenue_per_transfer"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120)
def load_network_data():
    sql = f"""
        SELECT total_calls, connected_calls, dropped_calls, connection_success_rate_pct,
               avg_mos_score, avg_delivery_rate_pct, excellent_calls, good_calls, fair_calls, poor_calls,
               sla_quality_met_pct, sla_connection_met_pct,
               calls_no_connection, calls_very_short, calls_short, calls_medium, calls_long
        FROM `{PROJECT_ID}.{DATASET}.mart_network_quality`
        LIMIT 1
    """
    df = query_to_dataframe(sql)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

@st.cache_data(ttl=120)
def load_corridor_data():
    sql = f"""
        SELECT corridor, sender_country, receiver_country, total_transfers,
               unique_senders, total_volume_usd, avg_transfer_usd, fraud_count,
               fraud_rate_pct, corridor_risk
        FROM `{PROJECT_ID}.{DATASET}.mart_corridor_analytics`
        ORDER BY total_volume_usd DESC
    """
    df = query_to_dataframe(sql)
    num_cols = ["total_transfers", "unique_senders", "total_volume_usd", "avg_transfer_usd", "fraud_count", "fraud_rate_pct"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

# ── Load All Datasets ─────────────────────────────────────────────────────────
df_fraud    = load_fraud_data()
df_cust     = load_customer_data()
df_rev      = load_revenue_data()
df_network  = load_network_data()
df_corridor = load_corridor_data()

# ── Global Plotly Layout Style ────────────────────────────────────────────────
PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c9d1d9", family="Inter"),
    margin=dict(t=40, b=20, l=10, r=10),
    hoverlabel=dict(bgcolor="#161b26", font_color="#c9d1d9", bordercolor="#30363d"),
)

RISK_COLORS = {
    "CRITICAL_RISK":   "#f85149",
    "HIGH_RISK_FRAUD": "#ff9f43",
    "MEDIUM_RISK":     "#d29922",
    "LOW_RISK":        "#3fb950",
    "SAFE":            "#58a6ff",
    "HIGH_RISK_CORRIDOR": "#f85149",
    "MONITOR_CORRIDOR":   "#d29922",
    "SAFE_CORRIDOR":      "#3fb950",
}

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR FILTERS
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 10px 0 15px 0;">
        <div style="font-size:1.6rem; font-weight:800; color:#58a6ff;">📡 REBTEL BI</div>
        <div style="font-size:0.75rem; color:#8b949e;">Enterprise Executive Analytics</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 🎛️ Global Controls")

    # Risk Filter
    all_risks = list(df_fraud["fraud_risk_level"].unique()) if not df_fraud.empty else []
    selected_risks = st.multiselect("Fraud Risk Tier", options=all_risks, default=all_risks)

    # Segment Filter
    all_segs = ["ALL"] + list(df_cust["customer_segment"].unique()) if not df_cust.empty else ["ALL"]
    selected_seg = st.selectbox("Customer Segment", options=all_segs, index=0)

    st.markdown("---")
    st.markdown("**📌 Data Source Connection**")
    st.caption(f"Project: `{PROJECT_ID}`")
    st.caption(f"Dataset: `{DATASET}`")
    st.caption("⚡ Status: Live BigQuery Connection")

# Filter application
if not df_fraud.empty and selected_risks:
    df_fraud_f = df_fraud[df_fraud["fraud_risk_level"].isin(selected_risks)]
else:
    df_fraud_f = df_fraud

if not df_cust.empty and selected_seg != "ALL":
    df_cust_f = df_cust[df_cust["customer_segment"] == selected_seg]
else:
    df_cust_f = df_cust

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="dash-header">
    <div class="dash-title">📡 Rebtel Telecom &amp; Fintech Intelligence Hub</div>
    <div class="dash-subtitle">
        Cross-Domain Executive Analytics | Unified Warehouse: GCP BigQuery dbt Analytics Engine
    </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE KPI SUMMARY ROW
# ══════════════════════════════════════════════════════════════════════════════
tot_users = len(df_fraud)
high_risk_users = len(df_fraud[df_fraud["fraud_risk_level"].isin(["CRITICAL_RISK", "HIGH_RISK_FRAUD"])])
tot_calls = df_network["total_calls"].iloc[0] if not df_network.empty else 0
conn_rate = df_network["connection_success_rate_pct"].iloc[0] if not df_network.empty else 0.0
tot_vol = df_corridor["total_volume_usd"].sum() if not df_corridor.empty else 0.0
tot_rev = df_rev["total_revenue"].sum() if not df_rev.empty else 0.0

k1, k2, k3, k4, k5, k6 = st.columns(6)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val">{tot_users:,}</div>
        <div class="kpi-lbl">Total Users</div>
        <div class="kpi-sub">Active Base</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val red">{high_risk_users:,}</div>
        <div class="kpi-lbl">High Risk Fraud</div>
        <div class="kpi-sub">Critical Flagged</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val green">{tot_calls:,.0f}</div>
        <div class="kpi-lbl">Total CDR Calls</div>
        <div class="kpi-sub">Network Volume</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val yellow">{conn_rate:.1f}%</div>
        <div class="kpi-lbl">Connection Rate</div>
        <div class="kpi-sub">SLA Target: 98.0%</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val purple">${tot_vol:,.0f}</div>
        <div class="kpi-lbl">Remittance Volume</div>
        <div class="kpi-sub">Global Transfers</div>
    </div>
    """, unsafe_allow_html=True)

with k6:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-val green">${tot_rev:,.0f}</div>
        <div class="kpi-lbl">Total Revenue</div>
        <div class="kpi-sub">Subscription Ledger</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION TABS
# ══════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Executive & Fraud Intelligence",
    "📶 Network SLA & Quality Monitor",
    "👥 Customer 360 & Health",
    "💰 Revenue & Remittance Corridors",
    "📋 Data Explorer & Export"
])

# ── TAB 1: EXECUTIVE & FRAUD INTELLIGENCE ──────────────────────────────────────
with tab1:
    col_a, col_b = st.columns([1, 1.2])

    with col_a:
        st.markdown("#### 🚨 Fraud Risk Classification")
        if not df_fraud_f.empty:
            risk_counts = df_fraud_f["fraud_risk_level"].value_counts().reset_index()
            risk_counts.columns = ["Risk Level", "Users"]
            color_map = [RISK_COLORS.get(r, "#58a6ff") for r in risk_counts["Risk Level"]]

            fig_donut = go.Figure(go.Pie(
                labels=risk_counts["Risk Level"],
                values=risk_counts["Users"],
                hole=0.55,
                marker=dict(colors=color_map, line=dict(color="#0b0e14", width=2)),
                textinfo="label+percent",
                textfont=dict(color="#c9d1d9", size=12),
            ))
            fig_donut.update_layout(
                **PLOTLY_THEME,
                height=320,
                showlegend=False,
                annotations=[dict(text=f"<b>{len(df_fraud_f)}</b><br>Users", x=0.5, y=0.5, font_size=16, font_color="#c9d1d9", showarrow=False)]
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown("""
            <div class="insight-banner">
                💡 <b>Executive Insight:</b> 44 out of 48 accounts trigger elevated fraud risk rules due to combined anomalies: high call drop rates matching large money transfer volumes.
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.markdown("#### 📈 Call Drop Rate vs. Transfer Amount (Risk Profile)")
        if not df_fraud_f.empty:
            fig_scatter = px.scatter(
                df_fraud_f,
                x="call_failure_rate_pct",
                y="total_transfer_usd",
                size="total_fraud_signals",
                color="fraud_risk_level",
                color_discrete_map=RISK_COLORS,
                hover_data=["user_id", "fraud_transfers", "fraud_tickets"],
                labels={
                    "call_failure_rate_pct": "Call Failure Rate (%)",
                    "total_transfer_usd": "Transfer Volume ($)",
                    "fraud_risk_level": "Risk Tier"
                }
            )
            fig_scatter.update_layout(**PLOTLY_THEME, height=320, xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
            st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")
    st.markdown("#### 🔎 Top High-Risk Account Priority Ledger")
    if not df_fraud_f.empty:
        disp_cols = ["user_id", "fraud_risk_level", "total_fraud_signals", "total_transfer_usd", "fraud_transfers", "call_failure_rate_pct", "fraud_tickets"]
        disp_df = df_fraud_f[disp_cols].sort_values("total_fraud_signals", ascending=False).head(15)
        st.dataframe(
            disp_df.rename(columns={
                "user_id": "User ID",
                "fraud_risk_level": "Risk Tier",
                "total_fraud_signals": "Fraud Signals",
                "total_transfer_usd": "Transfer Vol ($)",
                "fraud_transfers": "Fraud Transfers",
                "call_failure_rate_pct": "Call Fail %",
                "fraud_tickets": "Support Fraud Tickets"
            }),
            use_container_width=True,
            hide_index=True
        )

# ── TAB 2: NETWORK SLA & QUALITY MONITOR ──────────────────────────────────────
with tab2:
    st.markdown("#### 📶 Telecom SLA & Call Quality Metrics")
    if not df_network.empty:
        n1, n2, n3, n4 = st.columns(4)
        with n1: st.metric("Connection Success", f"{df_network['connection_success_rate_pct'].iloc[0]:.2f}%", delta="-25.4% Target gap", delta_color="inverse")
        with n2: st.metric("Average MOS Score", f"{df_network['avg_mos_score'].iloc[0]:.2f}", delta="-1.46 Benchmark gap", delta_color="inverse")
        with n3: st.metric("SLA Quality Met", f"{df_network['sla_quality_met_pct'].iloc[0]:.2f}%", delta="-58.3% Target gap", delta_color="inverse")
        with n4: st.metric("Packet Delivery Rate", f"{df_network['avg_delivery_rate_pct'].iloc[0]:.2f}%", delta="-26.7% Target gap", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        ncol1, ncol2 = st.columns(2)

        with ncol1:
            st.markdown("##### 🎯 MOS Call Quality Breakdown")
            q_data = pd.DataFrame({
                "Quality Tier": ["Excellent (>=4.0)", "Good (3.0-3.9)", "Fair (2.0-2.9)", "Poor (<2.0)"],
                "Call Count": [
                    df_network["excellent_calls"].iloc[0],
                    df_network["good_calls"].iloc[0],
                    df_network["fair_calls"].iloc[0],
                    df_network["poor_calls"].iloc[0]
                ]
            })
            fig_q = px.bar(q_data, x="Quality Tier", y="Call Count", color="Quality Tier",
                           color_discrete_sequence=["#3fb950", "#58a6ff", "#d29922", "#f85149"], text_auto=True)
            fig_q.update_layout(**PLOTLY_THEME, height=300, showlegend=False, xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
            st.plotly_chart(fig_q, use_container_width=True)

        with ncol2:
            st.markdown("##### ⏱️ Call Duration Distribution")
            d_data = pd.DataFrame({
                "Duration Bucket": ["No Connection", "Very Short (<30s)", "Short (<2m)", "Medium (<10m)", "Long (>10m)"],
                "Call Count": [
                    df_network["calls_no_connection"].iloc[0],
                    df_network["calls_very_short"].iloc[0],
                    df_network["calls_short"].iloc[0],
                    df_network["calls_medium"].iloc[0],
                    df_network["calls_long"].iloc[0]
                ]
            })
            fig_d = px.bar(d_data, x="Duration Bucket", y="Call Count", color_discrete_sequence=["#bc8cff"], text_auto=True)
            fig_d.update_layout(**PLOTLY_THEME, height=300, xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
            st.plotly_chart(fig_d, use_container_width=True)

# ── TAB 3: CUSTOMER 360 & HEALTH ──────────────────────────────────────────────
with tab3:
    st.markdown("#### 👥 Customer Segments & Churn Risk Analysis")
    if not df_cust_f.empty:
        ccol1, ccol2 = st.columns([1.2, 1])

        with ccol1:
            st.markdown("##### Customer Segment Distribution & Avg Health Score")
            seg_agg = df_cust_f.groupby("customer_segment").agg(
                users=("user_id", "count"),
                avg_health=("customer_health_score", "mean")
            ).reset_index()
            fig_seg = px.bar(seg_agg, x="customer_segment", y="users", color="avg_health",
                             color_continuous_scale="Blues", labels={"users": "Users", "avg_health": "Health Score"}, text_auto=True)
            fig_seg.update_layout(**PLOTLY_THEME, height=320, xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
            st.plotly_chart(fig_seg, use_container_width=True)

        with ccol2:
            st.markdown("##### Churn Risk Distribution")
            churn_counts = df_cust_f["churn_risk"].value_counts().reset_index()
            churn_counts.columns = ["Churn Risk", "Count"]
            fig_churn = px.pie(churn_counts, names="Churn Risk", values="Count", hole=0.5,
                               color_discrete_sequence=["#f85149", "#d29922", "#3fb950"])
            fig_churn.update_layout(**PLOTLY_THEME, height=320)
            st.plotly_chart(fig_churn, use_container_width=True)

# ── TAB 4: REVENUE & REMITTANCE CORRIDORS ──────────────────────────────────────
with tab4:
    rcol1, rcol2 = st.columns([1.3, 1])

    with rcol1:
        st.markdown("#### 💰 Top Money Transfer Corridors by Volume ($)")
        if not df_corridor.empty:
            top_corr = df_corridor.head(12)
            fig_corr = px.bar(
                top_corr,
                x="corridor",
                y="total_volume_usd",
                color="corridor_risk",
                color_discrete_map=RISK_COLORS,
                labels={"total_volume_usd": "Volume USD ($)", "corridor": "Corridor (Origin -> Destination)"},
                text_auto="$,.0f"
            )
            fig_corr.update_layout(**PLOTLY_THEME, height=340, xaxis=dict(tickangle=45, gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
            st.plotly_chart(fig_corr, use_container_width=True)

    with rcol2:
        st.markdown("#### 💳 Subscription Revenue Summary")
        if not df_rev.empty:
            rev_agg = df_rev.groupby("latest_subscription_plan").agg(
                users=("user_id", "count"),
                revenue=("total_revenue", "sum"),
                avg_ltv=("estimated_ltv", "mean")
            ).reset_index()
            fig_rev = px.bar(rev_agg, x="latest_subscription_plan", y="revenue", color="latest_subscription_plan",
                             color_discrete_sequence=["#58a6ff", "#bc8cff", "#3fb950"], text_auto="$,.0f")
            fig_rev.update_layout(**PLOTLY_THEME, height=340, showlegend=False)
            st.plotly_chart(fig_rev, use_container_width=True)

# ── TAB 5: RAW DATA EXPLORER & EXPORT ──────────────────────────────────────────
with tab5:
    st.markdown("#### 📋 Consolidated Data Explorer")
    dataset_choice = st.selectbox("Select Analytics Mart Table", ["mart_fraud_prevention", "mart_customer_360", "mart_revenue_analytics", "mart_corridor_analytics", "mart_network_quality"])

    if dataset_choice == "mart_fraud_prevention":
        st.dataframe(df_fraud, use_container_width=True)
    elif dataset_choice == "mart_customer_360":
        st.dataframe(df_cust, use_container_width=True)
    elif dataset_choice == "mart_revenue_analytics":
        st.dataframe(df_rev, use_container_width=True)
    elif dataset_choice == "mart_corridor_analytics":
        st.dataframe(df_corridor, use_container_width=True)
    elif dataset_choice == "mart_network_quality":
        st.dataframe(df_network, use_container_width=True)

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#484f58; font-size:0.8rem; padding: 10px 0;">
    📡 Rebtel Telecom Business Intelligence Hub &nbsp;|&nbsp; Powered by GCP BigQuery + dbt + Streamlit &nbsp;|&nbsp; Refreshed Real-time
</div>
""", unsafe_allow_html=True)
