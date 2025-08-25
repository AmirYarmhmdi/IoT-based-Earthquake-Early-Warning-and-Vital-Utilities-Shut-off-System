# main.py
import sys
import subprocess
import time
import pathlib

ROOT = pathlib.Path(__file__).parent.resolve()

SERVICES = [
    ("Data Catalog",          "services.Data_catalog"),
    ("Static Web Service",    "services.static_web_service"),
    ("Accelerometer Sensor",  "sensors.accelerometer_sensor"),
    ("Velocity Sensor",       "sensors.velocity_sensor"),
    ("Controller",            "services.controller"),
    ("Buzzer Alarm",          "actuators.buzzer_alarm"),
    ("Flashing Light",        "actuators.flashing_Light"),
    ("Electricity Cutoff",    "actuators.electricity_cutoff"),
    ("Gas Cutoff",            "actuators.gas_cutoff"),
    ("Water Cutoff",          "actuators.water_cutoff"),
    ("Telegram Bot",          "services.telegram_bot")
]

def start_service(name, module):
    print(f"\n→ starting {name} ...")
    # Run modules with -m so imports are accurate and hassle-free
    return subprocess.Popen([sys.executable, "-m", module], cwd=ROOT)

def main():
    print("[runner] booting...")
    processes = []
    for name, module in SERVICES:
        p = start_service(name, module)
        processes.append((name, p))
        time.sleep(2)
    time.sleep(5)
    print("\n✅ All services started by main.py. Press Ctrl+C to stop.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[runner] stopping...")
        for name, p in processes:
            print(f"⛔ stopping {name} ...")
            p.terminate()
        print("[runner] all stopped.")

if __name__ == "__main__":
    main()