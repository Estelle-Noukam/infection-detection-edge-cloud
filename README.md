# Système IoT Edge–Cloud pour la détection précoce d’infection à domicile

## 1. Présentation du projet

Ce projet implémente un prototype de télésurveillance médicale basé sur une architecture **IoT Edge–Cloud**.  
L’objectif est de détecter précocement des anomalies physiologiques compatibles avec un risque infectieux chez des patients suivis à domicile.

Le système repose sur :

- un **Raspberry Pi 4B** jouant le rôle de dispositif Edge ;
- un serveur **Cloud Flask** exécuté sur Kali Linux ;
- une communication **REST API / JSON** ;
- un dashboard Web sécurisé pour la supervision des patients.

Le Raspberry Pi simule plusieurs capteurs médicaux, calcule un score de risque localement, puis envoie les données vers le Cloud. Le Cloud reçoit les données, les stocke, affiche les patients dans un dashboard, génère des alertes et permet la consultation détaillée de chaque dossier patient.

---

## 2. Fonctionnalités principales

Le projet inclut :

- surveillance de plusieurs patients ;
- simulation de constantes vitales ;
- calcul automatique d’un score de risque ;
- dashboard Web de supervision ;
- dossier détaillé par patient ;
- graphiques d’évolution ;
- filtre par période d’observation ;
- génération d’alertes médicales ;
- buffer local Edge en cas de panne Cloud ;
- resynchronisation automatique après reprise du Cloud ;
- identification du dispositif Edge avec `device_id` ;
- authentification machine du Raspberry Pi par clé API ;
- authentification utilisateur avec login, mot de passe haché et session Flask.

---

## 3. Architecture du système

```text
Patients simulés
      |
      v
Capteurs simulés
(température, fréquence cardiaque, SpO₂,
respiration, pression systolique, confusion)
      |
      v
Raspberry Pi — Edge Device
      |
      |-- Simulation des données physiologiques
      |-- Calcul local du score de risque
      |-- Ajout du device_id
      |-- Buffer local si Cloud indisponible
      |
      v
Transmission HTTP REST / JSON
      |
      v
Cloud Flask sur Kali Linux
      |
      |-- Authentification du Raspberry Pi
      |-- Réception des données
      |-- Stockage JSON
      |-- Dashboard sécurisé
      |-- Alertes médicales
      |-- Vue globale et vue par patient

4. Paramètres physiologiques surveillés

Le système surveille les paramètres suivants :

Paramètre	Rôle
Température	Détection de fièvre ou hypothermie
Fréquence cardiaque	Détection de tachycardie
SpO₂	Surveillance de l’oxygénation
Fréquence respiratoire	Détection d’une respiration anormale
Pression systolique	Détection d’une hypotension
Confusion	Indicateur de dégradation neurologique

5. Méthode de calcul du score

Le score est inspiré de méthodes médicales comme NEWS2 et qSOFA, mais adapté de manière simplifiée pour ce prototype.

Chaque anomalie ajoute un point :

Condition	Score
Température ≥ 38 °C ou ≤ 35 °C	+1
Fréquence cardiaque ≥ 100 bpm	+1
SpO₂ ≤ 94 %	+1
Fréquence respiratoire ≥ 22/min	+1
Pression systolique ≤ 100 mmHg	+1
Confusion = True	+1

Interprétation :

Score	Niveau de risque
0	normal
1	faible
2	modéré
≥ 3	élevé

6. Structure du projet
infection-detection-iot/
│
├── cloud/
│   └── cloud_api.py
│
├── edge/
│   └── edge_device.py
│
├── sensors/
│
├── config.example.json
├── requirements.txt
├── README.md
└── .gitignore

7. Installation côté Cloud

Sur la machine Cloud, par exemple Kali Linux :

cd ~/infection-detection-iot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Lancer le serveur Cloud :

python cloud/cloud_api.py

Le serveur doit être accessible sur :

http://IP_DU_CLOUD:5000/login

Exemple :

http://192.168.2.35:5000/login

8. Installation côté Raspberry Pi

Sur le Raspberry Pi :

sudo apt update
sudo apt install python3-pip python3-venv -y

Créer l’environnement virtuel :

python3 -m venv ~/iot-env
source ~/iot-env/bin/activate
pip install requests

Lancer le module Edge :

cd ~/infection-detection-iot
source ~/iot-env/bin/activate
python edge/edge_device.py

9. Configuration réseau

Le Raspberry Pi et la machine Cloud doivent être sur le même réseau.

Pour vérifier l’adresse IP de la machine Cloud :

ip a

ou :

hostname -I

Dans edge/edge_device.py, la variable CLOUD_URL doit pointer vers le serveur Cloud :

CLOUD_URL = "http://IP_DU_CLOUD:5000/data"

Exemple :

CLOUD_URL = "http://192.168.2.35:5000/data"

10. Authentification et sécurité

Le projet utilise deux niveaux de sécurité.

10.1 Authentification du Raspberry Pi

Le Raspberry Pi envoie une clé API au Cloud via les headers HTTP :

headers = {
    "X-API-KEY": API_KEY,
    "X-DEVICE-ROLE": DEVICE_ROLE
}

Cela permet au Cloud de refuser les données venant d’un dispositif non autorisé.

10.2 Authentification utilisateur

Le dashboard Cloud est protégé par une page de connexion.

Comptes de démonstration :

Utilisateur : clinician
Mot de passe : Clinician123!
Utilisateur : admin
Mot de passe : Admin123!

Les mots de passe sont hachés côté application avec Werkzeug.

11. Dashboard

Le dashboard permet de visualiser :

la liste des patients ;
leur état physiologique courant ;
leur score de risque ;
les alertes ;
le device_id ;
les informations du patient ;
un lien vers le dossier complet.

Accès :

http://IP_DU_CLOUD:5000/login

Après connexion :

/dashboard
12. Dossier patient

Chaque patient dispose d’une page détaillée accessible depuis le dashboard.

Cette page affiche :

les informations d’identification fictives ;
les dernières constantes vitales ;
le score ;
le niveau de risque ;
l’historique des mesures ;
les graphiques d’évolution.

Exemple :

/patient/patient_001
13. Buffer local Edge

Le Raspberry Pi dispose d’un mécanisme de résilience.

Si le Cloud est indisponible :

l’envoi échoue ;
les données sont stockées localement ;
le fichier pending_data.json conserve les données ;
lorsque le Cloud revient, les données sont retransmises automatiquement.

Cela permet d’éviter une perte de données en cas de panne réseau ou d’arrêt temporaire du Cloud.

14. Tests réalisés

Les tests effectués incluent :

Test de communication

Vérification de l’envoi des données du Raspberry Pi vers Flask.

Test du score

Validation du calcul du score selon les constantes générées.

Test du dashboard

Vérification de l’affichage global, des dossiers patients et des graphiques.

Test de panne Cloud

Arrêt volontaire du Cloud pour valider le stockage local puis la resynchronisation.

Test de sécurité

Vérification que le dashboard n’est pas accessible sans authentification.

15. Commandes utiles pour la démonstration

Démarrer le Cloud
cd ~/infection-detection-iot
source venv/bin/activate
python cloud/cloud_api.py

Démarrer le Raspberry Pi Edge
cd ~/infection-detection-iot
source ~/iot-env/bin/activate
python edge/edge_device.py
Vérifier l’adresse IP
ip a

ou :

hostname -I
Tester la communication

Depuis le Raspberry Pi :

ping IP_DU_CLOUD
Vérifier le buffer local
cat edge/pending_data.json
16. Limites du prototype

Le projet reste un prototype académique. Ses principales limites sont :

les capteurs sont simulés ;
le score médical est simplifié ;
le stockage JSON n’est pas adapté à une production ;
la communication utilise HTTP et non HTTPS ;
la sécurité est pédagogique, mais pas complète pour un environnement médical réel ;
le système n’a pas été validé cliniquement.
17. Perspectives d’amélioration

Les améliorations possibles sont :

intégration de vrais capteurs médicaux ;
utilisation de MQTT ;
migration vers une base de données ;
ajout de notifications SMS ou email ;
déploiement Cloud réel ;
ajout de HTTPS ;
gestion IAM avancée ;
journalisation des accès ;
intégration d’intelligence artificielle ;
prédiction du risque d’infection.

18. Avertissement!!!!

Ce projet est un prototype académique. Il ne constitue pas un dispositif médical réel et ne doit pas être utilisé pour prendre des décisions cliniques.

Les données patients utilisées sont fictives et générées uniquement à des fins de démonstration.
