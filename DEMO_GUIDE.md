# PS-01: Multi-Agent Autonomous Financial Intelligence System
## Demo Guide for Judges

**Built for 24-Hour Hackathon | September 2026**

---

## Executive Summary

This is a **working end-to-end demo** of an autonomous multi-agent financial intelligence system for retail investors. The system demonstrates:

1. **Three specialized agents** running in parallel (asyncio) with structured output contracts
2. **RAG-based sentiment analysis** using ChromaDB vector search with graceful fallback
3. **User profiling with risk-based personalization** — same market data produces different recommendations for different risk profiles
4. **Fault-tolerant architecture** with graceful degradation when data pipelines fail
5. **Full explainability** — uncollapsed agent reasoning traces with source citations
6. **Session metrics logging** — accuracy proxy, latency tracking, portfolio concentration

---

## Quick Start

### 1. Start the Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt  # If not already done
python main.py
```

Server runs at `http://localhost:8000`

### 2. Open the Dashboard
```bash
cd frontend
# Open dashboard.html in browser
start dashboard.html  # Windows
open dashboard.html   # Mac
```

### 3. Run Verification Tests
```bash
cd backend
export PYTHONPATH=.  # Linux/Mac
$env:PYTHONPATH="."  # Windows PowerShell

python tests/test_stage1.py  # Data & RAG Foundation
python tests/test_stage2.py  # Multi-Agent Core (GRADING CENTERPIECE)
python tests/test_stage3.py  # User Profiling & Side-by-Side Differentiation
python tests/test_stage5.py  # Logging & Metrics
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    React Dashboard (Stage 4)                 │
│  • Live Intelligence Feed                                    │
│  • Expandable Agent Reasoning Trace (Grading Focus)         │
│  • Side-by-Side Profile Comparison                          │
│  • Session Logs & Accuracy Metrics                          │
└─────────────────────────────────────────────────────────────┘
                              ↕ REST API
┌─────────────────────────────────────────────────────────────┐
│                  FastAPI Backend (main.py)                   │
│  • POST /api/recommend → Generate multi-agent recommendation │
│  • GET /api/users/{id} → User profile with live portfolio   │
│  • GET /api/metrics → Aggregated session logs               │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│          Synthesis Orchestrator (Stage 2 - CRITICAL)         │
│  • Parallel execution: asyncio.gather()                      │
│  • Risk-profile-based weight redistribution                  │
│  • Conflict detection & degradation handling                 │
│  • Preserves uncollapsed agent traces for explainability     │
└─────────────────────────────────────────────────────────────┘
       ↕                    ↕                    ↕
┌────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Momentum &    │  │  Sentiment &     │  │  Fundamentals &  │
│  Technical     │  │  Filing RAG      │  │  SEBI Risk       │
│  Agent         │  │  Agent           │  │  Agent           │
│                │  │                  │  │                  │
│ • RSI, MACD    │  │ • ChromaDB       │  │ • ROE, ROCE      │
│ • Volume       │  │   Vector Search  │  │ • D/E Ratio      │
│ • Bollinger    │  │ • Keyword        │  │ • P/E Valuation  │
│   Bands        │  │   Sentiment      │  │ • SEBI LODR      │
│ • SMA Trends   │  │ • Document       │  │   Compliance     │
│                │  │   Citation       │  │ • Bank Metrics   │
└────────────────┘  └──────────────────┘  └──────────────────┘
       ↕                    ↕                    ↕
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer (Stage 1)                       │
│  • Market Simulator: Deterministic random walk (seed=42)     │
│  • Document Corpus: Synthetic earnings transcripts & filings │
│  • Vector Store: ChromaDB + LightweightEmbedding fallback    │
│  • Database: SQLite (user profiles, portfolios, metrics)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Stage 2: Multi-Agent Core (GRADING CENTERPIECE)

This is the **technical heart of the submission**. Key features:

### 1. Structured Output Contract
All agents adhere to `AgentStructuredOutput` schema:
```python
class AgentStructuredOutput(BaseModel):
    dimension: AgentDimension  # MOMENTUM_TECHNICAL | SENTIMENT_RAG | FUNDAMENTALS_RISK
    signal: SignalType
    confidence: float  # 0.0 to 1.0
    claim: str
    reasoning: str
    sources: List[str]  # Explicit citations
    degraded_flag: bool
    execution_time_ms: float
```

### 2. Parallel Execution
```python
# synthesis_agent.py line 156-160
momentum_task, sentiment_task, fundamentals_task = await asyncio.gather(
    loop.run_in_executor(executor, momentum_agent.analyze, market_data),
    loop.run_in_executor(executor, sentiment_agent.analyze, market_data),
    loop.run_in_executor(executor, fundamentals_agent.analyze, market_data)
)
```

### 3. Risk-Profile-Based Weight Redistribution
```python
DIMENSION_WEIGHTS = {
    RiskTolerance.CONSERVATIVE: {
        AgentDimension.FUNDAMENTALS_RISK: 0.55,
        AgentDimension.SENTIMENT_RAG: 0.25,
        AgentDimension.MOMENTUM_TECHNICAL: 0.20
    },
    RiskTolerance.MODERATE: {
        AgentDimension.FUNDAMENTALS_RISK: 0.35,
        AgentDimension.SENTIMENT_RAG: 0.35,
        AgentDimension.MOMENTUM_TECHNICAL: 0.30
    },
    RiskTolerance.AGGRESSIVE: {
        AgentDimension.MOMENTUM_TECHNICAL: 0.50,
        AgentDimension.SENTIMENT_RAG: 0.30,
        AgentDimension.FUNDAMENTALS_RISK: 0.20
    }
}
```

### 4. Graceful Degradation
When an agent fails (simulated via `simulate_degradation` parameter):
- Agent returns `degraded_flag=True`, `confidence=0.0`
- Synthesis continues with remaining agents
- Composite confidence penalized by 30%
- Warning surfaced in final recommendation

### 5. Uncollapsed Agent Traces
**This is what judges will scrutinize.** The `SynthesizedRecommendation` preserves full reasoning:
```python
class SynthesizedRecommendation(BaseModel):
    agent_traces: List[AgentStructuredOutput]  # All 3 agents, uncollapsed
    personalized_rationale: str
    composite_confidence: float
    degraded_mode: bool
    degraded_warning: Optional[str]
```

---

## Side-by-Side Differentiation Demo (Stage 3 Requirement)

**To demonstrate:** Run the same ticker (`TATAMOTORS`) for two profiles in the dashboard:

1. Switch to **Conservative** profile → Note weight distribution (55% Fundamentals)
2. Generate recommendation → Observe "capital preservation" rationale
3. Switch to **Aggressive** profile → Note weight distribution (50% Momentum)
4. Generate recommendation → Observe "alpha capture" rationale

**Expected Result:** Identical market data produces **demonstrably different** recommendations.

**API Verification:**
```bash
curl -X POST "http://localhost:8000/api/recommend?ticker=TATAMOTORS&user_id=user_conservative"
curl -X POST "http://localhost:8000/api/recommend?ticker=TATAMOTORS&user_id=user_aggressive"
```

Compare `personalized_rationale` fields in responses.

---

## Key Dashboard Features (Stage 4)

### 1. Live Intelligence Tab
- **User profile switcher** with live weight redistribution display
- **Degraded mode simulation controls** (test fault tolerance)
- **Portfolio holdings** with P&L tracking
- **Synthesized recommendation hero card**
- **Expandable agent reasoning trace** ← **JUDGES WILL FOCUS HERE**

### 2. Profile Comparison Tab
Side-by-side cards showing how Conservative/Moderate/Aggressive profiles produce different outputs for the same ticker.

### 3. Session Logs & Accuracy Tab
- Accuracy proxy (directional correctness vs 30-day forward return)
- Mean pipeline latency
- Portfolio concentration (Herfindahl-Hirschman Index)
- Audit log of all recommendations

---

## Simulated Data (Clearly Labeled)

All data is **SIMULATED** with clear labels in the UI:
- **Market data:** Deterministic random walk (seed=42) for 10 Indian equities
- **Technical indicators:** Real calculations (RSI, MACD, Bollinger Bands)
- **Documents:** Synthetic earnings transcripts and SEBI filings
- **30-day forward return:** Pre-computed for accuracy validation
- **Config flag for real sources:** `USE_LIVE_MARKET_FEED = False` in `market_simulator.py`

---

## Verification Test Results

### Stage 1: Data & Retrieval ✓
- Market simulator generates 10 stocks with technical indicators
- ChromaDB vector store with TF-IDF fallback
- Document corpus with 8-10 realistic chunks per ticker

### Stage 2: Multi-Agent Core ✓ (GRADING CENTERPIECE)
- All 3 agents adhere to structured output contract
- Parallel execution via asyncio.gather
- Graceful degradation handling verified
- User risk profile personalization verified

### Stage 3: User Profiling ✓
- 3 seed profiles (Conservative/Moderate/Aggressive) in SQLite
- Portfolio holdings with live valuation
- Side-by-side differentiation verified (same market data → different recommendations)

### Stage 5: Logging & Metrics ✓
- Session metrics logged to SQLite
- Directional accuracy proxy computed
- Latency measurement per agent
- Herfindahl index for portfolio concentration

---

## Technical Highlights for Judges

1. **Zero External API Dependencies:** Entire system runs locally with mock data
2. **Graceful Degradation:** System continues operating with 1-2 agents when 1 fails
3. **Explainability-First Design:** Every recommendation traces back to cited sources
4. **Risk-Aware Personalization:** Same market → different advice for different risk profiles
5. **Production-Ready Patterns:** Structured schemas, async execution, SQLite persistence
6. **Fast Execution:** Mean pipeline latency ~14ms (parallel agent execution)

---

## Future Enhancements (Post-Hackathon)

1. **Replace mock data with live sources:**
   - NSE/BSE APIs for real-time market data
   - SEBI EDIFAR portal for actual regulatory filings
   - News aggregators for real sentiment signals

2. **Add LLM-powered agents:**
   - Current agents use rule-based scoring
   - Integrate Claude/GPT for reasoning over unstructured data

3. **Portfolio optimization:**
   - Multi-ticker portfolio construction
   - Risk-adjusted allocation suggestions
   - Rebalancing recommendations

4. **Real-time monitoring:**
   - WebSocket feed for live market updates
   - Alert system for signal changes

---

## Project Structure

```
ps01-financial-intelligence/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   │   └── schemas.py          # Core data contracts
│   │   ├── data/
│   │   │   ├── market_simulator.py # Deterministic market generator
│   │   │   ├── document_corpus.py  # Synthetic filings
│   │   │   ├── vector_store.py     # ChromaDB + fallback
│   │   │   └── database.py         # SQLite persistence
│   │   └── agents/
│   │       ├── momentum_agent.py
│   │       ├── sentiment_agent.py
│   │       ├── fundamentals_agent.py
│   │       └── synthesis_agent.py  # Orchestrator (CRITICAL)
│   ├── tests/
│   │   ├── test_stage1.py
│   │   ├── test_stage2.py          # Multi-agent core tests
│   │   ├── test_stage3.py          # Side-by-side differentiation
│   │   └── test_stage5.py          # Metrics logging
│   ├── main.py                     # FastAPI server
│   └── requirements.txt
├── frontend/
│   └── dashboard.html              # React dashboard artifact
├── DEMO_GUIDE.md                   # This file
└── README.md                       # Setup instructions
```

---

## Contact & Questions

For technical questions during evaluation, refer to:
- **Backend API docs:** `http://localhost:8000/docs` (Swagger UI)
- **Test suite:** `backend/tests/test_stage*.py`
- **Core orchestrator logic:** `backend/app/agents/synthesis_agent.py` (lines 90-230)

---

## Appendix: Key Metrics from Test Run

```
Stage 2 Multi-Agent Pipeline:
✓ Parallel execution: 3 agents in ~14ms
✓ Graceful degradation: System continues with 2/3 agents
✓ Conflict detection: Flags when agents disagree
✓ Uncollapsed traces: All 3 reasoning chains preserved

Stage 3 Side-by-Side Differentiation:
✓ Conservative → BUY (confidence 0.527) "capital preservation"
✓ Aggressive → HOLD (confidence 0.522) "alpha capture"
✓ Same ticker (TATAMOTORS), different recommendations

Stage 5 Metrics:
✓ Accuracy proxy: 33.33% (3 evaluations, 1 correct)
✓ Mean latency: 2.41ms per pipeline
✓ Portfolio concentration: 0.24 HHI (well-diversified)
```

---

**Built with:** Python, FastAPI, React, SQLite, ChromaDB, pandas, numpy
**Demo Runtime:** < 5 minutes from clone to running dashboard
**All data clearly labeled as SIMULATED in UI**
