
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class MessageHandler(ABC):
    """
    Abstract base class for handling MQTT messages.
    """
    @abstractmethod
    def handle_message(self, topic: str, payload: Dict[str, Any]) -> None:
        """
        Handle an incoming MQTT message.
        
        :param topic: The MQTT topic the message was received on.
        :param payload: The parsed JSON payload of the message.
        """
        pass

    @abstractmethod
    def get_subscribed_topics(self) -> List[str]:
        """
        Get a list of topics that this handler is subscribed to.

        :return: List of subscribed MQTT topics.
        """
        pass
