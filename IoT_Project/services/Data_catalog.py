import cherrypy
import json, uuid, os
from utils.config_loader import ConfigLoader

class DataCatalog(object):
    def __init__(self, config_file=os.path.join("config", "system_config.json")):
        self.devices = {}

        # Load config from JSON
        try:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    config = json.load(f)
                    print(f"Config loaded from {config_file}.")
            else:
                print(f"{config_file} not found. Using default config.")
        except (OSError, json.JSONDecodeError) as e:
            print(f"Warning: Could not read {config_file}. Using default config. ({e})")

        # Load config from file
        cfg = ConfigLoader()
        catalog_host = cfg.catalog_host
        catalog_port = cfg.catalog_port

        cherrypy.config.update({
            'server.socket_host': catalog_host,
            'server.socket_port': catalog_port
        })

        print(f"CherryPy running on http://{catalog_host}:{catalog_port}")

        # MQTT topic map
        self.topic_map = {
            "Accelerometer_Sensor": "sensors/accelerometer/",
            "Velocity_Sensor": "sensors/velocity/",
            "Buzzer": "alarms/buzzer/",
            "FlashingLight": "alarms/flashing_light/",
            "ElectricityCutoff": "cutoffs/electricity/",
            "GasCutoff": "cutoffs/gas/",
            "WaterCutoff": "cutoffs/water/",
            "Controller": "EQ_WARNING/",
            "Telegram_Bot": "Tbot/",
            "Static_Web_Service": "Adjust/"
        }

        self.device_pref = {
            "Accelerometer_Sensor": "Acc",
            "Velocity_Sensor": "Vel",
            "Buzzer": "Buz",
            "FlashingLight": "Fla",
            "ElectricityCutoff": "ElC",
            "GasCutoff": "GaC",
            "WaterCutoff": "WaC",
            "Controller": "Con",
            "Telegram_Bot": "Tel",
            "Static_Web_Service": "Web"
        }

    # ------------------- REST endpoints -------------------
    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def register_device(self):
        try:
            data = cherrypy.request.json
        except Exception:
            cherrypy.response.status = 400
            return {"error": "Invalid JSON"}

        device_type = data.get("type")
        building = data.get("building")
        location = data.get("location", {})

        if not device_type or device_type not in self.topic_map:
            cherrypy.response.status = 400
            return {"error": "Invalid or missing device type"}

        if not building or not isinstance(building, str):
            cherrypy.response.status = 400
            return {"error": "Invalid or missing building"}

        latitude = location.get("latitude")
        longitude = location.get("longitude")

        if latitude is None or longitude is None:
            cherrypy.response.status = 400
            return {"error": "Missing latitude or longitude"}

        client_id = f"{self.device_pref[device_type]}_{uuid.uuid4()}"
        base_topic = self.topic_map[device_type]
        self_building = building.replace(" ", "_")
        topic = f"{base_topic}{self_building}/{client_id}"

        self.devices[client_id] = {
            "type": device_type,
            "building": building,
            "location": {"latitude": latitude, "longitude": longitude},
            "topic": topic
        }

        return {"client_id": client_id, "topic": topic}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_warning_topic(self):
        warning_topic = self.topic_map["Controller"]        #EQ_WARNING/
        return {"W_topic": warning_topic}
    
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_adjust_topic(self):
        Adjust_topic = self.topic_map["Static_Web_Service"]     #Adjust/
        return {"Adjust_topic": Adjust_topic}

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_tbot_topic(self):
        Tbot_topic = self.topic_map["Telegram_Bot"]     #Tbot/
        return {"Tbot_topic": Tbot_topic}


    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def delete_device(self):
        input_json = cherrypy.request.json
        device_id = input_json.get("device_id")
        if device_id in self.devices:
            del self.devices[device_id]
            return {"result": "Device deleted from catalog"}
        else:
            return {"error": "Device not found"}
        
    @cherrypy.expose
    @cherrypy.tools.json_out()
    def get_devices(self):
        return self.devices

# ------------------- Main -------------------
if __name__ == '__main__':
    conf = {'/': {'tools.sessions.on': True}}
    cherrypy.tree.mount(DataCatalog(), '/', conf)
    cherrypy.engine.start()
    cherrypy.engine.block()