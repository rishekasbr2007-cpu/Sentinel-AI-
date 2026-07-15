"""
SentinelAI - Flask backend
100% free stack: Flask + SQLite + scikit-learn. No paid services, no API keys.

Run:
    python app.py
Then open http://127.0.0.1:5000
"""

import os
import sys
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import get_db, init_db, DB_PATH
from model import predictor
from simulator import simulator

simulator.start()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

app = Flask(__name__)
app.secret_key = "sentinelai-dev-secret-change-this-for-real-deployment"


@app.after_request
def add_header(r):
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    return r



# ---------- Auth helpers ----------

def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject_user():
    return {"current_user_name": session.get("user_name"), "current_user_role": session.get("user_role")}


# ---------- Auth routes ----------

@app.route("/")
def root():
    return render_template("landing.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        import re
        def check_pw(pw):
            if len(pw) < 8: return False
            if not re.search(r"[A-Z]", pw): return False
            if not re.search(r"\d", pw): return False
            if not re.search(r"[!@#$%^&*()_+={}\[\]:;\"'<>,.?/\\|`~-]", pw): return False
            return True

        if not full_name or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth.html", active_tab="signup")
        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth.html", active_tab="signup")
        if not check_pw(password):
            flash("Password does not meet complexity requirements.", "error")
            return render_template("auth.html", active_tab="signup")

        db = get_db()
        existing = db.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("An account with that email already exists.", "error")
            db.close()
            return render_template("auth.html", active_tab="signup")

        db.execute(
            "INSERT INTO users (full_name, email, password_hash, role) VALUES (?, ?, ?, ?)",
            (full_name, email, generate_password_hash(password), "Security Analyst"),
        )
        db.commit()
        db.close()
        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))

    return render_template("auth.html", active_tab="signup")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

        success = user is not None and check_password_hash(user["password_hash"], password)
        db.execute(
            "INSERT INTO login_history (user_id, email, success) VALUES (?, ?, ?)",
            (user["id"] if user else None, email, 1 if success else 0),
        )
        db.commit()

        if success:
            session["user_id"] = user["id"]
            session["user_name"] = user["full_name"]
            session["user_role"] = user["role"]
            db.close()
            return redirect(url_for("dashboard"))

        db.close()
        flash("Invalid email or password.", "error")
        return render_template("auth.html", active_tab="login")

    return render_template("auth.html", active_tab="login")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- App pages ----------

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", model_ready=predictor.is_model_ready())


@app.route("/live-monitoring")
@login_required
def live_monitoring():
    return render_template("live_monitoring.html", model_ready=predictor.is_model_ready())


@app.route("/cyber-telemetry")
@login_required
def cyber_telemetry():
    return render_template("cyber_telemetry.html", model_ready=predictor.is_model_ready())


@app.route("/threat-detection")
@login_required
def threat_detection():
    return render_template("threat_detection.html", model_ready=predictor.is_model_ready())


@app.route("/fraud-analytics")
@login_required
def fraud_analytics():
    return render_template("fraud_analytics.html", model_ready=predictor.is_model_ready())


@app.route("/quantum-risk")
@login_required
def quantum_risk():
    return render_template("quantum_risk.html", model_ready=predictor.is_model_ready())


@app.route("/reports")
@login_required
def reports():
    db = get_db()
    alerts = db.execute("SELECT * FROM alerts ORDER BY created_at DESC LIMIT 200").fetchall()
    db.close()
    return render_template("reports.html", alerts=alerts, model_ready=predictor.is_model_ready())


@app.route("/admin-settings")
@login_required
def admin_settings():
    db = get_db()
    users = db.execute("SELECT id, full_name, email, role, created_at FROM users ORDER BY created_at DESC").fetchall()
    logins = db.execute("SELECT * FROM login_history ORDER BY created_at DESC LIMIT 25").fetchall()
    db.close()
    return render_template("admin_settings.html", users=users, logins=logins, model_ready=predictor.is_model_ready())
@app.route("/attack-chain")
@login_required
def attack_chain():
    return render_template("attack_chain.html", model_ready=predictor.is_model_ready())


@app.route("/predictive-risk")
@login_required
def predictive_risk():
    return render_template("predictive_risk.html", model_ready=predictor.is_model_ready())


# ---------- API: run the model on real held-out data ----------

@app.route("/api/run-analysis", methods=["POST"])
@login_required
def api_run_analysis():
    """Scores a batch of REAL, unseen transactions (saved by train_model.py
    from the real Kaggle test split) so judges see live AI predictions."""
    if not predictor.is_model_ready():
        return jsonify({"error": "Model not trained yet. Run: python model/train_model.py"}), 400

    sample_path = os.path.join(MODEL_DIR, "demo_sample.csv")
    if not os.path.exists(sample_path):
        return jsonify({"error": "No demo sample found. Re-run model/train_model.py"}), 400

    n = int(request.json.get("batch_size", 25)) if request.is_json else 25
    df = pd.read_csv(sample_path).sample(n=min(n, 300)).reset_index(drop=True)
    true_labels = df["Class"] if "Class" in df.columns else None

    scored = predictor.score_dataframe(df)

    db = get_db()
    for _, row in scored.iterrows():
        if row["risk_level"] in ("High", "Medium"):
            db.execute(
                "INSERT INTO alerts (transaction_ref, risk_score, risk_level, explanation, quantum_flag, status) "
                "VALUES (?, ?, ?, ?, ?, 'Open')",
                (f"TX-{_}", row["risk_score"], row["risk_level"], row["explanation"], int(row["quantum_flag"])),
            )
    db.commit()
    db.close()

    total = len(scored)
    safe = int((scored["risk_level"] == "Low").sum())
    suspicious = int((scored["risk_level"] == "Medium").sum())
    fraud_alerts = int((scored["risk_level"] == "High").sum())
    quantum_flags = int(scored["quantum_flag"].sum())

    return jsonify({
        "summary": {
            "total": total,
            "safe": safe,
            "suspicious": suspicious,
            "fraud_alerts": fraud_alerts,
            "quantum_flags": quantum_flags,
        },
        "transactions": scored[["risk_score", "risk_level", "explanation", "quantum_flag"]]
            .assign(ref=[f"TX-{i}" for i in range(total)])
            .to_dict(orient="records"),
    })


@app.route("/api/live-stream")
@login_required
def api_live_stream():
    n = request.args.get("n", 200, type=int)
    data = simulator.get_latest(n)
    
    # Calculate global summary from ALL available simulator memory to show continuous growth
    full_data = simulator.transactions
    
    total = len(full_data)
    safe = sum(1 for d in full_data if d["risk_level"] == "Low")
    suspicious = sum(1 for d in full_data if d["risk_level"] == "Medium")
    fraud_alerts = sum(1 for d in full_data if d["risk_level"] == "High")
    quantum_flags = sum(1 for d in full_data if d["quantum_flag"])
    
    return jsonify({
        "summary": {
            "total": total,
            "safe": safe,
            "suspicious": suspicious,
            "fraud_alerts": fraud_alerts,
            "quantum_flags": quantum_flags,
        },
        "transactions": data
    })


@app.route("/api/feedback", methods=["POST"])
@login_required
def api_feedback():
    data = request.json
    ref = data.get("ref")
    feedback = data.get("feedback")
    if not ref or feedback not in ("Confirmed", "False Alarm"):
        return jsonify({"error": "Invalid feedback"}), 400
        
    db = get_db()
    db.execute("UPDATE alerts SET analyst_feedback = ?, status = 'Closed' WHERE transaction_ref = ?", (feedback, ref))
    db.commit()
    db.close()
    
    # Also update the simulator in-memory so UI doesn't lose it if it polls again
    for tx in simulator.transactions:
        if tx["ref"] == ref:
            tx["analyst_feedback"] = feedback
            break
            
    return jsonify({"success": True})


@app.route("/api/stats")
@login_required
def api_stats():
    db = get_db()
    total_alerts = db.execute("SELECT COUNT(*) c FROM alerts").fetchone()["c"]
    high = db.execute("SELECT COUNT(*) c FROM alerts WHERE risk_level='High'").fetchone()["c"]
    quantum = db.execute("SELECT COUNT(*) c FROM alerts WHERE quantum_flag=1").fetchone()["c"]
    users = db.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    
    confirmed = db.execute("SELECT COUNT(*) c FROM alerts WHERE analyst_feedback='Confirmed'").fetchone()["c"]
    false_alarms = db.execute("SELECT COUNT(*) c FROM alerts WHERE analyst_feedback='False Alarm'").fetchone()["c"]
    db.close()
    
    total_feedback = confirmed + false_alarms
    accuracy = round((confirmed / total_feedback * 100) if total_feedback > 0 else 100, 1)
    fp_rate = round((false_alarms / total_feedback * 100) if total_feedback > 0 else 0, 1)
    
    return jsonify({
        "total_alerts": total_alerts, 
        "high_risk": high, 
        "quantum_flags": quantum, 
        "users": users,
        "accuracy": accuracy,
        "fp_rate": fp_rate,
        "total_feedback": total_feedback
    })


if __name__ == "__main__":
    if not os.path.exists(DB_PATH):
        init_db()
    app.run(debug=True, port=5000)
