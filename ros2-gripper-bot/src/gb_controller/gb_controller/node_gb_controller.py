#!/usr/bin/env_python3

import sys
import time 
import select
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

from gb_interfaces.msg import GbArm, GbControl

class GripperBotController(Node):
    def __init__(self):
        super().__init__("Controller")
        self.declare_parameter("vel_step", 0.1)
        self.declare_parameter("rotate_step", 0.1)
        self.declare_parameter("actuate_step", 0.1)
        self.declare_parameter("pinch_status", False)
        self.declare_parameter("poll_period", 0.01)

        self._vel_step     = float(self.get_parameter("vel_step").value)
        self._rotate_step   = float(self.get_parameter("rotate_step").value)
        self._actuate_step  = float(self.get_parameter("actuate_step").value)
        self._pinch_status = bool(self.get_parameter("pinch_status").value)

        poll_period = float(self.get_parameter("poll_period").value)

        self._vel_forward = 0.0
        self._vel_turn = 0.0

        self._arm_join1 = 0.0
        self._arm_rotate = 0.0
        #Pinch status open by default <- False

        self._vel_publisher = self.create_publisher(
            GbControl, "vel_cmd", 10
        )

        self._arm_publisher = self.create_publisher(
            GbArm, "arm_cmd", 10
        )

        self._configure_terminal()
        self._timer = self.create_timer(poll_period, self._poll_terminal)
        self._publish_termi_command()
        self.get_logger().info(
            "Simulation teleoperation started: "
            "Car: W/S forward, A/D turn, "
            "Arm: I/K actuate, J/L rotate, _ pinch"
            "r reset, Q quit"
        )

    def _configure_terminal(self) -> None:
        if not sys.stdin.isatty():
            self.get_logger().warn(
                "stdin is not a terminal; commands will be read as they become available"
            )
            return

        import termios
        import tty

        self._terminal_settings = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())

    def _poll_terminal(self) -> None:
        """
        ## Def:
            Callback function for a timer event. Reads terminal inputs when provided
            from `[sys.stdin]`'s first index and navigates specified actions consequently. 
            
        
        #### Base Commands:
        `w -> Increase forward velocity`  \n
        `s -> Descrease forward velocity` \n
        `a -> Decrease turn step (left)`  \n
        `d -> Increase turn step (right)` \n
        #### Arm Commands
        `space` -> Toggle Pincher Open Status \n
        `i`     -> Increase Arm Join Angle 
        `k`     -> Decrease Arm Join Angle
        `j`     -> Rotate Arm Base (left)
        `l`     -> Rotate Arm Base (right)
        """

        while select.select([sys.stdin], [], [], 0.0)[0]:
            key = sys.stdin.read(1).lower()
            if not key:
                self._vel_forward = 0.0
                self._vel_turn = 0.0
                break
            if key == "w":
                self._vel_forward = min(1.0, self._vel_forward + self._vel_step)
            elif key == "s":
                self._vel_forward = max(-1.0, self._vel_forward - self._vel_step)
            elif key == "a":
                self._vel_turn = max(-1.0, self._vel_turn - self._vel_step)
            elif key == "d":
                self._vel_turn = min(1.0, self._vel_turn + self._vel_step)
            elif key == "i":
                self._arm_join1 = min(1.0, self._arm_join1 + self._actuate_step)
            elif key == "k":
                self._arm_join1 = max(-1.0, self._arm_join1 - self._actuate_step)
            elif key == "j":
                self._arm_rotate = max(-1.0, self._arm_rotate - self._rotate_step)
            elif key == "l":
                self._arm_rotate = min(1.0, self._arm_rotate + self._rotate_step)
            elif key == " ":
                self._pinch_status = not self._pinch_status
            elif key == "r":
                self._vel_forward = 0.0
                self._vel_turn = 0.0
                self._arm_rotate = 0.0
                self._arm_rotate = 0.0
                self._pinch_status = False
            elif key == "q":
                self._vel_forward = 0.0
                self._vel_turn = 0.0
                self._arm_rotate = 0.0
                self._arm_rotate = 0.0
                self._pinch_status = False
                rclpy.shutdown()
                return
            else:
                continue
            self._publish_termi_command()
        self._publish(vel=self._vel_forward,
                        turn=self._vel_turn, 
                        actuate=self._arm_join1, 
                        rotate=self._arm_rotate, 
                        pinch=self._pinch_status)

    def _publish_termi_command(self) -> None:
        self._publish(vel=self._vel_forward,
                                turn=self._vel_turn, 
                                actuate=self._arm_join1, 
                                rotate=self._arm_rotate, 
                                pinch=self._pinch_status)
                
        self.get_logger().info(
            f"command: forward={self._vel_forward:+.1f}, "
            f"turn={self._vel_turn:+.1f}, "
            f"actuate={self._arm_join1}, "
            f"rotate={self._arm_rotate}, pinch={self._pinch_status}"
        )

    def _publish(self, *, vel: float, 
                    turn: float, 
                    actuate: float, 
                    rotate: float, 
                    pinch: bool) -> None:
        vel_command = GbControl() 
        arm_command = GbArm()
        
        vel_command.forward = vel
        vel_command.turn = turn
        
        arm_command.joint1 = actuate
        arm_command.base_rotate = rotate
        arm_command.open_pincher = pinch

        self._vel_publisher.publish(vel_command)
        self._arm_publisher.publish(arm_command)

    def destroy_node(self) ->  None:
        if self._terminal_settings is not None:
            import termios

            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._terminal_settings)
            self._terminal_settings = None
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = None

    try: 
        node = GripperBotController()
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