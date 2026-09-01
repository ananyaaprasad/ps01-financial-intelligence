"""
SQLite Database Layer (Stage 3 & Stage 5)
Persists User Profiles, Portfolio Holdings, Interaction History, and Session Logs.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.models.schemas import (
    UserProfile,
    UserPortfolioItem,
    RiskTolerance,
    SynthesizedRecommendation,
    SessionMetricLog
)

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "financial_intelligence.db")


def get_db_connection() -> sqlite3.Connection:
    """Create SQLite connection with row dictionary factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and seed default users for demo."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. User Profiles Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profiles (
        user_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        risk_tolerance TEXT NOT NULL,
        investment_horizon_months INTEGER DEFAULT 12,
        total_portfolio_value REAL DEFAULT 500000.0,
        cash_balance REAL DEFAULT 120000.0,
        watchlist_json TEXT DEFAULT '[]',
        updated_at TEXT
    )
    """)

    # 2. Portfolio Holdings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_holdings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        ticker TEXT NOT NULL,
        shares INTEGER NOT NULL,
        avg_buy_price REAL NOT NULL,
        FOREIGN KEY (user_id) REFERENCES user_profiles(user_id)
    )
    """)

    # 3. Recommendation History Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendation_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        ticker TEXT NOT NULL,
        overall_signal TEXT NOT NULL,
        composite_confidence REAL NOT NULL,
        risk_profile_applied TEXT NOT NULL,
        executive_summary TEXT,
        recommendation_json TEXT NOT NULL,
        created_at TEXT
    )
    """)

    # 4. Session & Metric Logs Table (Stage 5)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS session_metric_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT NOT NULL,
        ticker TEXT NOT NULL,
        recommended_signal TEXT NOT NULL,
        composite_confidence REAL NOT NULL,
        simulated_30d_return REAL,
        directionally_correct INTEGER NOT NULL,
        total_pipeline_latency_ms REAL NOT NULL,
        agent_latencies_json TEXT NOT NULL,
        portfolio_risk_concentration REAL NOT NULL,
        timestamp TEXT NOT NULL
    )
    """)

    conn.commit()

    # Seed demo users if empty
    cursor.execute("SELECT COUNT(*) FROM user_profiles")
    if cursor.fetchone()[0] == 0:
        seed_demo_data(conn)

    conn.close()


def seed_demo_data(conn: sqlite3.Connection):
    """Seed 3 distinct investor profiles for side-by-side demo comparison."""
    cursor = conn.cursor()
    now = datetime.now(timezone.utc).isoformat()

    users = [
        ("user_conservative", "Aarav Sharma (Retiree)", "conservative", 24, 1500000.0, 450000.0, json.dumps(["TCS", "ITC", "HDFCBANK", "INFY"])),
        ("user_moderate", "Priya Patel (Mid-Career)", "moderate", 12, 800000.0, 180000.0, json.dumps(["RELIANCE", "HDFCBANK", "TATAMOTORS", "INFY", "BHARTIARTL"])),
        ("user_aggressive", "Rohan Verma (Growth Trader)", "aggressive", 6, 400000.0, 90000.0, json.dumps(["TATAMOTORS", "RELIANCE", "BHARTIARTL", "SBIN", "ICICIBANK"])),
    ]

    cursor.executemany("""
    INSERT INTO user_profiles (user_id, name, risk_tolerance, investment_horizon_months, total_portfolio_value, cash_balance, watchlist_json, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, [(u[0], u[1], u[2], u[3], u[4], u[5], u[6], now) for u in users])

    # Seed portfolio holdings
    holdings = [
        # Conservative holdings (safe FMCG & IT dividend plays)
        ("user_conservative", "ITC", 1200, 410.0),
        ("user_conservative", "TCS", 150, 3650.0),
        ("user_conservative", "HDFCBANK", 200, 1580.0),

        # Moderate holdings (balanced)
        ("user_moderate", "RELIANCE", 120, 2380.0),
        ("user_moderate", "INFY", 180, 1480.0),
        ("user_moderate", "TATAMOTORS", 300, 580.0),

        # Aggressive holdings (high beta & auto)
        ("user_aggressive", "TATAMOTORS", 450, 560.0),
        ("user_aggressive", "SBIN", 250, 710.0),
        ("user_aggressive", "BHARTIARTL", 150, 1080.0),
    ]

    cursor.executemany("""
    INSERT INTO portfolio_holdings (user_id, ticker, shares, avg_buy_price)
    VALUES (?, ?, ?, ?)
    """, holdings)

    conn.commit()


class DatabaseManager:
    """Manager for CRUD operations on user profiles and session logs."""

    def __init__(self):
        init_db()

    def get_user_profile(self, user_id: str, market_prices: Optional[Dict[str, float]] = None) -> Optional[UserProfile]:
        """Fetch user profile with live portfolio valuation."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_profiles WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        # Fetch holdings
        cursor.execute("SELECT ticker, shares, avg_buy_price FROM portfolio_holdings WHERE user_id = ?", (user_id,))
        holding_rows = cursor.fetchall()
        conn.close()

        portfolio_items = []
        total_holdings_value = 0.0

        for h in holding_rows:
            ticker = h["ticker"]
            shares = h["shares"]
            avg_buy = h["avg_buy_price"]
            curr_price = market_prices.get(ticker, avg_buy * 1.05) if market_prices else avg_buy * 1.05
            unrealized_pnl = (curr_price - avg_buy) * shares
            unrealized_pnl_pct = ((curr_price - avg_buy) / avg_buy) * 100 if avg_buy > 0 else 0.0
            position_val = curr_price * shares
            total_holdings_value += position_val

            portfolio_items.append(UserPortfolioItem(
                ticker=ticker,
                shares=shares,
                avg_buy_price=avg_buy,
                current_price=curr_price,
                unrealized_pnl=round(unrealized_pnl, 2),
                unrealized_pnl_pct=round(unrealized_pnl_pct, 2),
                weight_pct=0.0  # calculate below
            ))

        # Calculate weights
        total_val = total_holdings_value + row["cash_balance"]
        for item in portfolio_items:
            item.weight_pct = round((item.current_price * item.shares / total_val) * 100, 2) if total_val > 0 else 0.0

        return UserProfile(
            user_id=row["user_id"],
            name=row["name"],
            risk_tolerance=RiskTolerance(row["risk_tolerance"]),
            investment_horizon_months=row["investment_horizon_months"],
            total_portfolio_value=round(total_val, 2),
            cash_balance=round(row["cash_balance"], 2),
            portfolio=portfolio_items,
            watchlist=json.loads(row["watchlist_json"]) if row["watchlist_json"] else []
        )

    def list_all_users(self) -> List[Dict[str, Any]]:
        """List all available user profiles for demo switching."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, risk_tolerance, cash_balance FROM user_profiles")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_user_risk_tolerance(self, user_id: str, new_risk: RiskTolerance):
        """Update user risk tolerance."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user_profiles SET risk_tolerance = ?, updated_at = ? WHERE user_id = ?",
            (new_risk.value, datetime.now(timezone.utc).isoformat(), user_id)
        )
        conn.commit()
        conn.close()

    def record_recommendation(self, user_id: str, rec: SynthesizedRecommendation):
        """Save a recommendation into interaction history."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO recommendation_history (
            user_id, ticker, overall_signal, composite_confidence,
            risk_profile_applied, executive_summary, recommendation_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            rec.ticker,
            rec.overall_signal.value,
            rec.composite_confidence,
            rec.user_risk_profile_applied.value,
            rec.executive_summary,
            rec.model_dump_json(),
            datetime.now(timezone.utc).isoformat()
        ))
        conn.commit()
        conn.close()

    def record_session_metric(self, metric: SessionMetricLog):
        """Log session metrics for Stage 5 tracking."""
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO session_metric_logs (
            session_id, ticker, recommended_signal, composite_confidence,
            simulated_30d_return, directionally_correct, total_pipeline_latency_ms,
            agent_latencies_json, portfolio_risk_concentration, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metric.session_id,
            metric.ticker,
            metric.recommended_signal.value,
            metric.composite_confidence,
            metric.simulated_30d_return,
            1 if metric.directionally_correct else 0,
            metric.total_pipeline_latency_ms,
            json.dumps(metric.agent_latencies_ms),
            metric.portfolio_risk_concentration,
            metric.timestamp
        ))
        conn.commit()
        conn.close()

    def get_session_metrics_summary(self) -> Dict[str, Any]:
        """Aggregate Stage 5 metrics: accuracy proxy, latencies, concentration."""
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*), AVG(directionally_correct), AVG(total_pipeline_latency_ms) FROM session_metric_logs")
        total_count, avg_acc, avg_lat = cursor.fetchone()

        cursor.execute("SELECT * FROM session_metric_logs ORDER BY id DESC LIMIT 20")
        recent_logs = [dict(r) for r in cursor.fetchall()]

        conn.close()

        return {
            "total_evaluations": total_count or 0,
            "accuracy_proxy_pct": round((avg_acc or 0.0) * 100, 2),
            "avg_pipeline_latency_ms": round(avg_lat or 0.0, 2),
            "recent_logs": recent_logs
        }


# Global singleton
_db_manager = None

def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
