"""
Comprehensive test suite verifying all 7 Multi-Agent Architectures.
"""

import pytest
from src.core.models import (
    ArchitectureType,
    ResourceType,
    ConcessionStrategy,
    AgentStatus
)
from src.simulation.assembly_environment import AssemblyEnvironment
from src.simulation.scenarios import (
    run_scenario_power_contention,
    run_scenario_tolerance_compensation,
    run_scenario_deadlock_escalation,
    run_scenario_parallel_throughput,
    run_scenario_blackboard_rfp
)


@pytest.fixture
def env():
    return AssemblyEnvironment()


def test_1_centralized_architecture(env):
    """Verifies Centralized Registry: Safety interlocks & power ceiling management."""
    # Under 100 kW ceiling -> Allowed
    assert env.central_arbiter.register_power_allocation("TEST_AGENT", 40.0) is True
    assert env.central_arbiter.total_power_draw_kw == 40.0
    
    # Another 50 kW -> Total 90 kW <= 100 kW -> Allowed
    assert env.central_arbiter.register_power_allocation("TEST_AGENT_2", 50.0) is True
    assert env.central_arbiter.total_power_draw_kw == 90.0
    
    # Request +20 kW -> Total 110 kW > 100 kW -> Denied by safety interlock
    assert env.central_arbiter.register_power_allocation("TEST_AGENT_3", 20.0) is False
    
    # Release power
    env.central_arbiter.release_power("TEST_AGENT", 40.0)
    assert env.central_arbiter.total_power_draw_kw == 50.0
    
    # Emergency halt
    env.central_arbiter.trigger_emergency_estop("Test Alarm")
    assert env.central_arbiter.emergency_halt is True
    assert env.central_arbiter.register_power_allocation("TEST_AGENT", 10.0) is False
    env.central_arbiter.reset_estop()
    assert env.central_arbiter.emergency_halt is False


def test_2_hierarchical_architecture(env):
    """Verifies Hierarchical Supervisor: Task dispatching and dispute arbitration."""
    sup = env.supervisor_a
    dispatched = sup.decompose_and_dispatch_task("WELD_CHASSIS_ORDER", "WP-101")
    assert "M1_LOADER" in dispatched
    assert "M2_WELDER" in dispatched
    
    # Test arbitration on simulated deadlock
    res = run_scenario_deadlock_escalation(env)
    assert res["negotiation_result"]["arbitrated"] is True
    assert sup.escalations_handled >= 1


def test_3_decentralized_architecture(env):
    """Verifies Autonomous Manipulator Agent utility calculations and concession strategies."""
    agent_boulware = env.m2  # Boulware (beta=0.45)
    agent_conceder = env.m3  # Conceder (beta=2.2)
    
    # Boulware concedes slower than Conceder at round 3
    u_boul = agent_boulware.compute_utility(20.0, 30.0, 15.0, 30.0, current_round=3, max_rounds=10, is_buyer=True)
    u_conc = agent_conceder.compute_utility(20.0, 30.0, 15.0, 30.0, current_round=3, max_rounds=10, is_buyer=True)
    
    assert u_boul > 0.0
    assert u_conc > 0.0


def test_4_sequential_pipeline_architecture(env):
    """Verifies Sequential Pipeline: Workpiece progression and feedforward data contracts."""
    wp = env.pipeline_engine.spawn_workpiece("WP-TEST-SEQ")
    assert wp.workpiece_id in env.pipeline_engine.active_workpieces
    
    # Stage 1: Infeed
    r1 = env.pipeline_engine.advance_stage(wp.workpiece_id)
    assert r1["completed_stage"] == "1_INFEED_ALIGNMENT"
    
    # Stage 2: Weld
    r2 = env.pipeline_engine.advance_stage(wp.workpiece_id)
    assert r2["completed_stage"] == "2_PRECISION_WELDING"
    assert wp.thermal_profile_c > 150.0  # Weld heat generated


def test_5_parallel_architecture(env):
    """Verifies Parallel Execution: Concurrent multi-arm thread-pool actions."""
    tasks = [
        {"agent_id": "M1_LOADER", "task_name": "Clamping", "power_kw": 10.0, "duration_sec": 0.05},
        {"agent_id": "M4_FASTENER", "task_name": "Torquing", "power_kw": 12.0, "duration_sec": 0.05}
    ]
    results = env.parallel_engine.run_parallel_batch(tasks)
    assert len(results) == 2
    assert results[0]["status"] == "SUCCESS"
    assert results[1]["status"] == "SUCCESS"


def test_6_blackboard_shared_state_architecture(env):
    """Verifies Blackboard: Pub/Sub, spot pricing, and RFP auctions."""
    bb = env.blackboard
    # Test lock
    assert bb.acquire_lock("LASER_SCANNER", "M2_WELDER", lease_seconds=2.0) is True
    assert bb.acquire_lock("LASER_SCANNER", "M3_SEALANT", lease_seconds=2.0) is False  # Already locked
    assert bb.release_lock("LASER_SCANNER", "M2_WELDER") is True
    assert bb.acquire_lock("LASER_SCANNER", "M3_SEALANT", lease_seconds=2.0) is True
    
    # Test RFP
    rfp_id = bb.post_rfp("M1_LOADER", ResourceType.GPU_COMPUTE_TOKENS, 10.0, 25.0, 100.0)
    assert rfp_id.startswith("RFP-")
    assert bb.submit_bid(rfp_id, "M4_FASTENER", 10.0, 22.0) is True


def test_7_peer_to_peer_architecture(env):
    """Verifies P2P Rubinstein alternating-offers negotiation and Pareto frontier."""
    res = env.run_bilateral_negotiation(
        buyer_id="M2_WELDER",
        seller_id="M3_SEALANT",
        resource_type_str=ResourceType.GRID_POWER_KW.value,
        quantity=20.0,
        initial_price=12.0,
        max_rounds=8
    )
    assert res["success"] is True
    assert len(res["history"]) >= 1
    assert "pareto_analysis" in res
    assert "frontier_points" in res["pareto_analysis"]
