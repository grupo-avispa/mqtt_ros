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

"""Launch file for the MqttToRosBridge node."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    """Generate the launch description for the MqttToRosBridge node."""
    # Get the package directory and the default parameters file.
    pkg_dir = get_package_share_directory('mqtt_ros')
    default_params_file = os.path.join(pkg_dir, 'params', 'default_params.yaml')

    # Input parameters declaration.
    params_file = LaunchConfiguration('params_file')

    declare_params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='Full path to the ROS 2 parameters file'
    )

    declare_log_level_arg = DeclareLaunchArgument(
        name='log_level',
        default_value='info',
        description='Logging level (info, debug, ...)'
    )

    # MQTT bridge node.
    mqtt_node_cmd = Node(
        package='mqtt_ros',
        executable='mqtt_ros_node',
        name='mqtt_ros_node',
        output='screen',
        parameters=[params_file],
        arguments=[
            '--ros-args',
            '--log-level',
            ['mqtt_ros_node:=', LaunchConfiguration('log_level')]
        ]
    )

    return LaunchDescription([
        declare_params_file_arg,
        declare_log_level_arg,
        mqtt_node_cmd
    ])
