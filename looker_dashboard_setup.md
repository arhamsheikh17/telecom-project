# Looker Studio Dashboard Setup Guide
## Rebtel Telecom — BigQuery Analytics Dashboard

> **Tool:** Looker Studio (Free) — [https://lookerstudio.google.com](https://lookerstudio.google.com)
> **Data Source:** BigQuery Project `telecom-project-504210` → Dataset `rebtel_analytics`

---

## Step 1: Connect BigQuery to Looker Studio

1. Go to [https://lookerstudio.google.com](https://lookerstudio.google.com)
2. Click **"Create" → "Report"**
3. Under "Connect to data", choose **BigQuery**
4. Select:
   - **Project:** `telecom-project-504210`
   - **Dataset:** `rebtel_analytics`
   - **Table:** `mart_customer_360` *(primary table)*
5. Click **"Add"** → **"Add to Report"**

---

## Step 2: Add All 5 Data Sources

Add each mart table as a separate data source:

| # | Table Name | Purpose |
|---|---|---|
| 1 | `mart_customer_360` | Customer segments, health scores, churn risk |
| 2 | `mart_fraud_prevention` | Fraud risk classification per user |
| 3 | `mart_revenue_analytics` | Revenue, LTV, unit economics |
| 4 | `mart_network_quality` | Network SLA & call quality KPIs |
| 5 | `mart_corridor_analytics` | Remittance corridor intelligence |

---

## Step 3: Charts to Create (with exact settings)

---

### 📊 Chart 1: Fraud Risk Distribution (Pie Chart)
**Data Source:** `mart_fraud_prevention`

| Setting | Value |
|---|---|
| Chart Type | Pie Chart |
| Dimension | `fraud_risk_level` |
| Metric | `COUNT(user_id)` |
| Filter | None |
| Title | "Fraud Risk Distribution" |
| Colors | Red=CRITICAL, Orange=HIGH_RISK, Yellow=MEDIUM, Blue=LOW, Green=SAFE |

**SQL for Custom Chart:**
```sql
SELECT fraud_risk_level, COUNT(user_id) AS user_count
FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
GROUP BY fraud_risk_level
ORDER BY user_count DESC
```

---

### 📊 Chart 2: Customer Segments Bar Chart
**Data Source:** `mart_customer_360`

| Setting | Value |
|---|---|
| Chart Type | Bar Chart (Vertical) |
| Dimension | `customer_segment` |
| Metric | `COUNT(user_id)` |
| Secondary Metric | `AVG(customer_health_score)` |
| Title | "Customer Segments" |

**SQL:**
```sql
SELECT customer_segment, COUNT(user_id) AS users,
       ROUND(AVG(customer_health_score), 1) AS avg_health_score
FROM `telecom-project-504210.rebtel_analytics.mart_customer_360`
GROUP BY customer_segment
ORDER BY users DESC
```

---

### 📊 Chart 3: Customer Health Score Distribution (Histogram)
**Data Source:** `mart_customer_360`

| Setting | Value |
|---|---|
| Chart Type | Histogram / Column Chart |
| Dimension | `customer_segment` |
| Metric | `AVG(customer_health_score)` |
| Breakdown | `churn_risk` |
| Title | "Customer Health Score by Segment" |

---

### 📊 Chart 4: Revenue by Subscription Plan (Bar Chart)
**Data Source:** `mart_revenue_analytics`

| Setting | Value |
|---|---|
| Chart Type | Bar Chart |
| Dimension | `latest_subscription_plan` |
| Metric | `SUM(total_revenue)` |
| Secondary Metric | `AVG(estimated_ltv)` |
| Title | "Revenue by Subscription Plan" |

**SQL:**
```sql
SELECT p.latest_subscription_plan,
       COUNT(r.user_id) AS users,
       ROUND(SUM(r.total_revenue), 2) AS total_revenue,
       ROUND(AVG(r.estimated_ltv), 2) AS avg_ltv
FROM `telecom-project-504210.rebtel_analytics.mart_revenue_analytics` r
JOIN `telecom-project-504210.rebtel_analytics.fct_payments` p ON r.user_id = p.user_id
GROUP BY p.latest_subscription_plan
ORDER BY total_revenue DESC
```

---

### 📊 Chart 5: Top Remittance Corridors (Table + Heatmap)
**Data Source:** `mart_corridor_analytics`

| Setting | Value |
|---|---|
| Chart Type | Table |
| Dimensions | `corridor`, `corridor_risk` |
| Metrics | `total_transfers`, `total_volume_usd`, `fraud_rate_pct` |
| Sort | `total_volume_usd DESC` |
| Title | "Top Money Transfer Corridors" |
| Heatmap | Enable on `fraud_rate_pct` (Red = high risk) |

**SQL:**
```sql
SELECT corridor, corridor_risk, total_transfers,
       total_volume_usd, fraud_rate_pct
FROM `telecom-project-504210.rebtel_analytics.mart_corridor_analytics`
ORDER BY total_volume_usd DESC
LIMIT 20
```

---

### 📊 Chart 6: Network SLA Scorecards (KPI Cards)
**Data Source:** `mart_network_quality`

Create 4 separate **Scorecard** charts:

| Scorecard | Metric | Target |
|---|---|---|
| Connection Success Rate | `connection_success_rate_pct` | Target: 98% |
| Avg MOS Score | `avg_mos_score` | Target: 4.0 |
| SLA Quality Met | `sla_quality_met_pct` | Target: 95% |
| Avg Delivery Rate | `avg_delivery_rate_pct` | Target: 95% |

**SQL:**
```sql
SELECT total_calls, connection_success_rate_pct,
       avg_mos_score, avg_delivery_rate_pct,
       sla_quality_met_pct, sla_connection_met_pct
FROM `telecom-project-504210.rebtel_analytics.mart_network_quality`
```

---

### 📊 Chart 7: Churn Risk Breakdown (Donut Chart)
**Data Source:** `mart_customer_360`

| Setting | Value |
|---|---|
| Chart Type | Donut Chart |
| Dimension | `churn_risk` |
| Metric | `COUNT(user_id)` |
| Title | "Churn Risk Distribution" |

---

## Step 4: Dashboard Layout (Suggested)

```
┌─────────────────────────────────────────────────────────────────┐
│  REBTEL TELECOM — Business Intelligence Dashboard               │
├──────────────┬──────────────┬──────────────┬──────────────────  │
│  Scorecard:  │  Scorecard:  │  Scorecard:  │  Scorecard:        │
│  Connection  │  MOS Score   │  SLA Quality │  Delivery Rate     │
│  89.84%      │  2.54        │  36.71%      │  68.31%            │
├──────────────────────────┬──────────────────────────────────────┤
│  Fraud Risk Pie Chart    │  Customer Segments Bar Chart         │
│  (mart_fraud_prevention) │  (mart_customer_360)                 │
├──────────────────────────┼──────────────────────────────────────┤
│  Revenue by Plan         │  Churn Risk Donut                    │
│  (mart_revenue_analytics)│  (mart_customer_360)                 │
├──────────────────────────────────────────────────────────────────┤
│  Top Corridors Table (mart_corridor_analytics)                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Step 5: Filters to Add

Add these **filter controls** at the top of the dashboard:

| Filter | Data Source | Field |
|---|---|---|
| Customer Segment | `mart_customer_360` | `customer_segment` |
| Fraud Risk Level | `mart_fraud_prevention` | `fraud_risk_level` |
| Churn Risk | `mart_customer_360` | `churn_risk` |
| Corridor Risk | `mart_corridor_analytics` | `corridor_risk` |

---

## Quick Verification Queries for Dashboard Data

Run these in BigQuery to verify data before building charts:

```sql
-- Verify all mart tables have data
SELECT 'mart_fraud_prevention' AS tbl, COUNT(*) AS rows FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
UNION ALL
SELECT 'mart_customer_360', COUNT(*) FROM `telecom-project-504210.rebtel_analytics.mart_customer_360`
UNION ALL
SELECT 'mart_revenue_analytics', COUNT(*) FROM `telecom-project-504210.rebtel_analytics.mart_revenue_analytics`
UNION ALL
SELECT 'mart_network_quality', COUNT(*) FROM `telecom-project-504210.rebtel_analytics.mart_network_quality`
UNION ALL
SELECT 'mart_corridor_analytics', COUNT(*) FROM `telecom-project-504210.rebtel_analytics.mart_corridor_analytics`;
```
