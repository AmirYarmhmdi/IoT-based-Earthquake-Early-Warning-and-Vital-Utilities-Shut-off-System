# flashing_Light.py
import json, time
from actuators.base_actuator import BaseActuator

class FlashingActuator(BaseActuator):
    def __init__(self):
        super().__init__(actuator_type="FlashingLight")

    def on_connect(self, client, userdata, flags, rc):
        super().on_connect(client, userdata, flags, rc)
        if rc == 0:
            print("[MQTT][Flashing] Subscribing also to Warning topic...")
            client.subscribe(self.warning_topic)

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            command = payload.get("command")

            if command in ["EARTHQUAKE", "ALARM"]:
                self.flashing()
            else:
                # fall back to parent behavior (adjust add/remove)
                super().on_message(client, userdata, msg)

        except Exception as e:
            return

    def flashing(self, repeats=10, delay=1):
        for _ in range(repeats):
            print("*** !FLASHING! ***")
            time.sleep(delay)

# ------------------- Main -------------------
if __name__ == "__main__":
    actuator = FlashingActuator()
    actuator.run()