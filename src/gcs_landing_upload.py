"""
Step 3a: GCS Landing Upload
Uploads static batch data (financial_payments.csv) to GCS bucket.
Destination: gs://rebtel-telecom-raw-landing-504210/batch/payments/financial_payments.csv
"""

import os
from google.cloud import storage

PROJECT_ID  = "telecom-project-504210"
BUCKET_NAME = "rebtel-telecom-raw-landing-504210"

script_dir  = os.path.dirname(os.path.abspath(__file__))
pay_path    = os.path.join(script_dir, "..", "data", "batch", "financial_payments.csv")

client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(BUCKET_NAME)

blob = bucket.blob("batch/payments/financial_payments.csv")
blob.upload_from_filename(pay_path)
print(f"[SUCCESS] Uploaded financial_payments.csv -> gs://{BUCKET_NAME}/batch/payments/financial_payments.csv")
print(f"  Size: {blob.size} bytes")
print("\n[DONE] Batch data uploaded to GCS successfully!")
