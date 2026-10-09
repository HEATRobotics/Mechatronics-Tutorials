#!/usr/bin/env_python3

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile

class GripperBotHelper(Node):
    def __init__(self):
        pass

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