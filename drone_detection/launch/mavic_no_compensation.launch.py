from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # Запуск официального контроллера Mavic из пакета webots_ros2_mavic
    mavic_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            get_package_share_directory('webots_ros2_mavic'),
            '/launch/robot_launch.py'
        ])
    )
    
    # Запуск нашего контроллера без компенсации повреждений
    no_compensation_controller = Node(
        package='drone_detection',
        executable='mavic_no_compensation',
        output='screen',
        parameters=[{
            'use_sim_time': True  # Использование симуляционного времени
        }]
    )
    
    return LaunchDescription([
        mavic_launch,
        no_compensation_controller,
    ])
