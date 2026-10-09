#!/bin/bash
set -e

ROS_HOME="${ROS_HOME:-/tmp/ros}"
export ROS_HOME
mkdir -p "${ROS_HOME}"

echo "ROS 2 ${ROS_DISTRO:-humble} development environment is ready."
echo "Have Fun ${USER}"

exec "$@"
