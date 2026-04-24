import socket
import json
import os
import random
import time
from datetime import datetime

import requests

API_KEY = "raspberry-secret-key"
DEVICE_ROLE = "edge_device"
CLOUD_URL = "http://192.168.2.35:5000/data"

PATIENTS = [
    {
        "patient_id": "patient_001",
        "full_name": "Marie Dubois",
        "age": 45,
        "sex": "F",
        "address": "12 Rue des Lilas, Chicoutimi",
        "phone": "418-555-0101",
        "emergency_contact": "Claire Dubois - 418-555-0191",
        "profile": "stable"
    },
    {
        "patient_id": "patient_002",
        "full_name": "Jean Tremblay",
        "age": 75,
        "sex": "M",
        "address": "45 Avenue du Parc, Saguenay",
        "phone": "418-555-0102",
        "emergency_contact": "Luc Tremblay - 418-555-0192",
        "profile": "infection_progressive"
    },
    {
        "patient_id": "patient_003",
        "full_name": "Amina Bouchard",
        "age": 90,
        "sex": "F",
        "address": "8 Rue du Centre, Jonquière",
        "phone": "418-555-0103",
        "emergency_contact": "Nadia Bouchard - 418-555-0193",
        "profile": "fragile"
    },
    {
        "patient_id": "patient_004",
        "full_name": "Paul Gagnon",
        "age": 84,
        "sex": "M",
        "address": "27 Boulevard Talbot, Chicoutimi",
        "phone": "418-555-0104",
        "emergency_contact": "Sophie Gagnon - 418-555-0194",
        "profile": "isolated_anomalies"
    },
]


CYCLE_COUNTER = {p["patient_id"]: 0 for p in PATIENTS}

EDGE_DIR = os.path.dirname(os.path.abspath(__file__))
PENDING_FILE = os.path.join(EDGE_DIR, "pending_data.json")


def read_pending_data():
    if not os.path.exists(PENDING_FILE):
        return []
    try:
        with open(PENDING_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def write_pending_data(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_pending_payload(payload):
    data = read_pending_data()
    data.append(payload)
    write_pending_data(data)
    print(f"[EDGE] Données stockées localement pour {payload['patient_id']}")


def resend_pending_data():
    data = read_pending_data()
    if not data:
        return

    print(f"[EDGE] Tentative de renvoi de {len(data)} donnée(s) en attente...")
    remaining = []

    for payload in data:
        try:
            response = requests.post(CLOUD_URL, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"[EDGE] Renvoi réussi pour {payload['patient_id']}")
            else:
                print(f"[EDGE] Renvoi échoué ({response.status_code}) pour {payload['patient_id']}")
                remaining.append(payload)
        except requests.exceptions.RequestException:
            remaining.append(payload)

    write_pending_data(remaining)

    if not remaining:
        print("[EDGE] Buffer vidé avec succès.")
    else:
        print(f"[EDGE] {len(remaining)} donnée(s) restent en attente.")


def generate_stable():
    return {
        "temperature": round(random.uniform(36.5, 37.2), 1),
        "heart_rate": random.randint(65, 85),
        "spo2": random.randint(97, 100),
        "respiratory_rate": random.randint(12, 17),
        "systolic_pressure": random.randint(110, 122),
        "confusion": False,
    }


def generate_infection_progressive(patient_id):
    CYCLE_COUNTER[patient_id] += 1
    step = CYCLE_COUNTER[patient_id]

    temperature = min(39.5, 36.9 + step * 0.12 + random.uniform(-0.2, 0.2))
    heart_rate = min(125, 82 + step * 1.8 + random.randint(-2, 3))
    spo2 = max(90, 98 - (step // 4) + random.randint(-1, 0))
    respiratory_rate = min(30, 15 + (step // 2) + random.randint(-1, 1))
    systolic_pressure = max(90, 112 - step + random.randint(-2, 2))
    confusion = step >= 10 and random.choice([False, False, True])

    return {
        "temperature": round(temperature, 1),
        "heart_rate": int(heart_rate),
        "spo2": int(spo2),
        "respiratory_rate": int(respiratory_rate),
        "systolic_pressure": int(systolic_pressure),
        "confusion": confusion,
    }


def generate_fragile():
    return {
        "temperature": round(random.uniform(36.0, 37.8), 1),
        "heart_rate": random.randint(82, 108),
        "spo2": random.randint(93, 97),
        "respiratory_rate": random.randint(18, 24),
        "systolic_pressure": random.randint(90, 103),
        "confusion": random.choice([False, False, True]),
    }


def generate_isolated_anomalies():
    anomaly_type = random.choice(["heart_rate", "spo2", "resp", "pressure", "none"])

    data = {
        "temperature": round(random.uniform(36.5, 37.4), 1),
        "heart_rate": random.randint(68, 88),
        "spo2": random.randint(96, 99),
        "respiratory_rate": random.randint(12, 18),
        "systolic_pressure": random.randint(108, 123),
        "confusion": False,
    }

    if anomaly_type == "heart_rate":
        data["heart_rate"] = random.randint(101, 118)
    elif anomaly_type == "spo2":
        data["spo2"] = random.randint(92, 94)
    elif anomaly_type == "resp":
        data["respiratory_rate"] = random.randint(22, 25)
    elif anomaly_type == "pressure":
        data["systolic_pressure"] = random.randint(95, 100)

    return data


def generate_patient_data(patient):
    profile = patient["profile"]
    patient_id = patient["patient_id"]

    if profile == "stable":
        return generate_stable()
    if profile == "infection_progressive":
        return generate_infection_progressive(patient_id)
    if profile == "fragile":
        return generate_fragile()
    if profile == "isolated_anomalies":
        return generate_isolated_anomalies()
    return generate_stable()


def calculate_score(data):
    score = 0

    if data["temperature"] >= 38.0 or data["temperature"] <= 35.0:
        score += 1
    if data["heart_rate"] >= 100:
        score += 1
    if data["spo2"] <= 94:
        score += 1
    if data["respiratory_rate"] >= 22:
        score += 1
    if data["systolic_pressure"] <= 100:
        score += 1
    if data["confusion"] is True:
        score += 1

    if score == 0:
        risk = "normal"
    elif score == 1:
        risk = "faible"
    elif score == 2:
        risk = "modéré"
    else:
        risk = "élevé"

    return score, risk


def build_payload(patient):
    vitals = generate_patient_data(patient)
    score, risk = calculate_score(vitals)

    return {
        "device_id": get_device_id(),
        "patient_id": patient["patient_id"],
        "full_name": patient["full_name"],
        "age": patient["age"],
        "sex": patient["sex"],
        "address": patient["address"],
        "phone": patient["phone"],
        "emergency_contact": patient["emergency_contact"],
        "profile": patient["profile"],
        "timestamp": datetime.now().isoformat(),
        "temperature": vitals["temperature"],
        "heart_rate": vitals["heart_rate"],
        "spo2": vitals["spo2"],
        "respiratory_rate": vitals["respiratory_rate"],
        "systolic_pressure": vitals["systolic_pressure"],
        "confusion": vitals["confusion"],
        "score": score,
        "risk": risk,
    }


def send_to_cloud(payload):
    try:
        headers = {
            "X-API-KEY": API_KEY,
            "X-DEVICE-ROLE": DEVICE_ROLE
        }
        response = requests.post(CLOUD_URL, json=payload, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"[OK] {payload['patient_id']} | risque={payload['risk']} | score={payload['score']}")
            print(payload)
            print(f"[CLOUD] {response.status_code} - {response.text}\n")
        else:
            print(f"[ERREUR] Réponse Cloud inattendue ({response.status_code}) pour {payload['patient_id']}")
            save_pending_payload(payload)
    except requests.exceptions.RequestException as error:
        print(f"[ERREUR] Envoi impossible pour {payload['patient_id']} : {error}")
        save_pending_payload(payload)


def main():
    print("Démarrage du système Edge multi-patients...")
    while True:
        resend_pending_data()
        for patient in PATIENTS:
            payload = build_payload(patient)
            send_to_cloud(payload)
            time.sleep(2)
        time.sleep(5)

def get_device_id():
    return socket.gethostname()


if __name__ == "__main__":
    main()
