"""
Architecture #3: DE-CENTRALIZED
Autonomous Manipulator Agents with Private Valuation, Multi-Issue Utility Functions, and Concession Dynamics.
"""

import threading
import time
import math
from typing import Dict, List, Optional, Any
from src.core.models import (
    ArchitectureType,
    ResourceType,
    ConcessionStrategy,
    AgentStatus,
    NegotiationAction,
    NegotiationOffer,
    AgentTelemetry
)
from src.core.blackboard import BlackboardSharedState


class ManipulatorAgent:
    """
    Autonomous robotic manipulator arm agent operating with decentralized decision-making.
    Evaluates resource utilities using private mathematical preference weights and time discounting.
    """
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: str,
        cell_id: str,
        blackboard: BlackboardSharedState,
        concession_strategy: ConcessionStrategy = ConcessionStrategy.LINEAR,
        beta_concession: float = 1.0,
        budget_tokens: float = 150.0,
        reservation_utility: float = 0.40,
        weight_quantity: float = 0.45,
        weight_price: float = 0.35,
        weight_time: float = 0.20,
        standby_power_kw: float = 3.5
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.cell_id = cell_id
        self.blackboard = blackboard
        self.strategy = concession_strategy
        self.beta = beta_concession
        self.budget_tokens = budget_tokens
        self.reservation_utility = reservation_utility
        self.standby_power_kw = standby_power_kw
        
        # Multi-issue weights (sum = 1.0)
        self.w_q = weight_quantity
        self.w_p = weight_price
        self.w_t = weight_time
        
        self.status = AgentStatus.IDLE
        self.current_task: Optional[str] = None
        self.current_power_kw: float = standby_power_kw
        self.tools_held: List[str] = []
        self.compute_tokens_held: float = 20.0
        self.completed_cycles: int = 0
        self.active_architecture = ArchitectureType.DECENTRALIZED
        self._lock = threading.RLock()
        
        # Local Telemetry & Negotiation Logs
        self.private_valuation_factors = {
            ResourceType.GRID_POWER_KW: 1.5,
            ResourceType.HIGH_RES_LASER_TOOL: 10.0,
            ResourceType.ULTRA_TORQUE_DRIVER: 7.5,
            ResourceType.GPU_COMPUTE_TOKENS: 2.5,
            ResourceType.BUFFER_STAGE_ZONE: 3.5
        }

    def compute_utility(self, quantity: float, max_qty: float, price: float, max_price: float, current_round: int, max_rounds: int, is_buyer: bool = True) -> float:
        """
        Calculates private multi-issue utility U(Q, P, t).
        """
        q_ratio = min(1.0, max(0.0, quantity / max(1.0, max_qty)))
        p_ratio = min(1.0, max(0.0, price / max(1.0, max_price)))
        t_ratio = min(1.0, max(0.0, current_round / max(1, max_rounds)))
        
        # Time discount with concession exponent beta
        time_penalty = math.pow(t_ratio, self.beta)
        
        if is_buyer:
            # Buyer prefers higher quantity and lower price
            utility = (self.w_q * q_ratio) + (self.w_p * (1.0 - p_ratio)) - (self.w_t * time_penalty)
        else:
            # Seller prefers higher price and giving less quantity
            utility = (self.w_q * (1.0 - q_ratio)) + (self.w_p * p_ratio) - (self.w_t * time_penalty)
            
        return max(0.0, min(1.0, utility))

    def evaluate_offer(self, offer: NegotiationOffer, max_rounds: int = 10, is_buyer: bool = True) -> NegotiationAction:
        """
        Decentralized decision rule: Accept if utility exceeds dynamic reservation threshold, else counter or escalate.
        """
        with self._lock:
            max_qty = offer.quantity * 1.5
            max_price = offer.price_tokens * 1.8
            
            u_current = self.compute_utility(
                quantity=offer.quantity,
                max_qty=max_qty,
                price=offer.price_tokens,
                max_price=max_price,
                current_round=offer.round_idx,
                max_rounds=max_rounds,
                is_buyer=is_buyer
            )
            
            # Dynamic reservation threshold lowers as deadline looms
            time_factor = (offer.round_idx / max_rounds) ** self.beta
            dynamic_reservation = self.reservation_utility * (1.0 - 0.3 * time_factor)
            
            if u_current >= dynamic_reservation:
                return NegotiationAction.ACCEPT
            elif offer.round_idx >= max_rounds:
                # Deadlock -> Escalate to Cell Supervisor
                return NegotiationAction.ESCALATE_TO_SUPERVISOR
            else:
                return NegotiationAction.COUNTER_PROPOSE

    def generate_counter_offer(self, previous_offer: NegotiationOffer, max_rounds: int = 10, is_buyer: bool = True) -> NegotiationOffer:
        """
        Formulates game-theoretic counter-proposal applying concession curve.
        """
        with self._lock:
            round_idx = previous_offer.round_idx + 1
            t_ratio = min(1.0, round_idx / max_rounds)
            concession = math.pow(t_ratio, self.beta)
            
            if is_buyer:
                # Buyer concedes by increasing price offer towards seller's ask
                delta_price = (previous_offer.price_tokens * 1.3 - previous_offer.price_tokens) * concession * 0.5
                new_price = round(previous_offer.price_tokens + delta_price, 2)
                new_qty = previous_offer.quantity
            else:
                # Seller concedes by discounting price slightly towards buyer's bid
                delta_price = (previous_offer.price_tokens * 0.25) * concession
                new_price = round(max(1.0, previous_offer.price_tokens - delta_price), 2)
                new_qty = previous_offer.quantity
            
            u_self = self.compute_utility(
                quantity=new_qty,
                max_qty=new_qty * 1.5,
                price=new_price,
                max_price=new_price * 1.8,
                current_round=round_idx,
                max_rounds=max_rounds,
                is_buyer=is_buyer
            )
            
            return NegotiationOffer(
                offer_id=f"OFFER-{int(time.time()*1000)}-{self.agent_id}",
                round_idx=round_idx,
                sender_id=self.agent_id,
                receiver_id=previous_offer.sender_id,
                resource_type=previous_offer.resource_type,
                quantity=new_qty,
                duration_sec=previous_offer.duration_sec,
                price_tokens=new_price,
                utility_sender=round(u_self, 3),
                utility_receiver_est=round(1.0 - u_self * 0.7, 3),
                action=NegotiationAction.COUNTER_PROPOSE,
                notes=f"Counter with {self.strategy.value} strategy (beta={self.beta})"
            )

    def set_task(self, task_name: str, power_req_kw: float = 10.0, compute_req: float = 5.0):
        with self._lock:
            self.current_task = task_name
            self.current_power_kw = power_req_kw
            self.status = AgentStatus.EXECUTING

    def complete_task(self):
        with self._lock:
            self.status = AgentStatus.IDLE
            self.current_task = None
            self.current_power_kw = self.standby_power_kw
            self.completed_cycles += 1

    def get_telemetry(self) -> AgentTelemetry:
        with self._lock:
            return AgentTelemetry(
                agent_id=self.agent_id,
                name=self.name,
                role=self.role,
                cell_id=self.cell_id,
                status=self.status,
                current_task=self.current_task,
                power_draw_kw=self.current_power_kw,
                compute_tokens_held=self.compute_tokens_held,
                tools_held=list(self.tools_held),
                budget_tokens=self.budget_tokens,
                concession_strategy=self.strategy,
                beta_concession=self.beta,
                active_architecture=self.active_architecture,
                completed_cycles=self.completed_cycles
            )
