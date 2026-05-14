# MQTT to ROS Bridge

A flexible and configurable ROS 2 node that acts as a bridge between MQTT brokers and the ROS ecosystem. This node listens to MQTT topics and republishes the messages as ROS messages.

## Overview

The MQTT to ROS Bridge provides a general-purpose solution for integrating MQTT-based systems with ROS applications. All aspects of the bridge are configurable through ROS parameters, including the MQTT broker connection details, input/output topics, and message types.

### Features

- **Configurable MQTT Connection**: Specify broker address, port, and client ID via parameters
- **Flexible Topic Mapping**: Map any MQTT topic to any ROS topic through parameters
- **JSON Support**: Automatically parses JSON payloads and enriches messages with metadata
- **Metadata Enrichment**: Adds timestamp and source topic information to all messages
- **Async Message Processing**: Uses threaded MQTT loop for non-blocking message handling
- **Logging**: Comprehensive ROS logging for debugging and monitoring

## Installation

### Dependencies

```bash
pip3 install paho-mqtt
```

Or install via rosdep from the package's `package.xml`:

```bash
rosdep install --from-paths src --ignore-src -y
```

## Configuration

All parameters can be set in a launch file or via command-line arguments. The following parameters are available:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mqtt_broker` | string | `localhost` | MQTT broker hostname or IP address |
| `mqtt_port` | int | `1883` | MQTT broker port |
| `client_id` | string | `mqtt_ros_client` | MQTT client identifier |
| `mqtt_topic` | string | `smarthome/flat_camera/` | MQTT topic(s) to subscribe to (supports wildcards) |
| `ros_topic` | string | `/camera/image_raw` | ROS topic to publish messages to |

## Usage

### Launch with Default Parameters

```bash
ros2 launch mqtt_ros mqtt_ros.launch.py
```

### Launch with Custom Parameters

```bash
ros2 launch mqtt_ros mqtt_ros.launch.py \
  mqtt_broker:=192.168.1.100 \
  mqtt_port:=1883 \
  mqtt_topic:=sensors/temperature \
  ros_topic:=/sensors/temperature_reading
```

### Using a Configuration File

Create a `params.yaml` file:

```yaml
mqtt_ros_bridge:
  ros__parameters:
    mqtt_broker: "broker.example.com"
    mqtt_port: 1883
    client_id: "my_ros_client"
    mqtt_topic: "building/floor1/room1/#"
    ros_topic: "/sensors/data"
```

Then launch with:

```bash
ros2 run mqtt_ros mqtt_ros --ros-args --params-file params.yaml
```

## Message Format

Published ROS messages include the following structure (as JSON string):

```json
{
  "source_topic": "smarthome/flat_camera/image",
  "timestamp": 1234567890.123,
  "data": {
    "image": "base64_encoded_data",
    "width": 640,
    "height": 480
  }
}
```

If the MQTT payload is not valid JSON, it will be published as a plain text string within the message.

## Examples

### Example 1: Temperature Sensor Bridge

Subscribe to MQTT temperature sensor and republish in ROS:

```bash
ros2 run mqtt_ros mqtt_ros --ros-args \
  -p mqtt_broker:=localhost \
  -p mqtt_port:=1883 \
  -p mqtt_topic:=sensors/temperature \
  -p ros_topic:=/sensors/temperature
```

### Example 2: Multiple Sensors with Wildcard

Subscribe to all sensors under a building:

```bash
ros2 run mqtt_ros mqtt_ros --ros-args \
  -p mqtt_broker:=192.168.1.100 \
  -p mqtt_topic:=building/sensors/# \
  -p ros_topic:=/building/sensor_data
```

## Troubleshooting

### Connection Issues

- **Cannot connect to broker**: Verify the `mqtt_broker` and `mqtt_port` parameters
- **Check network connectivity**: `ping <broker_address>`
- **Verify broker is running**: Ensure the MQTT broker is accessible and running

### Message Not Received

- **Wrong MQTT topic**: Verify the `mqtt_topic` parameter matches the publisher's topic
- **Check MQTT logs**: Enable MQTT broker logging for debugging
- **ROS logging**: Run with `--log-level=debug` for detailed debug information

## Debugging

Enable debug logging:

```bash
ros2 run mqtt_ros mqtt_ros --ros-args --log-level=debug
```

Monitor published messages:

```bash
ros2 topic echo /your_ros_topic
```

## Node Architecture

```
┌─────────────────────────┐
│   MQTT Broker           │
│  (External System)      │
└───────────┬─────────────┘
            │
            │ MQTT Protocol
            │
┌───────────▼─────────────┐
│  MQTT Client            │
│  (Async Loop Thread)    │
└───────────┬─────────────┘
            │
            │ on_message callback
            │
┌───────────▼─────────────────────┐
│  Message Processing             │
│  - Parse JSON (if applicable)   │
│  - Add metadata                 │
│  - Enrich with timestamp        │
└───────────┬─────────────────────┘
            │
            │ ROS Publish
            │
┌───────────▼─────────────┐
│  ROS Topic              │
│  (ros_topic parameter)  │
└─────────────────────────┘
```

## Limitations

- Messages are published as JSON strings in `String` type messages
- No authentication support for MQTT broker (username/password)
- SSL/TLS connection not supported in current version

## Future Enhancements

- Support for multiple MQTT subscriptions
- Support for MQTT authentication (username/password)
- Support for SSL/TLS connections
- Automatic message type detection and conversion
- Binary message support

## License

[Add your license here]

## Contributing

Contributions are welcome! Please submit pull requests or issues to the project repository.
