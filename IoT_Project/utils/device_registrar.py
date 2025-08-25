# device_registrar.py
import requests

class DeviceRegistrar:
    def __init__(self, catalog_url):
        self.catalog_url = catalog_url

    def register(self, payload):
        """
        Registers a device (sensor/actuator/controller) in the catalog.
        payload (dict):
                        device info to register & device_type 
        Returns:
                        (client_id, topic) from catalog
        """
        try:
            response = requests.post(f"{self.catalog_url}/register_device", json=payload)
            response.raise_for_status()
            data = response.json()
            client_id = data["client_id"]
            topic = data["topic"]
            print(f"[REGISTER] registered with ID: {client_id}, Topic: {topic}")
            return client_id, topic
        except Exception as e:
            print(f"[ERROR] Failed to register: {e}")
            exit(1)