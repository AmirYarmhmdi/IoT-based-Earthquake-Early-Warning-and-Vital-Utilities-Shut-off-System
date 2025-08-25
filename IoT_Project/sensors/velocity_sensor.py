# velocity_sensor.py
from sensors.base_sensor import BaseSensor

class VelocitySensor(BaseSensor):
    SENSOR_TYPE = "Velocity_Sensor"
    DATA_KEY = "velocity"
    UNIT = "m/s"
    DATA_RANGE = ((0.0,5.0),(0.0,5.0),(0.0,5.0))

# ------------------- Main -------------------
if __name__ == "__main__":
    accel_sensor = VelocitySensor()
    accel_sensor.run()