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

config = {
    'mqtt': {
        'broker_host': 'localhost',
        'broker_port': 1883,
        'client_id': 'my_service'
    }
}

broker = BrokerFactory.create_broker(config)
broker.connect()
```

## Testing

```bash
pytest -v
```