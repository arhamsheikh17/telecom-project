"""
Auth helper: Generate application_default_credentials.json from gcloud credentials.db
Run this ONCE to create the ADC file that Python SDK needs.
"""
import os
import json
import sqlite3
import sys

CRED_DB = r"C:\Users\HP\AppData\Roaming\gcloud\credentials.db"
ADC_PATH = r"C:\Users\HP\AppData\Roaming\gcloud\application_default_credentials.json"

conn = sqlite3.connect(CRED_DB)
cursor = conn.cursor()
cursor.execute("SELECT account_id, value FROM credentials")
rows = cursor.fetchall()
conn.close()

print(f"Found {len(rows)} credential entries:")
for i, (account_id, value) in enumerate(rows):
    print(f"  [{i}] {account_id}")

if not rows:
    print("ERROR: No credentials found in credentials.db")
    sys.exit(1)

# Use the gmail account credentials
target = None
for account_id, value in rows:
    if "gmail" in account_id.lower():
        target = (account_id, value)
        break

if not target:
    target = rows[0]

account_id, value = target
cred_data = json.loads(value)
print(f"\nUsing account: {account_id}")
print(f"Credential keys: {list(cred_data.keys())}")

# Build ADC JSON
adc = {
    "client_id": cred_data.get("client_id", "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com"),
    "client_secret": cred_data.get("client_secret", ""),
    "refresh_token": cred_data.get("refresh_token", ""),
    "type": "authorized_user",
    "universe_domain": "googleapis.com"
}

if not adc["refresh_token"]:
    print("ERROR: No refresh_token found!")
    print("Full cred data:", json.dumps(cred_data, indent=2))
    sys.exit(1)

with open(ADC_PATH, "w") as f:
    json.dump(adc, f, indent=2)

print(f"\n[SUCCESS] Created ADC file: {ADC_PATH}")
print(f"ADC contents: client_id={adc['client_id'][:20]}..., refresh_token present: {bool(adc['refresh_token'])}")
