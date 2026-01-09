# AGStock Agents & Investment Committee

The `src/agents` package implements the Multi-Agent System (MAS) that drives intelligent decision-making in AGStock.

## InvestmentCommittee (`committee.py`)

The `InvestmentCommittee` is the central hub where multiple AI agents debate and form a consensus on trading decisions.

### Initialization Structure

The `__init__` method is streamlined into four phases:

1. **Core Agents** (`_initialize_core_agents`)
   - `MarketAnalyst`: Technical analysis.
   - `RiskManager`: Risk assessment.
   - `MacroStrategist`: Global macro view.
   - *Note*: These are wrapped with `RLAgentWrapper` for reinforcement learning capabilities.

2. **Infrastructure** (`_initialize_infrastructure`)
   - `MacroLoader`, `EarningsHistory`, `FeedbackStore` for data.
   - `PositionSizer` for sizing logic.

3. **Specialists** (`_initialize_specialists`)
   - `DeepHunterRAG`: Research using RAG (Retrieval-Augmented Generation).
   - `ChartVisionEngine`: Visual chart analysis.
   - `IntuitionEngine`: "Gut feeling" based on pattern matching.

4. **Evolution** (`_initialize_evolution_modules`)
   - `DigitalTwin`: Simulation environment.
   - `AvatarCouncil`: Advanced persona-based debating.

## Key Interactions

- **`review_candidate(ticker, signal_data)`**:
  - The Committee takes a raw signal from the `FullyAutomatedTrader`.
  - Agents debate the signal.
  - Returns a `TradingDecision` (GO/NO-GO).

- **`hold_meeting(data)`**:
  - Conducts a broader market assessment meeting.

---

## Adding a New Agent

To add a new agent:
1. Create a class inheriting from `BaseAgent`.
2. Implement `analyze()` method.
3. Instantiate it in `InvestmentCommittee._initialize_specialists` (or appropriate helper).
4. Add it to the `self.agents` list if it participates in the voting loop.
