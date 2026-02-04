import json
import time
import threading

import paho.mqtt.client as mqtt
import folium
from flask import Flask, render_template, jsonify


BROKER = "localhost"
BROKER_PORT = 1883
TOPIC = "cam/packets"
QOS = 1

CARTE_CENTRE = [45.0531764, 7.6578783]
ZOOM_LEVEL = 17

MAX_POINTS_PER_VEHICLE = 30

vehicules = {}
vehicules_lock = threading.Lock()

couleurs_vehicules = [
    'red', 'green', 'blue', 'purple', 'orange', 'black', 'pink', 'cyan',
    'yellow', 'brown', 'gray', 'lime', 'magenta', 'navy', 'teal', 'gold',
    'silver', 'maroon', 'olive', 'coral', 'indigo', 'turquoise', 'violet',
    'chocolate', 'deepskyblue'
]

def get_vehicle_color(station_id: int) -> str:
    return couleurs_vehicules[int(station_id) % len(couleurs_vehicules)]


app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def get_vehicle_data():
    with vehicules_lock:
        return jsonify(vehicules)

@app.route("/map")
def map_view():
    return create_map_html()


def create_map_html():
    with vehicules_lock:
        snapshot = dict(vehicules)

    m = folium.Map(location=CARTE_CENTRE, zoom_start=ZOOM_LEVEL)

    for station_id, data in snapshot.items():
        couleur = data.get("color", "blue")
        trajets = data.get("positions", [])
        if not trajets:
            continue

        coords_latlon = [(p["coordinates"][1], p["coordinates"][0]) for p in trajets]

        folium.PolyLine(coords_latlon, color=couleur, weight=4, opacity=0.8).add_to(m)

        last = trajets[-1]
        folium.CircleMarker(
            location=(last["coordinates"][1], last["coordinates"][0]),
            radius=6,
            color=couleur,
            fill=True,
            fill_color=couleur,
            fill_opacity=0.9,
            popup=folium.Popup(
                f"Véhicule {station_id}<br>"
                f"Lat: {last['coordinates'][1]:.6f}<br>"
                f"Lon: {last['coordinates'][0]:.6f}<br>"
                f"Vitesse: {last['speed']:.1f} km/h",
                max_width=250
            )
        ).add_to(m)

    return m._repr_html_()


def update_position(station_id: int, lat: float, lon: float, speed: float):
    ts = int(time.time())
    with vehicules_lock:
        if station_id not in vehicules:
            vehicules[station_id] = {"color": get_vehicle_color(station_id), "positions": []}

        vehicules[station_id]["positions"].append({
            "time": ts,
            "coordinates": [float(lon), float(lat)],
            "speed": float(speed)
        })

        if len(vehicules[station_id]["positions"]) > MAX_POINTS_PER_VEHICLE:
            vehicules[station_id]["positions"] = vehicules[station_id]["positions"][-MAX_POINTS_PER_VEHICLE:]


def on_connect(client, userdata, flags, rc):
    print(f" MQTT connecté (rc={rc}) -> subscribe {TOPIC}")
    client.subscribe(TOPIC, qos=QOS)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode("utf-8", errors="replace"))
        station_id = int(data["stationId"])
        lat = float(data["latitude"])
        lon = float(data["longitude"])
        speed = float(data.get("speed", 0.0))

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return

        update_position(station_id, lat, lon, speed)
        print(f" {station_id} lat={lat:.6f} lon={lon:.6f} speed={speed:.1f}")

    except Exception as e:
        print(" Erreur:", e)


def run_flask():
    app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, BROKER_PORT, keepalive=60)
    client.loop_start()

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    print(" http://localhost:8080")
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
