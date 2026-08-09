"""Step 1 Verification Script"""
from google.cloud import bigquery

client = bigquery.Client(project="telecom-project-504210")
PROJECT = "telecom-project-504210"
DS      = "rebtel_raw_airbyte"
TBL     = "raw_airbyte_zendesk_tickets"
FULL    = f"`{PROJECT}.{DS}.{TBL}`"

# Check 1: Row count
q1 = client.query(f"SELECT COUNT(*) AS total FROM {FULL}")
total = list(q1.result())[0].total
print(f"Check 1 - Total rows: {total}  -> {'PASS' if total > 0 else 'FAIL'}")

# Check 2: Sample with Airbyte metadata
q2 = client.query(f"SELECT ticket_id, user_id, issue_category, _airbyte_ab_id, _airbyte_emitted_at FROM {FULL} LIMIT 3")
print("Check 2 - Sample rows with Airbyte metadata:")
for row in q2.result():
    print(f"  ticket={row.ticket_id}  user={row.user_id}  cat={row.issue_category}  ab_id={str(row._airbyte_ab_id)[:24]}...")

# Check 3: Distinct user_ids
q3 = client.query(f"SELECT COUNT(DISTINCT user_id) AS unique_users FROM {FULL}")
unique = list(q3.result())[0].unique_users
print(f"Check 3 - Distinct user_ids: {unique}")

# Check 4: Schema columns
q4 = client.query(f"SELECT column_name, data_type FROM `{PROJECT}.{DS}.INFORMATION_SCHEMA.COLUMNS` WHERE table_name = '{TBL}'")
cols = [(r.column_name, r.data_type) for r in q4.result()]
print(f"Check 4 - Schema columns ({len(cols)}):")
for col_name, dtype in cols:
    print(f"  {col_name:<35} {dtype}")

print()
print("=" * 50)
print("  STEP 1 VERIFICATION SUMMARY")
print("=" * 50)
print(f"  Table:             {DS}.{TBL}")
print(f"  Total Rows:        {total}")
print(f"  Distinct user_ids: {unique}")
print(f"  Schema columns:    {len(cols)}")
print(f"  Airbyte metadata:  PRESENT")
print(f"  Status:            {'PASS' if total > 0 else 'FAIL'}")
print("=" * 50)
