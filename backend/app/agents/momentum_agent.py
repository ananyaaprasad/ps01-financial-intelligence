"""
Agent 1: Momentum/Technical Agent (Stage 2)
Analyzes price/volume anomalies and technical indicators to generate directional signals.
"""

import time
from typing import Dict, Any
from datetime import datetime

from app.models.schemas import (
    AgentStructuredOutput,
    AgentDimension,
    SignalType,
    StockMarketData,
    TechnicalIndicators
)


class MomentumTechnicalAgent:
    """
    Detects price/volume anomalies using technical indicators.
    Outputs structured signal with confidence, reasoning, and source citations.
    """

    def __init__(self, agent_id: str = "momentum_tech_agent_01"):
        self.agent_id = agent_id
        self.dimension = AgentDimension.MOMENTUM_TECHNICAL

    def analyze(self, market_data: StockMarketData) -> AgentStructuredOutput:
        """
        Generate momentum/technical signal from market data.

        Args:
            market_data: Current market snapshot with indicators

        Returns:
            AgentStructuredOutput with signal, confidence, reasoning, sources
        """
        start_time = time.time()

        try:
            ind = market_data.indicators
            ticker = market_data.ticker

            # Extract key metrics
            rsi = ind.rsi_14
            macd_histogram = ind.macd_histogram
            price = ind.current_price
            sma_20 = ind.sma_20
            sma_50 = ind.sma_50
            sma_200 = ind.sma_200
            volume_surge = ind.volume_surge_ratio
            bb_upper = ind.bollinger_upper
            bb_lower = ind.bollinger_lower
            change_pct = ind.change_pct

            # Initialize scoring components
            score = 0.0
            reasoning_parts = []
            key_metrics = {}
            sources = []

            # RSI Analysis (oversold/overbought)
            if rsi < 30:
                score += 2.0
                reasoning_parts.append(f"RSI at {rsi:.1f} indicates oversold conditions, potential reversal upward.")
                key_metrics["rsi_signal"] = "OVERSOLD"
            elif rsi > 70:
                score -= 2.0
                reasoning_parts.append(f"RSI at {rsi:.1f} signals overbought territory, risk of pullback.")
                key_metrics["rsi_signal"] = "OVERBOUGHT"
            else:
                reasoning_parts.append(f"RSI at {rsi:.1f} is neutral.")
                key_metrics["rsi_signal"] = "NEUTRAL"

            sources.append(f"RSI(14): {rsi:.2f}")

            # MACD Momentum
            if macd_histogram > 0:
                score += 1.5
                reasoning_parts.append(f"MACD histogram positive ({macd_histogram:.2f}), bullish momentum building.")
                key_metrics["macd_signal"] = "BULLISH"
            else:
                score -= 1.5
                reasoning_parts.append(f"MACD histogram negative ({macd_histogram:.2f}), bearish pressure evident.")
                key_metrics["macd_signal"] = "BEARISH"

            sources.append(f"MACD Histogram: {macd_histogram:.3f}")

            # Moving Average Trend (Golden/Death Cross proximity)
            if price > sma_20 > sma_50 > sma_200:
                score += 2.5
                reasoning_parts.append(f"Price trading above all major SMAs (20/50/200), strong uptrend intact.")
                key_metrics["ma_trend"] = "STRONG_UPTREND"
            elif price < sma_20 < sma_50 < sma_200:
                score -= 2.5
                reasoning_parts.append(f"Price below all SMAs, confirmed downtrend.")
                key_metrics["ma_trend"] = "DOWNTREND"
            elif price > sma_50:
                score += 1.0
                reasoning_parts.append(f"Price above 50-day SMA, intermediate bullish bias.")
                key_metrics["ma_trend"] = "INTERMEDIATE_BULLISH"
            else:
                score -= 1.0
                key_metrics["ma_trend"] = "WEAK"

            sources.append(f"SMA(20/50/200): {sma_20:.2f}/{sma_50:.2f}/{sma_200:.2f}")

            # Volume Surge Detection
            if volume_surge > 2.0:
                score += 1.5
                reasoning_parts.append(f"Volume surge at {volume_surge:.1f}x 20-day average, institutional accumulation likely.")
                key_metrics["volume_anomaly"] = True
            elif volume_surge < 0.5:
                score -= 0.5
                reasoning_parts.append(f"Below-average volume ({volume_surge:.1f}x), lack of conviction.")
                key_metrics["volume_anomaly"] = False

            sources.append(f"Volume Surge Ratio: {volume_surge:.2f}x")

            # Bollinger Band Squeeze/Breakout
            bb_range = (bb_upper - bb_lower) / ind.bollinger_middle
            if price > bb_upper:
                score += 1.0
                reasoning_parts.append(f"Price breached upper Bollinger Band, momentum breakout.")
                key_metrics["bb_position"] = "ABOVE_UPPER"
            elif price < bb_lower:
                score -= 1.0
                reasoning_parts.append(f"Price below lower Bollinger Band, oversold bounce candidate.")
                key_metrics["bb_position"] = "BELOW_LOWER"
            else:
                key_metrics["bb_position"] = "WITHIN_BANDS"

            sources.append(f"Bollinger Bands: {bb_lower:.2f} - {bb_upper:.2f}, Current: {price:.2f}")

            # Intraday momentum
            if abs(change_pct) > 3.0:
                if change_pct > 0:
                    score += 1.0
                    reasoning_parts.append(f"Strong intraday gain of {change_pct:.2f}%, buying pressure accelerating.")
                else:
                    score -= 1.0
                    reasoning_parts.append(f"Sharp intraday decline of {change_pct:.2f}%, selling pressure mounting.")

            sources.append(f"Intraday Change: {change_pct:.2f}%")

            # Map score to signal
            if score >= 5.0:
                signal = SignalType.STRONG_BUY
                confidence = min(0.95, 0.70 + (score - 5.0) * 0.05)
            elif score >= 2.0:
                signal = SignalType.BUY
                confidence = 0.60 + (score - 2.0) * 0.05
            elif score <= -5.0:
                signal = SignalType.STRONG_SELL
                confidence = min(0.95, 0.70 + abs(score + 5.0) * 0.05)
            elif score <= -2.0:
                signal = SignalType.SELL
                confidence = 0.60 + abs(score + 2.0) * 0.05
            else:
                signal = SignalType.HOLD
                confidence = 0.50 + abs(score) * 0.02

            # Build claim
            signal_verb = "bullish" if score > 0 else "bearish" if score < 0 else "neutral"
            claim = f"{ticker} exhibits {signal_verb} momentum with score {score:.1f}/10. Technical indicators {'support accumulation' if score > 0 else 'suggest distribution' if score < 0 else 'show consolidation'}."

            reasoning = " ".join(reasoning_parts)

            key_metrics.update({
                "composite_score": round(score, 2),
                "rsi_14": round(rsi, 2),
                "macd_histogram": round(macd_histogram, 3),
                "volume_surge_ratio": round(volume_surge, 2),
                "current_price": round(price, 2)
            })

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
            # Graceful degradation: return degraded output
            execution_time_ms = (time.time() - start_time) * 1000
            return AgentStructuredOutput(
                agent_id=self.agent_id,
                dimension=self.dimension,
                ticker=market_data.ticker,
                claim=f"Unable to analyze {market_data.ticker} due to data processing error.",
                signal=SignalType.HOLD,
                confidence=0.0,
                reasoning=f"Technical analysis failed: {str(e)}",
                key_metrics={},
                sources=[],
                degraded_flag=True,
                degraded_reason=f"Exception during analysis: {type(e).__name__}",
                execution_time_ms=round(execution_time_ms, 2),
                timestamp=datetime.utcnow().isoformat()
            )
