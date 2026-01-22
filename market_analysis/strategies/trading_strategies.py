"""
Trading Strategies Module

Implements various trading strategies:
- Multi-market algorithm (stocks, futures, indexes)
- HFT entry/exit strategies
- Long-term position trading
- Options trading
- Pattern recognition
- Risk-managed aggressive positions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MarketType(Enum):
    """Types of markets"""
    STOCK = "stock"
    FUTURE = "future"
    INDEX = "index"
    OPTION = "option"
    FOREX = "forex"
    CRYPTO = "crypto"


class TradeDirection(Enum):
    """Trade directions"""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class StrategyType(Enum):
    """Strategy types"""
    HFT = "high_frequency"
    DAY_TRADE = "day_trade"
    SWING = "swing"
    POSITION = "position"
    OPTIONS = "options"


@dataclass
class TradingSignal:
    """Represents a trading signal"""
    symbol: str
    direction: TradeDirection
    strategy_type: StrategyType
    entry_price: float
    target_price: float
    stop_loss: float
    position_size: float
    confidence: float  # 0-1
    expected_return: float
    risk_reward_ratio: float
    holding_period_days: int
    timestamp: datetime
    rationale: str
    risk_score: float  # 0-1 (higher = riskier)


@dataclass
class Position:
    """Represents an open position"""
    symbol: str
    direction: TradeDirection
    entry_price: float
    current_price: float
    quantity: float
    entry_time: datetime
    stop_loss: float
    take_profit: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


class MultiMarketAlgorithm:
    """
    Universal trading algorithm that works across stocks, futures, indexes, etc.
    """

    def __init__(self, market_type: MarketType = MarketType.STOCK):
        self.market_type = market_type
        self.positions = []

    def generate_signal(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        factors: Dict[str, float],
        market_regime: str = 'normal'
    ) -> Optional[TradingSignal]:
        """
        Generate trading signal based on multi-factor analysis.

        Args:
            symbol: Trading symbol
            price_data: Historical OHLCV data
            factors: Dictionary of factor scores
            market_regime: Current market regime

        Returns:
            TradingSignal or None
        """
        current_price = price_data['close'].iloc[-1]

        # Calculate technical indicators
        rsi = self._calculate_rsi(price_data['close'])
        ma_50 = price_data['close'].rolling(50).mean().iloc[-1]
        ma_200 = price_data['close'].rolling(200).mean().iloc[-1]

        # Combine factors for signal
        technical_score = 0.0

        # Trend following
        if current_price > ma_50 > ma_200:
            technical_score += 0.3  # Strong uptrend
        elif current_price < ma_50 < ma_200:
            technical_score -= 0.3  # Strong downtrend

        # RSI
        if rsi < 30:
            technical_score += 0.2  # Oversold
        elif rsi > 70:
            technical_score -= 0.2  # Overbought

        # Factor scores
        factor_score = factors.get('prediction', 0.0)

        # Combined signal
        combined_score = technical_score * 0.4 + factor_score * 0.6

        # Generate signal if strong enough
        if combined_score > 0.3:
            direction = TradeDirection.LONG
            target_price = current_price * 1.05  # 5% target
            stop_loss = current_price * 0.98  # 2% stop
        elif combined_score < -0.3:
            direction = TradeDirection.SHORT
            target_price = current_price * 0.95
            stop_loss = current_price * 1.02
        else:
            return None  # No signal

        # Calculate position sizing and risk
        volatility = price_data['close'].pct_change().std()
        risk_score = min(1.0, volatility * 50)

        return TradingSignal(
            symbol=symbol,
            direction=direction,
            strategy_type=StrategyType.SWING,
            entry_price=current_price,
            target_price=target_price,
            stop_loss=stop_loss,
            position_size=1000 / current_price,  # $1000 position
            confidence=abs(combined_score),
            expected_return=abs(target_price / current_price - 1),
            risk_reward_ratio=abs(target_price - current_price) / abs(current_price - stop_loss),
            holding_period_days=5,
            timestamp=datetime.now(),
            rationale=f"Technical: {technical_score:.2f}, Factors: {factor_score:.2f}",
            risk_score=risk_score
        )

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi.iloc[-1]

    def apply_to_market(
        self,
        market_type: MarketType,
        symbol: str,
        data: pd.DataFrame,
        factors: Dict[str, float]
    ) -> Optional[TradingSignal]:
        """
        Apply algorithm to different market types.

        Args:
            market_type: Type of market
            symbol: Symbol
            data: Price data
            factors: Factor scores

        Returns:
            TradingSignal or None
        """
        # Market-specific adjustments
        if market_type == MarketType.FUTURE:
            # Futures: Account for leverage and margin
            factors['leverage_adjusted'] = factors.get('prediction', 0) * 0.5

        elif market_type == MarketType.OPTION:
            # Options: Include Greeks in decision
            factors['option_adjusted'] = factors.get('prediction', 0)

        elif market_type == MarketType.INDEX:
            # Indexes: Broader market view
            factors['index_adjusted'] = factors.get('prediction', 0) * 0.8

        return self.generate_signal(symbol, data, factors)


class HFTStrategy:
    """
    High-Frequency Trading strategy for millisecond-level execution.
    """

    def __init__(self):
        self.min_profit_bps = 1  # Minimum 1 basis point profit
        self.max_holding_seconds = 60

    def detect_arbitrage(
        self,
        orderbook_1: Dict[str, List[Tuple[float, float]]],
        orderbook_2: Dict[str, List[Tuple[float, float]]]
    ) -> Optional[Dict[str, Any]]:
        """
        Detect arbitrage opportunities between two order books.

        Args:
            orderbook_1: {'bids': [(price, size)], 'asks': [...]}
            orderbook_2: Same format

        Returns:
            Arbitrage opportunity details or None
        """
        # Best bid/ask from each book
        best_bid_1 = orderbook_1['bids'][0][0] if orderbook_1['bids'] else 0
        best_ask_1 = orderbook_1['asks'][0][0] if orderbook_1['asks'] else float('inf')

        best_bid_2 = orderbook_2['bids'][0][0] if orderbook_2['bids'] else 0
        best_ask_2 = orderbook_2['asks'][0][0] if orderbook_2['asks'] else float('inf')

        # Check for cross-market arbitrage
        if best_bid_1 > best_ask_2:
            profit_bps = (best_bid_1 - best_ask_2) / best_ask_2 * 10000

            if profit_bps >= self.min_profit_bps:
                return {
                    'type': 'arbitrage',
                    'buy_market': 2,
                    'sell_market': 1,
                    'buy_price': best_ask_2,
                    'sell_price': best_bid_1,
                    'profit_bps': profit_bps,
                    'execution_time_ms': 5  # Estimated
                }

        if best_bid_2 > best_ask_1:
            profit_bps = (best_bid_2 - best_ask_1) / best_ask_1 * 10000

            if profit_bps >= self.min_profit_bps:
                return {
                    'type': 'arbitrage',
                    'buy_market': 1,
                    'sell_market': 2,
                    'buy_price': best_ask_1,
                    'sell_price': best_bid_2,
                    'profit_bps': profit_bps,
                    'execution_time_ms': 5
                }

        return None

    def market_making_signal(
        self,
        current_price: float,
        volatility: float,
        order_flow_imbalance: float
    ) -> Dict[str, float]:
        """
        Generate market-making bid/ask quotes.

        Args:
            current_price: Current mid price
            volatility: Price volatility
            order_flow_imbalance: Buy/sell pressure (-1 to 1)

        Returns:
            Dictionary with bid/ask prices and sizes
        """
        # Spread based on volatility
        base_spread = volatility * 2
        spread = max(0.0001, base_spread)  # Minimum 1 bps

        # Skew quotes based on order flow
        skew = order_flow_imbalance * spread * 0.5

        bid_price = current_price - spread / 2 - skew
        ask_price = current_price + spread / 2 - skew

        return {
            'bid_price': bid_price,
            'ask_price': ask_price,
            'bid_size': 100,
            'ask_size': 100,
            'spread_bps': spread / current_price * 10000,
            'skew': skew
        }


class OptionsStrategy:
    """
    Options trading strategies.
    """

    def vertical_spread_signal(
        self,
        underlying_price: float,
        prediction: float,
        volatility: float
    ) -> Dict[str, Any]:
        """
        Generate vertical spread (bull/bear spread) signal.

        Args:
            underlying_price: Current stock price
            prediction: Price prediction (+/- %)
            volatility: Implied volatility

        Returns:
            Spread strategy details
        """
        if prediction > 0.05:  # Bullish
            # Bull call spread
            lower_strike = underlying_price * 1.00
            upper_strike = underlying_price * 1.10

            return {
                'strategy': 'bull_call_spread',
                'buy_call_strike': lower_strike,
                'sell_call_strike': upper_strike,
                'max_profit': upper_strike - lower_strike,
                'max_loss': 'premium_paid',
                'break_even': lower_strike + 'net_premium',
                'confidence': abs(prediction)
            }

        elif prediction < -0.05:  # Bearish
            # Bear put spread
            lower_strike = underlying_price * 0.90
            upper_strike = underlying_price * 1.00

            return {
                'strategy': 'bear_put_spread',
                'buy_put_strike': upper_strike,
                'sell_put_strike': lower_strike,
                'max_profit': upper_strike - lower_strike,
                'max_loss': 'premium_paid',
                'break_even': upper_strike - 'net_premium',
                'confidence': abs(prediction)
            }

        else:
            return {'strategy': 'no_signal'}

    def straddle_signal(
        self,
        underlying_price: float,
        expected_move: float,
        implied_volatility: float,
        historical_volatility: float
    ) -> Dict[str, Any]:
        """
        Generate straddle strategy for volatility plays.

        Args:
            underlying_price: Current price
            expected_move: Expected price move magnitude
            implied_volatility: IV
            historical_volatility: HV

        Returns:
            Straddle strategy details
        """
        # Straddle profitable if IV is low vs HV
        iv_hv_ratio = implied_volatility / historical_volatility

        if iv_hv_ratio < 0.8 and expected_move > 0.1:
            # Long straddle (buy volatility)
            return {
                'strategy': 'long_straddle',
                'strike': underlying_price,
                'buy_call': True,
                'buy_put': True,
                'rationale': f'IV underpriced ({iv_hv_ratio:.2f}), expect {expected_move:.1%} move',
                'max_loss': 'total_premium',
                'profit_zones': f'Price < {underlying_price * (1 - expected_move):.2f} or > {underlying_price * (1 + expected_move):.2f}'
            }

        elif iv_hv_ratio > 1.2:
            # Short straddle (sell volatility)
            return {
                'strategy': 'short_straddle',
                'strike': underlying_price,
                'sell_call': True,
                'sell_put': True,
                'rationale': f'IV overpriced ({iv_hv_ratio:.2f})',
                'max_profit': 'total_premium',
                'risk': 'UNLIMITED - use with caution'
            }

        return {'strategy': 'no_signal'}


class PatternRecognitionStrategy:
    """
    Chart pattern recognition for trading signals.
    """

    def detect_head_and_shoulders(
        self,
        prices: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Detect head and shoulders pattern (bearish reversal).

        Args:
            prices: OHLCV data

        Returns:
            Pattern details or None
        """
        highs = prices['high'].values
        n = len(highs)

        if n < 60:
            return None

        # Look for three peaks
        recent = highs[-60:]
        peaks = []

        for i in range(5, len(recent) - 5):
            if all(recent[i] > recent[i - j] for j in range(1, 6)) and \
               all(recent[i] > recent[i + j] for j in range(1, 6)):
                peaks.append((i, recent[i]))

        if len(peaks) >= 3:
            # Check if middle peak is highest (head)
            peaks = sorted(peaks, key=lambda x: x[1], reverse=True)[:3]

            if peaks[0][0] > peaks[1][0] and peaks[0][0] > peaks[2][0]:
                return {
                    'pattern': 'head_and_shoulders',
                    'signal': 'bearish',
                    'confidence': 0.7,
                    'target': prices['close'].iloc[-1] * 0.90,  # 10% decline
                    'neckline': min(peaks[1][1], peaks[2][1])
                }

        return None

    def detect_double_bottom(
        self,
        prices: pd.DataFrame
    ) -> Optional[Dict[str, Any]]:
        """
        Detect double bottom pattern (bullish reversal).

        Args:
            prices: OHLCV data

        Returns:
            Pattern details or None
        """
        lows = prices['low'].values
        n = len(lows)

        if n < 40:
            return None

        recent = lows[-40:]
        troughs = []

        for i in range(5, len(recent) - 5):
            if all(recent[i] < recent[i - j] for j in range(1, 6)) and \
               all(recent[i] < recent[i + j] for j in range(1, 6)):
                troughs.append((i, recent[i]))

        if len(troughs) >= 2:
            # Check if two troughs at similar levels
            troughs = sorted(troughs, key=lambda x: x[1])[:2]

            price_diff = abs(troughs[0][1] - troughs[1][1]) / troughs[0][1]

            if price_diff < 0.02:  # Within 2%
                return {
                    'pattern': 'double_bottom',
                    'signal': 'bullish',
                    'confidence': 0.75,
                    'target': prices['close'].iloc[-1] * 1.10,  # 10% rise
                    'support_level': min(troughs[0][1], troughs[1][1])
                }

        return None


if __name__ == "__main__":
    # Example usage
    print("=== Trading Strategies Test ===\n")

    # Generate sample data
    dates = pd.date_range('2024-01-01', '2024-12-31', freq='D')
    np.random.seed(42)
    prices = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'high': 102 + np.cumsum(np.random.randn(len(dates)) * 2),
        'low': 98 + np.cumsum(np.random.randn(len(dates)) * 2),
        'close': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'volume': np.random.randint(1e6, 10e6, len(dates))
    }, index=dates)

    # Multi-market algorithm
    print("1. Multi-Market Algorithm")
    algo = MultiMarketAlgorithm(MarketType.STOCK)
    signal = algo.generate_signal(
        'AAPL',
        prices,
        {'prediction': 0.05}
    )

    if signal:
        print(f"   Signal: {signal.direction.value}")
        print(f"   Entry: ${signal.entry_price:.2f}")
        print(f"   Target: ${signal.target_price:.2f}")
        print(f"   Stop: ${signal.stop_loss:.2f}")
        print(f"   R/R Ratio: {signal.risk_reward_ratio:.2f}")

    # HFT Strategy
    print("\n2. HFT Market Making")
    hft = HFTStrategy()
    quotes = hft.market_making_signal(
        current_price=100.0,
        volatility=0.02,
        order_flow_imbalance=0.3
    )
    print(f"   Bid: ${quotes['bid_price']:.4f}")
    print(f"   Ask: ${quotes['ask_price']:.4f}")
    print(f"   Spread: {quotes['spread_bps']:.2f} bps")

    # Options Strategy
    print("\n3. Options Strategy")
    options = OptionsStrategy()
    spread = options.vertical_spread_signal(
        underlying_price=100.0,
        prediction=0.08,
        volatility=0.25
    )
    print(f"   Strategy: {spread.get('strategy')}")
    if 'buy_call_strike' in spread:
        print(f"   Buy call: ${spread['buy_call_strike']:.2f}")
        print(f"   Sell call: ${spread['sell_call_strike']:.2f}")

    # Pattern Recognition
    print("\n4. Pattern Recognition")
    pattern_strat = PatternRecognitionStrategy()
    pattern = pattern_strat.detect_double_bottom(prices)
    if pattern:
        print(f"   Pattern: {pattern['pattern']}")
        print(f"   Signal: {pattern['signal']}")
        print(f"   Target: ${pattern['target']:.2f}")
