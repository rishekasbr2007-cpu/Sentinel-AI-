"""
SentinelAI - Prediction & Explainable AI helper.
Loads the trained model and scores transactions, producing a risk score
(0-100), a risk level, and a plain-English explanation of WHY a
transaction was flagged (feature deviation from the normal/training mean).
"""

import os
import joblib
import numpy as np
import pandas as pd

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))

_model = None
_feature_cols = None
_feature_stats = None


def _load():
    global _model, _feature_cols, _feature_stats
    if _model is None:
        _model = joblib.load(os.path.join(MODEL_DIR, "fraud_model.pkl"))
        _feature_cols = joblib.load(os.path.join(MODEL_DIR, "feature_cols.pkl"))
        _feature_stats = joblib.load(os.path.join(MODEL_DIR, "feature_stats.pkl"))
    return _model, _feature_cols, _feature_stats


def is_model_ready():
    return os.path.exists(os.path.join(MODEL_DIR, "fraud_model.pkl"))


def _risk_level(score):
    if score >= 75:
        return "High"
    if score >= 40:
        return "Medium"
    return "Low"


def _explain_row(row, feature_cols, stats, top_n=3):
    """Simple, transparent explainable-AI: shows which features deviate
    most (in standard deviations) from the training-data average - this
    tells an analyst WHY the model considers a transaction unusual."""
    deviations = []
    for col in feature_cols:
        mean = stats["mean"].get(col, 0)
        std = stats["std"].get(col, 1)
        z = (row[col] - mean) / std
        deviations.append((col, z))

    deviations.sort(key=lambda x: abs(x[1]), reverse=True)
    top = deviations[:top_n]

    parts = []
    for col, z in top:
        direction = "unusually high" if z > 0 else "unusually low"
        parts.append(f"{col} is {direction}")
    return "; ".join(parts) if parts else "No strong deviation detected"


def score_dataframe(df):
    """Takes a DataFrame containing at least the model's feature columns
    and returns it with risk_score, risk_level, explanation, quantum_flag."""
    model, feature_cols, stats = _load()

    missing = [c for c in feature_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Input data is missing required columns: {missing}")

    X = df[feature_cols].fillna(0)
    probs = model.predict_proba(X)[:, 1]  # probability of fraud
    scores = (probs * 100).round(1)

    results = []
    for i, (_, row) in enumerate(X.iterrows()):
        results.append({
            "risk_score": float(scores[i]),
            "risk_level": _risk_level(scores[i]),
            "explanation": _explain_row(row, feature_cols, stats),
            "quantum_flag": bool(row.get("quantum_risk", 0)),
        })

    out = df.copy().reset_index(drop=True)
    res_df = pd.DataFrame(results)
    return pd.concat([out, res_df], axis=1)
