"""
Architecture #1: CENTRALIZED
Global Factory Arbiter, Centralized Resource Registry, Safety Interlock, and Ledger Audit.
"""

import threading
import time
from typing import Dict, List, Optional, Any
from src.core.models import ArchitectureType, ArchitectureEvent, ResourceType
from src.core.blackboard import BlackboardSharedState


class CentralizedRegistry:
    """
    Centralized Authority managing global constraints, factory power limits,
    safety interlocks, and master contract audit logging.
    """
    def __init__(self, blackboard: BlackboardSharedState, max_grid_power_kw: float = 100.0):
        self.blackboard = blackboard
        self.max_grid_power_kw = max_grid_power_kw
        self.total_power_draw_kw: float = 0.0
        self._lock = threading.RLock()
        
        # Centralized Tool Inventory & Status
        self.master_tool_registry = {
            ResourceType.HIGH_RES_LASER_TOOL.value: {"total": 1, "available": 1, "holder": None},
            ResourceType.ULTRA_TORQUE_DRIVER.value: {"total": 1, "available": 1, "holder": None},
            ResourceType.GPU_COMPUTE_TOKENS.value: {"total": 100, "allocated": 0},
            ResourceType.BUFFER_STAGE_ZONE.value: {"total": 4, "occupied": 0}
        }
        
        # Centralized Signed Contract Audit Ledger
        self.contract_ledger: List[Dict[str, Any]] = []
        self.emergency_halt: bool = False
        self.total_contracts_executed: int = 0
        self.total_tokens_transacted: float = 0.0

    def register_power_allocation(self, agent_id: str, requested_kw: float) -> bool:
        """
        Safety interlock: verifies if requested power keeps the factory under the 100kW safety limit.
        """
        with self._lock:
            if self.emergency_halt:
                return False
            
            projected_power = self.total_power_draw_kw + requested_kw
            if projected_power <= self.max_grid_power_kw:
                self.total_power_draw_kw = projected_power
                self.blackboard._record_event(
                    ArchitectureType.CENTRALIZED,
                    source="CENTRAL_ARBITER",
                    target=agent_id,
                    action="POWER_APPROVED",
                    details=f"Approved +{requested_kw} kW for {agent_id}. Factory load: {self.total_power_draw_kw:.1f}/{self.max_grid_power_kw} kW"
                )
                return True
            else:
                self.blackboard._record_event(
                    ArchitectureType.CENTRALIZED,
                    source="CENTRAL_ARBITER",
                    target=agent_id,
                    action="POWER_DENIED_OVERLOAD",
                    details=f"Denied +{requested_kw} kW for {agent_id}. Exceeds safety envelope ({projected_power:.1f} > {self.max_grid_power_kw} kW)",
                    impact="CRITICAL"
                )
                return False

    def release_power(self, agent_id: str, kw_amount: float):
        with self._lock:
            self.total_power_draw_kw = max(0.0, self.total_power_draw_kw - kw_amount)
            self.blackboard._record_event(
                ArchitectureType.CENTRALIZED,
                source=agent_id,
                target="CENTRAL_ARBITER",
                action="POWER_RELEASED",
                details=f"Released {kw_amount} kW from {agent_id}. New factory load: {self.total_power_draw_kw:.1f} kW"
            )

    def commit_contract(self, contract_data: Dict[str, Any]) -> bool:
        """
        Non-repudiation registration: Central authority validates and registers bilateral P2P deals.
        """
        with self._lock:
            contract_id = f"CTR-CENTRAL-{int(time.time()*1000)}-{len(self.contract_ledger)+1}"
            contract_record = {
                "contract_id": contract_id,
                "timestamp": time.time(),
                "agent_a": contract_data.get("sender_id"),
                "agent_b": contract_data.get("receiver_id"),
                "resource_type": contract_data.get("resource_type"),
                "quantity": contract_data.get("quantity"),
                "price_tokens": contract_data.get("price_tokens"),
                "status": "COMMITTED_IN_LEDGER"
            }
            self.contract_ledger.append(contract_record)
            self.total_contracts_executed += 1
            self.total_tokens_transacted += contract_data.get("price_tokens", 0.0)
            
            self.blackboard._record_event(
                ArchitectureType.CENTRALIZED,
                source="CENTRAL_LEDGER",
                target=f"{contract_data.get('sender_id')}<->{contract_data.get('receiver_id')}",
                action="REGISTER_CONTRACT",
                details=f"Ledger committed contract {contract_id}: {contract_data.get('quantity')} {contract_data.get('resource_type')} @ {contract_data.get('price_tokens')} tokens"
            )
            return True

    def trigger_emergency_estop(self, reason: str):
        with self._lock:
            self.emergency_halt = True
            self.total_power_draw_kw = 0.0
            self.blackboard._record_event(
                ArchitectureType.CENTRALIZED,
                source="CENTRAL_ARBITER",
                target="ALL_MANIPULATORS",
                action="EMERGENCY_ESTOP",
                details=f"GLOBAL SAFETY HALT ACTIVATED! Reason: {reason}",
                impact="EMERGENCY"
            )
            self.blackboard.publish("emergency_halt", {"reason": reason, "timestamp": time.time()})

    def reset_estop(self):
        with self._lock:
            self.emergency_halt = False
            self.blackboard._record_event(
                ArchitectureType.CENTRALIZED,
                source="CENTRAL_ARBITER",
                target="ALL_MANIPULATORS",
                action="RESET_ESTOP",
                details="Global safety interlocks reset. Operations resuming."
            )

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "max_power_limit_kw": self.max_grid_power_kw,
                "current_power_draw_kw": round(self.total_power_draw_kw, 1),
                "power_utilization_pct": round((self.total_power_draw_kw / self.max_grid_power_kw) * 100, 1),
                "emergency_halt": self.emergency_halt,
                "contracts_registered": self.total_contracts_executed,
                "total_tokens_transacted": round(self.total_tokens_transacted, 2),
                "master_tool_registry": self.master_tool_registry
            }
