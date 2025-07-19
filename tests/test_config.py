import pytest
from fp_mqtt_broker.config import BrokerConfig

@pytest.mark.unit
class TestBrokerConfig:
    """Test cases for BrokerConfig class"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = BrokerConfig()
        
        assert config.broker_host == "localhost"
        assert config.broker_port == 1883
        assert config.client_id == "mqtt_client"
        assert config.keepalive == 60
        assert config.topics is None
        
    def test_custom_configuration(self):
        """Test custom configuration values"""
        topics = {'status': 'app/status', 'data': 'app/data'}
        config = BrokerConfig(
            broker_host="192.168.1.100",
            broker_port=1884,
            client_id="custom_client",
            keepalive=30,
            topics=topics
        )
        
        assert config.broker_host == "192.168.1.100"
        assert config.broker_port == 1884
        assert config.client_id == "custom_client"
        assert config.keepalive == 30
        assert config.topics == topics
        
    def test_from_dict_complete_config(self):
        """Test creating config from complete dictionary"""
        config_dict = {
            'mqtt': {
                'broker_host': 'test.broker.com',
                'broker_port': 1885,
                'client_id': 'dict_client',
                'keepalive': 45,
                'topics': {
                    'status': 'test/status',
                    'data': 'test/data'
                }
            }
        }
        
        config = BrokerConfig.from_dict(config_dict)
        
        assert config.broker_host == 'test.broker.com'
        assert config.broker_port == 1885
        assert config.client_id == 'dict_client'
        assert config.keepalive == 45
        assert config.topics['status'] == 'test/status'
        assert config.topics['data'] == 'test/data'
        
    def test_from_dict_partial_config(self):
        """Test creating config from partial dictionary"""
        config_dict = {
            'mqtt': {
                'broker_host': 'partial.broker.com',
                'topics': {'status': 'partial/status'}
            }
        }
        
        config = BrokerConfig.from_dict(config_dict)
        
        assert config.broker_host == 'partial.broker.com'
        assert config.broker_port == 1883  # Default value
        assert config.client_id == 'mqtt_client'  # Default value
        assert config.keepalive == 60  # Default value
        assert config.topics['status'] == 'partial/status'
        
    def test_from_dict_empty_config(self):
        """Test creating config from empty dictionary"""
        config_dict = {}
        
        config = BrokerConfig.from_dict(config_dict)
        
        assert config.broker_host == 'localhost'
        assert config.broker_port == 1883
        assert config.client_id == 'mqtt_client'
        assert config.keepalive == 60
        assert config.topics == {}
        
    def test_from_dict_no_mqtt_section(self):
        """Test creating config from dict without mqtt section"""
        config_dict = {'other': 'value'}
        
        config = BrokerConfig.from_dict(config_dict)
        
        assert config.broker_host == 'localhost'
        assert config.broker_port == 1883
        assert config.client_id == 'mqtt_client'
        assert config.keepalive == 60
        assert config.topics == {}