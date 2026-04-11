# bridge_node_async.py
import asyncio
import json
from typing import Dict, Any, Optional
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped

from pymoveit2 import MoveIt2
from pymoveit2.robots import ur5e

MAX_REFLECTION = 5

class AsyncOrchestrator(Node):
    def __init__(self):
        super().__init__('uel_async_orchestrator')
        self.get_logger().info("🚀 UEL Async Orchestrator v2 initialized (with cognitive loop)")

        # ROS2 publishers
        self.pose_pub = self.create_publisher(PoseStamped, '/uel_target_pose', 10)
        self.grasp_pub = self.create_publisher(String, '/uel_grasp_cmd', 10)

        # MoveIt2
        self.moveit2 = MoveIt2(
            node=self,
            joint_names=ur5e.joint_names(),
            base_link_name=ur5e.base_link_name(),
            end_effector_name=ur5e.end_effector_name(),
            group_name=ur5e.MOVE_GROUP,
        )
        self.moveit2.planner = "RRTConnect"

        # 状态
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.mission_state: Dict[str, Any] = {}
        self.reflection_count: int = 0
        self.final_result = {"status": "PENDING", "error_code": None, "latency_ms": None}

    # ==================== 安全校验器（UEL 灵魂） ====================
    def _safety_check(self, task: Dict) -> bool:
        capabilities = self.mission_state.get("capabilities", {})
        constraints = task.get("constraints", {})
        
        # 示例检查：碰撞避免必须遵守
        if constraints.get("collision_avoidance") and not capabilities.get("collision_avoidance_enabled", True):
            self.get_logger().error("❌ Safety violation: collision_avoidance required but not supported")
            return False
        # 可以继续扩展更多规则...
        return True

    # ==================== 入口函数 ====================
    async def execute_mission(self, uel_json: Dict[str, Any]):
        self.mission_state = {
            "mission_id": uel_json.get("mission_id"),
            "tasks": {t['id']: t for t in uel_json.get('tasks', [])},
            "capabilities": uel_json.get("capabilities", {}),
            "execution_mode": uel_json.get('execution', {}).get('mode', 'SEQUENTIAL'),
            "max_reflection": uel_json.get('execution', {}).get('max_reflection', MAX_REFLECTION)
        }
        self.reflection_count = 0
        self.final_result = {"status": "PENDING", "error_code": None, "latency_ms": None}

        # 🔥 关键修复：只把第一个任务入队，后续全靠 on_success/on_fail 动态驱动
        tasks = uel_json.get('tasks', [])
        if tasks:
            await self.task_queue.put(tasks[0]['id'])

        if self.mission_state['execution_mode'] == 'SEQUENTIAL':
            await self._run_sequential()
        else:
            await self._run_parallel()

        self.final_result["status"] = "SUCCEEDED"  # 简化，实际应根据结果判断
        self.get_logger().info(f"🏁 Mission {self.mission_state['mission_id']} completed")

    async def _run_sequential(self):
        while not self.task_queue.empty():
            task_id = await self.task_queue.get()
            await self._execute_task(task_id)

    async def _run_parallel(self):
        # 并行模式下暂时不支持动态分支（复杂），建议先用 SEQUENTIAL 测试闭环
        tasks = []
        while not self.task_queue.empty():
            task_id = await self.task_queue.get()
            tasks.append(asyncio.create_task(self._execute_task(task_id)))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ==================== 核心执行器 ====================
    async def _execute_task(self, task_id: str):
        if task_id not in self.mission_state['tasks']:
            return
        task = self.mission_state['tasks'][task_id]
        task_type = task['task']['type']

        try:
            if not self._safety_check(task):
                raise Exception("Safety check failed")

            if task_type == "MOVE":
                await self._execute_move(task)
            elif task_type == "GRASP":
                await self._execute_grasp(task)
            elif task_type == "VERIFY":
                success = await self._execute_verify(task)
                if not success:
                    await self._handle_on_fail(task)
                    return
            elif task_type == "REFLECT":
                await self._execute_reflect(task)
            elif task_type == "THINK":
                await self._execute_think(task)
            else:
                self.get_logger().warn(f"Unknown task type: {task_type}")

            # 成功则走 on_success
            if 'on_success' in task:
                next_id = task['on_success']
                if next_id in self.mission_state['tasks']:
                    await self.task_queue.put(next_id)

        except Exception as e:
            self.get_logger().error(f"Task {task_id} failed: {e}")
            await self._handle_on_fail(task)

    # ==================== 具体任务实现（保持你的原有逻辑） ====================
    async def _execute_move(self, task): 
        # ...（你的原代码不变）
        pose = PoseStamped()
        pose.header.frame_id = "base_link"
        pose.pose.position.x = task['task']['target']['x']
        pose.pose.position.y = task['task']['target']['y']
        pose.pose.position.z = task['task']['target']['z']
        pose.pose.orientation.w = 1.0
        self.pose_pub.publish(pose)
        self.get_logger().info(f"✅ MOVE {task['id']} to {task['task']['target']}")
        await asyncio.to_thread(self.moveit2.move_to_pose, pose)

    async def _execute_grasp(self, task):
        # ...（你的原代码不变）
        grasp_data = {"width": task['task']['width'], "force": task['task']['force']}
        msg = String()
        msg.data = json.dumps(grasp_data)
        self.grasp_pub.publish(msg)
        self.get_logger().info(f"🦾 GRASP {task['id']}")
        await asyncio.sleep(0.5)

    async def _execute_verify(self, task) -> bool:
        # TODO: 真实接入视觉节点
        self.get_logger().info(f"🔍 VERIFY {task['id']} object={task['task'].get('object')}")
        await asyncio.sleep(0.5)
        return True  # 真实场景请替换为传感器回调

    # ==================== 思考闭环核心 ====================
    async def _execute_reflect(self, task):
        if self.reflection_count >= self.mission_state.get("max_reflection", MAX_REFLECTION):
            self.get_logger().warn("⛔ Max reflection reached")
            return
        self.reflection_count += 1
        # TODO: 这里接入你的 LLM（OpenAI / Grok / Qwen 等）
        prompt = task['task']['prompt']
        self.get_logger().info(f"💭 REFLECT {task['id']} | count={self.reflection_count}")
        await asyncio.sleep(1.0)  # 模拟
        # 实际应让 LLM 返回 {"strategy": "CONTINUE | REPLAN", "next_task_id": "T007", ...}

    async def _execute_think(self, task):
        # TODO: LLM 生成子任务
        self.get_logger().info(f"🧠 THINK {task['id']} goal={task['task'].get('goal')}")
        await asyncio.sleep(1.0)
        # 示例：假设 LLM 返回新的子任务列表
        new_subtasks = [  # 真实应从 LLM 解析
            {"id": "T008", "task": {"type": "MOVE", "target": {"x": 0.4, "y": 0.0, "z": 0.1}}, "constraints": {}}
        ]
        for sub in new_subtasks:
            self.mission_state['tasks'][sub['id']] = sub
            await self.task_queue.put(sub['id'])  # 动态注入！

    async def _handle_on_fail(self, task):
        on_fail = task.get('on_fail')
        if isinstance(on_fail, str):
            if on_fail in self.mission_state['tasks']:
                await self.task_queue.put(on_fail)
        elif isinstance(on_fail, dict):
            fallback = on_fail.get('fallback_id')
            if fallback in self.mission_state['tasks']:
                await self.task_queue.put(fallback)

# ==================== 启动 ====================
def main():
    rclpy.init()
    node = AsyncOrchestrator()
    try:
        loop = asyncio.get_event_loop()
        # 示例调用（实际应从 FastAPI 接收）
        # with open("examples/object_consistency_v2.json") as f:
        #     uel = json.load(f)
        # loop.run_until_complete(node.execute_mission(uel))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()
