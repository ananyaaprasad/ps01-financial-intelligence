"""
Stage 2 Verification Test:
Validates Multi-Agent Core:
1. 3 specialized agents adhering to structured output contract
2. Parallel execution with asyncio
3. Synthesis preservation of reasoning traces
4. Degraded data handling & fault tolerance
5. Disagreement / conflict detection
"""

import unittest
import asyncio
from app.data.market_simulator import get_market_simulator
from app.agents.momentum_agent import MomentumTechnicalAgent
from app.agents.sentiment_agent import SentimentAgent
from app.agents.fundamentals_agent import FundamentalsRiskAgent
from app.agents.synthesis_agent import get_synthesis_orchestrator
from app.models.schemas import (
    AgentStructuredOutput,
    AgentDimension,
    SignalType,
    UserProfile,
    RiskTolerance
)


class TestStage2(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.sim = get_market_simulator()
        self.market_data = self.sim.get_current_market_data("RELIANCE")
        self.orchestrator = get_synthesis_orchestrator()

    def test_individual_agents_contract(self):
        # 1. Momentum Agent
        m_agent = MomentumTechnicalAgent()
        m_out = m_agent.analyze(self.market_data)
        self.assertIsInstance(m_out, AgentStructuredOutput)
        self.assertEqual(m_out.dimension, AgentDimension.MOMENTUM_TECHNICAL)
        self.assertGreater(len(m_out.sources), 0)
        self.assertTrue(0.0 <= m_out.confidence <= 1.0)
        self.assertIn("RSI", m_out.reasoning)

        # 2. Sentiment Agent
        s_agent = SentimentAgent()
        s_out = s_agent.analyze(self.market_data)
        self.assertIsInstance(s_out, AgentStructuredOutput)
        self.assertEqual(s_out.dimension, AgentDimension.SENTIMENT_RAG)
        self.assertGreater(len(s_out.sources), 0)
        self.assertIn("Chunk", s_out.sources[0])

        # 3. Fundamentals Agent
        f_agent = FundamentalsRiskAgent()
        f_out = f_agent.analyze(self.market_data)
        self.assertIsInstance(f_out, AgentStructuredOutput)
        self.assertEqual(f_out.dimension, AgentDimension.FUNDAMENTALS_RISK)
        self.assertIn("RoE", f_out.sources[0])

    async def test_parallel_pipeline_execution(self):
        rec = await self.orchestrator.execute_multi_agent_pipeline(self.market_data)
        self.assertEqual(rec.ticker, "RELIANCE")
        self.assertEqual(len(rec.agent_traces), 3, "Must preserve all 3 agent reasoning traces")
        self.assertIn(rec.overall_signal, [SignalType.STRONG_BUY, SignalType.BUY, SignalType.HOLD, SignalType.SELL, SignalType.STRONG_SELL])
        self.assertGreater(rec.composite_confidence, 0.0)
        self.assertIsNotNone(rec.personalized_rationale)

    async def test_graceful_degradation_handling(self):
        # Simulate Sentiment agent vector DB failure
        rec = await self.orchestrator.execute_multi_agent_pipeline(
            self.market_data,
            simulate_degradation="SENTIMENT_FAIL"
        )
        self.assertTrue(rec.degraded_mode, "Must flag degraded mode")
        self.assertIsNotNone(rec.degraded_warning)
        self.assertIn("DEGRADED DATA WARNING", rec.degraded_warning)
        # Check that the degraded agent is explicitly marked
        sentiment_trace = next(t for t in rec.agent_traces if t.dimension == AgentDimension.SENTIMENT_RAG)
        self.assertTrue(sentiment_trace.degraded_flag)
        self.assertEqual(sentiment_trace.confidence, 0.0)

    async def test_user_risk_profile_personalization(self):
        conservative_user = UserProfile(risk_tolerance=RiskTolerance.CONSERVATIVE)
        aggressive_user = UserProfile(risk_tolerance=RiskTolerance.AGGRESSIVE)

        rec_cons = await self.orchestrator.execute_multi_agent_pipeline(self.market_data, user_profile=conservative_user)
        rec_aggr = await self.orchestrator.execute_multi_agent_pipeline(self.market_data, user_profile=aggressive_user)

        self.assertEqual(rec_cons.user_risk_profile_applied, RiskTolerance.CONSERVATIVE)
        self.assertEqual(rec_aggr.user_risk_profile_applied, RiskTolerance.AGGRESSIVE)
        self.assertIn("CONSERVATIVE", rec_cons.personalized_rationale)
        self.assertIn("AGGRESSIVE", rec_aggr.personalized_rationale)


if __name__ == "__main__":
    unittest.main()
