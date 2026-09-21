"""
Architecture #5: PARALLEL
Concurrent Multi-Arm Execution Engine, Thread Pool Synchronization, and Shared Resource Contention Management.
"""

import threading
import time
import concurrent.futures
from typing import Dict, List, Optional, Any, Callable
from src.core.models import (
    ArchitectureType,
    ResourceType,
    AgentStatus
)
from src.core.decentralized_agent import ManipulatorAgent
from src.core.centralized_arbiter import CentralizedRegistry
from src.core.blackboard import BlackboardSharedState


class ParallelExecutionEngine:
    """
    Parallel Architecture Execution Engine enabling concurrent multi-station manipulator actions,
    handling simultaneous power envelope allocation, and asynchronous task execution.
    """
    def __init__(
        self,
        agents: List[ManipulatorAgent],
        central_arbiter: CentralizedRegistry,
        blackboard: BlackboardSharedState,
        max_workers: int = 6
    ):
        self.agents = {a.agent_id: a for a in agents}
        self.central_arbiter = central_arbiter
        self.blackboard = blackboard
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.RLock()
        self.active_parallel_tasks: Dict[str, Dict[str, Any]] = {}
        self.is_running = False

    def run_parallel_batch(self, task_specifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Launches concurrent tasks across multiple manipulator arms in parallel threads.
        Synchronizes resource locks and power envelope with Centralized Arbiter.
        """
        futures = []
        for task in task_specifications:
            agent_id = task.get("agent_id")
            if agent_id in self.agents:
                agent = self.agents[agent_id]
                agent.active_architecture = ArchitectureType.PARALLEL
                f = self.executor.submit(self._execute_single_arm_task, agent, task)
                futures.append((agent_id, f))
                
        results = []
        for agent_id, f in futures:
            try:
                res = f.result(timeout=10.0)
                results.append(res)
            except Exception as e:
                results.append({"agent_id": agent_id, "status": "ERROR", "error": str(e)})
                
        return results

    def _execute_single_arm_task(self, agent: ManipulatorAgent, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Worker execution function run inside individual worker threads.
        """
        task_name = task.get("task_name", "Parallel Workstation Step")
        power_req = task.get("power_kw", 15.0)
        compute_req = task.get("compute_tokens", 5.0)
        duration_sec = task.get("duration_sec", 0.5)
        
        # 1. Check Centralized Power Allocation
        power_approved = self.central_arbiter.register_power_allocation(agent.agent_id, power_req)
        
        if not power_approved:
            # Power throttled by centralized ceiling -> agent waits or negotiates
            agent.status = AgentStatus.WAITING_RESOURCE
            return {
                "agent_id": agent.agent_id,
                "status": "THROTTLED",
                "message": "Power ceiling exceeded; task deferred."
            }
            
        try:
            agent.set_task(task_name, power_req_kw=power_req, compute_req=compute_req)
            self.blackboard._record_event(
                ArchitectureType.PARALLEL,
                source=agent.agent_id,
                target="PARALLEL_BUS",
                action="CONCURRENT_EXECUTION_START",
                details=f"Agent {agent.agent_id} running '{task_name}' in parallel thread (+{power_req} kW)"
            )
            
            # Simulate work duration
            time.sleep(duration_sec)
            
            agent.complete_task()
            self.blackboard._record_event(
                ArchitectureType.PARALLEL,
                source=agent.agent_id,
                target="PARALLEL_BUS",
                action="CONCURRENT_EXECUTION_FINISH",
                details=f"Agent {agent.agent_id} completed parallel task '{task_name}'"
            )
            return {
                "agent_id": agent.agent_id,
                "task_name": task_name,
                "status": "SUCCESS",
                "power_drawn_kw": power_req,
                "duration_sec": duration_sec
            }
        finally:
            self.central_arbiter.release_power(agent.agent_id, power_req)

    def shutdown(self):
        self.executor.shutdown(wait=False)
