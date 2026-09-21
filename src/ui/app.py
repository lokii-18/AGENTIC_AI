"""
Rich Interactive Gradio Web Application for the 7-Architecture Negotiating Multi-Agent System.
"""

import gradio as gr
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
import time
from typing import Dict, Any, List, Tuple

from src.simulation.assembly_environment import AssemblyEnvironment
from src.simulation.scenarios import (
    run_scenario_power_contention,
    run_scenario_tolerance_compensation,
    run_scenario_deadlock_escalation,
    run_scenario_parallel_throughput,
    run_scenario_blackboard_rfp
)
from src.core.models import ResourceType, ConcessionStrategy, ArchitectureType

# Initialize global shared simulation environment
sim_env = AssemblyEnvironment()


def create_agent_status_cards_html() -> str:
    """Generates ultra-crisp, clean light-themed status cards for all 6 manipulators."""
    summary = sim_env.get_system_summary()
    agents = summary["agents"]
    
    html = """
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(310px, 1fr)); gap: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-sizing: border-box;">
    """
    
    status_styles = {
        "IDLE": {"bg": "#eff6ff", "border": "#93c5fd", "text": "#1d4ed8", "label": "STANDBY"},
        "EXECUTING": {"bg": "#ecfdf5", "border": "#6ee7b7", "text": "#047857", "label": "EXECUTING"},
        "NEGOTIATING": {"bg": "#faf5ff", "border": "#d8b4fe", "text": "#6b21a8", "label": "NEGOTIATING"},
        "REQUESTING": {"bg": "#fffbeb", "border": "#fde68a", "text": "#b45309", "label": "REQUESTING"},
        "WAITING_RESOURCE": {"bg": "#fff7ed", "border": "#fed7aa", "text": "#c2410c", "label": "WAITING"},
        "BLOCKED": {"bg": "#fef2f2", "border": "#fecaca", "text": "#b91c1c", "label": "BLOCKED"},
        "COMPLETED": {"bg": "#ecfeff", "border": "#a5f3fc", "text": "#0e7490", "label": "COMPLETED"}
    }
    
    for a in agents:
        raw_status = str(a.get("status", "IDLE")).replace("AgentStatus.", "").upper()
        cfg = status_styles.get(raw_status, status_styles["IDLE"])
        
        raw_strat = str(a.get("concession_strategy", "LINEAR")).replace("ConcessionStrategy.", "")
        beta_val = a.get("beta_concession", 1.0)
        strat_text = f"{raw_strat} (β={beta_val})"
        
        raw_arch = str(a.get("active_architecture", "DECENTRALIZED")).replace("ArchitectureType.", "")
        raw_cell = str(a.get("cell_id", "Cell A")).replace("CELL_", "Cell ")
        
        power_val = a.get("power_draw_kw", 0.0)
        power_status = "Standby" if raw_status == "IDLE" else ("Active" if raw_status == "EXECUTING" else "Draw")
        
        tokens_val = a.get("budget_tokens", 0.0)
        cycles_val = a.get("completed_cycles", 0)
        compute_val = a.get("compute_tokens_held", 0.0)
        
        html += f"""
        <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); box-sizing: border-box; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <!-- Top Header: ID & Status Badge -->
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 800; font-size: 16px; color: #0f172a; letter-spacing: 0.3px;">{a.get('agent_id')}</span>
                    <span style="background: {cfg['bg']}; border: 1px solid {cfg['border']}; color: {cfg['text']}; padding: 3px 9px; border-radius: 9999px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;">{cfg['label']}</span>
                </div>
                
                <!-- Subtitle: Name & Role -->
                <div style="color: #475569; font-size: 12px; line-height: 1.4; margin-bottom: 12px; min-height: 32px;">
                    <div style="color: #1e293b; font-weight: 600;">{a.get('name')}</div>
                    <div style="color: #64748b;">{a.get('role')}</div>
                </div>
                
                <!-- Badges -->
                <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px;">
                    <span style="background: #f1f5f9; border: 1px solid #cbd5e1; color: #334155; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">📍 {raw_cell}</span>
                    <span style="background: #f5f3ff; border: 1px solid #ddd6fe; color: #6d28d9; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">🎯 {strat_text}</span>
                </div>
            </div>

            <div>
                <!-- Telemetry Matrix -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 12px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px; border-radius: 8px; margin-bottom: 10px;">
                    <div style="color: #475569;">⚡ Power: <span style="color: #0284c7; font-weight: 700;">{power_val:.1f} kW</span> <span style="font-size: 10px; color: #94a3b8;">({power_status})</span></div>
                    <div style="color: #475569;">🪙 Tokens: <span style="color: #b45309; font-weight: 700;">{tokens_val:.1f}</span></div>
                    <div style="color: #475569;">🔄 Cycles: <span style="color: #047857; font-weight: 700;">{cycles_val}</span></div>
                    <div style="color: #475569;">🖥️ Compute: <span style="color: #6d28d9; font-weight: 700;">{compute_val:.1f}</span></div>
                </div>

                <!-- Active Architecture Footnote -->
                <div style="display: flex; align-items: center; justify-content: space-between; background: #f1f5f9; border: 1px solid #e2e8f0; padding: 5px 8px; border-radius: 6px; font-size: 11px;">
                    <span style="color: #64748b;">Active Architecture:</span>
                    <span style="color: #0284c7; font-weight: 700;">{raw_arch}</span>
                </div>
            </div>
        </div>
        """
    html += "</div>"
    return html


def create_factory_kpi_html() -> str:
    """Creates top summary banner for factory status, power draw, and emergency controls."""
    summary = sim_env.get_system_summary()
    arb = summary["arbiter"]
    bb = summary["blackboard"]
    
    pct = arb["power_utilization_pct"]
    bar_color = "#10b981" if pct < 70 else ("#f59e0b" if pct < 90 else "#ef4444")
    status_text = "🚨 EMERGENCY HALT" if arb["emergency_halt"] else "🟢 OPERATIONAL"
    status_bg = "#fef2f2" if arb["emergency_halt"] else "#ecfdf5"
    status_border = "#fecaca" if arb["emergency_halt"] else "#a7f3d0"
    status_color = "#b91c1c" if arb["emergency_halt"] else "#047857"
    
    return f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; margin-bottom: 14px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; box-sizing: border-box; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 12px; border-radius: 8px;">
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Factory State</div>
            <div style="margin-top: 6px;">
                <span style="background: {status_bg}; border: 1px solid {status_border}; color: {status_color}; padding: 3px 8px; border-radius: 6px; font-size: 12px; font-weight: 700;">{status_text}</span>
            </div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 12px; border-radius: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Total Grid Power</span>
                <span style="font-size: 11px; color: {bar_color}; font-weight: 700;">{pct}%</span>
            </div>
            <div style="font-size: 16px; font-weight: 800; color: #0f172a; margin-top: 4px;">
                <span style="color: #0284c7;">{arb['current_power_draw_kw']:.1f}</span> <span style="font-size: 12px; color: #64748b;">/ {arb['max_power_limit_kw']:.0f} kW</span>
            </div>
            <div style="background: #e2e8f0; height: 6px; border-radius: 3px; margin-top: 6px; overflow: hidden;">
                <div style="background: {bar_color}; width: {min(100, pct)}%; height: 100%; border-radius: 3px;"></div>
            </div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 12px; border-radius: 8px;">
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Central Ledger Contracts</div>
            <div style="font-size: 18px; font-weight: 800; color: #0284c7; margin-top: 4px;">{arb['contracts_registered']}</div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 12px; border-radius: 8px;">
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Tokens Transacted</div>
            <div style="font-size: 18px; font-weight: 800; color: #b45309; margin-top: 4px;">{arb['total_tokens_transacted']:.1f} 🪙</div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 12px; border-radius: 8px;">
            <div style="font-size: 11px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Blackboard Open RFPs</div>
            <div style="font-size: 18px; font-weight: 800; color: #d97706; margin-top: 4px;">{bb['open_rfps']}</div>
        </div>
    </div>
    """


def create_architecture_activity_plot() -> go.Figure:
    """Generates an interactive Plotly bar and radar chart showing all 7 architectures in active execution."""
    summary = sim_env.get_system_summary()
    act = summary["arch_activity"]
    
    categories = list(act.keys())
    values = list(act.values())
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=categories,
        y=values,
        marker=dict(
            color=values,
            colorscale='Blues',
            showscale=False
        ),
        text=values,
        textposition='auto',
        hoverinfo='x+y'
    ))
    
    fig.update_layout(
        title="<b>Real-Time Execution Activity Across All 7 Architectures</b>",
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#0f172a", size=12),
        margin=dict(l=40, r=40, t=50, b=80),
        xaxis=dict(tickangle=-25, showgrid=False),
        yaxis=dict(title="Event & Transaction Count", showgrid=True, gridcolor="rgba(0,0,0,0.06)")
    )
    return fig


def create_pareto_plot(pareto_data: Dict[str, Any]) -> go.Figure:
    """Generates Plotly Pareto frontier curve and Nash Bargaining Solution."""
    if not pareto_data or "frontier_points" not in pareto_data:
        fig = go.Figure()
        fig.update_layout(
            title="No Negotiation Data Available",
            template="plotly_white",
            paper_bgcolor="#ffffff"
        )
        return fig
        
    pts = pareto_data["frontier_points"]
    df = pd.DataFrame(pts)
    
    fig = go.Figure()
    
    # Pareto Curve
    fig.add_trace(go.Scatter(
        x=df["buyer_utility"],
        y=df["seller_utility"],
        mode='lines+markers',
        name='Pareto Efficient Frontier',
        line=dict(color='#7c3aed', width=3),
        marker=dict(size=7, color=df["price"], colorscale='Viridis', showscale=True, colorbar=dict(title="Price (Tokens)"))
    ))
    
    # Nash Equilibrium point
    nash = pareto_data.get("nash_equilibrium")
    if nash:
        fig.add_trace(go.Scatter(
            x=[nash["buyer_utility"]],
            y=[nash["seller_utility"]],
            mode='markers+text',
            name='Nash Bargaining Solution',
            marker=dict(size=14, color='#059669', symbol='star'),
            text=[f"Nash Optimum (Price={nash['price']})"],
            textposition='top right'
        ))
        
    # Reservation Utility threshold lines
    u_res_b = pareto_data.get("reservation_buyer", 0.4)
    u_res_s = pareto_data.get("reservation_seller", 0.4)
    
    fig.add_vline(x=u_res_b, line_dash="dash", line_color="#dc2626", annotation_text="Buyer Reservation U_min")
    fig.add_hline(y=u_res_s, line_dash="dash", line_color="#d97706", annotation_text="Seller Reservation U_min")
    
    fig.update_layout(
        title="<b>Game-Theoretic Pareto Efficiency Frontier & Nash Bargaining Solution</b>",
        xaxis_title="Buyer Utility U_buyer",
        yaxis_title="Seller Utility U_seller",
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#0f172a"),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def create_rounds_utility_plot(history: List[Dict[str, Any]]) -> go.Figure:
    """Plots the round-by-round utility trajectory of both negotiating agents."""
    if not history:
        fig = go.Figure()
        fig.update_layout(title="No rounds history", template="plotly_white", paper_bgcolor="#ffffff")
        return fig
        
    rounds = [h["round_idx"] for h in history]
    prices = [h["price_tokens"] for h in history]
    u_sender = [h["utility_sender"] for h in history]
    actions = [h["action"] for h in history]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=rounds,
        y=prices,
        mode='lines+markers+text',
        name='Offered Price (Tokens)',
        line=dict(color='#0284c7', width=2),
        marker=dict(size=10),
        text=actions,
        textposition='top center',
        yaxis='y1'
    ))
    
    fig.add_trace(go.Scatter(
        x=rounds,
        y=u_sender,
        mode='lines+markers',
        name='Sender Utility U_i',
        line=dict(color='#d97706', width=2, dash='dot'),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="<b>Negotiation Dynamics Across Alternating Rounds</b>",
        xaxis_title="Negotiation Round Index",
        yaxis=dict(title="Price (Tokens)", showgrid=True, gridcolor="rgba(0,0,0,0.06)"),
        yaxis2=dict(title="Utility [0.0 - 1.0]", overlaying='y', side='right', range=[0, 1]),
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#f8fafc",
        font=dict(color="#0f172a"),
        legend=dict(x=0.02, y=0.98),
        margin=dict(l=40, r=40, t=50, b=40)
    )
    return fig


def get_recent_events_table() -> pd.DataFrame:
    """Formats event log into a pandas dataframe for live table display."""
    summary = sim_env.get_system_summary()
    events = summary["recent_events"]
    if not events:
        return pd.DataFrame(columns=["Time", "Architecture", "Source", "Target", "Action", "Details"])
    
    rows = []
    for e in reversed(events):
        t_str = time.strftime("%H:%M:%S", time.localtime(e["timestamp"]))
        rows.append({
            "Time": t_str,
            "Architecture": e["architecture"],
            "Source": e["source"],
            "Target": e["target"],
            "Action": e["action"],
            "Details": e["details"]
        })
    return pd.DataFrame(rows)


def get_pipeline_table() -> pd.DataFrame:
    """Returns dataframe of active pipeline stages and workpieces."""
    summary = sim_env.get_system_summary()
    pipeline = summary["pipeline"]
    return pd.DataFrame(pipeline)


# Gradio Event Handlers
def handle_step_pipeline():
    res = sim_env.trigger_pipeline_step()
    return (
        create_factory_kpi_html(),
        create_agent_status_cards_html(),
        create_architecture_activity_plot(),
        get_recent_events_table(),
        get_pipeline_table(),
        f"Pipeline step executed: {json.dumps(res, indent=2)}"
    )


def handle_parallel_operations():
    res = sim_env.trigger_parallel_operations()
    return (
        create_factory_kpi_html(),
        create_agent_status_cards_html(),
        create_architecture_activity_plot(),
        get_recent_events_table(),
        get_pipeline_table(),
        f"Parallel batch results:\n{json.dumps(res, indent=2)}"
    )


def handle_run_negotiation(buyer_id, seller_id, res_type, qty, price, rounds):
    res = sim_env.run_bilateral_negotiation(
        buyer_id=buyer_id,
        seller_id=seller_id,
        resource_type_str=res_type,
        quantity=float(qty),
        initial_price=float(price),
        max_rounds=int(rounds)
    )
    pareto_fig = create_pareto_plot(res.get("pareto_analysis", {}))
    rounds_fig = create_rounds_utility_plot(res.get("history", []))
    
    history_df = pd.DataFrame(res.get("history", []))
    if not history_df.empty:
        cols_to_show = [c for c in ["round_idx", "sender_id", "receiver_id", "action", "quantity", "price_tokens", "utility_sender", "notes"] if c in history_df.columns]
        history_df = history_df[cols_to_show]
        
    summary_text = (
        f"🤝 Negotiation Outcome: {'AGREED' if res['success'] else 'FAILED'}\n"
        f"⚖️ Arbitrated by Supervisor: {res['arbitrated']}\n"
        f"🔄 Total Rounds: {res['rounds_count']}\n"
        f"💰 Buyer Budget: {res['buyer_final_budget']} tokens | Seller Budget: {res['seller_final_budget']} tokens\n"
        f"📝 Final Agreed Terms: {json.dumps(res['final_offer'], indent=2)}"
    )
    
    return (
        create_factory_kpi_html(),
        create_agent_status_cards_html(),
        create_architecture_activity_plot(),
        get_recent_events_table(),
        pareto_fig,
        rounds_fig,
        history_df,
        summary_text
    )


def handle_run_scenario(scenario_idx: int):
    if scenario_idx == 1:
        res = run_scenario_power_contention(sim_env)
    elif scenario_idx == 2:
        res = run_scenario_tolerance_compensation(sim_env)
    elif scenario_idx == 3:
        res = run_scenario_deadlock_escalation(sim_env)
    elif scenario_idx == 4:
        res = run_scenario_parallel_throughput(sim_env)
    elif scenario_idx == 5:
        res = run_scenario_blackboard_rfp(sim_env)
    else:
        res = {"status": "Unknown scenario"}
        
    return (
        create_factory_kpi_html(),
        create_agent_status_cards_html(),
        create_architecture_activity_plot(),
        get_recent_events_table(),
        get_pipeline_table(),
        f"=== {res.get('scenario_name', 'Scenario')} ===\n{json.dumps(res, indent=2, default=str)}"
    )


def handle_emergency_estop():
    if sim_env.central_arbiter.emergency_halt:
        sim_env.central_arbiter.reset_estop()
    else:
        sim_env.central_arbiter.trigger_emergency_estop("Operator Manual E-Stop pressed on Dashboard")
    return (
        create_factory_kpi_html(),
        create_agent_status_cards_html(),
        create_architecture_activity_plot(),
        get_recent_events_table()
    )


CUSTOM_CSS = """
body, .gradio-container {
    background-color: #f8fafc !important;
    color: #0f172a !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif !important;
}
.prose h1, .prose h2, .prose h3, .prose h4 {
    color: #0f172a !important;
}
.prose p, .prose li, .prose span {
    color: #334155 !important;
}
.tab-nav button {
    font-weight: 700 !important;
    font-size: 14px !important;
    color: #475569 !important;
}
.tab-nav button.selected {
    color: #0284c7 !important;
    border-bottom: 2px solid #0284c7 !important;
}
.gradio-container * {
    box-sizing: border-box;
}
"""

# Build the Gradio Application Layout
def build_app() -> gr.Blocks:
    with gr.Blocks(title="SYNAPSE-ARM | 7-Architecture Multi-Agent Resource Negotiator") as demo:
        
        # Header
        gr.HTML("""
        <div style="text-align: center; padding: 18px 0 10px 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 16px;">
            <h1 style="font-size: 28px; font-weight: 800; background: linear-gradient(90deg, #0284c7, #4f46e5, #7c3aed); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
                SYNAPSE-ARM: 7-Architecture Multi-Agent Resource Sharing & Negotiation
            </h1>
            <p style="font-size: 14px; color: #475569; margin: 6px 0 0 0; font-weight: 500;">
                Autonomous Industrial Robotic Assembly Unit with Game-Theoretic Bilateral Bargaining & Feedforward Data Contracts
            </p>
        </div>
        """)
        
        # Factory KPI Banner
        kpi_banner = gr.HTML(value=create_factory_kpi_html())
        
        with gr.Tabs() as tabs:
            # -------------------------------------------------------------
            # TAB 1: Live Assembly Digital Twin & Operations
            # -------------------------------------------------------------
            with gr.Tab("🏭 Assembly Digital Twin & Live Engine"):
                with gr.Row():
                    with gr.Column(scale=3):
                        gr.Markdown("### 🤖 Autonomous Manipulator Stations")
                        agent_cards_html = gr.HTML(value=create_agent_status_cards_html())
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### ⚡ Live Control Deck")
                        with gr.Group():
                            btn_step = gr.Button("▶️ Advance Pipeline Stage", variant="primary")
                            btn_parallel = gr.Button("⚡ Execute Parallel Multi-Arm Cycle", variant="secondary")
                            btn_estop = gr.Button("🛑 Toggle Safety E-Stop", variant="stop")
                            
                        gr.Markdown("### 📜 Real-Time Action Log")
                        console_out = gr.Textbox(label="Last Operation Payload", lines=6, max_lines=10)
                
                gr.Markdown("### 📡 Live Multi-Agent Event Bus (All 7 Architectures)")
                events_df = gr.Dataframe(value=get_recent_events_table(), interactive=False)

            # -------------------------------------------------------------
            # TAB 2: The 7 Multi-Agent Architectures Visual Map
            # -------------------------------------------------------------
            with gr.Tab("🏛️ 7-Architecture Topology & Activity"):
                with gr.Row():
                    with gr.Column(scale=2):
                        arch_plot = gr.Plot(value=create_architecture_activity_plot())
                    with gr.Column(scale=1):
                        gr.Markdown("""
                        ### 📐 Integrated Architecture Matrix
                        
                        1. **CENTRALIZED**: Global safety gatekeeper enforcing the 100 kW factory grid ceiling and signed ledger audit.
                        2. **HIERARCHICAL**: Cell Supervisor Agents (Cell A & B) handling task decomposition and Kalai-Smorodinsky deadlock arbitration.
                        3. **DE-CENTRALIZED**: Manipulators with private utility functions $U_i(Q, P, t)$, reservation prices, and concession strategies (Boulware, Conceder, Linear).
                        4. **SEQUENTIAL | PIPELINE**: 6-station assembly line streaming Workpiece Data Contracts with upstream-to-downstream defect compensation.
                        5. **PARALLEL**: Thread-pool concurrent multi-arm execution with dynamic collision/power lock synchronization.
                        6. **BLACKBOARD | SHARED-STATE**: Thread-safe memory board for Request-For-Proposals (RFPs), spot price oracles, and locks.
                        7. **PEER-TO-PEER**: Direct Rubinstein alternating-offers bargaining & Contract Net Protocol (CNP) without central bottleneck.
                        """)
                
                gr.HTML("""
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin-top: 14px;">
                    <div style="background: #eff6ff; border: 1px solid #dbeafe; border-left: 4px solid #0284c7; padding: 10px; border-radius: 6px; font-size: 12px; color: #1e3a8a;">
                        <b style="color: #1e40af;">1. Centralized</b><br/>Global Ledger & 100kW Cap
                    </div>
                    <div style="background: #eef2ff; border: 1px solid #e0e7ff; border-left: 4px solid #6366f1; padding: 10px; border-radius: 6px; font-size: 12px; color: #312e81;">
                        <b style="color: #3730a3;">2. Hierarchical</b><br/>Cell Supervisors & Quotas
                    </div>
                    <div style="background: #faf5ff; border: 1px solid #f3e8ff; border-left: 4px solid #a855f7; padding: 10px; border-radius: 6px; font-size: 12px; color: #581c87;">
                        <b style="color: #6b21a8;">3. Decentralized</b><br/>Private Utility & Preferences
                    </div>
                    <div style="background: #ecfdf5; border: 1px solid #d1fae5; border-left: 4px solid #10b981; padding: 10px; border-radius: 6px; font-size: 12px; color: #064e3b;">
                        <b style="color: #047857;">4. Sequential Pipeline</b><br/>Data Contracts & Feedforward
                    </div>
                    <div style="background: #fffbeb; border: 1px solid #fef3c7; border-left: 4px solid #f59e0b; padding: 10px; border-radius: 6px; font-size: 12px; color: #78350f;">
                        <b style="color: #b45309;">5. Parallel</b><br/>Async Multi-Arm Concurrency
                    </div>
                    <div style="background: #fff7ed; border: 1px solid #ffedd5; border-left: 4px solid #f97316; padding: 10px; border-radius: 6px; font-size: 12px; color: #7c2d12;">
                        <b style="color: #c2410c;">6. Blackboard</b><br/>Pub/Sub & Spot Bulletin
                    </div>
                    <div style="background: #fdf2f8; border: 1px solid #fce7f3; border-left: 4px solid #ec4899; padding: 10px; border-radius: 6px; font-size: 12px; color: #831843;">
                        <b style="color: #9d174d;">7. Peer-to-Peer</b><br/>Rubinstein Alternating Offers
                    </div>
                </div>
                """)

            # -------------------------------------------------------------
            # TAB 3: Game-Theoretic Negotiation Engine
            # -------------------------------------------------------------
            with gr.Tab("⚖️ Game-Theoretic Negotiation & Pareto Analytics"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🤝 Configure Bilateral P2P Negotiation")
                        buyer_dropdown = gr.Dropdown(
                            label="Buyer Manipulator (Demands Resource)",
                            choices=["M1_LOADER", "M2_WELDER", "M3_SEALANT", "M4_FASTENER", "M5_INSPECTOR", "M6_PALLETIZER"],
                            value="M2_WELDER"
                        )
                        seller_dropdown = gr.Dropdown(
                            label="Seller Manipulator (Holds Resource)",
                            choices=["M1_LOADER", "M2_WELDER", "M3_SEALANT", "M4_FASTENER", "M5_INSPECTOR", "M6_PALLETIZER"],
                            value="M3_SEALANT"
                        )
                        res_dropdown = gr.Dropdown(
                            label="Resource Type",
                            choices=[r.value for r in ResourceType],
                            value=ResourceType.GRID_POWER_KW.value
                        )
                        with gr.Row():
                            qty_input = gr.Number(label="Quantity", value=20.0, step=1.0)
                            price_input = gr.Number(label="Initial Offer Price", value=15.0, step=1.0)
                            rounds_input = gr.Slider(label="Max Bargaining Rounds", minimum=2, maximum=15, value=8, step=1)
                            
                        btn_negotiate = gr.Button("🚀 Start P2P Rubinstein Negotiation", variant="primary")
                    
                    with gr.Column(scale=2):
                        gr.Markdown("### 📊 Game-Theoretic Analysis")
                        with gr.Row():
                            pareto_graph = gr.Plot(value=create_pareto_plot({}))
                            rounds_graph = gr.Plot(value=create_rounds_utility_plot([]))
                            
                with gr.Row():
                    with gr.Column(scale=1):
                        negotiation_summary = gr.Textbox(label="Contract Summary & Settlement", lines=8)
                    with gr.Column(scale=2):
                        rounds_table = gr.Dataframe(label="Round-by-Round Offers Transcript", interactive=False)

            # -------------------------------------------------------------
            # TAB 4: Sequential Pipeline & Workpiece Data Contracts
            # -------------------------------------------------------------
            with gr.Tab("🔄 Sequential Pipeline & Data Contracts"):
                gr.Markdown("### 📦 Active Workpiece Assembly Stages & Data Handoffs")
                pipeline_df = gr.Dataframe(value=get_pipeline_table(), interactive=False)
                
                gr.Markdown(r"""
                #### 🔬 Feedforward Tolerance Compensation In Action:
                - **M1 (Infeed)**: Clamps raw jig and detects micro-misalignment ($\pm 0.18$ mm).
                - **M2 (Welder)**: Laser weld penetration creates thermal expansion profile ($185^\circ\text{C}$).
                - **M3 (Sealant)**: Dynamically adjusts sealant bead path $\Delta x = -0.95 \cdot \text{jig\_err}$ and adapts extrusion viscosity.
                - **M4 (Fastener)**: Modulates bolt torque signature based on thermal expansion state.
                - **M5 (Inspector)**: Validates that feedforward compensation eliminated cumulative variance ($<0.05$ mm).
                """)

            # -------------------------------------------------------------
            # TAB 5: Automated Scenarios & Benchmarks
            # -------------------------------------------------------------
            with gr.Tab("🚀 Scenario Benchmarks"):
                gr.Markdown("### 🧪 Pre-configured Industrial Assembly Test Scenarios")
                with gr.Row():
                    btn_scen1 = gr.Button("1️⃣ Peak Power Contention (P2P Barter)")
                    btn_scen2 = gr.Button("2️⃣ Tolerance Feedforward (Pipeline)")
                    btn_scen3 = gr.Button("3️⃣ Deadlock Escalation (Hierarchical)")
                with gr.Row():
                    btn_scen4 = gr.Button("4️⃣ Multi-Arm Stress (Parallel)")
                    btn_scen5 = gr.Button("5️⃣ Spot Price Surge (Blackboard RFP)")
                    
                scenario_result_box = gr.Textbox(label="Scenario Benchmark Execution Report", lines=12)

        # -------------------------------------------------------------
        # Wire up Interactivity & Callbacks
        # -------------------------------------------------------------
        btn_step.click(
            fn=handle_step_pipeline,
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pipeline_df, console_out]
        )
        
        btn_parallel.click(
            fn=handle_parallel_operations,
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pipeline_df, console_out]
        )
        
        btn_estop.click(
            fn=handle_emergency_estop,
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df]
        )
        
        btn_negotiate.click(
            fn=handle_run_negotiation,
            inputs=[buyer_dropdown, seller_dropdown, res_dropdown, qty_input, price_input, rounds_input],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pareto_graph, rounds_graph, rounds_table, negotiation_summary]
        )
        
        btn_scen1.click(
            fn=lambda: handle_run_scenario(1),
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pipeline_df, scenario_result_box]
        )
        btn_scen2.click(
            fn=lambda: handle_run_scenario(2),
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pipeline_df, scenario_result_box]
        )
        btn_scen3.click(
            fn=lambda: handle_run_scenario(3),
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pipeline_df, scenario_result_box]
        )
        btn_scen4.click(
            fn=lambda: handle_run_scenario(4),
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pipeline_df, scenario_result_box]
        )
        btn_scen5.click(
            fn=lambda: handle_run_scenario(5),
            inputs=[],
            outputs=[kpi_banner, agent_cards_html, arch_plot, events_df, pipeline_df, scenario_result_box]
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
