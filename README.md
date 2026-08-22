# 📡 Rebtel Telecom & Fintech — Enterprise Intelligence Hub

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![GCP BigQuery](https://img.shields.io/badge/GCP-BigQuery-4285F4.svg)](https://cloud.google.com/bigquery)
[![dbt Core](https://img.shields.io/badge/dbt-Core%20v1.7%2B-FF6B4A.svg)](https://www.getdbt.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E.svg)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An enterprise-grade, end-to-end modern data engineering & business intelligence platform built for telecommunications and remittance fintech operations. 

This repository integrates real-time event streaming, batch ELT ingestion, dbt transformation modeling in **GCP BigQuery**, machine learning fraud detection engines, and an executive dark-themed **Streamlit BI Hub**.

---

## End-to-End System Architecture

```mermaid
flowchart TD
    subgraph Data_Sources ["📥 1. Multi-Source Ingestion"]
        A1[Zendesk SaaS API\nSupport Tickets] -->|Airbyte EL| B1[(BigQuery Staging\nstg_airbyte_zendesk)]
        A2[Batch CSV Exports\nFinancial Payments] -->|GCS Landing| B2[(BigQuery Staging\nstg_batch_payments)]
        A3[Stream Event Generator\nCDR Telecom Calls] -->|Pub/Sub Topic| B3[(BigQuery Staging\nstg_stream_cdrs)]
        A4[Stream Event Generator\nMoney Transfers] -->|Pub/Sub Topic| B4[(BigQuery Staging\nstg_stream_transfers)]
    end

    subgraph Data_Warehouse ["2. GCP BigQuery Warehouse (rebtel_analytics)"]
        B1 & B2 & B3 & B4 --> C1[dbt Transformations\nFact Modeling]
        
        C1 --> F1[(fct_telecom_calls)]
        C1 --> F2[(fct_financial_transfers)]
        C1 --> F3[(fct_payments)]
        C1 --> F4[(fct_support_tickets)]

        F1 & F2 & F3 & F4 --> M1[(mart_fraud_prevention)]
        F1 & F2 & F3 & F4 --> M2[(mart_customer_360)]
        F1 & F2 & F3 & F4 --> M3[(mart_revenue_analytics)]
        F1 & F2 & F3 & F4 --> M4[(mart_network_quality)]
        F1 & F2 & F3 & F4 --> M5[(mart_corridor_analytics)]
    end

    subgraph Machine_Learning [" 3. ML Fraud Engine"]
        M1 -->|Scikit-Learn Random Forest| ML[Fraud Risk Classifier\nFeature Importances & Signals]
    end

    subgraph BI_Presentation [" 4. Streamlit Executive BI Hub"]
        M1 & M2 & M3 & M4 & M5 & ML --> Dash[Streamlit BI Hub\ndashboard_output/app.py]
    end
```

---

## dbt Transformations & Pipeline Architecture

### 1. What dbt Does in This Project
**dbt (Data Build Tool)** acts as the core **Transform (T)** engine in our **ELT (Extract, Load, Transform)** architecture. Instead of processing data outside the data warehouse, dbt leverages GCP BigQuery's cloud compute engine to transform raw, un-nested datasets into clean, aggregated, business-ready data models.

* **Decouples Ingestion from Business Logic:** Raw data lands unchanged into staging datasets (`rebtel_raw_airbyte`, `rebtel_raw_batch`, `rebtel_raw_stream`), allowing dbt to handle all cleaning, business rule application, and analytics modeling idempotently.
* **Automates Multi-Layer Modeling:** Sequentially materializes data across 4 distinct architectural layers: **Staging → Facts → Marts → Analytical Views**.
* **Guarantees Data Quality & Lineage:** Standardizes types, eliminates null values, handles edge cases, and maintains strict dependency graphs (`dbt_lineage.html`).

---

### 2. Types of Transformations Performed by dbt

| Transformation Type | Description & Business Applied Logic |
|---|---|
| **Data Cleaning & Standardization** | Trims whitespace, standardizes string casing with `LOWER(TRIM())`, casts string dates to `TIMESTAMP`, and handles null values using `COALESCE()`. |
| **Categorization & Feature Engineering** | Computes derived metrics such as: <br>• `call_duration_bucket` (`no_connection`, `very_short`, `short`, `medium`, `long`) <br>• MOS `quality_tier` (`excellent`, `good`, `fair`, `poor`) <br>• `transfer_size_tier` (`micro`, `small`, `medium`, `large`, `very_large`) <br>• Zendesk `resolution_hours` calculation. |
| **Multi-Source Fact Aggregation** | Aggregates raw streaming/batch events per user (e.g., total calls, failed calls, failure rates, fraud ticket counts, total transfer volumes). |
| **Multi-Factor Fraud Classification** | Evaluates cross-domain risk vectors (call failure rates + remittance volume + support tickets) to assign a composite `fraud_risk_level`: `CRITICAL_RISK`, `HIGH_RISK_FRAUD`, `MEDIUM_RISK`, `LOW_RISK`, `SAFE`. |
| **Customer Health & Churn Scoring** | Calculates an integrated **Customer Health Score (0–100)** based on quality (25%), satisfaction (25%), reliability (25%), and trust (25%), while categorizing churn risk (`HIGH_CHURN_RISK`, `MODERATE_CHURN_RISK`, `STABLE`). |
| **Unit Economics & Corridor Risk** | Calculates revenue per call/transfer, proxy Customer LTV, and classifies global remittance route risks (`HIGH_RISK_CORRIDOR`, `MONITOR_CORRIDOR`, `SAFE_CORRIDOR`). |

---

### 3. How dbt Performs Execution & Where Data Is Dumped

```
[Raw Sources] ──> [Layer 1: Staging Tables] ──> [Layer 2: Fact Tables] ──> [Layer 3: Analytics Marts] ──> [Layer 4: Reporting Views]
                                                                                      │
                                                                   DUMPED TO GCP BIGQUERY DATASET:
                                                           telecom-project-504210.rebtel_analytics
```

1. **Execution Workflow (`src/dbt_runner.py`):**
   - **Step 1 (Staging):** Reads raw tables from `rebtel_raw_airbyte`, `rebtel_raw_batch`, `rebtel_raw_stream` and creates staging tables in `rebtel_analytics`.
   - **Step 2 (Facts):** Reads staging tables and aggregates user-level metrics into core fact tables.
   - **Step 3 (Marts):** Executes `FULL OUTER JOIN` operations across Telecom, Fintech, SaaS, and Payment facts to generate consolidated business intelligence marts.
   - **Step 4 (Views):** Materializes lightweight reporting views for downstream executive queries.
2. **Target BigQuery Dataset:**
   - **Project ID:** `telecom-project-504210`
   - **Destination Dataset:** `rebtel_analytics`

---

### 4. Comprehensive Table Reference & Purpose

#### 🔹 Layer 1: Staging Tables (`rebtel_analytics.stg_*`)
| Table Name | Source Raw Table | Purpose & Transformation Logic |
|---|---|---|
| `stg_airbyte_zendesk` | `rebtel_raw_airbyte.raw_airbyte_zendesk_tickets` | Standardizes Zendesk SaaS tickets, cleans categories/priorities, and calculates `resolution_hours`. |
| `stg_stream_cdrs` | `rebtel_raw_stream.raw_stream_cdrs` | Cleans CDR telecom streams, handles nulls, and derives `call_duration_bucket` & MOS `quality_tier`. |
| `stg_stream_transfers` | `rebtel_raw_stream.raw_stream_money_transfers` | Cleans remittance events, constructs `corridor` (`US -> MX`), and assigns `transfer_size_tier`. |
| `stg_batch_payments` | `rebtel_raw_batch.raw_batch_payments` | Cleans payment transactions, standardizes plan names, and derives `is_payment_successful` boolean flag. |

#### 🔹 Layer 2: Fact Tables (`rebtel_analytics.fct_*`)
| Table Name | Source Staging Table | Purpose & Transformation Logic |
|---|---|---|
| `fct_telecom_calls` | `stg_stream_cdrs` | Aggregates user-level call metrics: total calls, failed calls, `call_failure_rate_pct`, avg MOS score, and duration metrics. |
| `fct_financial_transfers` | `stg_stream_transfers` | Aggregates user-level transfer metrics: total volume USD, avg transfer size, `fraud_transfers`, and `fraud_rate_pct`. |
| `fct_support_tickets` | `stg_airbyte_zendesk` | Aggregates user-level Zendesk metrics: total tickets, `fraud_tickets`, avg satisfaction score, and ticket statuses. |
| `fct_payments` | `stg_batch_payments` | Aggregates user-level payment metrics: total revenue, successful vs failed payments, and latest subscription plan. |

#### 🔹 Layer 3: Analytics Marts (`rebtel_analytics.mart_*`)
| Table Name | Source Fact Tables | Purpose & Key Business Value |
|---|---|---|
| `mart_fraud_prevention` | `fct_telecom_calls`<br>`fct_financial_transfers`<br>`fct_support_tickets` | **ML Fraud Classification Engine:** Combines call drop spikes, high-value transfers, and fraud support tickets to calculate `total_fraud_signals` and classify users into `CRITICAL_RISK`, `HIGH_RISK_FRAUD`, `MEDIUM_RISK`, `LOW_RISK`, and `SAFE`. |
| `mart_customer_360` | `fct_*`<br>`mart_fraud_prevention` | **Unified Customer Profile:** Computes a 0–100 **Customer Health Score**, assigns customer segments (`VIP`, `HIGH_VALUE`, `ACTIVE`, `REGULAR`, `INACTIVE`), and predicts churn risk (`HIGH_CHURN_RISK`, `MODERATE_CHURN_RISK`, `STABLE`). |
| `mart_revenue_analytics` | `fct_payments`<br>`fct_telecom_calls`<br>`fct_financial_transfers` | **Unit Economics & LTV Analytics:** Calculates `revenue_per_call`, `revenue_per_transfer`, payment failure rates, and estimates Customer Lifetime Value (`estimated_ltv`). |
| `mart_network_quality` | `stg_stream_cdrs` | **Telecom Network SLA Monitor:** Tracks overall connection success rates against 98% target, MOS scores against 4.0 target, and quality distribution across routes. |
| `mart_corridor_analytics` | `stg_stream_transfers` | **Global Remittance Route Intelligence:** Aggregates transfer volume, unique senders, and fraud rates across country corridors, classifying routes into `HIGH_RISK_CORRIDOR`, `MONITOR_CORRIDOR`, and `SAFE_CORRIDOR`. |

#### 🔹 Layer 4: Analytical Reporting Views (`rebtel_analytics.vw_*`)
| View Name | Source Mart Table | Purpose & Downstream Use Case |
|---|---|---|
| `vw_fraud_summary` | `mart_fraud_prevention` | Aggregates risk tier user counts and high-risk fraud exposure for fast dashboard executive summary cards. |
| `vw_customer_health` | `mart_customer_360` | Summarizes average health scores, churn risks, and total revenue per customer segment. |
| `vw_revenue_by_plan` | `mart_revenue_analytics` | Summarizes total revenue, transaction counts, and average spend per subscription plan. |
| `vw_corridor_top20` | `mart_corridor_analytics` | Ranks top 20 global remittance routes by transaction volume for executive corridor monitoring. |

---

## 🌟 Key Features & Analytics Hub

### 1.Fraud Risk Intelligence Center
* **Live BigQuery Querying:** Direct integration with `mart_fraud_prevention`.
* **Risk Tiering:** Real-time classification into `CRITICAL_RISK`, `HIGH_RISK_FRAUD`, `MEDIUM_RISK`, and `LOW_RISK`.
* **Signal Heatmap:** Multi-dimensional matrix mapping call drop rates, remittance transfer spikes, and support ticket fraud signals.
* **High-Risk Priority Ledger:** Interactive, sortable table featuring top flagged accounts with formatted currency (`$`), failure rates (`%`), and CSV export capabilities.

### 2. Network SLA & Quality Monitor
* **MOS Score Tracking:** Measures mean opinion scores across international telecom routes against benchmark targets ($>4.0$).
* **Connection Success Rate:** Real-time monitoring of CDR stream connection rates vs. 98% SLA thresholds.
* **Call Duration Profiling:** Binned analysis categorizing call lengths from drop-outs to long-duration calls.

### 3. Customer 360 & Health Analytics
* **Health Scoring:** Algorithm computing overall user engagement, retention scores, and satisfaction ratings.
* **Churn Risk Matrix:** Proactive classification of accounts vulnerable to churn.
* **Segment Breakdown:** Enterprise metrics broken down by plan tiers (`VIP`, `Premium`, `Standard`, `Basic`).

### 4.  Revenue & Remittance Analytics
* **LTV & Plan Revenue:** Aggregate revenue tracking across payment streams and subscription plans.
* **Global Corridors:** Remittance transfer volume, average transaction sizes, and high-risk corridor profiling across country pairs.

### 5. 🤖 ML Fraud Intelligence
* **Live Scikit-Learn Model Scoring:** Real-time feature importance visualization and model scorecard (Random Forest F1: 100%, AUC-ROC: 1.00).
* **Dynamic Plotly Visuals:** Interactive bubble scatter plots, signal intensity heatmaps, and tier comparison grouped bars.

---

##  Project Directory Structure

```directory
telecom-project/
├── dashboard_output/            # Streamlit BI Presentation App
│   ├── app.py                   # Main Executive Dashboard (Dark Theme Glassmorphic UI)
│   ├── README.md                # Quickstart instructions for BI Hub
│   └── requirements.txt         # Dashboard Python dependencies
│
├── src/                         # Pipeline, ELT, dbt & ML Scripts
│   ├── dashboard.py             # Alternative BI Hub script
│   ├── airbyte_ingest.py        # Airbyte SaaS connector trigger script
│   ├── data_generator.py        # Synthetic CDR, payment & transfer stream generator
│   ├── pubsub_publisher.py      # GCP Pub/Sub event publisher
│   ├── pubsub_to_gcs.py         # Pub/Sub subscriber to GCS landing
│   ├── gcs_landing_upload.py    # GCS file uploader utility
│   ├── gcs_to_bigquery_load.py  # BigQuery raw staging loader
│   ├── dbt_runner.py            # dbt transformation execution script
│   ├── ml_fraud_detection.py    # Random Forest fraud model trainer
│   ├── looker_dashboard_creator.py # Looker Studio API integration
│   └── setup_adc.py             # GCP authentication diagnostic script
│
├── data/                        # Local Data Files
│   ├── batch/                   # Batch CSV payment logs
│   ├── saas/                    # Zendesk support ticket JSONs
│   └── stream/                  # Live CDR and money transfer JSON streams
│
├── ml_outputs/                  # Machine Learning Models & Artifacts
│   ├── fraud_detection_model.pkl# Trained Random Forest Model
│   └── fraud_scaler.pkl         # Feature Scaler
│
├── dbt_lineage.html             # Interactive dbt Data Lineage Graph
├── dashboard_spec.json          # BI specification definition
└── README.md                    # Project Documentation (This File)
```

---

## Technology Stack

| Layer | Technology | Usage |
|---|---|---|
| **Data Warehouse** | **GCP BigQuery** | Enterprise Data Warehouse (`telecom-project-504210.rebtel_analytics`) |
| **Cloud Infrastructure** | **Google Cloud Platform** | GCS, Pub/Sub, Cloud SDK, IAM ADC Authentication |
| **Ingestion / ELT** | **Airbyte & Python** | SaaS (Zendesk), Batch CSV & Pub/Sub Event Streaming |
| **Data Transformation** | **dbt (Data Build Tool)** | Staging, Fact, Mart SQL modeling & data lineage |
| **Machine Learning** | **Scikit-Learn & Pandas** | Random Forest Classifier, Feature Engineering |
| **User Interface / BI** | **Streamlit & Plotly** | Executive BI Dashboard, Dark Glassmorphism Design |

---

## Quickstart Guide

### 1. Prerequisites
Ensure you have the following installed on your machine:
* **Python 3.10+**
* **Google Cloud SDK (`gcloud` CLI)**
* Access to GCP Project: `telecom-project-504210`

### 2. Environment Setup

Clone the repository and install the dependencies:

```bash
# Clone the repository
git clone https://github.com/arhamsheikh17/telecom-project.git
cd telecom-project

# Install required dependencies
pip install -r dashboard_output/requirements.txt
```

### 3. Google Cloud Authentication

Authenticate your GCP user account and set up Application Default Credentials (ADC) for BigQuery querying:

```powershell
# Authenticate gcloud user
gcloud auth login

# Set up Application Default Credentials (ADC) for BigQuery Client
gcloud auth application-default login
```

### 4. Running the Dashboard

To start the Streamlit BI Hub locally:

```powershell
python -m streamlit run dashboard_output/app.py
```

Open your browser and navigate to `http://localhost:8501`.


---

### Created & Maintained By
**Arham Sheikh** — Data Engineer
GitHub: [@arhamsheikh17](https://github.com/arhamsheikh17)
