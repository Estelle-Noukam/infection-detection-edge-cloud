from flask import Flask, request, jsonify, render_template_string, redirect, url_for, session
import json
import os
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

EDGE_API_KEY = "raspberry-secret-key"
CLINICIAN_TOKEN = "clinician-token"
ADMIN_TOKEN = "admin-token"

ALERT_FILE = "alerts.json"

app = Flask(__name__)

app.secret_key = "change-this-secret-key"

EDGE_API_KEY = "raspberry-secret-key"

USERS = {
    "admin": {
        "password_hash": generate_password_hash("Admin123!"),
        "role": "admin"
    },
    "clinician": {
        "password_hash": generate_password_hash("Clinician123!"),
        "role": "clinician"
    }
}

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

def require_edge_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-KEY")
        role = request.headers.get("X-DEVICE-ROLE")

        if api_key != EDGE_API_KEY or role != "edge_device":
            return jsonify({"error": "unauthorized edge device"}), 401

        return f(*args, **kwargs)
    return wrapper


def require_user_token(allowed_tokens):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = request.args.get("token")
            if token not in allowed_tokens:
                return jsonify({"error": "forbidden"}), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator

def require_edge_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-KEY")
        role = request.headers.get("X-DEVICE-ROLE")

        if api_key != EDGE_API_KEY or role != "edge_device":
            return jsonify({"error": "unauthorized edge device"}), 401

        return f(*args, **kwargs)
    return wrapper


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "role" not in session:
                return redirect(url_for("login"))

            if session["role"] not in allowed_roles:
                return "Accès refusé", 403

            return f(*args, **kwargs)
        return wrapper
    return decorator

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = USERS.get(username)

        if user and check_password_hash(user["password_hash"], password):
            session["username"] = username
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            error = "Identifiants invalides"

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Connexion</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background: #f4f6f9;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
            }
            .login-box {
                background: white;
                padding: 30px;
                border-radius: 12px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                width: 350px;
            }
            h1 {
                margin-top: 0;
                color: #1f3c88;
            }
            input {
                width: 100%;
                padding: 10px;
                margin: 10px 0;
                border-radius: 6px;
                border: 1px solid #ccc;
                box-sizing: border-box;
            }
            button {
                width: 100%;
                padding: 10px;
                background: #1f3c88;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: bold;
            }
            button:hover {
                background: #163066;
            }
            .error {
                color: red;
                margin-top: 10px;
            }
            .hint {
                color: #555;
                font-size: 13px;
                margin-top: 15px;
            }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>Connexion Cloud Santé</h1>
            <form method="post">
                <input type="text" name="username" placeholder="Nom d'utilisateur" required>
                <input type="password" name="password" placeholder="Mot de passe" required>
                <button type="submit">Se connecter</button>
            </form>
            {% if error %}
                <p class="error">{{ error }}</p>
            {% endif %}
            <p class="hint">Comptes de démonstration : admin / clinician</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/data", methods=["POST"])
@require_edge_auth
def receive_data():
    data = request.get_json()
    print("\n=== Données reçues du Edge ===")
    print(data)
    save_data(data)
    # détection alerte médicale
    if data.get("risk") == "élevé":
       print("⚠️ ALERTE MÉDICALE :", data["patient_id"])
       save_alert(data)
    return jsonify({
        "message": "Données reçues avec succès",
        "patient_id": data.get("patient_id"),
        "risk": data.get("risk")
    }), 200


@app.route("/", methods=["GET"])
def home():
    return "Cloud API opérationnelle", 200


@app.route("/patients", methods=["GET"])
@login_required
@role_required("clinician", "admin")
def get_patients():
    return jsonify(get_latest_by_patient()), 200


@app.route("/alerts", methods=["GET"])
@login_required
@role_required("clinician", "admin")
def get_alerts():
    data = load_all_data()
    alerts = [entry for entry in data if entry.get("risk") in ["modéré", "élevé"]]
    return jsonify(alerts), 200


@app.route("/history/<patient_id>", methods=["GET"])
@login_required
@role_required("clinician", "admin")
def get_history(patient_id):
    data = load_all_data()
    patient_history = [entry for entry in data if entry.get("patient_id") == patient_id]
    return jsonify(patient_history), 200

@app.route("/patient/<patient_id>", methods=["GET"])
@login_required
@role_required("clinician", "admin")
def patient_view(patient_id):
    data = load_all_data()
    full_history = [entry for entry in data if entry.get("patient_id") == patient_id]

    if not full_history:
        return f"Aucune donnée pour {patient_id}", 404

    period = request.args.get("period", "20")

    if period == "all":
        patient_history = full_history
    else:
        try:
            limit = int(period)
            patient_history = full_history[-limit:]
        except ValueError:
            period = "20"
            patient_history = full_history[-20:]

    latest = patient_history[-1]

    labels = [row["timestamp"] for row in patient_history]
    temperatures = [row["temperature"] for row in patient_history]
    heart_rates = [row["heart_rate"] for row in patient_history]
    scores = [row["score"] for row in patient_history]

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Dossier patient</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 30px;
                background: #f5f7fa;
            }
            .card, .chart-box {
                background: white;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            }
            h1, h2 {
                color: #1f3c88;
            }
            p {
                margin: 6px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background: white;
            }
            th, td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
            }
            th {
                background: #1f3c88;
                color: white;
            }
            a {
                text-decoration: none;
                color: #1f3c88;
                font-weight: bold;
            }
            select, button {
                padding: 8px 12px;
                margin-top: 8px;
                margin-right: 10px;
                border-radius: 6px;
                border: 1px solid #ccc;
                font-size: 14px;
            }
            button {
                background: #1f3c88;
                color: white;
                cursor: pointer;
                border: none;
            }
        </style>
    </head>
    <body>
        <p><a href="/dashboard">← Retour au dashboard</a></p>

        <div class="card">
            <form method="get">
                <label for="period"><strong>Choisir la période d'affichage :</strong></label>
                <select name="period" id="period">
                    <option value="10" {% if period == "10" %}selected{% endif %}>10 dernières mesures</option>
                    <option value="20" {% if period == "20" %}selected{% endif %}>20 dernières mesures</option>
                    <option value="50" {% if period == "50" %}selected{% endif %}>50 dernières mesures</option>
                    <option value="all" {% if period == "all" %}selected{% endif %}>Tout l'historique</option>
                </select>
                <button type="submit">Afficher</button>
            </form>
        </div>

        <h1>Dossier patient : {{ latest.full_name }}</h1>

        <div class="card">
            <p><strong>ID :</strong> {{ latest.patient_id }}</p>
            <p><strong>Device ID :</strong> {{ latest.device_id }}</p>
            <p><strong>Âge :</strong> {{ latest.age }}</p>
            <p><strong>Sexe :</strong> {{ latest.sex }}</p>
            <p><strong>Adresse :</strong> {{ latest.address }}</p>
            <p><strong>Téléphone :</strong> {{ latest.phone }}</p>
            <p><strong>Contact d'urgence :</strong> {{ latest.emergency_contact }}</p>
            <p><strong>Profil :</strong> {{ latest.profile }}</p>
            <p><strong>Dernier risque :</strong> {{ latest.risk }}</p>
            <p><strong>Dernier score :</strong> {{ latest.score }}</p>
        </div>

        <div class="chart-box">
            <h2>Évolution de la température</h2>
            <canvas id="tempChart"></canvas>
        </div>

        <div class="chart-box">
            <h2>Évolution de la fréquence cardiaque</h2>
            <canvas id="hrChart"></canvas>
        </div>

        <div class="chart-box">
            <h2>Évolution du score</h2>
            <canvas id="scoreChart"></canvas>
        </div>

        <h2>Historique des mesures</h2>
        <table>
            <tr>
                <th>Horodatage</th>
                <th>Température</th>
                <th>FC</th>
                <th>SpO₂</th>
                <th>Respiration</th>
                <th>Pression</th>
                <th>Confusion</th>
                <th>Score</th>
                <th>Risque</th>
            </tr>
            {% for row in history %}
            <tr>
                <td>{{ row.timestamp }}</td>
                <td>{{ row.temperature }}</td>
                <td>{{ row.heart_rate }}</td>
                <td>{{ row.spo2 }}</td>
                <td>{{ row.respiratory_rate }}</td>
                <td>{{ row.systolic_pressure }}</td>
                <td>{{ row.confusion }}</td>
                <td>{{ row.score }}</td>
                <td>{{ row.risk }}</td>
            </tr>
            {% endfor %}
        </table>

        <script>
            const labels = {{ labels|tojson }};
            const temperatures = {{ temperatures|tojson }};
            const heartRates = {{ heart_rates|tojson }};
            const scores = {{ scores|tojson }};

            new Chart(document.getElementById('tempChart'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Température (°C)',
                        data: temperatures,
                        borderWidth: 2,
                        fill: false
                    }]
                }
            });

            new Chart(document.getElementById('hrChart'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Fréquence cardiaque (bpm)',
                        data: heartRates,
                        borderWidth: 2,
                        fill: false
                    }]
                }
            });

            new Chart(document.getElementById('scoreChart'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Score',
                        data: scores,
                        borderWidth: 2,
                        fill: false
                    }]
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(
        html,
        latest=latest,
        history=patient_history,
        labels=labels,
        temperatures=temperatures,
        heart_rates=heart_rates,
        scores=scores,
        period=period,
        token=request.args.get("token")
    )

@app.route("/dashboard", methods=["GET"])
@login_required
@role_required("clinician", "admin")
def dashboard():
    patients = get_latest_by_patient()
    alerts = [p for p in patients.values() if p.get("risk") in ["modéré", "élevé"]]

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Dashboard IoT Santé</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 30px;
                background: #f4f6f9;
                color: #222;
            }

            h1 {
                margin-top: 0;
                color: #1f3c88;
            }

            h2 {
                color: #1f3c88;
                margin-bottom: 10px;
            }

            .topbar {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 25px;
                flex-wrap: wrap;
                gap: 10px;
            }

            .summary {
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                margin-bottom: 25px;
            }

            .summary-box {
                background: white;
                border-radius: 12px;
                padding: 15px 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                min-width: 180px;
            }

            .alerts-section {
                background: #fff4f4;
                border-left: 8px solid #e74c3c;
                padding: 20px;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                margin-bottom: 25px;
            }

            .alerts-section ul {
                margin: 10px 0 0 20px;
                padding: 0;
            }

            .container {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
                gap: 20px;
            }

            .card {
                background: white;
                border-radius: 14px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.08);
                border-top: 6px solid #bdc3c7;
            }

            .card.normal {
                border-top-color: #2ecc71;
            }

            .card.faible {
                border-top-color: #f1c40f;
            }

            .card.modéré {
                border-top-color: #e67e22;
            }

            .card.élevé {
                border-top-color: #e74c3c;
            }

            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 10px;
                margin-bottom: 15px;
                flex-wrap: wrap;
            }

            .patient-name {
                font-size: 22px;
                font-weight: bold;
                color: #111;
                margin: 0;
            }

            .patient-id {
                color: #555;
                font-size: 14px;
                margin-top: 4px;
            }

            .badge {
                display: inline-block;
                padding: 6px 12px;
                border-radius: 999px;
                font-size: 13px;
                font-weight: bold;
                color: white;
            }

            .badge.normal {
                background: #2ecc71;
            }

            .badge.faible {
                background: #f1c40f;
                color: #222;
            }

            .badge.modéré {
                background: #e67e22;
            }

            .badge.élevé {
                background: #e74c3c;
            }

            .section-title {
                font-size: 14px;
                text-transform: uppercase;
                color: #666;
                margin-top: 18px;
                margin-bottom: 8px;
                font-weight: bold;
            }

            .info-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px 20px;
            }

            .info-grid p {
                margin: 0;
                line-height: 1.5;
            }

            .actions {
                margin-top: 18px;
            }

            .btn {
                display: inline-block;
                background: #1f3c88;
                color: white;
                text-decoration: none;
                padding: 10px 14px;
                border-radius: 8px;
                font-weight: bold;
            }

            .btn:hover {
                background: #163066;
            }

            .muted {
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="topbar">
            <div>
                <h1>Dashboard de télésurveillance IoT santé</h1>
                <p class="muted">Vue globale des patients supervisés à domicile.</p>
            </div>
            <div>
                <p class="muted">Connecté en tant que : {{ username }} ({{ role }})</p>
                <a class="btn" href="/logout">Se déconnecter</a>
            </div>
        </div>

        <div class="summary">
            <div class="summary-box">
                <strong>Patients supervisés</strong>
                <p>{{ patients|length }}</p>
            </div>
            <div class="summary-box">
                <strong>Patients en alerte</strong>
                <p>{{ alerts|length }}</p>
            </div>
        </div>

        {% if alerts %}
        <div class="alerts-section">
            <h2>⚠️ Alertes médicales en cours</h2>
            <ul>
                {% for p in alerts %}
                <li>
                    <strong>{{ p.full_name }}</strong> ({{ p.patient_id }}) —
                    risque <strong>{{ p.risk }}</strong>,
                    score {{ p.score }},
                    profil {{ p.profile }}
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}

        <div class="container">
            {% for patient_id, p in patients.items() %}
                <div class="card {{ p.risk }}">
                    <div class="card-header">
                        <div>
                            <p class="patient-name">{{ p.full_name }}</p>
                            <p class="patient-id">{{ patient_id }}</p>
                        </div>
                        <span class="badge {{ p.risk }}">{{ p.risk|upper }}</span>
                    </div>

                    <div class="section-title">Identification</div>
                    <div class="info-grid">
                        <p><strong>Device ID :</strong> {{ p.device_id }}</p>
                        <p><strong>Âge :</strong> {{ p.age }}</p>
                        <p><strong>Sexe :</strong> {{ p.sex }}</p>
                        <p><strong>Profil :</strong> {{ p.profile }}</p>
                        <p><strong>Téléphone :</strong> {{ p.phone }}</p>
                        <p><strong>Adresse :</strong> {{ p.address }}</p>
                    </div>

                    <div class="section-title">Contact d'urgence</div>
                    <p>{{ p.emergency_contact }}</p>

                    <div class="section-title">Dernières constantes vitales</div>
                    <div class="info-grid">
                        <p><strong>Température :</strong> {{ p.temperature }} °C</p>
                        <p><strong>Fréquence cardiaque :</strong> {{ p.heart_rate }} bpm</p>
                        <p><strong>SpO₂ :</strong> {{ p.spo2 }} %</p>
                        <p><strong>Respiration :</strong> {{ p.respiratory_rate }} /min</p>
                        <p><strong>Pression systolique :</strong> {{ p.systolic_pressure }} mmHg</p>
                        <p><strong>Confusion :</strong> {{ p.confusion }}</p>
                    </div>

                    <div class="section-title">Évaluation clinique</div>
                    <div class="info-grid">
                        <p><strong>Score :</strong> {{ p.score }}</p>
                        <p><strong>Horodatage :</strong> {{ p.timestamp }}</p>
                    </div>

                    <div class="actions">
                        <a class="btn" href="/patient/{{ patient_id }}">Voir le dossier complet</a>
                    </div>
                </div>
            {% endfor %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, patients=patients, alerts=alerts, username=session.get("username"), role=session.get("role"))


def save_alert(data):
    alerts = []

    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            alerts = json.load(f)

    alerts.append(data)

    with open(ALERT_FILE, "w") as f:
        json.dump(alerts, f, indent=2)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
