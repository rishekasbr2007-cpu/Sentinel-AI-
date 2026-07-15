# Real Datasets Needed (Free — Kaggle account required, no payment)

Download these two REAL datasets and place them in this `data/raw/` folder
with the EXACT filenames below. Nothing in this project is auto-generated —
the model only trains on these real files.

## 1. creditcard.csv
- Dataset: "Credit Card Fraud Detection"
- Link: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud
- Click "Download" (free, just needs a free Kaggle sign-in)
- Unzip and place `creditcard.csv` directly in this folder:
  `data/raw/creditcard.csv`
- Columns: Time, V1...V28, Amount, Class (Class = 1 means fraud)

## 2. cybersecurity_intrusion_data.csv
- Dataset: "Cybersecurity Intrusion Detection Dataset"
- Link: https://www.kaggle.com/datasets/dnkumars/cybersecurity-intrusion-detection-dataset
- Download and place the CSV here as:
  `data/raw/cybersecurity_intrusion_data.csv`
- If the downloaded filename is different, just rename it to match exactly.

## After both files are here:
```
python model/train_model.py
```

If the cyber dataset's real column names differ slightly from what the
script expects, `train_model.py` will print the exact columns it found and
what it needs — just tell Claude the printed column names and the script
will be adjusted, no guessing/fake data involved.
