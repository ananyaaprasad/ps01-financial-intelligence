"""
Synthesis & Orchestrator Agent (Stage 2 & Stage 3)
Coordinates parallel agent execution (asyncio), reconciles consensus & conflict,
handles degraded data gracefully, and personalizes recommendations per user risk profile.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.models.schemas import (
    AgentStructuredOutput,
    AgentDimension,
    SignalType,
    StockMarketData,
    SynthesizedRecommendation,
    UserProfile,
    RiskTolerance
)
from app.agents.momentum_agent import MomentumTechnicalAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.fundamentals_agent import FundamentalsRiskAgent


# Signal numerical weights for mathematical synthesis
SIGNAL_NUMERICAL_WEIGHT = {
    SignalType.STRONG_BUY: 2.0,
    SignalType.BUY: 1.0,
    SignalType.HOLD: 0.0,
    SignalType.SELL: -1.0,
    SignalType.STRONG_SELL: -2.0,
}

# Dimension weights by user risk tolerance profile
PROFILE_DIMENSION_WEIGHTS = {
    RiskTolerance.CONSERVATIVE: {
        AgentDimension.FUNDAMENTALS_RISK: 0.55,
        AgentDimension.SENTIMENT_RAG: 0.25,
        AgentDimension.MOMENTUM_TECHNICAL: 0.20,
    },
    RiskTolerance.MODERATE: {
        AgentDimension.FUNDAMENTALS_RISK: 0.35,
        AgentDimension.SENTIMENT_RAG: 0.35,
        AgentDimension.MOMENTUM_TECHNICAL: 0.30,
    },
    RiskTolerance.AGGRESSIVE: {
        AgentDimension.MOMENTUM_TECHNICAL: 0.50,
        AgentDimension.SENTIMENT_RAG: 0.30,
        AgentDimension.FUNDAMENTALS_RISK: 0.20,
    },
}


class SynthesisOrchestratorAgent:
    """
    Multi-Agent Orchestrator:
    - Runs specialized agents concurrently via asyncio
    - Reconciles agent agreements and flags disagreements
    - Gracefully manages degraded data pipelines
    - Adapts synthesis based on user risk profiles
    - Preserves uncollapsed agent reasoning traces for complete explainability
    """

    def __init__(self, agent_id: str = "synthesis_orchestrator_01"):
        self.agent_id = agent_id
        self.momentum_agent = MomentumTechnicalAgent()
        self.sentiment_agent = SentimentAgent()
        self.fundamentals_agent = FundamentalsRiskAgent()

    async def _run_agent_async(self, agent_func, *args, **kwargs) -> AgentStructuredOutput:
        """Run synchronous agent analysis inside asyncio threadpool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, agent_func, *args, **kwargs)

    async def execute_multi_agent_pipeline(
        self,
        market_data: StockMarketData,
        user_profile: Optional[UserProfile] = None,
        simulate_degradation: Optional[str] = None  # e.g., "MOMENTUM_FAIL", "SENTIMENT_FAIL", "FUNDAMENTALS_FAIL"
    ) -> SynthesizedRecommendation:
        """
        Execute full multi-agent pipeline in parallel with synthesis and explainability.

        Args:
            market_data: Target stock market snapshot
            user_profile: User risk profile (defaults to MODERATE if None)
            simulate_degradation: Test hook to simulate data source failure for fault-tolerance demo

        Returns:
            SynthesizedRecommendation with full agent traces preserved
        """
        start_time = time.time()
        ticker = market_data.ticker
        company_name = market_data.company_name

        if user_profile is None:
            user_profile = UserProfile(
                user_id="default_user",
                name="Demo Investor",
                risk_tolerance=RiskTolerance.MODERATE
            )

        # 1. Parallel Agent Execution via asyncio.gather
        tasks = []

        # Momentum Agent Task
        if simulate_degradation == "MOMENTUM_FAIL":
            # Injected failure for degraded-mode demonstration
            tasks.append(self._create_degraded_output(
                AgentDimension.MOMENTUM_TECHNICAL,
                "momentum_tech_agent_01",
                ticker,
                "Simulated API timeout from live exchange market data feed."
            ))
        else:
            tasks.append(self._run_agent_async(self.momentum_agent.analyze, market_data))

        # Sentiment Agent Task
        if simulate_degradation == "SENTIMENT_FAIL":
            tasks.append(self._create_degraded_output(
                AgentDimension.SENTIMENT_RAG,
                "sentiment_rag_agent_01",
                ticker,
                "Vector database connection timeout during RAG retrieval."
            ))
        else:
            tasks.append(self._run_agent_async(self.sentiment_agent.analyze, market_data))

        # Fundamentals Agent Task
        if simulate_degradation == "FUNDAMENTALS_FAIL":
            tasks.append(self._create_degraded_output(
                AgentDimension.FUNDAMENTALS_RISK,
                "fundamentals_risk_agent_01",
                ticker,
                "SEBI regulatory filing repository unavailable."
            ))
        else:
            tasks.append(self._run_agent_async(self.fundamentals_agent.analyze, market_data))

        # Await all agents in parallel
        agent_results: List[AgentStructuredOutput] = await asyncio.gather(*tasks)

        # 2. Synthesis & Conflict Analysis
        recommendation = self._synthesize_traces(
            ticker=ticker,
            company_name=company_name,
            agent_traces=agent_results,
            user_profile=user_profile,
            simulated_30d_return=market_data.indicators.simulated_30d_forward_return
        )

        return recommendation

    async def _create_degraded_output(
        self,
        dimension: AgentDimension,
        agent_id: str,
        ticker: str,
        reason: str
    ) -> AgentStructuredOutput:
        """Helper to create realistic degraded output for testing resilience."""
        return AgentStructuredOutput(
            agent_id=agent_id,
            dimension=dimension,
            ticker=ticker,
            claim=f"Degraded Operation: Unable to collect valid signals for {ticker}.",
            signal=SignalType.HOLD,
            confidence=0.0,
            reasoning=f"Data feed failure: {reason}. Pipeline operating with flagged uncertainty.",
            key_metrics={"data_status": "DEGRADED"},
            sources=[],
            degraded_flag=True,
            degraded_reason=reason,
            execution_time_ms=5.0,
            timestamp=datetime.utcnow().isoformat()
        )

    def _synthesize_traces(
        self,
        ticker: str,
        company_name: str,
        agent_traces: List[AgentStructuredOutput],
        user_profile: UserProfile,
        simulated_30d_return: Optional[float] = None
    ) -> SynthesizedRecommendation:
        """
        Reconcile traces, apply user profile weights, detect conflicts, and construct explainable summary.
        """
        risk_tol = user_profile.risk_tolerance
        dim_weights = PROFILE_DIMENSION_WEIGHTS.get(risk_tol, PROFILE_DIMENSION_WEIGHTS[RiskTolerance.MODERATE])

        active_traces = [t for t in agent_traces if not t.degraded_flag]
        degraded_traces = [t for t in agent_traces if t.degraded_flag]

        degraded_mode = len(degraded_traces) > 0
        degraded_warning = None
        if degraded_mode:
            degraded_dims = ", ".join(t.dimension.value for t in degraded_traces)
            degraded_warning = f"DEGRADED DATA WARNING: {len(degraded_traces)} agent(s) ({degraded_dims}) operated under impaired data. Overall confidence has been penalized."

        # Compute weighted numerical signal
        total_weight = 0.0
        weighted_score = 0.0
        weighted_confidence = 0.0

        for trace in active_traces:
            base_w = dim_weights.get(trace.dimension, 0.33)
            # Modulate weight by agent's own confidence
            effective_w = base_w * (0.5 + 0.5 * trace.confidence)
            val = SIGNAL_NUMERICAL_WEIGHT.get(trace.signal, 0.0)

            weighted_score += val * effective_w
            weighted_confidence += trace.confidence * effective_w
            total_weight += effective_w

        if total_weight > 0:
            final_score = weighted_score / total_weight
            composite_conf = weighted_confidence / total_weight
        else:
            final_score = 0.0
            composite_conf = 0.1

        # Penalize confidence if degraded
        if degraded_mode:
            composite_conf = composite_conf * (len(active_traces) / len(agent_traces))

        # Check for Disagreements / Conflicts between agents
        signals_present = [t.signal for t in active_traces]
        has_bullish = any(s in [SignalType.BUY, SignalType.STRONG_BUY] for s in signals_present)
        has_bearish = any(s in [SignalType.SELL, SignalType.STRONG_SELL] for s in signals_present)

        conflict_detected = has_bullish and has_bearish
        conflict_details = None

        if conflict_detected:
            # Describe the exact nature of the disagreement
            bull_agents = [t.dimension.value for t in active_traces if t.signal in [SignalType.BUY, SignalType.STRONG_BUY]]
            bear_agents = [t.dimension.value for t in active_traces if t.signal in [SignalType.SELL, SignalType.STRONG_SELL]]
            conflict_details = f"AGENT DISAGREEMENT DETECTED: Bullish ({', '.join(bull_agents)}) vs Bearish ({', '.join(bear_agents)}). Confidence reduced by 25%."
            composite_conf *= 0.75  # Uncertainty penalty

        # Map final score to overall signal
        if final_score >= 1.2:
            overall_signal = SignalType.STRONG_BUY
        elif final_score >= 0.35:
            overall_signal = SignalType.BUY
        elif final_score <= -1.2:
            overall_signal = SignalType.STRONG_SELL
        elif final_score <= -0.35:
            overall_signal = SignalType.SELL
        else:
            overall_signal = SignalType.HOLD

        # Personalized suggested allocation based on user profile & confidence
        if overall_signal in [SignalType.STRONG_BUY, SignalType.BUY]:
            base_alloc = 0.15 if risk_tol == RiskTolerance.AGGRESSIVE else 0.08 if risk_tol == RiskTolerance.MODERATE else 0.04
            suggested_alloc_pct = round(base_alloc * composite_conf * 100, 1)
        elif overall_signal == SignalType.HOLD:
            suggested_alloc_pct = 0.0
        else:
            suggested_alloc_pct = 0.0  # Reduce/exit position

        # Construct Executive Summary
        exec_summary_parts = [
            f"Autonomous multi-agent consensus indicates a **{overall_signal.value}** recommendation for {company_name} ({ticker}) with {composite_conf*100:.1f}% confidence."
        ]

        if conflict_detected:
            exec_summary_parts.append(f"⚠️ {conflict_details}")
        if degraded_mode:
            exec_summary_parts.append(f"⚠️ {degraded_warning}")

        exec_summary = " ".join(exec_summary_parts)

        # Personalized Rationale per Risk Profile
        if risk_tol == RiskTolerance.CONSERVATIVE:
            pers_rationale = (
                f"Tailored for CONSERVATIVE profile: We heavily weighted fundamental balance sheet safety and SEBI governance ({dim_weights[AgentDimension.FUNDAMENTALS_RISK]*100:.0f}% weight). "
                f"High-volatility technical momentum was de-emphasized to prioritize capital preservation."
            )
        elif risk_tol == RiskTolerance.AGGRESSIVE:
            pers_rationale = (
                f"Tailored for AGGRESSIVE profile: Emphasized momentum, volume breakouts, and short-term catalyst signals ({dim_weights[AgentDimension.MOMENTUM_TECHNICAL]*100:.0f}% weight) "
                f"to capture alpha, accepting higher drawdown variance."
            )
        else:
            pers_rationale = (
                f"Tailored for MODERATE profile: Balanced blend of fundamental safety (35%), filing sentiment RAG (35%), and technical momentum (30%)."
            )

        # Accuracy evaluation against ground truth forward return
        accuracy_eval = None
        if simulated_30d_return is not None:
            is_bullish = overall_signal in [SignalType.STRONG_BUY, SignalType.BUY]
            is_bearish = overall_signal in [SignalType.STRONG_SELL, SignalType.SELL]
            ret_positive = simulated_30d_return > 0

            if (is_bullish and ret_positive) or (is_bearish and not ret_positive) or (overall_signal == SignalType.HOLD and abs(simulated_30d_return) < 0.03):
                accuracy_eval = f"CORRECT (30-day forward return: {simulated_30d_return*100:+.2f}%)"
            else:
                accuracy_eval = f"INCORRECT (30-day forward return: {simulated_30d_return*100:+.2f}%)"

        return SynthesizedRecommendation(
            ticker=ticker,
            company_name=company_name,
            overall_signal=overall_signal,
            composite_confidence=round(composite_conf, 4),
            executive_summary=exec_summary,
            personalized_rationale=pers_rationale,
            user_risk_profile_applied=risk_tol,
            suggested_allocation_pct=suggested_alloc_pct,
            conflict_detected=conflict_detected,
            conflict_details=conflict_details,
            degraded_mode=degraded_mode,
            degraded_warning=degraded_warning,
            agent_traces=agent_traces,
            simulated_30d_forward_return=simulated_30d_return,
            accuracy_eval=accuracy_eval,
            timestamp=datetime.utcnow().isoformat()
        )


# Global singleton
_orchestrator = None

def get_synthesis_orchestrator() -> SynthesisOrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SynthesisOrchestratorAgent()
    return _orchestrator
