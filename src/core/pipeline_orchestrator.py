"""
Architecture #4: SEQUENTIAL | PIPELINE
Sequential Assembly Line Orchestration, Workpiece Data Contracts, and Feedforward Defect Compensation.
"""

import threading
import time
import random
from typing import Dict, List, Optional, Any
from src.core.models import (
    ArchitectureType,
    WorkpieceDataContract,
    ResourceType
)
from src.core.decentralized_agent import ManipulatorAgent
from src.core.blackboard import BlackboardSharedState


class AssemblyPipelineEngine:
    """
    Sequential Pipeline Engine orchestrating linear assembly line operations.
    Transfers rich workpiece data contracts from upstream to downstream manipulator agents.
    """
    def __init__(self, agents_pipeline: List[ManipulatorAgent], blackboard: BlackboardSharedState):
        self.pipeline = agents_pipeline  # Ordered list: [M1, M2, M3, M4, M5, M6]
        self.blackboard = blackboard
        self._lock = threading.RLock()
        self.active_workpieces: Dict[str, WorkpieceDataContract] = {}
        self.completed_workpieces: List[WorkpieceDataContract] = []
        self.pipeline_stage_names = [
            "1_INFEED_ALIGNMENT",
            "2_PRECISION_WELDING",
            "3_SEALANT_DISPENSE",
            "4_TORQUE_FASTENING",
            "5_OPTICAL_METROLOGY",
            "6_OUTFEED_PALLETIZING"
        ]

    def spawn_workpiece(self, serial_prefix: str = "WP-AUTO") -> WorkpieceDataContract:
        """
        Injects a new raw workpiece onto the assembly pipeline infeed.
        """
        with self._lock:
            wp_id = f"{serial_prefix}-{int(time.time()*1000) % 100000:05d}"
            # Introduce realistic micro-variance in raw jig alignment (e.g. +/- 0.15 mm)
            initial_jig_err = round(random.uniform(-0.18, 0.18), 3)
            
            wp = WorkpieceDataContract(
                workpiece_id=wp_id,
                serial_no=f"SN-{random.randint(100000, 999999)}",
                current_stage=self.pipeline_stage_names[0],
                jig_alignment_err_mm=initial_jig_err,
                history=[f"Spawned at infeed with initial jig variance: {initial_jig_err:+.3f} mm"]
            )
            self.active_workpieces[wp_id] = wp
            
            self.blackboard._record_event(
                ArchitectureType.SEQUENTIAL_PIPELINE,
                source="PIPELINE_INFEED",
                target=self.pipeline[0].agent_id,
                action="SPAWN_WORKPIECE",
                details=f"Injected workpiece {wp_id} onto Stage 1 (Jig Err: {initial_jig_err:+.3f} mm)"
            )
            return wp

    def advance_stage(self, workpiece_id: str) -> Dict[str, Any]:
        """
        Executes one sequential pipeline step for the specified workpiece,
        passing data contracts downstream with adaptive feedforward compensation.
        """
        with self._lock:
            if workpiece_id not in self.active_workpieces:
                return {"error": f"Workpiece {workpiece_id} not found."}
            
            wp = self.active_workpieces[workpiece_id]
            current_idx = self.pipeline_stage_names.index(wp.current_stage)
            current_agent = self.pipeline[current_idx]
            
            # 1. Current Agent processes workpiece
            current_agent.active_architecture = ArchitectureType.SEQUENTIAL_PIPELINE
            current_agent.set_task(f"Process {wp.current_stage} on {workpiece_id}", power_req_kw=12.0)
            
            # 2. Update telemetry & physical metrics depending on stage
            notes = ""
            if current_idx == 0:  # M1 Infeed Loader
                wp.history.append(f"M1 clamped workpiece. Measured alignment error: {wp.jig_alignment_err_mm:+.3f} mm")
                notes = f"Clamped. Alignment offset: {wp.jig_alignment_err_mm:+.3f} mm"
                
            elif current_idx == 1:  # M2 Precision Welder
                # Weld creates thermal heat and depth
                wp.weld_penetration_mm = round(2.5 + random.uniform(-0.1, 0.1), 3)
                wp.thermal_profile_c = round(185.0 + random.uniform(-10.0, 15.0), 1)
                wp.history.append(f"M2 performed laser weld: penetration={wp.weld_penetration_mm}mm, temp={wp.thermal_profile_c}°C")
                notes = f"Welded: {wp.weld_penetration_mm}mm penetration, {wp.thermal_profile_c}°C"
                
            elif current_idx == 2:  # M3 Sealant Dispenser (Uses feedforward data from M2 weld thermal profile)
                # Downstream adaptive compensation:
                # If thermal profile is high (>190C), viscosity decreases -> adapt dispenser feed rate
                viscosity_adj = 320.0 - (wp.thermal_profile_c - 180.0) * 1.5
                wp.sealant_viscosity_cp = round(max(250.0, viscosity_adj), 1)
                # Compensate for jig alignment error
                wp.defect_compensation_offset_mm = round(-wp.jig_alignment_err_mm * 0.95, 3)
                wp.history.append(f"M3 adapted bead trajectory by {wp.defect_compensation_offset_mm:+.3f}mm to counter jig error")
                notes = f"Sealant applied: {wp.sealant_viscosity_cp} cP (Compensated {wp.defect_compensation_offset_mm:+.3f}mm)"
                
            elif current_idx == 3:  # M4 Bolt Fastener
                # Applies torque signature adapted to thermal state
                base_torque = 14.5
                wp.applied_torque_nm = round(base_torque + random.uniform(-0.3, 0.3), 2)
                wp.history.append(f"M4 torqued bolts to {wp.applied_torque_nm} Nm")
                notes = f"Torqued: {wp.applied_torque_nm} Nm"
                
            elif current_idx == 4:  # M5 Optical Metrology
                # Measures residual tolerance
                residual_tolerance = abs(wp.jig_alignment_err_mm + wp.defect_compensation_offset_mm)
                wp.metrology_pass = residual_tolerance < 0.05
                wp.history.append(f"M5 Metrology scan: Residual err = {residual_tolerance:.4f}mm (Pass: {wp.metrology_pass})")
                notes = f"Inspection: {'PASS' if wp.metrology_pass else 'REJECT'} (Residual: {residual_tolerance:.4f}mm)"
                
            elif current_idx == 5:  # M6 Outfeed Palletizer
                wp.history.append(f"M6 packaged and palletized workpiece {wp.workpiece_id}")
                notes = "Palletized and staged for shipping"

            current_agent.complete_task()
            
            # Check if pipeline stage completes or advances
            if current_idx + 1 < len(self.pipeline_stage_names):
                next_stage = self.pipeline_stage_names[current_idx + 1]
                next_agent = self.pipeline[current_idx + 1]
                
                # Sequential Data Handoff Contract
                self.blackboard._record_event(
                    ArchitectureType.SEQUENTIAL_PIPELINE,
                    source=current_agent.agent_id,
                    target=next_agent.agent_id,
                    action="DATA_CONTRACT_HANDOFF",
                    details=f"Passed Workpiece Contract {wp.workpiece_id} from {wp.current_stage} -> {next_stage}. ({notes})"
                )
                wp.current_stage = next_stage
                return {
                    "status": "ADVANCED",
                    "workpiece_id": wp.workpiece_id,
                    "completed_stage": self.pipeline_stage_names[current_idx],
                    "next_stage": next_stage,
                    "data_contract": wp.model_dump()
                }
            else:
                # Reached end of pipeline
                wp.current_stage = "COMPLETED"
                self.completed_workpieces.append(wp)
                del self.active_workpieces[workpiece_id]
                
                self.blackboard._record_event(
                    ArchitectureType.SEQUENTIAL_PIPELINE,
                    source=current_agent.agent_id,
                    target="WAREHOUSE",
                    action="PIPELINE_COMPLETE",
                    details=f"Workpiece {wp.workpiece_id} successfully finished all 6 assembly stages!"
                )
                return {
                    "status": "COMPLETED",
                    "workpiece_id": wp.workpiece_id,
                    "data_contract": wp.model_dump()
                }

    def get_pipeline_snapshot(self) -> List[Dict[str, Any]]:
        with self._lock:
            status_list = []
            for i, stage_name in enumerate(self.pipeline_stage_names):
                agent = self.pipeline[i]
                wps_at_stage = [wp for wp in self.active_workpieces.values() if wp.current_stage == stage_name]
                status_list.append({
                    "stage_index": i + 1,
                    "stage_name": stage_name,
                    "agent_id": agent.agent_id,
                    "agent_role": agent.role,
                    "active_workpiece": wps_at_stage[0].workpiece_id if wps_at_stage else None,
                    "agent_status": agent.status.value
                })
            return status_list
