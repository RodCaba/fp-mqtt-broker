import pytest
from fp_mqtt_broker.factories.broker_factory import BrokerFactory
from fp_mqtt_broker import MQTTBroker
from tests.conftest import TestMessageHandler


@pytest.mark.unit
class TestBrokerFactory:
    """Test cases for BrokerFactory class"""
    
    def test_create_broker_with_dict_config(self, basic_config):
        """Test creating broker with dictionary configuration"""
        handler = TestMessageHandler(['test/topic'])
        
        broker = BrokerFactory.create_broker(basic_config, [handler])
        
        assert isinstance(broker, MQTTBroker)
        assert broker.config.broker_host == 'localhost'
        assert broker.config.broker_port == 1883
        assert broker.config.client_id == 'test_client'
        assert len(broker.message_handlers) == 1
        assert broker.message_handlers[0] == handler
        
    def test_create_broker_no_handlers(self, basic_config):
        """Test creating broker without message handlers"""
        broker = BrokerFactory.create_broker(basic_config)
        
        assert isinstance(broker, MQTTBroker)
        assert len(broker.message_handlers) == 0
        
    def test_create_broker_with_config_object(self, broker_config):
        """Test creating broker with BrokerConfig object"""
        handler = TestMessageHandler(['test/topic'])
        
        broker = BrokerFactory.create_broker_with_config(broker_config, [handler])
        
        assert isinstance(broker, MQTTBroker)
        assert broker.config == broker_config
        assert len(broker.message_handlers) == 1
        assert broker.message_handlers[0] == handler
        
    def test_create_broker_with_config_object_no_handlers(self, broker_config):
        """Test creating broker with BrokerConfig object and no handlers"""
        broker = BrokerFactory.create_broker_with_config(broker_config)
        
        assert isinstance(broker, MQTTBroker)
        assert broker.config == broker_config
        assert len(broker.message_handlers) == 0
        
    def test_create_broker_minimal_config(self):
        """Test creating broker with minimal configuration"""
        minimal_config = {'mqtt': {'broker_host': 'test.com'}}
        
        broker = BrokerFactory.create_broker(minimal_config)
        
        assert isinstance(broker, MQTTBroker)
        assert broker.config.broker_host == 'test.com'
        assert broker.config.broker_port == 1883  # Default
        assert broker.config.client_id == 'mqtt_client'  # Default