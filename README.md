# mqtt_ros

![ROS2](https://img.shields.io/badge/ros2-jazzy-blue?logo=ros&logoColor=white)
![License](https://img.shields.io/github/license/grupo-avispa/mqtt_ros)

## Overview

`mqtt_ros` is a ROS 2 bridge node that subscribes to an MQTT broker and
republishes the received messages as ROS 2 topics. The translation from the
MQTT JSON payload to a ROS 2 message is delegated to topic-specific *parsers*,
so support for new MQTT message formats can be added without touching the
node logic.

The package currently ships the `FlatCameraParser`, which converts
`smarthome/flat_camera/` object-detection payloads into
`object_with_region/ObjectRegion3DArray` messages.

**Keywords:** ROS2, MQTT, bridge, object detection

**Author: Jose Galeas**

This package has been tested under [ROS2] Rolling on [Ubuntu] 24.04. This is
research code; expect that it changes often and any fitness for a particular
purpose is disclaimed.

## Installation

### Dependencies

- [Robot Operating System (ROS) 2](https://docs.ros.org/en/rolling/)
- [paho-mqtt](https://pypi.org/project/paho-mqtt/) (MQTT client library)
- `object_with_region` (provides the `ObjectRegion3DArray` message)

Install the ROS dependencies with rosdep from the workspace root:

```bash
rosdep install --from-paths src --ignore-src -y
```

If `paho-mqtt` is not available through rosdep on your system, install it
with pip:

```bash
pip install -r src/mqtt_ros/requirements.txt
```

### Building

```bash
cd ~/ros2_ws
colcon build --symlink-install --packages-select mqtt_ros
source install/setup.bash
```

## Usage

Launch the bridge with the default parameters:

```bash
ros2 launch mqtt_ros mqtt_ros.launch.py
```

Launch with a custom parameters file or log level:

```bash
ros2 launch mqtt_ros mqtt_ros.launch.py \
  params_file:=/path/to/custom_params.yaml \
  log_level:=debug
```

Run the node directly with parameter overrides:

```bash
ros2 run mqtt_ros mqtt_ros_node --ros-args \
  -p mqtt_broker:=192.168.1.100 \
  -p mqtt_topic:=smarthome/flat_camera/ \
  -p ros_topic:=/object_detection/objects_with_region
```

## Nodes

### mqtt_ros_node

Connects to an MQTT broker, subscribes to `mqtt_topic` and publishes the
parsed detections on `ros_topic`.

#### Published Topics

* **`/object_detection/objects_with_region`** (`object_with_region/ObjectRegion3DArray`)
  Parsed object detections, configurable through the `ros_topic` parameter.

#### Parameters

| Parameter     | Type   | Default                                 | Description                           |
| ------------- | ------ | --------------------------------------- | ------------------------------------- |
| `mqtt_broker` | string | `localhost`                             | MQTT broker hostname or IP address.   |
| `mqtt_port`   | int    | `1883`                                  | MQTT broker port.                     |
| `client_id`   | string | `mqtt_ros_client`                       | MQTT client identifier.               |
| `mqtt_topic`  | string | `smarthome/flat_camera/`                | MQTT topic to subscribe to.           |
| `msgs_type`   | string | `ObjectRegion3DArray`                   | Output ROS message type.              |
| `ros_topic`   | string | `/object_detection/objects_with_region` | ROS topic to publish the messages to. |

## MQTT Message Format

The `FlatCameraParser` expects JSON payloads with the following structure:

```json
{
  "region": "kitchen",
  "id": "class_id",
  "clase": "table",
  "confianza": 0.75,
  "centro_bb": {"x": 1.5, "y": 2.3, "z": 0.0},
  "timestamp": {"segundos": 0, "nanosegundos": 0},
  "camera_id": "0"
}
```

## Testing Publisher

A standalone example publisher is provided to test the bridge without a real
MQTT source:

```bash
python3 src/mqtt_ros/mqtt_ros/mqtt_publisher_example.py \
  --broker localhost --object table --region kitchen \
  --x 1.5 --y 2.3 --confidence 0.75
```

## License

This project is licensed under the Apache License 2.0. See the
[LICENSE](LICENSE) file for details.

[Ubuntu]: https://ubuntu.com/
[ROS2]: https://docs.ros.org/en/rolling/
