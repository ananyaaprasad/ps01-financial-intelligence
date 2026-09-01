"""
FastAPI Backend Server (Stages 1-5 Integration)
Main application entry point exposing REST API for the financial intelligence system.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

from app.models.schemas import (
    StockMarketData,
    SynthesizedRecommendation,
    UserProfile,
    SessionMetricLog,
    SignalType
)
from app.data.market_simulator import get_market_simulator
from app.data.database import get_db_manager
from app.agents.synthesis_agent import get_synthesis_orchestrator

app = FastAPI(
    title="PS-01 Financial Intelligence System",
    description="Multi-Agent Autonomous Financial Intelligence for Retail Investors",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Hackathon demo - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Singletons
market_sim = get_market_simulator()
db_manager = get_db_manager()
orchestrator = get_synthesis_orchestrator()


@app.get("/")
async def root():
    return {
        "project": "PS-01: Multi-Agent Autonomous Financial Intelligence System",
        "status": "operational",
        "endpoints": {
            "market_data": "/api/market/{ticker}",
            "all_stocks": "/api/market/stocks",
            "user_profile": "/api/users/{user_id}",
            "recommendation": "/api/recommend",
            "metrics": "/api/metrics"
        }
    }


@app.get("/api/market/stocks", response_model=List[StockMarketData])
async def get_all_stocks():
    """Get current market data for all simulated equities."""
    return market_sim.get_all_market_data()


@app.get("/api/market/{ticker}", response_model=StockMarketData)
async def get_market_data(ticker: str):
    """Get current market data for a specific ticker."""
    try:
        return market_sim.get_current_market_data(ticker.upper())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/users", response_model=List[Dict[str, Any]])
async def list_users():
    """List all available user profiles."""
    return db_manager.list_all_users()


@app.get("/api/users/{user_id}", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get user profile with live portfolio valuation."""
    # Fetch current market prices for portfolio valuation
    all_market = market_sim.get_all_market_data()
    prices = {s.ticker: s.indicators.current_price for s in all_market}

    profile = db_manager.get_user_profile(user_id, market_prices=prices)
    if not profile:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return profile


@app.post("/api/recommend", response_model=SynthesizedRecommendation)
async def generate_recommendation(
    ticker: str,
    user_id: str = "user_moderate",
    simulate_degradation: Optional[str] = None
):
    """
    Generate multi-agent recommendation for a ticker + user profile.

    Args:
        ticker: Stock ticker to analyze
        user_id: User profile ID (default: user_moderate)
        simulate_degradation: Optional degradation test flag (MOMENTUM_FAIL, SENTIMENT_FAIL, FUNDAMENTALS_FAIL)

    Returns:
        SynthesizedRecommendation with full agent traces
    """
    try:
        # 1. Get market data
        market_data = market_sim.get_current_market_data(ticker.upper())

        # 2. Get user profile
        all_market = market_sim.get_all_market_data()
        prices = {s.ticker: s.indicators.current_price for s in all_market}
        user_profile = db_manager.get_user_profile(user_id, market_prices=prices)

        if not user_profile:
            raise HTTPException(status_code=404, detail=f"User {user_id} not found")

        # 3. Execute multi-agent pipeline
        recommendation = await orchestrator.execute_multi_agent_pipeline(
            market_data=market_data,
            user_profile=user_profile,
            simulate_degradation=simulate_degradation
        )

        # 4. Record recommendation in history
        db_manager.record_recommendation(user_id, recommendation)

        # 5. Log session metrics (Stage 5)
        session_id = str(uuid.uuid4())[:8]

        # Calculate portfolio risk concentration (Herfindahl index)
        if user_profile.portfolio:
            weights = [item.weight_pct / 100.0 for item in user_profile.portfolio]
            herfindahl = sum(w**2 for w in weights)
        else:
            herfindahl = 0.0

        # Extract agent latencies
        agent_latencies = {
            trace.dimension.value: trace.execution_time_ms
            for trace in recommendation.agent_traces
        }

        # Directional accuracy check
        if recommendation.simulated_30d_forward_return is not None:
            is_bullish = recommendation.overall_signal in [SignalType.STRONG_BUY, SignalType.BUY]
            is_bearish = recommendation.overall_signal in [SignalType.STRONG_SELL, SignalType.SELL]
            ret_positive = recommendation.simulated_30d_forward_return > 0

            directionally_correct = (
                (is_bullish and ret_positive) or
                (is_bearish and not ret_positive) or
                (recommendation.overall_signal == SignalType.HOLD and abs(recommendation.simulated_30d_forward_return) < 0.03)
            )
        else:
            directionally_correct = False

        metric_log = SessionMetricLog(
            session_id=session_id,
            ticker=ticker.upper(),
            recommended_signal=recommendation.overall_signal,
            composite_confidence=recommendation.composite_confidence,
            simulated_30d_return=recommendation.simulated_30d_forward_return or 0.0,
            directionally_correct=directionally_correct,
            total_pipeline_latency_ms=sum(agent_latencies.values()),
            agent_latencies_ms=agent_latencies,
            portfolio_risk_concentration=round(herfindahl, 4),
            timestamp=datetime.utcnow().isoformat()
        )

        db_manager.record_session_metric(metric_log)

        return recommendation

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@app.get("/api/metrics", response_model=Dict[str, Any])
async def get_metrics_summary():
    """Get Stage 5 aggregated metrics: accuracy proxy, latencies, portfolio risk."""
    return db_manager.get_session_metrics_summary()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
