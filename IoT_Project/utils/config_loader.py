import json
import os

class ConfigLoader:
    def __init__(self, config_file=os.path.join("config", "system_config.json")):
        # Load config from file
        with open(config_file, "r") as f:
            config = json.load(f)

        # REST catalog URL
        rest_config = config["rest"]["catalog"]
        self.catalog_url = f"http://{rest_config['host']}:{rest_config['port']}"
        self.catalog_host = rest_config['host']
        self.catalog_port = rest_config['port']

        # REST 06_static_web_service URL
        rest_SWS_config = config["rest"]["web_service"]
        self.static_web_url = f"http://{rest_SWS_config['host']}:{rest_SWS_config['port']}"

        # MQTT broker info
        mqtt_config = config["mqtt"]["broker"]
        self.mqtt_host = mqtt_config["host"]
        self.mqtt_port = mqtt_config["port"]

        print(f"[CONFIG] Catalog URL: {self.catalog_url}")
        print(f"[CONFIG] MQTT broker: {self.mqtt_host}:{self.mqtt_port}")

        # thresholds
        self.thresholds_config = config["thresholds"]
        self.thresholds_Acc = self.thresholds_config["Acceleration"]
        self.thresholds_Vel = self.thresholds_config["Velocity"]

        # sensor interval (the time that sensors read)
        self.sensor_interval = config["sensor_interval"]

        # Earthquake time that we will check. (like if the acc is above thr. for 30 ms it will be Eq.)
        self.EQ_time_check = config["EQ_time_check"]

        # Telegram Token
        self.Token_config = config["TOKEN"]
