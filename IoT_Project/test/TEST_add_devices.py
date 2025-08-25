# TEST_add_devices.py
import requests
import time
from utils.config_loader import ConfigLoader

cfg = ConfigLoader()
catalog_url = cfg.catalog_url
static_web_url = cfg.static_web_url
mqtt_host = cfg.mqtt_host
mqtt_port = cfg.mqtt_port

BUILDING = "Building_A"
LOCATION = {"latitude": 45, "longitude": 7}

sensors_payload = [
    {
        "type": "Accelerometer_Sensor",
        "building": BUILDING,
        "location": LOCATION
    },
    {
        "type": "Accelerometer_Sensor",
        "building": BUILDING,
        "location": LOCATION
    },
    {
        "type": "Velocity_Sensor",
        "building": BUILDING,
        "location": LOCATION
    },
    {
        "type": "GasCutoff",
        "building": BUILDING,
        "location": LOCATION
    },
    {
        "type": "WaterCutoff",
        "building": BUILDING,
        "location": LOCATION
    },
    {
        "type": "ElectricityCutoff",
        "building": BUILDING,
        "location": LOCATION
    },
    {
        "type": "Buzzer",
        "building": BUILDING,
        "location": LOCATION
    },
    {
        "type": "FlashingLight",
        "building": BUILDING,
        "location": LOCATION
    },
]

for payload in sensors_payload:
    try:
        resp = requests.post(f"{static_web_url}/add_device", json=payload)
        if resp.status_code == 200:
            result = resp.json()
            device_id = result.get("device_id", payload["device_id"])
            print(f"[SUCCESS] Device {device_id} added.")
        else:
            print(f"[ERROR] Failed to add device {payload['device_id']}: {resp.status_code} {resp.text}")
        time.sleep(1)
    except Exception as e:
        print(f"[EXCEPTION] {e}")
