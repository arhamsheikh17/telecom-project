"""Full BigQuery verification — checks all 17 tables across raw + analytics layers."""
from google.cloud import bigquery

client = bigquery.Client(project="telecom-project-504210")

tables = [
    ("rebtel_raw_airbyte", "raw_airbyte_zendesk_tickets", "RAW"),
    ("rebtel_raw_stream",  "raw_stream_cdrs",              "RAW"),
    ("rebtel_raw_stream",  "raw_stream_money_transfers",   "RAW"),
    ("rebtel_raw_batch",   "raw_batch_payments",           "RAW"),
    ("rebtel_analytics",   "stg_airbyte_zendesk",          "STG"),
    ("rebtel_analytics",   "stg_stream_cdrs",              "STG"),
    ("rebtel_analytics",   "stg_stream_transfers",         "STG"),
    ("rebtel_analytics",   "stg_batch_payments",           "STG"),
    ("rebtel_analytics",   "fct_telecom_calls",            "FACT"),
    ("rebtel_analytics",   "fct_financial_transfers",      "FACT"),
    ("rebtel_analytics",   "fct_support_tickets",          "FACT"),
    ("rebtel_analytics",   "fct_payments",                 "FACT"),
    ("rebtel_analytics",   "mart_fraud_prevention",        "MART"),
    ("rebtel_analytics",   "mart_customer_360",            "MART"),
    ("rebtel_analytics",   "mart_revenue_analytics",       "MART"),
    ("rebtel_analytics",   "mart_network_quality",         "MART"),
    ("rebtel_analytics",   "mart_corridor_analytics",      "MART"),
]

print("=" * 75)
print("BIGQUERY WAREHOUSE — FULL VERIFICATION")
print("=" * 75)
header = f"{'Layer':<6} {'Dataset.Table':<55} {'Rows':>8}"
print(header)
print("-" * 75)

all_pass = True
for ds, tbl, layer in tables:
    ref = f"telecom-project-504210.{ds}.{tbl}"
    try:
        t = client.get_table(ref)
        status = "OK" if t.num_rows > 0 else "EMPTY"
        if t.num_rows == 0:
            all_pass = False
        print(f"[{layer:<4}] {ds}.{tbl:<50} {t.num_rows:>8}  {status}")
    except Exception as e:
        all_pass = False
        print(f"[{layer:<4}] {ds}.{tbl:<50} {'N/A':>8}  MISSING")

# -- Fraud Mart Breakdown --
print(f"\n{'='*75}")
print("MART: Fraud Prevention -- Risk Distribution")
print("-" * 40)
q1 = """
    SELECT fraud_risk_level, COUNT(*) AS cnt
    FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
    GROUP BY fraud_risk_level ORDER BY cnt DESC
"""
for r in client.query(q1).result():
    print(f"  {r.fraud_risk_level:<20} {r.cnt:>5} users")

# -- Customer 360 Breakdown --
print(f"\nMART: Customer 360 -- Segments & Churn Risk")
print("-" * 55)
q2 = """
    SELECT customer_segment, churn_risk,
           COUNT(*) AS cnt,
           ROUND(AVG(customer_health_score),1) AS avg_health
    FROM `telecom-project-504210.rebtel_analytics.mart_customer_360`
    GROUP BY customer_segment, churn_risk ORDER BY cnt DESC
"""
print(f"  {'Segment':<15} {'Churn Risk':<22} {'Users':>6} {'Health':>8}")
for r in client.query(q2).result():
    print(f"  {r.customer_segment:<15} {r.churn_risk:<22} {r.cnt:>6} {r.avg_health:>8}")

# -- Network Quality KPIs --
print(f"\nMART: Network Quality -- SLA Metrics")
print("-" * 40)
q3 = """
    SELECT total_calls, connection_success_rate_pct, avg_mos_score,
           avg_delivery_rate_pct, sla_quality_met_pct, sla_connection_met_pct
    FROM `telecom-project-504210.rebtel_analytics.mart_network_quality`
"""
for r in client.query(q3).result():
    print(f"  Total Calls:              {r.total_calls}")
    print(f"  Connection Success Rate:  {r.connection_success_rate_pct}%")
    print(f"  Avg MOS Score:            {r.avg_mos_score}")
    print(f"  Avg Delivery Rate:        {r.avg_delivery_rate_pct}%")
    print(f"  SLA Quality Met:          {r.sla_quality_met_pct}%  (target: 95%)")
    print(f"  SLA Connection Met:       {r.sla_connection_met_pct}%  (target: 98%)")

# -- Top 5 Corridors --
print(f"\nMART: Corridor Analytics -- Top 5 by Volume")
print("-" * 55)
q4 = """
    SELECT corridor, total_transfers, total_volume_usd, fraud_rate_pct, corridor_risk
    FROM `telecom-project-504210.rebtel_analytics.mart_corridor_analytics`
    ORDER BY total_volume_usd DESC LIMIT 5
"""
print(f"  {'Corridor':<20} {'Txns':>6} {'Volume USD':>12} {'Fraud%':>8} {'Risk':<20}")
for r in client.query(q4).result():
    print(f"  {r.corridor:<20} {r.total_transfers:>6} {r.total_volume_usd:>12.2f} {r.fraud_rate_pct:>7.1f}% {r.corridor_risk:<20}")

# -- JOIN integrity --
print(f"\nDATA INTEGRITY -- user_id coverage across mart_fraud_prevention")
print("-" * 55)
q5 = """
    SELECT
        COUNT(DISTINCT user_id) AS total_users,
        COUNTIF(total_calls IS NOT NULL) AS with_calls,
        COUNTIF(total_transfers IS NOT NULL) AS with_transfers,
        COUNTIF(support_tickets IS NOT NULL) AS with_tickets
    FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
"""
for r in client.query(q5).result():
    print(f"  Total unique users:       {r.total_users}")
    print(f"  Users with call data:     {r.with_calls}")
    print(f"  Users with transfer data: {r.with_transfers}")
    print(f"  Users with ticket data:   {r.with_tickets}")

# -- Duplicate check --
q6 = """
    SELECT user_id, COUNT(*) AS c
    FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
    GROUP BY user_id HAVING COUNT(*) > 1
"""
dupes = list(client.query(q6).result())
print(f"  Duplicate user_ids:       {len(dupes)}  {'PASS' if len(dupes)==0 else 'FAIL'}")

print(f"\n{'='*75}")
overall = "ALL CHECKS PASSED" if all_pass and len(dupes) == 0 else "SOME CHECKS FAILED"
print(f"OVERALL: {overall}")
print(f"{'='*75}")
