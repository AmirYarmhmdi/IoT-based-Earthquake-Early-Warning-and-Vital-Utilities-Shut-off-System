# controller.py

import paho.mqtt.client as mqtt
import requests, json, time
from utils.config_loader import ConfigLoader
from utils.device_registrar import DeviceRegistrar
from utils.topic_fetcher import TopicFetcher

class Controller:
    def __init__(self):
        self.sensor_topics = []
        self.devices_info = {}
        self.state = {}

        # Load config
        cfg = ConfigLoader()
        self.catalog_url = cfg.catalog_url
        self.mqtt_host = cfg.mqtt_host
        self.mqtt_port = cfg.mqtt_port
        self.Acc_thresholds = cfg.thresholds_Acc
        self.V_thresholds = cfg.thresholds_Vel
        self.EQ_time_check = cfg.EQ_time_check # 0.3 or 300 ms

        # Fetch warning topic
        fetcher = TopicFetcher(self.catalog_url)
        self.warning_topic = fetcher.get_warning_topic()

        # Register controller
        payload = {
            "type": "Controller",
            "building": "Central_Unit",
            "location": {"latitude": "Central_Unit", "longitude": "Central_Unit"}
        }
        registrar = DeviceRegistrar(self.catalog_url)
        self.client_id, self.topic = registrar.register(payload)
        self.mqtt_client = mqtt.Client(self.client_id)

    # --- Fetch sensors ---
    def get_devices(self):
        url = f"{self.catalog_url}/get_devices"
        self.sensor_topics = []
        try:
            response = requests.get(url)
            response.raise_for_status()
            self.devices_info = response.json()
            for client_id, info in self.devices_info.items():
                dev_type = info.get("type")
                topic = info.get("topic")
                if dev_type in ["Velocity_Sensor", "Accelerometer_Sensor"]:
                    self.sensor_topics.append(topic)
        except Exception as e:
            print(f"[WARN][controller] Could not fetch devices: {e}")
            self.sensor_topics = []

    # --- MQTT setup ---
    def setup_mqtt(self):
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.loop_start()  

    def on_connect(self, client, userdata, flags, rc,properties=None):
        if rc == 0:
            print("[MQTT][controller] Connected to broker.")
            for topic in set(self.sensor_topics):
                client.subscribe(topic, qos=0)
        else:
            print(f"[ERROR][controller] MQTT connection failed. Return code: {rc}")

    # --- Subscribe to sensor topics ---
    def subscribe(self, topics):
        for topic in topics:
            self.mqtt_client.subscribe(topic, qos=0)
            print(f"[INFO][controller] Subscribed to sensor topic: {topic}")


    # --- Message callback (check the thresholds on recieved message) ---
    def on_message(self, client, userdata, msg):
        try:
            data = json.loads(msg.payload.decode('utf-8'))
            sensor_id = data.get("bn")
            timestamp = data["e"][0]["t"]
            sensor_type = data["e"][0]["n"]
            if sensor_id is None or timestamp is None:
                print("[WARN][controller] Missing sensor_topic or timestamp.")
                return

            if sensor_type == "velocity":
                values = data["e"][0]["v"]
                warning_Thr = self.V_thresholds["Warning"]
                EQCuttoff_Thr = self.V_thresholds["EQ_Cutoff"]

            elif sensor_type == "acceleration":
                values = data["e"][0]["v"]
                warning_Thr = self.Acc_thresholds["Warning"]
                EQCuttoff_Thr = self.Acc_thresholds["EQ_Cutoff"]

            else:
                print(f"[WARN][controller] Unknown data format received: {sensor_type}")
                return

            x = values.get("x", 0.0) #if no value -> 0.0
            y = values.get("y", 0.0)

            # --- State init ---
            if sensor_id not in self.state:
                self.state[sensor_id] = {}

            if sensor_type not in self.state[sensor_id]:
                self.state[sensor_id][sensor_type] = {
                    "warn_start": None,
                    "eq_start": None,
                    "alarm_sent": False,
                    "eq_sent": False
                }
            st = self.state[sensor_id][sensor_type]

            # --- Reset below threshold ---
            if x < warning_Thr and y< warning_Thr:
                self.state[sensor_id][sensor_type] ={
                    "warn_start": None, "eq_start": None,
                    "alarm_sent": False, "eq_sent": False}
                return

            # --- Above thresholds ---
            if (x >= warning_Thr or y>= warning_Thr) and st["warn_start"] is None:
                st["warn_start"] = timestamp

            if (x >= EQCuttoff_Thr or y>= EQCuttoff_Thr):
                if st["eq_start"] is None:
                    st["eq_start"] = timestamp
            else:
                st["eq_start"] = None

            # EQ check (300ms)
            if st["eq_start"] is not None and not st["eq_sent"]:
                if timestamp - st["eq_start"] >= self.EQ_time_check:
                    print(f"[EARTHQUAKE][controller] {sensor_id} ({sensor_type})")
                    self.send_EQCutoff()
                    st["eq_sent"] = True
                    st["alarm_sent"] = True

            # Warning check (300ms)
            if st["warn_start"] is not None and not st["alarm_sent"]:
                if timestamp - st["warn_start"] >= self.EQ_time_check:
                    print(f"[controller][ALARM] {sensor_id} ({sensor_type})")
                    self.send_alert()
                    st["alarm_sent"] = True

        except Exception as e:
            print(f"[ERROR][controler] Failed to process incoming message: {e}")

    def send_alert(self):
        msg = json.dumps({"command": "ALARM"})
        self.mqtt_client.publish(self.warning_topic, msg, qos=1)
        print(f"[ALERT][controller] Sent ALARM → {self.warning_topic}")

    def send_EQCutoff(self):
        msg = json.dumps({"command": "EARTHQUAKE"})
        self.mqtt_client.publish(self.warning_topic, msg, qos=1)
        print(f"[ALERT][controller] Sent EARTHQUAKE → {self.warning_topic}")

    # --- Main run loop with 30-min polling ---
    def run(self):
        self.get_devices()
        self.setup_mqtt()
        print("[INFO] Controller is now running...")

        previous_topics = set(self.sensor_topics)

        try:
            while True:
                # Wait 1 minutes
                time.sleep(60)
                self.get_devices()
                new_topics = set(self.sensor_topics)

                topics_to_unsubscribe = previous_topics - new_topics
                topics_to_subscribe = new_topics - previous_topics

                for topic in topics_to_unsubscribe:
                    self.mqtt_client.unsubscribe(topic)
                    print(f"[INFO][controller] Unsubscribed from topic: {topic}")

                for topic in topics_to_subscribe:
                    self.mqtt_client.subscribe(topic)
                    print(f"[INFO][controller] Subscribed to new topic: {topic}")

                previous_topics = new_topics

        except KeyboardInterrupt:
            print("[INFO] Controller shutting down...")
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()


if __name__ == "__main__":
    controller = Controller()
    controller.run()