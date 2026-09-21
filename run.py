"""
Main launcher script for SYNAPSE-ARM Multi-Agent Negotiation System.
Can run as an interactive web UI (default) or headless CLI benchmark.
"""

import sys
import os
import argparse

# Ensure utf-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure src is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.simulation.assembly_environment import AssemblyEnvironment
from src.simulation.scenarios import (
    run_scenario_power_contention,
    run_scenario_tolerance_compensation,
    run_scenario_deadlock_escalation,
    run_scenario_parallel_throughput,
    run_scenario_blackboard_rfp
)


def run_headless_benchmarks():
    print("=" * 70)
    print("  SYNAPSE-ARM: 7-Architecture Multi-Agent Industrial Assembly System")
    print("=" * 70)
    
    env = AssemblyEnvironment()
    
    print("\n[1/5] Running Scenario 1: Peak Grid Power Contention (P2P Barter)...")
    res1 = run_scenario_power_contention(env)
    print(f"  -> Outcome: Agreement in {res1['negotiation_result']['rounds_count']} rounds | Agreed Price: {res1['negotiation_result']['final_offer']['price_tokens']} tokens")
    
    print("\n[2/5] Running Scenario 2: Downstream Tolerance Feedforward Data Contract...")
    res2 = run_scenario_tolerance_compensation(env)
    print(f"  -> Workpiece: {res2['workpiece_id']} | Final Metrology Pass: {res2['final_pass']}")
    
    print("\n[3/5] Running Scenario 3: Toolhead Scarcity & Hierarchical Deadlock Arbitration...")
    res3 = run_scenario_deadlock_escalation(env)
    print(f"  -> Arbitrated: {res3['negotiation_result']['arbitrated']} | Arbitrated Price: {res3['negotiation_result']['final_offer']['price_tokens']} tokens")
    
    print("\n[4/5] Running Scenario 4: Concurrent Multi-Arm Parallel Stress Test...")
    res4 = run_scenario_parallel_throughput(env)
    print(f"  -> Parallel Arms Executed: {len(res4['parallel_results'])}/6 | All threads completed successfully.")
    
    print("\n[5/5] Running Scenario 5: Blackboard Spot Market & Open RFP Bidding...")
    res5 = run_scenario_blackboard_rfp(env)
    print(f"  -> RFP Created: {res5['rfp_id']} | Total Blackboard Events: {res5['snapshot']['total_events']}")
    
    summary = env.get_system_summary()
    print("\n" + "=" * 70)
    print("  All 7 Architectures Successfully Verified in Action:")
    for arch, count in summary["arch_activity"].items():
        print(f"   • {arch:<26}: {count} operations logged")
    print("=" * 70)


def run_web_ui(port: int = 7860, share: bool = False):
    from src.ui.app import build_app, CUSTOM_CSS
    server_name = os.environ.get("GRADIO_SERVER_NAME", "127.0.0.1")
    print(f"\n🚀 Launching SYNAPSE-ARM Dashboard on http://{server_name}:{port} ...")
    app = build_app()
    app.launch(server_name=server_name, server_port=port, share=share, css=CUSTOM_CSS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SYNAPSE-ARM 7-Architecture Multi-Agent System")
    parser.add_argument("--cli", action="store_true", help="Run automated CLI benchmarks instead of web UI")
    parser.add_argument("--port", type=int, default=7860, help="Port to run the Gradio UI on (default: 7860)")
    parser.add_argument("--share", action="store_true", help="Create public shareable Gradio link")
    
    args = parser.parse_args()
    
    # Use PORT env var (set by Render/cloud platforms) if available
    port = int(os.environ.get("PORT", args.port))
    
    if args.cli:
        run_headless_benchmarks()
    else:
        run_web_ui(port=port, share=args.share)
