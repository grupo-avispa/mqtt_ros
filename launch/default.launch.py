# Copyright (c) 2025 Jose Galeas, DTE, Universidad de Málaga
# Copyright (c) 2025 Grupo Avispa, DTE, Universidad de Málaga
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

import os
import sys

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# Loading packages from the current virtual environment
# venv_path = os.environ.get('VIRTUAL_ENV')
# if venv_path:
#     site_packages = os.path.join(
#         venv_path,
#         'lib',
#         f'python{sys.version_info.major}.{sys.version_info.minor}',
#         'site-packages'
#     )
#     sys.path.insert(0, site_packages)
    
def generate_launch_description():
    #venv_path = os.environ.get('VIRTUAL_ENV')
    #venv_python = os.path.join(venv_path, 'bin', 'python') if venv_path else 'python3'
    
    mqtt_dir = get_package_share_directory('mqtt_ros')
    default_params_file = os.path.join(mqtt_dir, 'params', 'params.yaml')

    # Input parameters declaration
    params_file = LaunchConfiguration('params_file')

    declare_params_file_arg = DeclareLaunchArgument(
        'params_file',
        default_value=default_params_file,
        description='Full path to the ROS2 parameters file with detection configuration'
    )
    
    declare_log_level_arg = DeclareLaunchArgument(
        name='log-level',
        default_value='info',
        description='Logging level (info, debug, ...)'
    )
    
    # MQTT Service node
    mqtt_node_cmd = Node(
        package='mqtt_ros',
        executable='mqtt_ros_node',
        name='mqtt_ros_node',
        output='screen',
        #prefix=[venv_python, ' -u '],
        parameters=[params_file])
    
    return LaunchDescription([
        declare_log_level_arg,
        declare_params_file_arg,
        mqtt_node_cmd
    ])