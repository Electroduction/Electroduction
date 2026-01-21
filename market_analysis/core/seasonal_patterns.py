"""
Seasonal Pattern Analysis Module

Analyzes and quantifies calendar-based market anomalies:
- January Effect (small-cap outperformance)
- MLK Day effect (reversal patterns)
- Monthly seasonality
- Day-of-week effects
- Holiday effects
- Dividend calendar patterns
- Quarter-end effects
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MonthEffect(Enum):
    """Common monthly market effects"""
    JANUARY = "january_effect"
    SEPTEMBER_WEAK = "september_weakness"
    NOVEMBER_STRONG = "november_strength"
    DECEMBER_RALLY = "december_rally"
    SELL_IN_MAY = "sell_in_may"


@dataclass
class SeasonalSignal:
    """Represents a seasonal trading signal"""
    pattern_name: str
    signal_strength: float  # -1.0 to 1.0 (negative = sell, positive = buy)
    probability: float  # Historical win rate
    expected_return: float  # Expected return magnitude
    confidence: float  # Statistical confidence (0-1)
    start_date: datetime
    end_date: datetime
    description: str


class SeasonalPatternAnalyzer:
    """
    Analyzes historical price data to identify and quantify seasonal patterns.
    """

    def __init__(self):
        # MLK Day is 3rd Monday in January
        self.mlk_day_reversal_probability = 0.62  # User mentioned 62% loss probability

        # Historical monthly returns (approximate S&P 500 averages)
        self.monthly_avg_returns = {
            1: 0.011,   # January (best)
            2: 0.002,
            3: 0.006,
            4: 0.013,   # April (strong)
            5: 0.001,
            6: -0.002,
            7: 0.009,
            8: -0.004,
            9: -0.008,  # September (worst)
            10: 0.007,
            11: 0.015,  # November (strong)
            12: 0.014   # December (strong)
        }

        # Day of week effects (Monday = 0, Friday = 4)
        self.weekday_avg_returns = {
            0: -0.001,  # Monday (weak)
            1: 0.002,
            2: 0.003,   # Tuesday (strongest)
            3: 0.001,
            4: 0.002    # Friday (positive bias)
        }

    def analyze_january_effect(
        self,
        prices_large_cap: pd.Series,
        prices_small_cap: pd.Series,
        years: Optional[List[int]] = None
    ) -> Dict[str, float]:
        """
        Analyze January Effect: small-cap stocks outperform large-cap in January.

        Hypothesis: Tax-loss selling in December depresses small-caps,
        which rebound in January.

        Args:
            prices_large_cap: Large-cap index prices (e.g., S&P 500)
            prices_small_cap: Small-cap index prices (e.g., Russell 2000)
            years: Specific years to analyze (None = all available)

        Returns:
            Dictionary with effect statistics
        """
        # Filter for January only
        large_jan = prices_large_cap[prices_large_cap.index.month == 1]
        small_jan = prices_small_cap[prices_small_cap.index.month == 1]

        # Calculate monthly returns for each January
        large_returns = []
        small_returns = []

        for year in large_jan.index.year.unique():
            if years and year not in years:
                continue

            large_year = large_jan[large_jan.index.year == year]
            small_year = small_jan[small_jan.index.year == year]

            if len(large_year) > 1 and len(small_year) > 1:
                large_ret = (large_year.iloc[-1] / large_year.iloc[0]) - 1
                small_ret = (small_year.iloc[-1] / small_year.iloc[0]) - 1

                large_returns.append(large_ret)
                small_returns.append(small_ret)

        if not large_returns:
            return {'error': 'Insufficient data'}

        large_returns = np.array(large_returns)
        small_returns = np.array(small_returns)
        outperformance = small_returns - large_returns

        return {
            'avg_large_cap_return': np.mean(large_returns),
            'avg_small_cap_return': np.mean(small_returns),
            'avg_outperformance': np.mean(outperformance),
            'outperformance_std': np.std(outperformance),
            'pct_years_outperformed': np.mean(outperformance > 0),
            'max_outperformance': np.max(outperformance),
            'min_outperformance': np.min(outperformance),
            'n_years': len(large_returns)
        }

    def detect_mlk_day_effect(
        self,
        prices: pd.Series,
        year: int
    ) -> Dict[str, float]:
        """
        Analyze price action around MLK Day (3rd Monday in January).

        User hypothesis: High probability of reversal or loss continuation.
        Traders may take profits or meet quotas.

        Args:
            prices: Daily price series
            year: Year to analyze

        Returns:
            Dictionary with pre/post MLK statistics
        """
        # Find MLK Day (3rd Monday in January)
        jan_first = datetime(year, 1, 1)
        days_until_monday = (7 - jan_first.weekday()) % 7
        first_monday = jan_first + timedelta(days=days_until_monday)
        mlk_day = first_monday + timedelta(weeks=2)

        # Get prices 5 days before and after
        start_window = mlk_day - timedelta(days=7)
        end_window = mlk_day + timedelta(days=7)

        window_prices = prices[
            (prices.index >= start_window) & (prices.index <= end_window)
        ]

        if len(window_prices) < 5:
            return {'error': 'Insufficient data around MLK Day'}

        # Find actual MLK Day price (or closest trading day)
        mlk_idx = window_prices.index.get_indexer([mlk_day], method='nearest')[0]
        mlk_price = window_prices.iloc[mlk_idx]

        # Pre-MLK trend (5 days before)
        pre_mlk = window_prices.iloc[:mlk_idx]
        if len(pre_mlk) >= 2:
            pre_trend = (pre_mlk.iloc[-1] / pre_mlk.iloc[0]) - 1
        else:
            pre_trend = 0

        # Post-MLK trend (5 days after)
        post_mlk = window_prices.iloc[mlk_idx:]
        if len(post_mlk) >= 2:
            post_trend = (post_mlk.iloc[-1] / post_mlk.iloc[0]) - 1
        else:
            post_trend = 0

        # Check for reversal
        is_reversal = (pre_trend > 0 and post_trend < 0) or (pre_trend < 0 and post_trend > 0)

        return {
            'mlk_day': mlk_day.strftime('%Y-%m-%d'),
            'pre_mlk_return': pre_trend,
            'post_mlk_return': post_trend,
            'is_reversal': is_reversal,
            'reversal_magnitude': abs(post_trend - pre_trend),
            'total_window_return': (window_prices.iloc[-1] / window_prices.iloc[0]) - 1
        }

    def analyze_monthly_patterns(
        self,
        prices: pd.Series,
        min_years: int = 5
    ) -> pd.DataFrame:
        """
        Analyze return patterns for each month across multiple years.

        Args:
            prices: Daily price series with datetime index
            min_years: Minimum years of data required

        Returns:
            DataFrame with monthly statistics
        """
        # Calculate monthly returns
        monthly_data = []

        for month in range(1, 13):
            month_prices = prices[prices.index.month == month]

            yearly_returns = []
            for year in month_prices.index.year.unique():
                year_month = month_prices[month_prices.index.year == year]
                if len(year_month) > 1:
                    ret = (year_month.iloc[-1] / year_month.iloc[0]) - 1
                    yearly_returns.append(ret)

            if len(yearly_returns) >= min_years:
                monthly_data.append({
                    'month': month,
                    'month_name': datetime(2000, month, 1).strftime('%B'),
                    'avg_return': np.mean(yearly_returns),
                    'median_return': np.median(yearly_returns),
                    'std_return': np.std(yearly_returns),
                    'win_rate': np.mean(np.array(yearly_returns) > 0),
                    'max_return': np.max(yearly_returns),
                    'min_return': np.min(yearly_returns),
                    'n_years': len(yearly_returns),
                    'sharpe_ratio': np.mean(yearly_returns) / np.std(yearly_returns) if np.std(yearly_returns) > 0 else 0
                })

        df = pd.DataFrame(monthly_data)
        if not df.empty:
            df['rank'] = df['avg_return'].rank(ascending=False)
            df = df.sort_values('rank')

        return df

    def detect_day_of_week_effect(
        self,
        prices: pd.Series,
        min_observations: int = 50
    ) -> pd.DataFrame:
        """
        Analyze if certain weekdays have consistent return patterns.

        Classic findings:
        - Monday: Often weak (weekend news)
        - Tuesday: Historically strongest
        - Friday: Positive bias (weekend optimism)

        Args:
            prices: Daily price series
            min_observations: Minimum days per weekday

        Returns:
            DataFrame with weekday statistics
        """
        # Calculate daily returns
        returns = prices.pct_change().dropna()

        weekday_data = []
        for weekday in range(5):  # Monday=0 to Friday=4
            weekday_returns = returns[returns.index.weekday == weekday]

            if len(weekday_returns) >= min_observations:
                weekday_data.append({
                    'weekday': weekday,
                    'weekday_name': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'][weekday],
                    'avg_return': np.mean(weekday_returns),
                    'median_return': np.median(weekday_returns),
                    'std_return': np.std(weekday_returns),
                    'win_rate': np.mean(weekday_returns > 0),
                    'n_observations': len(weekday_returns),
                    'sharpe_ratio': np.mean(weekday_returns) / np.std(weekday_returns) * np.sqrt(252) if np.std(weekday_returns) > 0 else 0
                })

        df = pd.DataFrame(weekday_data)
        if not df.empty:
            df['rank'] = df['avg_return'].rank(ascending=False)
            df = df.sort_values('rank')

        return df

    def identify_dividend_seasonality(
        self,
        dividend_dates: List[datetime],
        prices: pd.Series,
        window_days: int = 5
    ) -> Dict[str, float]:
        """
        Analyze price patterns around ex-dividend dates.

        Typical pattern:
        - Price rises before ex-div (dividend capture)
        - Drops by ~dividend amount on ex-div
        - May drift back up after

        Args:
            dividend_dates: List of ex-dividend dates
            prices: Daily price series
            window_days: Days before/after to analyze

        Returns:
            Dictionary with dividend effect statistics
        """
        pre_div_returns = []
        post_div_returns = []
        ex_div_changes = []

        for ex_date in dividend_dates:
            # Window around ex-div
            start = ex_date - timedelta(days=window_days + 2)
            end = ex_date + timedelta(days=window_days + 2)

            window = prices[(prices.index >= start) & (prices.index <= end)]

            if len(window) < 3:
                continue

            # Find ex-div day price
            ex_idx = window.index.get_indexer([ex_date], method='nearest')[0]

            if ex_idx > 0 and ex_idx < len(window) - 1:
                # Pre ex-div return (5 days before to day before)
                pre_window = window.iloc[:ex_idx]
                if len(pre_window) >= 2:
                    pre_ret = (pre_window.iloc[-1] / pre_window.iloc[0]) - 1
                    pre_div_returns.append(pre_ret)

                # Ex-div day change
                ex_change = (window.iloc[ex_idx] / window.iloc[ex_idx - 1]) - 1
                ex_div_changes.append(ex_change)

                # Post ex-div return (day after to 5 days after)
                post_window = window.iloc[ex_idx + 1:]
                if len(post_window) >= 2:
                    post_ret = (post_window.iloc[-1] / post_window.iloc[0]) - 1
                    post_div_returns.append(post_ret)

        return {
            'avg_pre_div_return': np.mean(pre_div_returns) if pre_div_returns else 0,
            'avg_ex_div_change': np.mean(ex_div_changes) if ex_div_changes else 0,
            'avg_post_div_return': np.mean(post_div_returns) if post_div_returns else 0,
            'n_events': len(dividend_dates)
        }

    def generate_seasonal_signals(
        self,
        current_date: datetime,
        symbol: str = "SPY"
    ) -> List[SeasonalSignal]:
        """
        Generate trading signals based on seasonal patterns.

        Args:
            current_date: Current date for signal generation
            symbol: Stock/index symbol

        Returns:
            List of seasonal trading signals
        """
        signals = []
        month = current_date.month
        weekday = current_date.weekday()

        # January Effect signal
        if month == 1:
            signals.append(SeasonalSignal(
                pattern_name="January Effect",
                signal_strength=0.7,  # Moderately bullish
                probability=0.65,  # Historical win rate
                expected_return=0.011,  # 1.1% average
                confidence=0.75,
                start_date=datetime(current_date.year, 1, 1),
                end_date=datetime(current_date.year, 1, 31),
                description="Small-cap outperformance in January due to tax-loss selling reversal"
            ))

        # MLK Day Effect (around 3rd Monday in January)
        if month == 1:
            jan_first = datetime(current_date.year, 1, 1)
            days_until_monday = (7 - jan_first.weekday()) % 7
            first_monday = jan_first + timedelta(days=days_until_monday)
            mlk_day = first_monday + timedelta(weeks=2)

            if abs((current_date - mlk_day).days) <= 3:
                signals.append(SeasonalSignal(
                    pattern_name="MLK Day Reversal",
                    signal_strength=-0.5,  # Moderately bearish
                    probability=self.mlk_day_reversal_probability,
                    expected_return=-0.005,  # -0.5%
                    confidence=0.62,
                    start_date=mlk_day - timedelta(days=1),
                    end_date=mlk_day + timedelta(days=3),
                    description="Potential reversal or profit-taking around MLK Day"
                ))

        # Sell in May effect
        if month == 5:
            signals.append(SeasonalSignal(
                pattern_name="Sell in May",
                signal_strength=-0.4,  # Mildly bearish
                probability=0.58,
                expected_return=-0.001,
                confidence=0.60,
                start_date=datetime(current_date.year, 5, 1),
                end_date=datetime(current_date.year, 10, 31),
                description="Historical underperformance May-October vs November-April"
            ))

        # September weakness
        if month == 9:
            signals.append(SeasonalSignal(
                pattern_name="September Weakness",
                signal_strength=-0.6,  # Bearish
                probability=0.60,
                expected_return=-0.008,  # -0.8%
                confidence=0.70,
                start_date=datetime(current_date.year, 9, 1),
                end_date=datetime(current_date.year, 9, 30),
                description="September historically worst month for stocks"
            ))

        # November-December rally
        if month in [11, 12]:
            signals.append(SeasonalSignal(
                pattern_name="Year-End Rally",
                signal_strength=0.8,  # Bullish
                probability=0.68,
                expected_return=0.014,  # 1.4%
                confidence=0.78,
                start_date=datetime(current_date.year, 11, 1),
                end_date=datetime(current_date.year, 12, 31),
                description="Strong year-end performance driven by bonuses, window dressing, holiday optimism"
            ))

        # Monday weakness
        if weekday == 0:  # Monday
            signals.append(SeasonalSignal(
                pattern_name="Monday Effect",
                signal_strength=-0.2,  # Slightly bearish
                probability=0.52,
                expected_return=-0.001,
                confidence=0.55,
                start_date=current_date,
                end_date=current_date,
                description="Mondays tend to be weak due to weekend news digestion"
            ))

        # Tuesday strength
        if weekday == 1:  # Tuesday
            signals.append(SeasonalSignal(
                pattern_name="Tuesday Strength",
                signal_strength=0.3,  # Slightly bullish
                probability=0.55,
                expected_return=0.003,
                confidence=0.58,
                start_date=current_date,
                end_date=current_date,
                description="Tuesdays historically strongest day of week"
            ))

        return signals

    def calculate_seasonal_score(
        self,
        current_date: datetime,
        lookback_years: int = 10
    ) -> float:
        """
        Calculate overall seasonal favorability score for current date.

        Args:
            current_date: Date to score
            lookback_years: Years of historical data to consider

        Returns:
            Score from -1.0 (very unfavorable) to 1.0 (very favorable)
        """
        signals = self.generate_seasonal_signals(current_date)

        if not signals:
            return 0.0

        # Weight signals by confidence
        weighted_sum = sum(s.signal_strength * s.confidence for s in signals)
        weight_total = sum(s.confidence for s in signals)

        if weight_total == 0:
            return 0.0

        return weighted_sum / weight_total


if __name__ == "__main__":
    # Example usage and tests
    analyzer = SeasonalPatternAnalyzer()

    # Generate example price data
    dates = pd.date_range(start='2020-01-01', end='2024-12-31', freq='D')
    np.random.seed(42)
    prices = pd.Series(
        100 * np.exp(np.cumsum(np.random.randn(len(dates)) * 0.01)),
        index=dates
    )

    print("=== Monthly Pattern Analysis ===")
    monthly_patterns = analyzer.analyze_monthly_patterns(prices)
    print(monthly_patterns[['month_name', 'avg_return', 'win_rate', 'rank']].head(10))

    print("\n=== Day of Week Analysis ===")
    weekday_patterns = analyzer.detect_day_of_week_effect(prices)
    print(weekday_patterns[['weekday_name', 'avg_return', 'win_rate']])

    print("\n=== Current Seasonal Signals ===")
    current_signals = analyzer.generate_seasonal_signals(datetime.now())
    for signal in current_signals:
        print(f"\n{signal.pattern_name}:")
        print(f"  Strength: {signal.signal_strength:+.2f}")
        print(f"  Probability: {signal.probability:.1%}")
        print(f"  Expected Return: {signal.expected_return:+.2%}")
        print(f"  {signal.description}")

    print(f"\n=== Overall Seasonal Score ===")
    score = analyzer.calculate_seasonal_score(datetime.now())
    print(f"Seasonal favorability: {score:+.2f} (-1.0 to +1.0)")
