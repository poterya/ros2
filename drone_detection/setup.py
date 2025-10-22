from setuptools import setup
import os
from glob import glob

package_name = 'drone_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'resource'), glob('resource/*')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*')),
        (os.path.join('share', package_name, 'urdf'), glob('urdf/*.urdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='user',
    maintainer_email='user@todo.todo',
    description='Drone propeller damage detection',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
    'console_scripts': [
        'drone_controller = drone_detection.drone_controller:main',
        'mavic_damage_controller = drone_detection.mavic_damage_controller:main',
        'mavic_fast_damage = drone_detection.mavic_fast_damage:main',
        'mavic_real_sensors = drone_detection.mavic_real_sensors:main',
        'mavic_no_compensation = drone_detection.mavic_no_compensation:main',
    ],
},
)
