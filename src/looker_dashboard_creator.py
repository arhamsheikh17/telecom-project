"""
Looker Studio Dashboard Creator & Validator
============================================
For: Rebtel Telecom — Business Intelligence Dashboard
Project: telecom-project-504210 | Dataset: rebtel_analytics

This script does two things:
  1. Validates that all 5 BigQuery mart tables are populated and ready.
  2. Generates dashboard_spec.json with exact Looker Studio chart configurations.
  3. Prints step-by-step Looker Studio setup instructions with deep-link URLs.

Usage:
    python src/looker_dashboard_creator.py

Output:
    dashboard_spec.json (in project root)
    Console: Validation results + Looker Studio setup guide
"""

import io
import json
import sys
from datetime import datetime
from google.cloud import bigquery

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError with emoji/box-drawing chars)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ID = "telecom-project-504210"
DATASET    = "rebtel_analytics"

# ── BigQuery client ───────────────────────────────────────────────────────────
try:
    client = bigquery.Client(project=PROJECT_ID)
except Exception as e:
    print(f"[ERROR] Failed to create BigQuery client: {e}")
    print("Make sure GOOGLE_APPLICATION_CREDENTIALS is set or 'gcloud auth application-default login' was run.")
    sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1: VALIDATE ALL MART TABLES
# ══════════════════════════════════════════════════════════════════════════════

MART_TABLES = {
    "mart_fraud_prevention":   "Fraud risk classification per user",
    "mart_customer_360":       "Customer segments, health scores, churn risk",
    "mart_revenue_analytics":  "Revenue, LTV, unit economics",
    "mart_network_quality":    "Network SLA & call quality KPIs",
    "mart_corridor_analytics": "Remittance corridor intelligence",
}

print("\n" + "=" * 70)
print("  REBTEL TELECOM — Looker Studio Dashboard Creator")
print(f"  Project: {PROJECT_ID} | Dataset: {DATASET}")
print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70 + "\n")

print("[ STEP 1 ] Validating BigQuery Mart Tables...\n")

validation_results = {}
all_pass = True
total_rows = 0

for table, description in MART_TABLES.items():
    full_table = f"`{PROJECT_ID}.{DATASET}.{table}`"
    sql = f"SELECT COUNT(*) AS row_count FROM {full_table}"
    try:
        result = client.query(sql).to_dataframe()
        row_count = int(result["row_count"].iloc[0])
        status = "✅ PASS" if row_count > 0 else "❌ FAIL (no rows)"
        if row_count == 0:
            all_pass = False
        total_rows += row_count
        validation_results[table] = {"row_count": row_count, "status": "PASS" if row_count > 0 else "FAIL"}
    except Exception as e:
        status = f"❌ ERROR: {e}"
        validation_results[table] = {"row_count": 0, "status": "ERROR", "error": str(e)}
        all_pass = False
        row_count = 0

    print(f"  {status:<12} {table:<30} {row_count:>8,} rows   | {description}")

print()
if all_pass:
    print(f"  ✅ ALL TABLES VALIDATED — Total rows across all marts: {total_rows:,}")
else:
    print("  ⚠️  Some tables failed validation. Run the full pipeline (Steps 1–4) first.")

# ── Additional column checks ──────────────────────────────────────────────────
print("\n[ STEP 2 ] Checking Key Dashboard Columns...\n")

KEY_COLUMNS = {
    "mart_fraud_prevention":   ["user_id", "fraud_risk_level", "total_calls",
                                 "call_failure_rate_pct", "total_transfer_usd"],
    "mart_customer_360":       ["user_id", "customer_segment", "customer_health_score", "churn_risk"],
    "mart_revenue_analytics":  ["user_id", "total_revenue", "estimated_ltv"],
    "mart_network_quality":    ["total_calls", "connection_success_rate_pct",
                                "avg_mos_score", "sla_quality_met_pct", "avg_delivery_rate_pct"],
    "mart_corridor_analytics": ["corridor", "corridor_risk", "total_transfers",
                                "total_volume_usd", "fraud_rate_pct"],
}

for table, expected_cols in KEY_COLUMNS.items():
    schema_sql = f"""
        SELECT column_name
        FROM `{PROJECT_ID}.{DATASET}.INFORMATION_SCHEMA.COLUMNS`
        WHERE table_name = '{table}'
    """
    try:
        schema_df = client.query(schema_sql).to_dataframe()
        actual_cols = set(schema_df["column_name"].tolist())
        missing = [c for c in expected_cols if c not in actual_cols]
        if missing:
            print(f"  ⚠️  {table}: Missing columns → {missing}")
        else:
            print(f"  ✅ {table}: All {len(expected_cols)} required columns present")
    except Exception as e:
        print(f"  ❌ {table}: Schema check failed — {e}")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3: GENERATE DASHBOARD_SPEC.JSON
# ══════════════════════════════════════════════════════════════════════════════

print("\n[ STEP 3 ] Generating dashboard_spec.json...\n")

DASHBOARD_SPEC = {
    "dashboard_name": "Rebtel Telecom — Business Intelligence Dashboard",
    "project_id":     PROJECT_ID,
    "dataset":        DATASET,
    "generated_at":   datetime.now().isoformat(),
    "looker_studio_url": "https://lookerstudio.google.com",
    "data_sources": [
        {
            "id": "ds_fraud",
            "table": "mart_fraud_prevention",
            "display_name": "Fraud Prevention",
            "description": "Fraud risk classification per user",
        },
        {
            "id": "ds_customer",
            "table": "mart_customer_360",
            "display_name": "Customer 360",
            "description": "Customer segments, health scores, churn risk",
        },
        {
            "id": "ds_revenue",
            "table": "mart_revenue_analytics",
            "display_name": "Revenue Analytics",
            "description": "Revenue, LTV, unit economics",
        },
        {
            "id": "ds_network",
            "table": "mart_network_quality",
            "display_name": "Network Quality",
            "description": "Network SLA & call quality KPIs",
        },
        {
            "id": "ds_corridor",
            "table": "mart_corridor_analytics",
            "display_name": "Corridor Analytics",
            "description": "Remittance corridor intelligence",
        },
    ],
    "filters": [
        {
            "id":          "filter_segment",
            "label":       "Customer Segment",
            "data_source": "ds_customer",
            "field":       "customer_segment",
            "type":        "list",
        },
        {
            "id":          "filter_fraud_risk",
            "label":       "Fraud Risk Level",
            "data_source": "ds_fraud",
            "field":       "fraud_risk_level",
            "type":        "list",
        },
        {
            "id":          "filter_churn",
            "label":       "Churn Risk",
            "data_source": "ds_customer",
            "field":       "churn_risk",
            "type":        "list",
        },
        {
            "id":          "filter_corridor_risk",
            "label":       "Corridor Risk",
            "data_source": "ds_corridor",
            "field":       "corridor_risk",
            "type":        "list",
        },
    ],
    "charts": [
        {
            "id":          "chart_01",
            "title":       "Fraud Risk Distribution",
            "type":        "PIE_CHART",
            "data_source": "ds_fraud",
            "dimension":   "fraud_risk_level",
            "metric":      "COUNT(user_id)",
            "colors": {
                "CRITICAL":        "#f85149",
                "HIGH_RISK_FRAUD": "#ff9f43",
                "MEDIUM_RISK":     "#d29922",
                "LOW_RISK":        "#3fb950",
                "SAFE":            "#58a6ff",
            },
            "sql": (
                f"SELECT fraud_risk_level, COUNT(user_id) AS user_count "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_fraud_prevention` "
                f"GROUP BY fraud_risk_level "
                f"ORDER BY user_count DESC"
            ),
            "layout": {"row": 0, "col": 0, "width": 6, "height": 4},
        },
        {
            "id":              "chart_02",
            "title":           "Customer Segments",
            "type":            "BAR_CHART",
            "data_source":     "ds_customer",
            "dimension":       "customer_segment",
            "metric":          "COUNT(user_id)",
            "secondary_metric": "AVG(customer_health_score)",
            "sql": (
                f"SELECT customer_segment, COUNT(user_id) AS users, "
                f"ROUND(AVG(customer_health_score), 1) AS avg_health_score "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_customer_360` "
                f"GROUP BY customer_segment ORDER BY users DESC"
            ),
            "layout": {"row": 0, "col": 6, "width": 6, "height": 4},
        },
        {
            "id":          "chart_03",
            "title":       "Customer Health Score by Segment",
            "type":        "COLUMN_CHART",
            "data_source": "ds_customer",
            "dimension":   "customer_segment",
            "metric":      "AVG(customer_health_score)",
            "breakdown":   "churn_risk",
            "sql": (
                f"SELECT customer_segment, churn_risk, "
                f"ROUND(AVG(customer_health_score), 1) AS avg_health, "
                f"COUNT(user_id) AS users "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_customer_360` "
                f"GROUP BY customer_segment, churn_risk"
            ),
            "layout": {"row": 1, "col": 0, "width": 8, "height": 4},
        },
        {
            "id":              "chart_04",
            "title":           "Revenue by Subscription Plan",
            "type":            "BAR_CHART",
            "data_source":     "ds_revenue",
            "dimension":       "latest_subscription_plan",
            "metric":          "SUM(total_revenue)",
            "secondary_metric": "AVG(estimated_ltv)",
            "sql": (
                f"SELECT p.latest_subscription_plan, "
                f"COUNT(r.user_id) AS users, "
                f"ROUND(SUM(r.total_revenue), 2) AS total_revenue, "
                f"ROUND(AVG(r.estimated_ltv), 2) AS avg_ltv "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_revenue_analytics` r "
                f"JOIN `{PROJECT_ID}.{DATASET}.fct_payments` p ON r.user_id = p.user_id "
                f"GROUP BY p.latest_subscription_plan "
                f"ORDER BY total_revenue DESC"
            ),
            "layout": {"row": 1, "col": 8, "width": 4, "height": 4},
        },
        {
            "id":          "chart_05",
            "title":       "Top Money Transfer Corridors",
            "type":        "TABLE",
            "data_source": "ds_corridor",
            "dimensions":  ["corridor", "corridor_risk"],
            "metrics":     ["total_transfers", "total_volume_usd", "fraud_rate_pct"],
            "sort":        "total_volume_usd DESC",
            "heatmap_on":  "fraud_rate_pct",
            "sql": (
                f"SELECT corridor, corridor_risk, total_transfers, "
                f"total_volume_usd, fraud_rate_pct "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_corridor_analytics` "
                f"ORDER BY total_volume_usd DESC LIMIT 20"
            ),
            "layout": {"row": 2, "col": 0, "width": 12, "height": 5},
        },
        {
            "id":          "chart_06a",
            "title":       "Connection Success Rate",
            "type":        "SCORECARD",
            "data_source": "ds_network",
            "metric":      "connection_success_rate_pct",
            "target":      98.0,
            "target_unit": "%",
            "sql": (
                f"SELECT connection_success_rate_pct "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_network_quality`"
            ),
            "layout": {"row": 3, "col": 0, "width": 3, "height": 2},
        },
        {
            "id":          "chart_06b",
            "title":       "Avg MOS Score",
            "type":        "SCORECARD",
            "data_source": "ds_network",
            "metric":      "avg_mos_score",
            "target":      4.0,
            "target_unit": "score",
            "sql": (
                f"SELECT avg_mos_score "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_network_quality`"
            ),
            "layout": {"row": 3, "col": 3, "width": 3, "height": 2},
        },
        {
            "id":          "chart_06c",
            "title":       "SLA Quality Met",
            "type":        "SCORECARD",
            "data_source": "ds_network",
            "metric":      "sla_quality_met_pct",
            "target":      95.0,
            "target_unit": "%",
            "sql": (
                f"SELECT sla_quality_met_pct "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_network_quality`"
            ),
            "layout": {"row": 3, "col": 6, "width": 3, "height": 2},
        },
        {
            "id":          "chart_06d",
            "title":       "Avg Delivery Rate",
            "type":        "SCORECARD",
            "data_source": "ds_network",
            "metric":      "avg_delivery_rate_pct",
            "target":      95.0,
            "target_unit": "%",
            "sql": (
                f"SELECT avg_delivery_rate_pct "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_network_quality`"
            ),
            "layout": {"row": 3, "col": 9, "width": 3, "height": 2},
        },
        {
            "id":          "chart_07",
            "title":       "Churn Risk Distribution",
            "type":        "DONUT_CHART",
            "data_source": "ds_customer",
            "dimension":   "churn_risk",
            "metric":      "COUNT(user_id)",
            "colors": {"HIGH": "#f85149", "MEDIUM": "#d29922", "LOW": "#3fb950"},
            "sql": (
                f"SELECT churn_risk, COUNT(user_id) AS user_count "
                f"FROM `{PROJECT_ID}.{DATASET}.mart_customer_360` "
                f"GROUP BY churn_risk"
            ),
            "layout": {"row": 4, "col": 0, "width": 4, "height": 4},
        },
    ],
    "layout_description": """
    ┌─────────────────────────────────────────────────────────────────┐
    │  REBTEL TELECOM — Business Intelligence Dashboard               │
    ├──────────────┬──────────────┬──────────────┬───────────────────┤
    │  Scorecard:  │  Scorecard:  │  Scorecard:  │  Scorecard:       │
    │  Conn Rate   │  MOS Score   │  SLA Quality │  Delivery Rate    │
    ├──────────────────────────┬──────────────────────────────────────┤
    │  Fraud Risk Pie Chart    │  Customer Segments Bar Chart         │
    │  (mart_fraud_prevention) │  (mart_customer_360)                 │
    ├──────────────────────────┴──────────────────────────────────────┤
    │  Customer Health Score Histogram + Churn Risk Donut             │
    ├──────────────────────────────────────────────────────────────────┤
    │  Revenue by Plan Bar + Call Failure Rate Bar                    │
    ├──────────────────────────────────────────────────────────────────┤
    │  Top Corridors Scatter/Table (mart_corridor_analytics)          │
    ├──────────────────────────────────────────────────────────────────┤
    │  Detailed Fraud Risk Report Table                               │
    └──────────────────────────────────────────────────────────────────┘
    """,
}

spec_path = "dashboard_spec.json"
with open(spec_path, "w", encoding="utf-8") as f:
    json.dump(DASHBOARD_SPEC, f, indent=2)

print(f"  ✅ dashboard_spec.json written → {spec_path}")
print(f"     {len(DASHBOARD_SPEC['charts'])} charts | "
      f"{len(DASHBOARD_SPEC['data_sources'])} data sources | "
      f"{len(DASHBOARD_SPEC['filters'])} filters\n")

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4: PRINT LOOKER STUDIO SETUP GUIDE
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 70)
print("  LOOKER STUDIO SETUP GUIDE")
print("=" * 70)

guide = f"""
  URL: https://lookerstudio.google.com
  → Click "Create" → "Report"

  ┌─ STEP A: Connect BigQuery Data Sources ─────────────────────────────┐
  │  For each table below, add a BigQuery data source:                  │
  │                                                                     │
  │  Project:  {PROJECT_ID}                        │
  │  Dataset:  {DATASET}                                   │
  │                                                                     │
  │  Tables to add:                                                     │
  │    1. mart_fraud_prevention     (Fraud Risk)                        │
  │    2. mart_customer_360         (Customer Segments & Health)        │
  │    3. mart_revenue_analytics    (Revenue & LTV)                     │
  │    4. mart_network_quality      (Network SLA KPIs)                  │
  │    5. mart_corridor_analytics   (Remittance Corridors)              │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP B: Add Filters (top of dashboard) ────────────────────────────┐
  │  1. List filter → mart_customer_360 → customer_segment             │
  │  2. List filter → mart_fraud_prevention → fraud_risk_level         │
  │  3. List filter → mart_customer_360 → churn_risk                   │
  │  4. List filter → mart_corridor_analytics → corridor_risk          │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP C: Add 4 Scorecard Charts (Network SLA) ──────────────────────┐
  │  Data source: mart_network_quality                                  │
  │  Scorecard 1: connection_success_rate_pct  Target: 98%             │
  │  Scorecard 2: avg_mos_score                Target: 4.0             │
  │  Scorecard 3: sla_quality_met_pct          Target: 95%             │
  │  Scorecard 4: avg_delivery_rate_pct        Target: 95%             │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP D: Add Chart 1 — Fraud Risk Pie Chart ────────────────────────┐
  │  Type: Pie Chart | Source: mart_fraud_prevention                   │
  │  Dimension: fraud_risk_level | Metric: COUNT(user_id)              │
  │  Colors: CRITICAL=Red, HIGH_RISK=Orange, MEDIUM=Yellow,            │
  │          LOW=Green, SAFE=Blue                                       │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP E: Add Chart 2 — Customer Segments Bar ───────────────────────┐
  │  Type: Bar Chart | Source: mart_customer_360                       │
  │  Dimension: customer_segment | Metric: COUNT(user_id)              │
  │  Secondary Metric: AVG(customer_health_score)                      │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP F: Add Chart 3 — Health Score by Segment ────────────────────┐
  │  Type: Column Chart | Source: mart_customer_360                   │
  │  Dimension: customer_segment | Metric: AVG(customer_health_score) │
  │  Breakdown: churn_risk                                             │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP G: Add Chart 4 — Revenue by Subscription Plan ───────────────┐
  │  Type: Bar Chart | Source: mart_revenue_analytics                 │
  │  Dimension: subscription_plan | Metric: SUM(total_revenue)        │
  │  Secondary Metric: AVG(estimated_ltv)                             │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP H: Add Chart 5 — Top Remittance Corridors Table ─────────────┐
  │  Type: Table | Source: mart_corridor_analytics                    │
  │  Dimensions: corridor, corridor_risk                               │
  │  Metrics: total_transfers, total_volume_usd, fraud_rate_pct       │
  │  Sort: total_volume_usd DESC | Heatmap: fraud_rate_pct (Red=High) │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP I: Add Chart 7 — Churn Risk Donut ───────────────────────────┐
  │  Type: Donut Chart | Source: mart_customer_360                    │
  │  Dimension: churn_risk | Metric: COUNT(user_id)                   │
  │  Colors: HIGH=Red, MEDIUM=Yellow, LOW=Green                        │
  └─────────────────────────────────────────────────────────────────────┘

  ┌─ STEP J: Share & Publish ───────────────────────────────────────────┐
  │  → Click "Share" → "Manage access"                                 │
  │  → Set to "Anyone with the link can view"                          │
  │  → Copy the dashboard share link                                   │
  └─────────────────────────────────────────────────────────────────────┘

  ════════════════════════════════════════════════════════════════════════
  ALTERNATIVE: Run the Streamlit Dashboard (immediate, no manual setup)
  ════════════════════════════════════════════════════════════════════════
    python -m streamlit run src/dashboard.py

  This Streamlit dashboard is a pixel-perfect equivalent of the Looker
  Studio spec and connects to the same BigQuery tables live.
"""

print(guide)

print("=" * 70)
print(f"  ✅ Setup complete. dashboard_spec.json saved.")
print(f"     Run Streamlit: python -m streamlit run src/dashboard.py")
print("=" * 70 + "\n")
