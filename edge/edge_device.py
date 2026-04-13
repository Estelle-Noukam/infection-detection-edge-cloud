import random
import time
from datetime import datetime
import requests

CLOUD_URL = "http://192.168.2.35:5000/data"
PATIENT_ID = "patient_001"


def generate_temperature(infection=False):
    if infection:
        return round(random.uniform(38.0, 39.5), 1)
    return round(random.uniform(36.5, 37.4), 1)


def generate_heart_rate(infection=False):
    if infection:
        return random.randint(95, 120)
    return random.randint(65, 90)


def infection_score(temperature, heart_rate):
    score = 0

    if temperature >= 38.0:
        score += 1
    if heart_rate >= 100:
        score += 1

    if score == 0:
        risk = "faible"
    elif score == 1:
        risk = "modéré"
    else:
        risk = "élevé"

    return score, risk


def build_payload(infection=False):
    temperature = generate_temperature(infection)
    heart_rate = generate_heart_rate(infection)
    score, risk = infection_score(temperature, heart_rate)

    payload = {
        "patient_id": PATIENT_ID,
        "timestamp": datetime.now().isoformat(),
        "temperature": temperature,
        "heart_rate": heart_rate,
        "score": score,
        "risk": risk,
    }
    return payload


def send_to_cloud(payload):
    try:
        response = requests.post(CLOUD_URL, json=payload, timeout=5)
        print(f"[OK] Données envoyées : {payload}")
        print(f"[OK] Réponse Cloud : {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as error:
        print(f"[ERREUR] Impossible d'envoyer les données au Cloud : {error}")


def main():
    print("Démarrage du dispositif Edge...")
    while True:
        infection = random.choice([False, False, True])
        payload = build_payload(infection)
        send_to_cloud(payload)
        time.sleep(10)


if __name__ == "__main__":
    main()
