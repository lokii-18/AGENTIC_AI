# SYNAPSE-ARM: 7-Architecture Multi-Agent Industrial Assembly System
### *Autonomous Negotiating Agents for Resource Sharing & Sequential Assembly Data Contracts*

---

## 🌟 Executive Overview
**SYNAPSE-ARM** is an enterprise-grade Multi-Agent System (MAS) designed from first principles by a 20+ year AI Systems Architect. It orchestrates a 6-station advanced robotic assembly unit (Loader, Laser Welder, Sealant Dispenser, Bolt Fastener, Optical Inspector, Palletizer) sharing finite industrial resources (**Peak Grid Power kW**, **Specialized Quick-Change End-Effectors**, **GPU Vision Compute Tokens**, and **Buffer Overlap Staging Zones**).

Rather than superficial demos, **all 7 classical and modern multi-agent architectures are natively integrated into the system's operational fabric**.

---

## 🏛️ The 7 Integrated Multi-Agent Architectures

```
+-------------------------------------------------------------------------------+
|                        1. CENTRALIZED ARCHITECTURE                            |
|             Global Factory Safety Arbiter & Signed Contract Ledger            |
|               • Factory Grid Cap (100 kW) • Emergency E-Stop                  |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|     .................                  2. HIERARCHICAL ARCHITECTURE                            |
|        Cell Supervisor A (Welding)   <--->   Cell Supervisor B (Metrology)    |
|        • Sub-task decomposition              • Deadlock arbitration           |
|        • Regional quota management           • Emergency token subsidy        |
+-------------------------------------------------------------------------------+
         |                                                       |
         v                                                       v
+-------------------------------------------------------------------------------+
|                  6. BLACKBOARD | SHARED-STATE ARCHITECTURE                   |
|           • In-Memory Shared Workspace    • Dynamic Spot Price Oracle         |
|           • Pub/Sub Event Bus             • Open RFP Bidding Bulletin         |
+-------------------------------------------------------------------------------+
         |
         +---------------------------------------+
         |                                       |
         v                                       v
+---------------------------------+     +---------------------------------+
|   3. DE-CENTRALIZED ARCHITECTURE|     |   7. PEER-TO-PEER ARCHITECTURE  |
|  • Private Utility: U(Q, P, t)  |     |  • Rubinstein Alternating Offers|
|  • Concession: Boulware/Linear  | <-> |  • Contract Net Protocol (CNP)  |
|  • Autonomous Local Decisions   |     |  • Bilateral Power/Tool Barter  |
+---------------------------------+     +---------------------------------+
         |
         v
+-------------------------------------------------------------------------------+
|                     4. SEQUENTIAL | PIPELINE ARCHITECTURE                     |
|  M1 (Infeed) ===> M2 (Welder) ===> M3 (Sealant) ===> M4 (Fastener) ===> ...   |
|   • Workpiece Data Contracts passing tolerance drift, thermal profiles & bead |
|     offsets downstream for feedforward compensation.                          |
+-------------------------------------------------------------------------------+
         |
         v
+-------------------------------------------------------------------------------+
|                          5. PARALLEL ARCHITECTURE                             |
|  Concurrent Multi-Arm Thread-Pool Execution Engine with Power Lock Sync       |
+-------------------------------------------------------------------------------+
```

### Architecture Breakdown & Real-World Roles:
1. **CENTRALIZED (`CentralizedRegistry`)**:
   - Manages global factory safety envelope (100 kW ceiling), global emergency e-stop, and immutable transaction audit ledger.
2. **HIERARCHICAL (`CellSupervisorAgent`)**:
   - Supervisors oversee Cell A (Structural & Welding) and Cell B (Fastening & Metrology). They decompose macro-production orders, enforce cell quotas, and arbitrate P2P deadlocks using Kalai-Smorodinsky compromise with emergency subsidies.
3. **DE-CENTRALIZED (`ManipulatorAgent`)**:
   - Each manipulator arm evaluates decisions autonomously using private valuation models, dynamic reservation thresholds $U_{reserve}$, and multi-issue utility functions.
4. **SEQUENTIAL | PIPELINE (`AssemblyPipelineEngine`)**:
   - Workpieces traverse 6 sequential stages ($M_1 \to M_2 \to M_3 \to M_4 \to M_5 \to M_6$). Upstream agents emit rich **Workpiece Data Contracts** (jig misalignment, weld penetration, thermal expansion), allowing downstream arms to dynamically adapt their toolpaths and torque.
5. **PARALLEL (`ParallelExecutionEngine`)**:
   - Multi-threaded execution engine enabling concurrent multi-station assembly operations while dynamically avoiding power and spatial contention.
6. **BLACKBOARD | SHARED-STATE (`BlackboardSharedState`)**:
   - Thread-safe shared knowledge board with topic-based pub/sub, spot pricing bulletin for power/compute, resource lease locks, and open RFPs.
7. **PEER-TO-PEER (`P2PNegotiator`)**:
   - Direct bilateral bargaining implementing **Rubinstein Alternating Offers** and **Contract Net Protocol (CNP)** to trade power quotas and specialized toolheads without central bottlenecks.

---

## 🧮 Game-Theoretic Negotiation Mathematics

### 1. Multi-Issue Agent Utility Formulation
$$U_i(Q, P, t) = w_q \cdot \left(\frac{Q}{Q_{max}}\right) + w_p \cdot \left(1 - \frac{P}{P_{max}}\right) - w_t \cdot \left(\frac{t}{T_{deadline}}\right)^\beta$$
- $Q$: Resource quantity (e.g. kW power or GPU tokens).
- $P$: Token price offered.
- $t$: Current bargaining round.
- $\beta$: Concession strategy exponent.

### 2. Concession Curves
- **Boulware** ($\beta < 1$): Stubborn bargainer; holds firm until the deadline approaches, then rapidly concedes.
- **Conceder** ($\beta > 1$): Eager bargainer; quickly concedes to guarantee agreement and avoid deadlock.
- **Linear** ($\beta = 1$): Constant, predictable concession rate.

### 3. Pareto Efficiency & Nash Bargaining Solution
$$\max_{S} (U_{buyer}(S) - U_{reserve}^{buyer}) \cdot (U_{seller}(S) - U_{reserve}^{seller})$$

---

## 📦 Project Structure

```
e:/agentic_ai_project/
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py                  # Pydantic schemas, Enums, Contracts
│   │   ├── blackboard.py              # Arch 6: Shared State & PubSub
│   │   ├── centralized_arbiter.py     # Arch 1: Central Safety & Ledger
│   │   ├── hierarchical_supervisor.py # Arch 2: Cell Supervisors & Arbitration
│   │   ├── decentralized_agent.py     # Arch 3: Autonomous Arm Agent
│   │   ├── p2p_negotiator.py          # Arch 7: Rubinstein P2P Bargaining
│   │   ├── pipeline_orchestrator.py   # Arch 4: Sequential Data Contracts
│   │   └── parallel_engine.py         # Arch 5: Concurrent Multi-Arm Threading
│   ├── simulation/
│   │   ├── __init__.py
│   │   ├── assembly_environment.py    # Digital Twin Environment
│   │   └── scenarios.py               # 5 Industrial Benchmark Scenarios
│   └── ui/
│       ├── __init__.py
│       └── app.py                     # Rich Python Gradio Dashboard
├── tests/
│   ├── test_architectures.py          # Unit tests for all 7 architectures
│   └── test_negotiation.py            # Game-theoretic & Pareto tests
├── run.py                             # CLI & Web Launcher
└── README.md
```

---

## 🚀 Quickstart & Execution

### 1. Run Interactive Gradio Web Dashboard
```bash
python run.py --port 7860
```
Open your browser to: `http://127.0.0.1:7860`

#### Dashboard Features:
- **🏭 Assembly Digital Twin**: Live status cards for all 6 arms with real-time power, token budgets, and step triggers.
- **🏛️ 7-Architecture Topology**: Interactive Plotly activity bar charts and architectural map.
- **⚖️ Game-Theoretic Suite**: Live Pareto frontier curves, Nash equilibrium points, and round-by-round offer transcripts.
- **🔄 Pipeline Explorer**: Data contract inspector showing thermal compensation and feedforward defect correction.
- **🚀 1-Click Scenario Benchmarks**: Run peak power contention, deadlock escalation, and parallel stress tests.

### 2. Run Headless Automated Benchmarks
```bash
python run.py --cli
```

### 3. Run Pytest Suite
```bash
python -m pytest tests/ -v
```

