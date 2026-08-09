"""
Step 4b: dbt Transformation Runner (Python-based)
Executes SQL transformation models directly via BigQuery Python client,
replicating what dbt Cloud would do.

Layer Architecture:
  1. STAGING LAYER    - Clean, standardize, deduplicate raw data
  2. FACT TABLES      - Core business metrics aggregated per user
  3. ANALYTICS MARTS  - Cross-domain business intelligence
     - mart_fraud_prevention    -> ML Fraud risk classification
     - mart_customer_360        -> Unified customer health profile
     - mart_revenue_analytics   -> Revenue, churn, LTV insights
     - mart_network_quality     -> Telecom network SLA & quality KPIs
     - mart_corridor_analytics  -> Money transfer corridor intelligence
"""

from google.cloud import bigquery

PROJECT_ID = "telecom-project-504210"
client = bigquery.Client(project=PROJECT_ID)

# Ordered dict to ensure correct execution sequence (staging -> facts -> marts)
MODELS = {}

# ==============================================================================
# LAYER 1: STAGING (Clean & Standardize)
# ==============================================================================

MODELS["rebtel_analytics.stg_airbyte_zendesk"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.stg_airbyte_zendesk` AS
    SELECT
        ticket_id,
        user_id,
        TIMESTAMP(created_at)          AS created_at,
        TIMESTAMP(updated_at)          AS updated_at,
        LOWER(TRIM(issue_category))    AS issue_category,
        LOWER(TRIM(priority))          AS priority,
        LOWER(TRIM(ticket_status))     AS ticket_status,
        satisfaction_score,
        _airbyte_ab_id,
        _airbyte_emitted_at,
        -- Derived: resolution time in hours
        TIMESTAMP_DIFF(TIMESTAMP(updated_at), TIMESTAMP(created_at), HOUR) AS resolution_hours
    FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`
    WHERE ticket_id IS NOT NULL AND user_id IS NOT NULL
"""

MODELS["rebtel_analytics.stg_stream_cdrs"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.stg_stream_cdrs` AS
    SELECT
        call_id,
        user_id,
        COALESCE(duration_seconds, 0)                  AS duration_seconds,
        COALESCE(connection_success, FALSE)             AS connection_success,
        ROUND(COALESCE(call_quality_score, 0), 2)       AS call_quality_score,
        ROUND(COALESCE(delivery_rate_percent, 0), 2)    AS delivery_rate_percent,
        TIMESTAMP(timestamp)                            AS event_timestamp,
        -- Derived: call duration category for reporting
        CASE
            WHEN COALESCE(duration_seconds, 0) = 0         THEN 'no_connection'
            WHEN COALESCE(duration_seconds, 0) < 30        THEN 'very_short'
            WHEN COALESCE(duration_seconds, 0) < 120       THEN 'short'
            WHEN COALESCE(duration_seconds, 0) < 600       THEN 'medium'
            ELSE                                                'long'
        END AS call_duration_bucket,
        -- Derived: quality tier
        CASE
            WHEN COALESCE(call_quality_score, 0) >= 4.0    THEN 'excellent'
            WHEN COALESCE(call_quality_score, 0) >= 3.0    THEN 'good'
            WHEN COALESCE(call_quality_score, 0) >= 2.0    THEN 'fair'
            ELSE                                                'poor'
        END AS quality_tier
    FROM `telecom-project-504210.rebtel_raw_stream.raw_stream_cdrs`
    WHERE call_id IS NOT NULL AND user_id IS NOT NULL
"""

MODELS["rebtel_analytics.stg_stream_transfers"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.stg_stream_transfers` AS
    SELECT
        transfer_id,
        user_id,
        UPPER(TRIM(sender_country))    AS sender_country,
        UPPER(TRIM(receiver_country))  AS receiver_country,
        ROUND(COALESCE(transfer_amount_usd, 0), 2) AS transfer_amount_usd,
        COALESCE(is_fraud_flag, FALSE) AS is_fraud_flag,
        -- Derived: transfer size tier (for remittance analytics)
        CASE
            WHEN COALESCE(transfer_amount_usd, 0) < 50     THEN 'micro'
            WHEN COALESCE(transfer_amount_usd, 0) < 200    THEN 'small'
            WHEN COALESCE(transfer_amount_usd, 0) < 500    THEN 'medium'
            WHEN COALESCE(transfer_amount_usd, 0) < 1000   THEN 'large'
            ELSE                                                 'very_large'
        END AS transfer_size_tier,
        -- Derived: corridor (sender -> receiver)
        CONCAT(UPPER(TRIM(sender_country)), ' -> ', UPPER(TRIM(receiver_country))) AS corridor
    FROM `telecom-project-504210.rebtel_raw_stream.raw_stream_money_transfers`
    WHERE transfer_id IS NOT NULL AND user_id IS NOT NULL
"""

MODELS["rebtel_analytics.stg_batch_payments"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.stg_batch_payments` AS
    SELECT
        transaction_id,
        user_id,
        LOWER(TRIM(subscription_plan)) AS subscription_plan,
        ROUND(COALESCE(payment_amount, 0), 2) AS payment_amount,
        LOWER(TRIM(payment_status))    AS payment_status,
        -- Derived: is the payment successful?
        CASE
            WHEN LOWER(TRIM(payment_status)) IN ('completed', 'success', 'paid') THEN TRUE
            ELSE FALSE
        END AS is_payment_successful
    FROM `telecom-project-504210.rebtel_raw_batch.raw_batch_payments`
    WHERE transaction_id IS NOT NULL AND user_id IS NOT NULL
"""

# ==============================================================================
# LAYER 2: FACT TABLES (Core business metrics per user)
# ==============================================================================

MODELS["rebtel_analytics.fct_telecom_calls"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.fct_telecom_calls` AS
    SELECT
        user_id,
        COUNT(*)                                                            AS total_calls,
        COUNTIF(connection_success = FALSE)                                 AS failed_calls,
        COUNTIF(connection_success = TRUE)                                  AS successful_calls,
        ROUND(AVG(duration_seconds), 2)                                     AS avg_duration_seconds,
        ROUND(MAX(duration_seconds), 2)                                     AS max_duration_seconds,
        ROUND(SUM(duration_seconds), 2)                                     AS total_duration_seconds,
        ROUND(AVG(call_quality_score), 2)                                   AS avg_quality_score,
        ROUND(MIN(call_quality_score), 2)                                   AS min_quality_score,
        ROUND(AVG(delivery_rate_percent), 2)                                AS avg_delivery_rate_pct,
        ROUND(COUNTIF(connection_success = FALSE) * 100.0 / NULLIF(COUNT(*), 0), 2) AS call_failure_rate_pct,
        -- Call pattern metrics
        COUNTIF(call_duration_bucket = 'no_connection')                     AS no_connection_calls,
        COUNTIF(quality_tier = 'poor')                                      AS poor_quality_calls,
        COUNTIF(quality_tier = 'excellent')                                  AS excellent_quality_calls
    FROM `telecom-project-504210.rebtel_analytics.stg_stream_cdrs`
    GROUP BY user_id
"""

MODELS["rebtel_analytics.fct_financial_transfers"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.fct_financial_transfers` AS
    SELECT
        user_id,
        COUNT(*)                                   AS total_transfers,
        ROUND(SUM(transfer_amount_usd), 2)         AS total_transfer_usd,
        ROUND(AVG(transfer_amount_usd), 2)         AS avg_transfer_usd,
        ROUND(MAX(transfer_amount_usd), 2)         AS max_transfer_usd,
        ROUND(MIN(transfer_amount_usd), 2)         AS min_transfer_usd,
        COUNTIF(is_fraud_flag = TRUE)               AS fraud_transfers,
        ROUND(COUNTIF(is_fraud_flag = TRUE) * 100.0 / NULLIF(COUNT(*), 0), 2) AS fraud_rate_pct,
        COUNT(DISTINCT sender_country)              AS distinct_sender_countries,
        COUNT(DISTINCT receiver_country)            AS distinct_receiver_countries,
        COUNT(DISTINCT corridor)                    AS distinct_corridors,
        -- Transfer size distribution
        COUNTIF(transfer_size_tier = 'very_large')  AS very_large_transfers,
        COUNTIF(transfer_size_tier = 'micro')       AS micro_transfers
    FROM `telecom-project-504210.rebtel_analytics.stg_stream_transfers`
    GROUP BY user_id
"""

MODELS["rebtel_analytics.fct_support_tickets"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.fct_support_tickets` AS
    SELECT
        user_id,
        COUNT(*)                                        AS total_tickets,
        COUNTIF(issue_category = 'fraud_alert')         AS fraud_tickets,
        COUNTIF(issue_category = 'payment_failure')     AS payment_failure_tickets,
        COUNTIF(issue_category = 'call_drop')           AS call_drop_tickets,
        COUNTIF(issue_category = 'topup_delay')         AS topup_delay_tickets,
        ROUND(AVG(satisfaction_score), 2)               AS avg_satisfaction_score,
        ROUND(AVG(resolution_hours), 2)                 AS avg_resolution_hours,
        COUNTIF(ticket_status = 'open')                 AS open_tickets,
        COUNTIF(ticket_status = 'pending')              AS pending_tickets,
        COUNTIF(ticket_status = 'solved')               AS solved_tickets,
        COUNTIF(ticket_status = 'closed')               AS closed_tickets,
        COUNTIF(priority = 'urgent')                    AS urgent_tickets,
        COUNTIF(priority = 'high')                      AS high_priority_tickets
    FROM `telecom-project-504210.rebtel_analytics.stg_airbyte_zendesk`
    GROUP BY user_id
"""

MODELS["rebtel_analytics.fct_payments"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.fct_payments` AS
    SELECT
        user_id,
        COUNT(*)                                   AS total_payments,
        ROUND(SUM(payment_amount), 2)              AS total_payment_amount,
        ROUND(AVG(payment_amount), 2)              AS avg_payment_amount,
        COUNTIF(is_payment_successful = TRUE)       AS successful_payments,
        COUNTIF(is_payment_successful = FALSE)      AS failed_payments,
        ROUND(COUNTIF(is_payment_successful = FALSE) * 100.0 / NULLIF(COUNT(*), 0), 2) AS payment_failure_rate_pct,
        COUNT(DISTINCT subscription_plan)           AS distinct_plans,
        -- Latest plan (approximation)
        MAX(subscription_plan)                      AS latest_subscription_plan
    FROM `telecom-project-504210.rebtel_analytics.stg_batch_payments`
    GROUP BY user_id
"""

# ==============================================================================
# LAYER 3: ANALYTICS MARTS (Cross-domain business intelligence)
# ==============================================================================

# ---- MART 1: Fraud Prevention (ML-ready risk classification) ----
MODELS["rebtel_analytics.mart_fraud_prevention"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.mart_fraud_prevention` AS
    WITH cdrs AS (
        SELECT * FROM `telecom-project-504210.rebtel_analytics.fct_telecom_calls`
    ),
    transfers AS (
        SELECT * FROM `telecom-project-504210.rebtel_analytics.fct_financial_transfers`
    ),
    tickets AS (
        SELECT * FROM `telecom-project-504210.rebtel_analytics.fct_support_tickets`
    )
    SELECT
        COALESCE(c.user_id, t.user_id, k.user_id) AS user_id,
        -- Call metrics
        c.total_calls,
        c.failed_calls,
        c.call_failure_rate_pct,
        c.avg_quality_score,
        c.avg_delivery_rate_pct,
        c.poor_quality_calls,
        -- Transfer metrics
        t.total_transfers,
        t.total_transfer_usd,
        t.avg_transfer_usd,
        t.fraud_transfers,
        t.fraud_rate_pct,
        t.very_large_transfers,
        -- Support ticket metrics
        k.total_tickets          AS support_tickets,
        k.fraud_tickets,
        k.avg_satisfaction_score,
        -- Composite fraud signals
        COALESCE(t.fraud_transfers, 0) + COALESCE(k.fraud_tickets, 0) AS total_fraud_signals,
        -- ML Fraud Risk Classification (multi-factor scoring)
        CASE
            WHEN (COALESCE(t.fraud_transfers, 0) > 0 AND COALESCE(k.fraud_tickets, 0) > 0)
                THEN 'CRITICAL_RISK'
            WHEN COALESCE(t.fraud_transfers, 0) > 0
              OR COALESCE(k.fraud_tickets, 0) > 0
                THEN 'HIGH_RISK_FRAUD'
            WHEN COALESCE(c.call_failure_rate_pct, 0) > 30.0
              OR COALESCE(t.total_transfer_usd, 0) > 900
              OR COALESCE(t.very_large_transfers, 0) > 2
                THEN 'MEDIUM_RISK'
            WHEN COALESCE(c.call_failure_rate_pct, 0) > 15.0
              OR COALESCE(k.total_tickets, 0) > 5
                THEN 'LOW_RISK'
            ELSE 'SAFE'
        END AS fraud_risk_level,
        CURRENT_TIMESTAMP() AS mart_refreshed_at
    FROM cdrs c
    FULL OUTER JOIN transfers t ON c.user_id = t.user_id
    FULL OUTER JOIN tickets   k ON COALESCE(c.user_id, t.user_id) = k.user_id
"""

# ---- MART 2: Customer 360 (Unified customer health profile) ----
MODELS["rebtel_analytics.mart_customer_360"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.mart_customer_360` AS
    WITH calls AS (
        SELECT * FROM `telecom-project-504210.rebtel_analytics.fct_telecom_calls`
    ),
    transfers AS (
        SELECT * FROM `telecom-project-504210.rebtel_analytics.fct_financial_transfers`
    ),
    tickets AS (
        SELECT * FROM `telecom-project-504210.rebtel_analytics.fct_support_tickets`
    ),
    payments AS (
        SELECT * FROM `telecom-project-504210.rebtel_analytics.fct_payments`
    ),
    fraud AS (
        SELECT user_id, fraud_risk_level FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
    )
    SELECT
        COALESCE(c.user_id, t.user_id, k.user_id, p.user_id) AS user_id,
        -- Engagement: how active is the customer?
        COALESCE(c.total_calls, 0)             AS total_calls,
        COALESCE(t.total_transfers, 0)         AS total_transfers,
        COALESCE(p.total_payments, 0)          AS total_payments,
        COALESCE(k.total_tickets, 0)           AS total_support_tickets,
        COALESCE(c.total_calls, 0) + COALESCE(t.total_transfers, 0) + COALESCE(p.total_payments, 0) AS total_activity_events,
        -- Revenue
        COALESCE(p.total_payment_amount, 0)    AS total_revenue,
        COALESCE(t.total_transfer_usd, 0)      AS total_transfer_volume_usd,
        p.latest_subscription_plan,
        -- Quality of Experience
        COALESCE(c.avg_quality_score, 0)        AS call_quality_score,
        COALESCE(c.call_failure_rate_pct, 0)    AS call_failure_rate_pct,
        COALESCE(k.avg_satisfaction_score, 0)   AS support_satisfaction_score,
        COALESCE(k.avg_resolution_hours, 0)     AS avg_ticket_resolution_hours,
        -- Risk
        f.fraud_risk_level,
        COALESCE(p.payment_failure_rate_pct, 0) AS payment_failure_rate_pct,
        -- Customer Health Score (0-100, higher is better)
        ROUND(
            (COALESCE(c.avg_quality_score, 3) / 5.0 * 25)               -- call quality (25 pts)
            + (COALESCE(k.avg_satisfaction_score, 3) / 5.0 * 25)        -- satisfaction (25 pts)
            + (CASE WHEN COALESCE(c.call_failure_rate_pct, 0) < 10 THEN 25
                    WHEN COALESCE(c.call_failure_rate_pct, 0) < 25 THEN 15
                    WHEN COALESCE(c.call_failure_rate_pct, 0) < 50 THEN 5
                    ELSE 0 END)                                          -- reliability (25 pts)
            + (CASE WHEN f.fraud_risk_level IN ('SAFE', 'LOW_RISK') THEN 25
                    WHEN f.fraud_risk_level = 'MEDIUM_RISK' THEN 10
                    ELSE 0 END)                                          -- trust (25 pts)
        , 1) AS customer_health_score,
        -- Customer Segment
        CASE
            WHEN COALESCE(p.total_payment_amount, 0) > 500
                 AND COALESCE(c.total_calls, 0) > 50
                 AND COALESCE(t.total_transfers, 0) > 20   THEN 'VIP'
            WHEN COALESCE(p.total_payment_amount, 0) > 200
                 OR COALESCE(t.total_transfer_usd, 0) > 500 THEN 'HIGH_VALUE'
            WHEN COALESCE(c.total_calls, 0) > 30
                 OR COALESCE(t.total_transfers, 0) > 10     THEN 'ACTIVE'
            WHEN COALESCE(c.total_calls, 0) > 0
                 OR COALESCE(t.total_transfers, 0) > 0      THEN 'REGULAR'
            ELSE                                                  'INACTIVE'
        END AS customer_segment,
        -- Churn risk flag
        CASE
            WHEN COALESCE(k.total_tickets, 0) > 3
                 AND COALESCE(k.avg_satisfaction_score, 5) < 3.0
                 AND COALESCE(c.call_failure_rate_pct, 0) > 20  THEN 'HIGH_CHURN_RISK'
            WHEN COALESCE(k.total_tickets, 0) > 2
                 OR COALESCE(k.avg_satisfaction_score, 5) < 3.0 THEN 'MODERATE_CHURN_RISK'
            ELSE                                                      'STABLE'
        END AS churn_risk,
        CURRENT_TIMESTAMP() AS refreshed_at
    FROM calls c
    FULL OUTER JOIN transfers t ON c.user_id = t.user_id
    FULL OUTER JOIN tickets   k ON COALESCE(c.user_id, t.user_id) = k.user_id
    FULL OUTER JOIN payments  p ON COALESCE(c.user_id, t.user_id, k.user_id) = p.user_id
    LEFT JOIN fraud f ON COALESCE(c.user_id, t.user_id, k.user_id, p.user_id) = f.user_id
"""

# ---- MART 3: Revenue Analytics ----
MODELS["rebtel_analytics.mart_revenue_analytics"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.mart_revenue_analytics` AS
    SELECT
        p.user_id,
        p.latest_subscription_plan,
        p.total_payments,
        p.total_payment_amount                                         AS total_revenue,
        p.avg_payment_amount                                           AS avg_revenue_per_txn,
        p.successful_payments,
        p.failed_payments,
        p.payment_failure_rate_pct,
        COALESCE(t.total_transfer_usd, 0)                              AS transfer_volume_usd,
        -- Revenue per call (unit economics)
        CASE WHEN COALESCE(c.total_calls, 0) > 0
             THEN ROUND(p.total_payment_amount / c.total_calls, 2)
             ELSE 0 END                                                AS revenue_per_call,
        -- Revenue per transfer (unit economics)
        CASE WHEN COALESCE(t.total_transfers, 0) > 0
             THEN ROUND(p.total_payment_amount / t.total_transfers, 2)
             ELSE 0 END                                                AS revenue_per_transfer,
        -- Customer lifetime value proxy
        ROUND(p.total_payment_amount + COALESCE(t.total_transfer_usd, 0) * 0.05, 2) AS estimated_ltv,
        CURRENT_TIMESTAMP() AS refreshed_at
    FROM `telecom-project-504210.rebtel_analytics.fct_payments` p
    LEFT JOIN `telecom-project-504210.rebtel_analytics.fct_telecom_calls` c ON p.user_id = c.user_id
    LEFT JOIN `telecom-project-504210.rebtel_analytics.fct_financial_transfers` t ON p.user_id = t.user_id
"""

# ---- MART 4: Network Quality KPIs ----
MODELS["rebtel_analytics.mart_network_quality"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.mart_network_quality` AS
    SELECT
        'OVERALL' AS dimension,
        COUNT(*)                                                        AS total_calls,
        COUNTIF(connection_success = TRUE)                              AS connected_calls,
        COUNTIF(connection_success = FALSE)                             AS dropped_calls,
        ROUND(COUNTIF(connection_success = TRUE) * 100.0 / NULLIF(COUNT(*), 0), 2) AS connection_success_rate_pct,
        ROUND(AVG(duration_seconds), 2)                                 AS avg_call_duration_sec,
        ROUND(AVG(call_quality_score), 2)                               AS avg_mos_score,
        ROUND(AVG(delivery_rate_percent), 2)                            AS avg_delivery_rate_pct,
        -- Quality distribution
        COUNTIF(quality_tier = 'excellent')                             AS excellent_calls,
        COUNTIF(quality_tier = 'good')                                  AS good_calls,
        COUNTIF(quality_tier = 'fair')                                  AS fair_calls,
        COUNTIF(quality_tier = 'poor')                                  AS poor_calls,
        -- SLA: % calls with quality >= 3.0 (target: 95%)
        ROUND(COUNTIF(call_quality_score >= 3.0) * 100.0 / NULLIF(COUNT(*), 0), 2) AS sla_quality_met_pct,
        -- SLA: % calls connected (target: 98%)
        ROUND(COUNTIF(connection_success = TRUE) * 100.0 / NULLIF(COUNT(*), 0), 2) AS sla_connection_met_pct,
        -- Duration distribution
        COUNTIF(call_duration_bucket = 'no_connection')                 AS calls_no_connection,
        COUNTIF(call_duration_bucket = 'very_short')                    AS calls_very_short,
        COUNTIF(call_duration_bucket = 'short')                         AS calls_short,
        COUNTIF(call_duration_bucket = 'medium')                        AS calls_medium,
        COUNTIF(call_duration_bucket = 'long')                          AS calls_long,
        CURRENT_TIMESTAMP() AS refreshed_at
    FROM `telecom-project-504210.rebtel_analytics.stg_stream_cdrs`
"""

# ---- MART 5: Corridor Analytics (Money Transfer Routes) ----
MODELS["rebtel_analytics.mart_corridor_analytics"] = """
    CREATE OR REPLACE TABLE `telecom-project-504210.rebtel_analytics.mart_corridor_analytics` AS
    SELECT
        sender_country,
        receiver_country,
        corridor,
        COUNT(*)                                   AS total_transfers,
        COUNT(DISTINCT user_id)                    AS unique_senders,
        ROUND(SUM(transfer_amount_usd), 2)         AS total_volume_usd,
        ROUND(AVG(transfer_amount_usd), 2)         AS avg_transfer_usd,
        ROUND(MAX(transfer_amount_usd), 2)         AS max_transfer_usd,
        COUNTIF(is_fraud_flag = TRUE)               AS fraud_count,
        ROUND(COUNTIF(is_fraud_flag = TRUE) * 100.0 / NULLIF(COUNT(*), 0), 2) AS fraud_rate_pct,
        -- Transfer size mix
        COUNTIF(transfer_size_tier = 'micro')       AS micro_transfers,
        COUNTIF(transfer_size_tier = 'small')       AS small_transfers,
        COUNTIF(transfer_size_tier = 'medium')      AS medium_transfers,
        COUNTIF(transfer_size_tier = 'large')       AS large_transfers,
        COUNTIF(transfer_size_tier = 'very_large')  AS very_large_transfers,
        -- Corridor risk (high fraud + high volume = risky corridor)
        CASE
            WHEN COUNTIF(is_fraud_flag = TRUE) > 5
              OR ROUND(COUNTIF(is_fraud_flag = TRUE) * 100.0 / NULLIF(COUNT(*), 0), 2) > 10
                THEN 'HIGH_RISK_CORRIDOR'
            WHEN COUNTIF(is_fraud_flag = TRUE) > 0
                THEN 'MONITOR_CORRIDOR'
            ELSE 'SAFE_CORRIDOR'
        END AS corridor_risk,
        CURRENT_TIMESTAMP() AS refreshed_at
    FROM `telecom-project-504210.rebtel_analytics.stg_stream_transfers`
    GROUP BY sender_country, receiver_country, corridor
"""


# ==============================================================================
# EXECUTION ENGINE
# ==============================================================================

def run_model(model_name: str, sql: str, index: int, total: int):
    layer = "STAGING" if "stg_" in model_name else ("FACT" if "fct_" in model_name else "MART")
    print(f"\n[{index}/{total}] [{layer}] Running: {model_name}")
    try:
        job = client.query(sql.strip())
        job.result()
        # Get row count
        table_ref = f"{PROJECT_ID}.{model_name}"
        table = client.get_table(table_ref)
        print(f"  [OK] {model_name} -- {table.num_rows} rows")
        return model_name, table.num_rows, "PASS"
    except Exception as e:
        print(f"  [FAIL] {model_name} -- Error: {e}")
        return model_name, 0, f"FAIL: {e}"


print("=" * 70)
print("STEP 4b: dbt-Style SQL Transformations on BigQuery")
print("  Staging -> Facts -> Analytics Marts")
print("=" * 70)

results = []
total = len(MODELS)
for i, (model_name, sql) in enumerate(MODELS.items(), 1):
    result = run_model(model_name, sql, i, total)
    results.append(result)

# Summary Table
print(f"\n{'='*70}")
print(f"{'Model':<50} {'Rows':>8} {'Status':>8}")
print(f"{'-'*70}")
for name, rows, status in results:
    short_name = name.replace("rebtel_analytics.", "")
    s = "PASS" if "PASS" in status else "FAIL"
    print(f"{short_name:<50} {rows:>8} {s:>8}")
print(f"{'='*70}")

passed = sum(1 for _, _, s in results if "PASS" in s)
failed = total - passed

# Fraud mart verification
print("\n[INFO] Fraud Risk Distribution:")
verify_sql = """
    SELECT fraud_risk_level, COUNT(*) AS user_count
    FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
    GROUP BY fraud_risk_level
    ORDER BY user_count DESC
"""
rows = list(client.query(verify_sql).result())
print(f"  {'Risk Level':<20} {'Users':>8}")
print(f"  {'-'*30}")
for row in rows:
    print(f"  {row.fraud_risk_level:<20} {row.user_count:>8}")

# Customer segment verification
print("\n[INFO] Customer Segments:")
seg_sql = """
    SELECT customer_segment, COUNT(*) AS user_count,
           ROUND(AVG(customer_health_score), 1) AS avg_health_score
    FROM `telecom-project-504210.rebtel_analytics.mart_customer_360`
    GROUP BY customer_segment
    ORDER BY user_count DESC
"""
seg_rows = list(client.query(seg_sql).result())
print(f"  {'Segment':<20} {'Users':>8} {'Avg Health':>12}")
print(f"  {'-'*42}")
for row in seg_rows:
    print(f"  {row.customer_segment:<20} {row.user_count:>8} {row.avg_health_score:>12}")

print(f"\n{'='*70}")
print(f"RESULT: {passed}/{total} models passed, {failed} failed")
if failed == 0:
    print("[DONE] All dbt transformations applied successfully!")
else:
    print("[WARNING] Some models failed -- check errors above")
print(f"{'='*70}")
