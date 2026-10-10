"""Display the robot and accept arm_cmd commands through gb_helper."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    share = Path(get_package_share_directory('gb_description'))
    description = (share / 'urdf' / 'gripper_bot.urdf').read_text()
    return LaunchDescription([
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument(
            'helper', default_value='true',
            description='Start gb_helper; set false when running it separately.',
        ),
        Node(
            package='robot_state_publisher', executable='robot_state_publisher',
            parameters=[{'robot_description': description}], output='screen',
        ),
        Node(
            package='gb_helper', executable='gb_help', output='screen',
            condition=IfCondition(LaunchConfiguration('helper')),
        ),
        Node(
            package='rviz2', executable='rviz2',
            arguments=['-d', str(share / 'rviz' / 'gripper_bot.rviz')],
            condition=IfCondition(LaunchConfiguration('rviz')), output='screen',
        ),
    ])
