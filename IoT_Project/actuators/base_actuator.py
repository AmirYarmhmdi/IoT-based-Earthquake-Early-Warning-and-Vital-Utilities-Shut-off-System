# base_actuator.py
import paho.mqtt.client as mqtt
import json, time
import threading
from utils.config_loader import ConfigLoader
from utils.device_registrar import DeviceRegistrar
from utils.topic_fetcher import TopicFetcher

class BaseActuator:
    def __init__(self, actuator_type):
        self.actuator_type = actuator_type
        self.sensors = {}  # Store running sensors and threads

        # Load configuration
        cfg = ConfigLoader()
        self.catalog_url = cfg.catalog_url
        self.mqtt_host = cfg.mqtt_host
        self.mqtt_port = cfg.mqtt_port

        # Fetch topics
        fetcher = TopicFetcher(self.catalog_url)
        self.adjust_topic = fetcher.get_adjust_topic()
        self.warning_topic = fetcher.get_warning_topic()

    # MQTT connect callback
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[MQTT][baseActuator] Connected. Subscribing to Adjust topic for {self.actuator_type}...")
            client.subscribe(self.adjust_topic)
        else:
            print(f"[MQTT][baseActuator] Connection failed with code {rc}")

    # MQTT message callback
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode("utf-8"))
            action = data.get("action")

            if action == "add" and data.get("type") == self.actuator_type:
                self.add_device(data)

            elif action == "remove":
                device_id = data.get("device_id")
                self.remove_device(device_id)

        except Exception as e:
            return

    def add_device(self, data):
        """
        Register device and start its thread.
        This should be called by on_message for 'add' action.
        """
        building = data.get("building")
        location = data.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        # Register device in catalog
        registrar = DeviceRegistrar(self.catalog_url)
        device_id, topic = registrar.register(
            {"type": self.actuator_type, "building": building,
             "location": {"latitude": latitude, "longitude": longitude}},
            )

        running = {"flag": True}
        t = threading.Thread(
            target=self.run_single_device,
            args=(device_id, building, topic, running)
        )
        t.daemon = True
        self.sensors[device_id] = {"thread": t, "running": running}
        t.start()
        print(f"[INFO][baseActuator] {self.actuator_type} {device_id} started for building {building}")

    def remove_device(self, device_id):
        """
        Stop device thread and remove it from sensors dictionary.
        """
        if device_id in self.sensors:
            print(f"[INFO][baseActuator] Stopping {self.actuator_type} {device_id}")
            self.sensors[device_id]["running"]["flag"] = False
            self.sensors[device_id]["thread"].join()
            del self.sensors[device_id]

    def run_single_device(self, device_id, building, topic, running, interval=0.1):
        """
        Method to run the actuator thread.
        This should be overridden by child classes with actuator-specific behavior.
        """
        mqtt_client = mqtt.Client(device_id)
        mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        mqtt_client.loop_start()

        try:
            while running["flag"]:
                # Placeholder for actuator-specific behavior
                time.sleep(interval)
        finally:
            mqtt_client.loop_stop()
            mqtt_client.disconnect()
            print(f"[INFO][baseActuator] {self.actuator_type} {device_id} stopped.")

    def run(self):
        """
        Main loop to listen for Adjust messages.
        """
        self.mqtt_client = mqtt.Client(client_id=f"{self.actuator_type}AdjustListener")
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.loop_forever()