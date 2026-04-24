# 🏥 Système IoT Edge–Cloud pour la détection précoce d’infection

---

## 📌 1. Présentation

Ce projet implémente un système de télésurveillance médicale basé sur une architecture **IoT Edge–Cloud**.

🎯 **Objectif :** détecter précocement des anomalies physiologiques chez des patients à domicile.

Le système repose sur :

- 🔹 **Raspberry Pi (Edge)** → collecte et analyse  
- 🔹 **Serveur Flask (Cloud)** → stockage et visualisation  
- 🔹 **API REST / JSON** → communication  
- 🔹 **Dashboard Web sécurisé**  

---

## 🎯 2. Objectifs du projet

- ✔ Surveillance multi-patients  
- ✔ Détection automatique d’anomalies  
- ✔ Génération d’alertes médicales  
- ✔ Architecture Edge–Cloud  
- ✔ Interface sécurisée  

---

## 🧠 3. Architecture du système


Capteurs simulés
↓
Raspberry Pi (Edge)
↓
API REST (HTTP / JSON)
↓
Serveur Cloud (Flask)
↓
Dashboard Web


---

## ⚙️ 4. Composants

### 🔸 Edge (Raspberry Pi)

- Simulation des capteurs  
- Calcul du score de risque  
- Envoi des données  
- Buffer local en cas de panne  

---

### 🔸 Cloud (Flask)

- Réception des données  
- Stockage JSON  
- Dashboard Web  
- Gestion des alertes  
- Authentification utilisateur  

---

## 📊 5. Paramètres surveillés

- 🌡 Température  
- ❤️ Fréquence cardiaque  
- 🫁 SpO₂  
- 🌬 Fréquence respiratoire  
- 🩸 Pression artérielle  
- 🧠 Confusion  

---

## 🧮 6. Calcul du score

Le score est inspiré de **NEWS2** et **qSOFA**.

### ➤ Conditions

- Température ≥ 38°C ou ≤ 35°C → +1  
- Fréquence cardiaque ≥ 100 bpm → +1  
- SpO₂ ≤ 94 % → +1  
- Fréquence respiratoire ≥ 22/min → +1  
- Pression ≤ 100 mmHg → +1  
- Confusion → +1  

---

### ➤ Interprétation

| Score | Risque |
|------|--------|
| 0    | Normal |
| 1    | Faible |
| 2    | Modéré |
| ≥3   | Élevé  |

---

## 🔐 7. Sécurité

### 🔸 Authentification Edge

Le Raspberry Pi s’authentifie auprès du serveur Cloud en envoyant une **clé API** dans les requêtes HTTP.  
Cette clé permet de vérifier que les données proviennent bien d’un dispositif autorisé.

---

### 🔸 Authentification utilisateur

L’accès au dashboard est sécurisé grâce à :

- 🔒 Une page de connexion  
- 🔑 Des mots de passe hachés  
- 🍪 Une gestion de session avec Flask  
- 👤 Des rôles utilisateurs (admin, clinician)  


## 📁 8. Structure du projet
infection-detection-iot/
│
├── cloud/
│   └── cloud_api.py
│
├── edge/
│   └── edge_device.py
│
├── config.example.json
├── requirements.txt
├── README.md
└── .gitignore

## 🚀 9. Installation

##🔹 Cloud
cd infection-detection-iot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python cloud/cloud_api.py

##🔹 Raspberry Pi
sudo apt update
sudo apt install python3-pip python3-venv -y

python3 -m venv ~/iot-env
source ~/iot-env/bin/activate
pip install requests

python edge/edge_device.py

## 🌐 10. Configuration

Dans edge_device.py :

CLOUD_URL = "http://IP_DU_CLOUD:5000/data"

## 📈 11. Fonctionnalités
✔ Multi-patients
✔ Dashboard interactif
✔ Graphiques d’évolution
✔ Filtrage par période
✔ Alertes médicales
✔ Buffer local
✔ Resynchronisation automatique

## 🧪 12. Tests
Test Edge → Cloud
Test calcul du score
Test dashboard
Test panne Cloud
Test sécurité

## 📊 13. Résultats

Le système permet :

✔ Détection d’anomalies
✔ Surveillance en temps réel
✔ Visualisation claire
✔ Tolérance aux pannes

## ⚠️ 14. Limites
Capteurs simulés
Score simplifié
Stockage JSON
HTTP (pas HTTPS)
Pas de validation médicale

## 🔮 15. Améliorations futures
🔬 Capteurs réels
📡 MQTT
🗄 Base de données
🔐 HTTPS
🤖 Intelligence artificielle

## 📚 16. Références
NEWS2 – Royal College of Physicians
qSOFA – Sepsis-3
Flask Documentation
Raspberry Pi Documentation

18. Avertissement!!!!

Ce projet est un prototype académique. Il ne constitue pas un dispositif médical réel et ne doit pas être utilisé pour prendre des décisions cliniques.

Les données patients utilisées sont fictives et générées uniquement à des fins de démonstration.
