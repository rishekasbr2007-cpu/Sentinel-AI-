"""
Background data simulator for SentinelAI.
Generates realistic mock banking and telemetry data.
"""
import time
import random
import threading
import sqlite3
import os
from collections import deque
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "instance", "sentinelai.db")

class DataSimulator:
    def __init__(self):
        self.transactions = []
        self.counter = 0
        self.lock = threading.Lock()
        
        self.cities = [
            "New York", "London", "Tokyo", "Paris", "Berlin", 
            "Sydney", "Singapore", "Dubai", "Toronto", "Hong Kong",
            "Mumbai", "San Francisco", "Amsterdam", "Frankfurt", "Zurich"
        ]
        self.accounts = [f"ACC-{random.randint(1000, 9999)}" for _ in range(50)]
        self.ips = [f"192.168.1.{random.randint(1, 255)}" for _ in range(30)]
        self.active_attack = None
        
    def generate_fake_transaction(self, force_safe=False, force_suspicious=False):
        self.counter += 1
        ref = f"TX-SIM-{self.counter:04d}"
        
        is_suspicious = False
        account_id = random.choice(self.accounts)
        ip_address = random.choice(self.ips)
        
        if force_safe:
            is_suspicious = False
        elif force_suspicious:
            is_suspicious = True
        elif self.active_attack and self.active_attack["remaining"] > 0:
            is_suspicious = True
            account_id = self.active_attack["account_id"]
            ip_address = self.active_attack["ip_address"]
            self.active_attack["remaining"] -= 1
        else:
            is_suspicious = random.random() < 0.12
            if is_suspicious:
                self.active_attack = {
                    "account_id": account_id,
                    "ip_address": ip_address,
                    "remaining": random.randint(1, 3)
                }

        early_warning = False
        
        if is_suspicious:
            amount = round(random.uniform(5000, 50000), 2)
            risk_score = random.uniform(65, 99)
            risk_level = "High" if risk_score > 85 else "Medium"
            
            attack_type = random.choice(["brute_force", "impossible_travel", "known_bad_ip", "quantum_risk"])
            quantum_flag = (attack_type == "quantum_risk")
            
            if attack_type == "brute_force":
                explanation = f"Unusual amount (${amount:,.2f}) after multiple failed logins."
                failed_logins = random.randint(10, 50)
                location = random.choice(self.cities)
            elif attack_type == "impossible_travel":
                loc1 = random.choice(self.cities)
                loc2 = random.choice([c for c in self.cities if c != loc1])
                explanation = f"Impossible travel detected between {loc1} and {loc2}."
                failed_logins = random.randint(0, 2)
                location = loc2
            elif attack_type == "known_bad_ip":
                explanation = f"Transaction originating from known malicious IP block."
                failed_logins = random.randint(1, 5)
                location = random.choice(self.cities)
            elif attack_type == "quantum_risk":
                explanation = f"Suspicious activity on session using vulnerable legacy encryption."
                failed_logins = random.randint(0, 3)
                location = random.choice(self.cities)
                
            if quantum_flag:
                encryption = random.choice(["DES", "RC4", "RSA-1024"])
            else:
                encryption = "TLS 1.3"
                
        else:
            early_warning = random.random() < 0.1
            amount = round(random.uniform(5, 500), 2)
            if early_warning:
                risk_score = random.uniform(55, 75)
                risk_level = "Medium"
                explanation = "Behavioral drift detected (Early Warning). Unusual activity pattern."
            else:
                risk_score = random.uniform(1, 30)
                risk_level = "Low"
                explanation = "Normal transaction pattern."
                
            quantum_flag = False
            failed_logins = 0
            location = random.choice(self.cities)
            encryption = "TLS 1.3"
            
        data = {
            "ref": ref,
            "account_id": account_id,
            "ip_address": ip_address,
            "amount": amount,
            "location": location,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "explanation": explanation,
            "quantum_flag": int(quantum_flag),
            "early_warning": early_warning,
            "failed_logins": failed_logins,
            "encryption": encryption,
            "analyst_feedback": None
        }
        
        if risk_level in ("High", "Medium"):
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO alerts (transaction_ref, risk_score, risk_level, explanation, quantum_flag, status) "
                    "VALUES (?, ?, ?, ?, ?, 'Open')",
                    (ref, risk_score, risk_level, explanation, int(quantum_flag))
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"[Simulator] DB Error: {e}")
                
        return data

    def _loop(self):
        print("[Simulator] Started background data generation...")
        
        # Pre-seed with normal baseline and some suspicious
        with self.lock:
            for _ in range(40):
                self.transactions.append(self.generate_fake_transaction(force_safe=True))
            for _ in range(8):
                self.transactions.append(self.generate_fake_transaction(force_suspicious=True))
                
        while True:
            # Sleep exactly 15 seconds to match the UI polling rate
            time.sleep(15)
            
            new_txs = []
            
            # Occasionally (10% chance) introduce a bigger change (burst of suspicious activity)
            if random.random() < 0.1:
                # Burst: 3-5 suspicious
                for _ in range(random.randint(3, 5)):
                    new_txs.append(self.generate_fake_transaction(force_suspicious=True))
                # Plus some normal traffic
                for _ in range(random.randint(1, 3)):
                    new_txs.append(self.generate_fake_transaction(force_safe=True))
            else:
                # Normal steady growth (2-5 records)
                for _ in range(random.randint(2, 5)):
                    new_txs.append(self.generate_fake_transaction())
                    
            with self.lock:
                for tx in new_txs:
                    self.transactions.append(tx)

    def start(self):
        t = threading.Thread(target=self._loop, daemon=True)
        t.start()

    def get_latest(self, n=200):
        with self.lock:
            return self.transactions[-n:]

# Global singleton
simulator = DataSimulator()
