import pytest
import json
import time
import threading
from unittest.mock import Mock, patch
from fp_mqtt_broker import MQTTBroker, RecordingState
from tests.conftest import MockMQTTClient, TestMessageHandler


@pytest.mark.unit
class TestMQTTBroker:
    """Test cases for MQTTBroker class"""
    
    def test_initialization(self, broker_config, mock_mqtt_client, test_message_handler):
        """Test broker initialization"""
        broker = MQTTBroker(broker_config, mock_mqtt_client, [test_message_handler])
        
        assert broker.config == broker_config
        assert broker.client == mock_mqtt_client
        assert len(broker.message_handlers) == 1
        assert broker.current_recording_state == RecordingState.IDLE
        assert not broker.service_running
        assert len(broker.subscribed_topics) == 3
        # Threading attributes
        assert broker._connection_result is None
        assert isinstance(broker._connection_event, threading.Event)
        
    def test_initialization_no_handlers(self, broker_config, mock_mqtt_client):
        """Test broker initialization without handlers"""
        broker = MQTTBroker(broker_config, mock_mqtt_client)
        
        assert len(broker.message_handlers) == 0
        assert len(broker.subscribed_topics) == 3  # Only from config
        
    def test_connect_success(self, mqtt_broker, mock_mqtt_client):
        """Test successful connection"""
        def mock_connect(host, port, keepalive):
            mock_mqtt_client.connected = True
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0
            )).start()

        mock_mqtt_client.connect = mock_connect
        result = mqtt_broker.connect()

        assert result is True
        assert mqtt_broker.service_running is True
        assert mock_mqtt_client.connected is True
        
    def test_connect_failure(self, mqtt_broker, mock_mqtt_client):
        """Test connection failure"""
        mock_mqtt_client.connect = Mock(side_effect=Exception("Connection failed"))
        
        result = mqtt_broker.connect()
        
        assert result is False
        assert mqtt_broker.service_running is False

    def test_connect_failure_exception(self, mqtt_broker, mock_mqtt_client):
        """Test connection failure with exception"""
        mock_mqtt_client.connect = Mock(side_effect=Exception("Connection error"))
        
        with patch('fp_mqtt_broker.broker.logging') as mock_logging:
            result = mqtt_broker.connect()
            mock_logging.error.assert_called_with("Failed to connect to MQTT broker: Connection error")
        
        assert result is False
        assert mqtt_broker.service_running is False
    
    def test_connect_failure_callback(self, mqtt_broker, mock_mqtt_client):
        """Test connection failure with callback"""
        def mock_connect(host, port, keepalive):
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 1  # Non-zero rc indicates failure
            )).start()

        mock_mqtt_client.connect = mock_connect
        result = mqtt_broker.connect()
        
        assert result is False
        assert mqtt_broker.service_running is False
        assert len(mock_mqtt_client.subscribed_topics) == 0
    
    def test_connect_timeout(self, mqtt_broker, mock_mqtt_client):
        """Test connection timeout"""
        mock_mqtt_client.connect = Mock(side_effect=Exception("Connection timed out"))
        
        with patch('fp_mqtt_broker.broker.logging') as mock_logging:
            result = mqtt_broker.connect(timeout=1)
            mock_logging.error.assert_called_with("Failed to connect to MQTT broker: Connection timed out")
        
        assert result is False
        assert mqtt_broker.service_running is False
        
    def test_disconnect(self, mqtt_broker, mock_mqtt_client):
        """Test disconnection"""
        def mock_connect(host, port, keepalive):
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0
            )).start()
        mock_mqtt_client.connect = mock_connect
        mqtt_broker.disconnect()
        
        assert mqtt_broker.service_running is False
        assert mock_mqtt_client.connected is False
        
    def test_add_message_handler(self, mqtt_broker, mock_mqtt_client):
        """Test adding a message handler"""
        def mock_connect(host, port, keepalive):
            mock_mqtt_client.connected = True
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0
            )).start()
        mock_mqtt_client.connect = mock_connect
        mqtt_broker.connect(timeout=1)
        new_handler = TestMessageHandler(['new/topic'])
        initial_count = len(mqtt_broker.message_handlers)
        
        mqtt_broker.add_message_handler(new_handler)
        
        assert len(mqtt_broker.message_handlers) == initial_count + 1
        assert 'new/topic' in mqtt_broker.subscribed_topics
        assert 'new/topic' in mock_mqtt_client.subscribed_topics
        
    def test_remove_message_handler(self, mqtt_broker):
        """Test removing a message handler"""
        initial_handler = mqtt_broker.message_handlers[0]
        initial_count = len(mqtt_broker.message_handlers)
        
        mqtt_broker.remove_message_handler(initial_handler)
        
        assert len(mqtt_broker.message_handlers) == initial_count - 1
        assert initial_handler not in mqtt_broker.message_handlers
        
    def test_on_connect_success(self, mqtt_broker, mock_mqtt_client):
        """Test on_connect callback with successful connection"""
        mqtt_broker._connection_event.clear()
        mqtt_broker.on_connect(None, None, None, 0)

        assert mqtt_broker._connection_result == 0
        assert mqtt_broker._connection_event.is_set()
        
        # Should subscribe to all topics
        expected_topics = mqtt_broker.subscribed_topics
        assert mock_mqtt_client.subscribed_topics == expected_topics
        
    def test_on_connect_failure(self, mqtt_broker, mock_mqtt_client):
        """Test on_connect callback with connection failure"""
        mqtt_broker._connection_event.clear()
        mqtt_broker.on_connect(None, None, None, 1)

        assert mqtt_broker._connection_result == 1
        assert mqtt_broker._connection_event.is_set()
        
        # Should not subscribe to any topics
        assert len(mock_mqtt_client.subscribed_topics) == 0
        
    def test_on_message_valid_json(self, mqtt_broker, test_message_handler):
        """Test on_message callback with valid JSON"""
        test_payload = {'key': 'value', 'number': 42}
        mock_msg = Mock()
        mock_msg.topic = 'test/data'
        mock_msg.payload.decode.return_value = json.dumps(test_payload)
        
        mqtt_broker.on_message(None, None, mock_msg)
        
        assert len(test_message_handler.received_messages) == 1
        assert test_message_handler.received_messages[0]['topic'] == 'test/data'
        assert test_message_handler.received_messages[0]['payload'] == test_payload
        
    def test_on_message_invalid_json(self, mqtt_broker, test_message_handler):
        """Test on_message callback with invalid JSON"""
        mock_msg = Mock()
        mock_msg.topic = 'test/data'
        mock_msg.payload.decode.return_value = 'invalid json'
        
        with patch('fp_mqtt_broker.broker.logging') as mock_logging:
            mqtt_broker.on_message(None, None, mock_msg)
            mock_logging.error.assert_called()
            
        assert len(test_message_handler.received_messages) == 0
        
    def test_on_message_handler_exception(self, mqtt_broker, mock_mqtt_client):
        """Test on_message when handler raises exception"""
        failing_handler = TestMessageHandler(['test/data'])
        failing_handler.handle_message = Mock(side_effect=Exception("Handler error"))
        mqtt_broker.message_handlers = [failing_handler]
        
        test_payload = {'key': 'value'}
        mock_msg = Mock()
        mock_msg.topic = 'test/data'
        mock_msg.payload.decode.return_value = json.dumps(test_payload)
        
        with patch('fp_mqtt_broker.broker.logging') as mock_logging:
            mqtt_broker.on_message(None, None, mock_msg)
            mock_logging.error.assert_called()
            
    def test_on_disconnect_unexpected(self, mqtt_broker):
        """Test on_disconnect callback for unexpected disconnection"""
        mqtt_broker.service_running = True
        
        with patch.object(mqtt_broker, '_attempt_reconnection') as mock_reconnect:
            mqtt_broker.on_disconnect(None, None, 1)  # Non-zero rc = unexpected
            mock_reconnect.assert_called_once()
            
    def test_on_disconnect_expected(self, mqtt_broker):
        """Test on_disconnect callback for expected disconnection"""
        with patch.object(mqtt_broker, '_attempt_reconnection') as mock_reconnect:
            mqtt_broker.on_disconnect(None, None, 0)  # Zero rc = expected
            mock_reconnect.assert_not_called()
            
    def test_publish_message_connected(self, mqtt_broker, mock_mqtt_client):
        """Test publishing message when connected"""
        def mock_connect(host, port, keepalive):
            mock_mqtt_client.connected = True
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0
            )).start()
        mock_mqtt_client.connect = mock_connect
        mqtt_broker.connect(timeout=1)
        test_payload = {'test': 'data'}
        
        result = mqtt_broker.publish_message('test/topic', test_payload, qos=1)
        
        assert result is True
        assert len(mock_mqtt_client.published_messages) == 2 # One for status update, one for test message
        published = mock_mqtt_client.published_messages[1]
        assert published['topic'] == 'test/topic'
        assert json.loads(published['payload']) == test_payload
        assert published['qos'] == 1
        
    def test_publish_message_disconnected(self, mqtt_broker, mock_mqtt_client):
        """Test publishing message when disconnected"""
        test_payload = {'test': 'data'}
        
        result = mqtt_broker.publish_message('test/topic', test_payload)
        
        assert result is False
        assert len(mock_mqtt_client.published_messages) == 0
        
    def test_publish_status_update(self, mqtt_broker, mock_mqtt_client):
        """Test publishing status update"""
        def mock_connect(host, port, keepalive):
            mock_mqtt_client.connected = True
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0
            )).start()
        mock_mqtt_client.connect = mock_connect
        mqtt_broker.connect(timeout=1)

        mock_mqtt_client.published_messages.clear()  # Clear previous messages

        mqtt_broker.publish_status_update()
        
        assert len(mock_mqtt_client.published_messages) == 1
        published = mock_mqtt_client.published_messages[0]
        assert published['topic'] == 'test/status'
        
        status = json.loads(published['payload'])
        assert status['recording_state'] == 'idle'
        assert status['service'] == 'mqtt-broker-service'
        assert status['mqtt_status'] == 'connected'
        assert 'timestamp' in status
        assert 'uptime_seconds' in status
        
    def test_publish_status_update_no_topic(self, broker_config, mock_mqtt_client):
        """Test publishing status update without status topic configured"""
        broker_config.topics = {}
        broker = MQTTBroker(broker_config, mock_mqtt_client)
        def mock_connect(host, port, keepalive):
            threading.Thread(target=lambda: broker.on_connect(
                None, None, None, 0
            )).start()
        mock_mqtt_client.connect = mock_connect
        broker.connect(timeout=1)
        
        broker.publish_status_update()
        
        assert len(mock_mqtt_client.published_messages) == 0
        
    def test_publish_recording_command(self, mqtt_broker, mock_mqtt_client):
        """Test publishing recording command"""
        def mock_connect(host, port, keepalive):
            mock_mqtt_client.connected = True
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0
            )).start()
        mock_mqtt_client.connect = mock_connect
        mqtt_broker.connect(timeout=1)

        mock_mqtt_client.published_messages.clear()  # Clear previous messages

        command = {'command': 'start_recording', 'timestamp': time.time()}
        
        mqtt_broker.publish_recording_command(command)
        
        assert len(mock_mqtt_client.published_messages) == 1
        published = mock_mqtt_client.published_messages[0]
        assert published['topic'] == 'test/control'
        assert json.loads(published['payload']) == command
        assert published['qos'] == 1
        
    @patch('socket.socket')
    def test_get_ip_address_success(self, mock_socket, mqtt_broker):
        """Test getting IP address successfully"""
        mock_socket_instance = Mock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.getsockname.return_value = ('192.168.1.100', 12345)
        
        ip = mqtt_broker.get_ip_address()
        
        assert ip == '192.168.1.100'
        
    @patch('socket.socket')
    def test_get_ip_address_failure(self, mock_socket, mqtt_broker):
        """Test getting IP address with failure"""
        mock_socket.side_effect = Exception("Socket error")
        
        ip = mqtt_broker.get_ip_address()
        
        assert ip == 'localhost'
        
    @patch('sys.exit')
    def test_signal_handler(self, mock_exit, mqtt_broker, mock_mqtt_client):
        """Test signal handler"""
        def mock_connect(host, port, keepalive):
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0
            )).start()
        mock_mqtt_client.connect = mock_connect
        mqtt_broker.connect(timeout=1)
        
        mqtt_broker.signal_handler(2, None)  # SIGINT
        
        assert mqtt_broker.service_running is False
        mock_exit.assert_called_once_with(0)

    def test_connection_event_reset_on_new_connetion(self, mqtt_broker, mock_mqtt_client):
        """Test that the connection event is properly reset on new connection attempts"""
        def mock_connect_failure(host, port, keepalive):
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 1  # Simulate failure
            )).start()
        mock_mqtt_client.connect = mock_connect_failure
        result1 = mqtt_broker.connect(timeout=1)
        assert result1 is False
        assert mqtt_broker._connection_event.is_set()

        def mock_connect_success(host, port, keepalive):
            threading.Thread(target=lambda: mqtt_broker.on_connect(
                None, None, None, 0  # Simulate success
            )).start()
        mock_mqtt_client.connect = mock_connect_success
        result2 = mqtt_broker.connect(timeout=1)
        assert result2 is True
        assert mqtt_broker._connection_event.is_set()

    def test_timeout_behavior(self, mqtt_broker, mock_mqtt_client):
        """Test that the connection properly timesout when no callback is received"""
        mock_mqtt_client.connect = Mock()

        start_time = time.time()
        result = mqtt_broker.connect(timeout=0.1)  # Very short timeout
        end_time = time.time()
        assert result is False
        assert end_time - start_time < 0.2  # Ensure it timed out quickly