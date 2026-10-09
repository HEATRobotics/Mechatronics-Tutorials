# ROS 2 Humble development environment for the Heat Robotics Tutorials
FROM ros:humble-ros-base-jammy

ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=humble

SHELL ["/bin/bash", "-c"]

ARG USERNAME=stud
ARG USER_UID=1000
ARG USER_GID=1000

ENV HOME=/home/${USERNAME} \
    T_REPO=/home/${USERNAME}/Mechatronics-Tutorials \
    T_GB_WS=/home/${USERNAME}/Mechatronics-Tutorials/ros2-gripper-bot/gb_ws \
    ROS_HOME=/tmp/ros

COPY Tools/environment/ubuntu-packages.txt /tmp/ubuntu-packages.txt
RUN apt-get update \
    && grep -Ev '^[[:space:]]*(#|$)' /tmp/ubuntu-packages.txt \
        | xargs -r apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/* /tmp/ubuntu-packages.txt

RUN groupadd --gid "${USER_GID}" "${USERNAME}" \
    && useradd --uid "${USER_UID}" --gid "${USER_GID}" --create-home \
        --shell /bin/bash "${USERNAME}" \
    && mkdir -p /tmp/ros \
    && chmod 1777 /tmp/ros

WORKDIR ${T_REPO}

COPY docker/tutorials-entrypoint.sh /tutorials-entrypoint.sh

USER ${USERNAME}
ENTRYPOINT ["/tutorials-entrypoint.sh"]
CMD ["bash"]

LABEL maintainer="Heat Robotics" \
      description="Heat Robotics Mechatronics related tutorials" \
      version="1.2627"
