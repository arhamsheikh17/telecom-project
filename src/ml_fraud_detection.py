"""
ML Fraud Detection Pipeline — Rebtel Telecom Project
=====================================================
Data Source : BigQuery - telecom-project-504210.rebtel_analytics.mart_fraud_prevention
Target      : fraud_risk_level → Binary (1=Fraud, 0=Safe)
Models      : Random Forest (primary), XGBoost (secondary), Logistic Regression (baseline)
Outputs     : Model metrics, feature importance chart, confusion matrix, saved .pkl model
"""

import os
import warnings
import pickle
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from google.cloud import bigquery

warnings.filterwarnings('ignore')

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID  = "telecom-project-504210"
DATASET     = "rebtel_analytics"
TABLE       = "mart_fraud_prevention"
OUTPUT_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ml_outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 65)
print("  REBTEL TELECOM — ML FRAUD DETECTION PIPELINE")
print("=" * 65)

# ── Step 1: Load Data from BigQuery ──────────────────────────────────────────
print("\n[1/6] Loading data from BigQuery mart_fraud_prevention ...")
client = bigquery.Client(project=PROJECT_ID)

query = f"""
    SELECT
        user_id,
        total_calls,
        failed_calls,
        call_failure_rate_pct,
        avg_quality_score,
        avg_delivery_rate_pct,
        poor_quality_calls,
        total_transfers,
        total_transfer_usd,
        avg_transfer_usd,
        fraud_transfers,
        fraud_rate_pct,
        very_large_transfers,
        support_tickets,
        fraud_tickets,
        avg_satisfaction_score,
        total_fraud_signals,
        fraud_risk_level
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
"""

df = client.query(query).to_dataframe()
print(f"  [OK] Loaded {len(df)} rows, {df.shape[1]} columns")
print(f"  Fraud risk distribution:\n{df['fraud_risk_level'].value_counts().to_string()}")

# ── Step 2: Feature Engineering ───────────────────────────────────────────────
print("\n[2/6] Feature engineering ...")

# Fill NaN with 0 (users with no activity in certain domains)
feature_cols = [
    'total_calls', 'failed_calls', 'call_failure_rate_pct',
    'avg_quality_score', 'avg_delivery_rate_pct', 'poor_quality_calls',
    'total_transfers', 'total_transfer_usd', 'avg_transfer_usd',
    'fraud_transfers', 'fraud_rate_pct', 'very_large_transfers',
    'support_tickets', 'fraud_tickets', 'avg_satisfaction_score',
    'total_fraud_signals'
]

df[feature_cols] = df[feature_cols].fillna(0)

# Binary target: 1 = Fraud (CRITICAL or HIGH), 0 = Not Fraud
df['is_fraud'] = df['fraud_risk_level'].apply(
    lambda x: 1 if x in ('CRITICAL_RISK', 'HIGH_RISK_FRAUD') else 0
)

X = df[feature_cols].values
y = df['is_fraud'].values

print(f"  Features: {len(feature_cols)}")
print(f"  Fraud (1): {y.sum()} users | Safe (0): {(y == 0).sum()} users")
print(f"  Fraud rate: {y.mean()*100:.1f}%")

# ── Step 3: Train/Test Split ───────────────────────────────────────────────────
print("\n[3/6] Splitting data (70% train / 30% test) ...")

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42, stratify=y if y.sum() >= 2 else None
)

scaler = StandardScaler()
X_train_sc = scaler.fit_transform(X_train)
X_test_sc  = scaler.transform(X_test)

print(f"  Train: {len(X_train)} samples | Test: {len(X_test)} samples")

# ── Step 4: Train Models ───────────────────────────────────────────────────────
print("\n[4/6] Training models ...")

from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score, confusion_matrix,
                              classification_report)

models = {
    "Random Forest":         RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'),
    "Gradient Boosting":     GradientBoostingClassifier(n_estimators=100, random_state=42),
    "Logistic Regression":   LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced'),
}

results = {}
for name, model in models.items():
    # Use scaled data for Logistic Regression, raw for tree-based
    Xtr = X_train_sc if "Logistic" in name else X_train
    Xte = X_test_sc  if "Logistic" in name else X_test

    model.fit(Xtr, y_train)
    y_pred = model.predict(Xte)
    y_prob = model.predict_proba(Xte)[:, 1] if hasattr(model, "predict_proba") else y_pred

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec  = recall_score(y_test, y_pred, zero_division=0)
    f1   = f1_score(y_test, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_test, y_prob)
    except Exception:
        auc = 0.0
    cm   = confusion_matrix(y_test, y_pred)

    results[name] = {
        "model": model, "y_pred": y_pred, "y_prob": y_prob,
        "accuracy": acc, "precision": prec, "recall": rec,
        "f1": f1, "auc_roc": auc, "cm": cm
    }
    print(f"\n  [{name}]")
    print(f"    Accuracy:  {acc*100:.1f}%")
    print(f"    Precision: {prec*100:.1f}%")
    print(f"    Recall:    {rec*100:.1f}%")
    print(f"    F1 Score:  {f1*100:.1f}%")
    print(f"    AUC-ROC:   {auc:.3f}")

# Best model
best_name = max(results, key=lambda k: results[k]['f1'])
best      = results[best_name]
print(f"\n  *** Best Model: {best_name} (F1={best['f1']*100:.1f}%) ***")

# ── Step 5: Visualizations ────────────────────────────────────────────────────
print("\n[5/6] Generating charts ...")

# ── Chart 1: Model Comparison Dashboard ──────────────────────────────────────
fig = plt.figure(figsize=(20, 14), facecolor='#0a0e1a')
gs  = gridspec.GridSpec(2, 3, figure=fig, hspace=0.4, wspace=0.35)

colors_bar = ['#6366f1', '#10b981', '#f59e0b']
model_names = list(results.keys())

def make_ax(gs_pos):
    ax = fig.add_subplot(gs_pos)
    ax.set_facecolor('#1e293b')
    for spine in ax.spines.values():
        spine.set_color('#334155')
    ax.tick_params(colors='#94a3b8', labelsize=9)
    ax.title.set_color('#f1f5f9')
    ax.xaxis.label.set_color('#94a3b8')
    ax.yaxis.label.set_color('#94a3b8')
    return ax

# — Accuracy comparison —
ax1 = make_ax(gs[0, 0])
vals = [results[m]['accuracy']*100 for m in model_names]
bars = ax1.bar(model_names, vals, color=colors_bar, edgecolor='#0a0e1a', linewidth=1.5, zorder=3)
ax1.set_ylim(0, 115)
ax1.set_title('Model Accuracy (%)', fontsize=12, fontweight='bold', pad=10)
ax1.set_ylabel('Accuracy %')
ax1.grid(axis='y', color='#334155', linestyle='--', alpha=0.5, zorder=0)
for bar, v in zip(bars, vals):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{v:.1f}%',
             ha='center', va='bottom', color='#f1f5f9', fontsize=10, fontweight='bold')
ax1.set_xticks(range(len(model_names)))
ax1.set_xticklabels(['RF', 'GBoost', 'LR'], fontsize=9)

# — F1 Score comparison —
ax2 = make_ax(gs[0, 1])
vals2 = [results[m]['f1']*100 for m in model_names]
bars2 = ax2.bar(model_names, vals2, color=colors_bar, edgecolor='#0a0e1a', linewidth=1.5, zorder=3)
ax2.set_ylim(0, 115)
ax2.set_title('F1 Score (%)', fontsize=12, fontweight='bold', pad=10)
ax2.set_ylabel('F1 Score %')
ax2.grid(axis='y', color='#334155', linestyle='--', alpha=0.5, zorder=0)
for bar, v in zip(bars2, vals2):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2, f'{v:.1f}%',
             ha='center', va='bottom', color='#f1f5f9', fontsize=10, fontweight='bold')
ax2.set_xticks(range(len(model_names)))
ax2.set_xticklabels(['RF', 'GBoost', 'LR'], fontsize=9)

# — AUC-ROC comparison —
ax3 = make_ax(gs[0, 2])
vals3 = [results[m]['auc_roc'] for m in model_names]
bars3 = ax3.bar(model_names, vals3, color=colors_bar, edgecolor='#0a0e1a', linewidth=1.5, zorder=3)
ax3.set_ylim(0, 1.2)
ax3.set_title('AUC-ROC Score', fontsize=12, fontweight='bold', pad=10)
ax3.set_ylabel('AUC-ROC')
ax3.grid(axis='y', color='#334155', linestyle='--', alpha=0.5, zorder=0)
ax3.axhline(0.8, color='#6366f1', linestyle='--', alpha=0.6, label='Good threshold (0.8)')
for bar, v in zip(bars3, vals3):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02, f'{v:.3f}',
             ha='center', va='bottom', color='#f1f5f9', fontsize=10, fontweight='bold')
ax3.set_xticks(range(len(model_names)))
ax3.set_xticklabels(['RF', 'GBoost', 'LR'], fontsize=9)

# — Feature Importance (Best Model = Random Forest) —
ax4 = make_ax(gs[1, :2])
rf_model = results["Random Forest"]["model"]
importances = rf_model.feature_importances_
feat_series = pd.Series(importances, index=feature_cols).sort_values(ascending=True)
colors_feat = ['#6366f1' if v > feat_series.median() else '#334155' for v in feat_series.values]
bars4 = ax4.barh(feat_series.index, feat_series.values, color=colors_feat, edgecolor='#0a0e1a')
ax4.set_title('Feature Importance — Random Forest (Primary Model)', fontsize=12, fontweight='bold', pad=10)
ax4.set_xlabel('Importance Score')
ax4.grid(axis='x', color='#334155', linestyle='--', alpha=0.5)
for bar, v in zip(bars4, feat_series.values):
    ax4.text(v + 0.002, bar.get_y() + bar.get_height()/2,
             f'{v:.3f}', va='center', color='#94a3b8', fontsize=8)

# — Confusion Matrix (Best Model) —
ax5 = make_ax(gs[1, 2])
cm = best['cm']
im = ax5.imshow(cm, cmap='Blues', aspect='auto')
ax5.set_title(f'Confusion Matrix\n{best_name}', fontsize=12, fontweight='bold', pad=10)
ax5.set_xticks([0, 1]); ax5.set_yticks([0, 1])
ax5.set_xticklabels(['Predicted\nSafe', 'Predicted\nFraud'], color='#94a3b8', fontsize=9)
ax5.set_yticklabels(['Actual Safe', 'Actual Fraud'], color='#94a3b8', fontsize=9, rotation=90, va='center')
for i in range(2):
    for j in range(2):
        ax5.text(j, i, str(cm[i, j]), ha='center', va='center',
                 color='#f1f5f9' if cm[i, j] > cm.max()/2 else '#0a0e1a', fontsize=18, fontweight='bold')

# — Title —
fig.text(0.5, 0.97, 'Rebtel Telecom — ML Fraud Detection Dashboard',
         ha='center', va='top', fontsize=16, fontweight='800', color='#f1f5f9')
fig.text(0.5, 0.94, f'Source: BigQuery mart_fraud_prevention · Best Model: {best_name} (F1={best["f1"]*100:.1f}%)',
         ha='center', va='top', fontsize=11, color='#64748b')

chart_path = os.path.join(OUTPUT_DIR, 'fraud_detection_dashboard.png')
plt.savefig(chart_path, dpi=150, bbox_inches='tight', facecolor='#0a0e1a')
plt.close()
print(f"  [OK] Dashboard chart saved: {chart_path}")

# ── Chart 2: Risk Distribution Pie ───────────────────────────────────────────
fig2, ax = plt.subplots(figsize=(8, 6), facecolor='#0a0e1a')
ax.set_facecolor('#0a0e1a')
risk_counts = df['fraud_risk_level'].value_counts()
pie_colors  = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6']
wedges, texts, autotexts = ax.pie(
    risk_counts.values, labels=risk_counts.index,
    colors=pie_colors[:len(risk_counts)], autopct='%1.1f%%',
    startangle=140, pctdistance=0.75,
    wedgeprops=dict(edgecolor='#0a0e1a', linewidth=2)
)
for t in texts: t.set_color('#94a3b8'); t.set_fontsize(10)
for at in autotexts: at.set_color('#f1f5f9'); at.set_fontsize(9); at.set_fontweight('bold')
ax.set_title('Fraud Risk Level Distribution\n(mart_fraud_prevention)',
             color='#f1f5f9', fontsize=13, fontweight='bold', pad=20)
pie_path = os.path.join(OUTPUT_DIR, 'fraud_risk_distribution.png')
plt.savefig(pie_path, dpi=150, bbox_inches='tight', facecolor='#0a0e1a')
plt.close()
print(f"  [OK] Risk distribution chart saved: {pie_path}")

# ── Step 6: Save Best Model ───────────────────────────────────────────────────
print("\n[6/6] Saving best model ...")
model_path  = os.path.join(OUTPUT_DIR, 'fraud_detection_model.pkl')
scaler_path = os.path.join(OUTPUT_DIR, 'fraud_scaler.pkl')

with open(model_path, 'wb')  as f: pickle.dump(results[best_name]['model'], f)
with open(scaler_path, 'wb') as f: pickle.dump(scaler, f)

print(f"  [OK] Model saved:  {model_path}")
print(f"  [OK] Scaler saved: {scaler_path}")

# ── Final Summary Report ───────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("  ML FRAUD DETECTION — FINAL RESULTS SUMMARY")
print("=" * 65)
print(f"\n  {'Model':<22} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>8} {'AUC':>8}")
print(f"  {'-'*67}")
for name, r in results.items():
    marker = " <-- BEST" if name == best_name else ""
    print(f"  {name:<22} {r['accuracy']*100:>8.1f}% {r['precision']*100:>9.1f}% {r['recall']*100:>7.1f}% {r['f1']*100:>7.1f}% {r['auc_roc']:>8.3f}{marker}")

print(f"\n  Top 5 Most Important Features (Random Forest):")
top5 = pd.Series(rf_model.feature_importances_, index=feature_cols).sort_values(ascending=False).head(5)
for i, (feat, imp) in enumerate(top5.items(), 1):
    print(f"    {i}. {feat:<30} {imp:.4f}")

print(f"\n  Output Files:")
print(f"    - {chart_path}")
print(f"    - {pie_path}")
print(f"    - {model_path}")
print(f"    - {scaler_path}")
print("\n" + "=" * 65)
print("  [DONE] ML Pipeline Complete!")
print("=" * 65)
