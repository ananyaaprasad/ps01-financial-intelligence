"""
Stage 5 Verification Test:
Validates System Logging & Metrics:
1. Session metric logs stored in SQLite database
2. Directional accuracy proxy against 30-day forward return
3. Latency measurement per agent and total pipeline
4. Portfolio risk concentration (Herfindahl-Hirschman Index - HHI)
5. Aggregate metrics reporting
"""

import unittest
import asyncio
from datetime import datetime, timezone
import uuid

from app.data.database import get_db_manager
from app.data.market_simulator import get_market_simulator
from app.agents.synthesis_agent import get_synthesis_orchestrator
from app.models.schemas import SessionMetricLog, SignalType


class TestStage5(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = get_db_manager()
        self.sim = get_market_simulator()
        self.orchestrator = get_synthesis_orchestrator()

    async def test_session_metrics_logging(self):
        """Test generating a recommendation, computing session metrics and recording to SQLite."""
        market_data = self.sim.get_current_market_data("RELIANCE")
        user_profile = self.db.get_user_profile("user_moderate")
        self.assertIsNotNone(user_profile)

        rec = await self.orchestrator.execute_multi_agent_pipeline(market_data, user_profile=user_profile)

        # 1. Compute Herfindahl index
        weights = [item.weight_pct / 100.0 for item in user_profile.portfolio]
        herfindahl = sum(w**2 for w in weights)
        self.assertGreaterEqual(herfindahl, 0.0)

        # 2. Extract latencies
        agent_latencies = {
            trace.dimension.value: trace.execution_time_ms
            for trace in rec.agent_traces
        }
        self.assertEqual(len(agent_latencies), 3)

        # 3. Directional accuracy test
        is_bullish = rec.overall_signal in [SignalType.STRONG_BUY, SignalType.BUY]
        ret_positive = (rec.simulated_30d_forward_return or 0.0) > 0
        directionally_correct = is_bullish == ret_positive

        session_id = f"test_{uuid.uuid4().hex[:6]}"
        metric_log = SessionMetricLog(
            session_id=session_id,
            ticker="RELIANCE",
            recommended_signal=rec.overall_signal,
            composite_confidence=rec.composite_confidence,
            simulated_30d_return=rec.simulated_30d_forward_return or 0.0,
            directionally_correct=directionally_correct,
            total_pipeline_latency_ms=sum(agent_latencies.values()),
            agent_latencies_ms=agent_latencies,
            portfolio_risk_concentration=round(herfindahl, 4),
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # 4. Record to SQLite DB
        self.db.record_session_metric(metric_log)

        # 5. Fetch metrics summary
        summary = self.db.get_session_metrics_summary()
        self.assertGreaterEqual(summary["total_evaluations"], 1)
        self.assertIn("accuracy_proxy_pct", summary)
        self.assertIn("avg_pipeline_latency_ms", summary)
        self.assertGreaterEqual(len(summary["recent_logs"]), 1)


if __name__ == "__main__":
    unittest.main()
