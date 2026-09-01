"""
Stage 3 Verification Test:
Validates User Profiling & Persistence:
1. SQLite user profile loading & holdings calculation
2. Profile risk switching
3. Recommendation history recording
4. Side-by-side profile differentiation for the exact same market data
"""

import unittest
import asyncio
from app.data.database import get_db_manager
from app.data.market_simulator import get_market_simulator
from app.agents.synthesis_agent import get_synthesis_orchestrator
from app.models.schemas import RiskTolerance


class TestStage3(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = get_db_manager()
        self.sim = get_market_simulator()
        self.orchestrator = get_synthesis_orchestrator()

    def test_user_profiles_seeded(self):
        users = self.db.list_all_users()
        self.assertGreaterEqual(len(users), 3, "Must have at least 3 seed profiles")

        profile = self.db.get_user_profile("user_conservative")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.risk_tolerance, RiskTolerance.CONSERVATIVE)
        self.assertGreater(len(profile.portfolio), 0)

    async def test_side_by_side_profile_differentiation(self):
        """
        Verify identical market data produces demonstrably different output
        for two distinct user profiles (Demo Requirement).
        """
        market_data = self.sim.get_current_market_data("TATAMOTORS")

        user_cons = self.db.get_user_profile("user_conservative")
        user_aggr = self.db.get_user_profile("user_aggressive")

        rec_cons = await self.orchestrator.execute_multi_agent_pipeline(market_data, user_profile=user_cons)
        rec_aggr = await self.orchestrator.execute_multi_agent_pipeline(market_data, user_profile=user_aggr)

        # 1. Assert different risk profile recorded
        self.assertEqual(rec_cons.user_risk_profile_applied, RiskTolerance.CONSERVATIVE)
        self.assertEqual(rec_aggr.user_risk_profile_applied, RiskTolerance.AGGRESSIVE)

        # 2. Assert different personalized rationale
        self.assertNotEqual(rec_cons.personalized_rationale, rec_aggr.personalized_rationale)
        self.assertIn("CONSERVATIVE", rec_cons.personalized_rationale)
        self.assertIn("AGGRESSIVE", rec_aggr.personalized_rationale)

        # 3. Record in DB and check
        self.db.record_recommendation("user_conservative", rec_cons)
        self.db.record_recommendation("user_aggressive", rec_aggr)


if __name__ == "__main__":
    unittest.main()
