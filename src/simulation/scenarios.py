"""
Pre-packaged Industrial Assembly Scenarios demonstrating the 7 Architectures in action.
"""

from typing import Dict, Any, List
from src.core.models import ResourceType
from src.simulation.assembly_environment import AssemblyEnvironment


def run_scenario_power_contention(env: AssemblyEnvironment) -> Dict[str, Any]:
    """
    Scenario 1: Peak Grid Surge & Power Scarcity (P2P Rubinstein Bargaining).
    Manipulator M2 (Welder) needs +25 kW peak power for rapid deep seam welding,
    negotiates directly with M3 (Sealant) to buy power allowance.
    """
    # Simulate P2P negotiation between M2 (Welder) and M3 (Sealant)
    res = env.run_bilateral_negotiation(
        buyer_id="M2_WELDER",
        seller_id="M3_SEALANT",
        resource_type_str=ResourceType.GRID_POWER_KW.value,
        quantity=25.0,
        initial_price=18.0,
        max_rounds=6
    )
    return {
        "scenario_name": "Peak Grid Power Contention (P2P Barter)",
        "description": "Manipulator M2 (Laser Welder) bilaterally negotiates with M3 (Sealant) to acquire 25 kW power quota.",
        "negotiation_result": res,
        "architectures_highlighted": ["PEER-TO-PEER", "DECENTRALIZED", "CENTRALIZED", "BLACKBOARD"]
    }


def run_scenario_tolerance_compensation(env: AssemblyEnvironment) -> Dict[str, Any]:
    """
    Scenario 2: Sequential Defect Feedforward & Tolerance Compensation (Pipeline Architecture).
    Raw workpiece has jig misalignment. Upstream passes data contract to M3 and M5 to adapt trajectories.
    """
    wp = env.pipeline_engine.spawn_workpiece("WP-COMPENSATE")
    steps = []
    
    # Run through all 6 stages
    for _ in range(6):
        res = env.pipeline_engine.advance_stage(wp.workpiece_id)
        steps.append(res)
        if res.get("status") == "COMPLETED":
            break
            
    return {
        "scenario_name": "Downstream Tolerance Feedforward Data Contract",
        "description": "Sequential data contracts transmit micro-variance downstream for adaptive sealant & inspection calibration.",
        "workpiece_id": wp.workpiece_id,
        "stages_executed": steps,
        "final_pass": wp.metrology_pass,
        "architectures_highlighted": ["SEQUENTIAL | PIPELINE", "DECENTRALIZED", "BLACKBOARD"]
    }


def run_scenario_deadlock_escalation(env: AssemblyEnvironment) -> Dict[str, Any]:
    """
    Scenario 3: Toolhead Scarcity & Deadlock Escalation (Hierarchical Arbitration).
    Two stubborn Boulware agents (M2 Welder and M5 Inspector) dispute access to High-Res Laser Toolhead.
    P2P deadlocks -> Escalates to Supervisor A for Kalai-Smorodinsky compromise & token subsidy.
    """
    res = env.run_bilateral_negotiation(
        buyer_id="M2_WELDER",
        seller_id="M5_INSPECTOR",
        resource_type_str=ResourceType.HIGH_RES_LASER_TOOL.value,
        quantity=1.0,
        initial_price=8.0,
        max_rounds=3  # Force early deadline to trigger supervisor escalation
    )
    return {
        "scenario_name": "Toolhead Scarcity & Hierarchical Deadlock Arbitration",
        "description": "Deadlock between two stubborn agents is escalated to Cell Supervisor for hierarchical arbitration.",
        "negotiation_result": res,
        "architectures_highlighted": ["HIERARCHICAL", "PEER-TO-PEER", "CENTRALIZED", "DECENTRALIZED"]
    }


def run_scenario_parallel_throughput(env: AssemblyEnvironment) -> Dict[str, Any]:
    """
    Scenario 4: High-Speed Parallel Throughput (Parallel Multi-Arm Execution).
    Simultaneously executes operations on all 6 arms within factory power ceiling.
    """
    results = env.trigger_parallel_operations()
    return {
        "scenario_name": "Concurrent Multi-Arm Parallel Stress Test",
        "description": "Concurrent execution across all 6 robotic manipulators with thread pool synchronization.",
        "parallel_results": results,
        "architectures_highlighted": ["PARALLEL", "CENTRALIZED", "BLACKBOARD"]
    }


def run_scenario_blackboard_rfp(env: AssemblyEnvironment) -> Dict[str, Any]:
    """
    Scenario 5: Blackboard Dynamic Spot Market & Open RFP Bidding.
    """
    # Update spot price on blackboard
    env.blackboard.update_spot_price(ResourceType.GPU_COMPUTE_TOKENS, 4.5, "Surge in Vision Metrology demand")
    rfp_id = env.post_blackboard_rfp("M5_INSPECTOR", ResourceType.GPU_COMPUTE_TOKENS.value, 15.0, 50.0)
    
    return {
        "scenario_name": "Blackboard Spot Market & Open RFP Bidding",
        "description": "Agent M5 publishes an RFP on the shared blackboard; peers automatically submit bids.",
        "rfp_id": rfp_id,
        "snapshot": env.blackboard.get_snapshot(),
        "architectures_highlighted": ["BLACKBOARD | SHARED-STATE", "DECENTRALIZED"]
    }
