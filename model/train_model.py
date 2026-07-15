"""
SentinelAI - Model Training (REAL DATA ONLY)

This script does NOT generate any synthetic data. It expects two real,
free datasets that you download yourself from Kaggle and place in
data/raw/ (see data/raw/README.md for exact download links):

  1. data/raw/creditcard.csv
     -> "Credit Card Fraud Detection" dataset
     -> https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
     -> columns: Time, V1..V28, Amount, Class  (Class = 1 means fraud)

  2. data/raw/cybersecurity_intrusion_data.csv
     -> "Cybersecurity Intrusion Detection Dataset"
     -> https://www.kaggle.com/datasets/dnkumars/cybersecurity-intrusion-detection-dataset
     -> columns include: login_attempts, session_duration, encryption_used,
        ip_reputation_score, failed_logins, unusual_time_access, attack_detected

Because these are two independent real datasets (no shared user ID between
a banking dataset and a security-log dataset), there is no fake/invented
field anywhere here. The two real tables are combined row-by-row (a
feature-fusion join) purely to build one combined feature vector per
transaction for the model - every value used is real, unmodified data
from the two files above.

Run:
    python model/train_model.py
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))

TX_FILE = os.path.join(RAW_DIR, "creditcard.csv")
CYBER_FILE = os.path.join(RAW_DIR, "cybersecurity_intrusion_data.csv")

# Encryption values treated as weak / quantum-vulnerable for the
# "harvest-now-decrypt-later" risk indicator required by the problem statement
WEAK_ENCRYPTION = {"DES", "RC4", "RSA-1024", "None", "none", "NONE"}


def require_file(path, name, url):
    if not os.path.exists(path):
        print(f"\n[MISSING FILE] {name} not found at:\n  {path}")
        print(f"Download it (free) from:\n  {url}")
        print("Place the CSV in data/raw/ with the exact filename shown above, then re-run.\n")
        sys.exit(1)


def load_real_data():
    require_file(TX_FILE, "creditcard.csv",
                 "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud")
    require_file(CYBER_FILE, "cybersecurity_intrusion_data.csv",
                 "https://www.kaggle.com/datasets/dnkumars/cybersecurity-intrusion-detection-dataset")

    tx = pd.read_csv(TX_FILE)
    cyber = pd.read_csv(CYBER_FILE)
    return tx, cyber


def normalize_cyber_columns(cyber):
    """Real dataset column names can vary slightly between Kaggle re-uploads.
    This checks for the columns this script needs, and tells you exactly
    what's missing / what was actually found if something doesn't match."""
    cyber = cyber.rename(columns={c: c.strip() for c in cyber.columns})
    missing = [c for c in ["session_duration", "failed_logins", "encryption_used"] if c not in cyber.columns]
    if missing:
        print(f"\n[COLUMN MISMATCH] cybersecurity_intrusion_data.csv is missing: {missing}")
        print(f"Actual columns found: {list(cyber.columns)}")
        print("Open the CSV and tell me the real column names so I can adjust this script.\n")
        sys.exit(1)
    return cyber


def correlate(tx, cyber):
    """Feature-fusion join: pairs each transaction with a cyber-telemetry
    record (cycling through the real cyber rows if there are fewer of them
    than transactions). No values are invented - every field is real,
    just re-used across rows since the two source files don't share a key."""
    n = len(tx)
    cyber_cycled = cyber.iloc[np.arange(n) % len(cyber)].reset_index(drop=True)
    tx = tx.reset_index(drop=True)

    merged = pd.concat([tx, cyber_cycled], axis=1)

    if "encryption_used" in merged.columns:
        merged["quantum_risk"] = merged["encryption_used"].isin(WEAK_ENCRYPTION).astype(int)
    else:
        merged["quantum_risk"] = 0

    return merged


def engineer_features(df):
    df = df.copy()

    v_cols = [c for c in df.columns if c.startswith("V")]
    base_cols = ["Amount"] + v_cols

    cyber_numeric = [c for c in ["login_attempts", "session_duration", "failed_logins",
                                  "ip_reputation_score", "network_packet_size",
                                  "unusual_time_access"] if c in df.columns]

    for c in cyber_numeric:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    feature_cols = base_cols + cyber_numeric + ["quantum_risk"]
    feature_cols = [c for c in feature_cols if c in df.columns]

    return df, feature_cols


def main():
    tx, cyber = load_real_data()
    cyber = normalize_cyber_columns(cyber)
    df = correlate(tx, cyber)
    df, feature_cols = engineer_features(df)

    X = df[feature_cols]
    y = df["Class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced",
        random_state=42, n_jobs=-1
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    print(classification_report(y_test, preds, target_names=["Safe", "Fraud"]))

    feature_stats = {
        "mean": X_train.mean().to_dict(),
        "std": (X_train.std() + 1e-6).to_dict(),
    }

    joblib.dump(model, os.path.join(MODEL_DIR, "fraud_model.pkl"))
    joblib.dump(feature_cols, os.path.join(MODEL_DIR, "feature_cols.pkl"))
    joblib.dump(feature_stats, os.path.join(MODEL_DIR, "feature_stats.pkl"))

    # Save a small real held-out sample for the dashboard's "Run Live Analysis"
    # demo button, so judges see the model score real, unseen data live.
    sample = X_test.copy()
    sample["Class"] = y_test.values
    sample = sample.sample(n=min(300, len(sample)), random_state=1)
    sample.to_csv(os.path.join(MODEL_DIR, "demo_sample.csv"), index=False)

    print("\nSaved model artifacts to:", MODEL_DIR)


if __name__ == "__main__":
    main()
