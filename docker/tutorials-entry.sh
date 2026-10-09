#!/bin/bash
set -e

T_REPO="${T_REPO:-/home/${USER:-stud}/Mechatronics-Tutorials}"
T_GB_WS="${T_GB_WS:-${T_REPO}/ros2-gripper-bot/gb_ws}"
ROS_HOME="${ROS_HOME:-/tmp/ros}"
export ROS_HOME
mkdir -p "${ROS_HOME}"

source "/opt/ros/${ROS_DISTRO:-humble}/setup.bash"

# Build the physical workspace if this bind-mounted checkout has no artifacts.
if [ ! -f "${T_GB_WS}/install/setup.bash" ]; then
    echo "Building EMBR physical workspace..."
    cd "${T_GB_WS}"
    colcon build --symlink-install
fi

source "${T_GB_WS}/install/setup.bash"

echo "ROS 2 ${ROS_DISTRO:-humble} development environment is ready."
echo "Physical workspace: ${T_GB_WS}"

exec "$@"
