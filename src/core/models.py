"""
Data models and schema definitions for the 7-Architecture Multi-Agent Industrial Assembly System.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
import time


class ArchitectureType(str, Enum):
    CENTRALIZED = "CENTRALIZED"
    HIERARCHICAL = "HIERARCHICAL"
    DECENTRALIZED = "DECENTRALIZED"
    SEQUENTIAL_PIPELINE = "SEQUENTIAL | PIPELINE"
    PARALLEL = "PARALLEL"
    BLACKBOARD_SHARED_STATE = "BLACKBOARD | SHARED-STATE"
    PEER_TO_PEER = "PEER-TO-PEER"


class ResourceType(str, Enum):
    GRID_POWER_KW = "GRID_POWER_KW"
    HIGH_RES_LASER_TOOL = "HIGH_RES_LASER_TOOL"
    ULTRA_TORQUE_DRIVER = "ULTRA_TORQUE_DRIVER"
    GPU_COMPUTE_TOKENS = "GPU_COMPUTE_TOKENS"
    BUFFER_STAGE_ZONE = "BUFFER_STAGE_ZONE"


class ConcessionStrategy(str, Enum):
    BOULWARE = "BOULWARE"        # Beta < 1: Holds firm until deadline
    CONCEDER = "CONCEDER"        # Beta > 1: Concedes quickly to secure agreement
    LINEAR = "LINEAR"            # Beta = 1: Steady linear concession
    TIT_FOR_TAT = "TIT_FOR_TAT"  # Mirrors counterparty's concessions


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    REQUESTING = "REQUESTING"
    NEGOTIATING = "NEGOTIATING"
    EXECUTING = "EXECUTING"
    WAITING_RESOURCE = "WAITING_RESOURCE"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


class NegotiationAction(str, Enum):
    PROPOSE = "PROPOSE"
    COUNTER_PROPOSE = "COUNTER_PROPOSE"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    ESCALATE_TO_SUPERVISOR = "ESCALATE_TO_SUPERVISOR"
    SUPERVISOR_ARBITRATE = "SUPERVISOR_ARBITRATE"


class NegotiationOffer(BaseModel):
    offer_id: str
    round_idx: int
    sender_id: str
    receiver_id: str
    resource_type: ResourceType
    quantity: float
    duration_sec: float
    price_tokens: float
    utility_sender: float
    utility_receiver_est: float
    action: NegotiationAction
    notes: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)


class WorkpieceDataContract(BaseModel):
    """
    Data contract passed sequentially downstream across assembly stages.
    Enables feedforward compensation (Sequential/Pipeline architecture).
    """
    workpiece_id: str
    serial_no: str
    current_stage: str
    jig_alignment_err_mm: float = 0.0
    weld_penetration_mm: float = 0.0
    thermal_profile_c: float = 0.0
    sealant_viscosity_cp: float = 0.0
    applied_torque_nm: float = 0.0
    defect_compensation_offset_mm: float = 0.0
    metrology_pass: bool = True
    metadata: Dict[str, Any] = Field(default_factory=dict)
    history: List[str] = Field(default_factory=list)


class ArchitectureEvent(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    architecture: ArchitectureType
    source: str
    target: str
    action: str
    details: str
    impact: str = "NORMAL"


class AgentTelemetry(BaseModel):
    agent_id: str
    name: str
    role: str
    cell_id: str
    status: AgentStatus
    current_task: Optional[str] = None
    progress: float = 0.0
    power_draw_kw: float = 0.0
    compute_tokens_held: float = 0.0
    tools_held: List[str] = Field(default_factory=list)
    budget_tokens: float = 100.0
    utility_score: float = 1.0
    concession_strategy: ConcessionStrategy = ConcessionStrategy.LINEAR
    beta_concession: float = 1.0
    active_architecture: ArchitectureType = ArchitectureType.DECENTRALIZED
    completed_cycles: int = 0
