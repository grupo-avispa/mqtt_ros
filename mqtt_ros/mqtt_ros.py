# Copyright (c) 2026 Jose Galeas
# Copyright (c) 2026 Grupo Avispa, DTE, Universidad de Málaga
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
MqttToRosBridge ROS 2 node.

This module provides a ROS 2 node that subscribes to an MQTT broker and
republishes the received MQTT messages as ROS 2 messages. The translation
from the MQTT JSON payload to a ROS 2 message is delegated to topic-specific
parsers registered in a :class:`ParserRegistry`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import json
from typing import Dict, Optional

from geometry_msgs.msg import Pose, PoseWithCovariance

from object_with_region.msg import ObjectRegion3D, ObjectRegion3DArray

import paho.mqtt.client as mqtt

from rclpy.node import Node

from vision_msgs.msg import BoundingBox3D, Detection3D, ObjectHypothesisWithPose


class MQTTMessageParser(ABC):
    """Base class for MQTT message parsers."""

    @abstractmethod
    def parse(
        self,
        data: dict,
        node: Node,
    ) -> Optional[ObjectRegion3DArray]:
        """
        Parse an MQTT JSON payload into an ``ObjectRegion3DArray``.

        Parameters
        ----------
        data : dict
            The decoded JSON payload of the MQTT message.
        node : Node
            The owning ROS 2 node, used for logging.

        Returns
        -------
        Optional[ObjectRegion3DArray]
            The parsed message, or ``None`` if parsing failed.

        """
        raise NotImplementedError


class FlatCameraParser(MQTTMessageParser):
    """Parser for ``smarthome/flat_camera/`` messages."""

    def parse(
        self,
        data: dict,
        node: Node,
    ) -> Optional[ObjectRegion3DArray]:
        """
        Parse a ``flat_camera`` MQTT message.

        Expected input format::

            {
                "region": "unknown",
                "id": "class_id",
                "clase": "table",
                "confianza": "0.0",
                "centro_bb": {"x": 1.5, "y": 2.3},
                "timestamp": {"segundos": 0, "nanosegundos": 0},
                "camera_id": "0"
            }

        Parameters
        ----------
        data : dict
            The decoded JSON payload of the MQTT message.
        node : Node
            The owning ROS 2 node, used for logging.

        Returns
        -------
        Optional[ObjectRegion3DArray]
            The parsed message, or ``None`` if parsing failed.

        """
        try:
            # Create the main message container.
            msg = ObjectRegion3DArray()

            # Extract fields from the MQTT payload.
            confianza = data.get('confianza', 0.0)
            object_name = data.get('clase', '')
            region = data.get('region', 'unknown')
            bbox_center = data.get('centro_bb', {})
            timestamp = data.get('timestamp', {})
            camera_id = data.get('camera_id', '')

            # Set header with the timestamp coming from the MQTT message.
            stamp_sec = int(timestamp.get('segundos', 0))
            stamp_nanosec = int(timestamp.get('nanosegundos', 0))
            msg.header.stamp.sec = stamp_sec
            msg.header.stamp.nanosec = stamp_nanosec
            msg.header.frame_id = str(camera_id)

            if not object_name:
                node.get_logger().warning('No "clase" field in MQTT data')
                return msg

            # Create the ObjectRegion3D object.
            object_region = ObjectRegion3D()

            # Create the Detection3D with the class id.
            detection = Detection3D()
            detection.header.stamp.sec = stamp_sec
            detection.header.stamp.nanosec = stamp_nanosec
            detection.header.frame_id = str(camera_id)

            bounding_box = BoundingBox3D()
            bounding_box.center.position.x = float(bbox_center.get('x', 0.0))
            bounding_box.center.position.y = float(bbox_center.get('y', 0.0))
            detection.bbox = bounding_box

            # Add the hypothesis with the class id and score.
            hypothesis_with_pose = ObjectHypothesisWithPose()
            hypothesis_with_pose.hypothesis.class_id = str(object_name)
            hypothesis_with_pose.hypothesis.score = float(confianza)

            # Set the pose with the bbox center if available.
            hypothesis_with_pose.pose = PoseWithCovariance()
            hypothesis_with_pose.pose.pose = Pose()

            if bbox_center:
                pose = hypothesis_with_pose.pose.pose
                pose.position.x = float(bbox_center.get('x', 0.0))
                pose.position.y = float(bbox_center.get('y', 0.0))
                pose.position.z = float(bbox_center.get('z', 0.0))

            # Set the default orientation (identity quaternion).
            hypothesis_with_pose.pose.pose.orientation.x = 0.0
            hypothesis_with_pose.pose.pose.orientation.y = 0.0
            hypothesis_with_pose.pose.pose.orientation.z = 0.0
            hypothesis_with_pose.pose.pose.orientation.w = 1.0

            detection.results.append(hypothesis_with_pose)

            # Assign the object and region to the ObjectRegion3D.
            object_region.object = detection
            object_region.region = str(region)

            msg.objects.append(object_region)

            return msg

        except (ValueError, TypeError, AttributeError) as exc:
            # The payload did not match the expected schema/types.
            node.get_logger().error(
                f'Error parsing flat_camera message: {exc}')
            return None


class ParserRegistry:
    """Registry that maps MQTT topics to their message parsers."""

    def __init__(self) -> None:
        """Initialize the registry with the default parsers."""
        self.parsers: Dict[str, MQTTMessageParser] = {}
        self._register_default_parsers()

    def _register_default_parsers(self) -> None:
        """Register the default parsers for the known topics."""
        self.register('smarthome/flat_camera/', FlatCameraParser())

    def register(self, topic: str, parser: MQTTMessageParser) -> None:
        """
        Register a parser for a specific topic.

        Parameters
        ----------
        topic : str
            The MQTT topic (or topic pattern) to associate with the parser.
        parser : MQTTMessageParser
            The parser instance to register.

        """
        self.parsers[topic] = parser

    def get_parser(self, topic: str) -> Optional[MQTTMessageParser]:
        """
        Return the parser registered for a topic.

        Parameters
        ----------
        topic : str
            The MQTT topic to look up.

        Returns
        -------
        Optional[MQTTMessageParser]
            The registered parser, or ``None`` if none is found.

        """
        return self.parsers.get(topic)


class MqttToRosBridge(Node):
    """
    ROS 2 node that bridges MQTT messages to ROS 2 topics.

    The node connects to an MQTT broker, subscribes to a configurable topic
    and republishes the parsed payloads as ``ObjectRegion3DArray`` messages.

    Parameters
    ----------
    node_name : str
        Name of the ROS 2 node (default: ``'mqtt_ros_node'``).

    """

    def __init__(self, node_name: str = 'mqtt_ros_node') -> None:
        """
        Initialize the bridge node.

        Parameters
        ----------
        node_name : str
            Name of the ROS 2 node (default: ``'mqtt_ros_node'``).

        """
        super().__init__(node_name)

        # Declare and get parameters.
        self._declare_and_get_parameters()

        # ROS 2 publisher.
        self.ros_pub = self.create_publisher(self.msg_type, self.ros_topic, 10)

        # Parser registry.
        self.parser_registry = ParserRegistry()

        # MQTT client. ``CallbackAPIVersion`` only exists in paho-mqtt >= 2.0,
        # so fall back to the legacy constructor for older versions.
        try:
            self.mqtt_client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1, client_id=self.client_id)  # type: ignore
        except AttributeError:
            self.mqtt_client = mqtt.Client(client_id=self.client_id)
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message

        self.get_logger().info(
            f'Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}')
        self.connect()

    def _declare_and_get_parameters(self) -> None:
        """Declare and retrieve all ROS 2 parameters."""
        self.declare_parameter('mqtt_broker', 'localhost')
        self.mqtt_broker = self.get_parameter('mqtt_broker').value
        self.get_logger().info(f'Parameter mqtt_broker: [{self.mqtt_broker}]')

        self.declare_parameter('mqtt_port', 1883)
        self.mqtt_port = self.get_parameter('mqtt_port').value
        self.get_logger().info(f'Parameter mqtt_port: [{self.mqtt_port}]')

        self.declare_parameter('client_id', 'mqtt_ros_client')
        self.client_id = self.get_parameter('client_id').value
        self.get_logger().info(f'Parameter client_id: [{self.client_id}]')

        self.declare_parameter('mqtt_topic', 'smarthome/flat_camera/')
        self.mqtt_topic = self.get_parameter('mqtt_topic').value
        self.get_logger().info(f'Parameter mqtt_topic: [{self.mqtt_topic}]')

        self.declare_parameter('msgs_type', 'ObjectRegion3DArray')
        msgs_type_str = self.get_parameter('msgs_type').value
        if msgs_type_str != 'ObjectRegion3DArray':
            self.get_logger().warning(
                f'Unsupported msgs_type: {msgs_type_str}. '
                'Defaulting to ObjectRegion3DArray')
        self.msg_type = ObjectRegion3DArray
        self.get_logger().info(f'Parameter msgs_type: [{msgs_type_str}]')

        self.declare_parameter(
            'ros_topic', '/object_detection/objects_with_region')
        self.ros_topic = self.get_parameter('ros_topic').value
        self.get_logger().info(f'Parameter ros_topic: [{self.ros_topic}]')

    def on_mqtt_connect(self, client, userdata, flags, rc) -> None:
        """
        Handle the MQTT broker connection result.

        Parameters
        ----------
        client : paho.mqtt.client.Client
            The MQTT client instance.
        userdata : Any
            The user data set in the client (unused).
        flags : dict
            Response flags sent by the broker.
        rc : int
            The connection result code (0 means success).

        """
        if rc == 0:
            self.get_logger().info('Successfully connected to MQTT broker')
            client.subscribe(self.mqtt_topic)
            self.get_logger().info(
                f'Subscribed to MQTT topic: {self.mqtt_topic}')
        else:
            self.get_logger().error(f'MQTT connection error. Code: {rc}')

    def on_mqtt_message(self, client, userdata, msg) -> None:
        """
        Handle an incoming MQTT message.

        Parameters
        ----------
        client : paho.mqtt.client.Client
            The MQTT client instance (unused).
        userdata : Any
            The user data set in the client (unused).
        msg : paho.mqtt.client.MQTTMessage
            The received MQTT message.

        """
        mqtt_topic = msg.topic
        self.get_logger().debug(f'Message received from {mqtt_topic}')

        try:
            mqtt_payload = msg.payload.decode('utf-8')
            data = json.loads(mqtt_payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self.get_logger().warning(f'Invalid payload received from {mqtt_topic}')
            return

        ros_message = self._parse_message(mqtt_topic, data)
        if ros_message is None:
            self.get_logger().warning(f'Failed to parse message from {mqtt_topic}')
            return

        self.ros_pub.publish(ros_message)
        self.get_logger().debug(
            f'Published ObjectRegion3DArray with '
            f'{len(ros_message.objects)} objects')

    def _parse_message(
        self,
        topic: str,
        data: dict,
    ) -> Optional[ObjectRegion3DArray]:
        """
        Parse an MQTT message using the parser registered for the topic.

        Tries an exact topic match first, then a wildcard subscription match.

        Parameters
        ----------
        topic : str
            The MQTT topic the message was received on.
        data : dict
            The decoded JSON payload.

        Returns
        -------
        Optional[ObjectRegion3DArray]
            The parsed message, or ``None`` if no parser handled it.

        """
        # Try an exact topic match first.
        parser = self.parser_registry.get_parser(topic)
        if parser is not None:
            return parser.parse(data, self)

        # Try to match against a wildcard subscription pattern.
        if self.mqtt_topic.endswith('#') or self.mqtt_topic.endswith('+'):
            base_topic = self.mqtt_topic.rstrip('/#+')
            if topic.startswith(base_topic):
                parser = self.parser_registry.get_parser(self.mqtt_topic)
                if parser is not None:
                    return parser.parse(data, self)

        self.get_logger().warning(
            f'No parser found for topic: {topic}. '
            f'Available topics: {list(self.parser_registry.parsers.keys())}')
        return None

    def connect(self) -> None:
        """Connect to the MQTT broker and start the network loop."""
        try:
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            self.mqtt_client.loop_start()
            self.get_logger().info('MQTT->ROS bridge started')
        except OSError as exc:
            # Network/connection errors (broker unreachable, refused, ...).
            self.get_logger().error(f'Error starting the bridge: {exc}')

    def destroy_node(self) -> None:
        """
        Stop the MQTT client and destroy the node.

        Returns
        -------
        bool
            ``True`` if the node was successfully destroyed.

        """
        self.mqtt_client.loop_stop()
        self.mqtt_client.disconnect()
        self.get_logger().info('MQTT->ROS bridge stopped')
        super().destroy_node()
