from flask import Flask, request, jsonify, render_template_string
import json
import os

app = Flask(__name__)

DATA_FILE = "patients_data.json"


def save_data(data):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        f.write("\n")


def load_all_data():
    if not os.path.exists(DATA_FILE):
        return []

    records = []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def get_latest_by_patient():
    data = load_all_data()
    latest = {}
    for entry in data:
        latest[entry["patient_id"]] = entry
    return latest


@app.route("/data", methods=["POST"])
def receive_data():
    data = request.get_json()
    print("\n=== Données reçues du Edge ===")
    print(data)
    save_data(data)
    return jsonify({
        "message": "Données reçues avec succès",
        "patient_id": data.get("patient_id"),
        "risk": data.get("risk")
    }), 200


@app.route("/", methods=["GET"])
def home():
    return "Cloud API opérationnelle", 200


@app.route("/patients", methods=["GET"])
def get_patients():
    return jsonify(get_latest_by_patient()), 200


@app.route("/alerts", methods=["GET"])
def get_alerts():
    data = load_all_data()
    alerts = [entry for entry in data if entry.get("risk") in ["modéré", "élevé"]]
    return jsonify(alerts), 200


@app.route("/dashboard", methods=["GET"])
def dashboard():
    patients = get_latest_by_patient()

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard IoT Santé</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 30px;
                background: #f5f7fa;
            }
            h1 {
                color: #1f3c88;
            }
            .container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }
            .card {
                background: white;
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            }
            .normal {
                border-left: 8px solid #2ecc71;
            }
            .faible {
                border-left: 8px solid #f1c40f;
            }
            .modéré {
                border-left: 8px solid #e67e22;
            }
            .élevé {
                border-left: 8px solid #e74c3c;
            }
            p {
                margin: 6px 0;
            }
            .risk {
                font-weight: bold;
                font-size: 18px;
            }
        </style>
    </head>
    <body>
        <h1>Dashboard de télésurveillance IoT santé</h1>
        <p>Dernier état connu de chaque patient.</p>
        <div class="container">
            {% for patient_id, p in patients.items() %}
                <div class="card {{ p.risk }}">
                    <h2>{{ patient_id }}</h2>
                    <p><strong>Profil :</strong> {{ p.profile }}</p>
                    <p><strong>Horodatage :</strong> {{ p.timestamp }}</p>
                    <p><strong>Température :</strong> {{ p.temperature }} °C</p>
                    <p><strong>Fréquence cardiaque :</strong> {{ p.heart_rate }} bpm</p>
                    <p><strong>SpO₂ :</strong> {{ p.spo2 }} %</p>
                    <p><strong>Fréquence respiratoire :</strong> {{ p.respiratory_rate }} /min</p>
                    <p><strong>Pression systolique :</strong> {{ p.systolic_pressure }} mmHg</p>
                    <p><strong>Confusion :</strong> {{ p.confusion }}</p>
                    <p><strong>Score :</strong> {{ p.score }}</p>
                    <p class="risk"><strong>Risque :</strong> {{ p.risk }}</p>
                </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, patients=patients)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
