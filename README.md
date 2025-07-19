# FP MQTT Broker Package

A flexible MQTT broker package for IoT services that supports optional message handlers, allowing different services to subscribe and handle MQTT messages independently.

## Features

- **Flexible Message Handling**: Support for multiple, optional message handlers
- **Easy Configuration**: Simple configuration through dictionaries or BrokerConfig objects
- **Extensible**: Abstract interfaces for easy customization
- **Production Ready**: Built-in error handling, reconnection logic, and logging

## Installation

```bash
pip install -e .
```

## Usage

```python
from fp_mqtt_broker import BrokerFactory
from fp_mqtt_broker.abstractions import MessageHandler

config = {
    'mqtt': {
        'broker_host': 'localhost',
        'broker_port': 1883,
        'client_id': 'my_service'
    }
}

# Define a custom message handler
class MyMessageHandler(MessageHandler):
    def get_subscribed_topics(self) -> list:
        return ['my/topic']

    def handle_message(self, topic: str, payload: str):
        print(f"Received message on {topic}: {payload}")

# Create and connect the broker with the custom message handler
broker = BrokerFactory.create_broker(config, [MyMessageHandler()])
broker.connect()
```

## Testing

```bash
pytest -v
```