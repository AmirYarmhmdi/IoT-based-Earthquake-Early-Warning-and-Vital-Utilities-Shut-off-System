
import paho.mqtt.client as mqtt
from utils.topic_fetcher import TopicFetcher
from utils.config_loader import ConfigLoader

catalog_url = "http://127.0.0.1:8081"
static_web_url = "http://127.0.0.1:8080"

# Load config
cfg = ConfigLoader()
static_web_url = cfg.catalog_url
BROKER = cfg.mqtt_host
PORT = cfg.mqtt_port
#Fetch topics.
fetcher = TopicFetcher(catalog_url)
adjust_topic = fetcher.get_adjust_topic()
warning_topic = fetcher.get_warning_topic()

TOPIC ="sensors/accelerometer/Building_A/Acc_cf09b6c1-06c6-4868-b95b-5372a4bdce4d"    #"sensors/velocity/building_A/Vel_6e3fab63-81c9-4c76-b493-2798a75fe7ca"         # "sensors/velocity/"                #"sensors/accelerometer/"    

def on_connect(client, userdata, flags, rc):
    print("Connected with result code", rc)
    client.subscribe(TOPIC)  

def on_message(client, userdata, msg):
    print(f"[{msg.topic}] {msg.payload.decode()}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()