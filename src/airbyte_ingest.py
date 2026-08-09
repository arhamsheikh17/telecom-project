"""
Step 1: Airbyte Simulation Script
Simulates Airbyte EL behavior:
  - Reads Zendesk tickets from data/saas/zendesk_tickets.json
  - Appends Airbyte audit metadata columns
  - Loads into BigQuery: telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets
"""

import json
import uuid
import datetime
import os
from google.cloud import bigquery

PROJECT_ID = "telecom-project-504210"
DATASET_ID = "rebtel_raw_airbyte"
TABLE_ID    = "raw_airbyte_zendesk_tickets"

# ── 1. Load raw Zendesk tickets ──────────────────────────────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
data_path  = os.path.join(script_dir, "..", "data", "saas", "zendesk_tickets.json")

with open(data_path, "r", encoding="utf-8") as f:
    raw_tickets = json.load(f)

print(f"[INFO] Loaded {len(raw_tickets)} raw Zendesk tickets from {data_path}")

# ── 2. Append Airbyte audit metadata ─────────────────────────────────────────
now_ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

enriched = []
for ticket in raw_tickets:
    row = {
        "ticket_id":              ticket["ticket_id"],
        "user_id":                ticket["user_id"],
        "created_at":             ticket["created_at"],
        "updated_at":             ticket["updated_at"],
        "issue_category":         ticket["issue_category"],
        "priority":               ticket["priority"],
        "ticket_status":          ticket["ticket_status"],
        "satisfaction_score":     ticket["satisfaction_score"],
        # Airbyte system columns
        "_airbyte_ab_id":         str(uuid.uuid4()),
        "_airbyte_emitted_at":    now_ts,
        "_airbyte_normalized_at": now_ts,
    }
    enriched.append(row)

print(f"[INFO] Enriched {len(enriched)} records with Airbyte audit metadata")

# ── 3. BigQuery schema ────────────────────────────────────────────────────────
schema = [
    bigquery.SchemaField("ticket_id",              "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("user_id",                "STRING",    mode="REQUIRED"),
    bigquery.SchemaField("created_at",             "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("updated_at",             "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("issue_category",         "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("priority",               "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("ticket_status",          "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("satisfaction_score",     "INTEGER",   mode="NULLABLE"),
    bigquery.SchemaField("_airbyte_ab_id",         "STRING",    mode="NULLABLE"),
    bigquery.SchemaField("_airbyte_emitted_at",    "TIMESTAMP", mode="NULLABLE"),
    bigquery.SchemaField("_airbyte_normalized_at", "TIMESTAMP", mode="NULLABLE"),
]

# ── 4. Create dataset + table, then load data ─────────────────────────────────
client = bigquery.Client(project=PROJECT_ID)

# Create dataset if not exists
dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
try:
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "US"
    client.create_dataset(dataset, exists_ok=True)
    print(f"[INFO] Dataset `{DATASET_ID}` ready")
except Exception as e:
    print(f"[WARN] Dataset creation: {e}")

# Create or replace table
table_ref = dataset_ref.table(TABLE_ID)
table = bigquery.Table(table_ref, schema=schema)
table = client.create_table(table, exists_ok=True)
print(f"[INFO] Table `{TABLE_ID}` ready")

# Insert rows
errors = client.insert_rows_json(table_ref, enriched)
if errors:
    print(f"[ERROR] BigQuery insert errors: {errors}")
    raise RuntimeError("BigQuery insert failed")
else:
    print(f"[SUCCESS] Inserted {len(enriched)} rows into `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`")

print("\n[DONE] Step 1 Complete - Zendesk data loaded into BigQuery via Airbyte simulation!")
