from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    
    # Запускаем официальный Mavic
    mavic_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('webots_ros2_mavic'),
            '/launch/robot_launch.py'
        ])
    )
    
    # Контроллер быстрых повреждений БЕЗ компенсации
    fast_damage_controller = Node(
        package='drone_detection',
        executable='mavic_fast_damage',
        output='screen',
        parameters=[{
            'use_sim_time': True
        }]
    )
    
    return LaunchDescription([
        mavic_launch,
        fast_damage_controller,
    ])