"""
Data Collection Apparatus

Comprehensive data gathering system for market analysis:
- Market data (stocks, futures, indexes, options)
- News and sentiment
- Social media
- Economic indicators
- Alternative data

Supports multiple providers and data frequencies.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
import warnings


class DataSource(Enum):
    """Available data sources"""
    YAHOO_FINANCE = "yahoo"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex"
    QUANDL = "quandl"
    FRED = "fred"  # Economic data
    NEWS_API = "news_api"
    TWITTER = "twitter"
    REDDIT = "reddit"


class DataFrequency(Enum):
    """Data update frequencies"""
    TICK = "tick"  # Real-time tick data
    SECOND = "1s"
    MINUTE = "1min"
    FIVE_MINUTE = "5min"
    FIFTEEN_MINUTE = "15min"
    HOUR = "1h"
    DAILY = "1d"
    WEEKLY = "1w"
    MONTHLY = "1mo"


@dataclass
class MarketDataConfig:
    """Configuration for market data collection"""
    symbols: List[str]
    start_date: datetime
    end_date: datetime
    frequency: DataFrequency = DataFrequency.DAILY
    include_extended_hours: bool = False
    include_dividends: bool = True
    include_splits: bool = True


@dataclass
class CollectedData:
    """Container for collected market data"""
    symbol: str
    data_type: str
    frequency: str
    data: pd.DataFrame
    metadata: Dict[str, Any] = field(default_factory=dict)
    collection_timestamp: datetime = field(default_factory=datetime.now)


class MarketDataCollector:
    """
    Collects market data from various sources.
    """

    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Args:
            api_keys: Dictionary of API keys for various services
        """
        self.api_keys = api_keys or {}
        self.rate_limits = {}
        self._setup_rate_limits()

    def _setup_rate_limits(self):
        """Configure rate limits for different APIs"""
        self.rate_limits = {
            DataSource.YAHOO_FINANCE: {'calls_per_minute': 2000, 'last_call': 0},
            DataSource.ALPHA_VANTAGE: {'calls_per_minute': 5, 'last_call': 0},
            DataSource.IEX_CLOUD: {'calls_per_minute': 100, 'last_call': 0}
        }

    def _respect_rate_limit(self, source: DataSource):
        """Enforce rate limiting"""
        if source not in self.rate_limits:
            return

        limit_info = self.rate_limits[source]
        current_time = time.time()
        time_since_last = current_time - limit_info['last_call']

        min_interval = 60.0 / limit_info['calls_per_minute']

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            time.sleep(sleep_time)

        limit_info['last_call'] = time.time()

    def collect_ohlcv(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        frequency: DataFrequency = DataFrequency.DAILY,
        source: DataSource = DataSource.YAHOO_FINANCE
    ) -> CollectedData:
        """
        Collect OHLCV (Open, High, Low, Close, Volume) data.

        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            frequency: Data frequency
            source: Data provider

        Returns:
            CollectedData object
        """
        self._respect_rate_limit(source)

        # Simulate data collection (in production, call actual APIs)
        data = self._simulate_ohlcv_data(symbol, start_date, end_date, frequency)

        return CollectedData(
            symbol=symbol,
            data_type='ohlcv',
            frequency=frequency.value,
            data=data,
            metadata={
                'source': source.value,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        )

    def _simulate_ohlcv_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        frequency: DataFrequency
    ) -> pd.DataFrame:
        """
        Simulate OHLCV data (replace with actual API calls in production).
        """
        # Generate date range
        if frequency == DataFrequency.DAILY:
            dates = pd.date_range(start_date, end_date, freq='D')
        elif frequency == DataFrequency.HOUR:
            dates = pd.date_range(start_date, end_date, freq='H')
        elif frequency == DataFrequency.MINUTE:
            dates = pd.date_range(start_date, end_date, freq='min')
        else:
            dates = pd.date_range(start_date, end_date, freq='D')

        # Simulate realistic price data
        n = len(dates)
        returns = np.random.randn(n) * 0.02  # 2% daily volatility
        close = 100 * np.exp(np.cumsum(returns))

        # OHLC around close
        high = close * (1 + np.abs(np.random.randn(n)) * 0.01)
        low = close * (1 - np.abs(np.random.randn(n)) * 0.01)
        open_price = np.roll(close, 1)
        open_price[0] = close[0]

        volume = np.random.randint(1000000, 10000000, n)

        return pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)

    def collect_options_chain(
        self,
        symbol: str,
        expiration_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Collect options chain data.

        Args:
            symbol: Underlying symbol
            expiration_date: Specific expiration (None = all)

        Returns:
            DataFrame with options data
        """
        # Simulate options chain
        strikes = np.arange(80, 121, 5)  # $80-$120 in $5 increments

        options_data = []
        for strike in strikes:
            # Calls
            options_data.append({
                'strike': strike,
                'type': 'call',
                'bid': max(0, 100 - strike - 2),
                'ask': max(0, 100 - strike + 2),
                'volume': np.random.randint(0, 1000),
                'open_interest': np.random.randint(0, 5000),
                'implied_volatility': 0.2 + np.random.randn() * 0.05
            })

            # Puts
            options_data.append({
                'strike': strike,
                'type': 'put',
                'bid': max(0, strike - 100 - 2),
                'ask': max(0, strike - 100 + 2),
                'volume': np.random.randint(0, 1000),
                'open_interest': np.random.randint(0, 5000),
                'implied_volatility': 0.2 + np.random.randn() * 0.05
            })

        return pd.DataFrame(options_data)

    def collect_fundamentals(
        self,
        symbol: str
    ) -> Dict[str, Any]:
        """
        Collect fundamental data for a company.

        Args:
            symbol: Ticker symbol

        Returns:
            Dictionary with fundamental metrics
        """
        # Simulate fundamental data
        return {
            'symbol': symbol,
            'company_name': f"{symbol} Corporation",
            'sector': 'Technology',
            'industry': 'Software',

            # Valuation
            'market_cap': 500e9,
            'enterprise_value': 520e9,
            'pe_ratio': 25.5,
            'peg_ratio': 1.8,
            'price_to_book': 8.2,
            'price_to_sales': 12.3,
            'ev_to_ebitda': 18.5,

            # Profitability
            'profit_margin': 0.25,
            'operating_margin': 0.30,
            'return_on_equity': 0.35,
            'return_on_assets': 0.20,

            # Growth
            'revenue_growth': 0.25,
            'earnings_growth': 0.30,
            'revenue_per_share_growth': 0.22,

            # Financial Health
            'debt_to_equity': 0.3,
            'current_ratio': 2.5,
            'quick_ratio': 2.0,

            # Dividends
            'dividend_yield': 0.015,
            'payout_ratio': 0.20,

            # Other
            'beta': 1.2,
            'shares_outstanding': 1e9,
            'float_shares': 0.9e9
        }

    def collect_economic_indicators(
        self,
        indicators: List[str],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, pd.Series]:
        """
        Collect economic indicators (GDP, inflation, rates, etc.).

        Args:
            indicators: List of indicator codes (e.g., ['GDP', 'CPI', 'UNRATE'])
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary mapping indicator to time series
        """
        data = {}

        for indicator in indicators:
            dates = pd.date_range(start_date, end_date, freq='M')

            if indicator == 'GDP':
                values = 20000 + np.cumsum(np.random.randn(len(dates)) * 100)
            elif indicator == 'CPI':
                values = 250 + np.cumsum(np.random.randn(len(dates)) * 2)
            elif indicator == 'UNRATE':
                values = 4.0 + np.random.randn(len(dates)) * 0.5
            elif indicator == 'FEDFUNDS':
                values = 2.5 + np.random.randn(len(dates)) * 0.3
            else:
                values = np.random.randn(len(dates))

            data[indicator] = pd.Series(values, index=dates)

        return data

    def collect_news_sentiment(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        source: DataSource = DataSource.NEWS_API
    ) -> pd.DataFrame:
        """
        Collect news articles and sentiment for a symbol.

        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date
            source: News provider

        Returns:
            DataFrame with articles and sentiment scores
        """
        # Simulate news data
        n_articles = int((end_date - start_date).days * 2)  # 2 articles per day

        dates = [
            start_date + timedelta(days=np.random.randint(0, (end_date - start_date).days))
            for _ in range(n_articles)
        ]

        articles = []
        for date in dates:
            sentiment = np.random.choice(['positive', 'neutral', 'negative'], p=[0.4, 0.4, 0.2])

            articles.append({
                'date': date,
                'title': f"Article about {symbol}",
                'source': np.random.choice(['Bloomberg', 'Reuters', 'WSJ']),
                'sentiment': sentiment,
                'sentiment_score': {
                    'positive': np.random.uniform(0.6, 1.0),
                    'neutral': np.random.uniform(0.3, 0.7),
                    'negative': np.random.uniform(0.0, 0.4)
                }[sentiment]
            })

        return pd.DataFrame(articles).sort_values('date')

    def collect_social_media_sentiment(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        platforms: List[str] = ['twitter', 'reddit']
    ) -> Dict[str, pd.DataFrame]:
        """
        Collect social media mentions and sentiment.

        Args:
            symbol: Ticker symbol or company name
            start_date: Start date
            end_date: End date
            platforms: List of social media platforms

        Returns:
            Dictionary mapping platform to mentions DataFrame
        """
        data = {}

        for platform in platforms:
            dates = pd.date_range(start_date, end_date, freq='H')

            mentions_data = []
            for date in dates:
                n_mentions = np.random.poisson(50)
                positive = np.random.binomial(n_mentions, 0.6)
                negative = np.random.binomial(n_mentions - positive, 0.3)
                neutral = n_mentions - positive - negative

                mentions_data.append({
                    'timestamp': date,
                    'total_mentions': n_mentions,
                    'positive': positive,
                    'neutral': neutral,
                    'negative': negative,
                    'sentiment_score': (positive - negative) / n_mentions if n_mentions > 0 else 0
                })

            data[platform] = pd.DataFrame(mentions_data)

        return data

    def collect_alternative_data(
        self,
        symbol: str,
        data_type: str
    ) -> Any:
        """
        Collect alternative data sources.

        Types:
        - 'hiring': Job postings, LinkedIn data
        - 'web_traffic': Website visits
        - 'app_usage': Mobile app downloads/usage
        - 'satellite': Parking lot counts, supply chain
        - 'credit_card': Consumer spending patterns

        Args:
            symbol: Company ticker
            data_type: Type of alternative data

        Returns:
            Data appropriate to type
        """
        if data_type == 'hiring':
            return {
                'total_job_postings': np.random.randint(100, 500),
                'engineering_postings': np.random.randint(50, 200),
                'posting_growth_mom': np.random.uniform(-0.1, 0.3),
                'avg_salary': np.random.randint(80000, 150000),
                'employee_reviews_score': np.random.uniform(3.5, 4.5)
            }

        elif data_type == 'web_traffic':
            return {
                'monthly_visits': np.random.randint(1e6, 100e6),
                'unique_visitors': np.random.randint(0.5e6, 50e6),
                'traffic_growth_yoy': np.random.uniform(-0.1, 0.5),
                'avg_session_duration': np.random.uniform(120, 600),
                'bounce_rate': np.random.uniform(0.2, 0.6)
            }

        elif data_type == 'satellite':
            return {
                'parking_lot_fullness': np.random.uniform(0.5, 0.95),
                'change_vs_last_month': np.random.uniform(-0.2, 0.2),
                'supply_chain_activity_score': np.random.uniform(0.6, 1.0)
            }

        else:
            return {'data_not_available': True}


class DataAggregator:
    """
    Aggregates data from multiple sources and frequencies.
    """

    def __init__(self):
        self.collector = MarketDataCollector()

    def create_comprehensive_dataset(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Create comprehensive dataset with all available data.

        Args:
            symbol: Ticker symbol
            start_date: Start date
            end_date: End date

        Returns:
            Dictionary with all collected data
        """
        print(f"Collecting comprehensive data for {symbol}...")

        dataset = {
            'symbol': symbol,
            'date_range': (start_date, end_date),
            'collection_time': datetime.now()
        }

        # Market data
        dataset['ohlcv'] = self.collector.collect_ohlcv(
            symbol, start_date, end_date
        )

        # Options
        dataset['options'] = self.collector.collect_options_chain(symbol)

        # Fundamentals
        dataset['fundamentals'] = self.collector.collect_fundamentals(symbol)

        # Economic indicators
        dataset['economic'] = self.collector.collect_economic_indicators(
            ['GDP', 'CPI', 'UNRATE', 'FEDFUNDS'],
            start_date,
            end_date
        )

        # News sentiment
        dataset['news'] = self.collector.collect_news_sentiment(
            symbol, start_date, end_date
        )

        # Social media
        dataset['social'] = self.collector.collect_social_media_sentiment(
            symbol, start_date, end_date
        )

        # Alternative data
        dataset['hiring'] = self.collector.collect_alternative_data(symbol, 'hiring')
        dataset['web_traffic'] = self.collector.collect_alternative_data(symbol, 'web_traffic')

        print(f"Data collection complete for {symbol}")

        return dataset

    def save_dataset(
        self,
        dataset: Dict[str, Any],
        filepath: str
    ):
        """
        Save dataset to disk.

        Args:
            dataset: Data to save
            filepath: Output file path
        """
        # Convert DataFrames to dict for JSON serialization
        serializable = {}

        for key, value in dataset.items():
            if isinstance(value, pd.DataFrame):
                serializable[key] = value.to_dict(orient='records')
            elif isinstance(value, pd.Series):
                serializable[key] = value.to_dict()
            elif isinstance(value, CollectedData):
                serializable[key] = {
                    'symbol': value.symbol,
                    'data_type': value.data_type,
                    'data': value.data.to_dict(orient='records'),
                    'metadata': value.metadata
                }
            else:
                serializable[key] = value

        with open(filepath, 'w') as f:
            json.dump(serializable, f, indent=2, default=str)

        print(f"Dataset saved to {filepath}")


if __name__ == "__main__":
    # Example usage
    print("=== Market Data Collection System ===\n")

    collector = MarketDataCollector()

    # Collect OHLCV data
    print("1. Collecting OHLCV data...")
    ohlcv = collector.collect_ohlcv(
        'AAPL',
        datetime(2024, 1, 1),
        datetime(2024, 12, 31)
    )
    print(f"   Collected {len(ohlcv.data)} bars")
    print(f"   Latest close: ${ohlcv.data['close'].iloc[-1]:.2f}")

    # Collect options
    print("\n2. Collecting options chain...")
    options = collector.collect_options_chain('AAPL')
    print(f"   Collected {len(options)} contracts")

    # Collect fundamentals
    print("\n3. Collecting fundamentals...")
    fundamentals = collector.collect_fundamentals('AAPL')
    print(f"   P/E Ratio: {fundamentals['pe_ratio']:.1f}")
    print(f"   Revenue Growth: {fundamentals['revenue_growth']:.1%}")

    # Collect news sentiment
    print("\n4. Collecting news sentiment...")
    news = collector.collect_news_sentiment(
        'AAPL',
        datetime(2024, 12, 1),
        datetime(2024, 12, 31)
    )
    print(f"   Collected {len(news)} articles")
    sentiment_dist = news['sentiment'].value_counts()
    print(f"   Sentiment distribution: {sentiment_dist.to_dict()}")

    # Create comprehensive dataset
    print("\n5. Creating comprehensive dataset...")
    aggregator = DataAggregator()
    dataset = aggregator.create_comprehensive_dataset(
        'NVDA',
        datetime(2024, 1, 1),
        datetime(2024, 12, 31)
    )

    print(f"\n=== Dataset Summary ===")
    print(f"Symbol: {dataset['symbol']}")
    print(f"Keys: {list(dataset.keys())}")
    print(f"OHLCV records: {len(dataset['ohlcv'].data)}")
    print(f"News articles: {len(dataset['news'])}")
