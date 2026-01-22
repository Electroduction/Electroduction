"""
Market Pattern Database

Comprehensive database of documented market patterns, anomalies, and effects
from academic research and practical trading experience.

Each pattern includes:
- Description and mechanism
- Historical performance statistics
- Applicability conditions
- Detection algorithms
- Risk factors
"""

import json
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import pickle


@dataclass
class MarketPattern:
    """Represents a market pattern/anomaly"""
    pattern_id: str
    name: str
    category: str  # 'seasonal', 'technical', 'fundamental', 'behavioral', 'macro'
    description: str

    # Performance statistics
    avg_return: float  # Average return when pattern active
    win_rate: float  # Historical win rate
    sharpe_ratio: float
    avg_duration_days: int

    # Applicability
    applicable_markets: List[str]  # ['stocks', 'futures', 'forex', 'crypto']
    applicable_timeframes: List[str]  # ['intraday', 'daily', 'weekly', 'monthly']

    # Pattern specifics
    detection_function: str  # Name of detection function
    required_data: List[str]  # ['price', 'volume', 'fundamentals', etc.]

    # Research backing
    research_papers: List[str]
    first_documented: int  # Year
    still_works: bool  # Does it still work or is it arbitraged away?

    # Risk factors
    max_drawdown: float
    volatility: float
    market_cap_bias: Optional[str]  # 'small', 'large', None

    # Additional metadata
    strength_factors: List[str]  # What makes pattern stronger
    failure_signs: List[str]  # Signs pattern might fail
    related_patterns: List[str]  # Related pattern IDs


class PatternDatabase:
    """
    Database manager for market patterns.
    """

    def __init__(self, db_path: str = "market_patterns.db"):
        """
        Initialize pattern database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = None
        self._initialize_database()
        self._load_default_patterns()

    def _initialize_database(self):
        """Create database schema"""
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()

        # Create patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                avg_return REAL,
                win_rate REAL,
                sharpe_ratio REAL,
                avg_duration_days INTEGER,
                applicable_markets TEXT,
                applicable_timeframes TEXT,
                detection_function TEXT,
                required_data TEXT,
                research_papers TEXT,
                first_documented INTEGER,
                still_works INTEGER,
                max_drawdown REAL,
                volatility REAL,
                market_cap_bias TEXT,
                strength_factors TEXT,
                failure_signs TEXT,
                related_patterns TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create pattern performance history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT NOT NULL,
                date DATE NOT NULL,
                symbol TEXT,
                signal_strength REAL,
                actual_return REAL,
                holding_period INTEGER,
                success INTEGER,
                FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id)
            )
        """)

        # Create pattern detection cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pattern_detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT NOT NULL,
                symbol TEXT NOT NULL,
                detection_date DATE NOT NULL,
                signal_strength REAL,
                metadata TEXT,
                FOREIGN KEY (pattern_id) REFERENCES patterns(pattern_id)
            )
        """)

        self.conn.commit()

    def _load_default_patterns(self):
        """Load comprehensive set of documented market patterns"""

        default_patterns = [
            # ===== SEASONAL PATTERNS =====
            MarketPattern(
                pattern_id="january_effect",
                name="January Effect",
                category="seasonal",
                description="Small-cap stocks outperform large-caps in January due to tax-loss selling reversal and window dressing",
                avg_return=0.055,
                win_rate=0.68,
                sharpe_ratio=1.2,
                avg_duration_days=31,
                applicable_markets=['stocks'],
                applicable_timeframes=['monthly'],
                detection_function="detect_january_effect",
                required_data=['price', 'market_cap'],
                research_papers=['Rozeff & Kinney (1976)', 'Keim (1983)'],
                first_documented=1976,
                still_works=True,
                max_drawdown=-0.08,
                volatility=0.15,
                market_cap_bias='small',
                strength_factors=['Strong prior year losses', 'High retail participation', 'December tax-loss selling'],
                failure_signs=['Strong December rally', 'Low volatility', 'Weak prior year performance'],
                related_patterns=['turn_of_year_effect', 'small_cap_premium']
            ),

            MarketPattern(
                pattern_id="sell_in_may",
                name="Sell in May and Go Away",
                category="seasonal",
                description="Stock market underperforms May-October vs November-April period",
                avg_return=-0.02,
                win_rate=0.58,
                sharpe_ratio=0.4,
                avg_duration_days=184,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['monthly'],
                detection_function="detect_sell_in_may",
                required_data=['price'],
                research_papers=['Bouman & Jacobsen (2002)'],
                first_documented=2002,
                still_works=True,
                max_drawdown=-0.12,
                volatility=0.14,
                market_cap_bias=None,
                strength_factors=['European markets stronger effect', 'Historical volatility in summer'],
                failure_signs=['Strong economic growth', 'Bull market momentum'],
                related_patterns=['summer_doldrums', 'santa_claus_rally']
            ),

            MarketPattern(
                pattern_id="santa_claus_rally",
                name="Santa Claus Rally",
                category="seasonal",
                description="Market tends to rally in the last 5 trading days of year and first 2 of new year",
                avg_return=0.018,
                win_rate=0.74,
                sharpe_ratio=1.5,
                avg_duration_days=7,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['daily'],
                detection_function="detect_santa_rally",
                required_data=['price'],
                research_papers=['Hirsch Stock Trader\'s Almanac'],
                first_documented=1972,
                still_works=True,
                max_drawdown=-0.03,
                volatility=0.08,
                market_cap_bias=None,
                strength_factors=['Low trading volume', 'Year-end bonuses', 'Optimism'],
                failure_signs=['Major news events', 'Economic crisis'],
                related_patterns=['january_effect', 'turn_of_year_effect']
            ),

            MarketPattern(
                pattern_id="september_effect",
                name="September Effect",
                category="seasonal",
                description="September historically worst month for stocks, averaging negative returns",
                avg_return=-0.01,
                win_rate=0.45,
                sharpe_ratio=-0.2,
                avg_duration_days=30,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['monthly'],
                detection_function="detect_september_weakness",
                required_data=['price'],
                research_papers=['Various market studies'],
                first_documented=1950,
                still_works=True,
                max_drawdown=-0.15,
                volatility=0.16,
                market_cap_bias=None,
                strength_factors=['Post-summer return', 'Mutual fund tax considerations', 'Psychological'],
                failure_signs=['Strong summer momentum', 'Fed support'],
                related_patterns=['sell_in_may', 'october_effect']
            ),

            MarketPattern(
                pattern_id="monday_effect",
                name="Monday Effect / Weekend Effect",
                category="seasonal",
                description="Stock returns tend to be lower on Mondays, especially Monday mornings",
                avg_return=-0.0015,
                win_rate=0.48,
                sharpe_ratio=-0.3,
                avg_duration_days=1,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['daily'],
                detection_function="detect_monday_effect",
                required_data=['price'],
                research_papers=['French (1980)', 'Lakonishok & Levi (1982)'],
                first_documented=1980,
                still_works=False,  # Largely arbitraged away
                max_drawdown=-0.02,
                volatility=0.12,
                market_cap_bias='small',
                strength_factors=['Bad news over weekend', 'Settlement timing'],
                failure_signs=['Positive weekend news', 'Global market rallies'],
                related_patterns=['friday_effect', 'intraday_patterns']
            ),

            MarketPattern(
                pattern_id="fomc_announcement",
                name="FOMC Announcement Day Pattern",
                category="seasonal",
                description="Markets tend to drift higher in the 24 hours before Fed announcements",
                avg_return=0.0049,
                win_rate=0.65,
                sharpe_ratio=0.9,
                avg_duration_days=1,
                applicable_markets=['stocks', 'indexes', 'bonds'],
                applicable_timeframes=['intraday', 'daily'],
                detection_function="detect_fomc_drift",
                required_data=['price', 'fed_calendar'],
                research_papers=['Lucca & Moench (2015)'],
                first_documented=2015,
                still_works=True,
                max_drawdown=-0.01,
                volatility=0.09,
                market_cap_bias=None,
                strength_factors=['Pre-announcement positioning', 'Dealer hedging'],
                failure_signs=['Crisis periods', 'Unexpected news'],
                related_patterns=['earnings_announcement_drift', 'event_premium']
            ),

            # ===== TECHNICAL PATTERNS =====

            MarketPattern(
                pattern_id="momentum",
                name="Price Momentum",
                category="technical",
                description="Stocks that outperformed recently tend to continue outperforming (3-12 month horizon)",
                avg_return=0.09,
                win_rate=0.58,
                sharpe_ratio=0.7,
                avg_duration_days=90,
                applicable_markets=['stocks', 'futures', 'crypto'],
                applicable_timeframes=['daily', 'weekly'],
                detection_function="detect_momentum",
                required_data=['price'],
                research_papers=['Jegadeesh & Titman (1993)', 'Carhart (1997)'],
                first_documented=1993,
                still_works=True,
                max_drawdown=-0.25,
                volatility=0.18,
                market_cap_bias=None,
                strength_factors=['Strong trend', 'Volume confirmation', 'Sector momentum'],
                failure_signs=['Overbought conditions', 'Reversal patterns', 'Negative news'],
                related_patterns=['trend_following', 'relative_strength']
            ),

            MarketPattern(
                pattern_id="mean_reversion",
                name="Short-Term Mean Reversion",
                category="technical",
                description="Stocks that fell sharply in prior week tend to bounce back",
                avg_return=0.012,
                win_rate=0.54,
                sharpe_ratio=0.6,
                avg_duration_days=5,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['daily'],
                detection_function="detect_mean_reversion",
                required_data=['price', 'volume'],
                research_papers=['Lehmann (1990)', 'Jegadeesh (1990)'],
                first_documented=1990,
                still_works=True,
                max_drawdown=-0.08,
                volatility=0.14,
                market_cap_bias='small',
                strength_factors=['Oversold conditions', 'High volume on decline', 'No fundamental news'],
                failure_signs=['Continued selling pressure', 'Fundamental deterioration'],
                related_patterns=['rsi_oversold', 'bollinger_bounce']
            ),

            MarketPattern(
                pattern_id="52_week_high",
                name="52-Week High Effect",
                category="technical",
                description="Stocks making new 52-week highs tend to continue rising (anchoring bias)",
                avg_return=0.045,
                win_rate=0.59,
                sharpe_ratio=0.8,
                avg_duration_days=60,
                applicable_markets=['stocks'],
                applicable_timeframes=['daily', 'weekly'],
                detection_function="detect_52_week_high",
                required_data=['price'],
                research_papers=['George & Hwang (2004)'],
                first_documented=2004,
                still_works=True,
                max_drawdown=-0.18,
                volatility=0.16,
                market_cap_bias=None,
                strength_factors=['Volume surge', 'Fundamental support', 'Industry momentum'],
                failure_signs=['Exhaustion gaps', 'Negative divergences'],
                related_patterns=['momentum', 'breakout_pattern']
            ),

            MarketPattern(
                pattern_id="gap_fade",
                name="Gap Fade",
                category="technical",
                description="Large overnight gaps tend to partially reverse during the trading day",
                avg_return=0.008,
                win_rate=0.56,
                sharpe_ratio=0.5,
                avg_duration_days=1,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['intraday'],
                detection_function="detect_gap_fade",
                required_data=['price', 'volume'],
                research_papers=['Market microstructure research'],
                first_documented=2000,
                still_works=True,
                max_drawdown=-0.04,
                volatility=0.11,
                market_cap_bias=None,
                strength_factors=['No fundamental news', 'Large gap size', 'Early reversal'],
                failure_signs=['News-driven gaps', 'High volume continuation'],
                related_patterns=['opening_range_breakout', 'intraday_reversal']
            ),

            # ===== FUNDAMENTAL PATTERNS =====

            MarketPattern(
                pattern_id="value_premium",
                name="Value Premium",
                category="fundamental",
                description="Stocks with low P/E, P/B ratios outperform growth stocks over long periods",
                avg_return=0.038,
                win_rate=0.57,
                sharpe_ratio=0.65,
                avg_duration_days=365,
                applicable_markets=['stocks'],
                applicable_timeframes=['monthly', 'quarterly'],
                detection_function="detect_value_premium",
                required_data=['price', 'fundamentals'],
                research_papers=['Fama & French (1992)', 'Graham & Dodd (1934)'],
                first_documented=1934,
                still_works=True,
                max_drawdown=-0.30,
                volatility=0.15,
                market_cap_bias=None,
                strength_factors=['Economic recovery', 'Rising rates', 'Market rotation'],
                failure_signs=['Growth dominance', 'Tech booms'],
                related_patterns=['quality_factor', 'profitability_premium']
            ),

            MarketPattern(
                pattern_id="earnings_surprise",
                name="Post-Earnings Announcement Drift",
                category="fundamental",
                description="Stocks with positive earnings surprises continue drifting up for weeks",
                avg_return=0.024,
                win_rate=0.62,
                sharpe_ratio=0.9,
                avg_duration_days=45,
                applicable_markets=['stocks'],
                applicable_timeframes=['daily'],
                detection_function="detect_earnings_drift",
                required_data=['price', 'earnings', 'estimates'],
                research_papers=['Ball & Brown (1968)', 'Bernard & Thomas (1989)'],
                first_documented=1968,
                still_works=True,
                max_drawdown=-0.10,
                volatility=0.13,
                market_cap_bias='small',
                strength_factors=['Large surprise', 'Guidance raise', 'Analyst upgrades'],
                failure_signs=['Sector weakness', 'Macro headwinds'],
                related_patterns=['analyst_revision', 'guidance_premium']
            ),

            MarketPattern(
                pattern_id="insider_buying",
                name="Insider Buying Signal",
                category="fundamental",
                description="Significant insider purchases predict positive returns",
                avg_return=0.031,
                win_rate=0.61,
                sharpe_ratio=0.75,
                avg_duration_days=120,
                applicable_markets=['stocks'],
                applicable_timeframes=['weekly', 'monthly'],
                detection_function="detect_insider_buying",
                required_data=['insider_trades', 'price'],
                research_papers=['Seyhun (1986)', 'Lakonishok & Lee (2001)'],
                first_documented=1986,
                still_works=True,
                max_drawdown=-0.15,
                volatility=0.14,
                market_cap_bias='small',
                strength_factors=['Multiple insiders', 'CEO purchases', 'Clustered timing'],
                failure_signs=['Routine selling', 'Sector decline'],
                related_patterns=['buyback_announcement', 'institutional_buying']
            ),

            MarketPattern(
                pattern_id="dividend_initiation",
                name="Dividend Initiation Effect",
                category="fundamental",
                description="Stocks initiating dividends show positive abnormal returns",
                avg_return=0.033,
                win_rate=0.64,
                sharpe_ratio=0.85,
                avg_duration_days=90,
                applicable_markets=['stocks'],
                applicable_timeframes=['daily', 'weekly'],
                detection_function="detect_dividend_initiation",
                required_data=['dividends', 'price'],
                research_papers=['Asquith & Mullins (1983)'],
                first_documented=1983,
                still_works=True,
                max_drawdown=-0.08,
                volatility=0.12,
                market_cap_bias=None,
                strength_factors=['Mature company', 'Strong cash flow', 'Commitment signal'],
                failure_signs=['Forced by pressure', 'Weak financials'],
                related_patterns=['dividend_increase', 'yield_premium']
            ),

            # ===== BEHAVIORAL PATTERNS =====

            MarketPattern(
                pattern_id="overreaction",
                name="Loser Portfolio Overreaction",
                category="behavioral",
                description="Extreme losers over 3-5 years tend to become winners (overreaction reversal)",
                avg_return=0.248,
                win_rate=0.59,
                sharpe_ratio=0.68,
                avg_duration_days=1095,
                applicable_markets=['stocks'],
                applicable_timeframes=['monthly'],
                detection_function="detect_overreaction",
                required_data=['price'],
                research_papers=['De Bondt & Thaler (1985)'],
                first_documented=1985,
                still_works=True,
                max_drawdown=-0.35,
                volatility=0.22,
                market_cap_bias='small',
                strength_factors=['No bankruptcy risk', 'Secular decline ending', 'Turnaround catalyst'],
                failure_signs=['Structural decline', 'Continued losses'],
                related_patterns=['contrarian_strategy', 'distressed_value']
            ),

            MarketPattern(
                pattern_id="lottery_stock",
                name="Lottery Stock Underperformance",
                category="behavioral",
                description="Stocks with lottery-like characteristics (low price, high skew) underperform",
                avg_return=-0.06,
                win_rate=0.35,
                sharpe_ratio=-0.4,
                avg_duration_days=180,
                applicable_markets=['stocks'],
                applicable_timeframes=['monthly'],
                detection_function="detect_lottery_stocks",
                required_data=['price', 'returns', 'volume'],
                research_papers=['Kumar (2009)', 'Bali et al (2011)'],
                first_documented=2009,
                still_works=True,
                max_drawdown=-0.50,
                volatility=0.45,
                market_cap_bias='small',
                strength_factors=['High retail interest', 'Penny stock status', 'Extreme volatility'],
                failure_signs=['Fundamental improvement', 'Institutional buying'],
                related_patterns=['high_volatility_low_return', 'retail_favorite']
            ),

            MarketPattern(
                pattern_id="attention_grabbing",
                name="Attention-Grabbing Stocks",
                category="behavioral",
                description="Stocks with abnormal news/volume get temporary boost then revert",
                avg_return=0.015,  # Short-term, then reversal
                win_rate=0.52,
                sharpe_ratio=0.3,
                avg_duration_days=3,
                applicable_markets=['stocks'],
                applicable_timeframes=['daily'],
                detection_function="detect_attention_spike",
                required_data=['price', 'volume', 'news'],
                research_papers=['Barber & Odean (2008)'],
                first_documented=2008,
                still_works=True,
                max_drawdown=-0.12,
                volatility=0.20,
                market_cap_bias='small',
                strength_factors=['Media coverage', 'Social media buzz', 'Unusual volume'],
                failure_signs=['Fundamental news', 'Sustainable catalyst'],
                related_patterns=['meme_stock', 'retail_buying_pressure']
            ),

            MarketPattern(
                pattern_id="anchoring_effect",
                name="52-Week Low Anchoring",
                category="behavioral",
                description="Stocks near 52-week lows face selling pressure from anchored investors",
                avg_return=-0.018,
                win_rate=0.46,
                sharpe_ratio=-0.3,
                avg_duration_days=30,
                applicable_markets=['stocks'],
                applicable_timeframes=['daily'],
                detection_function="detect_52_week_low",
                required_data=['price'],
                research_papers=['George & Hwang (2004)'],
                first_documented=2004,
                still_works=True,
                max_drawdown=-0.15,
                volatility=0.18,
                market_cap_bias=None,
                strength_factors=['Psychological resistance', 'Stop-loss clusters', 'Retail selling'],
                failure_signs=['Fundamental support', 'Institutional buying'],
                related_patterns=['psychological_levels', 'round_number_effect']
            ),

            # ===== MACRO PATTERNS =====

            MarketPattern(
                pattern_id="fed_model",
                name="Fed Model / Earnings Yield Spread",
                category="macro",
                description="Stocks attractive when earnings yield exceeds 10-year Treasury yield",
                avg_return=0.042,
                win_rate=0.60,
                sharpe_ratio=0.7,
                avg_duration_days=180,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['monthly'],
                detection_function="detect_fed_model_signal",
                required_data=['price', 'earnings', 'interest_rates'],
                research_papers=['Lander et al (1997)'],
                first_documented=1997,
                still_works=True,
                max_drawdown=-0.20,
                volatility=0.15,
                market_cap_bias=None,
                strength_factors=['Wide spread', 'Falling rates', 'Stable earnings'],
                failure_signs=['Rising rates', 'Earnings decline'],
                related_patterns=['equity_risk_premium', 'yield_curve']
            ),

            MarketPattern(
                pattern_id="yield_curve_inversion",
                name="Yield Curve Inversion",
                category="macro",
                description="Inverted yield curve (2y > 10y) predicts recession and bear market",
                avg_return=-0.15,
                win_rate=0.22,
                sharpe_ratio=-0.5,
                avg_duration_days=365,
                applicable_markets=['stocks', 'bonds'],
                applicable_timeframes=['monthly'],
                detection_function="detect_yield_curve_inversion",
                required_data=['interest_rates'],
                research_papers=['Estrella & Mishkin (1998)'],
                first_documented=1998,
                still_works=True,
                max_drawdown=-0.40,
                volatility=0.22,
                market_cap_bias=None,
                strength_factors=['Deep inversion', 'Sustained period', 'Tight Fed policy'],
                failure_signs=['Fed pivot', 'Brief inversion'],
                related_patterns=['credit_spread_widening', 'recession_indicators']
            ),

            MarketPattern(
                pattern_id="dollar_strength",
                name="Strong Dollar / Weak Emerging Markets",
                category="macro",
                description="Rising dollar correlates with EM underperformance and commodity weakness",
                avg_return=-0.08,
                win_rate=0.38,
                sharpe_ratio=-0.4,
                avg_duration_days=120,
                applicable_markets=['emerging_markets', 'commodities'],
                applicable_timeframes=['weekly', 'monthly'],
                detection_function="detect_dollar_strength",
                required_data=['currency', 'price'],
                research_papers=['IMF studies'],
                first_documented=1980,
                still_works=True,
                max_drawdown=-0.30,
                volatility=0.18,
                market_cap_bias=None,
                strength_factors=['Fed tightening', 'Risk-off sentiment', 'Capital flight'],
                failure_signs=['Fed pause', 'EM reforms'],
                related_patterns=['currency_carry', 'commodity_cycle']
            ),

            # ===== SENTIMENT PATTERNS =====

            MarketPattern(
                pattern_id="vix_spike",
                name="VIX Spike Reversal",
                category="behavioral",
                description="Extreme VIX spikes (>30) often mark short-term bottoms",
                avg_return=0.065,
                win_rate=0.67,
                sharpe_ratio=1.1,
                avg_duration_days=30,
                applicable_markets=['stocks', 'indexes'],
                applicable_timeframes=['daily'],
                detection_function="detect_vix_spike",
                required_data=['vix', 'price'],
                research_papers=['Whaley (2000)'],
                first_documented=2000,
                still_works=True,
                max_drawdown=-0.10,
                volatility=0.16,
                market_cap_bias=None,
                strength_factors=['VIX > 40', 'Panic selling', 'Oversold conditions'],
                failure_signs=['Systemic crisis', 'Fundamental deterioration'],
                related_patterns=['put_call_extreme', 'sentiment_extreme']
            ),

            MarketPattern(
                pattern_id="short_squeeze",
                name="Short Squeeze Pattern",
                category="behavioral",
                description="High short interest stocks rally sharply on positive news",
                avg_return=0.12,
                win_rate=0.58,
                sharpe_ratio=0.7,
                avg_duration_days=7,
                applicable_markets=['stocks'],
                applicable_timeframes=['daily'],
                detection_function="detect_short_squeeze",
                required_data=['price', 'short_interest', 'volume'],
                research_papers=['Dechow et al (2001)'],
                first_documented=2001,
                still_works=True,
                max_drawdown=-0.15,
                volatility=0.35,
                market_cap_bias='small',
                strength_factors=['High short interest', 'Positive catalyst', 'Illiquidity'],
                failure_signs=['No catalyst', 'Fundamental deterioration'],
                related_patterns=['gamma_squeeze', 'meme_stock_surge']
            ),
        ]

        # Add all patterns to database
        for pattern in default_patterns:
            self.add_pattern(pattern)

    def add_pattern(self, pattern: MarketPattern):
        """Add or update a pattern in database"""
        cursor = self.conn.cursor()

        # Convert lists to JSON strings
        data = {
            'pattern_id': pattern.pattern_id,
            'name': pattern.name,
            'category': pattern.category,
            'description': pattern.description,
            'avg_return': pattern.avg_return,
            'win_rate': pattern.win_rate,
            'sharpe_ratio': pattern.sharpe_ratio,
            'avg_duration_days': pattern.avg_duration_days,
            'applicable_markets': json.dumps(pattern.applicable_markets),
            'applicable_timeframes': json.dumps(pattern.applicable_timeframes),
            'detection_function': pattern.detection_function,
            'required_data': json.dumps(pattern.required_data),
            'research_papers': json.dumps(pattern.research_papers),
            'first_documented': pattern.first_documented,
            'still_works': 1 if pattern.still_works else 0,
            'max_drawdown': pattern.max_drawdown,
            'volatility': pattern.volatility,
            'market_cap_bias': pattern.market_cap_bias,
            'strength_factors': json.dumps(pattern.strength_factors),
            'failure_signs': json.dumps(pattern.failure_signs),
            'related_patterns': json.dumps(pattern.related_patterns)
        }

        cursor.execute("""
            INSERT OR REPLACE INTO patterns VALUES (
                :pattern_id, :name, :category, :description, :avg_return, :win_rate,
                :sharpe_ratio, :avg_duration_days, :applicable_markets, :applicable_timeframes,
                :detection_function, :required_data, :research_papers, :first_documented,
                :still_works, :max_drawdown, :volatility, :market_cap_bias,
                :strength_factors, :failure_signs, :related_patterns,
                CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
            )
        """, data)

        self.conn.commit()

    def get_pattern(self, pattern_id: str) -> Optional[MarketPattern]:
        """Retrieve a pattern by ID"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM patterns WHERE pattern_id = ?", (pattern_id,))
        row = cursor.fetchone()

        if not row:
            return None

        # Parse JSON fields
        cols = [desc[0] for desc in cursor.description]
        data = dict(zip(cols, row))

        # Convert JSON strings back to lists
        data['applicable_markets'] = json.loads(data['applicable_markets'])
        data['applicable_timeframes'] = json.loads(data['applicable_timeframes'])
        data['required_data'] = json.loads(data['required_data'])
        data['research_papers'] = json.loads(data['research_papers'])
        data['strength_factors'] = json.loads(data['strength_factors'])
        data['failure_signs'] = json.loads(data['failure_signs'])
        data['related_patterns'] = json.loads(data['related_patterns'])
        data['still_works'] = bool(data['still_works'])

        # Remove timestamp fields
        data.pop('created_at', None)
        data.pop('updated_at', None)

        return MarketPattern(**data)

    def search_patterns(
        self,
        category: Optional[str] = None,
        market: Optional[str] = None,
        min_win_rate: float = 0.0,
        min_sharpe: float = 0.0,
        still_works_only: bool = True
    ) -> List[MarketPattern]:
        """
        Search for patterns matching criteria.

        Args:
            category: Pattern category to filter
            market: Market type (e.g., 'stocks')
            min_win_rate: Minimum historical win rate
            min_sharpe: Minimum Sharpe ratio
            still_works_only: Only return patterns that still work

        Returns:
            List of matching patterns
        """
        cursor = self.conn.cursor()

        query = "SELECT * FROM patterns WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category)

        if min_win_rate > 0:
            query += " AND win_rate >= ?"
            params.append(min_win_rate)

        if min_sharpe > 0:
            query += " AND sharpe_ratio >= ?"
            params.append(min_sharpe)

        if still_works_only:
            query += " AND still_works = 1"

        query += " ORDER BY sharpe_ratio DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        patterns = []
        for row in rows:
            cols = [desc[0] for desc in cursor.description]
            data = dict(zip(cols, row))

            # Parse JSON fields
            data['applicable_markets'] = json.loads(data['applicable_markets'])
            data['applicable_timeframes'] = json.loads(data['applicable_timeframes'])
            data['required_data'] = json.loads(data['required_data'])
            data['research_papers'] = json.loads(data['research_papers'])
            data['strength_factors'] = json.loads(data['strength_factors'])
            data['failure_signs'] = json.loads(data['failure_signs'])
            data['related_patterns'] = json.loads(data['related_patterns'])
            data['still_works'] = bool(data['still_works'])

            data.pop('created_at', None)
            data.pop('updated_at', None)

            # Filter by market if specified
            if market and market in data['applicable_markets']:
                patterns.append(MarketPattern(**data))
            elif not market:
                patterns.append(MarketPattern(**data))

        return patterns

    def get_all_categories(self) -> List[str]:
        """Get list of all pattern categories"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM patterns")
        return [row[0] for row in cursor.fetchall()]

    def get_pattern_count(self) -> Dict[str, int]:
        """Get count of patterns by category"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT category, COUNT(*)
            FROM patterns
            GROUP BY category
            ORDER BY COUNT(*) DESC
        """)
        return {row[0]: row[1] for row in cursor.fetchall()}

    def record_performance(
        self,
        pattern_id: str,
        date: datetime,
        symbol: str,
        signal_strength: float,
        actual_return: float,
        holding_period: int
    ):
        """Record actual performance of a pattern detection"""
        cursor = self.conn.cursor()

        success = 1 if actual_return > 0 else 0

        cursor.execute("""
            INSERT INTO pattern_performance
            (pattern_id, date, symbol, signal_strength, actual_return, holding_period, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (pattern_id, date, symbol, signal_strength, actual_return, holding_period, success))

        self.conn.commit()

    def get_pattern_performance(
        self,
        pattern_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get historical performance of a pattern"""
        query = "SELECT * FROM pattern_performance WHERE pattern_id = ?"
        params = [pattern_id]

        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)

        return pd.read_sql_query(query, self.conn, params=params)

    def export_patterns(self, filepath: str):
        """Export all patterns to JSON file"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM patterns")

        patterns_data = []
        for row in cursor.fetchall():
            cols = [desc[0] for desc in cursor.description]
            data = dict(zip(cols, row))

            # Parse JSON strings
            data['applicable_markets'] = json.loads(data['applicable_markets'])
            data['applicable_timeframes'] = json.loads(data['applicable_timeframes'])
            data['required_data'] = json.loads(data['required_data'])
            data['research_papers'] = json.loads(data['research_papers'])
            data['strength_factors'] = json.loads(data['strength_factors'])
            data['failure_signs'] = json.loads(data['failure_signs'])
            data['related_patterns'] = json.loads(data['related_patterns'])

            patterns_data.append(data)

        with open(filepath, 'w') as f:
            json.dump(patterns_data, f, indent=2, default=str)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    # Example usage
    print("=== Market Pattern Database ===\n")

    # Initialize database
    db = PatternDatabase("market_patterns.db")

    # Get pattern statistics
    print("Pattern Statistics:")
    counts = db.get_pattern_count()
    for category, count in counts.items():
        print(f"  {category}: {count} patterns")

    # Search for high-quality seasonal patterns
    print("\n=== Top Seasonal Patterns ===")
    seasonal = db.search_patterns(
        category='seasonal',
        min_win_rate=0.60,
        min_sharpe=0.5,
        still_works_only=True
    )

    for pattern in seasonal[:5]:
        print(f"\n{pattern.name}")
        print(f"  Win Rate: {pattern.win_rate:.1%}")
        print(f"  Avg Return: {pattern.avg_return:+.1%}")
        print(f"  Sharpe: {pattern.sharpe_ratio:.2f}")
        print(f"  Research: {', '.join(pattern.research_papers[:2])}")

    # Search for technical patterns
    print("\n=== Top Technical Patterns ===")
    technical = db.search_patterns(
        category='technical',
        market='stocks',
        min_sharpe=0.6
    )

    for pattern in technical[:3]:
        print(f"\n{pattern.name}")
        print(f"  Description: {pattern.description}")
        print(f"  Sharpe: {pattern.sharpe_ratio:.2f}")
        print(f"  Duration: {pattern.avg_duration_days} days")

    # Get specific pattern details
    print("\n=== Pattern Details: January Effect ===")
    jan_effect = db.get_pattern('january_effect')
    if jan_effect:
        print(f"Name: {jan_effect.name}")
        print(f"Category: {jan_effect.category}")
        print(f"Win Rate: {jan_effect.win_rate:.1%}")
        print(f"Avg Return: {jan_effect.avg_return:+.1%}")
        print(f"Strength Factors:")
        for factor in jan_effect.strength_factors:
            print(f"  - {factor}")
        print(f"Failure Signs:")
        for sign in jan_effect.failure_signs:
            print(f"  - {sign}")

    # Export patterns
    db.export_patterns("market_patterns_export.json")
    print("\n✓ Patterns exported to market_patterns_export.json")

    db.close()
