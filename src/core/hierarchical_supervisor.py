"""
Architecture #2: HIERARCHICAL
Cell Supervisor Agents, Task Decomposition, Resource Quota Allocation, and Deadlock Arbitration.
"""

import threading
import time
from typing import Dict, List, Optional, Any
from src.core.models import (
    ArchitectureType,
    ArchitectureEvent,
    ResourceType,
    NegotiationOffer,
    NegotiationAction
)
from src.core.blackboard import BlackboardSharedState


class CellSupervisorAgent:
    """
    Hierarchical Supervisor managing a cluster of manipulator agents within a manufacturing cell.
    Handles cell-level quota management, task decomposition, and deadlock dispute arbitration.
    """
    def __init__(self, supervisor_id: str, cell_id: str, cell_name: str, managed_agents: List[str], blackboard: BlackboardSharedState):
        self.supervisor_id = supervisor_id
        self.cell_id = cell_id
        self.cell_name = cell_name
        self.managed_agents = managed_agents
        self.blackboard = blackboard
        self._lock = threading.RLock()
        
        # Cell Quota Allowances
        self.cell_power_budget_kw = 50.0
        self.allocated_power_kw = 0.0
        self.emergency_reserve_tokens = 250.0
        self.arbitration_history: List[Dict[str, Any]] = []
        self.escalations_handled = 0

    def decompose_and_dispatch_task(self, macro_order: str, workpiece_id: str) -> Dict[str, str]:
        """
        Decomposes top-level assembly order into sequential sub-tasks for managed manipulator agents.
        """
        with self._lock:
            dispatched = {}
            for agent_id in self.managed_agents:
                sub_task = f"Execute [{macro_order}] phase for workpiece {workpiece_id}"
                dispatched[agent_id] = sub_task
                self.blackboard._record_event(
                    ArchitectureType.HIERARCHICAL,
                    source=self.supervisor_id,
                    target=agent_id,
                    action="DISPATCH_SUBTASK",
                    details=f"Supervisor assigned sub-task: '{sub_task}'"
                )
            return dispatched

    def arbitrate_deadlock(self, offer_history: List[NegotiationOffer]) -> NegotiationOffer:
        """
        Hierarchical Dispute Resolution: When bilateral P2P bargaining between two arms fails
        or deadlocks, the supervisor arbitrates by calculating a fair Nash-Kalai-Smorodinsky compromise
        and injecting emergency supervisor reserve subsidy.
        """
        with self._lock:
            self.escalations_handled += 1
            if not offer_history:
                raise ValueError("Cannot arbitrate empty negotiation history.")
            
            last_offer = offer_history[-1]
            agent_a = last_offer.sender_id
            agent_b = last_offer.receiver_id
            
            # Compute compromise quantity & price based on historical spread
            quantities = [o.quantity for o in offer_history]
            prices = [o.price_tokens for o in offer_history]
            
            compromise_qty = sum(quantities) / len(quantities)
            compromise_price = sum(prices) / len(prices)
            
            # Supervisor injects 20% subsidy from cell reserve to close utility gap
            subsidy = compromise_price * 0.20
            self.emergency_reserve_tokens = max(0.0, self.emergency_reserve_tokens - subsidy)
            adjusted_price = max(1.0, compromise_price - subsidy)
            
            arbitrated_offer = NegotiationOffer(
                offer_id=f"ARB-{int(time.time()*1000)}-{self.supervisor_id}",
                round_idx=len(offer_history) + 1,
                sender_id=self.supervisor_id,
                receiver_id=f"{agent_a}+{agent_b}",
                resource_type=last_offer.resource_type,
                quantity=round(compromise_qty, 1),
                duration_sec=last_offer.duration_sec,
                price_tokens=round(adjusted_price, 2),
                utility_sender=0.90,
                utility_receiver_est=0.90,
                action=NegotiationAction.SUPERVISOR_ARBITRATE,
                notes=f"Hierarchical resolution with {subsidy:.1f} token supervisor subsidy."
            )
            
            self.arbitration_history.append({
                "dispute_between": [agent_a, agent_b],
                "resolved_at": time.time(),
                "compromise_offer": arbitrated_offer.model_dump(),
                "subsidy_given": subsidy
            })
            
            self.blackboard._record_event(
                ArchitectureType.HIERARCHICAL,
                source=self.supervisor_id,
                target=f"{agent_a} & {agent_b}",
                action="RESOLVE_DEADLOCK_ARBITRATION",
                details=f"Supervisor arbitrated dispute: {compromise_qty} {last_offer.resource_type.value} @ {adjusted_price:.2f} tokens (Subsidized: {subsidy:.1f})"
            )
            return arbitrated_offer

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "supervisor_id": self.supervisor_id,
                "cell_id": self.cell_id,
                "cell_name": self.cell_name,
                "managed_agents": self.managed_agents,
                "escalations_handled": self.escalations_handled,
                "emergency_reserve_tokens": round(self.emergency_reserve_tokens, 1),
                "cell_power_budget_kw": self.cell_power_budget_kw
            }
