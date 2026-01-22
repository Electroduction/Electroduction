"""
Market Analysis System - Main Integration Script

Demonstrates the complete workflow integrating all modules:
1. Data collection
2. Factor analysis (seasonal, behavioral, technical, fundamental)
3. Black-Scholes option pricing
4. Multi-factor prediction
5. Trading signal generation
6. Risk management
7. Backtesting

Author: Market Analysis Team
Date: 2026-01-21
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

# Import all modules
from core.black_scholes_merton import BlackScholesMerton, HestonModel
from core.seasonal_patterns import SeasonalPatternAnalyzer
from core.behavioral_factors import BehavioralFactorAnalyzer, InvestorProfile
from models.factor_weighting import FactorWeightingEngine
from data.data_collector import MarketDataCollector, DataAggregator
from strategies.trading_strategies import MultiMarketAlgorithm, HFTStrategy, OptionsStrategy, MarketType, TradeDirection
from utils.risk_management import RiskManager
from utils.backtesting import Backtester, Order, OrderType


class MarketAnalysisSystem:
    """
    Integrated market analysis and trading system.
    """

    def __init__(self, initial_capital: float = 100000):
        """
        Initialize all system components.

        Args:
            initial_capital: Starting capital for trading
        """
        print("Initializing Market Analysis System...")

        self.initial_capital = initial_capital

        # Initialize components
        self.bs_model = BlackScholesMerton()
        self.seasonal_analyzer = SeasonalPatternAnalyzer()
        self.behavioral_analyzer = BehavioralFactorAnalyzer()
        self.factor_engine = FactorWeightingEngine('ensemble')
        self.data_collector = MarketDataCollector()
        self.trading_algo = MultiMarketAlgorithm(MarketType.STOCK)
        self.risk_manager = RiskManager(portfolio_value=initial_capital)
        self.backtester = Backtester(initial_capital=initial_capital)

        print("✓ All modules initialized successfully\n")

    def analyze_symbol(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> dict:
        """
        Perform comprehensive analysis on a symbol.

        Args:
            symbol: Ticker symbol
            start_date: Analysis start date
            end_date: Analysis end date

        Returns:
            Dictionary with complete analysis
        """
        print(f"=== Analyzing {symbol} ===\n")

        analysis = {'symbol': symbol, 'timestamp': datetime.now()}

        # 1. Collect data
        print("1. Collecting market data...")
        ohlcv_data = self.data_collector.collect_ohlcv(symbol, start_date, end_date)
        fundamentals = self.data_collector.collect_fundamentals(symbol)
        news_sentiment = self.data_collector.collect_news_sentiment(symbol, start_date, end_date)
        social_sentiment = self.data_collector.collect_social_media_sentiment(symbol, start_date, end_date)

        analysis['data_points'] = len(ohlcv_data.data)
        print(f"   ✓ Collected {len(ohlcv_data.data)} price bars")

        # 2. Seasonal pattern analysis
        print("\n2. Analyzing seasonal patterns...")
        seasonal_score = self.seasonal_analyzer.calculate_seasonal_score(datetime.now())
        seasonal_signals = self.seasonal_analyzer.generate_seasonal_signals(datetime.now(), symbol)

        analysis['seasonal'] = {
            'score': seasonal_score,
            'signals': [
                {'pattern': s.pattern_name, 'strength': s.signal_strength, 'probability': s.probability}
                for s in seasonal_signals
            ]
        }
        print(f"   ✓ Seasonal score: {seasonal_score:+.2f}")
        print(f"   ✓ Active patterns: {len(seasonal_signals)}")

        # 3. Behavioral analysis
        print("\n3. Analyzing behavioral factors...")

        # Company trust factor (e.g., for NVIDIA)
        trust_data = {
            'brand_reputation': 0.85,
            'innovation_score': 0.90,
            'management_score': 0.82,
            'customer_satisfaction': 0.80
        }
        trust_score = self.behavioral_analyzer.calculate_trust_factor(trust_data)

        # Fear & Greed index
        fg_index = self.behavioral_analyzer.calculate_fear_greed_index(
            vix=20, put_call_ratio=0.95, market_momentum=60,
            market_breadth=55, safe_haven_demand=40
        )

        analysis['behavioral'] = {
            'trust_score': trust_score,
            'fear_greed_score': fg_index['fear_greed_score'],
            'sentiment': fg_index['sentiment']
        }

        print(f"   ✓ Trust factor: {trust_score:.2f}")
        print(f"   ✓ Fear/Greed: {fg_index['fear_greed_score']:.1f} ({fg_index['sentiment']})")

        # 4. Black-Scholes option pricing
        print("\n4. Calculating option prices and drift...")

        current_price = ohlcv_data.data['close'].iloc[-1]
        historical_prices = ohlcv_data.data['close'].values

        # Calculate drift from historical data
        drift_params = self.bs_model.calculate_drift(historical_prices)

        # Price an ATM call option (6 months)
        call_price = self.bs_model.black_scholes_call(
            S=current_price,
            K=current_price,
            T=0.5,
            r=0.05,
            sigma=drift_params['annual_volatility']
        )

        greeks = self.bs_model.calculate_greeks(
            S=current_price,
            K=current_price,
            T=0.5,
            r=0.05,
            sigma=drift_params['annual_volatility']
        )

        analysis['options'] = {
            'atm_call_price': call_price,
            'implied_drift': drift_params['drift'],
            'annual_volatility': drift_params['annual_volatility'],
            'delta': greeks['delta']
        }

        print(f"   ✓ ATM Call (6mo): ${call_price:.2f}")
        print(f"   ✓ Annual volatility: {drift_params['annual_volatility']:.1%}")
        print(f"   ✓ Drift rate: {drift_params['drift']:.4f}")

        # 5. Multi-factor prediction
        print("\n5. Generating multi-factor prediction...")

        # Prepare features (simplified for demo)
        technical_features = {
            'ma_50': current_price,
            'ma_200': current_price * 0.95,
            'rsi': 55,
            'volatility': drift_params['annual_volatility']
        }

        fundamental_features = {
            'pe_ratio': fundamentals.get('pe_ratio', 20),
            'revenue_growth': fundamentals.get('revenue_growth', 0.15),
            'profit_margin': fundamentals.get('profit_margin', 0.20)
        }

        seasonal_features = {
            'seasonal_score': seasonal_score,
            'january_effect': 1 if datetime.now().month == 1 else 0
        }

        behavioral_features = {
            'trust': trust_score,
            'fear_greed': fg_index['fear_greed_score'] / 100,
            'sentiment': 0.6
        }

        macro_features = {
            'interest_rate': 0.05,
            'gdp_growth': 0.03
        }

        # For demo, we'll skip actual ML training and use a simplified prediction
        combined_score = (
            seasonal_score * 0.2 +
            (trust_score - 0.5) * 0.3 +
            (fg_index['fear_greed_score'] / 100 - 0.5) * 0.2 +
            (drift_params['annual_return']) * 0.3
        )

        analysis['prediction'] = {
            'signal_strength': combined_score,
            'direction': 'bullish' if combined_score > 0 else 'bearish',
            'confidence': min(1.0, abs(combined_score) * 2)
        }

        print(f"   ✓ Prediction: {analysis['prediction']['direction']}")
        print(f"   ✓ Signal strength: {combined_score:+.2f}")
        print(f"   ✓ Confidence: {analysis['prediction']['confidence']:.1%}")

        # 6. Trading signal generation
        print("\n6. Generating trading signal...")

        signal = self.trading_algo.generate_signal(
            symbol=symbol,
            price_data=ohlcv_data.data,
            factors={'prediction': combined_score}
        )

        if signal:
            analysis['signal'] = {
                'direction': signal.direction.value,
                'entry_price': signal.entry_price,
                'target_price': signal.target_price,
                'stop_loss': signal.stop_loss,
                'position_size': signal.position_size,
                'risk_reward': signal.risk_reward_ratio,
                'expected_return': signal.expected_return
            }

            print(f"   ✓ Signal: {signal.direction.value.upper()}")
            print(f"   ✓ Entry: ${signal.entry_price:.2f}")
            print(f"   ✓ Target: ${signal.target_price:.2f} (+{signal.expected_return:.1%})")
            print(f"   ✓ Stop: ${signal.stop_loss:.2f}")
            print(f"   ✓ R/R Ratio: {signal.risk_reward_ratio:.2f}")

            # 7. Risk assessment
            print("\n7. Assessing risk...")

            position_risk = self.risk_manager.assess_position_risk(
                symbol=symbol,
                position_size=signal.position_size,
                entry_price=signal.entry_price,
                current_price=signal.entry_price,
                stop_loss=signal.stop_loss,
                win_probability=0.55 + analysis['prediction']['confidence'] * 0.15
            )

            analysis['risk'] = {
                'risk_amount': position_risk.risk_amount,
                'risk_percentage': position_risk.risk_percentage,
                'recommendation': position_risk.recommendation,
                'expected_loss': position_risk.expected_loss
            }

            print(f"   ✓ Risk amount: ${position_risk.risk_amount:,.2f}")
            print(f"   ✓ Risk %: {position_risk.risk_percentage:.2%}")
            print(f"   ✓ Recommendation: {position_risk.recommendation.upper()}")

        else:
            analysis['signal'] = None
            analysis['risk'] = None
            print("   ✗ No trading signal generated")

        return analysis

    def run_comprehensive_demo(self):
        """
        Run a complete demonstration of the system.
        """
        print("="*70)
        print(" MARKET ANALYSIS SYSTEM - COMPREHENSIVE DEMONSTRATION")
        print("="*70)
        print()

        # Analyze a symbol
        symbol = "NVDA"
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        analysis = self.analyze_symbol(symbol, start_date, end_date)

        # Summary
        print("\n" + "="*70)
        print(" ANALYSIS SUMMARY")
        print("="*70)

        print(f"\nSymbol: {analysis['symbol']}")
        print(f"Analysis Date: {analysis['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\nSeasonal Analysis:")
        print(f"  Score: {analysis['seasonal']['score']:+.2f}")
        print(f"  Active Patterns: {len(analysis['seasonal']['signals'])}")

        print(f"\nBehavioral Analysis:")
        print(f"  Trust Score: {analysis['behavioral']['trust_score']:.2f}")
        print(f"  Market Sentiment: {analysis['behavioral']['sentiment']}")

        print(f"\nOptions Pricing:")
        print(f"  ATM Call (6mo): ${analysis['options']['atm_call_price']:.2f}")
        print(f"  Volatility: {analysis['options']['annual_volatility']:.1%}")

        print(f"\nPrediction:")
        print(f"  Direction: {analysis['prediction']['direction'].upper()}")
        print(f"  Confidence: {analysis['prediction']['confidence']:.1%}")

        if analysis['signal']:
            print(f"\nTrading Signal:")
            print(f"  Action: {analysis['signal']['direction'].upper()}")
            print(f"  Entry: ${analysis['signal']['entry_price']:.2f}")
            print(f"  Target: ${analysis['signal']['target_price']:.2f}")
            print(f"  Stop: ${analysis['signal']['stop_loss']:.2f}")

            print(f"\nRisk Assessment:")
            print(f"  Risk Amount: ${analysis['risk']['risk_amount']:,.2f}")
            print(f"  Portfolio Risk: {analysis['risk']['risk_percentage']:.2%}")
            print(f"  Recommendation: {analysis['risk']['recommendation'].upper()}")

        print("\n" + "="*70)
        print(" END OF ANALYSIS")
        print("="*70)


def main():
    """Main entry point"""
    # Create system instance
    system = MarketAnalysisSystem(initial_capital=100000)

    # Run comprehensive demonstration
    system.run_comprehensive_demo()

    print("\n\n" + "="*70)
    print(" SYSTEM COMPONENTS AVAILABLE:")
    print("="*70)
    print("""
    1. Black-Scholes-Merton Option Pricing
    2. Seasonal Pattern Analysis (January Effect, MLK Day, etc.)
    3. Behavioral Finance Factors (Fear/Greed, Trust, Sentiment)
    4. Multi-Factor ML Weighting
    5. Data Collection Apparatus
    6. Multi-Market Trading Algorithms (Stocks, Futures, Options)
    7. HFT Strategies
    8. Pattern Recognition
    9. Risk Management & Position Sizing
    10. Backtesting Engine
    """)
    print("="*70)


if __name__ == "__main__":
    main()
