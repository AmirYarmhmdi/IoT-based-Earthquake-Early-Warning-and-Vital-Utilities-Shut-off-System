# 🌐 IoT-based Earthquake Early Warning and Vital Utilities Shut-off System

This project implements an **IoT-based earthquake early warning system** that not only detects earthquakes but also **automatically shuts off critical utilities** such as electricity, gas, and water. The system is fully configurable and monitorable via the **Telegram bot** `@EEWiotbot`.

---

## Architecture Overview

The system consists of the following components:

### 1. Sensors
- Digital accelerometers (e.g., ADXL345 via I2C) and analog geophones.  
- Sensors publish data in **SenML format** to MQTT topics.

### 2. Message Broker (MQTT)
- A broker such as **HiveMQ** is used to handle communication between sensors, controller, and actuators.

### 3. Controller
- Subscribes to sensor topics.  
- Retrieves thresholds and device information from the **Data Catalog** via REST API.  
- Sends commands to alarms and actuators.

### 4. Actuators
- **Buzzer alarms** and **flashing lights**  
- **Cut-off switches** for electricity, gas, and water

### 5. Telegram Bot
- View real-time sensor data  
- Manage and register sensors and actuators  
- Check system status and reconnect after a shutdown  
- Send commands for shutdown or recovery

### 6. Static Web Service
- Stores and manages sensor data  
- Provides **REST gateways** for the Telegram bot

### 7. Utils Module
The `utils/` folder contains reusable Python modules that are imported across services and other components:

- `config_loader.py` – for configuration management  
- `device_manager.py` – for device control and management  
- `device_registrar.py` – for registering devices in the system  
- `sensor_storage.py` – for managing sensor data storage  
- `telBot_graph_table_generator.py` – for Telegram bot visualization  
- `topic_fetcher.py` – for fetching MQTT topics  

---

## Prerequisites

- Python 3.11+  
- Python libraries:
```bash
pip install -r requirements.txt
```

- Access to an MQTT broker and REST catalog

---

## Running the System

The system is designed to be run **from a single `main.py` file**. Running this file will start all services in the correct order:

```python
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
```

**Execution sequence:**  
1. `Data Catalog`  
2. `Static Web Service`  
3. Sensors: `Accelerometer` → `Velocity Sensor`  
4. `Controller`  
5. Actuators: `Buzzer Alarm` → `Flashing Light` → `Electricity/Gas/Water Cutoff`  
6. `Telegram Bot`

After running `main.py`, you can fully configure and monitor the system using the Telegram bot `@EEWiotbot`.

---

## Running Individual Modules

Each service, sensor, or actuator can also be run independently using:

```bash
python -m <folder>.<module_name>
```

**Examples:**

```bash
python -m services.Data_catalog
python -m sensors.accelerometer_sensor
python -m actuators.electricity_cutoff
python -m services.telegram_bot
```

---

## Testing

A `test/` folder is included for testing purposes. All test modules can also be run independently using:

```bash
python -m test.<module_name>
```

**Available test modules:**

- `TEST_add_devices.py` – test device registration  
- `TEST_remove_devices.py` – test device removal  
- `TEST_mqtt_sub.py` – test MQTT subscription  
- `TEST_fake_accelerometer.py` – simulate accelerometer sensor data  
- `TEST_fake_velocitymeter.py` – simulate velocity sensor data  

---
⚠️ The system has been designed to minimize hardcoding; almost all parameters are configurable through the JSON file. (conf/ -> system_config.json)
---

## Directory Structure

```
/IoT_Project
│
├──/conf/                   # # Configuration folder (system_config.json)
├── sensors/                # Accelerometer and velocity sensors
├── actuators/              # Buzzer, flashing light, and cut-off actuators
├── services/               # Data catalog, web service, controller, Telegram bot
├── utils/                  # Reusable utility modules
├── test/                   # Testing scripts
├── main.py                 # Main file to start the entire system
├── requirements.txt        # Python dependencies
└── main.py                 # the nain file that run all files in order
└── requirements.txt        # the installation requirenments
└── DiagramـofـUseـCase.jpg # the application diagram.
└── README.md

```

---

## Future Enhancements

- Integration of machine learning algorithms for earthquake detection   
- Interactive web dashboard for visualizing real-time sensor data  
