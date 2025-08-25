# topic_fetcher.py
import requests

class TopicFetcher:
    """
    Fetch topics from the catalog (REST).
    """
    def __init__(self, url):

        self.catalog_url = url
        self.adjust_topic = None
        self.warning_topic = None

    def get_adjust_topic(self):
        """
        Fetch the Adjust topic from the catalog.
        """
        try:
            response = requests.get(f"{self.catalog_url}/get_adjust_topic")
            response.raise_for_status()
            data = response.json()
            self.adjust_topic = data.get("Adjust_topic")
            print(f"[CONFIG] Adjust topic retrieved via REST: {self.adjust_topic}")
            return self.adjust_topic
        except Exception as e:
            print(f"[ERROR] Failed to fetch Adjust topic via REST: {e}")
            return None
        
    def get_warning_topic(self):
        """
        Fetch the Warning topic from the REST catalog.
        """
        try:
            response = requests.get(f"{self.catalog_url}/get_warning_topic")
            response.raise_for_status()
            data = response.json()
            self.warning_topic = data.get("W_topic")
            print(f"[CONFIG] Warning topic retrieved via REST: {self.warning_topic}")
            return self.warning_topic
        except Exception as e:
            print(f"[ERROR] Failed to fetch Warning topic via REST: {e}")
            return None
    