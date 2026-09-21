"""
Game-theoretic negotiation and Pareto efficiency test suite.
"""

import pytest
from src.core.models import (
    ResourceType,
    ConcessionStrategy,
    NegotiationAction
)
from src.core.decentralized_agent import ManipulatorAgent
from src.core.p2p_negotiator import P2PNegotiator
from src.core.blackboard import BlackboardSharedState
from src.core.centralized_arbiter import CentralizedRegistry
from src.core.hierarchical_supervisor import CellSupervisorAgent


@pytest.fixture
def test_setup():
    bb = BlackboardSharedState()
    central = CentralizedRegistry(bb, max_grid_power_kw=100.0)
    sup = CellSupervisorAgent("SUP_TEST", "CELL_TEST", "Test Cell", ["A1", "A2"], bb)
    
    agent_a = ManipulatorAgent(
        agent_id="ARM_A",
        name="Arm A (Boulware)",
        role="Test Buyer",
        cell_id="CELL_TEST",
        blackboard=bb,
        concession_strategy=ConcessionStrategy.BOULWARE,
        beta_concession=0.3,
        budget_tokens=200.0
    )
    
    agent_b = ManipulatorAgent(
        agent_id="ARM_B",
        name="Arm B (Conceder)",
        role="Test Seller",
        cell_id="CELL_TEST",
        blackboard=bb,
        concession_strategy=ConcessionStrategy.CONCEDER,
        beta_concession=2.0,
        budget_tokens=200.0
    )
    
    negotiator = P2PNegotiator(bb, central, sup)
    return agent_a, agent_b, negotiator, central


def test_rubinstein_concession_agreement(test_setup):
    agent_a, agent_b, negotiator, central = test_setup
    
    res = negotiator.run_bilateral_negotiation(
        buyer=agent_a,
        seller=agent_b,
        resource_type=ResourceType.GRID_POWER_KW,
        required_amount=15.0,
        initial_offer_price=10.0,
        max_rounds=10
    )
    
    assert res["success"] is True
    assert res["rounds_count"] <= 10
    # Token budgets updated correctly
    agreed_price = res["final_offer"]["price_tokens"]
    assert agent_a.budget_tokens == 200.0 - agreed_price
    assert agent_b.budget_tokens == 200.0 + agreed_price
    assert central.total_contracts_executed == 1


def test_pareto_frontier_calculation(test_setup):
    agent_a, agent_b, negotiator, _ = test_setup
    
    pareto = negotiator.calculate_pareto_frontier(
        buyer=agent_a,
        seller=agent_b,
        resource_type=ResourceType.GPU_COMPUTE_TOKENS,
        quantity=10.0,
        price_samples=20
    )
    
    assert "frontier_points" in pareto
    assert len(pareto["frontier_points"]) == 21
    assert "nash_equilibrium" in pareto
    assert pareto["nash_equilibrium"] is not None
    assert pareto["nash_equilibrium"]["nash_product"] >= 0.0


def test_utility_function_bounds(test_setup):
    agent_a, _, _, _ = test_setup
    # Utility must always stay within [0.0, 1.0]
    u1 = agent_a.compute_utility(10, 10, 5, 50, 1, 10, is_buyer=True)
    u2 = agent_a.compute_utility(0, 10, 50, 50, 10, 10, is_buyer=True)
    u3 = agent_a.compute_utility(20, 10, 0, 50, 1, 10, is_buyer=True)
    
    assert 0.0 <= u1 <= 1.0
    assert 0.0 <= u2 <= 1.0
    assert 0.0 <= u3 <= 1.0
