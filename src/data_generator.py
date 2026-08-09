"""
Step 2: Synthetic Data Generator
Reads exact user_id values from BigQuery Zendesk table, then generates:
  - 2500 Call Data Records (CDRs) → data/stream/call_data_records.json
  - 1500 Money Transfer records  → data/stream/money_transfers.json
  - 1500 Financial Payment rows  → data/batch/financial_payments.csv
All records use the SAME user_id pool from Zendesk for referential integrity.
"""

import json
import csv
import uuid
import random
import os
import datetime
from google.cloud import bigquery

PROJECT_ID = "telecom-project-504210"

# ── 1. Fetch user_ids from BigQuery ──────────────────────────────────────────
print("[INFO] Fetching user_ids from BigQuery Zendesk table...")
client = bigquery.Client(project=PROJECT_ID)

query = """
    SELECT DISTINCT user_id
    FROM `telecom-project-504210.rebtel_raw_airbyte.raw_airbyte_zendesk_tickets`
    ORDER BY user_id
"""
results = client.query(query).result()
user_ids = [row.user_id for row in results]
print(f"[INFO] Found {len(user_ids)} unique user_ids: {user_ids[:5]}...")

if not user_ids:
    raise ValueError("No user_ids found — run Step 1 (airbyte_ingest.py) first!")

# ── 2. Helper functions ───────────────────────────────────────────────────────
def random_ts(start_days=0, end_days=365):
    base = datetime.datetime(2024, 1, 1)
    delta = random.randint(start_days * 86400, end_days * 86400)
    return (base + datetime.timedelta(seconds=delta)).strftime("%Y-%m-%dT%H:%M:%SZ")

COUNTRIES = ["SE", "US", "UK", "DE", "NG", "IN", "PK", "PH", "TR", "MX", "BR", "ZA"]
PLANS      = ["basic", "standard", "premium", "family"]
PAY_STATUS = ["success", "failed", "pending", "refunded"]

script_dir = os.path.dirname(os.path.abspath(__file__))

# ── 3. Generate Call Data Records (CDRs) — 2500 rows ────────────────────────
print("[INFO] Generating 2500 CDR records...")
cdrs = []
for i in range(2500):
    quality = round(random.uniform(1.0, 5.0), 2)
    success = random.random() > 0.25   # 75% success rate (25% drop)
    cdrs.append({
        "call_id":               f"CALL-{str(i+1).zfill(5)}",
        "user_id":               random.choice(user_ids),
        "duration_seconds":      random.randint(10, 3600) if success else random.randint(0, 30),
        "connection_success":    success,
        "call_quality_score":    quality if success else round(random.uniform(0.5, 2.0), 2),
        "delivery_rate_percent": round(random.uniform(70.0, 99.9), 2) if success else round(random.uniform(0.0, 50.0), 2),
        "timestamp":             random_ts(),
    })

cdr_path = os.path.join(script_dir, "..", "data", "stream", "call_data_records.json")
with open(cdr_path, "w", encoding="utf-8") as f:
    json.dump(cdrs, f, indent=2)
print(f"[SUCCESS] Saved {len(cdrs)} CDRs -> {cdr_path}")

# -- 4. Generate Money Transfer records - 1500 rows ---------------------------
print("[INFO] Generating 1500 money transfer records...")
transfers = []
for i in range(1500):
    amount   = round(random.uniform(5.0, 2000.0), 2)
    is_fraud = random.random() < 0.08   # 8% fraud rate
    sender   = random.choice(COUNTRIES)
    receiver = random.choice([c for c in COUNTRIES if c != sender])
    transfers.append({
        "transfer_id":        f"TRF-{str(i+1).zfill(5)}",
        "user_id":            random.choice(user_ids),
        "sender_country":     sender,
        "receiver_country":   receiver,
        "transfer_amount_usd": amount if not is_fraud else round(random.uniform(800.0, 2000.0), 2),
        "is_fraud_flag":      is_fraud,
    })

trf_path = os.path.join(script_dir, "..", "data", "stream", "money_transfers.json")
with open(trf_path, "w", encoding="utf-8") as f:
    json.dump(transfers, f, indent=2)
print(f"[SUCCESS] Saved {len(transfers)} transfers -> {trf_path}")

# -- 5. Generate Financial Payments - 1500 rows -------------------------------
print("[INFO] Generating 1500 financial payment records...")
payments = []
for i in range(1500):
    plan   = random.choice(PLANS)
    amount = {"basic": 4.99, "standard": 9.99, "premium": 19.99, "family": 29.99}[plan]
    payments.append({
        "transaction_id":   f"TXN-{str(i+1).zfill(5)}",
        "user_id":          random.choice(user_ids),
        "subscription_plan": plan,
        "payment_amount":   amount + round(random.uniform(-0.5, 0.5), 2),
        "payment_status":   random.choice(PAY_STATUS),
    })

pay_path = os.path.join(script_dir, "..", "data", "batch", "financial_payments.csv")
with open(pay_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["transaction_id", "user_id", "subscription_plan", "payment_amount", "payment_status"])
    writer.writeheader()
    writer.writerows(payments)
print(f"[SUCCESS] Saved {len(payments)} payments -> {pay_path}")

# -- 6. Referential integrity check -------------------------------------------
print("\n[INFO] Running referential integrity check...")
zendesk_ids = set(user_ids)
cdr_ids      = set(r["user_id"] for r in cdrs)
trf_ids      = set(r["user_id"] for r in transfers)
pay_ids      = set(r["user_id"] for r in payments)

orphan_cdr  = cdr_ids - zendesk_ids
orphan_trf  = trf_ids - zendesk_ids
orphan_pay  = pay_ids - zendesk_ids

print(f"\n{'='*55}")
print(f"{'File':<30} {'Rows':>6} {'Orphan IDs':>10} {'Status':>6}")
print(f"{'='*55}")
print(f"{'call_data_records.json':<30} {len(cdrs):>6} {len(orphan_cdr):>10} {'PASS' if not orphan_cdr else 'FAIL':>6}")
print(f"{'money_transfers.json':<30} {len(transfers):>6} {len(orphan_trf):>10} {'PASS' if not orphan_trf else 'FAIL':>6}")
print(f"{'financial_payments.csv':<30} {len(payments):>6} {len(orphan_pay):>10} {'PASS' if not orphan_pay else 'FAIL':>6}")
print(f"{'='*55}")

if orphan_cdr or orphan_trf or orphan_pay:
    raise ValueError("Referential integrity check FAILED!")

print(f"[DONE] Step 2 Complete - All synthetic data generated with full referential integrity!")
