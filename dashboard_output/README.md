# Rebtel Telecom — Streamlit Dashboard

## Quick Start

```bash
cd d:\bootcamp\projects\telecom-project\dashboard_output
streamlit run app.py
```

Or from the project root:
```bash
streamlit run dashboard_output/app.py
```

## What's Included

| Tab | Data Source | Description |
|-----|-------------|-------------|
| 🚨 Fraud Intelligence | BigQuery `mart_fraud_prevention` | Risk tiers, scatter profiles, priority ledger |
| 📶 Network & SLA | BigQuery `mart_network_quality` + Local CDR JSON | MOS quality, duration, connection rates |
| 👥 Customer 360 | BigQuery `mart_customer_360` + Zendesk JSON | Segments, churn, health scores |
| 💰 Revenue & Payments | BigQuery `mart_revenue_analytics` + Local CSV | Plan revenue, payment status, LTV |
| 🌍 Remittance Corridors | BigQuery `mart_corridor_analytics` + Local Transfers | Corridor risk, volume, country analysis |
| 🤖 ML Model Insights | `ml_outputs/*.pkl` + `ml_outputs/*.png` | Feature importance, radar, live predictor |
| 📋 Data Explorer | All 9 sources | Unified search + CSV export |

## Data Sources

### BigQuery Marts (dbt-transformed)
- `rebtel_analytics.mart_fraud_prevention`
- `rebtel_analytics.mart_customer_360`
- `rebtel_analytics.mart_revenue_analytics`
- `rebtel_analytics.mart_network_quality`
- `rebtel_analytics.mart_corridor_analytics`

### Local Files (always available)
- `data/batch/financial_payments.csv` — 1,500 payment records
- `data/stream/call_data_records.json` — CDR streaming events
- `data/stream/money_transfers.json` — Money transfer events
- `data/saas/zendesk_tickets.json` — Support ticket data

### ML Outputs
- `ml_outputs/fraud_detection_model.pkl` — Random Forest model
- `ml_outputs/fraud_scaler.pkl` — Feature scaler
- `ml_outputs/fraud_detection_dashboard.png` — Model comparison chart
- `ml_outputs/fraud_risk_distribution.png` — Risk pie chart
