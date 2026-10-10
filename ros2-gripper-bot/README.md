# ROS 2 Gripper Bot Tutorial

The robot has a 60 × 40 cm box chassis, four wheels, a central vertical
cylindrical arm base, a cylindrical elbow hinge, a second cylindrical arm
segment, and a fixed wrist with two sliding gripper fingers. Dimensions are
example values in metres; edit `src/gb_description/urdf/gripper_bot.urdf` to
match your build. The base and elbow rotate over −1 to +1 radians.

Build and display (ROS 2 Humble):

```bash
cd ros2-gripper-bot
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch gb_description display.launch.py
```

In a second terminal, source the same ROS and workspace setup files and run:

```bash
ros2 run gb_controller gb_ctrl
```

Use J/L to rotate the arm base, I/K to bend the elbow, and Space to toggle
the pincher. The pincher starts open; R resets the arm and opens it. The wrist stays fixed
relative to the forearm (it moves with the arm but has no independent rotation).
`open_pincher=true` slides each finger outward 4 cm; `false` closes them.

The helper publishes `joint_states` for visualization and continues to forward
`GbArm` to `arm_base_joint/command` and `arm_elbow_joint/command`. It converts
W/S and A/D commands into `cmd_vel` and integrates ideal skid-steer motion
to publish `odom` → `base_footprint` and wheel rotation. W/S adjust forward
speed; A/D adjust turning speed. Commands persist until adjusted; R stops
driving and resets the arm. The chassis keeps its current location on reset.
The helper stops motion after 0.5 seconds without velocity commands.
RViz uses `odom` as its fixed frame so chassis movement is visible.
This launch is a kinematic display with no physics simulator or hardware driver.
Joint states represent requested positions, not
measured hardware feedback. Do not run another joint-state publisher alongside
the helper. Use `rviz:=false` for a headless launch.

The launch starts `gb_help` automatically. Run only the keyboard controller in
the second terminal. If you prefer to run the helper yourself, launch with
`helper:=false` and run `ros2 run gb_helper gb_help` in another terminal.
The helper alone has no window and waits for controller commands.
After changing source files, rebuild and source `install/setup.bash` in each
terminal before restarting the nodes.

You can also open the pincher without the keyboard node:

```bash
ros2 topic pub --once /arm_cmd gb_interfaces/msg/GbArm \
  '{base_rotate: 0.0, joint1: 0.0, open_pincher: true}'
```
