# AgentTor Runtime  
**Reference Implementation for UEL**

AgentTor-Core is a reference runtime for executing UEL (Universal Execution Language) programs on ROS2-based robotic systems.

## 🔗 Related Standard
**UEL Specification (v1.0-alpha)**:  
https://github.com/wcg696/uel-spec  

*(This repository is the **implementation/reference runtime**, not the protocol standard itself. The full UEL protocol definition, schema, semantics, and adapter interfaces are defined in the uel-spec repo.)*

---

## 🧠 What this repo contains
- UEL → ROS2 bridge
- MoveIt execution layer
- Gazebo simulation support (UR5e + Robotiq 2F-85)
- FastAPI backend + web UI demo (AgentTor V3.1 control console)

## ⚠️ Important Note
This repo is **NOT** the UEL standard.  
The standard protocol lives in:  
→ https://github.com/wcg696/uel-spec

---

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture Overview](#architecture-overview)
- [Installation](#installation)
- [Running the Demo](#running-the-demo)
- [Contributing](#contributing)
- [License](#license)

## Prerequisites
- Ubuntu 22.04 / 24.04 (recommended)
- ROS 2 Jazzy Jalisco[](https://docs.ros.org/en/jazzy/Installation.html)
- Python 3.10+
- Gazebo Harmonic (comes with ROS 2 Jazzy)
- pip packages: fastapi, uvicorn, pydantic, openai (for LLM compilation), pymoveit2

## Quick Start (Simulation Demo)
```bash
# 1. Source ROS 2
source /opt/ros/jazzy/setup.bash

# 2. Launch Gazebo + UR5e + MoveIt
ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=ur5e gripper:=robotiq_2f_85

# 3. In a new terminal: Launch UEL Bridge
cd ~/AgentTor-Core  # or your path
source install/setup.bash   # if you built as ROS package
python3 bridge_node.py

# 4. In another terminal: Start FastAPI backend
cd backend   # or wherever your main.py is
uvicorn main:app --reload --port 8000

# 5. Open browser: http://localhost:8000 (or your UI endpoint)
# Input natural language command → see UEL JSON → robot moves in Gazebo

# 启动 FastAPI backend
uvicorn main:app --reload --port 8000
## UEL Specification

This project follows the UEL (Universal Execution Language) standard:

https://github.com/wcg696/uel-spec
