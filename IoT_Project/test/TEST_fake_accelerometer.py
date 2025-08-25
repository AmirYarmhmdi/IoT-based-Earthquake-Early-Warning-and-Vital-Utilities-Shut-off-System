# fake_accelerometer.py
import paho.mqtt.client as mqtt
import time
import json

from utils.config_loader import ConfigLoader
from utils.device_registrar import DeviceRegistrar
from utils.topic_fetcher import TopicFetcher
# Load config
cfg = ConfigLoader()
catalog_url = cfg.catalog_url
mqtt_host = cfg.mqtt_host
mqtt_port = cfg.mqtt_port
# Fetch warning topic
fetcher = TopicFetcher(catalog_url)
warning_topic = fetcher.get_warning_topic()

# Register controller
payload = {
    "type": "Accelerometer_Sensor",
    "building": "Virtual_Unit",
    "location": {"latitude": "fake", "longitude": "fake"}
}
registrar = DeviceRegistrar(catalog_url)
sensor_id , topic = registrar.register(payload)
mqtt_client = mqtt.Client(sensor_id)


def main():
    client = mqtt.Client()
    client.connect(mqtt_host, mqtt_port, 60)

    print(f"🚀 Fake accelerometer started, publishing to {topic}")
    while True:
        payload = {
                "bn": sensor_id,
                "e": [
                { "n": "acceleration", "u": "Gal" , "t": time.time(), "v":{"x": 5.01, "y": 5, "z": 5} }
                ]
                }
        '''
          "thresholds": {
                        "Acceleration": { "Warning": 5, "EQ_Cutoff": 15 },
                        "Velocity": { "Warning": 10, "EQ_Cutoff": 20 }
        '''
        client.publish(topic, json.dumps(payload))
        print(f"📡 Published: {payload}")
        time.sleep(.01)  

if __name__ == "__main__":
    main()
