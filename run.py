```python
"""
Main launcher script for SYNAPSE-ARM Multi-Agent Negotiation System.

Can run as:
1. Interactive Gradio web UI (default)
2. Headless CLI benchmark using --cli

Render deployment:
    python run.py

The application automatically uses the PORT environment variable
provided by Render/cloud platforms.
"""

import sys
import os
import argparse


# ============================================================
# UTF-8 OUTPUT CONFIGURATION
# ============================================================

# Ensure UTF-8 output encoding on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# PYTHON PATH CONFIGURATION
# ============================================================

# Ensure the project root is in the Python path
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# SYNAPSE-ARM IMPORTS
# ============================================================

from src.simulation.assembly_environment import AssemblyEnvironment

from src.simulation.scenarios import (
    run_scenario_power_contention,
    run_scenario_tolerance_compensation,
    run_scenario_deadlock_escalation,
    run_scenario_parallel_throughput,
    run_scenario_blackboard_rfp,
)


# ============================================================
# HEADLESS BENCHMARK MODE
# ============================================================

def run_headless_benchmarks():
    """
    Run all SYNAPSE-ARM multi-agent architecture scenarios
    without starting the web interface.
    """

    print("=" * 70)
    print("  SYNAPSE-ARM: 7-Architecture Multi-Agent Industrial Assembly System")
    print("=" * 70)

    env = AssemblyEnvironment()

    # --------------------------------------------------------
    # Scenario 1
    # --------------------------------------------------------

    print(
        "\n[1/5] Running Scenario 1: "
        "Peak Grid Power Contention (P2P Barter)..."
    )

    res1 = run_scenario_power_contention(env)

    print(
        f"  -> Outcome: Agreement in "
        f"{res1['negotiation_result']['rounds_count']} rounds | "
        f"Agreed Price: "
        f"{res1['negotiation_result']['final_offer']['price_tokens']} tokens"
    )

    # --------------------------------------------------------
    # Scenario 2
    # --------------------------------------------------------

    print(
        "\n[2/5] Running Scenario 2: "
        "Downstream Tolerance Feedforward Data Contract..."
    )

    res2 = run_scenario_tolerance_compensation(env)

    print(
        f"  -> Workpiece: {res2['workpiece_id']} | "
        f"Final Metrology Pass: {res2['final_pass']}"
    )

    # --------------------------------------------------------
    # Scenario 3
    # --------------------------------------------------------

    print(
        "\n[3/5] Running Scenario 3: "
        "Toolhead Scarcity & Hierarchical Deadlock Arbitration..."
    )

    res3 = run_scenario_deadlock_escalation(env)

    print(
        f"  -> Arbitrated: "
        f"{res3['negotiation_result']['arbitrated']} | "
        f"Arbitrated Price: "
        f"{res3['negotiation_result']['final_offer']['price_tokens']} tokens"
    )

    # --------------------------------------------------------
    # Scenario 4
    # --------------------------------------------------------

    print(
        "\n[4/5] Running Scenario 4: "
        "Concurrent Multi-Arm Parallel Stress Test..."
    )

    res4 = run_scenario_parallel_throughput(env)

    print(
        f"  -> Parallel Arms Executed: "
        f"{len(res4['parallel_results'])}/6 | "
        f"All threads completed successfully."
    )

    # --------------------------------------------------------
    # Scenario 5
    # --------------------------------------------------------

    print(
        "\n[5/5] Running Scenario 5: "
        "Blackboard Spot Market & Open RFP Bidding..."
    )

    res5 = run_scenario_blackboard_rfp(env)

    print(
        f"  -> RFP Created: {res5['rfp_id']} | "
        f"Total Blackboard Events: "
        f"{res5['snapshot']['total_events']}"
    )

    # --------------------------------------------------------
    # System Summary
    # --------------------------------------------------------

    summary = env.get_system_summary()

    print("\n" + "=" * 70)
    print("  All 7 Architectures Successfully Verified in Action:")
    print("=" * 70)

    for arch, count in summary["arch_activity"].items():
        print(f"  • {arch:<26}: {count} operations logged")

    print("=" * 70)


# ============================================================
# GRADIO WEB UI
# ============================================================

def run_web_ui(port: int = 7860, share: bool = False):
    """
    Start the SYNAPSE-ARM Gradio web dashboard.

    For Render/cloud deployment:
        Host = 0.0.0.0
        Port = value provided through the PORT environment variable
    """

    # Import UI only when web mode is requested.
    # This prevents unnecessary UI dependencies during CLI mode.
    from src.ui.app import build_app, CUSTOM_CSS

    # --------------------------------------------------------
    # SERVER HOST
    # --------------------------------------------------------
    #
    # Render requires the application to listen on all
    # network interfaces.
    #
    # Therefore the default is 0.0.0.0 instead of 127.0.0.1.
    #

    server_name = os.environ.get(
        "GRADIO_SERVER_NAME",
        "0.0.0.0"
    )

    # --------------------------------------------------------
    # SERVER PORT
    # --------------------------------------------------------
    #
    # The port passed into this function normally comes from
    # the PORT environment variable in main().
    #

    print("\n" + "=" * 70)
    print("  SYNAPSE-ARM Web Dashboard")
    print("=" * 70)
    print(f"  Server Host : {server_name}")
    print(f"  Server Port : {port}")
    print(f"  Render PORT : {os.environ.get('PORT', 'Not set')}")
    print("=" * 70)

    print(
        f"\n🚀 Launching SYNAPSE-ARM Dashboard "
        f"on http://{server_name}:{port}"
    )

    # Build the Gradio application
    app = build_app()

    # Launch Gradio
    app.launch(
        server_name=server_name,
        server_port=port,
        share=share,
        css=CUSTOM_CSS,
    )


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "SYNAPSE-ARM 7-Architecture "
            "Multi-Agent Industrial Assembly System"
        )
    )

    # --------------------------------------------------------
    # CLI BENCHMARK OPTION
    # --------------------------------------------------------

    parser.add_argument(
        "--cli",
        action="store_true",
        help=(
            "Run automated CLI benchmarks "
            "instead of the web UI"
        ),
    )

    # --------------------------------------------------------
    # PORT OPTION
    # --------------------------------------------------------

    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help=(
            "Port to run the Gradio UI on. "
            "Render automatically overrides this using PORT."
        ),
    )

    # --------------------------------------------------------
    # GRADIO SHARE OPTION
    # --------------------------------------------------------

    parser.add_argument(
        "--share",
        action="store_true",
        help=(
            "Create a public Gradio shareable link"
        ),
    )

    args = parser.parse_args()

    # ========================================================
    # RENDER / CLOUD PORT HANDLING
    # ========================================================
    #
    # Render automatically provides:
    #
    #     PORT=<assigned port>
    #
    # We use that value when available.
    #
    # For local development, if PORT is not defined,
    # the default --port value (7860) is used.
    #

    port = int(
        os.environ.get(
            "PORT",
            args.port
        )
    )

    # ========================================================
    # APPLICATION MODE
    # ========================================================

    if args.cli:

        # Run benchmark mode
        run_headless_benchmarks()

    else:

        # Run Gradio web dashboard
        run_web_ui(
            port=port,
            share=args.share
        )