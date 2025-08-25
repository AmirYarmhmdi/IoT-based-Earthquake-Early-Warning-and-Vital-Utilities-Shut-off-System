# water_cutoff_actuator.py
import json, time
from actuators.base_actuator import BaseActuator

class WaterCutoffActuator(BaseActuator):
    def __init__(self):
        super().__init__(actuator_type="WaterCutoff")

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        if rc == 0:
            print("[MQTT][WaterCutoff] Subscribing also to Warning topic...")
            client.subscribe(self.warning_topic)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            command = payload.get("command")

            if command in ["EARTHQUAKE", "MANUAL_SHUTOFF"]:
                self.cut_water(command)
            elif command == "REACTIVATE":
                self.reconnect_water()
            else:
                # fall back to parent behavior (adjust add/remove)
                super().on_message(client, userdata, msg)

        except Exception as e:
            return

    def cut_water(self, command):
        if command == "EARTHQUAKE":
            time.sleep(2)
            print("*** Earthquake detected -> Water shut off! ***")
        else:
            print("X Water flow is OFF (manual shutoff) X")

    def reconnect_water(self):
        print("Water cutoff DEACTIVATED! System reconnected.")
        print("~~~ Water flow is now ON ~~~")

# ------------------- Main -------------------
if __name__ == "__main__":
    actuator = WaterCutoffActuator()
    actuator.run()