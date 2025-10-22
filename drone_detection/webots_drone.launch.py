import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, EmitEvent
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Get package share directory
    package_dir = get_package_share_directory('drone_detection')
    
    # Webots process
    webots_process = ExecuteProcess(
        cmd=[
            'webots',
            '--mode=realtime',
            os.path.join(package_dir, 'worlds', 'drone_visualization.wbt')
        ],
        output='screen'
    )
    
    # Damage detector node
    damage_detector = Node(
        package='drone_detection',
        executable='drone_controller',
        output='screen'
    )
    
    # Event handler for Webots exit
    webots_exit_event_handler = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=webots_process,
            on_exit=[EmitEvent(event=Shutdown())]
        )
    )
    
    return LaunchDescription([
        webots_process,
        damage_detector,
        webots_exit_event_handler
    ])
