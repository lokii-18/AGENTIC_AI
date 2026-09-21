"""
Industrial Assembly Environment orchestrating all 6 Manipulators, 2 Cell Supervisors,
Central Arbiter, Blackboard, Pipeline, and Parallel Engine.
"""

import time
import threading
from typing import Dict, List, Optional, Any
from src.core.models import (
    ArchitectureType,
    ResourceType,
    ConcessionStrategy,
    AgentStatus,
    NegotiationOffer,
    WorkpieceDataContract
)
from src.core.blackboard import BlackboardSharedState
from src.core.centralized_arbiter import CentralizedRegistry
from src.core.hierarchical_supervisor import CellSupervisorAgent
from src.core.decentralized_agent import ManipulatorAgent
from src.core.p2p_negotiator import P2PNegotiator
from src.core.pipeline_orchestrator import AssemblyPipelineEngine
from src.core.parallel_engine import ParallelExecutionEngine


class AssemblyEnvironment:
    """
    Comprehensive Robotic Assembly Environment seamlessly unifying all 7 Multi-Agent Architectures.
    """
    def __init__(self):
        # 1. Instantiate Blackboard Shared State (Arch 6)
        self.blackboard = BlackboardSharedState()
        
        # 2. Instantiate Centralized Registry (Arch 1)
        self.central_arbiter = CentralizedRegistry(self.blackboard, max_grid_power_kw=100.0)
        
        # 3. Instantiate Autonomous Manipulator Agents (Arch 3)
        self.m1 = ManipulatorAgent(
            agent_id="M1_LOADER",
            name="Manipulator 1 (Infeed Loader)",
            role="Raw Workpiece Jig Clamping & Orientation",
            cell_id="CELL_A",
            blackboard=self.blackboard,
            concession_strategy=ConcessionStrategy.LINEAR,
            beta_concession=1.0,
            budget_tokens=180.0,
            standby_power_kw=3.2
        )
        self.m2 = ManipulatorAgent(
            agent_id="M2_WELDER",
            name="Manipulator 2 (Laser Welder)",
            role="High-Precision Fiber Laser Welding",
            cell_id="CELL_A",
            blackboard=self.blackboard,
            concession_strategy=ConcessionStrategy.BOULWARE,
            beta_concession=0.45,  # Boulware: stubborn, hard bargainer
            budget_tokens=220.0,
            standby_power_kw=4.8
        )
        self.m3 = ManipulatorAgent(
            agent_id="M3_SEALANT",
            name="Manipulator 3 (Adhesive Dispenser)",
            role="Thermal Sealant & Gasket Dispensing",
            cell_id="CELL_A",
            blackboard=self.blackboard,
            concession_strategy=ConcessionStrategy.CONCEDER,
            beta_concession=2.2,   # Conceder: eager for consensus
            budget_tokens=150.0,
            standby_power_kw=3.5
        )
        self.m4 = ManipulatorAgent(
            agent_id="M4_FASTENER",
            name="Manipulator 4 (Bolt Fastener)",
            role="Multi-Spindle Torque Bolt Fastening",
            cell_id="CELL_B",
            blackboard=self.blackboard,
            concession_strategy=ConcessionStrategy.LINEAR,
            beta_concession=1.0,
            budget_tokens=190.0,
            standby_power_kw=3.8
        )
        self.m5 = ManipulatorAgent(
            agent_id="M5_INSPECTOR",
            name="Manipulator 5 (Optical Inspector)",
            role="AI Computer Vision Metrology & Defect Analysis",
            cell_id="CELL_B",
            blackboard=self.blackboard,
            concession_strategy=ConcessionStrategy.BOULWARE,
            beta_concession=0.6,
            budget_tokens=200.0,
            standby_power_kw=4.2
        )
        self.m6 = ManipulatorAgent(
            agent_id="M6_PALLETIZER",
            name="Manipulator 6 (Outfeed Palletizer)",
            role="Finished Part Boxing & Buffer Palletizing",
            cell_id="CELL_B",
            blackboard=self.blackboard,
            concession_strategy=ConcessionStrategy.CONCEDER,
            beta_concession=1.8,
            budget_tokens=140.0,
            standby_power_kw=3.0
        )
        
        self.agents_list = [self.m1, self.m2, self.m3, self.m4, self.m5, self.m6]
        self.agents_dict = {a.agent_id: a for a in self.agents_list}
        
        # 4. Instantiate Hierarchical Supervisors (Arch 2)
        self.supervisor_a = CellSupervisorAgent(
            supervisor_id="SUP_CELL_A",
            cell_id="CELL_A",
            cell_name="Structural & Welding Cell",
            managed_agents=["M1_LOADER", "M2_WELDER", "M3_SEALANT"],
            blackboard=self.blackboard
        )
        self.supervisor_b = CellSupervisorAgent(
            supervisor_id="SUP_CELL_B",
            cell_id="CELL_B",
            cell_name="Assembly, Metrology & Packing Cell",
            managed_agents=["M4_FASTENER", "M5_INSPECTOR", "M6_PALLETIZER"],
            blackboard=self.blackboard
        )
        
        # 5. Instantiate P2P Negotiator (Arch 7)
        self.p2p_negotiator = P2PNegotiator(
            blackboard=self.blackboard,
            central_arbiter=self.central_arbiter,
            supervisor=self.supervisor_a
        )
        
        # 6. Instantiate Sequential Pipeline Engine (Arch 4)
        self.pipeline_engine = AssemblyPipelineEngine(
            agents_pipeline=self.agents_list,
            blackboard=self.blackboard
        )
        
        # 7. Instantiate Parallel Execution Engine (Arch 5)
        self.parallel_engine = ParallelExecutionEngine(
            agents=self.agents_list,
            central_arbiter=self.central_arbiter,
            blackboard=self.blackboard,
            max_workers=6
        )
        
        # Simulation step counter
        self.sim_tick = 0
        self._lock = threading.RLock()
        
        # Auto-seed first workpiece
        self.pipeline_engine.spawn_workpiece("WP-CHASSIS")

    def run_bilateral_negotiation(
        self,
        buyer_id: str,
        seller_id: str,
        resource_type_str: str,
        quantity: float,
        initial_price: float,
        max_rounds: int = 8
    ) -> Dict[str, Any]:
        """
        Executes a P2P negotiation between two selected manipulator arms.
        """
        buyer = self.agents_dict.get(buyer_id, self.m2)
        seller = self.agents_dict.get(seller_id, self.m3)
        res_type = ResourceType(resource_type_str)
        
        # Determine supervisor
        sup = self.supervisor_a if buyer.cell_id == "CELL_A" else self.supervisor_b
        self.p2p_negotiator.supervisor = sup
        
        return self.p2p_negotiator.run_bilateral_negotiation(
            buyer=buyer,
            seller=seller,
            resource_type=res_type,
            required_amount=quantity,
            initial_offer_price=initial_price,
            max_rounds=max_rounds
        )

    def trigger_pipeline_step(self) -> Dict[str, Any]:
        """
        Advances the sequential pipeline by one stage for active workpieces.
        """
        with self._lock:
            active_ids = list(self.pipeline_engine.active_workpieces.keys())
            if not active_ids:
                wp = self.pipeline_engine.spawn_workpiece("WP-BATCH")
                active_ids = [wp.workpiece_id]
                
            results = []
            for wp_id in active_ids:
                res = self.pipeline_engine.advance_stage(wp_id)
                results.append(res)
            return {"active_ids": active_ids, "results": results}

    def trigger_parallel_operations(self) -> List[Dict[str, Any]]:
        """
        Triggers concurrent multi-station tasks across all 6 manipulators simultaneously.
        """
        tasks = [
            {"agent_id": "M1_LOADER", "task_name": "Rapid Jig Clamping", "power_kw": 12.0, "duration_sec": 0.2},
            {"agent_id": "M2_WELDER", "task_name": "Seam Laser Pass", "power_kw": 28.0, "duration_sec": 0.3},
            {"agent_id": "M3_SEALANT", "task_name": "Perimeter Bead Extrusion", "power_kw": 14.0, "duration_sec": 0.25},
            {"agent_id": "M4_FASTENER", "task_name": "Synchronous 4-Bolt Drive", "power_kw": 18.0, "duration_sec": 0.2},
            {"agent_id": "M5_INSPECTOR", "task_name": "3D Point-Cloud Defect Scan", "power_kw": 10.0, "duration_sec": 0.35},
            {"agent_id": "M6_PALLETIZER", "task_name": "Vacuum E-Grip Staging", "power_kw": 8.0, "duration_sec": 0.2}
        ]
        return self.parallel_engine.run_parallel_batch(tasks)

    def post_blackboard_rfp(self, requester_id: str, resource_type_str: str, amount: float, max_price: float) -> str:
        """
        Posts an RFP on the shared blackboard and simulates automated peer bids.
        """
        res_type = ResourceType(resource_type_str)
        rfp_id = self.blackboard.post_rfp(
            requester_id=requester_id,
            resource_type=res_type,
            amount=amount,
            max_price=max_price,
            deadline=time.time() + 30.0
        )
        
        # Simulate other agents responding with bids
        for agent in self.agents_list:
            if agent.agent_id != requester_id:
                # 50% probability to bid
                bid_p = round(max_price * 0.85, 2)
                self.blackboard.submit_bid(rfp_id, agent.agent_id, amount, bid_p)
                break
        return rfp_id

    def get_system_summary(self) -> Dict[str, Any]:
        """
        Returns full telemetry snapshot across all 7 architectures.
        """
        with self._lock:
            self.sim_tick += 1
            agents_telemetry = []
            for a in self.agents_list:
                tel = a.get_telemetry()
                tel_dict = tel.model_dump()
                # Normalize enum string values
                tel_dict["status"] = tel.status.value if hasattr(tel.status, "value") else str(tel.status).replace("AgentStatus.", "")
                tel_dict["concession_strategy"] = tel.concession_strategy.value if hasattr(tel.concession_strategy, "value") else str(tel.concession_strategy).replace("ConcessionStrategy.", "")
                tel_dict["active_architecture"] = tel.active_architecture.value if hasattr(tel.active_architecture, "value") else str(tel.active_architecture).replace("ArchitectureType.", "")
                tel_dict["cell_id"] = str(tel.cell_id).replace("CELL_", "Cell ")
                agents_telemetry.append(tel_dict)
                
            arbiter_metrics = self.central_arbiter.get_metrics()
            
            # Real-time power calculation:
            if self.central_arbiter.emergency_halt:
                current_power = 0.0
                for a in agents_telemetry:
                    a["power_draw_kw"] = 0.0
                    a["status"] = "BLOCKED"
            else:
                # Sum active & standby power across all manipulators
                current_power = round(sum(a["power_draw_kw"] for a in agents_telemetry), 1)
                
            arbiter_metrics["current_power_draw_kw"] = current_power
            arbiter_metrics["power_utilization_pct"] = round((current_power / self.central_arbiter.max_grid_power_kw) * 100, 1)
            
            blackboard_snap = self.blackboard.get_snapshot()
            pipeline_snap = self.pipeline_engine.get_pipeline_snapshot()
            recent_events = [e.model_dump() for e in self.blackboard.get_recent_events(limit=25)]
            
            # Architecture Activity Heatmap
            arch_activity = {
                ArchitectureType.CENTRALIZED.value: arbiter_metrics["contracts_registered"] + 1,
                ArchitectureType.HIERARCHICAL.value: self.supervisor_a.escalations_handled + self.supervisor_b.escalations_handled + 2,
                ArchitectureType.DECENTRALIZED.value: sum(a["completed_cycles"] for a in agents_telemetry) + 5,
                ArchitectureType.SEQUENTIAL_PIPELINE.value: len(self.pipeline_engine.completed_workpieces) * 6 + len(self.pipeline_engine.active_workpieces),
                ArchitectureType.PARALLEL.value: self.sim_tick * 2,
                ArchitectureType.BLACKBOARD_SHARED_STATE.value: blackboard_snap["total_events"],
                ArchitectureType.PEER_TO_PEER.value: arbiter_metrics["contracts_registered"] * 3 + 1
            }
            
            return {
                "sim_tick": self.sim_tick,
                "agents": agents_telemetry,
                "arbiter": arbiter_metrics,
                "blackboard": blackboard_snap,
                "pipeline": pipeline_snap,
                "supervisors": [self.supervisor_a.get_status(), self.supervisor_b.get_status()],
                "arch_activity": arch_activity,
                "recent_events": recent_events
            }
