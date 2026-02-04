import json
import os
import time
import subprocess
import re

import paho.mqtt.client as mqtt

BROKER = "localhost"
BROKER_PORT = 1883
TOPIC = "cam/packets"
QOS = 1

PCAP_FILE = "v2v-EVA-2-0.pcap"

SLEEP_SECONDS = 0.25          # plus lent = plus lisible
MAX_VEHICLES = 6              # max 6 véhicules
MAX_MSG_PER_VEHICLE = 30      # max 30 points par véhicule


def _find_all(obj, predicate, path=""):
    results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}" if path else str(k)
            if predicate(k):
                results.append((new_path, v))
            results.extend(_find_all(v, predicate, new_path))
    elif isinstance(obj, list):
        for i, it in enumerate(obj):
            new_path = f"{path}[{i}]"
            results.extend(_find_all(it, predicate, new_path))
    return results


def _to_int(x):
    if x is None:
        return None
    if isinstance(x, list) and x:
        x = x[0]
    if isinstance(x, (int, float)):
        return int(x)
    if isinstance(x, str):
        m = re.search(r"\((\-?\d+)\)", x)
        if m:
            return int(m.group(1))
        m2 = re.search(r"\-?\d+", x.replace(",", ""))
        if m2:
            return int(m2.group(0))
    return None


def extract_cam_from_tshark_json(pcap_path):
    out = subprocess.check_output(["tshark", "-r", pcap_path, "-T", "json"], text=True)
    data = json.loads(out)

    cam_list = []

    for entry in data:
        layers = entry.get("_source", {}).get("layers", {})

        station_candidates = _find_all(layers, lambda k: "stationid" in str(k).lower())
        station_id = None
        for _, v in station_candidates:
            station_id = _to_int(v)
            if station_id is not None:
                break
        if station_id is None:
            continue

        lat_candidates = _find_all(layers, lambda k: str(k).lower().endswith("latitude"))
        lon_candidates = _find_all(layers, lambda k: str(k).lower().endswith("longitude"))

        lat_ref = [(_p, _to_int(_v)) for (_p, _v) in lat_candidates if "referenceposition" in _p.lower()]
        lon_ref = [(_p, _to_int(_v)) for (_p, _v) in lon_candidates if "referenceposition" in _p.lower()]

        lat_raw = lat_ref[0][1] if lat_ref else (_to_int(lat_candidates[0][1]) if lat_candidates else None)
        lon_raw = lon_ref[0][1] if lon_ref else (_to_int(lon_candidates[0][1]) if lon_candidates else None)

        if lat_raw is None or lon_raw is None:
            continue

        lat = lat_raw / 10**7
        lon = lon_raw / 10**7

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            continue

        speed_candidates = _find_all(layers, lambda k: "speedvalue" in str(k).lower())
        speed_raw = None
        for _, v in speed_candidates:
            speed_raw = v
            break

        speed_kmh = 0.0
        sr = _to_int(speed_raw)
        if sr is not None:
            speed_kmh = (sr / 100.0) * 3.6

        cam_list.append({
            "stationId": int(station_id),
            "latitude": float(lat),
            "longitude": float(lon),
            "speed": float(speed_kmh),
            "lat_raw": int(lat_raw),
            "lon_raw": int(lon_raw),
        })

    return cam_list


def main():
    if not os.path.exists(PCAP_FILE):
        print(f" PCAP introuvable: {PCAP_FILE}")
        return

    print(" Extraction CAM depuis le PCAP (tshark -T json)...")
    cam_msgs = extract_cam_from_tshark_json(PCAP_FILE)
    print(f"CAM extraits: {len(cam_msgs)}")

    client = mqtt.Client()
    client.connect(BROKER, BROKER_PORT, keepalive=60)
    client.loop_start()

    allowed_ids = []
    per_vehicle = {}
    sent = 0

    for i, cam in enumerate(cam_msgs, start=1):
        sid = cam["stationId"]

        # sélectionner MAX_VEHICLES ids max
        if sid not in allowed_ids:
            if len(allowed_ids) >= MAX_VEHICLES:
                continue
            allowed_ids.append(sid)
            print(f"🚗 Véhicule ajouté: {sid}")

        per_vehicle.setdefault(sid, 0)
        if per_vehicle[sid] >= MAX_MSG_PER_VEHICLE:
            continue
        per_vehicle[sid] += 1

        # Afficher 3 preuves brutes (cam réel)
        if sent < 3:
            print(f"PREUVE: sid={sid} lat_raw={cam['lat_raw']} lon_raw={cam['lon_raw']} -> lat={cam['latitude']} lon={cam['longitude']}")

        payload = {
            "seq": i,
            "ts": time.time(),
            "stationId": sid,
            "latitude": cam["latitude"],
            "longitude": cam["longitude"],
            "speed": cam["speed"]
        }

        client.publish(TOPIC, json.dumps(payload), qos=QOS, retain=False)
        sent += 1

        time.sleep(SLEEP_SECONDS)

    client.loop_stop()
    client.disconnect()

    print(f"Envoyés: {sent} | Véhicules: {allowed_ids}")


if __name__ == "__main__":
    main()
