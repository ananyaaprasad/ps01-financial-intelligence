"""
Agent 2: Sentiment Agent (Stage 2)
Analyzes filing/news text via RAG retrieval, citing retrieved chunks as sources.
"""

import time
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.models.schemas import (
    AgentStructuredOutput,
    AgentDimension,
    SignalType,
    StockMarketData,
    DocumentChunk
)
from app.data.vector_store import get_vector_store


class SentimentAgent:
    """
    Performs sentiment analysis on regulatory filings and earnings transcripts using RAG retrieval.
    Cites retrieved document chunks as explicit sources.
    """

    def __init__(self, agent_id: str = "sentiment_rag_agent_01"):
        self.agent_id = agent_id
        self.dimension = AgentDimension.SENTIMENT_RAG
        self.vector_store = get_vector_store()

    def analyze(
        self,
        market_data: StockMarketData,
        query_context: Optional[str] = None
    ) -> AgentStructuredOutput:
        """
        Generate sentiment signal from retrieved document chunks.

        Args:
            market_data: Current market snapshot
            query_context: Optional query hint for retrieval

        Returns:
            AgentStructuredOutput with sentiment signal, confidence, reasoning, and RAG sources
        """
        start_time = time.time()

        try:
            ticker = market_data.ticker
            company_name = market_data.company_name

            # Construct retrieval query
            if query_context:
                query = f"{company_name} {ticker} {query_context} growth outlook risk management performance"
            else:
                query = f"{company_name} {ticker} revenue growth profitability margin outlook risk factors strategic initiatives"

            # Retrieve top-k relevant chunks
            retrieved_chunks: List[DocumentChunk] = self.vector_store.retrieve_top_k(
                query=query,
                ticker=ticker,
                top_k=4
            )

            if not retrieved_chunks:
                # Graceful degradation: no documents available
                execution_time_ms = (time.time() - start_time) * 1000
                return AgentStructuredOutput(
                    agent_id=self.agent_id,
                    dimension=self.dimension,
                    ticker=ticker,
                    claim=f"No sentiment data available for {ticker} due to missing regulatory filings.",
                    signal=SignalType.HOLD,
                    confidence=0.0,
                    reasoning="Unable to retrieve relevant earnings transcripts or SEBI filings from document corpus.",
                    key_metrics={},
                    sources=[],
                    degraded_flag=True,
                    degraded_reason="Zero documents retrieved from vector store",
                    execution_time_ms=round(execution_time_ms, 2),
                    timestamp=datetime.utcnow().isoformat()
                )

            # Analyze sentiment from retrieved chunks
            sentiment_score = 0.0
            reasoning_parts = []
            sources = []
            key_metrics = {}

            positive_keywords = [
                "growth", "strong", "expand", "increase", "improved", "momentum",
                "robust", "outperform", "beat", "exceeded", "optimistic", "positive",
                "upside", "accelerat", "win", "order", "partnership", "innovation",
                "margin expansion", "cash flow", "profitable", "recovery", "traction"
            ]

            negative_keywords = [
                "decline", "weak", "headwind", "pressure", "risk", "concern",
                "challenging", "cautious", "slowdown", "miss", "below", "disappointing",
                "competition", "volatility", "uncertainty", "deteriorat", "loss",
                "stress", "disruption", "exposure", "slippage", "attrition", "delay"
            ]

            neutral_keywords = [
                "stable", "maintain", "steady", "hold", "consistent", "flat", "unchanged"
            ]

            for idx, chunk in enumerate(retrieved_chunks):
                content_lower = chunk.content.lower()

                # Count keyword occurrences
                pos_count = sum(1 for kw in positive_keywords if kw in content_lower)
                neg_count = sum(1 for kw in negative_keywords if kw in content_lower)
                neu_count = sum(1 for kw in neutral_keywords if kw in content_lower)

                chunk_sentiment = pos_count - neg_count

                # Weight by similarity score
                weight = chunk.similarity_score if chunk.similarity_score else 0.5
                weighted_sentiment = chunk_sentiment * weight

                sentiment_score += weighted_sentiment

                # Extract key phrases for reasoning
                if chunk_sentiment > 2:
                    tone = "positive"
                elif chunk_sentiment < -2:
                    tone = "negative"
                else:
                    tone = "neutral"

                snippet = chunk.content[:150] + "..." if len(chunk.content) > 150 else chunk.content
                reasoning_parts.append(
                    f"[{chunk.doc_type}, {chunk.date}] {tone.capitalize()} tone detected: \"{snippet}\""
                )

                # Build source citation
                source_citation = f"{chunk.title} ({chunk.quarter}) - Chunk {chunk.chunk_id} [Similarity: {chunk.similarity_score:.2f}]"
                sources.append(source_citation)

            # Normalize sentiment score
            normalized_sentiment = sentiment_score / len(retrieved_chunks)

            # Map sentiment to signal
            if normalized_sentiment > 3.0:
                signal = SignalType.STRONG_BUY
                confidence = min(0.90, 0.70 + (normalized_sentiment - 3.0) * 0.05)
            elif normalized_sentiment > 1.0:
                signal = SignalType.BUY
                confidence = 0.60 + (normalized_sentiment - 1.0) * 0.05
            elif normalized_sentiment < -3.0:
                signal = SignalType.STRONG_SELL
                confidence = min(0.90, 0.70 + abs(normalized_sentiment + 3.0) * 0.05)
            elif normalized_sentiment < -1.0:
                signal = SignalType.SELL
                confidence = 0.60 + abs(normalized_sentiment + 1.0) * 0.05
            else:
                signal = SignalType.HOLD
                confidence = 0.50 + abs(normalized_sentiment) * 0.05

            # Build claim
            sentiment_label = "positive" if normalized_sentiment > 0 else "negative" if normalized_sentiment < 0 else "neutral"
            claim = f"{ticker} sentiment analysis from recent filings reveals {sentiment_label} outlook (score: {normalized_sentiment:.1f}). Management commentary and regulatory disclosures {'support bullish' if normalized_sentiment > 0 else 'raise bearish' if normalized_sentiment < 0 else 'suggest neutral'} thesis."

            reasoning = " ".join(reasoning_parts)

            key_metrics = {
                "sentiment_score": round(normalized_sentiment, 2),
                "documents_analyzed": len(retrieved_chunks),
                "avg_similarity": round(sum(c.similarity_score for c in retrieved_chunks) / len(retrieved_chunks), 3),
                "doc_types": list(set(c.doc_type for c in retrieved_chunks))
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
            # Graceful degradation
            execution_time_ms = (time.time() - start_time) * 1000
            return AgentStructuredOutput(
                agent_id=self.agent_id,
                dimension=self.dimension,
                ticker=market_data.ticker,
                claim=f"Sentiment analysis failed for {market_data.ticker}.",
                signal=SignalType.HOLD,
                confidence=0.0,
                reasoning=f"RAG retrieval or sentiment processing error: {str(e)}",
                key_metrics={},
                sources=[],
                degraded_flag=True,
                degraded_reason=f"Exception: {type(e).__name__}",
                execution_time_ms=round(execution_time_ms, 2),
                timestamp=datetime.utcnow().isoformat()
            )
