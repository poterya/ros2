import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    package_dir = get_package_share_directory('drone_detection')
    
    return LaunchDescription([
        Node(
            package='drone_detection',
            executable='drone_controller',
            name='drone_controller',
            output='screen'
        )
    ])
