#!/usr/bin/env_python3

import math
import time

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

from gb_interfaces.msg import GbArm, GbControl
from geometry_msgs.msg import TransformStamped, Twist
from tf2_ros import TransformBroadcaster

class GripperBotHelper(Node):
    def __init__(self):
        super().__init__('gripper_bot_helper')
        self.declare_parameter('max_linear_speed', 1.0)
        self.declare_parameter('max_angular_speed', 1.0)
        self.declare_parameter('command_timeout', 0.5)
        self.declare_parameter('publish_period', 0.05)
        self.declare_parameter('pinch_status', True)
        self.declare_parameter('wheel_radius', 0.1)
        self.declare_parameter('wheel_separation', 0.47)

        self._timeout = self._positive_parameter('command_timeout')
        period = self._positive_parameter('publish_period')
        self._linear_speed = self._positive_parameter('max_linear_speed')
        self._angular_speed = self._positive_parameter('max_angular_speed')
        self._wheel_radius = self._positive_parameter('wheel_radius')
        self._wheel_separation = self._positive_parameter('wheel_separation')
        self._x = self._y = self._yaw = 0.0
        self._left_wheel = self._right_wheel = 0.0
        self._last_update = time.monotonic()
        self._tf_broadcaster = TransformBroadcaster(self)

        if period >= self._timeout:
            raise ValueError('publish_period must be less than command_timeout')
        self._forward = self._turn = 0.0
        self._last_command = None
        self._base_angle = self._elbow_angle = 0.0
        self._finger_position = (
            0.04 if self.get_parameter('pinch_status').value else 0.0
        )
        self._joint_publisher = self.create_publisher(JointState, 'joint_states', 10)

        # Publishers
        self._vel_publisher = self.create_publisher(
            Twist, "cmd_vel", 10
        )

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
        if not (math.isfinite(command.forward) and math.isfinite(command.turn)):
            self.get_logger().warn('Ignoring non-finite velocity command')
            return
        self._forward = max(-1.0, min(1.0, command.forward))
        self._turn = max(-1.0, min(1.0, command.turn))
        self._last_command = time.monotonic()

    def _receive_arm(self, command):
        if not (math.isfinite(command.base_rotate) and math.isfinite(command.joint1)):
            self.get_logger().warn('Ignoring non-finite arm command')
            return
        self._base_angle = max(-1.0, min(1.0, command.base_rotate))
        self._elbow_angle = max(-1.0, min(1.0, command.joint1))
        # Each finger slides outward 4 cm; the wrist has no rotation joint.
        self._finger_position = 0.04 if command.open_pincher else 0.0
        for publisher in self._arm_publishers.values():
            publisher.publish(command)

    def _publish_command(self):
        now = time.monotonic()
        dt = min(now - self._last_update, self._timeout)
        self._last_update = now
        if (self._last_command is None
                or now - self._last_command > self._timeout):
            self._forward = self._turn = 0.0

        vel_command = Twist()
        vel_command.linear.x = self._forward * self._linear_speed
        # Teleoperation uses positive turn for right; ROS yaw is positive left.
        vel_command.angular.z = -self._turn * self._angular_speed

        self._vel_publisher.publish(vel_command)
        self._advance_base(vel_command.linear.x, vel_command.angular.z, dt)
        stamp = self.get_clock().now().to_msg()
        transform = TransformStamped()
        transform.header.stamp = stamp
        transform.header.frame_id = 'odom'
        transform.child_frame_id = 'base_footprint'
        transform.transform.translation.x = self._x
        transform.transform.translation.y = self._y
        transform.transform.rotation.z = math.sin(self._yaw / 2.0)
        transform.transform.rotation.w = math.cos(self._yaw / 2.0)
        self._tf_broadcaster.sendTransform(transform)
        joints = JointState()
        joints.header.stamp = stamp
        joints.name = [
            'front_left_wheel_joint', 'front_right_wheel_joint',
            'rear_left_wheel_joint', 'rear_right_wheel_joint',
            'arm_base_joint', 'arm_elbow_joint',
            'gripper_left_joint', 'gripper_right_joint',
        ]
        joints.position = [self._left_wheel, self._right_wheel] * 2 + [
            self._base_angle, self._elbow_angle,
            self._finger_position, self._finger_position,
        ]
        self._joint_publisher.publish(joints)

    def _advance_base(self, linear, angular, dt):
        # Ideal skid-steer motion for RViz; this is not hardware odometry.
        next_yaw = self._yaw + angular * dt
        if abs(angular) < 1e-9:
            self._x += linear * math.cos(self._yaw) * dt
            self._y += linear * math.sin(self._yaw) * dt
        else:
            self._x += linear / angular * (math.sin(next_yaw) - math.sin(self._yaw))
            self._y += linear / angular * (math.cos(self._yaw) - math.cos(next_yaw))
        self._yaw = math.atan2(math.sin(next_yaw), math.cos(next_yaw))
        half_track = self._wheel_separation / 2.0
        self._left_wheel += (linear - angular * half_track) * dt / self._wheel_radius
        self._right_wheel += (linear + angular * half_track) * dt / self._wheel_radius

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
