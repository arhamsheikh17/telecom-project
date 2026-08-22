import subprocess, os
import google.oauth2.credentials
from google.cloud import bigquery

def get_token():
    for cmd in [['gcloud.cmd', 'auth', 'print-access-token'], ['gcloud', 'auth', 'print-access-token']]:
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=5)
            lines = [l.strip() for l in res.stdout.splitlines() if l.strip().startswith('ya29.') or l.strip().startswith('ya29_')]
            if lines:
                return lines[0]
            last_line = res.stdout.strip().splitlines()[-1].strip()
            if len(last_line) > 50 and not ' ' in last_line:
                return last_line
        except Exception as e:
            print('Err:', e)
    return None

token = get_token()
print('Extracted Token length:', len(token) if token else 0)

creds = google.oauth2.credentials.Credentials(token=token)
client = bigquery.Client(project='telecom-project-504210', credentials=creds)

query = "SELECT user_id, fraud_risk_level, total_fraud_signals FROM `telecom-project-504210.rebtel_analytics.mart_fraud_prevention` LIMIT 5"
df = client.query(query).to_dataframe()
print("QUERY SUCCESSFUL!")
print(df)
