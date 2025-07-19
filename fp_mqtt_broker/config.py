from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BrokerConfig:
    """
    Configuration for the MQTT broker.
    """

    broker_host: str = "localhost"
    broker_port: int = 1883
    client_id: str = "mqtt_client"
    keepalive: int = 60
    topics: Optional[Dict[str, str]] = None

    @classmethod
    def from_dict(cls, config: Dict[str, any]) -> 'BrokerConfig':
        """
        Creates a BrokerConfig instance from a dictionary.
        """
        mqtt_config = config.get("mqtt", {})
        return cls(
            broker_host=mqtt_config.get("broker_host", "localhost"),
            broker_port=mqtt_config.get("broker_port", 1883),
            client_id=mqtt_config.get("client_id", "mqtt_client"),
            keepalive=mqtt_config.get("keepalive", 60),
            topics=mqtt_config.get("topics", {})
        )