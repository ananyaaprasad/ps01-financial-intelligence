"""
Stage 1 Verification Test:
Validates market data simulation, document corpus, and vector retrieval top-k with metadata.
"""

import unittest
from app.data.market_simulator import get_market_simulator
from app.data.document_corpus import get_document_corpus
from app.data.vector_store import get_vector_store
from app.models.schemas import StockMarketData, DocumentChunk


class TestStage1(unittest.TestCase):

    def test_market_simulator_repeatability(self):
        sim = get_market_simulator()
        stocks = sim.get_all_market_data()
        self.assertEqual(len(stocks), 10, "Should simulate 10 listed equities")

        rel = sim.get_current_market_data("RELIANCE")
        self.assertIsInstance(rel, StockMarketData)
        self.assertGreater(rel.indicators.current_price, 0)
        self.assertGreater(rel.indicators.rsi_14, 0)
        self.assertLess(rel.indicators.rsi_14, 100)
        self.assertEqual(rel.source_type, "SIMULATED")

    def test_document_corpus(self):
        corpus = get_document_corpus()
        docs = corpus.get_all_documents()
        self.assertGreaterEqual(len(docs), 8, "Should generate at least 8 document chunks")
        summary = corpus.get_document_summary()
        self.assertIn("RELIANCE", summary["tickers"])
        self.assertIn("TCS", summary["tickers"])

    def test_vector_store_retrieval(self):
        store = get_vector_store()
        # Query for EBITDA and 5G in Reliance
        results = store.retrieve_top_k("EBITDA retail 5G subscriber growth", ticker="RELIANCE", top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].ticker, "RELIANCE")
        self.assertIsNotNone(results[0].similarity_score)
        self.assertIn("chunk_", results[0].chunk_id)
        self.assertTrue(len(results[0].content) > 20)


if __name__ == "__main__":
    unittest.main()
