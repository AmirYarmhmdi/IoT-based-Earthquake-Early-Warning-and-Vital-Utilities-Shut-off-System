# device_manager.py
import requests
import json
from utils.config_loader import ConfigLoader
from utils.topic_fetcher import TopicFetcher

class DeviceManager:
    def __init__(self, mqtt_client):
        self.all_devices = ["Accelerometer_Sensor", "Velocity_Sensor", "Buzzer",
                            "FlashingLight","ElectricityCutoff", "GasCutoff",
                            "WaterCutoff"]
        self.mqtt_client = mqtt_client
        
        # Load config from file
        cfg = ConfigLoader()
        self.catalog_url = cfg.catalog_url
        self.mqtt_host = cfg.mqtt_host
        self.mqtt_port = cfg.mqtt_port


        #Fetch topics.
        fetcher = TopicFetcher(self.catalog_url)
        self.adjust_topic = fetcher.get_adjust_topic()

    def add_device(self, data: dict):
        """ publishes MQTT message to add new device. """
        data["action"] = "add"
        device_type = data.get("type")
        building = data.get("building")
        location = data.get("location", {})

        # Validation
        if not device_type or device_type not in self.all_devices:
            return {"error": "Invalid or missing device type"}
        if not building or not isinstance(building, str):
            return {"error": "Invalid or missing building"}
        if location.get("latitude") is None or location.get("longitude") is None:
            return {"error": "Missing latitude or longitude"}

        try:
            payload = json.dumps(data)
            self.mqtt_client.publish(self.adjust_topic, payload, qos=1)
        except Exception as e:
            return {"error": f"Failed to publish MQTT message: {str(e)}"}

        return {
            "message": f"One {device_type} adjustment message sent!",
            "MQTT topic": self.adjust_topic,
            "payload": data
        }


    def remove_device(self, data: dict):
        data["action"] = "remove"
        device_id = data.get("device_id")
        try:
            payload = json.dumps(data)
            self.mqtt_client.publish(self.adjust_topic, payload, qos=1)
        except Exception as e:
            return {"error": f"Failed to publish MQTT message: {str(e)}"}

        try:
            response = requests.post(f"{self.catalog_url}/delete_device", json={"device_id": device_id})
            if response.status_code == 200:
                catalog_deleted = True
            else:
                catalog_deleted = False
        except Exception as e:
            catalog_deleted = False

        return catalog_deleted