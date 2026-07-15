# SentinelAI — Banking Threat Intelligence & Fraud Detection

100% free stack. No paid tools, no paid API keys anywhere in this project.

## Folder structure
```
sentinelai/
├── app.py                  # Flask app (routes, auth, API)
├── database.py             # SQLite setup (users, alerts, login history)
├── requirements.txt
├── data/
│   └── raw/                # <-- put the 2 real downloaded CSVs here (see README.md inside)
├── model/
│   ├── train_model.py      # trains the model on REAL data only
│   ├── predictor.py        # scoring + explainable-AI logic
│   └── (fraud_model.pkl, feature_cols.pkl, etc. created after training)
├── templates/              # every page as its own file
│   ├── login.html
│   ├── signup.html
│   ├── base.html            # shared sidebar/topbar layout
│   ├── dashboard.html
│   ├── live_monitoring.html
│   ├── cyber_telemetry.html
│   ├── threat_detection.html
│   ├── fraud_analytics.html
│   ├── quantum_risk.html
│   ├── reports.html
│   └── admin_settings.html
├── static/
│   ├── css/style.css
│   └── js/script.js
└── instance/                # SQLite .db file gets created here
```

## Setup (run in VS Code terminal)

```bash
cd sentinelai
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

## Step 1 — Get the real datasets (free)
Read `data/raw/README.md` — download the 2 Kaggle CSVs and place them in `data/raw/`.

## Step 2 — Train the model
```bash
python model/train_model.py
```
This prints accuracy/precision/recall and saves the trained model into `model/`.

## Step 3 — Initialize the database (creates default admin login)
```bash
python database.py
```

## Step 4 — Run the website
```bash
python app.py
```
Open **http://127.0.0.1:5000**

Login with:
- Email: `admin@sentinelai.com`
- Password: `Admin@123`

...or click "Sign up" to create your own analyst account.

## How it works
1. Log in / sign up.
2. Go to Dashboard (or any page) → click **"Run Live Analysis"**.
3. This scores real, unseen transactions (from the real Kaggle test split) using the trained RandomForest model.
4. Dashboard shows: safe/suspicious/fraud counts, risk scores, plain-English AI explanations, and quantum-risk flags.
5. Flagged items are saved to Reports & Alerts (SQLite) permanently.
6. Admin Settings shows registered users + login history.

## Do you need any API / API key?
**No.** This entire project runs 100% locally and free:
- No OpenAI/Claude/paid AI API — the model is your own trained scikit-learn RandomForest (`.pkl` file), loaded locally by Flask.
- No paid database — SQLite is a local file.
- No paid charting — Chart.js is free via CDN.
- The only external "download" step is grabbing the two real datasets from Kaggle, which is free (just requires a free Kaggle account to click download).

If you later want to deploy it online (optional, for judges to access remotely), free hosting options are Render, Railway free tier, or PythonAnywhere free tier — still no payment needed.
