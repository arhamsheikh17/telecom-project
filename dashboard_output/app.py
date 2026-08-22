"""
╔══════════════════════════════════════════════════════════════════╗
║   REBTEL TELECOM & FINTECH — ENTERPRISE INTELLIGENCE DASHBOARD   ║
║   Built with Streamlit | Data: GCP BigQuery + dbt Analytics      ║
║   ML Engine: Random Forest Fraud Detection                       ║
╚══════════════════════════════════════════════════════════════════╝

Dashboard Output Folder — Standalone Professional BI Hub
Covers: Fraud Intelligence · Network SLA · Customer 360 ·
        Revenue Analytics · ML Model Outputs · Raw Data Explorer
"""

import os
import sys
import json
import warnings
import subprocess

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────
# PATHS  (all relative to this file, so it works from anywhere)
# ─────────────────────────────────────────────────────────────────
THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.join(THIS_DIR, "..")



DATA_BATCH  = os.path.join(PROJECT_ROOT, "data", "batch")
DATA_STREAM = os.path.join(PROJECT_ROOT, "data", "stream")
DATA_SAAS   = os.path.join(PROJECT_ROOT, "data", "saas")

PROJECT_ID  = "telecom-project-504210"
DATASET     = "rebtel_analytics"


def fmt_currency(val):
    """Format numeric currency values cleanly for executive cards and charts."""
    if not isinstance(val, (int, float)):
        return str(val)
    if val >= 1_000_000:
        return f"${val / 1_000_000:.2f}M"
    elif val >= 100_000:
        return f"${val / 1_000:.0f}K"
    elif val >= 1_000:
        return f"${val / 1_000:.1f}K"
    else:
        return f"${val:,.0f}"


# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Rebtel BI Hub — Executive Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# GLOBAL CSS — Dark Premium Theme
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #080c14 !important;
    color: #cdd6e4 !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1424 0%, #0a0f1c 100%) !important;
    border-right: 1px solid #1e2d45 !important;
    min-width: 265px !important;
}
[data-testid="stSidebar"] * { color: #cdd6e4 !important; }

.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 2rem;
    max-width: 1600px;
}

.hero-banner {
    background: linear-gradient(135deg, #0f172a 0%, #1e1035 40%, #0f172a 100%);
    border: 1px solid #2d3a55;
    border-radius: 18px;
    padding: 28px 36px;
    margin-bottom: 28px;
    position: relative;
    overflow: hidden;
    box-shadow: 0 8px 40px rgba(88,166,255,0.07);
}
.hero-title {
    font-size: 2.4rem;
    font-weight: 900;
    background: linear-gradient(90deg, #60a5fa, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1.2;
    margin: 0;
    letter-spacing: -0.03em;
}
.hero-subtitle {
    font-size: 0.93rem;
    color: #6b7fa3;
    margin-top: 8px;
    font-weight: 500;
}
.hero-badges {
    display: flex;
    gap: 10px;
    margin-top: 14px;
    flex-wrap: wrap;
}
.badge {
    background: rgba(96,165,250,0.1);
    border: 1px solid rgba(96,165,250,0.25);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    color: #93c5fd;
    letter-spacing: 0.03em;
}
.badge.green  { background:rgba(52,211,153,0.1); border-color:rgba(52,211,153,0.25); color:#6ee7b7; }
.badge.purple { background:rgba(167,139,250,0.1); border-color:rgba(167,139,250,0.25); color:#c4b5fd; }
.badge.orange { background:rgba(251,146,60,0.1); border-color:rgba(251,146,60,0.25); color:#fdba74; }
.badge.red    { background:rgba(248,81,73,0.1); border-color:rgba(248,81,73,0.25); color:#fca5a5; }

.kpi-card {
    background: linear-gradient(145deg, #111827 0%, #0d1524 100%);
    border: 1px solid #1e2d45;
    border-radius: 14px;
    padding: 14px 10px 12px;
    text-align: center;
    position: relative;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    height: 125px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    align-items: center;
    box-sizing: border-box;
}
.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 0 0 14px 14px;
}
.kpi-card.blue::after   { background: linear-gradient(90deg,#3b82f6,#60a5fa); }
.kpi-card.green::after  { background: linear-gradient(90deg,#059669,#34d399); }
.kpi-card.red::after    { background: linear-gradient(90deg,#dc2626,#f87171); }
.kpi-card.purple::after { background: linear-gradient(90deg,#7c3aed,#a78bfa); }
.kpi-card.orange::after { background: linear-gradient(90deg,#d97706,#fbbf24); }
.kpi-card.cyan::after   { background: linear-gradient(90deg,#0891b2,#22d3ee); }

.kpi-icon { font-size: 1.35rem; margin-bottom: 2px; line-height: 1; }
.kpi-val {
    font-size: 1.55rem;
    font-weight: 800;
    line-height: 1.1;
    margin: 2px 0;
    letter-spacing: -0.02em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
}
.kpi-card.blue   .kpi-val { color: #60a5fa; }
.kpi-card.green  .kpi-val { color: #34d399; }
.kpi-card.red    .kpi-val { color: #f87171; }
.kpi-card.purple .kpi-val { color: #a78bfa; }
.kpi-card.orange .kpi-val { color: #fbbf24; }
.kpi-card.cyan   .kpi-val { color: #22d3ee; }
.kpi-lbl {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #64748b;
    white-space: nowrap;
}
.kpi-delta {
    font-size: 0.70rem;
    font-weight: 600;
    color: #475569;
    white-space: nowrap;
}

.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 24px 0 14px;
    padding-bottom: 10px;
    border-bottom: 1px solid #1e2d45;
}
.section-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #e2e8f0;
    margin: 0;
}
.section-pill {
    background: rgba(96,165,250,0.12);
    border: 1px solid rgba(96,165,250,0.2);
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.7rem;
    font-weight: 700;
    color: #60a5fa;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.insight-box {
    background: rgba(96,165,250,0.06);
    border: 1px solid rgba(96,165,250,0.18);
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 12px 16px;
    font-size: 0.84rem;
    color: #cbd5e1;
    margin: 10px 0 16px;
    line-height: 1.5;
}
.insight-box.warn {
    background: rgba(251,146,60,0.06);
    border-color: rgba(251,146,60,0.18);
    border-left-color: #f97316;
}
.insight-box.danger {
    background: rgba(248,81,73,0.06);
    border-color: rgba(248,81,73,0.18);
    border-left-color: #ef4444;
}
.insight-box.success {
    background: rgba(52,211,153,0.06);
    border-color: rgba(52,211,153,0.18);
    border-left-color: #10b981;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(15, 23, 42, 0.75) !important;
    backdrop-filter: blur(12px);
    border-radius: 14px !important;
    padding: 6px 8px !important;
    border: 1px solid #1e293b !important;
    margin-bottom: 24px !important;
    display: flex !important;
    flex-wrap: wrap !important;
}
.stTabs [data-baseweb="tab"] {
    height: 42px !important;
    border-radius: 10px !important;
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 0 18px !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    transition: all 0.2s ease-in-out !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #f1f5f9 !important;
    background: rgba(255, 255, 255, 0.05) !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    border: 1px solid rgba(147, 197, 253, 0.3) !important;
}
.stTabs [data-baseweb="tab-highlight-container"],
.stTabs [data-baseweb="tab-border"] {
    display: none !important;
}

.status-online {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(52,211,153,0.1);
    border: 1px solid rgba(52,211,153,0.25);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.75rem;
    font-weight: 700;
    color: #34d399;
}
.status-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: #34d399;
    animation: pulse 1.5s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.3; }
}

.pipeline-step {
    background: #111827;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 10px 14px;
    margin-bottom: 7px;
    display: flex;
    align-items: center;
    gap: 12px;
}
.step-icon { font-size: 1.2rem; }
.step-text { font-size: 0.8rem; color: #94a3b8; }
.step-label { font-size: 0.72rem; font-weight: 700; color: #60a5fa; text-transform: uppercase; letter-spacing: 0.05em; }

.sidebar-logo { text-align: center; padding: 16px 0 20px; border-bottom: 1px solid #1e2d45; margin-bottom: 16px; }
.sidebar-logo-title { font-size: 1.5rem; font-weight: 900; color: #60a5fa; letter-spacing: -0.02em; }
.sidebar-logo-sub   { font-size: 0.7rem; color: #475569; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; margin-top: 2px; }

[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 14px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #60a5fa;
    font-weight: 800;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────
# BIGQUERY CLIENT (optional – graceful fallback to local CSV/JSON)
# ─────────────────────────────────────────────────────────────────
@st.cache_resource
def get_bq_client():
    """Get authenticated BigQuery client using gcloud access token."""
    import concurrent.futures
    def _try_connect():
        try:
            import google.oauth2.credentials
            from google.cloud import bigquery
            gcloud_path = os.path.join(
                os.environ.get("LOCALAPPDATA", r"C:\Users\ADVANCES PC\AppData\Local"),
                "Google", "Cloud SDK", "google-cloud-sdk", "bin", "gcloud.cmd"
            )
            cmds = [
                [gcloud_path, "auth", "print-access-token"] if os.path.exists(gcloud_path) else ["gcloud.cmd", "auth", "print-access-token"],
                ["gcloud", "auth", "print-access-token"]
            ]
            token = None
            for cmd in cmds:
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=6)
                    lines = [l.strip() for l in res.stdout.splitlines() if l.strip().startswith('ya29.') or l.strip().startswith('ya29_')]
                    if lines:
                        token = lines[0]
                        break
                    last_line = res.stdout.strip().splitlines()[-1].strip() if res.stdout.strip() else ""
                    if len(last_line) > 50 and ' ' not in last_line:
                        token = last_line
                        break
                except Exception:
                    pass
            
            if token:
                creds = google.oauth2.credentials.Credentials(token=token)
                return bigquery.Client(project=PROJECT_ID, credentials=creds)
        except Exception:
            pass
        try:
            from google.cloud import bigquery
            return bigquery.Client(project=PROJECT_ID)
        except Exception:
            return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_try_connect)
        try:
            return future.result(timeout=10)
        except Exception:
            return None


BQ_QUERY_TIMEOUT = 15  # seconds for BigQuery query execution



def bq_query(sql: str) -> pd.DataFrame:
    """Run a BigQuery SQL query with a hard timeout. Returns empty DataFrame on failure."""
    import concurrent.futures
    client = get_bq_client()
    if client is None:
        return pd.DataFrame()

    def _run_query():
        try:
            job = client.query(sql)
            return job.result(timeout=BQ_QUERY_TIMEOUT).to_dataframe()
        except Exception:
            return pd.DataFrame()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(_run_query)
        try:
            return future.result(timeout=BQ_QUERY_TIMEOUT + 2)
        except concurrent.futures.TimeoutError:
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────
# LOCAL DATA LOADERS
# ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_local_payments() -> pd.DataFrame:
    path = os.path.join(DATA_BATCH, "financial_payments.csv")
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["payment_amount"] = pd.to_numeric(df["payment_amount"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_local_cdrs() -> pd.DataFrame:
    path = os.path.join(DATA_STREAM, "call_data_records.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        for c in ["duration_seconds", "call_quality_score", "delivery_rate_percent"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        return df
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_local_transfers() -> pd.DataFrame:
    path = os.path.join(DATA_STREAM, "money_transfers.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        df = pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
        if "transfer_amount_usd" in df.columns:
            df["transfer_amount_usd"] = pd.to_numeric(df["transfer_amount_usd"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_local_zendesk() -> pd.DataFrame:
    path = os.path.join(DATA_SAAS, "zendesk_tickets.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            data = json.load(f)
        return pd.DataFrame(data) if isinstance(data, list) else pd.DataFrame()
    return pd.DataFrame()


# ─────────────────────────────────────────────────────────────────
# BIGQUERY MART LOADERS
# ─────────────────────────────────────────────────────────────────
def _coerce(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120)
def load_fraud_mart():
    sql = f"""
        SELECT user_id, fraud_risk_level,
               total_calls, failed_calls, call_failure_rate_pct,
               total_transfers, total_transfer_usd, fraud_transfers,
               support_tickets, fraud_tickets, total_fraud_signals
        FROM `{PROJECT_ID}.{DATASET}.mart_fraud_prevention`
        ORDER BY total_fraud_signals DESC
    """
    df = bq_query(sql)
    return _coerce(df, ["total_calls","failed_calls","call_failure_rate_pct",
                        "total_transfers","total_transfer_usd","fraud_transfers",
                        "support_tickets","fraud_tickets","total_fraud_signals"])


@st.cache_data(ttl=120)
def load_customer_mart():
    sql = f"""
        SELECT user_id, total_calls, total_transfers, total_payments,
               total_revenue, total_transfer_volume_usd,
               customer_health_score, customer_segment, churn_risk
        FROM `{PROJECT_ID}.{DATASET}.mart_customer_360`
    """
    df = bq_query(sql)
    return _coerce(df, ["total_calls","total_transfers","total_payments",
                        "total_revenue","total_transfer_volume_usd","customer_health_score"])


@st.cache_data(ttl=120)
def load_revenue_mart():
    sql = f"""
        SELECT user_id, latest_subscription_plan, total_revenue,
               estimated_ltv, payment_failure_rate_pct,
               revenue_per_call, revenue_per_transfer
        FROM `{PROJECT_ID}.{DATASET}.mart_revenue_analytics`
    """
    df = bq_query(sql)
    return _coerce(df, ["total_revenue","estimated_ltv","payment_failure_rate_pct",
                        "revenue_per_call","revenue_per_transfer"])


@st.cache_data(ttl=120)
def load_network_mart():
    sql = f"""
        SELECT total_calls, connected_calls, dropped_calls,
               connection_success_rate_pct, avg_mos_score, avg_delivery_rate_pct,
               excellent_calls, good_calls, fair_calls, poor_calls,
               sla_quality_met_pct, sla_connection_met_pct,
               calls_no_connection, calls_very_short, calls_short, calls_medium, calls_long
        FROM `{PROJECT_ID}.{DATASET}.mart_network_quality`
        LIMIT 1
    """
    df = bq_query(sql)
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df


@st.cache_data(ttl=120)
def load_corridor_mart():
    sql = f"""
        SELECT corridor, sender_country, receiver_country,
               total_transfers, unique_senders, total_volume_usd,
               avg_transfer_usd, fraud_count, fraud_rate_pct, corridor_risk
        FROM `{PROJECT_ID}.{DATASET}.mart_corridor_analytics`
        ORDER BY total_volume_usd DESC
    """
    df = bq_query(sql)
    return _coerce(df, ["total_transfers","unique_senders","total_volume_usd",
                        "avg_transfer_usd","fraud_count","fraud_rate_pct"])


# ─────────────────────────────────────────────────────────────────
# LOAD ALL DATA
# ─────────────────────────────────────────────────────────────────
df_payments  = load_local_payments()
df_cdrs      = load_local_cdrs()
df_transfers = load_local_transfers()
df_zendesk   = load_local_zendesk()

df_fraud     = load_fraud_mart()
df_cust      = load_customer_mart()
df_rev       = load_revenue_mart()
df_network   = load_network_mart()
df_corridor  = load_corridor_mart()

HAS_BQ = not df_fraud.empty

# ─────────────────────────────────────────────────────────────────
# PLOTLY THEME & COLOR MAP
# ─────────────────────────────────────────────────────────────────
THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8"),
    margin=dict(t=36, b=16, l=8, r=8),
    hoverlabel=dict(bgcolor="#111827", font_color="#e2e8f0", bordercolor="#334155"),
)

RISK_COLOR = {
    "CRITICAL_RISK":       "#ef4444",
    "HIGH_RISK_FRAUD":     "#f97316",
    "MEDIUM_RISK":         "#eab308",
    "LOW_RISK":            "#22c55e",
    "SAFE":                "#3b82f6",
    "HIGH_RISK_CORRIDOR":  "#ef4444",
    "MONITOR_CORRIDOR":    "#eab308",
    "SAFE_CORRIDOR":       "#22c55e",
}

GRID = "rgba(30,45,69,0.8)"


def cdr_stats(df_c: pd.DataFrame) -> dict:
    if df_c.empty:
        return {}
    total = len(df_c)
    connected = int(df_c.get("connection_success", pd.Series([False])).sum()) \
                if "connection_success" in df_c.columns else 0
    return {
        "total_calls":   total,
        "connected":     connected,
        "conn_rate":     100 * connected / max(total, 1),
        "avg_quality":   float(df_c["call_quality_score"].mean()) if "call_quality_score" in df_c.columns else 0,
        "avg_duration":  float(df_c["duration_seconds"].mean()) if "duration_seconds" in df_c.columns else 0,
        "avg_delivery":  float(df_c["delivery_rate_percent"].mean()) if "delivery_rate_percent" in df_c.columns else 0,
    }


# ═══════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-title">📡 REBTEL BI</div>
        <div class="sidebar-logo-sub">Enterprise Intelligence Hub</div>
    </div>
    """, unsafe_allow_html=True)

    if HAS_BQ:
        st.markdown('<div class="status-online"><div class="status-dot"></div>BigQuery Live</div>',
                    unsafe_allow_html=True)
    else:
        st.warning("⚠️ BigQuery offline — using local data")

    st.markdown("---")
    st.markdown("### 🎛️ Dashboard Controls")

    if HAS_BQ and not df_fraud.empty:
        all_risks = sorted(df_fraud["fraud_risk_level"].dropna().unique().tolist())
        sel_risks = st.multiselect("Fraud Risk Tier", all_risks, default=all_risks)
    else:
        sel_risks = []

    if HAS_BQ and not df_cust.empty:
        all_segs = ["ALL"] + sorted(df_cust["customer_segment"].dropna().unique().tolist())
        sel_seg = st.selectbox("Customer Segment", all_segs)
    else:
        sel_seg = "ALL"

    if not df_payments.empty:
        all_plans = ["ALL"] + sorted(df_payments["subscription_plan"].dropna().unique().tolist())
        sel_plan = st.selectbox("Subscription Plan", all_plans)
    else:
        sel_plan = "ALL"

    st.markdown("---")
    st.markdown("**📌 Data Pipeline**")
    for icon, label, detail in [
        ("☁️", "Zendesk SaaS",   "Airbyte EL → BigQuery"),
        ("📤", "Batch CSV",      "GCS → BigQuery Raw"),
        ("⚡", "Stream Events",  "Pub/Sub → GCS → BQ"),
        ("⚙️", "dbt Transforms", "5 Analytics Marts"),
        ("🤖", "ML Fraud Model", "Random Forest F1=100%"),
    ]:
        st.markdown(f"""
        <div class="pipeline-step">
            <div class="step-icon">{icon}</div>
            <div>
                <div class="step-label">{label}</div>
                <div class="step-text">{detail}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"🏗️ Project: `{PROJECT_ID}`")
    st.caption(f"📦 Dataset: `{DATASET}`")


# ─── Apply filters ────────────────────────────────────────────────
df_fraud_f = df_fraud[df_fraud["fraud_risk_level"].isin(sel_risks)] \
             if (HAS_BQ and sel_risks) else df_fraud
df_cust_f  = df_cust[df_cust["customer_segment"] == sel_seg] \
             if (HAS_BQ and sel_seg != "ALL") else df_cust
df_pay_f   = df_payments[df_payments["subscription_plan"] == sel_plan] \
             if (sel_plan != "ALL") else df_payments


# ═══════════════════════════════════════════════════════════════════
# HERO BANNER
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero-banner">
    <div class="hero-title">📡 Rebtel Telecom &amp; Fintech Intelligence</div>
    <div class="hero-subtitle">
        Enterprise Executive Analytics Hub &nbsp;·&nbsp;
        Zendesk → Airbyte → GCS → BigQuery → dbt → ML → Dashboard
    </div>
    <div class="hero-badges">
        <span class="badge">📊 5 Analytics Marts</span>
        <span class="badge green">🤖 ML Fraud Detection</span>
        <span class="badge purple">⚙️ dbt Transforms</span>
        <span class="badge orange">⚡ Pub/Sub Streaming</span>
        <span class="badge red">🚨 Real-Time Fraud Alerts</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# GLOBAL KPI ROW
# ═══════════════════════════════════════════════════════════════════
_stats = cdr_stats(df_cdrs)

k_users     = len(df_fraud) if HAS_BQ else (df_payments["user_id"].nunique() if not df_payments.empty else "N/A")
k_fraud     = len(df_fraud[df_fraud["fraud_risk_level"].isin(["CRITICAL_RISK","HIGH_RISK_FRAUD"])]) if HAS_BQ else "N/A"
k_calls     = f"{_stats.get('total_calls', 0):,}" if _stats else "N/A"
k_conn      = f"{_stats.get('conn_rate', 0):.1f}%" if _stats else "N/A"
k_vol       = fmt_currency(df_transfers['transfer_amount_usd'].sum()) if not df_transfers.empty else "N/A"
k_rev       = fmt_currency(df_pay_f['payment_amount'].sum()) if not df_pay_f.empty else "N/A"

kpi_defs = [
    ("blue",   "👥", str(k_users),  "Total Users",      "Active Base"),
    ("red",    "🚨", str(k_fraud),  "High Fraud Risk",  "Critical + High"),
    ("green",  "📞", k_calls,       "CDR Events",       "Stream Volume"),
    ("orange", "📶", k_conn,        "Connection Rate",  "SLA: 98% Target"),
    ("purple", "💸", k_vol,         "Transfer Volume",  "Global Remittance"),
    ("cyan",   "💰", k_rev,         "Payment Revenue",  "Subscription"),
]

cols_kpi = st.columns(6)
for col, (color, icon, val, lbl, sub) in zip(cols_kpi, kpi_defs):
    col.markdown(f"""
    <div class="kpi-card {color}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-val">{val}</div>
        <div class="kpi-lbl">{lbl}</div>
        <div class="kpi-delta">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🚨 Fraud Intelligence",
    "📶 Network & SLA",
    "👥 Customer 360",
    "💰 Revenue & Payments",
    "🌍 Remittance Corridors",
    "🤖 ML Model Insights",
    "📋 Data Explorer",
])


# ───────────────────────────────────────────────────────────────────
# TAB 1 — FRAUD INTELLIGENCE
# ───────────────────────────────────────────────────────────────────
with tab1:
    st.markdown("""<div class="section-header">
        <span class="section-pill">Live BigQuery</span>
        <h3 class="section-title">🚨 Fraud Risk Intelligence Center</h3>
    </div>""", unsafe_allow_html=True)

    if HAS_BQ and not df_fraud_f.empty:
        c1, c2 = st.columns([1, 1.2])

        with c1:
            st.markdown("##### 🛡️ User Base Distribution by Risk Severity Tier")
            tier_counts = df_fraud_f.groupby("fraud_risk_level").agg(
                users=("user_id", "count"),
                vol=("total_transfer_usd", "sum")
            ).reset_index()

            risk_order = ["CRITICAL_RISK", "HIGH_RISK_FRAUD", "MEDIUM_RISK", "LOW_RISK"]
            tier_counts["sort_key"] = tier_counts["fraud_risk_level"].apply(
                lambda x: risk_order.index(x) if x in risk_order else 99
            )
            tier_counts = tier_counts.sort_values("sort_key")

            fig_risk_dist = go.Figure(go.Bar(
                y=tier_counts["fraud_risk_level"],
                x=tier_counts["users"],
                orientation="h",
                marker=dict(
                    color=[RISK_COLOR.get(r, "#3b82f6") for r in tier_counts["fraud_risk_level"]],
                    line=dict(color="#080c14", width=1.5)
                ),
                text=[f" <b>{u} Users</b> ({fmt_currency(v)})" for u, v in zip(tier_counts["users"], tier_counts["vol"])],
                textposition="outside",
                textfont=dict(color="#cbd5e1", size=12)
            ))
            fig_risk_dist.update_layout(
                **{**THEME, "margin": dict(l=20, r=140, t=30, b=30)},
                height=310,
                showlegend=False,
                xaxis=dict(title="Number of Flagged Accounts", gridcolor=GRID, zeroline=False),
                yaxis=dict(autorange="reversed", gridcolor=GRID)
            )
            st.plotly_chart(fig_risk_dist, use_container_width=True)

            total_f = len(df_fraud_f)
            critical = (df_fraud_f["fraud_risk_level"] == "CRITICAL_RISK").sum()
            high     = (df_fraud_f["fraud_risk_level"] == "HIGH_RISK_FRAUD").sum()
            pct = 100 * (critical + high) / max(total_f, 1)
            st.markdown(f"""<div class="insight-box danger">
            🚨 <b>{pct:.1f}% elevated fraud risk</b> — {critical} Critical + {high} High.
            Correlated patterns: high call drop rates + large international transfers.
            </div>""", unsafe_allow_html=True)

        with c2:
            st.markdown("##### 💸 Financial Volume Exposure at Risk ($ USD)")
            tier_metrics = df_fraud_f.groupby("fraud_risk_level").agg(
                total_vol=("total_transfer_usd", "sum")
            ).reset_index()
            tier_metrics["sort_key"] = tier_metrics["fraud_risk_level"].apply(
                lambda x: risk_order.index(x) if x in risk_order else 99
            )
            tier_metrics = tier_metrics.sort_values("sort_key")

            fig_exposure = go.Figure(go.Bar(
                x=tier_metrics["fraud_risk_level"],
                y=tier_metrics["total_vol"],
                marker_color=[RISK_COLOR.get(r, "#3b82f6") for r in tier_metrics["fraud_risk_level"]],
                text=[fmt_currency(v) for v in tier_metrics["total_vol"]],
                textposition="outside",
                textfont=dict(color="#e2e8f0", size=11)
            ))
            fig_exposure.update_layout(
                **{**THEME, "margin": dict(l=20, r=20, t=30, b=30)},
                height=310,
                showlegend=False,
                xaxis=dict(title="Risk Tier", gridcolor=GRID),
                yaxis=dict(title="Total Transfer Exposure ($ USD)", gridcolor=GRID, zeroline=False)
            )
            st.plotly_chart(fig_exposure, use_container_width=True)

        st.markdown("---")
        c3, c4 = st.columns(2)

        with c3:
            st.markdown("##### 🔋 Avg Fraud Signals by Risk Tier")
            tier_agg = df_fraud_f.groupby("fraud_risk_level").agg(
                avg_signals=("total_fraud_signals","mean"),
                user_count=("user_id","count"),
            ).reset_index().sort_values("avg_signals")
            fig_b = go.Figure(go.Bar(
                y=tier_agg["fraud_risk_level"], x=tier_agg["avg_signals"],
                orientation="h",
                marker_color=[RISK_COLOR.get(r,"#3b82f6") for r in tier_agg["fraud_risk_level"]],
                text=[f"{v:.1f}" for v in tier_agg["avg_signals"]],
                textposition="outside", textfont_color="#94a3b8",
            ))
            fig_b.update_layout(**THEME, height=260, showlegend=False,
                                xaxis=dict(gridcolor=GRID, zeroline=False),
                                yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_b, use_container_width=True)

        with c4:
            st.markdown("##### 🎭 Failed Calls vs Fraud Transfers by Tier")
            tier_comp = df_fraud_f.groupby("fraud_risk_level").agg(
                failed_calls=("failed_calls","sum"),
                fraud_transfers=("fraud_transfers","sum"),
            ).reset_index()
            fig_g = go.Figure()
            fig_g.add_trace(go.Bar(x=tier_comp["fraud_risk_level"], y=tier_comp["failed_calls"],
                                   name="Failed Calls", marker_color="#60a5fa"))
            fig_g.add_trace(go.Bar(x=tier_comp["fraud_risk_level"], y=tier_comp["fraud_transfers"],
                                   name="Fraud Transfers", marker_color="#f87171"))
            fig_g.update_layout(**THEME, height=260, barmode="group",
                                xaxis=dict(gridcolor=GRID),
                                yaxis=dict(gridcolor=GRID),
                                legend=dict(bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig_g, use_container_width=True)

        st.markdown("---")
        st.markdown("##### 📋 High-Risk Account Priority Ledger (Top 20)")
        ledger = df_fraud_f[["user_id","fraud_risk_level","total_fraud_signals",
                              "total_transfer_usd","fraud_transfers",
                              "call_failure_rate_pct","fraud_tickets"]]\
                 .sort_values("total_fraud_signals", ascending=False).head(20)
        st.dataframe(ledger.rename(columns={
            "user_id":"User ID","fraud_risk_level":"Risk Tier",
            "total_fraud_signals":"Fraud Signals","total_transfer_usd":"Transfer Vol ($)",
            "fraud_transfers":"Fraud Txns","call_failure_rate_pct":"Call Fail %",
            "fraud_tickets":"Fraud Tickets"}),
            use_container_width=True, hide_index=True)

    else:
        st.markdown("""<div class="insight-box warn">
        ⚠️ mart_fraud_prevention not accessible. Check GCP credentials.
        ML outputs are visible in the 🤖 ML Model Insights tab.
        </div>""", unsafe_allow_html=True)
        if not df_transfers.empty and "is_fraud_flag" in df_transfers.columns:
            st.markdown("##### 📦 Raw Fraud Signals from Local Stream Data")
            fraud_raw = df_transfers[df_transfers["is_fraud_flag"] == True]
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Transfers", f"{len(df_transfers):,}")
            m2.metric("Flagged Fraud",   f"{len(fraud_raw):,}")
            m3.metric("Fraud Rate",      f"{100*len(fraud_raw)/max(len(df_transfers),1):.1f}%")


# ───────────────────────────────────────────────────────────────────
# TAB 2 — NETWORK & SLA
# ───────────────────────────────────────────────────────────────────
with tab2:
    st.markdown("""<div class="section-header">
        <span class="section-pill">Telecom</span>
        <h3 class="section-title">📶 Network SLA & Call Quality Monitor</h3>
    </div>""", unsafe_allow_html=True)

    if HAS_BQ and not df_network.empty:
        n = df_network.iloc[0]
        nk1, nk2, nk3, nk4 = st.columns(4)
        nk1.metric("Connection Rate",  f"{n['connection_success_rate_pct']:.2f}%", "-25.4% vs Target 98%")
        nk2.metric("Avg MOS Score",    f"{n['avg_mos_score']:.2f}",               "-1.46 vs Benchmark 4.0")
        nk3.metric("SLA Quality Met",  f"{n['sla_quality_met_pct']:.2f}%",        "-58.3% vs Target 95%")
        nk4.metric("Delivery Rate",    f"{n['avg_delivery_rate_pct']:.2f}%",      "-26.7% vs Target 95%")

        st.markdown("<br>", unsafe_allow_html=True)
        nc1, nc2 = st.columns(2)

        with nc1:
            st.markdown("##### 🎯 MOS Quality Breakdown")
            q_df = pd.DataFrame({
                "Quality": ["Excellent (≥4.0)","Good (3.0-3.9)","Fair (2.0-2.9)","Poor (<2.0)"],
                "Count":   [n["excellent_calls"],n["good_calls"],n["fair_calls"],n["poor_calls"]],
            })
            fig_q = px.bar(q_df, x="Quality", y="Count", color="Quality", text_auto=True,
                           color_discrete_sequence=["#22c55e","#3b82f6","#eab308","#ef4444"])
            fig_q.update_layout(**THEME, height=280, showlegend=False,
                                xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_q, use_container_width=True)

        with nc2:
            st.markdown("##### ⏱️ Call Duration Distribution")
            d_df = pd.DataFrame({
                "Bucket": ["No Conn","Very Short","Short","Medium","Long"],
                "Count":  [n["calls_no_connection"],n["calls_very_short"],
                           n["calls_short"],n["calls_medium"],n["calls_long"]],
            })
            fig_dur = px.bar(d_df, x="Bucket", y="Count", text_auto=True,
                             color_discrete_sequence=["#a78bfa"])
            fig_dur.update_traces(marker_line_width=0)
            fig_dur.update_layout(**THEME, height=280,
                                  xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_dur, use_container_width=True)

        st.markdown("""<div class="insight-box warn">
        ⚠️ <b>SLA Alert:</b> Connection success <b>72.6%</b> (−25.4 pts vs 98% target).
        Avg MOS <b>2.54</b> = "Fair" quality. Immediate infrastructure review recommended.
        </div>""", unsafe_allow_html=True)

    # Local CDR analysis
    if not df_cdrs.empty:
        st.markdown("---")
        st.markdown("##### 📦 Local CDR Stream Analytics")
        _s = cdr_stats(df_cdrs)
        if _s:
            lc1, lc2, lc3, lc4 = st.columns(4)
            lc1.metric("Total CDR Events",  f"{_s['total_calls']:,}")
            lc2.metric("Connection Rate",   f"{_s['conn_rate']:.1f}%")
            lc3.metric("Avg Quality Score", f"{_s['avg_quality']:.2f}")
            lc4.metric("Avg Duration (s)",  f"{_s['avg_duration']:.1f}")

        lcc1, lcc2 = st.columns(2)
        with lcc1:
            if "call_quality_score" in df_cdrs.columns:
                st.markdown("##### 📊 Quality Score Distribution")
                fig_hist = px.histogram(df_cdrs, x="call_quality_score", nbins=30,
                                        color_discrete_sequence=["#60a5fa"], opacity=0.85,
                                        labels={"call_quality_score":"MOS Quality Score"})
                fig_hist.update_traces(marker_line_width=0)
                fig_hist.update_layout(**THEME, height=250,
                                       xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
                st.plotly_chart(fig_hist, use_container_width=True)

        with lcc2:
            if "duration_seconds" in df_cdrs.columns:
                st.markdown("##### ⏱️ Call Duration (Raw Stream)")
                fig_hist2 = px.histogram(df_cdrs[df_cdrs["duration_seconds"] > 0],
                                         x="duration_seconds", nbins=30,
                                         color_discrete_sequence=["#a78bfa"], opacity=0.85,
                                         labels={"duration_seconds":"Duration (s)"})
                fig_hist2.update_traces(marker_line_width=0)
                fig_hist2.update_layout(**THEME, height=250,
                                        xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
                st.plotly_chart(fig_hist2, use_container_width=True)

        if "user_id" in df_cdrs.columns:
            agg_cols = {"call_quality_score": "mean", "duration_seconds": "mean"}
            agg_cols = {k: v for k, v in agg_cols.items() if k in df_cdrs.columns}
            agg_cols["user_id"] = "count"
            user_cdr = df_cdrs.groupby("user_id").agg(
                calls=("call_quality_score", "count") if "call_quality_score" in df_cdrs.columns else ("user_id", "count"),
                avg_quality=("call_quality_score","mean") if "call_quality_score" in df_cdrs.columns else ("user_id","count"),
                avg_dur=("duration_seconds","mean") if "duration_seconds" in df_cdrs.columns else ("user_id","count"),
            ).reset_index().sort_values("calls", ascending=False).head(15)
            st.markdown("##### 👤 Top Users by CDR Volume")
            st.dataframe(user_cdr, use_container_width=True, hide_index=True)


# ───────────────────────────────────────────────────────────────────
# TAB 3 — CUSTOMER 360
# ───────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("""<div class="section-header">
        <span class="section-pill">CRM</span>
        <h3 class="section-title">👥 Customer 360 — Segments, Health & Churn</h3>
    </div>""", unsafe_allow_html=True)

    if HAS_BQ and not df_cust_f.empty:
        cc1, cc2 = st.columns([1.3, 1])

        with cc1:
            st.markdown("##### 📊 Segments — Count & Avg Health Score")
            seg_agg = df_cust_f.groupby("customer_segment").agg(
                users=("user_id","count"),
                avg_health=("customer_health_score","mean"),
            ).reset_index().sort_values("users", ascending=False)
            fig_seg = px.bar(seg_agg, x="customer_segment", y="users",
                             color="avg_health", color_continuous_scale="Blues", text_auto=True,
                             labels={"users":"Users","avg_health":"Avg Health","customer_segment":"Segment"})
            fig_seg.update_traces(marker_line_width=0)
            fig_seg.update_layout(**THEME, height=300,
                                  xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID),
                                  coloraxis_colorbar=dict(title="Health",tickfont=dict(color="#94a3b8")))
            st.plotly_chart(fig_seg, use_container_width=True)

        with cc2:
            st.markdown("##### 🔄 Churn Risk Distribution")
            churn_c = df_cust_f["churn_risk"].value_counts().reset_index()
            churn_c.columns = ["Churn Risk","Count"]
            high_churn = int(churn_c[churn_c["Churn Risk"]=="HIGH"]["Count"].sum()) if "HIGH" in churn_c["Churn Risk"].values else 0
            fig_ch = go.Figure(go.Pie(
                labels=churn_c["Churn Risk"], values=churn_c["Count"], hole=0.55,
                marker=dict(colors=["#ef4444","#eab308","#22c55e"],
                            line=dict(color="#080c14",width=3)),
                textinfo="label+percent+value", textfont=dict(color="#e2e8f0",size=11),
            ))
            fig_ch.update_layout(**THEME, height=300, showlegend=False,
                annotations=[dict(text=f"<b>{high_churn}</b><br>High Risk",x=0.5,y=0.5,
                                  font_size=16,font_color="#ef4444",showarrow=False)])
            st.plotly_chart(fig_ch, use_container_width=True)

        st.markdown("---")
        hc1, hc2 = st.columns(2)

        with hc1:
            st.markdown("##### 💊 Health Score Distribution")
            fig_health = px.histogram(df_cust_f, x="customer_health_score", nbins=20,
                                      color_discrete_sequence=["#34d399"], opacity=0.85,
                                      labels={"customer_health_score":"Health Score"})
            fig_health.update_traces(marker_line_width=0)
            fig_health.update_layout(**THEME, height=260,
                                     xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_health, use_container_width=True)

        with hc2:
            st.markdown("##### 💎 Avg Revenue per Segment")
            seg_rev = df_cust_f.groupby("customer_segment").agg(
                avg_rev=("total_revenue","mean")
            ).reset_index().sort_values("avg_rev")
            fig_rev_seg = px.bar(seg_rev, y="customer_segment", x="avg_rev",
                                  orientation="h", color_discrete_sequence=["#a78bfa"],
                                  text_auto="$,.1f",
                                  labels={"customer_segment":"Segment","avg_rev":"Avg Revenue ($)"})
            fig_rev_seg.update_traces(marker_line_width=0)
            fig_rev_seg.update_layout(**THEME, height=260,
                                      xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_rev_seg, use_container_width=True)

        st.markdown("---")
        st.markdown("##### ⚠️ Churn Risk vs Customer Health Score")
        fig_box = px.box(df_cust_f, x="churn_risk", y="customer_health_score",
                         color="churn_risk",
                         color_discrete_map={"HIGH":"#ef4444","MEDIUM":"#eab308","LOW":"#22c55e"},
                         labels={"churn_risk":"Churn Risk","customer_health_score":"Health Score"})
        fig_box.update_layout(**THEME, height=270, showlegend=False,
                              xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
        st.plotly_chart(fig_box, use_container_width=True)

    else:
        st.markdown('<div class="insight-box warn">⚠️ mart_customer_360 not accessible.</div>',
                    unsafe_allow_html=True)

    if not df_zendesk.empty:
        st.markdown("---")
        st.markdown("##### 🎫 Zendesk Support Ticket Analytics")
        z1, z2 = st.columns(2)
        with z1:
            if "issue_category" in df_zendesk.columns:
                cat_c = df_zendesk["issue_category"].value_counts().reset_index()
                cat_c.columns = ["Category","Count"]
                fig_z = px.bar(cat_c, x="Category", y="Count",
                               color_discrete_sequence=["#22d3ee"], text_auto=True)
                fig_z.update_layout(**THEME, height=240, showlegend=False,
                                    xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
                st.plotly_chart(fig_z, use_container_width=True)
        with z2:
            if "ticket_status" in df_zendesk.columns:
                stat_c = df_zendesk["ticket_status"].value_counts().reset_index()
                stat_c.columns = ["Status","Count"]
                fig_zs = px.pie(stat_c, names="Status", values="Count", hole=0.45,
                                color_discrete_sequence=["#22d3ee","#a78bfa","#f472b6","#fbbf24"])
                fig_zs.update_layout(**THEME, height=240)
                st.plotly_chart(fig_zs, use_container_width=True)


# ───────────────────────────────────────────────────────────────────
# TAB 4 — REVENUE & PAYMENTS
# ───────────────────────────────────────────────────────────────────
with tab4:
    st.markdown("""<div class="section-header">
        <span class="section-pill">Finance</span>
        <h3 class="section-title">💰 Revenue Analytics & Payment Performance</h3>
    </div>""", unsafe_allow_html=True)

    if not df_pay_f.empty:
        tot_rev_l  = df_pay_f["payment_amount"].sum()
        avg_pay    = df_pay_f["payment_amount"].mean()
        suc_pct    = 100*(df_pay_f["payment_status"]=="success").sum()/max(len(df_pay_f),1) if "payment_status" in df_pay_f.columns else 0
        fail_pct   = 100*(df_pay_f["payment_status"]=="failed").sum()/max(len(df_pay_f),1)  if "payment_status" in df_pay_f.columns else 0

        pk1, pk2, pk3, pk4 = st.columns(4)
        pk1.metric("Total Revenue",  f"${tot_rev_l:,.2f}")
        pk2.metric("Avg Payment",    f"${avg_pay:.2f}")
        pk3.metric("Success Rate",   f"{suc_pct:.1f}%",  delta=f"{suc_pct-70:.1f}% vs 70% baseline")
        pk4.metric("Failure Rate",   f"{fail_pct:.1f}%", delta=f"-{fail_pct:.1f}%", delta_color="inverse")

        st.markdown("<br>", unsafe_allow_html=True)
        rc1, rc2 = st.columns(2)

        with rc1:
            st.markdown("##### 📦 Revenue by Subscription Plan")
            if "subscription_plan" in df_pay_f.columns:
                plan_agg = df_pay_f.groupby("subscription_plan").agg(
                    revenue=("payment_amount","sum"),
                    txns=("transaction_id","count"),
                ).reset_index().sort_values("revenue", ascending=False)
                fig_plan = px.bar(plan_agg, x="subscription_plan", y="revenue",
                                  color="subscription_plan", text_auto="$,.0f",
                                  color_discrete_sequence=["#3b82f6","#8b5cf6","#10b981","#f59e0b"],
                                  labels={"subscription_plan":"Plan","revenue":"Revenue ($)"})
                fig_plan.update_traces(marker_line_width=0, textposition="outside")
                fig_plan.update_layout(**THEME, height=290, showlegend=False,
                                       xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
                st.plotly_chart(fig_plan, use_container_width=True)

        with rc2:
            st.markdown("##### ✅ Payment Status Breakdown")
            if "payment_status" in df_pay_f.columns:
                stat_agg = df_pay_f["payment_status"].value_counts().reset_index()
                stat_agg.columns = ["Status","Count"]
                fig_stat = go.Figure(go.Pie(
                    labels=stat_agg["Status"], values=stat_agg["Count"], hole=0.55,
                    marker=dict(colors=["#22c55e","#ef4444","#eab308"],
                                line=dict(color="#080c14",width=3)),
                    textinfo="label+percent+value", textfont=dict(color="#e2e8f0",size=11),
                ))
                fig_stat.update_layout(**THEME, height=290, showlegend=False)
                st.plotly_chart(fig_stat, use_container_width=True)

        st.markdown("---")
        rc3, rc4 = st.columns(2)

        with rc3:
            st.markdown("##### 💳 Payment Amount Distribution")
            fig_amnt = px.histogram(df_pay_f, x="payment_amount", nbins=30,
                                    color_discrete_sequence=["#60a5fa"], opacity=0.85,
                                    labels={"payment_amount":"Payment Amount ($)"})
            fig_amnt.update_traces(marker_line_width=0)
            fig_amnt.update_layout(**THEME, height=250,
                                   xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_amnt, use_container_width=True)

        with rc4:
            if "subscription_plan" in df_pay_f.columns and "payment_status" in df_pay_f.columns:
                st.markdown("##### 📉 Failure Rate by Plan")
                fail_rate = df_pay_f.groupby("subscription_plan").apply(
                    lambda x: 100*(x["payment_status"]=="failed").sum()/max(len(x),1)
                ).reset_index(name="failure_rate")
                fig_fail = px.bar(fail_rate, x="subscription_plan", y="failure_rate",
                                  color_discrete_sequence=["#f87171"], text_auto=".1f",
                                  labels={"subscription_plan":"Plan","failure_rate":"Failure Rate (%)"})
                fig_fail.update_traces(marker_line_width=0, textposition="outside")
                fig_fail.update_layout(**THEME, height=250, showlegend=False,
                                       xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
                st.plotly_chart(fig_fail, use_container_width=True)

    if HAS_BQ and not df_rev.empty:
        st.markdown("---")
        st.markdown("##### 📊 BigQuery Revenue Analytics Mart")
        rev_agg = df_rev.groupby("latest_subscription_plan").agg(
            users=("user_id","count"),
            total_rev=("total_revenue","sum"),
            avg_ltv=("estimated_ltv","mean"),
        ).reset_index().sort_values("total_rev", ascending=False)
        bc1, bc2 = st.columns(2)
        with bc1:
            fig_bq_r = px.bar(rev_agg, x="latest_subscription_plan", y="total_rev",
                              color="latest_subscription_plan", text_auto="$,.0f",
                              color_discrete_sequence=["#3b82f6","#8b5cf6","#10b981","#f59e0b"],
                              labels={"latest_subscription_plan":"Plan","total_rev":"Revenue ($)"})
            fig_bq_r.update_layout(**THEME, height=250, showlegend=False,
                                   xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_bq_r, use_container_width=True)
        with bc2:
            fig_ltv = px.bar(rev_agg, x="latest_subscription_plan", y="avg_ltv",
                             color_discrete_sequence=["#34d399"], text_auto="$,.0f",
                             labels={"latest_subscription_plan":"Plan","avg_ltv":"Avg LTV ($)"})
            fig_ltv.update_layout(**THEME, height=250, showlegend=False,
                                  xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_ltv, use_container_width=True)

        st.markdown("""<div class="insight-box success">
        💡 <b>Revenue Insight:</b> Premium subscribers generate highest LTV.
        Optimize dunning for failed payments — focus on Premium tier for max revenue impact.
        </div>""", unsafe_allow_html=True)


# ───────────────────────────────────────────────────────────────────
# TAB 5 — REMITTANCE CORRIDORS
# ───────────────────────────────────────────────────────────────────
with tab5:
    st.markdown("""<div class="section-header">
        <span class="section-pill">Fintech</span>
        <h3 class="section-title">🌍 Global Remittance Corridor Intelligence</h3>
    </div>""", unsafe_allow_html=True)

    if not df_transfers.empty:
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("Total Transfers", f"{len(df_transfers):,}")
        t2.metric("Total Volume",    f"${df_transfers['transfer_amount_usd'].sum():,.0f}")
        t3.metric("Avg Transfer",    f"${df_transfers['transfer_amount_usd'].mean():,.2f}")
        t4.metric("Max Transfer",    f"${df_transfers['transfer_amount_usd'].max():,.2f}")

        st.markdown("<br>", unsafe_allow_html=True)
        gc1, gc2 = st.columns(2)

        with gc1:
            if "sender_country" in df_transfers.columns:
                st.markdown("##### 🗺️ Top Sending Countries by Volume")
                sender_agg = df_transfers.groupby("sender_country").agg(
                    volume=("transfer_amount_usd","sum"),
                ).reset_index().sort_values("volume").tail(12)
                fig_s = px.bar(sender_agg, y="sender_country", x="volume", orientation="h",
                               color_discrete_sequence=["#60a5fa"], text_auto="$,.0f",
                               labels={"sender_country":"Country","volume":"Volume ($)"})
                fig_s.update_traces(marker_line_width=0)
                fig_s.update_layout(**THEME, height=340, xaxis=dict(gridcolor=GRID), yaxis=dict(gridcolor=GRID))
                st.plotly_chart(fig_s, use_container_width=True)

        with gc2:
            st.markdown("##### 💸 Transfer Size Distribution")
            def size_tier(v):
                if v < 50:   return "Micro (<$50)"
                if v < 200:  return "Small (<$200)"
                if v < 500:  return "Medium (<$500)"
                if v < 1000: return "Large (<$1K)"
                return "Very Large (≥$1K)"
            df_transfers["size_tier"] = df_transfers["transfer_amount_usd"].apply(size_tier)
            tier_c = df_transfers["size_tier"].value_counts().reset_index()
            tier_c.columns = ["Tier","Count"]
            fig_t = px.pie(tier_c, names="Tier", values="Count", hole=0.45,
                           color_discrete_sequence=["#3b82f6","#8b5cf6","#22c55e","#f59e0b","#ef4444"])
            fig_t.update_layout(**THEME, height=340)
            st.plotly_chart(fig_t, use_container_width=True)

        if "sender_country" in df_transfers.columns and "receiver_country" in df_transfers.columns:
            df_transfers["corridor"] = df_transfers["sender_country"] + " → " + df_transfers["receiver_country"]
            corr_l = df_transfers.groupby("corridor").agg(
                volume=("transfer_amount_usd","sum"),
                count=("transfer_amount_usd","count"),
            ).reset_index().sort_values("volume", ascending=False).head(15)
            st.markdown("---")
            st.markdown("##### 🔗 Top Transfer Corridors")
            fig_cl = px.bar(corr_l, x="corridor", y="volume",
                            color_discrete_sequence=["#a78bfa"], text_auto="$,.0f",
                            labels={"corridor":"Corridor","volume":"Volume ($)"})
            fig_cl.update_traces(marker_line_width=0, textposition="outside")
            fig_cl.update_layout(**THEME, height=310,
                                 xaxis=dict(tickangle=45, gridcolor=GRID),
                                 yaxis=dict(gridcolor=GRID))
            st.plotly_chart(fig_cl, use_container_width=True)

    if HAS_BQ and not df_corridor.empty:
        st.markdown("---")
        st.markdown("##### 📊 BigQuery Corridor Analytics Mart (with Risk Classification)")
        fig_bc = px.bar(df_corridor.head(15), x="corridor", y="total_volume_usd",
                        color="corridor_risk", color_discrete_map=RISK_COLOR,
                        text_auto="$,.0f",
                        labels={"total_volume_usd":"Volume ($)","corridor":"Corridor","corridor_risk":"Risk"})
        fig_bc.update_traces(marker_line_width=0, textposition="outside")
        fig_bc.update_layout(**THEME, height=310,
                             xaxis=dict(tickangle=45, gridcolor=GRID),
                             yaxis=dict(gridcolor=GRID),
                             legend=dict(bgcolor="rgba(0,0,0,0)"))
        st.plotly_chart(fig_bc, use_container_width=True)

        st.markdown("##### 📋 Corridor Risk Register")
        st.dataframe(df_corridor[["corridor","corridor_risk","total_transfers","total_volume_usd",
                                  "avg_transfer_usd","fraud_count","fraud_rate_pct"]]\
                     .rename(columns={"corridor":"Corridor","corridor_risk":"Risk",
                                      "total_transfers":"Txns","total_volume_usd":"Volume ($)",
                                      "avg_transfer_usd":"Avg ($)","fraud_count":"Fraud Count",
                                      "fraud_rate_pct":"Fraud Rate %"}),
                     use_container_width=True, hide_index=True)


# ───────────────────────────────────────────────────────────────────
# TAB 6 — ML MODEL INSIGHTS (Live BigQuery)
# ───────────────────────────────────────────────────────────────────
with tab6:
    st.markdown("""<div class="section-header">
        <span class="section-pill">Live BigQuery</span>
        <h3 class="section-title">🤖 ML Fraud Intelligence — Live Analytics from BigQuery</h3>
    </div>""", unsafe_allow_html=True)

    @st.cache_data(ttl=120)
    def load_ml_fraud_data():
        sql = f"""
            SELECT
                user_id,
                fraud_risk_level,
                total_calls,
                failed_calls,
                call_failure_rate_pct,
                total_transfers,
                total_transfer_usd,
                fraud_transfers,
                support_tickets,
                fraud_tickets,
                total_fraud_signals
            FROM `{PROJECT_ID}.{DATASET}.mart_fraud_prevention`
            ORDER BY total_fraud_signals DESC
        """
        df = bq_query(sql)
        return _coerce(df, [
            "total_calls","failed_calls","call_failure_rate_pct",
            "total_transfers","total_transfer_usd","fraud_transfers",
            "support_tickets","fraud_tickets","total_fraud_signals"
        ])

    df_ml = load_ml_fraud_data()
    ml_live = not df_ml.empty

    if ml_live:
        total_u  = len(df_ml)
        crit     = (df_ml["fraud_risk_level"] == "CRITICAL_RISK").sum()
        high     = (df_ml["fraud_risk_level"] == "HIGH_RISK_FRAUD").sum()
        avg_sigs = df_ml["total_fraud_signals"].mean()
        total_exp = df_ml["total_transfer_usd"].sum()
        risk_order = ["CRITICAL_RISK","HIGH_RISK_FRAUD","MEDIUM_RISK","LOW_RISK"]

        # ── KPI cards ──────────────────────────────────────────────────
        lk1, lk2, lk3, lk4, lk5 = st.columns(5)
        for col, (color, icon, val, lbl, sub) in zip(
            [lk1, lk2, lk3, lk4, lk5],
            [
                ("blue",   "👥", f"{total_u:,}",         "Total Flagged Users",   "mart_fraud_prevention"),
                ("red",    "🚨", f"{crit:,}",             "Critical Risk",         f"{100*crit/max(total_u,1):.1f}% of base"),
                ("orange", "⚠️", f"{high:,}",             "High Risk Fraud",       f"{100*high/max(total_u,1):.1f}% of base"),
                ("cyan",   "📊", f"{avg_sigs:.2f}",       "Avg Fraud Signals",     "Per flagged user"),
                ("purple", "💸", fmt_currency(total_exp), "Total Exposure",        "Transfer volume at risk"),
            ]
        ):
            col.markdown(f"""
            <div class="kpi-card {color}">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-val">{val}</div>
                <div class="kpi-lbl">{lbl}</div>
                <div class="kpi-delta">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 1: Risk Distribution Bar + Fraud Signal Heatmap ────────
        st.markdown("""<div class="section-header">
            <span class="section-pill">Distribution</span>
            <h3 class="section-title">📊 Risk Classification &amp; Fraud Signal Intensity</h3>
        </div>""", unsafe_allow_html=True)

        r1c1, r1c2 = st.columns([1, 1.3])

        with r1c1:
            st.markdown("##### 🛡️ User Count by Fraud Risk Tier")
            risk_dist = (
                df_ml.groupby("fraud_risk_level")
                .agg(users=("user_id","count"), avg_signals=("total_fraud_signals","mean"),
                     total_vol=("total_transfer_usd","sum"))
                .reset_index()
            )
            risk_dist["_sort"] = risk_dist["fraud_risk_level"].apply(
                lambda x: risk_order.index(x) if x in risk_order else 99
            )
            risk_dist = risk_dist.sort_values("_sort")

            fig_rd = go.Figure(go.Bar(
                y=risk_dist["fraud_risk_level"],
                x=risk_dist["users"],
                orientation="h",
                marker=dict(
                    color=[RISK_COLOR.get(r,"#3b82f6") for r in risk_dist["fraud_risk_level"]],
                    line=dict(color="#080c14", width=1)
                ),
                text=[
                    f"  {u} users | Avg: {s:.1f} | {fmt_currency(v)}"
                    for u, s, v in zip(risk_dist["users"], risk_dist["avg_signals"], risk_dist["total_vol"])
                ],
                textposition="outside",
                textfont=dict(color="#94a3b8", size=10),
            ))
            fig_rd.update_layout(
                **{**THEME, "margin": dict(l=10, r=200, t=20, b=10)},
                height=260,
                showlegend=False,
                xaxis=dict(title="Number of Users", gridcolor=GRID, zeroline=False),
                yaxis=dict(gridcolor=GRID, autorange="reversed")
            )
            st.plotly_chart(fig_rd, use_container_width=True)

        with r1c2:
            st.markdown("##### 🔥 Fraud Signal Intensity Heatmap — Signals vs Transfers by Risk Tier")
            max_sig = df_ml["total_fraud_signals"].max()
            df_ml["signal_bucket"] = pd.cut(
                df_ml["total_fraud_signals"],
                bins=[0, 1, 2, 3, 5, 8, max_sig + 1],
                labels=["1","2","3","4-5","6-8","9+"],
                right=False
            ).astype(str)
            heat_pivot = (
                df_ml.groupby(["fraud_risk_level","signal_bucket"])
                .agg(users=("user_id","count"))
                .reset_index()
            )
            heat_pv = heat_pivot.pivot(
                index="fraud_risk_level", columns="signal_bucket", values="users"
            ).fillna(0)
            heat_pv = heat_pv.reindex([r for r in risk_order if r in heat_pv.index])
            col_order = [c for c in ["1","2","3","4-5","6-8","9+"] if c in heat_pv.columns]
            heat_pv = heat_pv[col_order]

            fig_heat = go.Figure(go.Heatmap(
                z=heat_pv.values.tolist(),
                x=col_order,
                y=heat_pv.index.tolist(),
                colorscale=[
                    [0.0,  "#111827"],
                    [0.25, "#1e3a5f"],
                    [0.5,  "#f97316"],
                    [0.75, "#ef4444"],
                    [1.0,  "#7f1d1d"],
                ],
                text=[[f"{int(v)}" for v in row] for row in heat_pv.values],
                texttemplate="%{text}",
                textfont=dict(color="#f1f5f9", size=12, family="Inter"),
                hovertemplate=(
                    "Risk: <b>%{y}</b><br>"
                    "Signals: <b>%{x}</b><br>"
                    "Users: <b>%{z}</b><extra></extra>"
                ),
                showscale=True,
                colorbar=dict(
                    title=dict(text="Users", font=dict(color="#94a3b8")),
                    thickness=12, len=0.9,
                    tickfont=dict(color="#94a3b8")
                )
            ))
            fig_heat.update_layout(
                **THEME,
                height=260,
                xaxis=dict(title="Fraud Signal Bucket", gridcolor=GRID, tickfont=dict(color="#94a3b8")),
                yaxis=dict(title="Risk Tier", gridcolor=GRID, tickfont=dict(color="#94a3b8"))
            )
            st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 2: Call Failure vs Transfer Scatter + Ticket Scatter ───
        st.markdown("""<div class="section-header">
            <span class="section-pill">Profiling</span>
            <h3 class="section-title">📈 Call Failure × Transfer Volume × Fraud Signals</h3>
        </div>""", unsafe_allow_html=True)

        sc_c1, sc_c2 = st.columns([1.6, 1])

        with sc_c1:
            st.markdown("##### 📡 Call Failure Rate vs. Remittance Volume — Fraud Signal Intensity")
            fig_sc = px.scatter(
                df_ml,
                x="call_failure_rate_pct",
                y="total_transfer_usd",
                size="total_fraud_signals",
                color="fraud_risk_level",
                color_discrete_map=RISK_COLOR,
                size_max=30,
                hover_data={
                    "user_id": True,
                    "fraud_transfers": True,
                    "fraud_tickets": True,
                    "total_fraud_signals": True,
                },
                labels={
                    "call_failure_rate_pct": "Call Failure Rate (%)",
                    "total_transfer_usd": "Transfer Volume (USD)",
                    "fraud_risk_level": "Risk Tier",
                    "total_fraud_signals": "Fraud Signals"
                }
            )
            fig_sc.update_traces(marker=dict(opacity=0.80, line=dict(width=0.6, color="#080c14")))
            fig_sc.update_layout(
                **THEME,
                height=360,
                xaxis=dict(title="Call Failure Rate (%)", gridcolor=GRID, zeroline=False),
                yaxis=dict(title="Total Transfer Volume (USD)", gridcolor=GRID, zeroline=False),
                legend=dict(bgcolor="rgba(0,0,0,0)", title_text="Risk Tier")
            )
            st.plotly_chart(fig_sc, use_container_width=True)

        with sc_c2:
            st.markdown("##### 🎫 Support Ticket vs. Fraud Ticket Concentration")
            fig_ticket = px.scatter(
                df_ml,
                x="support_tickets",
                y="fraud_tickets",
                size="total_fraud_signals",
                color="fraud_risk_level",
                color_discrete_map=RISK_COLOR,
                size_max=22,
                hover_data={"user_id": True, "fraud_transfers": True},
                labels={
                    "support_tickets": "Support Tickets",
                    "fraud_tickets": "Fraud Tickets",
                    "fraud_risk_level": "Risk Tier"
                }
            )
            fig_ticket.update_traces(marker=dict(opacity=0.80, line=dict(width=0.6, color="#080c14")))
            fig_ticket.update_layout(
                **THEME,
                height=360,
                xaxis=dict(title="Support Tickets", gridcolor=GRID, zeroline=False),
                yaxis=dict(title="Fraud-Specific Tickets", gridcolor=GRID, zeroline=False),
                legend=dict(bgcolor="rgba(0,0,0,0)", title_text="Risk Tier")
            )
            st.plotly_chart(fig_ticket, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 3: Avg Signals + Failed Calls grouped bars ─────────────
        st.markdown("""<div class="section-header">
            <span class="section-pill">Tier Analysis</span>
            <h3 class="section-title">🔋 Per-Tier Behavioural Metrics</h3>
        </div>""", unsafe_allow_html=True)

        ba_c1, ba_c2 = st.columns(2)

        with ba_c1:
            st.markdown("##### 📊 Avg Fraud Signals per Risk Tier")
            tier_agg = (
                df_ml.groupby("fraud_risk_level")
                .agg(avg_signals=("total_fraud_signals","mean"), user_count=("user_id","count"))
                .reset_index()
            )
            tier_agg["_sort"] = tier_agg["fraud_risk_level"].apply(
                lambda x: risk_order.index(x) if x in risk_order else 99
            )
            tier_agg = tier_agg.sort_values("_sort")
            fig_bar = go.Figure(go.Bar(
                y=tier_agg["fraud_risk_level"],
                x=tier_agg["avg_signals"],
                orientation="h",
                marker_color=[RISK_COLOR.get(r,"#3b82f6") for r in tier_agg["fraud_risk_level"]],
                text=[f"{v:.2f}  ({c} users)" for v, c in zip(tier_agg["avg_signals"], tier_agg["user_count"])],
                textposition="outside",
                textfont=dict(color="#94a3b8", size=10),
            ))
            fig_bar.update_layout(
                **{**THEME, "margin": dict(l=10, r=160, t=20, b=10)},
                height=240,
                showlegend=False,
                xaxis=dict(title="Avg Fraud Signals", gridcolor=GRID, zeroline=False),
                yaxis=dict(gridcolor=GRID, autorange="reversed")
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with ba_c2:
            st.markdown("##### 🎭 Failed Calls vs. Fraud Transfers by Tier")
            tier_comp = (
                df_ml.groupby("fraud_risk_level")
                .agg(failed_calls=("failed_calls","sum"), fraud_transfers=("fraud_transfers","sum"))
                .reset_index()
            )
            tier_comp["_sort"] = tier_comp["fraud_risk_level"].apply(
                lambda x: risk_order.index(x) if x in risk_order else 99
            )
            tier_comp = tier_comp.sort_values("_sort")
            fig_grp = go.Figure()
            fig_grp.add_trace(go.Bar(
                x=tier_comp["fraud_risk_level"], y=tier_comp["failed_calls"],
                name="Failed Calls", marker_color="#60a5fa"
            ))
            fig_grp.add_trace(go.Bar(
                x=tier_comp["fraud_risk_level"], y=tier_comp["fraud_transfers"],
                name="Fraud Transfers", marker_color="#f87171"
            ))
            fig_grp.update_layout(
                **THEME,
                height=240,
                barmode="group",
                xaxis=dict(gridcolor=GRID),
                yaxis=dict(gridcolor=GRID),
                legend=dict(bgcolor="rgba(0,0,0,0)")
            )
            st.plotly_chart(fig_grp, use_container_width=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Row 4: Executive High-Risk Priority Ledger ─────────────────
        st.markdown("""<div class="section-header">
            <span class="section-pill">Priority Ledger</span>
            <h3 class="section-title">🏴 Live Executive High-Risk Priority Ledger (Top 30)</h3>
        </div>""", unsafe_allow_html=True)

        st.markdown("""<div class="insight-box danger">
        🚨 <b>Live from BigQuery:</b> Queried directly from
        <code>telecom-project-504210.rebtel_analytics.mart_fraud_prevention</code>.
        Sorted by highest fraud signal count descending.
        </div>""", unsafe_allow_html=True)

        ledger = (
            df_ml[["user_id","fraud_risk_level","total_fraud_signals",
                   "total_transfer_usd","fraud_transfers",
                   "call_failure_rate_pct","failed_calls","fraud_tickets"]]
            .sort_values("total_fraud_signals", ascending=False)
            .head(30)
            .copy()
        )
        ledger_display = ledger.rename(columns={
            "user_id":               "User ID",
            "fraud_risk_level":      "Risk Tier",
            "total_fraud_signals":   "Fraud Signals",
            "total_transfer_usd":    "Transfer Vol",
            "fraud_transfers":       "Fraud Txns",
            "call_failure_rate_pct": "Call Fail %",
            "failed_calls":          "Failed Calls",
            "fraud_tickets":         "Fraud Tickets",
        })
        ledger_display["Transfer Vol"] = ledger_display["Transfer Vol"].apply(
            lambda v: fmt_currency(v) if isinstance(v, (int, float)) else v
        )
        ledger_display["Call Fail %"] = ledger_display["Call Fail %"].apply(
            lambda v: f"{v:.1f}%" if isinstance(v, (int, float)) else v
        )

        st.dataframe(
            ledger_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "User ID":       st.column_config.TextColumn("User ID", width="medium"),
                "Risk Tier":     st.column_config.TextColumn("Risk Tier", width="medium"),
                "Fraud Signals": st.column_config.NumberColumn("Fraud Signals", format="%d"),
                "Fraud Txns":    st.column_config.NumberColumn("Fraud Txns", format="%d"),
                "Failed Calls":  st.column_config.NumberColumn("Failed Calls", format="%d"),
                "Fraud Tickets": st.column_config.NumberColumn("Fraud Tickets", format="%d"),
            }
        )

        csv_ledger = ledger.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export High-Risk Ledger as CSV",
            data=csv_ledger,
            file_name="rebtel_high_risk_ledger.csv",
            mime="text/csv",
            type="primary"
        )

    else:
        st.markdown("""<div class="insight-box warn">
        ⚠️ <b>BigQuery Offline:</b> Could not connect to
        <code>telecom-project-504210.rebtel_analytics.mart_fraud_prevention</code>.
        Ensure GCP credentials are configured (<code>gcloud auth application-default login</code>).
        </div>""", unsafe_allow_html=True)
        st.markdown("""<div class="insight-box">
        💡 <b>To enable live data:</b><br>
        1. Run <code>gcloud auth application-default login</code><br>
        2. Ensure BigQuery API is enabled for project <code>telecom-project-504210</code><br>
        3. Refresh the dashboard — all charts populate automatically.
        </div>""", unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────
# TAB 7 — DATA EXPLORER
# ───────────────────────────────────────────────────────────────────
with tab7:
    st.markdown("""<div class="section-header">
        <span class="section-pill">Explorer</span>
        <h3 class="section-title">📋 Consolidated Data Explorer & CSV Export</h3>
    </div>""", unsafe_allow_html=True)

    source = st.selectbox("Select Data Source", [
        "💳 Financial Payments (Batch CSV)",
        "📞 Call Data Records (Stream JSON)",
        "💸 Money Transfers (Stream JSON)",
        "🎫 Zendesk Tickets (SaaS JSON)",
        "🚨 Fraud Prevention Mart (BigQuery)",
        "👥 Customer 360 Mart (BigQuery)",
        "💰 Revenue Analytics Mart (BigQuery)",
        "📶 Network Quality Mart (BigQuery)",
        "🌍 Corridor Analytics Mart (BigQuery)",
    ])

    df_show = {
        "Financial Payments": df_payments,
        "Call Data Records":  df_cdrs,
        "Money Transfers":    df_transfers,
        "Zendesk Tickets":    df_zendesk,
        "Fraud Prevention":   df_fraud,
        "Customer 360":       df_cust,
        "Revenue Analytics":  df_rev,
        "Network Quality":    df_network,
        "Corridor Analytics": df_corridor,
    }.get(next((k for k in ["Financial Payments","Call Data Records","Money Transfers",
                             "Zendesk Tickets","Fraud Prevention","Customer 360",
                             "Revenue Analytics","Network Quality","Corridor Analytics"]
                if k in source), ""), pd.DataFrame())

    if not df_show.empty:
        ec1, ec2, ec3, ec4 = st.columns(4)
        ec1.metric("Rows",    f"{len(df_show):,}")
        ec2.metric("Columns", str(df_show.shape[1]))
        ec3.metric("Null %",  f"{df_show.isnull().mean().mean()*100:.1f}%")
        ec4.metric("Memory",  f"{df_show.memory_usage(deep=True).sum()/1024:.1f} KB")

        search = st.text_input("🔍 Search across all columns", "", key="exp_search")
        if search:
            mask = df_show.astype(str).apply(lambda c: c.str.contains(search, case=False, na=False)).any(axis=1)
            df_show = df_show[mask]
            st.caption(f"Showing {len(df_show):,} matching rows")

        st.dataframe(df_show, use_container_width=True, height=420)
        csv_out = df_show.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download as CSV", data=csv_out,
                           file_name=f"rebtel_{source[:20].strip().lower().replace(' ','_')}.csv",
                           mime="text/csv", type="primary")
    else:
        bq_needed = "BigQuery" in source or "Mart" in source
        msg = "BigQuery data not available — connect GCP credentials." if bq_needed else "Local data file not found."
        st.markdown(f'<div class="insight-box warn">⚠️ {msg}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#64748b;font-size:0.82rem;padding:16px 0 6px;letter-spacing:0.04em;font-weight:500;">
    📡 Rebtel Telecom &amp; Fintech &nbsp;|&nbsp; Enterprise Business Intelligence Hub
</div>
""", unsafe_allow_html=True)
