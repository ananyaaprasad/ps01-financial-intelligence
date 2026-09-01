# PS-01: Multi-Agent Autonomous Financial Intelligence System

A real-time financial intelligence platform leveraging parallel multi-agent architecture to deliver personalized investment recommendations for retail investors. Built with FastAPI, React, and asyncio-powered agent orchestration.

## Architecture Overview

### Multi-Agent System
The platform coordinates three specialized autonomous agents operating in parallel:

- **Momentum/Technical Agent**: Analyzes price action, technical indicators (RSI, MACD, Bollinger Bands), breakout patterns, and volume trends
- **Sentiment/RAG Agent**: Performs vector-similarity search over regulatory filings, earnings transcripts, and news documents to extract sentiment signals
- **Fundamentals/Risk Agent**: Evaluates balance sheet health, P/E ratios, debt metrics, SEBI compliance scores, and governance risk

### Orchestration & Synthesis
A central **Synthesis Agent** coordinates parallel agent execution via asyncio, reconciles consensus/conflicts across dimensions, and applies dynamic weighting based on user risk profiles (Conservative, Moderate, Aggressive). The system implements graceful degradation when data sources become unavailable, penalizing confidence scores and surfacing warnings to users.

### Real-Time Market Simulation
Deterministic random-walk price generator produces synthetic OHLCV data for 10 Indian equities across sectors (Energy, IT, Banking, Automotive, Telecom, FMCG). Seeded for repeatability during evaluation.

### Vector Store & RAG
ChromaDB-backed vector store using `sentence-transformers` for semantic search over document corpus. Supports metadata filtering by ticker, document type, and date range. Returns top-k chunks with similarity scores for agent reasoning.

## Technology Stack

### Backend
- **FastAPI 0.141.1**: REST API with CORS middleware
- **Uvicorn 0.52.4**: ASGI server
- **Pydantic 2.13.4**: Schema validation & structured outputs
- **ChromaDB 0.4.24**: Vector similarity search
- **sentence-transformers 2.5.1**: `all-MiniLM-L6-v2` embeddings
- **aiosqlite 0.19.0**: Async database for session/metric logging
- **NumPy 2.2.4 / Pandas 2.2.3**: Numerical computation & time-series analysis

### Frontend
- **React 18 (UMD)**: Component architecture with hooks (useState, useEffect, useMemo, useRef, useCallback)
- **Chart.js 4.4.0**: Real-time streaming price charts with 5-tick moving average overlay
- **Tailwind CSS 3.4.1**: Utility-first styling via CDN play mode
- **Browser-native**: Single-file HTML deployment, no build step required

## Project Structure

```
ps01-financial-intelligence/
├── backend/
│   ├── main.py                          # FastAPI application entry point
│   ├── requirements.txt                 # Python dependencies
│   ├── app/
│   │   ├── agents/
│   │   │   ├── momentum_agent.py        # Technical analysis agent
│   │   │   ├── sentiment_agent.py       # RAG-powered sentiment agent
│   │   │   ├── fundamentals_agent.py    # Risk/balance sheet agent
│   │   │   └── synthesis_agent.py       # Orchestrator & weighted synthesis
│   │   ├── data/
│   │   │   ├── market_simulator.py      # Deterministic price generator
│   │   │   ├── document_corpus.py       # Synthetic filing/news corpus
│   │   │   ├── vector_store.py          # ChromaDB wrapper & retrieval
│   │   │   └── database.py              # Session metrics & logging
│   │   ├── models/
│   │   │   └── schemas.py               # Pydantic models for API contracts
│   │   └── utils/
│   ├── tests/
│   │   ├── test_stage1.py               # Market data & vector retrieval tests
│   │   ├── test_stage2.py               # Multi-agent parallelism tests
│   │   ├── test_stage3.py               # User personalization tests
│   │   └── test_stage5.py               # Fault tolerance & degradation tests
│   └── data/
│       └── chroma_db/                   # Persisted vector embeddings
├── frontend/
│   ├── dashboard.html                   # Main dashboard (Antigravity theme)
```

## Installation & Setup

### Prerequisites
- Python 3.12+
- Modern browser with ES2020+ support (Chrome 90+, Firefox 88+, Safari 14+)

### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Initialize vector store (first run only)
python -c "from app.data.vector_store import get_vector_store; get_vector_store()"

# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server runs at `http://localhost:8000`  
API documentation: `http://localhost:8000/docs`

### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Open dashboard in browser (no build required)
# Windows:
start dashboard.html

# macOS:
open dashboard.html

# Linux:
xdg-open dashboard.html
```

The dashboard connects to the backend at `http://localhost:8000` via CORS-enabled REST endpoints.

## API Endpoints

### Market Data
- `GET /api/market/{ticker}` - Real-time market data for a single equity
- `GET /api/market/all` - All 10 simulated equities with current prices

### Agent Analysis
- `POST /api/analyze/{ticker}` - Run multi-agent analysis with synthesis
  - **Query Parameters**: `user_profile` (conservative/moderate/aggressive)
  - **Response**: Synthesized recommendation with agent traces, confidence scores, reasoning chains, and cited sources

### Session Management
- `POST /api/session/log` - Log user interaction metrics
- `GET /api/health` - System health check

### Example Request
```bash
curl -X POST "http://localhost:8000/api/analyze/RELIANCE?user_profile=moderate" \
  -H "Content-Type: application/json"
```

### Example Response
```json
{
  "ticker": "RELIANCE",
  "signal": "BUY",
  "confidence": 0.74,
  "suggested_allocation_pct": 12.5,
  "personalized_rationale": "Moderate investor: Strong fundamentals (0.0% promoter pledge) combined with positive momentum breakout. Sentiment is neutral but fundamentals are solid.",
  "agent_outputs": [
    {
      "dimension": "MOMENTUM_TECHNICAL",
      "signal": "BUY",
      "confidence": 0.82,
      "claim": "Bullish breakout detected with RSI at 64.2",
      "reasoning": "Price crossed above 20-day SMA with increasing volume...",
      "sources": ["RSI(14): 64.2", "MACD: +12.5", "Volume spike: +18%"],
      "latency_ms": 42
    }
    // ... other agents
  ],
  "is_degraded": false,
  "consensus_level": "STRONG"
}
```

## Key Features

### 1. Real-Time Streaming Architecture
- Autonomous tick generation with configurable interval (default: 800ms)
- Flash animations on price changes (green/red)
- Live Chart.js canvas updates with 5-tick moving average
- Micro-indicator panel (RSI, P/E, Beta, 30D Forward Return)

### 2. Personalized Risk Profiles
Dynamic agent weighting based on user tolerance:

| Profile | Fundamentals | Sentiment | Momentum |
|---------|-------------|-----------|----------|
| Conservative | 55% | 25% | 20% |
| Moderate | 35% | 35% | 30% |
| Aggressive | 20% | 30% | 50% |

### 3. Uncollapsed Reasoning Traces
All agent outputs preserved and rendered in UI:
- Step-by-step reasoning chains
- Cited evidence sources with metadata
- Individual confidence scores
- Parallel execution latencies

### 4. Graceful Degradation
When data pipelines fail:
- System detects missing vector store results or API failures
- Penalizes composite confidence by 30%
- Surfaces amber warning banner to user
- Continues operation with reduced certainty

### 5. Multi-Stock Portfolio Tracking
- Real-time P&L calculation across holdings
- Auto-updated total portfolio value
- Per-holding percentage gains/losses
- Cash reserve management

## Testing

### Run Test Suite
```bash
cd backend
python -m pytest tests/ -v
```

### Test Coverage
- **Stage 1**: Market simulator repeatability, document corpus, vector top-k retrieval
- **Stage 2**: Agent structured output contracts, parallel asyncio execution, synthesis preservation
- **Stage 3**: User profile dynamic weighting, personalized rationale generation
- **Stage 5**: Degraded data handling, confidence penalization, fault tolerance

### Manual UI Testing
1. Start backend: `uvicorn main:app --reload`
2. Open `frontend/dashboard.html`
3. Click **Start Streaming** to activate autonomous market updates
4. Switch between user profiles (Conservative/Moderate/Aggressive) to observe weight reallocation
5. Select different tickers from live feed ribbon
6. Expand agent traces to view reasoning chains
7. Monitor synthesis confidence and suggested allocation updates

## Configuration

### Market Simulator
Edit `backend/app/data/market_simulator.py`:
- `SIMULATED_STOCKS`: Add/modify tickers, base prices, sectors
- `seed`: Change random seed for different price trajectories
- `lookback_days`: Adjust historical data window (default: 252 trading days)

### Agent Weights
Edit `backend/app/agents/synthesis_agent.py`:
- `PROFILE_DIMENSION_WEIGHTS`: Modify risk profile allocations
- `SIGNAL_NUMERICAL_WEIGHT`: Adjust signal strength mappings
- `CONFIDENCE_PENALTY_DEGRADED`: Change degradation penalty (default: 0.3)

### Vector Store
Edit `backend/app/data/vector_store.py`:
- `EMBEDDING_MODEL`: Change sentence-transformer model
- `CHROMA_PERSIST_DIR`: Relocate vector database
- `top_k`: Modify retrieval count per query

## Performance Characteristics

- **Agent Latency**: 30-80ms per agent (parallel execution)
- **End-to-End Synthesis**: ~100ms for 3-agent orchestration
- **Vector Retrieval**: ~15ms for top-5 semantic search
- **Market Tick Update**: <5ms per stock update
- **Chart Render**: 60 FPS via Chart.js canvas with requestAnimationFrame

## Deployment Considerations

### Production Checklist
- [ ] Replace CORS `allow_origins=["*"]` with explicit frontend domain
- [ ] Connect real market data API (replace `MarketDataSimulator`)
- [ ] Implement user authentication & session management
- [ ] Add rate limiting on `/api/analyze` endpoint
- [ ] Enable HTTPS with valid TLS certificate
- [ ] Configure database connection pooling for `aiosqlite`
- [ ] Set up monitoring (Prometheus/Grafana) for agent latencies
- [ ] Implement caching layer (Redis) for frequently-accessed tickers
- [ ] Add request logging & audit trails
- [ ] Review SEBI regulatory compliance requirements

### Scaling Recommendations
- **Horizontal**: Deploy multiple FastAPI workers behind Nginx load balancer
- **Agent Parallelism**: Current asyncio model scales to ~100 concurrent synthesis requests per worker
- **Vector Store**: Migrate ChromaDB to Pinecone/Weaviate for >1M documents
- **Database**: Migrate from SQLite to PostgreSQL for multi-user sessions

## Theme Variants

The platform includes two UI themes:

### Antigravity Theme (`dashboard.html`)
Clean, professional financial dashboard with blue/slate color palette. Production-ready design.

## Dependencies

### Python Backend
```
fastapi==0.141.1
uvicorn==0.52.4
pydantic==2.13.4
numpy==2.2.4
pandas==2.2.3
chromadb==0.4.24
sentence-transformers==2.5.1
aiosqlite==0.19.0
python-multipart==0.0.9
```

### Frontend (CDN)
```html
<!-- React 18.3.1 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.production.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.production.min.js"></script>

<!-- Chart.js 4.4.0 -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>

<!-- Tailwind CSS 3.4.1 -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- Google Fonts -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
```

## License

This project was developed as part of a hackathon demonstration. All market data is synthetically generated and should not be used for actual investment decisions.

## Disclaimer

**This system is for educational and demonstration purposes only.** The platform uses simulated market data and does not provide actual financial advice. Consult a registered financial advisor before making investment decisions. The authors assume no liability for financial outcomes resulting from use of this software.

## Support & Documentation

- **Demo Guide**: See `DEMO_GUIDE.md` for live presentation walkthrough
- **User Guide**: See `USER_GUIDE.md` for end-user instructions
- **Technical Deep-Dive**: See `TECHNICAL_GUIDE.md` for architecture details
- **Compliance Notes**: See `COMPLIANCE_CHECKLIST.md` for regulatory considerations
- **Future Roadmap**: See `ENHANCEMENTS.md` for planned features

## Author

Prasanna - Multi-Agent Financial Intelligence System  
Built with FastAPI, React, ChromaDB, and sentence-transformers
