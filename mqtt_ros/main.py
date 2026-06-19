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

"""Entry point for the MqttToRosBridge node."""

from typing import Any, Optional

from mqtt_ros.mqtt_ros import MqttToRosBridge

import rclpy
from rclpy.executors import ExternalShutdownException


def main(args: Optional[Any] = None) -> None:
    """
    Run the MqttToRosBridge node.

    Initialize the ROS 2 context, create the node and spin until shutdown is
    requested. The MQTT network loop runs in its own thread, so a single
    threaded executor is enough here.

    Parameters
    ----------
    args : Optional[Any]
        Command-line arguments (default: None).

    """
    rclpy.init(args=args)
    node = None

    try:
        node = MqttToRosBridge()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except ExternalShutdownException:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
