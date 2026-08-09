"""Step 2 Verification Script — Checks generated synthetic data files."""
import json
import csv

print("=" * 60)
print("STEP 2 VERIFICATION — Synthetic Data Files")
print("=" * 60)

# --- Check CDRs ---
cdrs = json.load(open('data/stream/call_data_records.json'))
cdr_count = len(cdrs)
cdr_cols = list(cdrs[0].keys())
expected_cdr_cols = ['call_id', 'user_id', 'duration_seconds', 'connection_success',
                     'call_quality_score', 'delivery_rate_percent', 'timestamp']

# --- Check Money Transfers ---
transfers = json.load(open('data/stream/money_transfers.json'))
transfer_count = len(transfers)
transfer_cols = list(transfers[0].keys())
expected_transfer_cols = ['transfer_id', 'user_id', 'sender_country', 'receiver_country',
                          'transfer_amount_usd', 'is_fraud_flag']

# --- Check Payments ---
with open('data/batch/financial_payments.csv') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
payment_count = len(rows)
payment_cols = reader.fieldnames
expected_payment_cols = ['transaction_id', 'user_id', 'subscription_plan', 'payment_amount', 'payment_status']

# --- Referential Integrity ---
zendesk = json.load(open('data/saas/zendesk_tickets.json'))
zendesk_ids = set(t['user_id'] for t in zendesk)
cdr_ids = set(c['user_id'] for c in cdrs)
transfer_ids = set(t['user_id'] for t in transfers)
payment_ids = set(p['user_id'] for p in rows)

orphan_cdrs = cdr_ids - zendesk_ids
orphan_transfers = transfer_ids - zendesk_ids
orphan_payments = payment_ids - zendesk_ids

# --- Print Report ---
print("\n[CHECK 1] Row Counts")
print(f"  CDRs:            {cdr_count:>6} records  (expected ~2500)  => {'PASS' if cdr_count >= 2000 else 'FAIL'}")
print(f"  Money Transfers: {transfer_count:>6} records  (expected ~1500)  => {'PASS' if transfer_count >= 1000 else 'FAIL'}")
print(f"  Payments:        {payment_count:>6} records  (expected ~1500)  => {'PASS' if payment_count >= 1000 else 'FAIL'}")

print("\n[CHECK 2] Column Names")
cdr_col_pass = set(expected_cdr_cols).issubset(set(cdr_cols))
trans_col_pass = set(expected_transfer_cols).issubset(set(transfer_cols))
pay_col_pass = set(expected_payment_cols).issubset(set(payment_cols))
print(f"  CDR columns:      {cdr_cols}")
print(f"  Expected subset:  {expected_cdr_cols}")
print(f"  => {'PASS' if cdr_col_pass else 'FAIL'}")
print(f"  Transfer columns: {transfer_cols}")
print(f"  => {'PASS' if trans_col_pass else 'FAIL'}")
print(f"  Payment columns:  {payment_cols}")
print(f"  => {'PASS' if pay_col_pass else 'FAIL'}")

print("\n[CHECK 3] Referential Integrity (user_ids vs Zendesk)")
print(f"  Zendesk unique user_ids:    {len(zendesk_ids)}")
print(f"  CDR unique user_ids:        {len(cdr_ids)}")
print(f"  Transfer unique user_ids:   {len(transfer_ids)}")
print(f"  Payment unique user_ids:    {len(payment_ids)}")
print(f"  CDR orphan IDs:      {len(orphan_cdrs)}  => {'PASS' if len(orphan_cdrs) == 0 else 'FAIL'}")
print(f"  Transfer orphan IDs: {len(orphan_transfers)}  => {'PASS' if len(orphan_transfers) == 0 else 'FAIL'}")
print(f"  Payment orphan IDs:  {len(orphan_payments)}  => {'PASS' if len(orphan_payments) == 0 else 'FAIL'}")

all_pass = (
    cdr_count >= 2000 and
    transfer_count >= 1000 and
    payment_count >= 1000 and
    cdr_col_pass and trans_col_pass and pay_col_pass and
    len(orphan_cdrs) == 0 and
    len(orphan_transfers) == 0 and
    len(orphan_payments) == 0
)
print("\n" + "=" * 60)
print(f"OVERALL STEP 2 STATUS: {'[PASS] -- Ready for Step 3' if all_pass else '[FAIL] -- Fix issues above'}")
print("=" * 60)
