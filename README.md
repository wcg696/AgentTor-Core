# AgentTor Runtime  
**Reference Implementation for UEL**

AgentTor-Core is the official reference runtime for executing UEL (Universal Execution Language) programs on ROS2-based robotic systems.

## 🔗 Related Standard
**UEL Specification (v1.0-alpha)**:  
https://github.com/wcg696/uel-spec  

*(This repository is the **implementation/reference runtime**, not the protocol standard itself. The full UEL protocol definition, schema, semantics, and adapter interfaces are defined in the uel-spec repo.)*

[![UEL Spec](https://img.shields.io/badge/UEL_Spec-v1.0--alpha-blue)](https://github.com/wcg696/uel-spec)

---

## 🧠 What this repo contains
- UEL → ROS2 bridge
- MoveIt execution layer
- Gazebo simulation support (UR5e + Robotiq 2F-85)
- FastAPI backend + web UI demo (AgentTor V3.1 control console)

## ⚠️ Important Note
This repo is **NOT** the UEL standard.  
The standard protocol lives here:  
→ https://github.com/wcg696/uel-spec

---

（下面继续放原来的内容：安装步骤、快速启动命令、架构说明、依赖列表、贡献指南、许可证等）

### Demo
![UR5e Pick & Place in Gazebo](docs/demo.gif)  <!-- 如果你有 GIF，就放这里；没有可以删掉或先留占位 -->

### Quick Start
```bash
# 启动 Gazebo + UR5e + MoveIt
ros2 launch ur_simulation_gz ur_sim_moveit.launch.py ur_type:=ur5e

# 启动 UEL Bridge
python3 bridge_node.py

# 启动 FastAPI backend
uvicorn main:app --reload --port 8000
