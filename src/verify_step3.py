"""Step 3 Verification Script"""
from google.cloud import storage, pubsub_v1

PROJECT_ID  = "telecom-project-504210"
BUCKET_NAME = "rebtel-telecom-raw-landing-504210"

storage_client = storage.Client(project=PROJECT_ID)
pubsub_client  = pubsub_v1.PublisherClient()

print("=" * 60)
print("  STEP 3 VERIFICATION SUMMARY")
print("=" * 60)

# Check 1: Verify Pub/Sub topics exist
topics = [t.name.split("/")[-1] for t in pubsub_client.list_topics(project=f"projects/{PROJECT_ID}")]
print(f"Check 1 - Pub/Sub Topics found: {topics}")
topic_pass = "rebtel-cdr-stream" in topics and "rebtel-transfer-stream" in topics

# Check 2: Verify GCS Bucket & Files
bucket = storage_client.bucket(BUCKET_NAME)
blobs  = list(bucket.list_blobs())

cdr_files      = [b for b in blobs if b.name.startswith("stream/cdrs/")]
transfer_files = [b for b in blobs if b.name.startswith("stream/transfers/")]
batch_files    = [b for b in blobs if b.name.startswith("batch/payments/")]

print(f"Check 2 - GCS Landing Bucket (`gs://{BUCKET_NAME}`):")
print(f"  CDR stream files:      {len(cdr_files)}")
print(f"  Transfer stream files: {len(transfer_files)}")
print(f"  Batch payment files:   {len(batch_files)}")

gcs_pass = len(cdr_files) > 0 and len(transfer_files) > 0 and len(batch_files) > 0

print("-" * 60)
print(f"  Pub/Sub Topics Status: {'PASS' if topic_pass else 'FAIL'}")
print(f"  GCS Files Status:      {'PASS' if gcs_pass else 'FAIL'}")
print(f"  OVERALL STATUS:        {'PASS' if topic_pass and gcs_pass else 'FAIL'}")
print("=" * 60)
