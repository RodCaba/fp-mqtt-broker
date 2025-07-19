import pytest
import paho.mqtt.client as mqtt
from unittest.mock import Mock, patch
from fp_mqtt_broker.implementations.paho_mqtt_client import PahoMQTTClient


@pytest.mark.unit
class TestPahoMQTTClient:
    """Test cases for PahoMQTTClient implementation"""
    
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_initialization(self, mock_mqtt_client):
        """Test client initialization"""
        client = PahoMQTTClient('test_client')
        
        assert client.client_id == 'test_client'
        mock_mqtt_client.assert_called_once_with(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id='test_client'
        )

    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_connect(self, mock_mqtt_client):
        """Test connecting to broker"""
        mock_instance = Mock()
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        client.connect('localhost', 1883, 60)
        
        mock_instance.connect.assert_called_once_with('localhost', 1883, 60)
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_disconnect(self, mock_mqtt_client):
        """Test disconnecting from broker"""
        mock_instance = Mock()
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        client.disconnect()
        
        mock_instance.disconnect.assert_called_once()
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_reconnect(self, mock_mqtt_client):
        """Test reconnecting to broker"""
        mock_instance = Mock()
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        client.reconnect()
        
        mock_instance.reconnect.assert_called_once()
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_subscribe(self, mock_mqtt_client):
        """Test subscribing to topic"""
        mock_instance = Mock()
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        client.subscribe('test/topic', qos=1)
        
        mock_instance.subscribe.assert_called_once_with('test/topic', 1)
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_publish_success(self, mock_mqtt_client):
        """Test successful message publishing"""
        mock_instance = Mock()
        mock_info = Mock()
        mock_info.rc = 0  # Success
        mock_instance.publish.return_value = mock_info
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        result = client.publish('test/topic', 'test payload', qos=1)
        
        assert result is True
        mock_instance.publish.assert_called_once_with('test/topic', 'test payload', 1)
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_publish_failure(self, mock_mqtt_client):
        """Test failed message publishing"""
        mock_instance = Mock()
        mock_info = Mock()
        mock_info.rc = 1  # Failure
        mock_instance.publish.return_value = mock_info
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        result = client.publish('test/topic', 'test payload', qos=1)
        
        assert result is False
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_is_connected(self, mock_mqtt_client):
        """Test connection status check"""
        mock_instance = Mock()
        mock_instance.is_connected.return_value = True
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        result = client.is_connected()
        
        assert result is True
        mock_instance.is_connected.assert_called_once()
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_loop_start_stop(self, mock_mqtt_client):
        """Test starting and stopping client loop"""
        mock_instance = Mock()
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        client.loop_start()
        client.loop_stop()
        
        mock_instance.loop_start.assert_called_once()
        mock_instance.loop_stop.assert_called_once()
        
    @patch('fp_mqtt_broker.implementations.paho_mqtt_client.mqtt.Client')
    def test_callback_setters(self, mock_mqtt_client):
        """Test setting callbacks"""
        mock_instance = Mock()
        mock_mqtt_client.return_value = mock_instance
        
        client = PahoMQTTClient('test_client')
        
        connect_callback = Mock()
        message_callback = Mock()
        disconnect_callback = Mock()
        
        client.set_on_connect_callback(connect_callback)
        client.set_on_message_callback(message_callback)
        client.set_on_disconnect_callback(disconnect_callback)
        
        assert mock_instance.on_connect == connect_callback
        assert mock_instance.on_message == message_callback
        assert mock_instance.on_disconnect == disconnect_callback