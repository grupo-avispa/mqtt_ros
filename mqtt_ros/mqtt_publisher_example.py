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
Example MQTT publisher to test the MQTT to ROS bridge.

This standalone script publishes object detection messages using the JSON
schema expected by the ``FlatCameraParser`` of the ``mqtt_ros`` node.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Optional

import paho.mqtt.client as mqtt


class MQTTObjectPublisher:
    """
    Example publisher for object detection messages over MQTT.

    Parameters
    ----------
    broker : str
        MQTT broker hostname or IP address (default: ``'localhost'``).
    port : int
        MQTT broker port (default: ``1883``).
    client_id : str
        MQTT client identifier (default: ``'mqtt_publisher'``).

    """

    def __init__(
        self,
        broker: str = 'localhost',
        port: int = 1883,
        client_id: str = 'mqtt_publisher',
    ) -> None:
        """Initialize the publisher and its MQTT client."""
        self.broker = broker
        self.port = port
        self.client_id = client_id

        # ``CallbackAPIVersion`` only exists in paho-mqtt >= 2.0, so fall back
        # to the legacy constructor for older versions.
        try:
            self.client = mqtt.Client(
                mqtt.CallbackAPIVersion.VERSION1, client_id=client_id)  # type: ignore
        except AttributeError:
            self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

    def on_connect(self, client, userdata, flags, rc) -> None:
        """Print the result of the connection attempt."""
        if rc == 0:
            print(f'Connected to MQTT broker at {self.broker}:{self.port}')
        else:
            print(f'MQTT connection error. Code: {rc}')

    def on_disconnect(self, client, userdata, rc) -> None:
        """Print the result of the disconnection."""
        if rc != 0:
            print(f'Unexpected disconnection. Code: {rc}')
        else:
            print('Disconnected from MQTT broker')

    def connect(self) -> bool:
        """
        Connect to the MQTT broker and start the network loop.

        Returns
        -------
        bool
            ``True`` if the connection was established, ``False`` otherwise.

        """
        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
            # Give the client a moment to establish the connection.
            time.sleep(1)
        except OSError as exc:
            print(f'Error connecting to broker: {exc}')
            return False
        return True

    def publish_object(
        self,
        object_name: str,
        region: str,
        mqtt_topic: str = 'smarthome/flat_camera/',
        bbox_center: Optional[dict] = None,
        confidence: float = 0.0,
    ) -> None:
        """
        Publish a single object detection message to MQTT.

        Parameters
        ----------
        object_name : str
            Name of the detected object (e.g. ``'chair'``).
        region : str
            Region where the object is located (e.g. ``'kitchen'``).
        mqtt_topic : str
            MQTT topic to publish to.
        bbox_center : Optional[dict]
            Optional ``{'x', 'y', 'z'}`` coordinates of the bbox center.
        confidence : float
            Detection confidence score.

        """
        center = bbox_center or {}
        message = {
            'region': region,
            'clase': object_name,
            'confianza': float(confidence),
            'centro_bb': {
                'x': float(center.get('x', 0.0)),
                'y': float(center.get('y', 0.0)),
                'z': float(center.get('z', 0.0)),
            },
            'timestamp': {'segundos': 0, 'nanosegundos': 0},
            'camera_id': '0',
        }

        result = self.client.publish(mqtt_topic, json.dumps(message), qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f'Published: {object_name} in {region} to {mqtt_topic}')
        else:
            print(f'Failed to publish message. Error code: {result.rc}')

    def disconnect(self) -> None:
        """Stop the network loop and disconnect from the broker."""
        self.client.loop_stop()
        self.client.disconnect()


def _parse_args() -> argparse.Namespace:
    """
    Parse the command-line arguments.

    Returns
    -------
    argparse.Namespace
        The parsed command-line arguments.

    """
    parser = argparse.ArgumentParser(
        description='MQTT object detection publisher to test the mqtt_ros '
                    'bridge')
    parser.add_argument(
        '--broker', default='localhost',
        help='MQTT broker address (default: localhost)')
    parser.add_argument(
        '--port', type=int, default=1883,
        help='MQTT broker port (default: 1883)')
    parser.add_argument(
        '--topic', default='smarthome/flat_camera/',
        help='MQTT topic to publish to (default: smarthome/flat_camera/)')
    parser.add_argument(
        '--object', required=True,
        help='Object name (e.g. chair, table, person)')
    parser.add_argument(
        '--region', required=True,
        help='Region name (e.g. kitchen, bedroom, hallway)')
    parser.add_argument(
        '--confidence', type=float, default=0.0,
        help='Detection confidence score (default: 0.0)')
    parser.add_argument('--x', type=float, default=0.0,
                        help='X coordinate of the bbox center')
    parser.add_argument('--y', type=float, default=0.0,
                        help='Y coordinate of the bbox center')
    parser.add_argument('--z', type=float, default=0.0,
                        help='Z coordinate of the bbox center')
    parser.add_argument(
        '--loop', type=int, default=1,
        help='Number of times to publish (default: 1)')
    parser.add_argument(
        '--interval', type=float, default=2.0,
        help='Interval between publications in seconds (default: 2.0)')
    return parser.parse_args()


def main() -> int:
    """
    Run the example publisher.

    Returns
    -------
    int
        Process exit code (0 on success, 1 on connection failure).

    """
    args = _parse_args()

    publisher = MQTTObjectPublisher(
        broker=args.broker,
        port=args.port,
        client_id='mqtt_publisher_example')

    if not publisher.connect():
        return 1

    bbox_center = {'x': args.x, 'y': args.y, 'z': args.z}

    try:
        for i in range(args.loop):
            publisher.publish_object(
                args.object, args.region, args.topic, bbox_center,
                args.confidence)
            if i < args.loop - 1:
                time.sleep(args.interval)
    finally:
        publisher.disconnect()

    return 0


if __name__ == '__main__':
    sys.exit(main())
