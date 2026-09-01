"""
Agent 3: Fundamentals/Risk Agent (Stage 2)
Evaluates equity against fundamental metrics, balance sheet health, and SEBI-style regulatory risk disclosures.
"""

import time
from typing import Dict, Any, List
from datetime import datetime

from app.models.schemas import (
    AgentStructuredOutput,
    AgentDimension,
    SignalType,
    StockMarketData
)
from app.data.vector_store import get_vector_store


# Synthetic fundamental profile database for our 10 equities
FUNDAMENTAL_PROFILES: Dict[str, Dict[str, Any]] = {
    "RELIANCE": {
        "pe_ratio": 24.5,
        "pb_ratio": 2.1,
        "debt_to_equity": 0.42,
        "interest_coverage": 7.8,
        "roe_pct": 14.2,
        "roce_pct": 13.8,
        "operating_margin_pct": 18.5,
        "fcf_cr": 38000,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.4,
        "governance_risk": "LOW"
    },
    "TCS": {
        "pe_ratio": 28.2,
        "pb_ratio": 12.8,
        "debt_to_equity": 0.02,
        "interest_coverage": 48.0,
        "roe_pct": 42.5,
        "roce_pct": 54.0,
        "operating_margin_pct": 25.1,
        "fcf_cr": 42000,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.8,
        "governance_risk": "VERY_LOW"
    },
    "INFY": {
        "pe_ratio": 22.8,
        "pb_ratio": 7.5,
        "debt_to_equity": 0.04,
        "interest_coverage": 36.0,
        "roe_pct": 29.8,
        "roce_pct": 38.2,
        "operating_margin_pct": 21.2,
        "fcf_cr": 21000,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.6,
        "governance_risk": "VERY_LOW"
    },
    "HDFCBANK": {
        "pe_ratio": 18.4,
        "pb_ratio": 2.6,
        "debt_to_equity": 6.8,  # Bank leverage
        "interest_coverage": 3.2,
        "roe_pct": 18.4,
        "roce_pct": 16.2,
        "operating_margin_pct": 34.0,
        "fcf_cr": 45000,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.5,
        "governance_risk": "LOW",
        "gnpa_pct": 1.08,
        "car_pct": 18.9
    },
    "ICICIBANK": {
        "pe_ratio": 16.8,
        "pb_ratio": 2.8,
        "debt_to_equity": 6.4,
        "interest_coverage": 3.5,
        "roe_pct": 17.6,
        "roce_pct": 15.4,
        "operating_margin_pct": 32.5,
        "fcf_cr": 38000,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.2,
        "governance_risk": "LOW",
        "gnpa_pct": 2.15,
        "car_pct": 17.5
    },
    "TATAMOTORS": {
        "pe_ratio": 14.2,
        "pb_ratio": 3.8,
        "debt_to_equity": 1.15,
        "interest_coverage": 4.8,
        "roe_pct": 22.4,
        "roce_pct": 18.2,
        "operating_margin_pct": 12.8,
        "fcf_cr": 18500,
        "promoter_pledge_pct": 1.8,
        "sebi_compliance_score": 8.9,
        "governance_risk": "MODERATE"
    },
    "BHARTIARTL": {
        "pe_ratio": 32.0,
        "pb_ratio": 6.2,
        "debt_to_equity": 1.65,
        "interest_coverage": 3.9,
        "roe_pct": 19.5,
        "roce_pct": 16.8,
        "operating_margin_pct": 52.0,
        "fcf_cr": 24000,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.1,
        "governance_risk": "LOW"
    },
    "ITC": {
        "pe_ratio": 26.5,
        "pb_ratio": 7.8,
        "debt_to_equity": 0.01,
        "interest_coverage": 120.0,
        "roe_pct": 28.5,
        "roce_pct": 36.2,
        "operating_margin_pct": 37.8,
        "fcf_cr": 16500,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.7,
        "governance_risk": "VERY_LOW"
    },
    "WIPRO": {
        "pe_ratio": 21.0,
        "pb_ratio": 3.2,
        "debt_to_equity": 0.15,
        "interest_coverage": 22.0,
        "roe_pct": 15.2,
        "roce_pct": 19.5,
        "operating_margin_pct": 15.8,
        "fcf_cr": 9500,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.3,
        "governance_risk": "LOW"
    },
    "SBIN": {
        "pe_ratio": 10.5,
        "pb_ratio": 1.4,
        "debt_to_equity": 8.2,
        "interest_coverage": 2.8,
        "roe_pct": 16.8,
        "roce_pct": 14.2,
        "operating_margin_pct": 28.0,
        "fcf_cr": 28000,
        "promoter_pledge_pct": 0.0,
        "sebi_compliance_score": 9.0,
        "governance_risk": "MODERATE",
        "gnpa_pct": 2.42,
        "car_pct": 14.8
    }
}


class FundamentalsRiskAgent:
    """
    Evaluates fundamental financial health, valuation ratios, debt sustainability,
    and regulatory compliance against SEBI disclosure benchmarks.
    """

    def __init__(self, agent_id: str = "fundamentals_risk_agent_01"):
        self.agent_id = agent_id
        self.dimension = AgentDimension.FUNDAMENTALS_RISK
        self.vector_store = get_vector_store()

    def analyze(self, market_data: StockMarketData) -> AgentStructuredOutput:
        """
        Generate fundamentals & risk evaluation.

        Args:
            market_data: Stock market data snapshot

        Returns:
            AgentStructuredOutput with fundamental signal, risk metrics, and regulatory audit trace
        """
        start_time = time.time()

        try:
            ticker = market_data.ticker
            profile = FUNDAMENTAL_PROFILES.get(ticker)

            if not profile:
                # Degraded fallback if ticker profile is missing
                execution_time_ms = (time.time() - start_time) * 1000
                return AgentStructuredOutput(
                    agent_id=self.agent_id,
                    dimension=self.dimension,
                    ticker=ticker,
                    claim=f"No fundamental profile found for {ticker}.",
                    signal=SignalType.HOLD,
                    confidence=0.1,
                    reasoning="Missing balance sheet and SEBI filing fundamentals data.",
                    key_metrics={},
                    sources=[],
                    degraded_flag=True,
                    degraded_reason="Ticker not present in fundamentals database",
                    execution_time_ms=round(execution_time_ms, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

            # Query SEBI filing disclosures via RAG for regulatory audit
            sebi_chunks = self.vector_store.retrieve_top_k(
                query=f"{ticker} SEBI LODR related party compliance audit governance risk",
                ticker=ticker,
                top_k=2
            )

            score = 0.0
            reasoning_parts = []
            sources = []

            # 1. Profitability & Returns (ROE/ROCE)
            roe = profile.get("roe_pct", 10.0)
            if roe > 25.0:
                score += 2.5
                reasoning_parts.append(f"Outstanding capital efficiency with RoE at {roe:.1f}%.")
            elif roe > 15.0:
                score += 1.5
                reasoning_parts.append(f"Solid RoE of {roe:.1f}% indicates healthy shareholder returns.")
            elif roe < 8.0:
                score -= 2.0
                reasoning_parts.append(f"Subdued RoE of {roe:.1f}% lags cost of equity.")

            sources.append(f"RoE: {roe:.1f}%, RoCE: {profile.get('roce_pct', 0):.1f}%")

            # 2. Leverage & Solvency
            is_bank = "BANK" in ticker or ticker == "SBIN"
            de = profile.get("debt_to_equity", 0.0)
            ic = profile.get("interest_coverage", 1.0)

            if not is_bank:
                if de < 0.3:
                    score += 2.0
                    reasoning_parts.append(f"Virtually debt-free balance sheet (D/E: {de:.2f}).")
                elif de > 1.5:
                    score -= 2.0
                    reasoning_parts.append(f"Elevated financial leverage with D/E at {de:.2f}.")
                else:
                    score += 0.5
                    reasoning_parts.append(f"Manageable leverage (D/E: {de:.2f}).")

                if ic > 15.0:
                    score += 1.0
                    reasoning_parts.append(f"Extremely safe interest coverage ratio of {ic:.1f}x.")
                elif ic < 3.0:
                    score -= 1.5
                    reasoning_parts.append(f"Tight interest coverage of {ic:.1f}x.")
                sources.append(f"Debt/Equity: {de:.2f}, Interest Coverage: {ic:.1f}x")
            else:
                # Bank specific metrics (NPA and CAR)
                gnpa = profile.get("gnpa_pct", 2.0)
                car = profile.get("car_pct", 15.0)
                if gnpa < 1.5 and car > 16.0:
                    score += 2.5
                    reasoning_parts.append(f"Robust asset quality (GNPA: {gnpa:.2f}%) and fortress capital adequacy (CAR: {car:.1f}%).")
                elif gnpa > 3.0:
                    score -= 2.0
                    reasoning_parts.append(f"High non-performing assets ratio (GNPA: {gnpa:.2f}%).")
                sources.append(f"GNPA: {gnpa:.2f}%, CAR: {car:.1f}%")

            # 3. Valuation (P/E relative to growth)
            pe = profile.get("pe_ratio", 20.0)
            if pe < 15.0:
                score += 1.5
                reasoning_parts.append(f"Attractive valuation at P/E of {pe:.1f}x.")
            elif pe > 35.0:
                score -= 1.5
                reasoning_parts.append(f"Priced at a premium with P/E of {pe:.1f}x, leaving little margin of safety.")
            sources.append(f"P/E: {pe:.1f}x, P/B: {profile.get('pb_ratio', 0):.1f}x")

            # 4. Governance & SEBI Compliance
            compliance_score = profile.get("sebi_compliance_score", 9.0)
            pledge = profile.get("promoter_pledge_pct", 0.0)
            gov_risk = profile.get("governance_risk", "LOW")

            if pledge > 10.0:
                score -= 2.5
                reasoning_parts.append(f"Caution: promoter encumbrance/pledge is high at {pledge:.1f}%.")
            elif pledge == 0.0:
                score += 0.5
                reasoning_parts.append("Zero promoter pledge.")

            if compliance_score >= 9.5:
                score += 1.0
                reasoning_parts.append(f"Flawless SEBI LODR regulatory compliance track record ({compliance_score}/10).")

            sources.append(f"SEBI Compliance Score: {compliance_score}/10, Promoter Pledge: {pledge}%")

            # Add RAG citations from SEBI filings if found
            for c in sebi_chunks:
                sources.append(f"Filing Citation: {c.title} ({c.date}) - {c.content[:80]}...")

            # Map score to signal
            if score >= 4.5:
                signal = SignalType.STRONG_BUY
                confidence = min(0.95, 0.75 + (score - 4.5) * 0.04)
            elif score >= 1.5:
                signal = SignalType.BUY
                confidence = 0.65 + (score - 1.5) * 0.04
            elif score <= -4.5:
                signal = SignalType.STRONG_SELL
                confidence = min(0.95, 0.75 + abs(score + 4.5) * 0.04)
            elif score <= -1.5:
                signal = SignalType.SELL
                confidence = 0.65 + abs(score + 1.5) * 0.04
            else:
                signal = SignalType.HOLD
                confidence = 0.55 + abs(score) * 0.02

            claim = f"{ticker} exhibits {gov_risk.lower()} governance risk with fundamental score {score:.1f}/10. Balance sheet strength and profitability metrics {'warrant investment grade' if score > 0 else 'reflect fundamental headwinds'}."
            reasoning = " ".join(reasoning_parts)

            key_metrics = {
                "fundamental_score": round(score, 2),
                "pe_ratio": pe,
                "roe_pct": roe,
                "debt_to_equity": de,
                "sebi_compliance_score": compliance_score,
                "governance_risk": gov_risk
            }

            execution_time_ms = (time.time() - start_time) * 1000

            return AgentStructuredOutput(
                agent_id=self.agent_id,
                dimension=self.dimension,
                ticker=ticker,
                claim=claim,
                signal=signal,
                confidence=round(confidence, 4),
                reasoning=reasoning,
                key_metrics=key_metrics,
                sources=sources,
                degraded_flag=False,
                execution_time_ms=round(execution_time_ms, 2),
                timestamp=datetime.utcnow().isoformat()
            )

        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return AgentStructuredOutput(
                agent_id=self.agent_id,
                dimension=self.dimension,
                ticker=market_data.ticker,
                claim=f"Fundamentals analysis failed for {market_data.ticker}.",
                signal=SignalType.HOLD,
                confidence=0.0,
                reasoning=f"Fundamental evaluation error: {str(e)}",
                key_metrics={},
                sources=[],
                degraded_flag=True,
                degraded_reason=f"Exception: {type(e).__name__}",
                execution_time_ms=round(execution_time_ms, 2),
                timestamp=datetime.utcnow().isoformat()
            )
