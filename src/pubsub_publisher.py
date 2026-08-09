"""
Step 3b: Pub/Sub Publisher
Reads CDR and Money Transfer JSON files and publishes each record
to GCP Pub/Sub topics, simulating real-time streaming ingestion.
Topics:
  - rebtel-cdr-stream      → CDR records
  - rebtel-transfer-stream → Money transfer records
"""

import json
import os
import time
from google.cloud import pubsub_v1

PROJECT_ID = "telecom-project-504210"
CDR_TOPIC  = "rebtel-cdr-stream"
TRF_TOPIC  = "rebtel-transfer-stream"

script_dir = os.path.dirname(os.path.abspath(__file__))
cdr_path   = os.path.join(script_dir, "..", "data", "stream", "call_data_records.json")
trf_path   = os.path.join(script_dir, "..", "data", "stream", "money_transfers.json")

publisher = pubsub_v1.PublisherClient()


def publish_records(topic_id: str, records: list, label: str):
    topic_path = publisher.topic_path(PROJECT_ID, topic_id)
    futures = []
    for i, record in enumerate(records):
        data = json.dumps(record).encode("utf-8")
        future = publisher.publish(topic_path, data)
        futures.append(future)
        if (i + 1) % 100 == 0:
            print(f"  [{label}] Published {i+1}/{len(records)} messages...")
        # Small delay to simulate real-time stream (20ms)
        time.sleep(0.02)

    # Wait for all futures to complete
    errors = 0
    for future in futures:
        try:
            future.result(timeout=30)
        except Exception as e:
            print(f"  [WARN] Publish error: {e}")
            errors += 1

    print(f"  [{label}] Published {len(records) - errors}/{len(records)} messages successfully")
    return errors


# ── Publish CDRs ──────────────────────────────────────────────────────────────
print(f"[INFO] Loading CDR records from {cdr_path}...")
with open(cdr_path, "r", encoding="utf-8") as f:
    cdr_records = json.load(f)
print(f"[INFO] Publishing {len(cdr_records)} CDR records to topic `{CDR_TOPIC}`...")
cdr_errors = publish_records(CDR_TOPIC, cdr_records, "CDR")

# ── Publish Money Transfers ───────────────────────────────────────────────────
print(f"\n[INFO] Loading transfer records from {trf_path}...")
with open(trf_path, "r", encoding="utf-8") as f:
    trf_records = json.load(f)
print(f"[INFO] Publishing {len(trf_records)} transfer records to topic `{TRF_TOPIC}`...")
trf_errors = publish_records(TRF_TOPIC, trf_records, "TRANSFER")

print(f"\n{'='*50}")
print(f"CDR messages published:      {len(cdr_records) - cdr_errors}")
print(f"Transfer messages published: {len(trf_records) - trf_errors}")
print(f"{'='*50}")
print("[DONE] Step 3b Complete -- All stream records published to Pub/Sub!")
