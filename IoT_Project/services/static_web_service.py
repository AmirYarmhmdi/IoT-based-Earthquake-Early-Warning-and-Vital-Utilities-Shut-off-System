#static_web_service

import paho.mqtt.client as mqtt
import cherrypy, requests 
import json, os, time
from utils.config_loader import ConfigLoader
from utils.device_registrar import DeviceRegistrar
from utils.topic_fetcher import TopicFetcher
from utils.device_manager import DeviceManager
from utils.sensor_storage import SensorStorage

class StaticWebService:
    def __init__(self):
        self.sensor_storage = SensorStorage()
        # --- FILE PATHS ---
        self.dC_file = os.path.join("config", "Data_Catalogue.json")
        
        # --- MAIN DATA STRUCTURE ---
        if os.path.exists(self.dC_file):
            with open(self.dC_file, "r") as f:
                self.config_data = json.load(f)
        else:
            self.config_data = {
                "project": {
                    "name": "IoT-based Earthquake Early Warning and Vital Utilities Shut-off System",
                    "version": "1.0",
                    "developers": ["Amir Yarmohamadi", "Saeideh Mohammadikish", "Erfan Afshinnia"]
                },
                "topics": [],
                "thresholds": {},
                "Buildings": [],
                "System_Status": "Monitoring",
                "devices": {}
            }

        # Load config from file
        cfg = ConfigLoader()
        self.catalog_url = cfg.catalog_url
        self.static_web_url = cfg.static_web_url
        self.mqtt_host = cfg.mqtt_host
        self.mqtt_port = cfg.mqtt_port
        self.config_data["thresholds"] = cfg.thresholds_config
    
        #Fetch topics.
        fetcher = TopicFetcher(self.catalog_url)
        self.adjust_topic = fetcher.get_adjust_topic()
        self.warning_topic = fetcher.get_warning_topic()

        # Register the Static_Web_Service on the Data Catalog
        registrar = DeviceRegistrar(self.catalog_url)
        self.client_id, self.topic = registrar.register({
            "type": "Static_Web_Service",
            "building": "Central_Unit",
            "location": {"latitude": "Central_Unit", "longitude": "Central_Unit"}
        })
        # --- MQTT setup ---
        self.mqtt_client = mqtt.Client(self.client_id)
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_message = self.on_message

    # --- Save JSON files ---
    def save_json_file(self):
        self.get_devices()
        with open(self.dC_file, "w") as f:
            json.dump(self.config_data, f, indent=2)

    # --- Load device list and topics from the catalog ---  
    def get_devices(self):
        url = f"{self.catalog_url}/get_devices"
        try:
            response = requests.get(url)
            response.raise_for_status()
            devices = response.json()
            self.config_data["devices"] = devices #with all information exists in catalog for each device.

            buildings = set()
            topics = set()
            for device_id, info in devices.items():
                buildings.add(info["building"])
                topics.add(info["topic"])

            self.config_data["Buildings"] = list(buildings)
            self.config_data["topics"] = list(topics)

            print("[INFO][static_web_service] Devices and topics loaded.")
        except Exception as e:
            print(f"[ERROR][static_web_service] Failed to fetch devices: {e}")
            exit(1)

    def subscribe_all_devices(self):  
        for device_id, info in self.config_data["devices"].items():  
            device_type = info.get("type", "")  
            topic = info.get("topic", "")  
            if device_type in ["Velocity_Sensor", "Accelerometer_Sensor"]:  
                self.mqtt_client.subscribe(topic)  
                print(f"[MQTT][static_web_service] Subscribed to topic: {topic} ({device_type})")  

    # === MQTT Connection Callback ===
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT][static_web_service] Connected successfully.")
            # Subscribe to all existing devices' topics
            self.mqtt_client.subscribe(self.warning_topic)
            print(f"[MQTT][static_web_service] Subscribed to WARNING topic: {self.warning_topic}")
            self.subscribe_all_devices()  
        else:
            print(f"[MQTT][static_web_service] Connection failed with code {rc}")


    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))

            # Manage controller messages
            if "command" in payload:
                if payload["command"] == "ALARM":
                    self.config_data["System_Status"] = "ALARM"
                    self.save_json_file()
                elif payload["command"] == "EARTHQUAKE":
                    self.config_data["System_Status"] = "EARTHQUAKE"
                    self.save_json_file()
                elif payload["command"] == "Monitoring":
                    self.config_data["System_Status"] = "Monitoring"
                    self.save_json_file()
            elif "e" in payload:
                self.sensor_storage.process_message(payload)
            
        except Exception as e:
            print(f"[ERROR][static_web_service] Failed to parse MQTT message: {e}")

    # === Start MQTT client ===
    def start_mqtt(self):
        self.get_devices()
        self.save_json_file()
        self.mqtt_client.connect(self.mqtt_host, self.mqtt_port)
        self.mqtt_client.loop_start()

    #   =============================== endpoints   ==============================
    ##############################  system details ##################################    
    # GET /devices - Return all registered devices
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def devices(self):
        # Refresh device data before responding
        self.get_devices()
        return self.config_data.get("devices", {})

    # GET /sensors - Return only active acceleration/velocity sensors
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sensors(self):
        # Refresh device data before responding
        self.get_devices()
        sensors = {}
        for device_id, info in self.config_data["devices"].items():
            if info.get("type") in ["Accelerometer_Sensor", "Velocity_Sensor"]:
                sensors[device_id] = info
        return sensors
    
    # GET /sensors - Return only active actuators. (buzzer, light, cutoffs)
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def actuators(self):
        # Refresh device data before responding
        self.get_devices()
        actuators = {}
        for device_id, info in self.config_data["devices"].items():
            if info.get("type") in ["Buzzer","FlashingLight","ElectricityCutoff",
                                     "GasCutoff","WaterCutoff"]:
                actuators[device_id] = info
        return actuators
    
    # GET /devices_building?type=Accelerometer_Sensor&building=Building1
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def devices_building(self, type, building):
        # Refresh device data before responding
        self.get_devices()
        device_ids = []

        for device_id, device_info in self.config_data["devices"].items():
            if device_info.get("type") == type and device_info.get("building") == building:
                device_ids.append(device_id)

        return {"matching_devices": device_ids}

    # GET /status - Return system status
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def status(self):
        return {
            "system_status": self.config_data["System_Status"]
        }
    
    # GET / sensors' outputs - for drawing charts and tables
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_chart_data(self, sensor_id, limit=100):
        return self.sensor_storage.get_chart_data(sensor_id, limit)
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_table_data(self, sensor_id, limit=20):
        return self.sensor_storage.get_table_data(sensor_id, int(limit))
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_sensors_with_data(self):
        return self.sensor_storage.get_sensors_with_data()
    
##############################  ADD/REMOVE device ##################################
    # POST/ telegram to static_web_service -> static_web_service PUBLISH in MQTT
    # UPDATE Data_Catalogue.json & self.config_data
    # POST on cataloge to delete the client
    # MQTT Publish for the device to stop that client from operating
#####################################################################################
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()    
    def add_device(self):
        try:
            data = cherrypy.request.json
        except Exception:
            cherrypy.response.status = 400
            return {"error": "Invalid JSON"}
        manager = DeviceManager(self.mqtt_client)
        result = manager.add_device(data)
        self.save_json_file()
        self.subscribe_all_devices()
        return result

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def delete_device(self):
        # Refresh device data before responding
        self.get_devices()
        try:
            data = cherrypy.request.json
        except Exception:
            cherrypy.response.status = 400
            return {"error": "Invalid JSON"}
        '''payload = 
        {
        "type": "Accelerometer_Sensor",
        "device_id": "Acc_12345"
        }'''
        # Delete from Catalog and stop data generating in sensor
        manager = DeviceManager(self.mqtt_client)
        catalog_deleted =  manager.remove_device(data)
        self.save_json_file()

        # Step 3: Final Response
        if catalog_deleted:
            return {"result": "Device deleted from catalog"}
        else:
            return {"error": "Device not found in catalog"}

#####################  Manual shut off &  Reactivation ###############################
    # POST/ telegram to static_web_service -> static_web_service PUBLISH in MQTT
    # MQTT Publish for the device to active/stop the gas/elec./water actuators.
#####################################################################################
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def manual_shutoff(self):
        alert_msg = json.dumps({"command": "MANUAL_SHTOFF"})
        self.mqtt_client.publish(self.topic, alert_msg, qos=1)
        self.config_data["System_Status"] = "MANUAL_SHTOFF"
        print(f"[static_web_service]Shutdown sent to topic: {self.topic}")
        self.save_json_file()

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def reactivate(self):
        alert_msg = json.dumps({"command": "REACTIVATE"})
        self.mqtt_client.publish(self.topic, alert_msg, qos=1)
        print(f"[static_web_service]Earthquake alert sent to topic: {self.topic}")
        self.config_data["System_Status"] = "Monitoring"
        self.save_json_file()

# ------------------- Main -------------------
if __name__ == "__main__":
    service = StaticWebService()
    service.get_devices()
    service.start_mqtt()

    # ----------------- Start CherryPy -----------------
    conf = {'/': {'tools.sessions.on': True}}
    cherrypy.tree.mount(service, '/', conf)
    cherrypy.engine.start()

    # ----------------- Periodic device check (simple loop) -----------------
    old_devices = set(service.config_data["devices"].keys())
    try:
        while True:
            time.sleep(60)  # wait 60 seconds
            service.get_devices()
            new_devices = set(service.config_data["devices"].keys()) - old_devices
            if new_devices:
                print(f"[INFO][static_web_service] New devices detected: {new_devices}")
                service.subscribe_all_devices()
            old_devices = set(service.config_data["devices"].keys())
    except KeyboardInterrupt:
        print("[static_web_service]Exiting periodic device check.")

    cherrypy.engine.block()
