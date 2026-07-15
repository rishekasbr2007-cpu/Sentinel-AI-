import os
import csv
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
os.makedirs(RAW_DIR, exist_ok=True)

tx_file = os.path.join(RAW_DIR, "creditcard.csv")
cyber_file = os.path.join(RAW_DIR, "cybersecurity_intrusion_data.csv")

# 1. Generate creditcard.csv
print("Generating creditcard.csv...")
with open(tx_file, "w", newline="") as f:
    writer = csv.writer(f)
    # Header: Time, V1..V28, Amount, Class
    header = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount", "Class"]
    writer.writerow(header)
    
    for i in range(500):
        time = i * 10
        v_features = [round(random.gauss(0, 1), 6) for _ in range(28)]
        amount = round(random.uniform(0.5, 500.0), 2)
        # ~10% chance of fraud (Class = 1)
        is_fraud = 1 if random.random() < 0.1 else 0
        if is_fraud:
            v_features[0] += 3.0  # shift V1 to create a correlation
            v_features[1] -= 3.0  # shift V2
            amount = round(random.uniform(100.0, 2000.0), 2)
            
        writer.writerow([time] + v_features + [amount, is_fraud])

# 2. Generate cybersecurity_intrusion_data.csv
print("Generating cybersecurity_intrusion_data.csv...")
encryptions = ["AES-256", "AES-128", "TLS-1.3", "DES", "RC4", "RSA-1024", "None"]

with open(cyber_file, "w", newline="") as f:
    writer = csv.writer(f)
    header = [
        "session_duration", 
        "failed_logins", 
        "encryption_used", 
        "login_attempts", 
        "ip_reputation_score", 
        "network_packet_size", 
        "unusual_time_access"
    ]
    writer.writerow(header)
    
    for _ in range(500):
        sess_dur = round(random.uniform(10, 3600), 2)
        failed_log = random.randint(0, 5)
        enc = random.choice(encryptions)
        login_att = failed_log + random.randint(1, 3)
        ip_rep = round(random.uniform(0.0, 1.0), 2)
        net_size = random.randint(64, 1500)
        unusual_time = 1 if random.random() < 0.15 else 0
        
        # If weak encryption, let's simulate higher fail logins sometimes
        if enc in ["DES", "RC4", "None"]:
            failed_log = random.randint(2, 8)
            login_att = failed_log + random.randint(1, 2)
            
        writer.writerow([sess_dur, failed_log, enc, login_att, ip_rep, net_size, unusual_time])

print("Mock datasets generated successfully in data/raw/!")
