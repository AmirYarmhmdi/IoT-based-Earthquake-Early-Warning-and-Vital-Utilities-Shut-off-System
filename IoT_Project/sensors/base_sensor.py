# base_sensor.py
import paho.mqtt.client as mqtt
import threading
import json
import time
import random
from utils.config_loader import ConfigLoader
from utils.device_registrar import DeviceRegistrar
from utils.topic_fetcher import TopicFetcher

'''
Sensors publishe their reading on SenML Dataformat (Sensor Markup Language):
payload = {
"bn": "client_id",
"e": [{ "n": "self.DATA_KEY", "u": "Gal", "t": time.time(), "v":{"x": x, "y": y, "z": z} }]
}
'''


class BaseSensor:
    SENSOR_TYPE = "BaseSensor"  # overridden in child class
    DATA_KEY = "data"           # key in mqtt message, for accelerometer: "acceleration", velocity: "velocity"
    UNIT = "unit"               # overridden in child class
    DATA_RANGE = ((0,1),(0,1),(0,1)) # x, y, z range

    def __init__(self):
        self.sensors = {}

        # Load config
        cfg = ConfigLoader()
        self.catalog_url = cfg.catalog_url
        self.mqtt_host = cfg.mqtt_host
        self.mqtt_port = cfg.mqtt_port
        self.sensor_interval = float(cfg.sensor_interval)

        # Fetch Adjust topic
        fetcher = TopicFetcher(self.catalog_url)
        self.adjust_topic = fetcher.get_adjust_topic()

    # MQTT callbacks
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT][baseSensor] Connected. Subscribing to Adjust topic for {self.SENSOR_TYPE}...")
            client.subscribe(self.adjust_topic)
        else:
            print(f"[MQTT][baseSensor] Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            action = data.get("action")

            if action == "add" and data.get("type") == self.SENSOR_TYPE:
                building = data.get("building")
                location = data.get("location", {})
                latitude = location.get("latitude")
                longitude = location.get("longitude")

                registrar = DeviceRegistrar(self.catalog_url)
                client_id, topic = registrar.register(
                    {"type": self.SENSOR_TYPE, "building": building,
                     "location": {"latitude": latitude, "longitude": longitude}}
                )

                running = {"flag": True} #is used for the time that the operator orders to stop that sensor!
                '''
                we need to use multiple sensors at the same time.
                so this code should read some lines not in its' usual order!
                We esued threating to run some parts of the code in a simultaniously!
                '''
                t = threading.Thread(               # the representative of that sensor in our code!
                    target=self.run_single_sensor,
                    args=(client_id, topic, running, self.sensor_interval)
                )
                t.daemon = True
                self.sensors[client_id] = {"thread": t, "running": running}
                t.start()
                print(f"[INFO][baseSensor] {self.SENSOR_TYPE}|{client_id} started for building {building}")

            elif action == "remove" and data.get("type") == self.SENSOR_TYPE:
                device_id = data.get("device_id")
                if device_id in self.sensors:
                    print(f"[INFO][baseSensor] Stopping sensor: {device_id}")
                    self.sensors[device_id]["running"]["flag"] = False  # This will cause the while running["flag"]: inside run_single_sensor to become false and exit the sensor loop.
                    self.sensors[device_id]["thread"].join()       # The main program says: "I'll wait until that thread actually terminates and all its resources are freed." :)
                    del self.sensors[device_id] #And Goodby sensor_id! :)
                else:
                    print(f"[INFO][baseSensor] Sensor with device_id {device_id} not found.")

        except Exception as e:
            print(f"[ERROR][baseSensor] Failed to process Adjust message: {e}")

    # Run a single sensor
    def run_single_sensor(self, client_id, topic, running, interval):
        mqtt_client = mqtt.Client(client_id)
        mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        mqtt_client.loop_start()

        try:
            while running["flag"]:
                x = round(random.uniform(*self.DATA_RANGE[0]), 3) #ex. random.uniform(0,1,3) -> 0.342
                y = round(random.uniform(*self.DATA_RANGE[1]), 3)
                z = round(random.uniform(*self.DATA_RANGE[2]), 3)
                reading = {
                "bn": client_id,
                "e": [
                { "n": self.DATA_KEY, "u": self.UNIT, "t": time.time(), "v":{"x": x, "y": y, "z": z} }
                ]
                }
                mqtt_client.publish(topic, json.dumps(reading), qos=0)
                time.sleep(interval)
        finally:    #A command that should always be executed, whether the program ends normally or not.
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            print(f"[INFO][baseSensor] {self.SENSOR_TYPE} {client_id} stopped.")

    # Main run loop
    def run(self):
        self.mqtt_client = mqtt.Client(client_id=f"{self.SENSOR_TYPE}/AdjustListener")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.loop_forever()