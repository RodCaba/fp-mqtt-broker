from typing import Dict, Any, Optional, List
from ..broker import MQTTBroker
from ..config import BrokerConfig
from ..abstractions.message_handler import MessageHandler
from ..implementations import PahoMQTTClient

class BrokerFactory:
    """Factory class for creating MQTT brokers."""
    
    @staticmethod
    def create_broker(
        config: Dict[str, Any],
        message_handlers: Optional[List[MessageHandler]] = None
        ) -> MQTTBroker:
        """
        Create an instance of an MQTT broker with the given configuration and handlers.
        :param config: Configuration dictionary for the broker
        :param message_handlers: Optional list of message handlers
        :return: An instance of MQTTBroker
        """
        broker_config = BrokerConfig.from_dict(config)
        mqtt_client = PahoMQTTClient(broker_config.client_id)
        return MQTTBroker(config=broker_config, mqtt_client=mqtt_client, message_handlers=message_handlers)

    @staticmethod
    def create_broker_with_config(
        broker_config: BrokerConfig,
        message_handlers: Optional[List[MessageHandler]] = None
    ) -> MQTTBroker:
        """
        Create an MQTT broker with a pre-defined BrokerConfig.
        
        :param broker_config: An instance of BrokerConfig
        :param message_handlers: Optional list of message handlers
        :return: An instance of MQTTBroker
        """
        mqtt_client = PahoMQTTClient(broker_config.client_id)
        return MQTTBroker(config=broker_config, mqtt_client=mqtt_client, message_handlers=message_handlers)