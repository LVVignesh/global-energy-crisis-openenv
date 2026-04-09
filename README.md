---
title: Global Energy Crisis Simulator
emoji: 🏙️
colorFrom: red
colorTo: yellow
sdk: docker
pinned: false
tags:
  - openenv
---

# 🏙️ Global Energy Crisis: Logistics & Geopolitical Simulator (Round 1)

**Participant:** Vignesh LV | **Category:** Real-World Task Simulation | **OpenEnv Verified**

## 🌐 Environment Motivation
This environment simulates a high-stakes Geopolitical Energy Crisis, requiring a Crisis Logistics AI to manage a constrained Strategic Global Reserve (Fuel). Unlike simple games, this simulator models a **real-world logistics bottleneck**: fuel must be allocated across four critical sectors, but failure to prioritize **Transport** (Supply Chains) leads to a systemic breakdown where fuel cannot be efficiently delivered to Hospitals or Emergency services.

### 🏆 30% Real-World Utility
This environment models a genuine task: **Strategic Resource Allocation**. It evaluates an agent's ability to prioritize long-term supply chain stability (Transport) over short-term critical needs (Hospitals) under severe scarcity.

## 🛠️ Environment Interface

### Action Space (Pydantic: `TaskAction`)
The agent provides a dictionary of fuel allocations (integers):
- `fuel_to_hospital`: 🏥 Priority 1 (Crucial for life safety)
- `fuel_to_emergency`: 🚨 Priority 2 (Relief vehicles & Fire services)
- `fuel_to_transport`: 🚛 **Tactical Priority** (Logistics & Supply Chain)
- `fuel_to_residential`: 🏠 Priority 4 (Grid stability)

### Observation Space (Pydantic: `TaskObservation`)
The agent receives a full tactical report:
- `fuel_available`: Units remaining in the Strategic Reserve.
- `hospital_demand`: Units required to prevent generator failure.
- `emergency_demand`: Units required for ongoing response.
- `transport_demand`: **Critical Variable** (Impacts delivery efficiency).
- `residential_demand`: Units for civilian grid stability.
- `message`: Intelligence report on logistics bottlenecks.

## 🏅 Strategic Tasks & Gradual Difficulty

| Task ID | Name | Difficulty | Resources | Objective |
| :--- | :--- | :--- | :--- | :--- |
| `easy` | Baseline Crisis | Easy | 160 Units | Implement immediate sector stability. |
| `medium` | Scarcity Protocol | Medium | 120 Units | Manage prioritized depletion with moderate reserves. |
| `hard` | Logistics Bottleneck | Hard | 80 Units | Solve the Supply Chain deadlock by prioritizing Transport. |

## 📐 Crisis Rules & Scoring Logic

To succeed, an agent must master three "Hidden" mechanics that separate high-performing LLMs from standard chat models:

1.  **Episode Persistence**: Every mission lasts **exactly 5 steps**. Success is measured by the **Final Mission Score** (clamped 0-1) accumulated across the entire crisis, visible in the log upon completion.
2.  **The "Supply Chain" Bottleneck (HARD Mode Only)**: 
    *   **The Rule**: If the `transport_demand` is **greater than 5**, a systemic logistics deadlock occurs.
    *   **The Penalty**: All fuel sent to **Hospitals** and **Emergency** services will be **90% less effective** (multiplier 0.1).
    *   **The Solution**: The agent *must* prioritize clearing the roads (reducing transport demand below 5) first.

## 🧪 The Frontier Challenge: Research Insights

This simulator is designed as a **Frontier Benchmark** for testing the limits of LLM planning and strategic reasoning under scarcity:

*   **Easy Mode**: Intended for baseline verification and standard agent training.
*   **Hard Mode**: A high-difficulty challenge even for Frontier LLMs (like Llama-3-8B). Success requires precise multi-turn planning and strict mastery of the Logistics Bottleneck.
*   **Zero-Shot Baseline**: Our provided baseline (`inference.py`) serves as a starting point. Low scores on Hard mode are expected and demonstrate the complexity of the task, proving that this environment is a valid test of sophisticated planning rather than simple pattern matching.

3.  **Weighted Priority Rewards**:
    *   **Hospitals (40% Weighting)**: The primary moral objective.
    *   **Emergency (30% Weighting)**: Immediate secondary response.
    *   **Transport (20% Weighting)**: The critical enabler of the city.
    *   **Residential (10% Weighting)**: Essential for civilian stability.
    
The reward is normalized by total weighted demand (30.5), ensuring fair scoring across all difficulty modes.

## 🚀 Setup & Execution

### Local Development
1. **Clone & Install**: `pip install -r requirements.txt`
2. **Launch Server**: `uvicorn server.app:app --port 7860`
3. **Execute Baseline**: `python inference.py`

### Docker Build
```bash
docker build -t global-crisis-env .
docker run -p 7860:7860 global-crisis-env
```

## 📊 Baseline Evaluation
The environment uses a specialized reward function (0.0 - 1.0) based on weighted demand fulfillment and supply chain efficiency.

**Elite Simulation Features:**
- **Deterministic Seeding**: Implements `random.seed(seed)` for 100% reproducibility in benchmarks.
- **Calibrated Fairness**: Reward scaling is normalized against total weighted demand, ensuring "Easy" and "Hard" modes are mathematically comparable.

**Target Mission Scores:**
- **EASY**: 0.9 - 1.0/1.0 (Full Sector Stability)
- **MEDIUM**: 0.7 - 0.9/1.0 (Prioritized Sector Survival)
- **HARD**: 0.4 - 0.6/1.0 (Demonstrated Bottleneck Logic)

## 🧪 Baseline Failure Insight
Baseline LLM agents (e.g., Meta-Llama-3-8B-Instruct) consistently fail to plan fuel allocation across multiple timesteps. As demonstrated in our logs, these agents exhibit panic logic—exhausting strict reserves early (Step 1 or 2) and causing late-stage collapse (Steps 3-5 with 0.00 rewards). 

This demonstrates that the environment requires **temporal reasoning and long-term planning**, making it a highly suitable and challenging benchmark for Reinforcement Learning research beyond standard prompt-based agents.

---

