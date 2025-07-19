import json
import time
import logging
import sys
import socket
import threading
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional, List

from .abstractions.mqtt_client import MQTTClient
from .abstractions.message_handler import MessageHandler
from .config import BrokerConfig

class RecordingState(Enum):
    """Enumeration for the different states of recording."""
    IDLE = "idle"
    RECORDING = "recording"
    PAUSED = "paused"

class MQTTBroker:
    """
    A flexible MQTT broker client that can work with optional message handlers.
    """
    
    def __init__(self, 
                 config: BrokerConfig,
                 mqtt_client: MQTTClient,
                 message_handlers: Optional[List[MessageHandler]] = None):
        """
        Initialize the MQTT broker with configuration and optional message handlers.
        
        :param config: BrokerConfig containing MQTT configuration parameters
        :param mqtt_client: MQTT client abstraction
        :param message_handlers: Optional list of message handlers
        """
        self.config = config
        self.client = mqtt_client
        self.message_handlers = message_handlers or []
        
        # Set up MQTT client callbacks
        self.client.set_on_connect_callback(self.on_connect)
        self.client.set_on_message_callback(self.on_message)
        self.client.set_on_disconnect_callback(self.on_disconnect)
        
        # Initialize state variables
        self.start_time = time.time()
        self.current_recording_state = RecordingState.IDLE
        self.service_running = False

        # Connection event thread
        self._connection_result = None
        self._connection_event = threading.Event()
        
        # Collect all topics from handlers
        self.subscribed_topics = set()
        for handler in self.message_handlers:
            self.subscribed_topics.update(handler.get_subscribed_topics())
        
        # Add default topics from config if available
        if self.config.topics:
            self.subscribed_topics.update(self.config.topics.values())

    def connect(self, timeout: int = 10) -> bool:
        """Connect to the MQTT broker."""
        try:
            logging.info(f"Attempting to connect to MQTT broker at {self.config.broker_host}:{self.config.broker_port}")

            # Set up connection event
            self._connection_result = None
            self._connection_event.clear()

            self.client.connect(self.config.broker_host, self.config.broker_port, self.config.keepalive)
            self.client.loop_start()

            # Wait for connection result
            if self._connection_event.wait(timeout):
                if self._connection_result == 0:
                    logging.info("Connected to MQTT broker successfully")
                    self.service_running = True
                    return True
                else:
                    logging.error(f"Failed to connect to MQTT broker with code {self._connection_result}")
                    self.service_running = False
                    return False
            else:
                logging.error("Connection to MQTT broker timed out")
                self.client.loop_stop()
                self.service_running = False
                return False
            
        except Exception as e:
            logging.error(f"Failed to connect to MQTT broker: {str(e)}")
            self.service_running = False
            return False

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.service_running = False
        if self.client and self.client.is_connected():
            self.client.loop_stop()
            self.client.disconnect()
        logging.info("Disconnected from MQTT broker")

    def add_message_handler(self, handler: MessageHandler) -> None:
        """Add a message handler and subscribe to its topics."""
        self.message_handlers.append(handler)
        new_topics = handler.get_subscribed_topics()
        
        for topic in new_topics:
            if topic not in self.subscribed_topics:
                self.subscribed_topics.add(topic)
                if self.client.is_connected():
                    self.client.subscribe(topic)

    def remove_message_handler(self, handler: MessageHandler) -> None:
        """Remove a message handler."""
        if handler in self.message_handlers:
            self.message_handlers.remove(handler)

    # MQTT Event Handlers
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the MQTT client connects to the broker"""
        self._connection_result = rc
        self._connection_event.set()
        
        if rc == 0:            
            # Subscribe to all collected topics
            for topic in self.subscribed_topics:
                self.client.subscribe(topic)
                logging.info(f"Subscribed to topic: {topic}")
            
            # Publish initial status if status topic is configured
            if self.config.topics and 'status' in self.config.topics:
                self.publish_status_update()
                
        else:
            logging.error(f"Failed to connect to MQTT broker with code {rc}")

    def on_message(self, client, userdata, msg):
        """Callback for when a message is received on a subscribed topic"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            logging.info(f"Received MQTT message on topic {topic}")
            
            # Pass message to all handlers
            for handler in self.message_handlers:
                if topic in handler.get_subscribed_topics():
                    try:
                        handler.handle_message(topic, payload)
                    except Exception as e:
                        logging.error(f"Error in message handler {handler.__class__.__name__}: {str(e)}")
                        
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in MQTT message: {msg.payload}")
        except Exception as e:
            logging.error(f"Error processing MQTT message: {str(e)}")

    def on_disconnect(self, client, userdata, rc):
        """Callback for when the MQTT client disconnects"""
        if rc != 0:
            logging.warning(f"Unexpected MQTT disconnection with code {rc}")
            self._attempt_reconnection()
        else:
            logging.info("Disconnected from MQTT broker")

    def _attempt_reconnection(self):
        """Attempt to reconnect to the MQTT broker"""
        if self.service_running:
            try:
                logging.info("Attempting to reconnect to MQTT broker...")
                self.client.reconnect()
            except Exception as e:
                logging.error(f"Failed to reconnect to MQTT broker: {str(e)}")

    def publish_message(self, topic: str, payload: Dict[str, Any], qos: int = 0) -> bool:
        """Publish a message to a topic."""
        if self.client and self.client.is_connected():
            try:
                success = self.client.publish(topic, json.dumps(payload), qos)
                if success:
                    logging.debug(f"Published message to topic {topic}")
                else:
                    logging.warning(f"Failed to publish message to topic {topic}")
                return success
            except Exception as e:
                logging.error(f"Error publishing message to {topic}: {str(e)}")
                return False
        else:
            logging.debug("Skipping message publish - MQTT client not properly connected")
            return False

    def publish_status_update(self):
        """Publish current server status"""
        if not self.config.topics or 'status' not in self.config.topics:
            return
            
        status = {
            'recording_state': self.current_recording_state.value,
            'timestamp': datetime.now().isoformat(),
            'service': 'mqtt-broker-service',
            'mqtt_status': 'connected',
            'uptime_seconds': time.time() - self.start_time,
        }
        
        self.publish_message(self.config.topics['status'], status)

    def publish_recording_command(self, command: Dict[str, Any]):
        """Publish recording command to devices"""
        if self.config.topics and 'recording_control' in self.config.topics:
            self.publish_message(self.config.topics['recording_control'], command, qos=1)

    def get_ip_address(self) -> str:
        """Get the IP address of the device"""
        try:
            # Auto-detect IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            logging.error(f"Error getting IP address: {str(e)}")
            return "localhost"

    def signal_handler(self, signum, frame):
        """Handle termination signals to gracefully shut down the service"""
        logging.info(f"Received signal {signum}. Shutting down...")
        self.disconnect()
        sys.exit(0)