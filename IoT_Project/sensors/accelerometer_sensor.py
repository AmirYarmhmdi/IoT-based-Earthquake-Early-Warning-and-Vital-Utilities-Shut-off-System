# accelerometer_sensor.py
from sensors.base_sensor import BaseSensor

class AccelerometerSensor(BaseSensor):
    SENSOR_TYPE = "Accelerometer_Sensor"
    DATA_KEY = "acceleration"
    UNIT = "Gal"
    DATA_RANGE = ((0.0, 1.0),(0.0,1.0),(0.0,1.0)) # Gal = 0.01 m/s2

# ------------------- Main -------------------
if __name__ == "__main__":
    accel_sensor = AccelerometerSensor()
    accel_sensor.run()