"""
Pattern Detection Engine

Automatically detects active market patterns from the database
and generates trading signals based on pattern matching.

Integrates with the pattern database to:
1. Detect when patterns are active
2. Score pattern strength
3. Combine multiple pattern signals
4. Track pattern performance
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Import pattern database
sys.path.append(str(Path(__file__).parent.parent))
from data.pattern_database import PatternDatabase, MarketPattern


@dataclass
class PatternSignal:
    """Signal from a detected pattern"""
    pattern: MarketPattern
    signal_strength: float  # 0-1
    confidence: float  # 0-1
    detected_date: datetime
    expected_return: float
    expected_duration: int
    strength_factors_present: List[str]
    failure_signs_present: List[str]
    metadata: Dict[str, Any]


class PatternDetector:
    """
    Detects and scores market patterns from the database.
    """

    def __init__(self, db_path: str = "market_patterns.db"):
        """
        Initialize pattern detector.

        Args:
            db_path: Path to pattern database
        """
        self.db = PatternDatabase(db_path)
        self.active_patterns = []

    def detect_all_patterns(
        self,
        symbol: str,
        price_data: pd.DataFrame,
        current_date: datetime,
        market_type: str = 'stocks',
        additional_data: Optional[Dict[str, Any]] = None
    ) -> List[PatternSignal]:
        """
        Detect all applicable patterns for a symbol.

        Args:
            symbol: Ticker symbol
            price_data: Historical OHLCV data
            current_date: Current date
            market_type: Type of market
            additional_data: Additional data (fundamentals, etc.)

        Returns:
            List of detected pattern signals
        """
        additional_data = additional_data or {}

        # Get all patterns applicable to this market
        all_patterns = self.db.search_patterns(
            market=market_type,
            still_works_only=True
        )

        detected_signals = []

        for pattern in all_patterns:
            # Detect if pattern is active
            signal = self._detect_pattern(
                pattern, symbol, price_data, current_date, additional_data
            )

            if signal:
                detected_signals.append(signal)

        # Sort by strength
        detected_signals.sort(key=lambda x: x.signal_strength, reverse=True)

        return detected_signals

    def _detect_pattern(
        self,
        pattern: MarketPattern,
        symbol: str,
        price_data: pd.DataFrame,
        current_date: datetime,
        additional_data: Dict[str, Any]
    ) -> Optional[PatternSignal]:
        """
        Detect specific pattern using its detection function.
        """
        # Route to appropriate detection function
        detection_func = getattr(self, pattern.detection_function, None)

        if not detection_func:
            return None

        try:
            result = detection_func(
                pattern, symbol, price_data, current_date, additional_data
            )
            return result
        except Exception as e:
            # Pattern detection failed, skip
            return None

    # ===== SEASONAL PATTERN DETECTORS =====

    def detect_january_effect(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect January Effect"""
        if current_date.month != 1:
            return None

        # Check market cap bias
        market_cap = additional_data.get('market_cap', 0)
        is_small_cap = market_cap < 2e9  # < $2B

        # Stronger for small caps
        strength = 0.7 if is_small_cap else 0.4

        # Check strength factors
        strength_factors = []
        if price_data['close'].iloc[-252] if len(price_data) >= 252 else 0:
            yearly_return = (price_data['close'].iloc[-1] / price_data['close'].iloc[-252]) - 1
            if yearly_return < -0.15:
                strength += 0.2
                strength_factors.append('Strong prior year losses')

        # Check failure signs
        failure_signs = []
        if len(price_data) >= 20:
            dec_return = (price_data['close'].iloc[-1] / price_data['close'].iloc[-20]) - 1
            if dec_return > 0.15:
                strength -= 0.2
                failure_signs.append('Strong December rally')

        if strength < 0.3:
            return None

        return PatternSignal(
            pattern=pattern,
            signal_strength=min(1.0, strength),
            confidence=0.68,  # Historical win rate
            detected_date=current_date,
            expected_return=pattern.avg_return,
            expected_duration=pattern.avg_duration_days,
            strength_factors_present=strength_factors,
            failure_signs_present=failure_signs,
            metadata={'month': 1, 'is_small_cap': is_small_cap}
        )

    def detect_sell_in_may(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect Sell in May pattern"""
        if current_date.month < 5 or current_date.month > 10:
            return None

        # Pattern is bearish during May-October
        strength = 0.58  # Historical win rate

        return PatternSignal(
            pattern=pattern,
            signal_strength=strength,
            confidence=0.58,
            detected_date=current_date,
            expected_return=pattern.avg_return,  # Negative
            expected_duration=pattern.avg_duration_days,
            strength_factors_present=['Summer period'],
            failure_signs_present=[],
            metadata={'month': current_date.month}
        )

    def detect_santa_rally(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect Santa Claus Rally"""
        # Last 5 trading days of year + first 2 of new year
        if current_date.month == 12 and current_date.day >= 24:
            days_to_year_end = (datetime(current_date.year, 12, 31) - current_date).days
            if days_to_year_end <= 7:
                return PatternSignal(
                    pattern=pattern,
                    signal_strength=0.74,
                    confidence=0.74,
                    detected_date=current_date,
                    expected_return=pattern.avg_return,
                    expected_duration=7,
                    strength_factors_present=['Year-end optimism'],
                    failure_signs_present=[],
                    metadata={'days_to_year_end': days_to_year_end}
                )

        elif current_date.month == 1 and current_date.day <= 5:
            return PatternSignal(
                pattern=pattern,
                signal_strength=0.68,
                confidence=0.74,
                detected_date=current_date,
                expected_return=pattern.avg_return * 0.5,
                expected_duration=3,
                strength_factors_present=['New year continuation'],
                failure_signs_present=[],
                metadata={'days_into_year': current_date.day}
            )

        return None

    def detect_september_weakness(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect September weakness"""
        if current_date.month != 9:
            return None

        return PatternSignal(
            pattern=pattern,
            signal_strength=0.55,  # Moderate bearish
            confidence=0.55,
            detected_date=current_date,
            expected_return=pattern.avg_return,
            expected_duration=30,
            strength_factors_present=['September effect'],
            failure_signs_present=[],
            metadata={'month': 9}
        )

    def detect_monday_effect(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect Monday effect"""
        if current_date.weekday() != 0:  # Monday = 0
            return None

        # Note: This pattern has been largely arbitraged away
        return PatternSignal(
            pattern=pattern,
            signal_strength=0.3,  # Weak signal
            confidence=0.48,
            detected_date=current_date,
            expected_return=pattern.avg_return,
            expected_duration=1,
            strength_factors_present=[],
            failure_signs_present=['Pattern weakened over time'],
            metadata={'weekday': 'Monday'}
        )

    def detect_fomc_drift(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect FOMC announcement drift"""
        fomc_dates = additional_data.get('fomc_dates', [])

        # Check if within 24 hours before FOMC
        for fomc_date in fomc_dates:
            if isinstance(fomc_date, str):
                fomc_date = datetime.fromisoformat(fomc_date)

            days_until = (fomc_date - current_date).days

            if 0 <= days_until <= 1:
                return PatternSignal(
                    pattern=pattern,
                    signal_strength=0.65,
                    confidence=0.65,
                    detected_date=current_date,
                    expected_return=pattern.avg_return,
                    expected_duration=1,
                    strength_factors_present=['Pre-FOMC drift'],
                    failure_signs_present=[],
                    metadata={'fomc_date': fomc_date, 'days_until': days_until}
                )

        return None

    # ===== TECHNICAL PATTERN DETECTORS =====

    def detect_momentum(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect momentum pattern"""
        if len(price_data) < 63:  # Need 3 months of data
            return None

        # Calculate 3-month return
        returns_3m = (price_data['close'].iloc[-1] / price_data['close'].iloc[-63]) - 1

        # Momentum: positive if stock up > 10% in 3 months
        if returns_3m > 0.10:
            strength = min(1.0, returns_3m / 0.30)  # Scale to 30% max

            # Check volume confirmation
            recent_volume = price_data['volume'].iloc[-20:].mean()
            avg_volume = price_data['volume'].mean()

            strength_factors = []
            if recent_volume > avg_volume * 1.2:
                strength += 0.1
                strength_factors.append('Volume confirmation')

            return PatternSignal(
                pattern=pattern,
                signal_strength=min(1.0, strength),
                confidence=0.58,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=90,
                strength_factors_present=strength_factors,
                failure_signs_present=[],
                metadata={'3m_return': returns_3m}
            )

        return None

    def detect_mean_reversion(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect mean reversion opportunity"""
        if len(price_data) < 5:
            return None

        # Check for sharp decline in last 1-5 days
        returns_1w = (price_data['close'].iloc[-1] / price_data['close'].iloc[-5]) - 1

        if returns_1w < -0.05:  # Down > 5% in a week
            # Check RSI if available
            rsi = additional_data.get('rsi', 50)

            strength = min(1.0, abs(returns_1w) / 0.15)  # Scale to 15% max decline

            strength_factors = []
            if rsi < 30:
                strength += 0.2
                strength_factors.append('Oversold RSI')

            # Check volume
            if len(price_data) >= 20:
                recent_volume = price_data['volume'].iloc[-5:].mean()
                avg_volume = price_data['volume'].iloc[-20:].mean()

                if recent_volume > avg_volume * 1.5:
                    strength += 0.1
                    strength_factors.append('High volume on decline')

            if strength > 0.4:
                return PatternSignal(
                    pattern=pattern,
                    signal_strength=min(1.0, strength),
                    confidence=0.54,
                    detected_date=current_date,
                    expected_return=pattern.avg_return,
                    expected_duration=5,
                    strength_factors_present=strength_factors,
                    failure_signs_present=[],
                    metadata={'1w_return': returns_1w, 'rsi': rsi}
                )

        return None

    def detect_52_week_high(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect 52-week high breakout"""
        if len(price_data) < 252:
            return None

        current_price = price_data['close'].iloc[-1]
        year_high = price_data['high'].iloc[-252:].max()

        # Check if at or near 52-week high
        pct_from_high = (current_price / year_high) - 1

        if pct_from_high >= -0.02:  # Within 2% of 52-week high
            strength = 0.6

            strength_factors = []

            # Volume confirmation
            if len(price_data) >= 20:
                recent_volume = price_data['volume'].iloc[-5:].mean()
                avg_volume = price_data['volume'].iloc[-20:].mean()

                if recent_volume > avg_volume * 1.3:
                    strength += 0.2
                    strength_factors.append('Volume surge')

            return PatternSignal(
                pattern=pattern,
                signal_strength=min(1.0, strength),
                confidence=0.59,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=60,
                strength_factors_present=strength_factors,
                failure_signs_present=[],
                metadata={'pct_from_high': pct_from_high, 'year_high': year_high}
            )

        return None

    def detect_gap_fade(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect gap fade opportunity"""
        if len(price_data) < 2:
            return None

        # Check for gap
        today_open = price_data['open'].iloc[-1]
        yesterday_close = price_data['close'].iloc[-2]

        gap_pct = (today_open / yesterday_close) - 1

        # Large gap (>2%)
        if abs(gap_pct) > 0.02:
            strength = min(1.0, abs(gap_pct) / 0.05)

            # Check if it's fading
            current_price = price_data['close'].iloc[-1]
            intraday_move = (current_price / today_open) - 1

            # Gap up but fading down, or gap down but bouncing
            is_fading = (gap_pct > 0 and intraday_move < 0) or (gap_pct < 0 and intraday_move > 0)

            if is_fading:
                return PatternSignal(
                    pattern=pattern,
                    signal_strength=strength,
                    confidence=0.56,
                    detected_date=current_date,
                    expected_return=pattern.avg_return if gap_pct > 0 else -pattern.avg_return,
                    expected_duration=1,
                    strength_factors_present=['Gap fading'],
                    failure_signs_present=[],
                    metadata={'gap_pct': gap_pct, 'intraday_move': intraday_move}
                )

        return None

    # ===== FUNDAMENTAL PATTERN DETECTORS =====

    def detect_value_premium(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect value premium opportunity"""
        pe_ratio = additional_data.get('pe_ratio', None)
        pb_ratio = additional_data.get('price_to_book', None)

        if not pe_ratio and not pb_ratio:
            return None

        # Value: low P/E and P/B
        is_value = False
        strength = 0.0

        if pe_ratio and pe_ratio < 15:
            is_value = True
            strength += 0.5

        if pb_ratio and pb_ratio < 2:
            is_value = True
            strength += 0.3

        if is_value and strength > 0.5:
            strength_factors = []
            if pe_ratio and pe_ratio < 12:
                strength_factors.append('Very low P/E')
            if pb_ratio and pb_ratio < 1.5:
                strength_factors.append('Low P/B')

            return PatternSignal(
                pattern=pattern,
                signal_strength=min(1.0, strength),
                confidence=0.57,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=365,
                strength_factors_present=strength_factors,
                failure_signs_present=[],
                metadata={'pe_ratio': pe_ratio, 'pb_ratio': pb_ratio}
            )

        return None

    def detect_earnings_drift(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect post-earnings announcement drift"""
        earnings_surprise = additional_data.get('earnings_surprise', None)
        days_since_earnings = additional_data.get('days_since_earnings', 999)

        if earnings_surprise is None or days_since_earnings > 45:
            return None

        # Positive surprise within drift window
        if earnings_surprise > 0.05 and days_since_earnings < 45:
            strength = min(1.0, earnings_surprise / 0.20)  # Scale to 20% surprise

            strength_factors = []
            if earnings_surprise > 0.15:
                strength_factors.append('Large surprise')

            if additional_data.get('guidance_raised', False):
                strength += 0.15
                strength_factors.append('Guidance raised')

            return PatternSignal(
                pattern=pattern,
                signal_strength=min(1.0, strength),
                confidence=0.62,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=45 - days_since_earnings,
                strength_factors_present=strength_factors,
                failure_signs_present=[],
                metadata={
                    'earnings_surprise': earnings_surprise,
                    'days_since': days_since_earnings
                }
            )

        return None

    def detect_insider_buying(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect insider buying signal"""
        insider_buys = additional_data.get('insider_buys_30d', 0)
        insider_sells = additional_data.get('insider_sells_30d', 0)

        if insider_buys == 0:
            return None

        # Net buying
        if insider_buys > insider_sells * 2:  # At least 2:1 buy/sell
            strength = min(1.0, insider_buys / 5)  # Scale to 5 transactions

            strength_factors = []
            if insider_buys >= 3:
                strength_factors.append('Multiple insiders')

            if additional_data.get('ceo_buying', False):
                strength += 0.2
                strength_factors.append('CEO buying')

            return PatternSignal(
                pattern=pattern,
                signal_strength=min(1.0, strength),
                confidence=0.61,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=120,
                strength_factors_present=strength_factors,
                failure_signs_present=[],
                metadata={'insider_buys': insider_buys, 'insider_sells': insider_sells}
            )

        return None

    def detect_dividend_initiation(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect dividend initiation"""
        dividend_initiated = additional_data.get('dividend_initiated', False)
        days_since_announcement = additional_data.get('days_since_div_announcement', 999)

        if not dividend_initiated or days_since_announcement > 90:
            return None

        return PatternSignal(
            pattern=pattern,
            signal_strength=0.64,
            confidence=0.64,
            detected_date=current_date,
            expected_return=pattern.avg_return,
            expected_duration=90 - days_since_announcement,
            strength_factors_present=['Dividend initiation'],
            failure_signs_present=[],
            metadata={'days_since': days_since_announcement}
        )

    # ===== BEHAVIORAL PATTERN DETECTORS =====

    def detect_overreaction(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect overreaction reversal"""
        if len(price_data) < 1095:  # Need 3 years
            return None

        # 3-year return
        returns_3y = (price_data['close'].iloc[-1] / price_data['close'].iloc[-1095]) - 1

        # Extreme loser (down >50% in 3 years)
        if returns_3y < -0.50:
            strength = min(1.0, abs(returns_3y) / 1.0)

            strength_factors = []

            # Check for turnaround signs
            if len(price_data) >= 63:
                recent_return = (price_data['close'].iloc[-1] / price_data['close'].iloc[-63]) - 1
                if recent_return > 0:
                    strength += 0.2
                    strength_factors.append('Recent turnaround')

            return PatternSignal(
                pattern=pattern,
                signal_strength=min(1.0, strength),
                confidence=0.59,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=365,
                strength_factors_present=strength_factors,
                failure_signs_present=[],
                metadata={'3y_return': returns_3y}
            )

        return None

    def detect_lottery_stocks(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect lottery stock characteristics"""
        current_price = price_data['close'].iloc[-1]
        market_cap = additional_data.get('market_cap', 1e10)

        if len(price_data) < 20:
            return None

        volatility = price_data['close'].pct_change().std() * np.sqrt(252)

        # Lottery stock: low price, small cap, high volatility
        is_lottery = current_price < 10 and market_cap < 500e6 and volatility > 0.60

        if is_lottery:
            return PatternSignal(
                pattern=pattern,
                signal_strength=0.65,  # Bearish signal
                confidence=0.65,
                detected_date=current_date,
                expected_return=pattern.avg_return,  # Negative
                expected_duration=180,
                strength_factors_present=['Low price', 'Small cap', 'High volatility'],
                failure_signs_present=[],
                metadata={
                    'price': current_price,
                    'market_cap': market_cap,
                    'volatility': volatility
                }
            )

        return None

    def detect_attention_spike(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect attention-grabbing spike"""
        if len(price_data) < 20:
            return None

        # Check for unusual volume
        recent_volume = price_data['volume'].iloc[-1]
        avg_volume = price_data['volume'].iloc[-20:-1].mean()

        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1

        # Check for unusual price move
        price_change = price_data['close'].pct_change().iloc[-1]

        if volume_ratio > 3.0 or abs(price_change) > 0.10:
            # Attention spike - expect short-term pop then reversion
            strength = min(1.0, (volume_ratio / 5.0 + abs(price_change) / 0.20) / 2)

            return PatternSignal(
                pattern=pattern,
                signal_strength=strength,
                confidence=0.52,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=3,
                strength_factors_present=['Volume spike', 'Price spike'],
                failure_signs_present=[],
                metadata={
                    'volume_ratio': volume_ratio,
                    'price_change': price_change
                }
            )

        return None

    def detect_52_week_low(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect 52-week low anchoring"""
        if len(price_data) < 252:
            return None

        current_price = price_data['close'].iloc[-1]
        year_low = price_data['low'].iloc[-252:].min()

        pct_from_low = (current_price / year_low) - 1

        if pct_from_low <= 0.02:  # Within 2% of 52-week low
            return PatternSignal(
                pattern=pattern,
                signal_strength=0.54,  # Moderate bearish
                confidence=0.54,
                detected_date=current_date,
                expected_return=pattern.avg_return,  # Negative
                expected_duration=30,
                strength_factors_present=['Near 52-week low'],
                failure_signs_present=[],
                metadata={'pct_from_low': pct_from_low, 'year_low': year_low}
            )

        return None

    # ===== MACRO PATTERN DETECTORS =====

    def detect_fed_model_signal(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect Fed model signal"""
        earnings_yield = additional_data.get('earnings_yield', None)
        treasury_10y = additional_data.get('treasury_10y_yield', 0.05)

        if earnings_yield is None:
            return None

        # Fed model: stocks attractive when E/P > Treasury yield
        spread = earnings_yield - treasury_10y

        if spread > 0.02:  # 200 bps spread
            strength = min(1.0, spread / 0.06)  # Scale to 600 bps

            return PatternSignal(
                pattern=pattern,
                signal_strength=strength,
                confidence=0.60,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=180,
                strength_factors_present=[f'Wide spread: {spread:.1%}'],
                failure_signs_present=[],
                metadata={'earnings_yield': earnings_yield, 'treasury_yield': treasury_10y, 'spread': spread}
            )

        return None

    def detect_yield_curve_inversion(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect yield curve inversion"""
        treasury_2y = additional_data.get('treasury_2y_yield', 0.05)
        treasury_10y = additional_data.get('treasury_10y_yield', 0.05)

        spread = treasury_10y - treasury_2y

        if spread < 0:  # Inverted
            strength = min(1.0, abs(spread) / 0.015)  # Scale to 150 bps inversion

            return PatternSignal(
                pattern=pattern,
                signal_strength=strength,
                confidence=0.78,  # Strong historical predictor
                detected_date=current_date,
                expected_return=pattern.avg_return,  # Negative
                expected_duration=365,
                strength_factors_present=['Yield curve inverted'],
                failure_signs_present=[],
                metadata={'2y_yield': treasury_2y, '10y_yield': treasury_10y, 'spread': spread}
            )

        return None

    def detect_dollar_strength(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect strong dollar effect"""
        dxy_change = additional_data.get('dxy_3m_change', 0)

        # Dollar up >5% in 3 months
        if dxy_change > 0.05:
            strength = min(1.0, dxy_change / 0.15)

            return PatternSignal(
                pattern=pattern,
                signal_strength=strength,
                confidence=0.62,
                detected_date=current_date,
                expected_return=pattern.avg_return,  # Negative for EM/commodities
                expected_duration=120,
                strength_factors_present=['Dollar strength'],
                failure_signs_present=[],
                metadata={'dxy_change': dxy_change}
            )

        return None

    def detect_vix_spike(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect VIX spike reversal"""
        vix = additional_data.get('vix', 20)

        if vix > 30:  # VIX spike
            strength = min(1.0, vix / 50)  # Scale to VIX 50

            strength_factors = []
            if vix > 40:
                strength_factors.append('Extreme fear (VIX > 40)')

            return PatternSignal(
                pattern=pattern,
                signal_strength=strength,
                confidence=0.67,
                detected_date=current_date,
                expected_return=pattern.avg_return,
                expected_duration=30,
                strength_factors_present=strength_factors,
                failure_signs_present=[],
                metadata={'vix': vix}
            )

        return None

    def detect_short_squeeze(
        self, pattern, symbol, price_data, current_date, additional_data
    ) -> Optional[PatternSignal]:
        """Detect short squeeze potential"""
        short_interest = additional_data.get('short_interest_pct', 0)

        if short_interest > 0.15:  # >15% short interest
            # Check for positive catalyst
            recent_return = price_data['close'].pct_change().iloc[-1] if len(price_data) > 0 else 0

            if recent_return > 0.05:  # Up >5% today
                strength = min(1.0, short_interest / 0.30)  # Scale to 30% SI

                return PatternSignal(
                    pattern=pattern,
                    signal_strength=strength,
                    confidence=0.58,
                    detected_date=current_date,
                    expected_return=pattern.avg_return,
                    expected_duration=7,
                    strength_factors_present=['High short interest', 'Positive catalyst'],
                    failure_signs_present=[],
                    metadata={
                        'short_interest': short_interest,
                        'price_change': recent_return
                    }
                )

        return None

    def combine_pattern_signals(
        self,
        signals: List[PatternSignal]
    ) -> Dict[str, float]:
        """
        Combine multiple pattern signals into unified prediction.

        Args:
            signals: List of detected patterns

        Returns:
            Combined prediction with factors
        """
        if not signals:
            return {'prediction': 0.0, 'confidence': 0.0, 'num_patterns': 0}

        # Weight by signal strength * confidence * Sharpe ratio
        weighted_returns = []
        weights = []

        for signal in signals:
            weight = signal.signal_strength * signal.confidence * max(0.1, signal.pattern.sharpe_ratio)
            weighted_returns.append(signal.expected_return * weight)
            weights.append(weight)

        total_weight = sum(weights)

        if total_weight == 0:
            return {'prediction': 0.0, 'confidence': 0.0, 'num_patterns': len(signals)}

        # Weighted average prediction
        combined_prediction = sum(weighted_returns) / total_weight

        # Average confidence
        avg_confidence = sum(s.confidence * w for s, w in zip(signals, weights)) / total_weight

        # Pattern breakdown by category
        category_counts = {}
        for signal in signals:
            cat = signal.pattern.category
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            'prediction': combined_prediction,
            'confidence': avg_confidence,
            'num_patterns': len(signals),
            'category_breakdown': category_counts,
            'top_patterns': [
                {
                    'name': s.pattern.name,
                    'strength': s.signal_strength,
                    'expected_return': s.expected_return
                }
                for s in signals[:5]
            ]
        }


if __name__ == "__main__":
    # Example usage
    print("=== Pattern Detection System ===\n")

    # Initialize detector
    detector = PatternDetector("market_patterns.db")

    # Generate sample data
    dates = pd.date_range('2020-01-01', '2025-01-15', freq='D')
    np.random.seed(42)

    price_data = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'high': 102 + np.cumsum(np.random.randn(len(dates)) * 2),
        'low': 98 + np.cumsum(np.random.randn(len(dates)) * 2),
        'close': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'volume': np.random.randint(1e6, 10e6, len(dates))
    }, index=dates)

    # Additional data
    additional_data = {
        'market_cap': 5e9,  # $5B small cap
        'pe_ratio': 18,
        'price_to_book': 2.5,
        'vix': 25,
        'short_interest_pct': 0.08,
        'insider_buys_30d': 2,
        'insider_sells_30d': 0,
        'treasury_2y_yield': 0.048,
        'treasury_10y_yield': 0.045,  # Inverted!
        'earnings_yield': 0.06
    }

    # Detect patterns
    print("Detecting patterns for symbol AAPL...")
    current_date = datetime(2025, 1, 15)

    signals = detector.detect_all_patterns(
        symbol='AAPL',
        price_data=price_data,
        current_date=current_date,
        market_type='stocks',
        additional_data=additional_data
    )

    print(f"\n✓ Detected {len(signals)} active patterns\n")

    # Show top patterns
    print("=== Top 10 Active Patterns ===")
    for i, signal in enumerate(signals[:10], 1):
        print(f"\n{i}. {signal.pattern.name}")
        print(f"   Category: {signal.pattern.category}")
        print(f"   Signal Strength: {signal.signal_strength:.2f}")
        print(f"   Confidence: {signal.confidence:.1%}")
        print(f"   Expected Return: {signal.expected_return:+.1%}")
        print(f"   Duration: {signal.expected_duration} days")

        if signal.strength_factors_present:
            print(f"   Strength Factors:")
            for factor in signal.strength_factors_present:
                print(f"     • {factor}")

    # Combine signals
    print("\n=== Combined Pattern Signal ===")
    combined = detector.combine_pattern_signals(signals)

    print(f"Overall Prediction: {combined['prediction']:+.2%}")
    print(f"Confidence: {combined['confidence']:.1%}")
    print(f"Active Patterns: {combined['num_patterns']}")
    print(f"\nCategory Breakdown:")
    for category, count in combined['category_breakdown'].items():
        print(f"  {category}: {count}")

    print(f"\nTop Contributing Patterns:")
    for pattern in combined['top_patterns']:
        print(f"  • {pattern['name']}: {pattern['expected_return']:+.1%} (strength: {pattern['strength']:.2f})")

    detector.db.close()
