# test_remove_sensors.py
import requests
from utils.config_loader import ConfigLoader

cfg = ConfigLoader()
catalog_url = cfg.catalog_url
static_web_url = cfg.static_web_url

BUILDING = "Building_A"
LOCATION = {"latitude": 45.01, "longitude": 7.61}

payload ={
        "type": "Accelerometer_Sensor",
        "device_id": "Acc_cf09b6c1-06c6-4868-b95b-5372a4bdce4d"
        }             

try:
    resp = requests.post(f"{static_web_url}/delete_device", json=payload)
    if resp.status_code == 200:
        result = resp.json()
        print(f"[SUCCESS] Device sent!.")
    else:
        print(f"[ERROR] Failed to send del: {resp.status_code} {resp.text}")
except Exception as e:
    print(f"[EXCEPTION] {e}")