# Rebtel Telecom & Fintech — Complete Enterprise Data Architecture Implementation

**GCP Project:** `telecom-project-504210`
**GCP Service Account Key:** `gcp_key.json` (already configured in project root)

> [!IMPORTANT]
> This document is a **sequential, step-by-step execution guide**. Each step MUST be verified before moving to the next. Do NOT skip verification gates.

---

## Architecture Overview

```
[ Zendesk SaaS API ] ──► [ Airbyte Open-Source EL ] ──────────────────────────────────────────────┐
                                                                                                   │
[ Static Data (Payments CSV) ] ──► [ Python Generator ] ──► [ GCS Bucket: /batch/ ] ──┐            │
                                                                                       ├──► [ GCP BIGQUERY ] ──► [ dbt Cloud ] ──► [ Looker / Dashboard ]
[ Stream Data (CDRs, Transfers) ] ──► [ GCP Pub/Sub ] ──► [ GCS Bucket: /stream/ ] ──┘            │
                                                                                                   │
                                                                            (All data unified here) ┘
```

---

# ═══════════════════════════════════════════════════════════════
# STEP 1: FETCH ZENDESK DATA VIA AIRBYTE INTO GCP BIGQUERY
# ═══════════════════════════════════════════════════════════════

## 1.1 Objective
Extract customer support ticket data from the **Zendesk Support REST API** using **Airbyte Open-Source EL Connector** and load it directly into **GCP BigQuery** dataset `rebtel_raw_airbyte`.

## 1.2 Airbyte Setup & Configuration

### Option A: Airbyte Cloud (Fastest — No Docker Required)
1. Go to [https://cloud.airbyte.com](https://cloud.airbyte.com) and sign up / log in.
2. **Create Source:**
   - Click **Sources** → **New Source** → Search **"Zendesk Support"**.
   - Fill in:
     - **Subdomain:** Your Zendesk subdomain (e.g., `rebtel` if your URL is `rebtel.zendesk.com`).
     - **Authentication:** Select **API Token** → Enter your Zendesk email + API token.
     - **Start Date:** Set to `2024-01-01T00:00:00Z` (or your preferred historical start).
   - Click **Set up Source** → Wait for connection test to pass.
3. **Create Destination:**
   - Click **Destinations** → **New Destination** → Search **"BigQuery"**.
   - Fill in:
     - **Project ID:** `telecom-project-504210`
     - **Dataset ID:** `rebtel_raw_airbyte`
     - **Dataset Location:** `US`
     - **Loading Method:** Select **Standard Inserts** (for small datasets) or **GCS Staging** (for large datasets).
     - **Service Account Key JSON:** Paste the contents of your `gcp_key.json` file.
   - Click **Set up Destination** → Wait for connection test to pass.
4. **Create Connection:**
   - Click **Connections** → **New Connection**.
   - Select your Zendesk Source and BigQuery Destination.
   - **Select Streams to Sync:** Enable at minimum:
     - `tickets` ✅
     - `users` ✅ (optional but recommended)
     - `satisfaction_ratings` ✅ (optional but recommended)
   - **Sync Frequency:** Set to **Manual** for now.
   - Click **Set up Connection**.
5. **Trigger First Sync:**
   - Click **Sync Now** on the connection page.
   - Wait for the sync status to show **Succeeded**.

### Option B: Airbyte OSS on Docker (Self-Hosted — Free)
Run these commands in terminal:
```bash
git clone --depth 1 https://github.com/airbytehq/airbyte.git
cd airbyte
docker compose up -d
```
Then open `http://localhost:8000` in browser and follow the same Source/Destination/Connection setup as Option A above.

### Option C: Direct Python Script Simulation (If Airbyte/Zendesk Not Available)
If you do not have a live Zendesk account or Airbyte setup, run the simulation script:
```bash
cd C:\Users\HP\.gemini\antigravity\scratch\rebtel_data_stack
python src/airbyte_ingest.py
```
This script simulates the exact Airbyte behavior:
- Reads Zendesk JSON payload from `data/saas/zendesk_tickets.json`.
- Appends Airbyte system audit metadata columns (`_airbyte_ab_id`, `_airbyte_emitted_at`, `_airbyte_normalized_at`).
- Loads directly into BigQuery table `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`.

## 1.3 Expected Zendesk Schema in BigQuery (After Airbyte Sync)

After Airbyte syncs, the following table will be created in BigQuery:

**Table:** `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`

| Column Name | Data Type | Source | Description |
| :--- | :--- | :--- | :--- |
| `ticket_id` | STRING | Zendesk API | Primary Key — Unique ticket identifier |
| `user_id` | STRING | Zendesk API | The requester/user who opened the ticket |
| `created_at` | TIMESTAMP | Zendesk API | Ticket creation time |
| `updated_at` | TIMESTAMP | Zendesk API | Last update timestamp |
| `issue_category` | STRING | Zendesk API | `payment_failure`, `call_drop`, `fraud_alert`, `topup_delay` |
| `priority` | STRING | Zendesk API | `low`, `medium`, `high`, `urgent` |
| `ticket_status` | STRING | Zendesk API | `open`, `pending`, `solved`, `closed` |
| `satisfaction_score` | INTEGER | Zendesk API | Customer CSAT rating (1 to 5) |
| `_airbyte_ab_id` | STRING | Airbyte System | Airbyte-generated unique record UUID |
| `_airbyte_emitted_at` | TIMESTAMP | Airbyte System | Timestamp when Airbyte extracted the record |
| `_airbyte_normalized_at` | TIMESTAMP | Airbyte System | Timestamp when Airbyte normalized the schema |

## 1.4 ✅ VERIFICATION GATE — STEP 1

**Do NOT proceed to Step 2 until ALL of the following checks pass:**

Run these verification queries in **GCP BigQuery SQL Editor:**

### Check 1: Confirm table exists and has rows
```sql
SELECT COUNT(*) AS total_zendesk_tickets
FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`;
```
**Expected:** Row count > 0.

### Check 2: Confirm Airbyte audit metadata columns exist and are populated
```sql
SELECT 
    ticket_id,
    user_id,
    issue_category,
    _airbyte_ab_id,
    _airbyte_emitted_at
FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`
LIMIT 5;
```
**Expected:** `_airbyte_ab_id` should contain UUID strings. `_airbyte_emitted_at` should contain valid timestamps.

### Check 3: List all distinct user_ids from Zendesk data
```sql
SELECT DISTINCT user_id
FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`
ORDER BY user_id;
```
**Expected:** A list of unique user IDs. **SAVE THIS LIST — You will need it in Step 2 for generating matching synthetic data.**

### Check 4: List all distinct columns and data types
```sql
SELECT column_name, data_type
FROM `telecom-project-504210.rebtel_raw_airbyte.INFORMATION_SCHEMA.COLUMNS`
WHERE table_name = 'raw_airbyte_zendesk_tickets';
```
**Expected:** All columns from the schema table above should appear.

**Print a summary table confirming:**
- Table Name
- Total Row Count
- Airbyte Audit Timestamp Sample
- Number of Distinct user_ids
- Status: PASS / FAIL

> [!CAUTION]
> STOP HERE. Do not proceed to Step 2 until Step 1 verification is complete and all checks PASS.

---

# ═══════════════════════════════════════════════════════════════
# STEP 2: ANALYZE ZENDESK DATA & GENERATE MATCHING SYNTHETIC DATASETS
# ═══════════════════════════════════════════════════════════════

## 2.1 Objective
Analyze the Zendesk data that arrived via Airbyte in Step 1. Extract the **exact `user_id` values** from that data. Then write Python scripts to generate synthetic **Call Data Records (CDRs)** and **Financial Payment Data** and **Money Transfer Data** using those **same `user_id` values** — so that all datasets can be joined together in BigQuery later via the shared `user_id` column.

## 2.2 Analyze Zendesk Data (Extract User IDs for Referential Integrity)

Run this BigQuery query to extract all unique user IDs from Zendesk:
```sql
SELECT DISTINCT user_id
FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`
ORDER BY user_id;
```

**Action:** Export this result as CSV or copy the user_id list. This list will be the **master seed** for all synthetic data generators to ensure referential integrity across all datasets.

## 2.3 Analyze Zendesk Column Patterns

Run this query to understand the data distribution:
```sql
SELECT 
    COUNT(*) AS total_tickets,
    COUNT(DISTINCT user_id) AS unique_users,
    COUNT(DISTINCT issue_category) AS unique_categories,
    COUNT(DISTINCT priority) AS unique_priorities,
    MIN(created_at) AS earliest_ticket,
    MAX(created_at) AS latest_ticket
FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`;
```

## 2.4 Generate Synthetic Static & Stream Data (Python Script)

Create and run `src/data_generator.py` that:

1. **Reads the exact `user_id` list** from BigQuery Zendesk table (or from the exported CSV).
2. **Generates Call Data Records (CDRs)** — Stream Data:
   - Uses those exact `user_id` values.
   - Columns: `call_id`, `user_id`, `duration_seconds`, `connection_success`, `call_quality_score`, `delivery_rate_percent`, `timestamp`.
   - Output: `data/stream/call_data_records.json` (2500 records).

3. **Generates Money Transfer Data** — Stream Data:
   - Uses those exact `user_id` values.
   - Columns: `transfer_id`, `user_id`, `sender_country`, `receiver_country`, `transfer_amount_usd`, `is_fraud_flag`.
   - Output: `data/stream/money_transfers.json` (1500 records).

4. **Generates Financial Payment Data** — Batch/Static Data:
   - Uses those exact `user_id` values.
   - Columns: `transaction_id`, `user_id`, `subscription_plan`, `payment_amount`, `payment_status`.
   - Output: `data/batch/financial_payments.csv` (1500 records).

**Command to execute:**
```bash
cd C:\Users\HP\.gemini\antigravity\scratch\rebtel_data_stack
python src/data_generator.py
```

## 2.5 ✅ VERIFICATION GATE — STEP 2

**Do NOT proceed to Step 3 until ALL of the following checks pass:**

### Check 1: Verify generated files exist and have correct row counts
```bash
# PowerShell commands to verify file contents
(Get-Content data\stream\call_data_records.json | ConvertFrom-Json).Count
(Get-Content data\stream\money_transfers.json | ConvertFrom-Json).Count
(Import-Csv data\batch\financial_payments.csv).Count
```
**Expected:** CDRs ≈ 2500, Money Transfers ≈ 1500, Payments ≈ 1500.

### Check 2: Verify user_id referential integrity (CRITICAL!)
```bash
# Run a Python check that confirms ALL user_ids in generated files exist in Zendesk user_id list
python -c "
import json
zendesk = json.load(open('data/saas/zendesk_tickets.json'))
cdrs = json.load(open('data/stream/call_data_records.json'))
zendesk_ids = set(t['user_id'] for t in zendesk)
cdr_ids = set(c['user_id'] for c in cdrs)
orphan_ids = cdr_ids - zendesk_ids
print(f'Zendesk user_ids: {len(zendesk_ids)}')
print(f'CDR user_ids: {len(cdr_ids)}')
print(f'Orphan IDs (not in Zendesk): {len(orphan_ids)}')
print('PASS' if len(orphan_ids) == 0 else 'FAIL — IDs do not match!')
"
```
**Expected:** `Orphan IDs: 0` and status `PASS`.

### Check 3: Verify column names match Scrum specifications
```bash
python -c "
import json, csv
cdrs = json.load(open('data/stream/call_data_records.json'))
print('CDR Columns:', list(cdrs[0].keys()))
transfers = json.load(open('data/stream/money_transfers.json'))
print('Transfer Columns:', list(transfers[0].keys()))
with open('data/batch/financial_payments.csv') as f:
    reader = csv.DictReader(f)
    print('Payment Columns:', reader.fieldnames)
"
```
**Expected columns:**
- CDRs: `call_id, user_id, duration_seconds, connection_success, call_quality_score, delivery_rate_percent, timestamp`
- Transfers: `transfer_id, user_id, sender_country, receiver_country, transfer_amount_usd, is_fraud_flag`
- Payments: `transaction_id, user_id, subscription_plan, payment_amount, payment_status`

**Print a summary table confirming:**
- File Name
- Row Count
- Column Names
- User ID Match Status (vs Zendesk)
- Status: PASS / FAIL

> [!CAUTION]
> STOP HERE. Do not proceed to Step 3 until Step 2 verification is complete and all checks PASS.

---

# ═══════════════════════════════════════════════════════════════
# STEP 3: STREAM DATA VIA GCP PUB/SUB + DUMP ALL FILES TO GCS
# ═══════════════════════════════════════════════════════════════

## 3.1 Objective
- Create a **GCP Pub/Sub Topic** for streaming CDR and Money Transfer events.
- Publish stream data records to Pub/Sub, then subscribe and dump them into **GCS Bucket** (`gs://rebtel-telecom-raw-landing-504210/stream/`).
- Upload static/batch payment data directly to **GCS Bucket** (`gs://rebtel-telecom-raw-landing-504210/batch/`).
- Result: Both stream AND static raw data land in GCS as the **Data Lake Landing Zone**.

## 3.2 GCS Bucket Creation

Create the GCS Landing Zone bucket (if not already exists):
```bash
gcloud storage buckets create gs://rebtel-telecom-raw-landing-504210 --project=telecom-project-504210 --location=US
```

## 3.3 GCP Pub/Sub Topic & Subscription Setup

Create Pub/Sub topic and subscription for streaming events:
```bash
# Create Pub/Sub Topic for CDR events
gcloud pubsub topics create rebtel-cdr-stream --project=telecom-project-504210

# Create Pub/Sub Topic for Money Transfer events
gcloud pubsub topics create rebtel-transfer-stream --project=telecom-project-504210

# Create Pull Subscriptions
gcloud pubsub subscriptions create rebtel-cdr-sub --topic=rebtel-cdr-stream --project=telecom-project-504210
gcloud pubsub subscriptions create rebtel-transfer-sub --topic=rebtel-transfer-stream --project=telecom-project-504210
```

## 3.4 Stream Publisher Script (`src/pubsub_publisher.py`)

Create a Python script that:
1. Reads `data/stream/call_data_records.json` and publishes each record as a message to Pub/Sub topic `rebtel-cdr-stream`.
2. Reads `data/stream/money_transfers.json` and publishes each record as a message to Pub/Sub topic `rebtel-transfer-stream`.
3. Simulates real-time streaming by adding small delays between publishes (e.g., 10-50ms).

**Required library:**
```bash
pip install google-cloud-pubsub
```

**Script behavior:**
```python
# Pseudocode
from google.cloud import pubsub_v1
import json, time

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("telecom-project-504210", "rebtel-cdr-stream")

for record in cdr_records:
    data = json.dumps(record).encode("utf-8")
    future = publisher.publish(topic_path, data)
    future.result()  # Wait for publish confirmation
    time.sleep(0.02)  # 20ms delay to simulate real-time stream
```

## 3.5 Stream Subscriber + GCS Dump Script (`src/pubsub_to_gcs.py`)

Create a Python script that:
1. Subscribes to Pub/Sub subscriptions `rebtel-cdr-sub` and `rebtel-transfer-sub`.
2. Collects messages into micro-batches (e.g., 100 messages per batch).
3. Writes each micro-batch as a JSON file to GCS:
   - CDRs → `gs://rebtel-telecom-raw-landing-504210/stream/cdrs/batch_001.json`
   - Transfers → `gs://rebtel-telecom-raw-landing-504210/stream/transfers/batch_001.json`

**Required library:**
```bash
pip install google-cloud-storage
```

## 3.6 Static/Batch Data Upload to GCS (`src/gcs_landing_upload.py`)

Upload the static payment CSV file directly to GCS:
```python
# Upload financial_payments.csv to GCS batch landing zone
blob = bucket.blob("batch/payments/financial_payments.csv")
blob.upload_from_filename("data/batch/financial_payments.csv")
```

**Destination:** `gs://rebtel-telecom-raw-landing-504210/batch/payments/financial_payments.csv`

## 3.7 Execution Order
```bash
cd C:\Users\HP\.gemini\antigravity\scratch\rebtel_data_stack

# 3.7.1: Upload static batch data to GCS
python src/gcs_landing_upload.py

# 3.7.2: Start the Pub/Sub subscriber (GCS writer) in background
python src/pubsub_to_gcs.py &

# 3.7.3: Publish stream data to Pub/Sub topics
python src/pubsub_publisher.py
```

## 3.8 ✅ VERIFICATION GATE — STEP 3

**Do NOT proceed to Step 4 until ALL of the following checks pass:**

### Check 1: Verify GCS bucket has all landing files
```bash
gcloud storage ls gs://rebtel-telecom-raw-landing-504210/stream/cdrs/
gcloud storage ls gs://rebtel-telecom-raw-landing-504210/stream/transfers/
gcloud storage ls gs://rebtel-telecom-raw-landing-504210/batch/payments/
```
**Expected:** Files listed under each path.

### Check 2: Verify Pub/Sub topics exist
```bash
gcloud pubsub topics list --project=telecom-project-504210
```
**Expected:** `rebtel-cdr-stream` and `rebtel-transfer-stream` topics listed.

### Check 3: Verify file content in GCS
```bash
# Download and check a sample stream file
gcloud storage cat gs://rebtel-telecom-raw-landing-504210/stream/cdrs/batch_001.json | head -5
gcloud storage cat gs://rebtel-telecom-raw-landing-504210/batch/payments/financial_payments.csv | head -5
```
**Expected:** Valid JSON records (CDRs) and CSV header + rows (Payments).

### Check 4: Verify row counts in GCS files
```bash
python -c "
from google.cloud import storage
client = storage.Client(project='telecom-project-504210')
bucket = client.bucket('rebtel-telecom-raw-landing-504210')
blobs = list(bucket.list_blobs())
for b in blobs:
    print(f'{b.name} — {b.size} bytes')
"
```

**Print a summary table confirming:**
- GCS Path
- File Name
- File Size (bytes)
- Data Type (Stream / Batch)
- Status: PASS / FAIL

> [!CAUTION]
> STOP HERE. Do not proceed to Step 4 until Step 3 verification is complete and all checks PASS.

---

# ═══════════════════════════════════════════════════════════════
# STEP 4: LOAD GCS DATA INTO BIGQUERY + dbt TRANSFORMATIONS
# ═══════════════════════════════════════════════════════════════

## 4.1 Objective
- Import stream and static data from **GCS Landing Bucket** into **GCP BigQuery** raw datasets.
- At this point, **ALL data sources are unified in BigQuery:**
  - `rebtel_raw_airbyte` → Zendesk SaaS tickets (from Step 1)
  - `rebtel_raw_stream` → CDRs + Money Transfers (from GCS, Step 3)
  - `rebtel_raw_batch` → Financial Payments (from GCS, Step 3)
- Run **dbt Cloud SQL transformations** on BigQuery to build clean staging models, dimensional marts, and the ML Fraud Prevention mart.

## 4.2 Create BigQuery Datasets (if not exists)
```bash
bq mk --dataset --location=US telecom-project-504210:rebtel_raw_stream
bq mk --dataset --location=US telecom-project-504210:rebtel_raw_batch
bq mk --dataset --location=US telecom-project-504210:rebtel_analytics
```

## 4.3 Load GCS Files into BigQuery (`src/gcs_to_bigquery_load.py`)

Execute BigQuery LoadJobs using GCS URI paths:

```bash
cd C:\Users\HP\.gemini\antigravity\scratch\rebtel_data_stack
python src/gcs_to_bigquery_load.py
```

**What this script does:**
- Loads `gs://rebtel-telecom-raw-landing-504210/stream/cdrs/*.json` → `rebtel_raw_stream.raw_stream_cdrs`
- Loads `gs://rebtel-telecom-raw-landing-504210/stream/transfers/*.json` → `rebtel_raw_stream.raw_stream_money_transfers`
- Loads `gs://rebtel-telecom-raw-landing-504210/batch/payments/*.csv` → `rebtel_raw_batch.raw_batch_payments`

## 4.4 dbt Cloud Transformations (`src/dbt_runner.py`)

Execute dbt SQL models on unified BigQuery warehouse:
```bash
python src/dbt_runner.py
```

**dbt Models to Build:**

### Staging Layer (Clean & Standardize)
- `stg_airbyte_zendesk` → Cleans raw Zendesk tickets (lowercase categories, cast timestamps)
- `stg_stream_cdrs` → Cleans raw CDR stream data
- `stg_stream_transfers` → Cleans raw money transfer data
- `stg_batch_payments` → Cleans raw payment ledger data

### Core Analytics Marts
- `fct_telecom_calls` → Call volume, success rates, quality metrics per user
- `fct_financial_transfers` → Money transfer volumes, fraud flags per user
- `fct_support_tickets` → Support ticket counts, categories per user

### ML Fraud Prevention Mart (Advanced Use Case from Rebtel Case Study)
- `mart_fraud_prevention` → Joins ALL datasets on `user_id`:
  - High call failure rate (from CDRs) + High transfer amounts (from Transfers) + Fraud tickets (from Zendesk) = `HIGH_RISK_FRAUD`
  - Medium indicators = `MEDIUM_RISK`
  - Normal behavior = `LOW_RISK`

**dbt SQL for `mart_fraud_prevention`:**
```sql
CREATE OR REPLACE TABLE `rebtel_analytics.mart_fraud_prevention` AS
WITH cdrs AS (
    SELECT user_id,
           COUNT(*) AS total_calls,
           COUNTIF(connection_success = FALSE) AS failed_calls,
           ROUND(COUNTIF(connection_success = FALSE) * 100.0 / NULLIF(COUNT(*), 0), 2) AS call_failure_rate_pct
    FROM `rebtel_raw_stream.raw_stream_cdrs`
    GROUP BY user_id
),
transfers AS (
    SELECT user_id,
           COUNT(*) AS total_transfers,
           SUM(transfer_amount_usd) AS total_transfer_usd,
           COUNTIF(is_fraud_flag = TRUE) AS fraud_transfers
    FROM `rebtel_raw_stream.raw_stream_money_transfers`
    GROUP BY user_id
),
tickets AS (
    SELECT user_id,
           COUNT(*) AS support_tickets,
           COUNTIF(issue_category = 'fraud_alert') AS fraud_tickets
    FROM `rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`
    GROUP BY user_id
)
SELECT
    COALESCE(c.user_id, t.user_id, k.user_id) AS user_id,
    c.total_calls, c.failed_calls, c.call_failure_rate_pct,
    t.total_transfers, t.total_transfer_usd, t.fraud_transfers,
    k.support_tickets, k.fraud_tickets,
    CASE
        WHEN t.fraud_transfers > 0 OR k.fraud_tickets > 0 THEN 'HIGH_RISK_FRAUD'
        WHEN c.call_failure_rate_pct > 30.0 OR t.total_transfer_usd > 900 THEN 'MEDIUM_RISK'
        ELSE 'LOW_RISK'
    END AS fraud_risk_level
FROM cdrs c
FULL OUTER JOIN transfers t ON c.user_id = t.user_id
FULL OUTER JOIN tickets k ON COALESCE(c.user_id, t.user_id) = k.user_id;
```

## 4.5 ✅ VERIFICATION GATE — STEP 4

**Do NOT proceed to Step 5 until ALL of the following checks pass:**

### Check 1: Verify all raw tables in BigQuery
```sql
SELECT 'raw_stream_cdrs' AS tbl, COUNT(*) AS rows FROM `telecom-project-504210.rebtel_raw_stream.raw_stream_cdrs`
UNION ALL
SELECT 'raw_stream_money_transfers', COUNT(*) FROM `telecom-project-504210.rebtel_raw_stream.raw_stream_money_transfers`
UNION ALL
SELECT 'raw_batch_payments', COUNT(*) FROM `telecom-project-504210.rebtel_raw_batch.raw_batch_payments`
UNION ALL
SELECT 'raw_airbyte_zendesk_tickets', COUNT(*) FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`;
```
**Expected:** All 4 tables have row counts > 0.

### Check 2: Verify mart_fraud_prevention built successfully
```sql
SELECT fraud_risk_level, COUNT(*) AS user_count
FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
GROUP BY fraud_risk_level;
```
**Expected:** Rows for `HIGH_RISK_FRAUD`, `MEDIUM_RISK`, and `LOW_RISK`.

### Check 3: Verify JOIN integrity (user_ids match across all sources)
```sql
SELECT 
    COUNT(DISTINCT user_id) AS total_unique_users,
    COUNTIF(total_calls IS NOT NULL) AS users_with_calls,
    COUNTIF(total_transfers IS NOT NULL) AS users_with_transfers,
    COUNTIF(support_tickets IS NOT NULL) AS users_with_tickets
FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`;
```
**Expected:** `users_with_calls`, `users_with_transfers`, and `users_with_tickets` should all be > 0, confirming successful JOINs.

### Check 4: dbt Data Quality Tests
```sql
-- Unique user_id test
SELECT user_id, COUNT(*) FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`
GROUP BY user_id HAVING COUNT(*) > 1;
```
**Expected:** 0 rows (no duplicate user_ids).

**Print a summary table confirming:**
- BigQuery Table Name
- Row Count
- JOIN Coverage (%)
- dbt Test Status
- Status: PASS / FAIL

> [!CAUTION]
> STOP HERE. Do not proceed to Step 5 until Step 4 verification is complete and all checks PASS.

---

# ═══════════════════════════════════════════════════════════════
# STEP 5: BIGQUERY TO DASHBOARD (LOOKER / GCP BUILT-IN)
# ═══════════════════════════════════════════════════════════════

## 5.1 Objective
Connect the transformed dbt analytics tables from BigQuery to a **BI Dashboard** for executive reporting and fraud monitoring visualization.

## 5.2 Dashboard Options

### Option A: Looker Studio (Google Data Studio) — Free & Recommended
1. Go to [https://lookerstudio.google.com](https://lookerstudio.google.com).
2. Click **Create** → **Report**.
3. Click **Add Data** → Select **BigQuery**.
4. Navigate to Project: `telecom-project-504210` → Dataset: `rebtel_analytics`.
5. Select table: `mart_fraud_prevention` → Click **Add**.
6. Build Dashboard Panels:
   - **Panel 1:** Pie Chart → Fraud Risk Distribution (`HIGH_RISK_FRAUD`, `MEDIUM_RISK`, `LOW_RISK`).
   - **Panel 2:** Scorecard → Total Users, Total Calls, Total Transfers.
   - **Panel 3:** Bar Chart → Top 10 High-Risk Users by Transfer Amount.
   - **Panel 4:** Table → Detailed Fraud Risk Report.

### Option B: Streamlit Dashboard (Python — Interactive)
Build and run a Python Streamlit dashboard:
```bash
pip install streamlit plotly
python -m streamlit run src/dashboard.py
```

### Option C: GCP BigQuery Built-In Charts
1. In BigQuery SQL Editor, run any query.
2. Click **"Chart"** tab in the results panel.
3. BigQuery will auto-generate a visualization.

## 5.3 Key Dashboard KPIs to Visualize

| KPI | Source Table | SQL Metric |
| :--- | :--- | :--- |
| **Fraud Risk Distribution** | `mart_fraud_prevention` | `GROUP BY fraud_risk_level` |
| **Call Drop Rate (%)** | `mart_fraud_prevention` | `AVG(call_failure_rate_pct)` |
| **Total Money Transferred (USD)** | `mart_fraud_prevention` | `SUM(total_transfer_usd)` |
| **High-Risk Fraud Users** | `mart_fraud_prevention` | `WHERE fraud_risk_level = 'HIGH_RISK_FRAUD'` |
| **Support Ticket Volume** | `mart_fraud_prevention` | `SUM(support_tickets)` |

## 5.4 ✅ VERIFICATION GATE — STEP 5

### Check 1: Dashboard loads successfully with live BigQuery data
### Check 2: Fraud risk pie chart shows all 3 risk categories
### Check 3: Drill-down into HIGH_RISK_FRAUD users shows user_id, transfer amounts, and fraud flags

---

# ═══════════════════════════════════════════════════════════════
# EXECUTION SUMMARY
# ═══════════════════════════════════════════════════════════════

| Step | Description | Key Tool | Output |
| :--- | :--- | :--- | :--- |
| **Step 1** | Fetch Zendesk data via Airbyte into BigQuery | Airbyte EL | `rebtel_raw_airbyte.raw_airbyte_zendesk_tickets` |
| **Step 2** | Analyze Zendesk IDs + Generate matching synthetic data | Python + BigQuery | `data/stream/*.json`, `data/batch/*.csv` |
| **Step 3** | Stream via Pub/Sub + Dump all files to GCS Landing Zone | GCP Pub/Sub + GCS | `gs://rebtel-telecom-raw-landing-504210/` |
| **Step 4** | GCS → BigQuery Load + dbt Transformations + Fraud Mart | BigQuery + dbt Cloud | `rebtel_analytics.mart_fraud_prevention` |
| **Step 5** | BigQuery → Dashboard Visualization | Looker Studio / Streamlit | Executive Fraud Dashboard |
