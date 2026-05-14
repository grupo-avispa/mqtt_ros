#!/usr/bin/env python3
"""
ROS 2 node that listens to MQTT messages and republishes them as ROS messages.
Generic bridge with topic-specific parsers for different message formats.
"""

import rclpy
from rclpy.node import Node
import paho.mqtt.client as mqtt
import json
from abc import ABC, abstractmethod
from geometry_msgs.msg import PoseWithCovariance, Pose
from vision_msgs.msg import Detection3D, ObjectHypothesisWithPose
from object_with_region.msg import ObjectRegion3D, ObjectRegion3DArray


class MQTTMessageParser(ABC):
    """Base class for MQTT message parsers"""
    
    @abstractmethod
    def parse(self, data: dict, node: Node) -> ObjectRegion3DArray:
        """Parse MQTT JSON data to ObjectRegion3DArray"""
        pass


class FlatCameraParser(MQTTMessageParser):
    """Parser for smarthome/flat_camera/ messages"""
    
    def parse(self, data: dict, node: Node) -> ObjectRegion3DArray:
        """
        Parse flat_camera MQTT messages.
        
        Expected input format:
        {
            "object_name": "table",
            "region": "unknown"
        }
        """
        try:
            # Create the main message container
            msg = ObjectRegion3DArray()
            
            # Set header with current timestamp
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.header.frame_id = ''
            
            # Extract object_name and region from MQTT data
            object_name = data.get('object_name', '')
            region = data.get('region', 'unknown')
            
            if not object_name:
                node.get_logger().warn('No "object_name" field in MQTT data')
                return msg
            
            # Create ObjectRegion3D object
            object_region = ObjectRegion3D()
            
            # Create Detection3D with the class_id
            detection = Detection3D()
            detection.header.stamp = node.get_clock().now().to_msg()
            detection.header.frame_id = ''
            
            # Add hypothesis with class_id
            hypothesis_with_pose = ObjectHypothesisWithPose()
            hypothesis_with_pose.hypothesis.class_id = str(object_name)
            hypothesis_with_pose.hypothesis.score = 0.0
            
            # Set pose with default values
            hypothesis_with_pose.pose = PoseWithCovariance()
            hypothesis_with_pose.pose.pose = Pose()
            
            detection.results.append(hypothesis_with_pose)
            
            # Assign object and region to ObjectRegion3D
            object_region.object = detection
            object_region.region = str(region)
            
            msg.objects.append(object_region)
            
            return msg
            
        except Exception as e:
            node.get_logger().error(f'Error parsing flat_camera message: {str(e)}')
            return None


class ParserRegistry:
    """Registry for MQTT message parsers mapped to topics"""
    
    def __init__(self):
        self.parsers = {}
        self._register_default_parsers()
    
    def _register_default_parsers(self):
        """Register default parsers for known topics"""
        self.register('smarthome/flat_camera/', FlatCameraParser())
    
    def register(self, topic: str, parser: MQTTMessageParser):
        """Register a parser for a specific topic"""
        self.parsers[topic] = parser
    
    def get_parser(self, topic: str) -> MQTTMessageParser:
        """Get parser for a topic, returns None if not found"""
        return self.parsers.get(topic)
    
    def register_wildcard(self, pattern: str, parser: MQTTMessageParser):
        """Register parser for topic pattern (e.g., 'sensors/+'"""
        self.parsers[pattern] = parser


class MqttToRosBridge(Node):
    def __init__(self):
        super().__init__('mqtt_ros_node')
        
        # Declare and get parameters
        self._declare_and_get_parameters()
        
        # Publisher de ROS
        self.ros_pub = self.create_publisher(self.msg_type, self.ros_topic, 10)
        
        # Initialize parser registry
        self.parser_registry = ParserRegistry()
        
        # Cliente MQTT
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        
        self.get_logger().info(
            f'Connecting to MQTT broker at {self.mqtt_broker}:{self.mqtt_port}')
        
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
        if msgs_type_str == 'ObjectRegion3DArray':
            self.msg_type = ObjectRegion3DArray
        else:
            self.get_logger().warn(
                f'Unsupported msgs_type: {msgs_type_str}. Defaulting to ObjectRegion3DArray')
            self.msg_type = ObjectRegion3DArray
        self.get_logger().info(f'Parameter msgs_type: [{msgs_type_str}]')
        
        self.declare_parameter('ros_topic', '/object_detection/objects_with_region')
        self.ros_topic = self.get_parameter('ros_topic').value
        self.get_logger().info(f'Parameter ros_topic: [{self.ros_topic}]')

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when connecting to MQTT broker"""
        if rc == 0:
            self.get_logger().info('Successfully connected to MQTT broker')
            # Subscribe to topic
            client.subscribe(self.mqtt_topic)
            self.get_logger().info(f'Subscribed to MQTT topic: {self.mqtt_topic}')
        else:
            self.get_logger().error(f'MQTT connection error. Code: {rc}')
    
    def on_mqtt_message(self, client, userdata, msg):
        """Callback when receiving MQTT message"""
        try:
            # Decode MQTT payload
            mqtt_payload = msg.payload.decode('utf-8')
            mqtt_topic = msg.topic
            
            self.get_logger().debug(f'Message received from {mqtt_topic}')
            
            # Parse JSON message
            try:
                data = json.loads(mqtt_payload)
                ros_message = self._parse_message(mqtt_topic, data)
                
                if ros_message:
                    # Publish in ROS
                    self.ros_pub.publish(ros_message)
                    self.get_logger().debug(
                        f'Published ObjectRegion3DArray with {len(ros_message.objects)} objects')
                else:
                    self.get_logger().warn(f'Failed to parse message from {mqtt_topic}')
            except json.JSONDecodeError:
                self.get_logger().warn(
                    f'Invalid JSON received from {mqtt_topic}: {mqtt_payload[:100]}')
            
        except Exception as e:
            self.get_logger().error(f'Error processing MQTT message: {str(e)}')
    
    def _parse_message(self, topic: str, data: dict) -> ObjectRegion3DArray:
        """
        Parse MQTT message using appropriate parser for the topic.
        
        First tries exact topic match, then tries pattern matching.
        """
        # Try exact topic match first
        parser = self.parser_registry.get_parser(topic)
        
        if parser:
            return parser.parse(data, self)
        
        # Try to match subscribed topic if this is a wildcard subscription
        # Check if the current message topic matches the subscribed pattern
        if self.mqtt_topic.endswith('#') or self.mqtt_topic.endswith('+'):
            # Extract base topic and try to find a matching parser
            base_topic = self.mqtt_topic.rstrip('/#')
            if topic.startswith(base_topic):
                parser = self.parser_registry.get_parser(self.mqtt_topic)
                if parser:
                    return parser.parse(data, self)
        
        self.get_logger().warn(
            f'No parser found for topic: {topic}. '
            f'Available topics: {list(self.parser_registry.parsers.keys())}'
        )
        return None
    
    def start(self):
        """Start the bridge"""
        try:
            # Connect to MQTT broker
            self.mqtt_client.connect(self.mqtt_broker, self.mqtt_port, 60)
            
            # Start MQTT loop in separate thread
            self.mqtt_client.loop_start()
            
            self.get_logger().info('MQTT->ROS Bridge started')
            
            # Keep the node active
            rclpy.spin(self)
            
        except Exception as e:
            self.get_logger().error(f'Error starting the bridge: {str(e)}')
        finally:
            # Cleanup on exit
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()
            self.get_logger().info('MQTT->ROS Bridge stopped')


def main(args=None):
    rclpy.init(args=args)
    
    bridge = MqttToRosBridge()
    try:
        bridge.start()
    except KeyboardInterrupt:
        pass
    finally:
        bridge.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()