"""
Step 4a: GCS to BigQuery Loader
Loads all raw files from GCS Landing Zone into BigQuery raw datasets:
  - stream/cdrs/*.json      → rebtel_raw_stream.raw_stream_cdrs
  - stream/transfers/*.json → rebtel_raw_stream.raw_stream_money_transfers
  - batch/payments/*.csv    → rebtel_raw_batch.raw_batch_payments
"""

import json
from google.cloud import bigquery, storage

PROJECT_ID  = "telecom-project-504210"
BUCKET_NAME = "rebtel-telecom-raw-landing-504210"
LOCATION    = "US"

client = bigquery.Client(project=PROJECT_ID)
storage_client = storage.Client(project=PROJECT_ID)


def create_dataset(dataset_id: str):
    """Create a BigQuery dataset if it doesn't exist."""
    ref = bigquery.DatasetReference(PROJECT_ID, dataset_id)
    ds  = bigquery.Dataset(ref)
    ds.location = LOCATION
    client.create_dataset(ds, exists_ok=True)
    print(f"[INFO] Dataset `{dataset_id}` ready")


def load_json_stream_from_gcs(prefix: str, dataset_id: str, table_id: str, schema: list):
    """Read micro-batch JSON array files from GCS and load into BigQuery."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs  = list(bucket.list_blobs(prefix=prefix))
    
    all_records = []
    for blob in blobs:
        if blob.name.endswith(".json"):
            content = blob.download_as_text()
            batch = json.loads(content)
            all_records.extend(batch)
            
    table_ref = f"{PROJECT_ID}.{dataset_id}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    
    load_job = client.load_table_from_json(all_records, table_ref, job_config=job_config)
    load_job.result()   # Wait for job to finish
    table = client.get_table(table_ref)
    print(f"[SUCCESS] Loaded {table.num_rows} rows into `{table_ref}` from {len(blobs)} GCS blobs")
    return table.num_rows


def load_csv_from_gcs(gcs_uri_pattern: str, dataset_id: str, table_id: str, schema: list):
    """Load CSV from GCS into BigQuery."""
    table_ref = f"{PROJECT_ID}.{dataset_id}.{table_id}"
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        schema=schema,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=False,
    )
    load_job = client.load_table_from_uri(gcs_uri_pattern, table_ref, job_config=job_config)
    load_job.result()
    table = client.get_table(table_ref)
    print(f"[SUCCESS] Loaded {table.num_rows} rows into `{table_ref}`")
    return table.num_rows


# ── Schemas ───────────────────────────────────────────────────────────────────
cdr_schema = [
    bigquery.SchemaField("call_id",               "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("user_id",               "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("duration_seconds",      "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("connection_success",    "BOOLEAN", mode="NULLABLE"),
    bigquery.SchemaField("call_quality_score",    "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("delivery_rate_percent", "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("timestamp",             "TIMESTAMP", mode="NULLABLE"),
]

transfer_schema = [
    bigquery.SchemaField("transfer_id",          "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("user_id",              "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("sender_country",       "STRING",  mode="NULLABLE"),
    bigquery.SchemaField("receiver_country",     "STRING",  mode="NULLABLE"),
    bigquery.SchemaField("transfer_amount_usd",  "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("is_fraud_flag",        "BOOLEAN", mode="NULLABLE"),
]

payment_schema = [
    bigquery.SchemaField("transaction_id",    "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("user_id",           "STRING",  mode="REQUIRED"),
    bigquery.SchemaField("subscription_plan", "STRING",  mode="NULLABLE"),
    bigquery.SchemaField("payment_amount",    "FLOAT",   mode="NULLABLE"),
    bigquery.SchemaField("payment_status",    "STRING",  mode="NULLABLE"),
]

# ── Create Datasets ───────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 4a: Loading GCS files into BigQuery")
print("=" * 60)

create_dataset("rebtel_raw_stream")
create_dataset("rebtel_raw_batch")
create_dataset("rebtel_analytics")

# ── Load Tables ───────────────────────────────────────────────────────────────
print("\n[INFO] Loading CDR stream data from GCS...")
cdr_rows = load_json_stream_from_gcs(
    "stream/cdrs/",
    "rebtel_raw_stream", "raw_stream_cdrs", cdr_schema
)

print("\n[INFO] Loading money transfer stream data from GCS...")
trf_rows = load_json_stream_from_gcs(
    "stream/transfers/",
    "rebtel_raw_stream", "raw_stream_money_transfers", transfer_schema
)

print("\n[INFO] Loading batch payment data from GCS...")
pay_rows = load_csv_from_gcs(
    f"gs://{BUCKET_NAME}/batch/payments/financial_payments.csv",
    "rebtel_raw_batch", "raw_batch_payments", payment_schema
)

print(f"\n{'='*60}")
print(f"{'Table':<45} {'Rows':>10}")
print(f"{'='*60}")
print(f"{'rebtel_raw_stream.raw_stream_cdrs':<45} {cdr_rows:>10}")
print(f"{'rebtel_raw_stream.raw_stream_money_transfers':<45} {trf_rows:>10}")
print(f"{'rebtel_raw_batch.raw_batch_payments':<45} {pay_rows:>10}")
print(f"{'='*60}")
print("\n[DONE] Step 4a Complete - All GCS data loaded into BigQuery!")
