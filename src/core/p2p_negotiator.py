"""
Architecture #7: PEER-TO-PEER
Direct Bilateral Rubinstein Alternating Offers Protocol, Contract Net Protocol (CNP), and Pareto Frontier Analysis.
"""

import time
import math
from typing import Dict, List, Tuple, Optional, Any
from src.core.models import (
    ArchitectureType,
    ResourceType,
    NegotiationAction,
    NegotiationOffer
)
from src.core.decentralized_agent import ManipulatorAgent
from src.core.hierarchical_supervisor import CellSupervisorAgent
from src.core.blackboard import BlackboardSharedState
from src.core.centralized_arbiter import CentralizedRegistry


class P2PNegotiator:
    """
    Direct Peer-to-Peer negotiation engine implementing Rubinstein Alternating Offers Bargaining
    and Contract Net Protocol for bilateral resource transfer without centralized bottleneck.
    """
    def __init__(
        self,
        blackboard: BlackboardSharedState,
        central_arbiter: CentralizedRegistry,
        supervisor: Optional[CellSupervisorAgent] = None
    ):
        self.blackboard = blackboard
        self.central_arbiter = central_arbiter
        self.supervisor = supervisor

    def run_bilateral_negotiation(
        self,
        buyer: ManipulatorAgent,
        seller: ManipulatorAgent,
        resource_type: ResourceType,
        required_amount: float,
        initial_offer_price: float,
        duration_sec: float = 10.0,
        max_rounds: int = 8
    ) -> Dict[str, Any]:
        """
        Executes an alternating-offers negotiation dialogue between two robotic manipulator peers.
        """
        buyer.active_architecture = ArchitectureType.PEER_TO_PEER
        seller.active_architecture = ArchitectureType.PEER_TO_PEER
        
        rounds_history: List[NegotiationOffer] = []
        agreement_reached = False
        final_contract = None
        
        # Round 1: Buyer creates initial proposal
        u_init_buyer = buyer.compute_utility(
            quantity=required_amount,
            max_qty=required_amount * 1.5,
            price=initial_offer_price,
            max_price=initial_offer_price * 2.0,
            current_round=1,
            max_rounds=max_rounds,
            is_buyer=True
        )
        
        current_offer = NegotiationOffer(
            offer_id=f"P2P-OFFER-1-{buyer.agent_id}",
            round_idx=1,
            sender_id=buyer.agent_id,
            receiver_id=seller.agent_id,
            resource_type=resource_type,
            quantity=required_amount,
            duration_sec=duration_sec,
            price_tokens=initial_offer_price,
            utility_sender=round(u_init_buyer, 3),
            utility_receiver_est=0.50,
            action=NegotiationAction.PROPOSE,
            notes=f"Initial P2P proposal: {required_amount} {resource_type.value} @ {initial_offer_price} tokens"
        )
        rounds_history.append(current_offer)
        
        self.blackboard._record_event(
            ArchitectureType.PEER_TO_PEER,
            source=buyer.agent_id,
            target=seller.agent_id,
            action="P2P_PROPOSE",
            details=f"P2P Round 1: Propose {required_amount} {resource_type.value} for {initial_offer_price} tokens"
        )
        
        current_turn = "SELLER"
        
        for r_idx in range(1, max_rounds + 1):
            if current_turn == "SELLER":
                decision = seller.evaluate_offer(current_offer, max_rounds=max_rounds, is_buyer=False)
                
                if decision == NegotiationAction.ACCEPT:
                    agreement_reached = True
                    accept_offer = NegotiationOffer(
                        offer_id=f"P2P-ACCEPT-{r_idx}-{seller.agent_id}",
                        round_idx=r_idx,
                        sender_id=seller.agent_id,
                        receiver_id=buyer.agent_id,
                        resource_type=resource_type,
                        quantity=current_offer.quantity,
                        duration_sec=current_offer.duration_sec,
                        price_tokens=current_offer.price_tokens,
                        utility_sender=round(seller.compute_utility(current_offer.quantity, current_offer.quantity*1.5, current_offer.price_tokens, current_offer.price_tokens*2, r_idx, max_rounds, is_buyer=False), 3),
                        utility_receiver_est=current_offer.utility_sender,
                        action=NegotiationAction.ACCEPT,
                        notes="Seller accepted buyer offer."
                    )
                    rounds_history.append(accept_offer)
                    self.blackboard._record_event(
                        ArchitectureType.PEER_TO_PEER,
                        source=seller.agent_id,
                        target=buyer.agent_id,
                        action="P2P_ACCEPT",
                        details=f"P2P Deal Agreed in Round {r_idx}! {current_offer.quantity} {resource_type.value} @ {current_offer.price_tokens} tokens"
                    )
                    break
                elif decision == NegotiationAction.ESCALATE_TO_SUPERVISOR:
                    break
                else:
                    # Seller counters
                    counter = seller.generate_counter_offer(current_offer, max_rounds=max_rounds, is_buyer=False)
                    rounds_history.append(counter)
                    current_offer = counter
                    current_turn = "BUYER"
                    self.blackboard._record_event(
                        ArchitectureType.PEER_TO_PEER,
                        source=seller.agent_id,
                        target=buyer.agent_id,
                        action="P2P_COUNTER",
                        details=f"P2P Round {counter.round_idx}: Seller counters with price {counter.price_tokens} tokens"
                    )
            else:
                # BUYER's turn to evaluate seller's counter
                decision = buyer.evaluate_offer(current_offer, max_rounds=max_rounds, is_buyer=True)
                
                if decision == NegotiationAction.ACCEPT:
                    agreement_reached = True
                    accept_offer = NegotiationOffer(
                        offer_id=f"P2P-ACCEPT-{r_idx}-{buyer.agent_id}",
                        round_idx=r_idx,
                        sender_id=buyer.agent_id,
                        receiver_id=seller.agent_id,
                        resource_type=resource_type,
                        quantity=current_offer.quantity,
                        duration_sec=current_offer.duration_sec,
                        price_tokens=current_offer.price_tokens,
                        utility_sender=round(buyer.compute_utility(current_offer.quantity, current_offer.quantity*1.5, current_offer.price_tokens, current_offer.price_tokens*2, r_idx, max_rounds, is_buyer=True), 3),
                        utility_receiver_est=current_offer.utility_sender,
                        action=NegotiationAction.ACCEPT,
                        notes="Buyer accepted seller counter-offer."
                    )
                    rounds_history.append(accept_offer)
                    self.blackboard._record_event(
                        ArchitectureType.PEER_TO_PEER,
                        source=buyer.agent_id,
                        target=seller.agent_id,
                        action="P2P_ACCEPT",
                        details=f"P2P Deal Agreed in Round {r_idx}! {current_offer.quantity} {resource_type.value} @ {current_offer.price_tokens} tokens"
                    )
                    break
                elif decision == NegotiationAction.ESCALATE_TO_SUPERVISOR:
                    break
                else:
                    # Buyer counters
                    counter = buyer.generate_counter_offer(current_offer, max_rounds=max_rounds, is_buyer=True)
                    rounds_history.append(counter)
                    current_offer = counter
                    current_turn = "SELLER"
                    self.blackboard._record_event(
                        ArchitectureType.PEER_TO_PEER,
                        source=buyer.agent_id,
                        target=seller.agent_id,
                        action="P2P_COUNTER",
                        details=f"P2P Round {counter.round_idx}: Buyer counters with price {counter.price_tokens} tokens"
                    )

        # If deadlock and supervisor is available -> Escalate (Hierarchical Resolution)
        arbitrated = False
        if not agreement_reached and self.supervisor:
            self.blackboard._record_event(
                ArchitectureType.HIERARCHICAL,
                source=f"{buyer.agent_id}+{seller.agent_id}",
                target=self.supervisor.supervisor_id,
                action="ESCALATE_DISPUTE",
                details=f"P2P Deadlock after {len(rounds_history)} rounds. Escalated to Cell Supervisor."
            )
            arb_offer = self.supervisor.arbitrate_deadlock(rounds_history)
            rounds_history.append(arb_offer)
            current_offer = arb_offer
            agreement_reached = True
            arbitrated = True

        # Commit contract to Centralized Registry if settled
        if agreement_reached:
            # Transfer tokens & update budgets
            cost = current_offer.price_tokens
            buyer.budget_tokens -= cost
            seller.budget_tokens += cost
            
            final_contract = {
                "sender_id": buyer.agent_id,
                "receiver_id": seller.agent_id,
                "resource_type": resource_type.value,
                "quantity": current_offer.quantity,
                "price_tokens": current_offer.price_tokens,
                "duration_sec": current_offer.duration_sec,
                "arbitrated": arbitrated,
                "total_rounds": len(rounds_history)
            }
            # Register with Centralized Architecture
            self.central_arbiter.commit_contract(final_contract)
            
        pareto_analysis = self.calculate_pareto_frontier(buyer, seller, resource_type, required_amount)
        
        return {
            "success": agreement_reached,
            "arbitrated": arbitrated,
            "final_offer": current_offer.model_dump(),
            "rounds_count": len(rounds_history),
            "history": [o.model_dump() for o in rounds_history],
            "buyer_final_budget": round(buyer.budget_tokens, 2),
            "seller_final_budget": round(seller.budget_tokens, 2),
            "pareto_analysis": pareto_analysis
        }

    def calculate_pareto_frontier(
        self,
        buyer: ManipulatorAgent,
        seller: ManipulatorAgent,
        resource_type: ResourceType,
        quantity: float,
        price_samples: int = 25
    ) -> Dict[str, Any]:
        """
        Computes Pareto efficiency curve and Nash Bargaining Solution.
        """
        min_p = 5.0
        max_p = 50.0
        step = (max_p - min_p) / price_samples
        
        points = []
        best_nash_prod = -1.0
        nash_solution = None
        
        for i in range(price_samples + 1):
            p = min_p + i * step
            u_b = buyer.compute_utility(quantity, quantity*1.5, p, max_p*1.5, 1, 10, is_buyer=True)
            u_s = seller.compute_utility(quantity, quantity*1.5, p, max_p*1.5, 1, 10, is_buyer=False)
            
            # Nash Product = (U_b - U_reserve_b) * (U_s - U_reserve_s)
            surplus_b = max(0.0, u_b - buyer.reservation_utility)
            surplus_s = max(0.0, u_s - seller.reservation_utility)
            nash_prod = surplus_b * surplus_s
            
            point = {
                "price": round(p, 2),
                "buyer_utility": round(u_b, 3),
                "seller_utility": round(u_s, 3),
                "nash_product": round(nash_prod, 4)
            }
            points.append(point)
            
            if nash_prod > best_nash_prod:
                best_nash_prod = nash_prod
                nash_solution = point
                
        return {
            "frontier_points": points,
            "nash_equilibrium": nash_solution,
            "reservation_buyer": buyer.reservation_utility,
            "reservation_seller": seller.reservation_utility
        }
