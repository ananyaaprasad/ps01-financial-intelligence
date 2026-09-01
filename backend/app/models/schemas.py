"""
Pydantic Schemas for Multi-Agent Autonomous Financial Intelligence System (PS-01).
Enforces structured output contracts across all agents and endpoints.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


class RiskTolerance(str, Enum):
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class SignalType(str, Enum):
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class AgentDimension(str, Enum):
    MOMENTUM_TECHNICAL = "MOMENTUM_TECHNICAL"
    SENTIMENT_RAG = "SENTIMENT_RAG"
    FUNDAMENTALS_RISK = "FUNDAMENTALS_RISK"
    SYNTHESIS_ORCHESTRATOR = "SYNTHESIS_ORCHESTRATOR"


class TechnicalIndicators(BaseModel):
    current_price: float
    open_price: float
    high_52w: float
    low_52w: float
    change_pct: float
    volume: int
    volume_surge_ratio: float  # current vol vs 20-day avg
    rsi_14: float
    macd: float
    macd_signal: float
    macd_histogram: float
    sma_20: float
    sma_50: float
    sma_200: float
    bollinger_upper: float
    bollinger_middle: float
    bollinger_lower: float
    atr_14: float
    simulated_30d_forward_return: Optional[float] = None  # for ground-truth accuracy tracking


class StockMarketData(BaseModel):
    ticker: str
    company_name: str
    sector: str
    timestamp: str
    indicators: TechnicalIndicators
    price_history: List[Dict[str, Any]] = Field(default_factory=list)
    source_type: str = "SIMULATED"


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    ticker: str
    company_name: str
    doc_type: str  # "EARNINGS_TRANSCRIPT", "SEBI_FILING", "ANNUAL_REPORT", "PRESS_RELEASE"
    title: str
    quarter: str
    date: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    similarity_score: Optional[float] = None


# Shared Structured Output Contract for all Agents (Grading requirement)
class AgentStructuredOutput(BaseModel):
    agent_id: str
    dimension: AgentDimension
    ticker: str
    claim: str = Field(description="Clear, concise core assertion or directional hypothesis")
    signal: SignalType = Field(description="Actionable classification label")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    reasoning: str = Field(description="Step-by-step reasoning explaining how the agent arrived at the claim")
    key_metrics: Dict[str, Any] = Field(default_factory=dict, description="Key numerical or categorical indicators used")
    sources: List[str] = Field(default_factory=list, description="Explicit citations to retrieved chunks, market indicators, or filing sections")
    degraded_flag: bool = Field(default=False, description="True if agent operated with incomplete or degraded data")
    degraded_reason: Optional[str] = None
    execution_time_ms: float = Field(default=0.0, description="Latency in milliseconds")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SynthesizedRecommendation(BaseModel):
    ticker: str
    company_name: str
    overall_signal: SignalType
    composite_confidence: float = Field(ge=0.0, le=1.0)
    executive_summary: str
    personalized_rationale: str
    user_risk_profile_applied: RiskTolerance
    suggested_allocation_pct: float
    conflict_detected: bool = False
    conflict_details: Optional[str] = None
    degraded_mode: bool = False
    degraded_warning: Optional[str] = None
    agent_traces: List[AgentStructuredOutput]
    simulated_30d_forward_return: Optional[float] = None
    accuracy_eval: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class UserPortfolioItem(BaseModel):
    ticker: str
    shares: int
    avg_buy_price: float
    current_price: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    weight_pct: float


class UserProfile(BaseModel):
    user_id: str = "retail_user_01"
    name: str = "Aarav Sharma"
    risk_tolerance: RiskTolerance = RiskTolerance.MODERATE
    investment_horizon_months: int = 12
    total_portfolio_value: float = 500000.0  # INR
    cash_balance: float = 120000.0
    portfolio: List[UserPortfolioItem] = Field(default_factory=list)
    watchlist: List[str] = Field(default_factory=lambda: ["RELIANCE", "TCS", "INFY", "HDFCBANK", "TATAMOTORS"])


class SessionMetricLog(BaseModel):
    session_id: str
    ticker: str
    recommended_signal: SignalType
    composite_confidence: float
    simulated_30d_return: float
    directionally_correct: bool
    total_pipeline_latency_ms: float
    agent_latencies_ms: Dict[str, float]
    portfolio_risk_concentration: float
    timestamp: str
