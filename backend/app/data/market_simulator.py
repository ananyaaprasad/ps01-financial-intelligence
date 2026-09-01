"""
Market Data Simulator (Stage 1) - Generates synthetic real-time price/volume/technical indicators.
Uses deterministic random-walk generator seeded for repeatability (demo requirement).
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from app.models.schemas import StockMarketData, TechnicalIndicators


# 10 representative Indian equities across sectors
SIMULATED_STOCKS = [
    {"ticker": "RELIANCE", "company_name": "Reliance Industries Ltd", "sector": "Energy", "base_price": 2450.0},
    {"ticker": "TCS", "company_name": "Tata Consultancy Services", "sector": "IT", "base_price": 3800.0},
    {"ticker": "INFY", "company_name": "Infosys Ltd", "sector": "IT", "base_price": 1520.0},
    {"ticker": "HDFCBANK", "company_name": "HDFC Bank Ltd", "sector": "Banking", "base_price": 1680.0},
    {"ticker": "ICICIBANK", "company_name": "ICICI Bank Ltd", "sector": "Banking", "base_price": 980.0},
    {"ticker": "TATAMOTORS", "company_name": "Tata Motors Ltd", "sector": "Automotive", "base_price": 620.0},
    {"ticker": "BHARTIARTL", "company_name": "Bharti Airtel Ltd", "sector": "Telecom", "base_price": 1150.0},
    {"ticker": "ITC", "company_name": "ITC Ltd", "sector": "FMCG", "base_price": 440.0},
    {"ticker": "WIPRO", "company_name": "Wipro Ltd", "sector": "IT", "base_price": 550.0},
    {"ticker": "SBIN", "company_name": "State Bank of India", "sector": "Banking", "base_price": 750.0},
]


class MarketDataSimulator:
    """Deterministic market data generator for hackathon demo."""

    def __init__(self, seed: int = 42):
        """
        Initialize with a fixed seed for repeatability.

        Args:
            seed: Random seed for deterministic price generation
        """
        self.seed = seed
        self.rng = np.random.RandomState(seed)
        self.stocks = SIMULATED_STOCKS
        self.historical_data: Dict[str, pd.DataFrame] = {}
        self._generate_historical_data()

    def _generate_historical_data(self, lookback_days: int = 252):
        """Generate 1 year of historical OHLCV data for all stocks."""
        for stock in self.stocks:
            ticker = stock["ticker"]
            base_price = stock["base_price"]

            # Random walk with drift and volatility
            dates = pd.date_range(end=datetime.utcnow(), periods=lookback_days, freq='D')

            # Drift (annual return): -10% to +25%
            annual_drift = self.rng.uniform(-0.10, 0.25)
            daily_drift = annual_drift / 252

            # Volatility: 15% to 45% annualized
            annual_vol = self.rng.uniform(0.15, 0.45)
            daily_vol = annual_vol / np.sqrt(252)

            # Generate price path
            returns = self.rng.normal(daily_drift, daily_vol, lookback_days)
            price_multipliers = np.exp(np.cumsum(returns))
            close_prices = base_price * price_multipliers

            # Generate OHLC from close
            high_prices = close_prices * (1 + np.abs(self.rng.normal(0, 0.01, lookback_days)))
            low_prices = close_prices * (1 - np.abs(self.rng.normal(0, 0.01, lookback_days)))
            open_prices = self.rng.uniform(low_prices, high_prices)

            # Volume: 500K to 10M shares with occasional surges
            base_volume = self.rng.uniform(500_000, 10_000_000)
            volume = self.rng.lognormal(np.log(base_volume), 0.5, lookback_days).astype(int)

            df = pd.DataFrame({
                'date': dates,
                'open': open_prices,
                'high': high_prices,
                'low': low_prices,
                'close': close_prices,
                'volume': volume
            })

            self.historical_data[ticker] = df

    def _calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators from price history."""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values

        # Simple Moving Averages
        sma_20 = np.mean(close[-20:]) if len(close) >= 20 else close[-1]
        sma_50 = np.mean(close[-50:]) if len(close) >= 50 else close[-1]
        sma_200 = np.mean(close[-200:]) if len(close) >= 200 else close[-1]

        # RSI (14-period)
        rsi_14 = self._calculate_rsi(close, period=14)

        # MACD
        ema_12 = self._calculate_ema(close, 12)
        ema_26 = self._calculate_ema(close, 26)
        macd = ema_12 - ema_26
        macd_signal = self._calculate_ema(np.array([macd] * 9), 9)  # Simplified
        macd_histogram = macd - macd_signal

        # Bollinger Bands (20, 2)
        bb_middle = sma_20
        bb_std = np.std(close[-20:]) if len(close) >= 20 else 0
        bb_upper = bb_middle + 2 * bb_std
        bb_lower = bb_middle - 2 * bb_std

        # ATR (14-period)
        atr_14 = self._calculate_atr(high, low, close, period=14)

        # Volume surge ratio
        volume_20_avg = np.mean(volume[-20:]) if len(volume) >= 20 else volume[-1]
        volume_surge_ratio = volume[-1] / volume_20_avg if volume_20_avg > 0 else 1.0

        # 52-week high/low
        high_52w = np.max(high[-252:]) if len(high) >= 252 else np.max(high)
        low_52w = np.min(low[-252:]) if len(low) >= 252 else np.min(low)

        current_price = close[-1]
        open_price = df['open'].iloc[-1]
        change_pct = ((current_price - open_price) / open_price) * 100

        # Simulated 30-day forward return (for accuracy tracking)
        simulated_30d_return = self.rng.normal(0.02, 0.08)  # 2% mean, 8% std dev

        return {
            "current_price": float(current_price),
            "open_price": float(open_price),
            "high_52w": float(high_52w),
            "low_52w": float(low_52w),
            "change_pct": float(change_pct),
            "volume": int(volume[-1]),
            "volume_surge_ratio": float(volume_surge_ratio),
            "rsi_14": float(rsi_14),
            "macd": float(macd),
            "macd_signal": float(macd_signal),
            "macd_histogram": float(macd_histogram),
            "sma_20": float(sma_20),
            "sma_50": float(sma_50),
            "sma_200": float(sma_200),
            "bollinger_upper": float(bb_upper),
            "bollinger_middle": float(bb_middle),
            "bollinger_lower": float(bb_lower),
            "atr_14": float(atr_14),
            "simulated_30d_forward_return": float(simulated_30d_return)
        }

    def _calculate_rsi(self, prices: np.ndarray, period: int = 14) -> float:
        """Calculate Relative Strength Index."""
        if len(prices) < period + 1:
            return 50.0

        deltas = np.diff(prices[-period-1:])
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return prices[-1] if len(prices) > 0 else 0.0

        multiplier = 2 / (period + 1)
        ema = prices[0]
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        return ema

    def _calculate_atr(self, high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float:
        """Calculate Average True Range."""
        if len(high) < period + 1:
            return np.mean(high - low) if len(high) > 0 else 0.0

        high = high[-period-1:]
        low = low[-period-1:]
        close = close[-period-1:]

        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])

        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        atr = np.mean(tr)
        return atr

    def get_current_market_data(self, ticker: str) -> StockMarketData:
        """
        Get current simulated market data for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            StockMarketData with current indicators
        """
        if ticker not in self.historical_data:
            raise ValueError(f"Ticker {ticker} not found in simulated stocks")

        df = self.historical_data[ticker]
        stock_info = next(s for s in self.stocks if s["ticker"] == ticker)

        indicators = self._calculate_technical_indicators(df)

        # Get recent price history (last 30 days)
        recent_df = df.tail(30)
        price_history = [
            {
                "date": row['date'].isoformat(),
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            }
            for _, row in recent_df.iterrows()
        ]

        return StockMarketData(
            ticker=ticker,
            company_name=stock_info["company_name"],
            sector=stock_info["sector"],
            timestamp=datetime.utcnow().isoformat(),
            indicators=TechnicalIndicators(**indicators),
            price_history=price_history,
            source_type="SIMULATED"
        )

    def get_all_market_data(self) -> List[StockMarketData]:
        """Get current market data for all simulated stocks."""
        return [self.get_current_market_data(s["ticker"]) for s in self.stocks]

    def refresh_market_tick(self, ticker: str) -> StockMarketData:
        """
        Simulate a market tick (add one new bar to historical data).

        Args:
            ticker: Stock ticker to update

        Returns:
            Updated StockMarketData
        """
        if ticker not in self.historical_data:
            raise ValueError(f"Ticker {ticker} not found")

        df = self.historical_data[ticker]
        last_close = df['close'].iloc[-1]

        # Small random walk for next tick
        price_change = self.rng.normal(0.0001, 0.02)  # 0.01% mean, 2% std
        new_close = last_close * (1 + price_change)

        new_open = last_close * (1 + self.rng.normal(0, 0.005))
        new_high = max(new_open, new_close) * (1 + abs(self.rng.normal(0, 0.01)))
        new_low = min(new_open, new_close) * (1 - abs(self.rng.normal(0, 0.01)))

        base_vol = df['volume'].iloc[-20:].mean()
        new_volume = int(self.rng.lognormal(np.log(base_vol), 0.3))

        new_row = pd.DataFrame({
            'date': [df['date'].iloc[-1] + timedelta(days=1)],
            'open': [new_open],
            'high': [new_high],
            'low': [new_low],
            'close': [new_close],
            'volume': [new_volume]
        })

        self.historical_data[ticker] = pd.concat([df, new_row], ignore_index=True)

        return self.get_current_market_data(ticker)


# Global singleton instance (re-seeded for deterministic demo)
_market_simulator = None

def get_market_simulator() -> MarketDataSimulator:
    """Get or create the global market simulator instance."""
    global _market_simulator
    if _market_simulator is None:
        _market_simulator = MarketDataSimulator(seed=42)
    return _market_simulator
