#!/usr/bin/env python3
"""
Example MQTT publisher for testing the MQTT to ROS bridge.
Publishes object detection messages in the format expected by mqtt_ros node.
"""

import paho.mqtt.client as mqtt
import json
import time
import argparse
from typing import Optional


class MQTTObjectPublisher:
    """Example publisher for object detection messages via MQTT"""
    
    def __init__(self, broker: str = 'localhost', port: int = 1883, client_id: str = 'mqtt_publisher'):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.client = mqtt.Client(client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connecting to MQTT broker"""
        if rc == 0:
            print(f'✓ Successfully connected to MQTT broker at {self.broker}:{self.port}')
        else:
            print(f'✗ MQTT connection error. Code: {rc}')
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnecting from MQTT broker"""
        if rc != 0:
            print(f'✗ Unexpected disconnection. Code: {rc}')
        else:
            print('✓ Successfully disconnected from MQTT broker')
    
    def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            # Give it a moment to connect
            time.sleep(1)
        except Exception as e:
            print(f'✗ Error connecting to broker: {str(e)}')
            return False
        return True
    
    def publish_object(self, object_name: str, region: str, mqtt_topic: str = 'smarthome/flat_camera/', bbox_center: Optional[dict] = None):
        """
        Publish an object detection message to MQTT.
        
        Args:
            object_name: The name of the detected object (e.g., 'chair')
            region: The region where the object is located (e.g., 'kitchen')
            mqtt_topic: The MQTT topic to publish to
            bbox_center: Optional dict with 'x', 'y', 'z' coordinates of bbox center
        """
        message = {
            'object_name': object_name,
            'region': region
        }
        
        # Add bbox_center if provided
        if bbox_center:
            message['bbox_center'] = {
                'x': float(bbox_center.get('x', 0.0)),
                'y': float(bbox_center.get('y', 0.0)),
                'z': float(bbox_center.get('z', 0.0))
            }
        
        try:
            result = self.client.publish(mqtt_topic, json.dumps(message), qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f'✓ Published: {object_name} in {region} to {mqtt_topic}')
                print(f'  Payload: {json.dumps(message, indent=2)}')
            else:
                print(f'✗ Failed to publish message. Error code: {result.rc}')
        except Exception as e:
            print(f'✗ Error publishing message: {str(e)}')
    
    def publish_multiple(self, objects: list, mqtt_topic: str = 'smarthome/flat_camera/', interval: float = 2.0):
        """
        Publish multiple objects sequentially with delay.
        
        Args:
            objects: List of tuples (object_name, region) or dicts with object_name, region, bbox_center
            mqtt_topic: The MQTT topic to publish to
            interval: Time in seconds between publications
        """
        for idx, obj in enumerate(objects):
            if isinstance(obj, dict):
                self.publish_object(
                    obj['object_name'], 
                    obj['region'], 
                    mqtt_topic,
                    obj.get('bbox_center')
                )
            else:
                self.publish_object(obj[0], obj[1], mqtt_topic)
            
            if idx < len(objects) - 1:
                time.sleep(interval)
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description='MQTT object detection publisher for testing mqtt_ros bridge'
    )
    parser.add_argument(
        '--broker', 
        default='localhost',
        help='MQTT broker address (default: localhost)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=1883,
        help='MQTT broker port (default: 1883)'
    )
    parser.add_argument(
        '--topic',
        default='smarthome/flat_camera/',
        help='MQTT topic to publish to (default: smarthome/flat_camera/)'
    )
    parser.add_argument(
        '--object',
        required=True,
        help='Object name (e.g., chair, table, person)'
    )
    parser.add_argument(
        '--region',
        required=True,
        help='Region name (e.g., kitchen, bedroom, hallway)'
    )
    parser.add_argument(
        '--x',
        type=float,
        default=None,
        help='X coordinate of bbox center'
    )
    parser.add_argument(
        '--y',
        type=float,
        default=None,
        help='Y coordinate of bbox center'
    )
    parser.add_argument(
        '--z',
        type=float,
        default=None,
        help='Z coordinate of bbox center'
    )
    parser.add_argument(
        '--loop',
        type=int,
        default=1,
        help='Number of times to publish (default: 1)'
    )
    parser.add_argument(
        '--interval',
        type=float,
        default=2.0,
        help='Interval between publications in seconds (default: 2.0)'
    )
    
    args = parser.parse_args()
    
    # Create publisher
    publisher = MQTTObjectPublisher(
        broker=args.broker,
        port=args.port,
        client_id='mqtt_publisher_example'
    )
    
    # Connect to broker
    if not publisher.connect():
        return 1
    
    # Prepare bbox_center if coordinates were provided
    bbox_center = None
    if args.x is not None or args.y is not None or args.z is not None:
        bbox_center = {
            'x': args.x if args.x is not None else 0.0,
            'y': args.y if args.y is not None else 0.0,
            'z': args.z if args.z is not None else 0.0
        }
    
    try:
        # Publish object(s)
        if args.loop == 1:
            publisher.publish_object(args.object, args.region, args.topic, bbox_center)
        else:
            # For multiple publications, publish the same object multiple times
            for i in range(args.loop):
                publisher.publish_object(args.object, args.region, args.topic, bbox_center)
                if i < args.loop - 1:
                    time.sleep(args.interval)
    finally:
        publisher.disconnect()
    
    return 0


if __name__ == '__main__':
    exit(main())
