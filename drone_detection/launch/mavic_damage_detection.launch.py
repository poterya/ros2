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
    
    # Наш контроллер повреждений
    damage_controller = Node(
        package='drone_detection',
        executable='mavic_damage_controller',
        output='screen',
        parameters=[{
            'use_sim_time': True
        }]
    )
    
    # Узел для визуализации статуса (опционально)
    status_monitor = Node(
        package='drone_detection',
        executable='drone_controller',  # ваш оригинальный контроллер для мониторинга
        output='screen',
        name='status_monitor'
    )
    
    return LaunchDescription([
        mavic_launch,
        damage_controller,
        status_monitor,
    ])