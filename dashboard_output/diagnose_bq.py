import subprocess
import sys

print("=== GCP CONNECTION DIAGNOSTIC ===\n")

# Step 1: Get access token
print("[1] Getting access token...")
try:
    result = subprocess.run(
        ['gcloud.cmd', 'auth', 'print-access-token'],
        capture_output=True, text=True, shell=True, timeout=10
    )
    token = result.stdout.strip()
    print(f"    Token obtained: {bool(token)} (length={len(token)})")
    if result.stderr:
        print(f"    STDERR: {result.stderr[:200]}")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

# Step 2: Create BigQuery client
print("\n[2] Creating BigQuery client...")
try:
    import google.oauth2.credentials
    from google.cloud import bigquery
    creds = google.oauth2.credentials.Credentials(token=token)
    client = bigquery.Client(project='telecom-project-504210', credentials=creds)
    print("    Client created OK")
except Exception as e:
    print(f"    FAILED: {e}")
    sys.exit(1)

# Step 3: Test a simple query
print("\n[3] Testing BigQuery query on mart_fraud_prevention...")
try:
    sql = "SELECT COUNT(*) as cnt FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention`"
    job = client.query(sql)
    df = job.result(timeout=30).to_dataframe()
    print(f"    SUCCESS: {df.to_string()}")
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {e}")

# Step 4: List all tables in the dataset
print("\n[4] Listing all tables in rebtel_analytics dataset...")
try:
    tables = list(client.list_tables('rebtel_analytics'))
    if tables:
        for t in tables:
            print(f"    - {t.table_id}")
    else:
        print("    No tables found!")
except Exception as e:
    print(f"    FAILED: {type(e).__name__}: {e}")

# Step 5: Check Application Default Credentials
print("\n[5] Checking Application Default Credentials (ADC)...")
try:
    import google.auth
    creds_adc, project = google.auth.default()
    print(f"    ADC project: {project}")
    print(f"    ADC type: {type(creds_adc).__name__}")
except Exception as e:
    print(f"    ADC not set: {e}")

print("\n=== DIAGNOSTIC COMPLETE ===")
