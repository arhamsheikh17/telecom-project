"""
Step 3c: Pub/Sub Subscriber -> GCS Dump
Subscribes to Pub/Sub subscriptions, collects messages in micro-batches,
and writes them to GCS as JSON files.
Subscriptions:
  - rebtel-cdr-sub      -> gs://rebtel-telecom-raw-landing-504210/stream/cdrs/
  - rebtel-transfer-sub -> gs://rebtel-telecom-raw-landing-504210/stream/transfers/
"""

import json
import os
import time
from google.cloud import pubsub_v1, storage

PROJECT_ID  = "telecom-project-504210"
BUCKET_NAME = "rebtel-telecom-raw-landing-504210"
CDR_SUB     = "rebtel-cdr-sub"
TRF_SUB     = "rebtel-transfer-sub"
BATCH_SIZE  = 100   # messages per GCS file
TIMEOUT_SEC = 30    # seconds to wait for messages


def pull_and_dump(subscription_id: str, gcs_prefix: str, expected_count: int, label: str):
    """Pull all messages from a subscription and dump them to GCS in batches."""
    sub_client = pubsub_v1.SubscriberClient()
    gcs_client = storage.Client(project=PROJECT_ID)
    bucket     = gcs_client.bucket(BUCKET_NAME)

    sub_path   = sub_client.subscription_path(PROJECT_ID, subscription_id)
    all_records = []
    batch_num   = 1
    no_msg_count = 0
    MAX_NO_MSG   = 5   # stop after 5 empty pulls

    print(f"[INFO] Pulling from `{subscription_id}` (expecting ~{expected_count} messages)...")

    while len(all_records) < expected_count and no_msg_count < MAX_NO_MSG:
        response = sub_client.pull(
            request={"subscription": sub_path, "max_messages": BATCH_SIZE},
            timeout=TIMEOUT_SEC,
        )
        messages = response.received_messages
        if not messages:
            no_msg_count += 1
            time.sleep(2)
            continue

        no_msg_count = 0
        ack_ids  = []
        batch    = []

        for msg in messages:
            record = json.loads(msg.message.data.decode("utf-8"))
            batch.append(record)
            ack_ids.append(msg.ack_id)

        # Acknowledge messages
        sub_client.acknowledge(request={"subscription": sub_path, "ack_ids": ack_ids})

        # Upload batch to GCS
        blob_name = f"{gcs_prefix}/batch_{str(batch_num).zfill(3)}.json"
        blob = bucket.blob(blob_name)
        blob.upload_from_string(json.dumps(batch, indent=2), content_type="application/json")

        all_records.extend(batch)
        print(f"  [{label}] Batch {batch_num}: {len(batch)} messages -> gs://{BUCKET_NAME}/{blob_name}")
        batch_num += 1

    print(f"  [{label}] Total pulled & dumped: {len(all_records)} records in {batch_num-1} batches")
    return len(all_records)


# -- Pull CDRs ----------------------------------------------------------------
print("=" * 55)
print("STEP 3c: Pub/Sub -> GCS Dump")
print("=" * 55)

cdr_count = pull_and_dump(CDR_SUB,  "stream/cdrs",      2500, "CDR")
trf_count = pull_and_dump(TRF_SUB, "stream/transfers",  1500, "TRANSFER")

print(f"\n{'='*55}")
print(f"CDR records dumped to GCS:      {cdr_count}")
print(f"Transfer records dumped to GCS: {trf_count}")
print(f"{'='*55}")
print("[DONE] Step 3c Complete -- All stream data dumped from Pub/Sub -> GCS!")
