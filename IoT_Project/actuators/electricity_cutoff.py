# Elec_cutoff_actuator.py
import json, time
from actuators.base_actuator import BaseActuator

class ElecCutoffActuator(BaseActuator):
    def __init__(self):
        super().__init__(actuator_type="ElectricityCutoff")

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        if rc == 0:
            print("[MQTT][ElectricityCutoff] Subscribing also to Warning topic...")
            client.subscribe(self.warning_topic)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            command = payload.get("command")

            if command in ["EARTHQUAKE", "MANUAL_SHUTOFF"]:
                self.cut_elec(command)
            elif command == "REACTIVATE":
                self.reconnect_elec()
            else:
                # fall back to parent behavior (adjust add/remove)
                super().on_message(client, userdata, msg)

        except Exception as e:
            return

    def cut_elec(self, command):
        if command == "EARTHQUAKE":
            time.sleep(2)
            print("*** Earthquake detected -> Electricity shut off! ***")
        else:
            print("X Electricity flow is OFF (manual shutoff) X")

    def reconnect_elec(self):
        print("Electricity cutoff DEACTIVATED! System reconnected.")
        print("~~~ Electricity flow is now ON ~~~")

# ------------------- Main -------------------
if __name__ == "__main__":
    actuator = ElecCutoffActuator()
    actuator.run()