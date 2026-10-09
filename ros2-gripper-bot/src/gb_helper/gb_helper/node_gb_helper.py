#!/usr/bin/env_python3

import math
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from gb_interfaces.msg import GbArm, GbControl
from geometry_msgs.msg import Twist

class GripperBotHelper(Node):
    def __init__(self):
        super().__init__('gripper_bot_helper')
        self.declare_parameter('max_linear_speed', 1.0)
        self.declare_parameter('max_angular_speed', 1.0)
        self.declare_parameter('command_timeout', 0.5)
        self.declare_parameter('publish_period', 0.05)

        self._timeout = self._positive_parameter('command_timeout')
        period = self._positive_parameter('publish_period')
        self._linear_speed = self._positive_parameter('max_linear_speed')
        self._angular_speed = self._positive_parameter('max_angular_speed')

        if period >= self._timeout:
            raise ValueError('publish_period must be less than command_timeout')
        self._forward = self._turn = 0.0
        self._last_command = None

        # Publishers
        self._vel_publisher = self.create_publisher(
            Twist, "cmd_vel", 10
        )

        # Placeholder joint command topics until the arm URDF/controllers exist.
        # Replace these example joint names with the names in your URDF and
        # the topics with those configured by your GbArm-compatible controllers.
        # The base controller reads base_rotate; the elbow reads joint1.
        # 'your_joint_name': self.create_publisher(
        #     GbArm, 'your_joint_name/command', 10
        # ),

        self._arm_publishers = {
            'arm_base_joint': self.create_publisher(
                GbArm, 'arm_base_joint/command', 10
            ),
            'arm_elbow_joint': self.create_publisher(
                GbArm, 'arm_elbow_joint/command', 10
            ),
        }

        # Subscribers
        self._vel_subscriber = self.create_subscription(
            GbControl, "vel_cmd", self._receive_velocity, 10
        )

        self._arm_subscription = self.create_subscription(
            GbArm, "arm_cmd", self._receive_arm, 10
        )

        self._timer = self.create_timer(period, self._publish_command)

    def _positive_parameter(self, name):
        value = float(self.get_parameter(name).value)
        if not math.isfinite(value) or value <= 0.0:
            raise ValueError(f'{name} must be finite and positive')
        return value

    def _receive_velocity(self, command):
        self._forward = command.forward
        self._turn = command.turn
        self._last_command = time.monotonic()

    def _receive_arm(self, command):
        # Forward the complete command so GbArm fields, including open_pincher,
        # remain available to the eventual arm controllers.
        for publisher in self._arm_publishers.values():
            publisher.publish(command)

    def _publish_command(self):
        if (self._last_command is None
                or time.monotonic() - self._last_command > self._timeout):
            self._forward = self._turn = 0.0

        vel_command = Twist()
        vel_command.linear.x = self._forward * self._linear_speed
        # Teleoperation uses positive turn for right; ROS yaw is positive left.
        vel_command.angular.z = -self._turn * self._angular_speed

        self._vel_publisher.publish(vel_command)

def main(args=None):
    rclpy.init(args=args)
    node = None

    try: 
        node = GripperBotHelper()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
