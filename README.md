# 🚗 Système de Suivi des Véhicules en Temps Réel

Système de visualisation en temps réel des déplacements de véhicules utilisant les technologies **ITS-G5** (Intelligent Transport Systems - G5) et le protocole de messagerie **MQTT**.

## 📋 Description

Ce projet capture, traite et affiche de manière interactive les positions des véhicules à partir de messages CAM (Cooperative Awareness Message) extraits d'un fichier PCAP. Le système permet de visualiser sur une carte interactive les trajectoires de plusieurs véhicules avec leurs vitesses respectives.

## 🏗️ Architecture

```
PCAP (v2v-EVA-2-0.pcap)
        ↓
    Producer (Tshark + Python)
        ↓
    MQTT Broker (localhost:1883)
        ↓
    Consumer (Flask + Folium)
        ↓
    Interface Web (HTML/CSS/JS)
```

### Composants principaux :
- **Producer** (`producer.py`) : Extrait les messages CAM du fichier PCAP et les publie via MQTT
- **Consumer** (`consumer.py`) : Récupère les messages MQTT et gère le serveur web Flask
- **Interface Web** : Visualisation interactive sur carte avec mise à jour en temps réel

## 🛠️ Prérequis

- Python 3.8+
- Wireshark/Tshark installé
- Mosquitto MQTT Broker

### Installation de Tshark

**macOS :**
```bash
brew install wireshark
```

**Ubuntu/Debian :**
```bash
sudo apt-get install tshark
```

### Installation de Mosquitto

**macOS :**
```bash
brew install mosquitto
brew services start mosquitto
```

**Ubuntu/Debian :**
```bash
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

## 📦 Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/votre-username/Projet_Reseau_Vehiculaire.git
cd Projet_Reseau_Vehiculaire
```

2. Créez un environnement virtuel :
```bash
python3 -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

## 🚀 Utilisation

1. **Démarrez le broker MQTT** (si ce n'est pas déjà fait) :
```bash
mosquitto
```

2. **Lancez le consumer** (dans un premier terminal) :
```bash
python consumer.py
```

3. **Lancez le producer** (dans un second terminal) :
```bash
python producer.py
```

4. **Ouvrez votre navigateur** :
```
http://localhost:8080
```

## 🌐 Fonctionnalités

- ✅ Extraction automatique des messages CAM depuis fichier PCAP
- ✅ Communication temps réel via MQTT (QoS 1)
- ✅ Visualisation interactive sur carte (Folium)
- ✅ Suivi de jusqu'à 6 véhicules simultanés
- ✅ Historique de 30 points par véhicule
- ✅ Attribution automatique de couleurs par véhicule
- ✅ Affichage de la vitesse en temps réel
- ✅ Interface web responsive avec mise à jour automatique

## 📊 Configuration

### Producer (`producer.py`)
```python
BROKER = "localhost"
BROKER_PORT = 1883
TOPIC = "cam/packets"
SLEEP_SECONDS = 0.25          # Délai entre les messages
MAX_VEHICLES = 6              # Nombre max de véhicules
MAX_MSG_PER_VEHICLE = 30      # Points max par véhicule
```

### Consumer (`consumer.py`)
```python
BROKER = "localhost"
BROKER_PORT = 1883
TOPIC = "cam/packets"
CARTE_CENTRE = [45.0531764, 7.6578783]  # Coordonnées du centre de la carte
ZOOM_LEVEL = 17
MAX_POINTS_PER_VEHICLE = 30
```

## 📁 Structure du Projet

```
.
├── producer.py              # Module d'extraction et publication MQTT
├── consumer.py              # Module de consommation et serveur Flask
├── v2v-EVA-2-0.pcap        # Fichier PCAP contenant les messages ITS-G5
├── RAPPORT.md              # Rapport technique détaillé
├── requirements.txt        # Dépendances Python
├── templates/
│   └── index.html         # Interface web
└── static/
    └── fond.png           # Image de fond
```

## 🔧 Technologies Utilisées

- **Python 3** : Langage principal
- **Paho MQTT** : Client MQTT pour Python
- **Flask** : Framework web
- **Folium** : Bibliothèque de cartographie
- **Tshark** : Outil d'analyse de paquets réseau
- **Bootstrap 5** : Framework CSS
- **jQuery** : Bibliothèque JavaScript

## 📝 Format des Messages MQTT

```json
{
  "seq": 1,
  "ts": 1735927680.5,
  "stationId": 123456,
  "latitude": 45.0531764,
  "longitude": 7.6578783,
  "speed": 45.3
}
```

## 🐛 Dépannage

### Le producer ne trouve pas Tshark
- Vérifiez que Tshark est installé : `tshark --version`
- Ajoutez Tshark au PATH si nécessaire

### Erreur de connexion MQTT
- Vérifiez que Mosquitto est en cours d'exécution : `ps aux | grep mosquitto`
- Testez la connexion : `mosquitto_sub -t cam/packets -v`

### La carte ne s'affiche pas
- Vérifiez les logs du consumer
- Assurez-vous que le producer est lancé
- Vérifiez la console du navigateur pour les erreurs JavaScript

## 📄 Licence

MIT License - Voir le fichier [LICENSE](LICENSE) pour plus de détails

## 👥 Auteurs

Votre Nom - [Votre GitHub](https://github.com/votre-username)

## 🙏 Remerciements

- Fichier PCAP : v2v-EVA-2-0 (ITS-G5 CAM messages)
- Technologies ITS-G5 pour la communication véhicule-à-véhicule

---

⭐ Si ce projet vous est utile, n'hésitez pas à lui donner une étoile !
