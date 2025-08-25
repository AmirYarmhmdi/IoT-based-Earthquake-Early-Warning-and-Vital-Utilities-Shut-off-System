# sensor_storage.py

import json
import os
import time
import threading
import csv

class SensorStorage:
    def __init__(self):
        self.last_saved_second = {}
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_folder = os.path.join(base_dir, "..", "data")
        self.data_folder = os.path.abspath(self.data_folder)

        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

        self.lock = threading.Lock()

    def process_message(self, payload):
        sensor_id = payload["bn"]
        timestamp = payload["e"][0]["t"]
        sensor_type = payload["e"][0]["n"]
        unit = payload["e"][0]["u"]
        current_second = int(timestamp)

        if sensor_id is None:
            return

        with self.lock:
            # Save only once per second
            if self.last_saved_second.get(sensor_id) == current_second:
                return
            self.last_saved_second[sensor_id] = current_second
            
            reading = None
            if sensor_type in ["acceleration", "velocity"]:
                values = payload["e"][0]["v"]
                reading = {
                    "n": sensor_id,
                    "u": unit,
                    "t": timestamp,
                    "x": values.get("x", 0.0),
                    "y": values.get("y", 0.0),
                    "z": values.get("z", 0.0)
                }
            
            if reading:
                # --- Save to CSV file ---
                csv_filename = os.path.join(self.data_folder, f"{sensor_id}.csv")
                csv_header = ["timestamp", "name", "unit", "x", "y", "z"]
                
                write_header = not os.path.exists(csv_filename) or os.path.getsize(csv_filename) == 0
                
                with open(csv_filename, "a", newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=csv_header)
                    if write_header:
                        writer.writeheader()
                    writer.writerow({
                        "timestamp": reading["t"],
                        "name": reading["n"],
                        "unit": reading["u"],
                        "x": reading["x"],
                        "y": reading["y"],
                        "z": reading["z"]
                    })
                    
                # --- Save to JSON file ---
                json_filename = os.path.join(self.data_folder, f"{sensor_id}.json")
                data_list = []
                if os.path.exists(json_filename):
                    try:
                        with open(json_filename, "r") as f:
                            data_list = json.load(f)
                    except json.JSONDecodeError:
                        print(f"[WARNING] Corrupted JSON file found for {sensor_id}. Starting a new one.")
                        data_list = []
                
                data_list.append(reading)

                with open(json_filename, "w") as f:
                    json.dump(data_list, f, indent=2)
                
    def get_history(self, sensor_id, limit):
        json_filename = os.path.join(self.data_folder, f"{sensor_id}.json")
        if not os.path.exists(json_filename):
            return []

        try:
            with open(json_filename, "r") as f:
                data_list = json.load(f)
        except json.JSONDecodeError:
            print(f"[ERROR] The JSON file for sensor '{sensor_id}' is corrupted.")
            return []

        if limit:
            return data_list[-limit:]
        return data_list

    def get_chart_data(self, sensor_id, limit=100):
        raw_data = self.get_history(sensor_id, limit)

        if not raw_data:
            return {"error": "No data found for this sensor.", "sensor_id": sensor_id}

        sensor_type = raw_data[0].get('n')
        
        timestamps = [item['t'] for item in raw_data]
        x_values = [item['x'] for item in raw_data]
        y_values = [item['y'] for item in raw_data]

        return {
            "sensor_id": sensor_id,
            "sensor_type": sensor_type,
            "data": {
                "timestamps": timestamps,
                "x_axis": {
                    "label": f"{sensor_type.capitalize()} X",
                    "values": x_values
                },
                "y_axis": {
                    "label": f"{sensor_type.capitalize()} Y",
                    "values": y_values
                }
            }
        }

    def get_table_data(self, sensor_id, limit=100):
        """
        Returns raw sensor data formatted as a list of lists, suitable for a table view.
        """
        raw_data = self.get_history(sensor_id, limit)
        
        if not raw_data:
            return {"error": "No data found for this sensor.", "sensor_id": sensor_id}

        header = ["timestamp", "name", "unit", "x", "y", "z"]
        
        table_rows = []
        for item in raw_data:
            table_rows.append([
                item.get("t"),
                item.get("n"),
                item.get("u"),
                item.get("x"),
                item.get("y"),
                item.get("z")
            ])
            
        return {
            "sensor_id": sensor_id,
            "table_data": {
                "header": header,
                "rows": table_rows
            }
        }
    def get_sensors_with_data(self):
        # Returns a list of sensor IDs for which data files exist.
        sensors_with_data = []
        try:
            for filename in os.listdir(self.data_folder):
                if filename.endswith(".json"):
                    sensor_id = filename.replace(".json", "")
                    sensors_with_data.append(sensor_id)
        except FileNotFoundError:
            print(f"[ERROR][sensor storage] Data folder not found: {self.data_folder}")
        return sensors_with_data