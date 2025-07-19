import pytest
from unittest.mock import Mock
from typing import Dict, Any, List
import json
import time

from fp_mqtt_broker import BrokerConfig, MQTTBroker, MessageHandler
from fp_mqtt_broker.abstractions.mqtt_client import MQTTClient


class MockMQTTClient(MQTTClient):
    """Mock MQTT client for testing"""
    
    def __init__(self, client_id: str):
        self.client_id = client_id
        self.connected = False
        self.subscribed_topics = set()
        self.published_messages = []
        self.callbacks = {}
        
    def connect(self, host: str, port: int, keepalive: int) -> None:
        self.connected = True
        
    def disconnect(self) -> None:
        self.connected = False
        
    def reconnect(self) -> None:
        self.connected = True
        
    def subscribe(self, topic: str, qos: int = 0) -> None:
        self.subscribed_topics.add(topic)
        
    def publish(self, topic: str, payload: str, qos: int = 0) -> bool:
        if self.connected:
            self.published_messages.append({
                'topic': topic,
                'payload': payload,
                'qos': qos,
                'timestamp': time.time()
            })
            return True
        return False
        
    def loop_start(self) -> None:
        pass
        
    def loop_stop(self) -> None:
        pass
        
    def is_connected(self) -> bool:
        return self.connected
        
    def set_on_connect_callback(self, callback) -> None:
        self.callbacks['on_connect'] = callback
        
    def set_on_message_callback(self, callback) -> None:
        self.callbacks['on_message'] = callback
        
    def set_on_disconnect_callback(self, callback) -> None:
        self.callbacks['on_disconnect'] = callback
        
    def simulate_message(self, topic: str, payload: Dict[str, Any]):
        """Simulate receiving a message"""
        if 'on_message' in self.callbacks:
            msg_mock = Mock()
            msg_mock.topic = topic
            msg_mock.payload.decode.return_value = json.dumps(payload)
            self.callbacks['on_message'](None, None, msg_mock)
            
    def simulate_connect(self, rc: int = 0):
        """Simulate connection event"""
        if 'on_connect' in self.callbacks:
            self.callbacks['on_connect'](None, None, None, rc)
            
    def simulate_disconnect(self, rc: int = 0):
        """Simulate disconnection event"""
        if 'on_disconnect' in self.callbacks:
            self.callbacks['on_disconnect'](None, None, rc)


class TestMessageHandler(MessageHandler):
    """Test message handler implementation"""
    
    def __init__(self, topics: List[str]):
        self.topics = topics
        self.received_messages = []
        self.handle_message_calls = []
        
    def handle_message(self, topic: str, payload: Dict[str, Any]) -> None:
        self.received_messages.append({'topic': topic, 'payload': payload})
        self.handle_message_calls.append((topic, payload))
        
    def get_subscribed_topics(self) -> List[str]:
        return self.topics


@pytest.fixture
def basic_config():
    """Basic broker configuration for testing"""
    return {
        'mqtt': {
            'broker_host': 'localhost',
            'broker_port': 1883,
            'client_id': 'test_client',
            'topics': {
                'status': 'test/status',
                'data_stream': 'test/data',
                'recording_control': 'test/control'
            }
        }
    }


@pytest.fixture
def broker_config(basic_config):
    """BrokerConfig instance for testing"""
    return BrokerConfig.from_dict(basic_config)


@pytest.fixture
def mock_mqtt_client():
    """Mock MQTT client for testing"""
    return MockMQTTClient('test_client')


@pytest.fixture
def test_message_handler():
    """Test message handler"""
    return TestMessageHandler(['test/data', 'test/control'])


@pytest.fixture
def mqtt_broker(broker_config, mock_mqtt_client, test_message_handler):
    """MQTT broker instance with mocks"""
    return MQTTBroker(
        config=broker_config,
        mqtt_client=mock_mqtt_client,
        message_handlers=[test_message_handler]
    )