# 🌐 IoT-based Earthquake Early Warning and Vital Utilities Shut-off System

A **modular, scalable, and real-time** earthquake-warning platform that detects seismic activity and autonomously shuts off critical utilities (gas, electricity, water) to minimise damage and improve safety. The system integrates hybrid sensors, a controller, a Telegram bot, and a static web interface, all orchestrated through MQTT and REST micro-services.

---

## 📦 Key Features
- **Real-time seismic monitoring** with accelerometer & geophone sensors  
- **Automatic intensity classification** (low / medium / high)  
- **Audible & visual alerts** via buzzer and flashing LED  
- **Utility shut-off** for electricity, gas, and water  
- **Static web interface** for live data visualisation  
- **Telegram bot** for remote status and control  
- **MQTT + REST architecture** for loose coupling and easy scaling  
- **Approx. deployment cost:** **€250** per building

---

## 🛠 Architecture Overview

| Layer | Component | Responsibilities |
| --- | --- | --- |
| **Registry** | **Data Catalog** | Stores device IDs, MQTT topics, thresholds; exposes REST API |
| **Sensing** | *ADXL345 Accelerometer* <br> *SM-24 Geophone* | Publish ground acceleration & velocity via MQTT |
| **Messaging** | **Mosquitto Broker** | Pub/Sub hub for all sensors, controller, and services |
| **Logic** | **Controller (Raspberry Pi)** | Subscribes to data, applies thresholds, triggers alarms & actuators |
| **Actuation** | Buzzer + LED <br> Relays / Solenoids | Audible & visual alerts, automatic utility shut-off |
| **Visualisation** | **Static Web Service** | Live map of sensors & danger zones |
| **User I/O** | **Telegram Bot** | Remote commands: status, danger zone config, system reset |

---

## ⚙️ Quick-Start

> **Prerequisite:** run an MQTT broker (e.g. Mosquitto) on **`localhost:1883`**.

Start the micro-services **in order**:

```bash
# 1 – Data catalog
python data_catalog.py

# 2 – Sensors
python accelerometer_sensor.py
python velocity_sensor.py

# 3 – Static web interface
python static_web_service.py

# 4 – Alarms and Actuators (MQTT subscribers)
python buzzer_alarm.py
python flashing_Light.py
python electricity_cutoff.py
python gas_cutoff.py
python water_cutoff.py

# 5 – Controller
python controller.py

# 6 – Telegram bot
python telegram_bot.py
```

- System metadata lives in **`catalog.json`**  
- Sensor data & logs live in **`database.json`**

---

## 🔩 Hardware Bill of Materials

| Device | Qty | Purpose |
| --- | --- | --- |
| ADXL345 Accelerometer | 1 / location | 3-axis ground acceleration |
| SM-24 Geophone | 1 / location | Ground velocity |
| Raspberry Pi 4 (or local PC) | 1 | Runs broker & controller |
| Kingbright HLMP-K150 LED | 1 / alarm | Visual alert |
| Adafruit Piezo Buzzer | 1 / alarm | Audible alert |
| Songle SRD-05VDC-SL-C Relay | 1 | Electricity shut-off |
| Asco RedHat 8210G Solenoid | 1 | Gas shut-off |
| Rain Bird 100-DV Valve | 1 | Water shut-off |
| 5 V 3 A PSU | as needed | Power for sensors & actuators |

---

## 📈 Scalability & Cost
- Designed for **single-building** or **neighbourhood** deployment  
- Base hardware pack ≈ **€250** per building  
- Add sensors / actuators with minimal configuration via Data Catalog

---

## 👥 Authors
- **Amir Yarmohamadi** — *S329783*  
- **Saeideh Mohammadikish** — *S329781*  
- **Erfan Afshinnia** — *S329945*

---

## 🏛 Domains
Smart Cities • Civil Protection • Earthquake Engineering • Internet of Things

---
