"""
Comprehensive Market Analysis Demo

Shows full system integration with pattern database for price prediction.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add to path
sys.path.append(str(Path(__file__).parent))

from data.pattern_database import PatternDatabase
from core.pattern_detector import PatternDetector
from core.black_scholes_merton import BlackScholesMerton
from core.seasonal_patterns import SeasonalPatternAnalyzer
from core.behavioral_factors import BehavioralFactorAnalyzer


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_section(text):
    """Print formatted section"""
    print(f"\n{text}")
    print("-" * 80)


def run_comprehensive_demo():
    """Run full demonstration of integrated system"""

    print_header("MARKET ANALYSIS SYSTEM - COMPREHENSIVE DEMO")
    print("             Pattern Database Enhanced Prediction Engine")
    print()

    # ===== 1. Pattern Database Overview =====
    print_section("📊 PATTERN DATABASE OVERVIEW")

    db = PatternDatabase("market_patterns.db")

    # Show statistics
    counts = db.get_pattern_count()
    total_patterns = sum(counts.values())

    print(f"\n✓ Loaded {total_patterns} market patterns from research")
    print(f"\nPatterns by Category:")
    for category, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * (count * 2)
        print(f"  {category:15s} [{count:2d}] {bar}")

    # ===== 2. Sample Analysis =====
    print_section("📈 ANALYZING: NVIDIA (NVDA)")

    # Generate sample price data
    dates = pd.date_range('2020-01-01', '2025-01-15', freq='D')
    np.random.seed(42)

    # Simulate NVDA's strong performance
    trend = np.linspace(0, 3, len(dates))  # Strong uptrend
    noise = np.random.randn(len(dates)) * 0.05

    price_data = pd.DataFrame({
        'open': 100 * np.exp(trend + noise),
        'high': 102 * np.exp(trend + noise),
        'low': 98 * np.exp(trend + noise),
        'close': 100 * np.exp(trend + noise),
        'volume': np.random.randint(10e6, 100e6, len(dates))
    }, index=dates)

    current_price = price_data['close'].iloc[-1]
    print(f"\nCurrent Price: ${current_price:.2f}")
    print(f"52-Week Range: ${price_data['low'].iloc[-252:].min():.2f} - ${price_data['high'].iloc[-252:].max():.2f}")

    # Calculate key metrics
    ytd_return = (price_data['close'].iloc[-1] / price_data['close'].iloc[-365]) - 1
    vol = price_data['close'].pct_change().std() * np.sqrt(252)

    print(f"YTD Return: {ytd_return:+.1%}")
    print(f"Volatility: {vol:.1%}")

    # ===== 3. Pattern Detection =====
    print_section("🔍 PATTERN DETECTION ENGINE")

    detector = PatternDetector("market_patterns.db")

    # Market data
    additional_data = {
        'market_cap': 3000e9,  # $3T - Large cap
        'pe_ratio': 65,        # High P/E (growth stock)
        'price_to_book': 45,
        'earnings_yield': 0.015,
        'revenue_growth': 0.80,  # 80% growth!
        'profit_margin': 0.55,
        'vix': 16,  # Low volatility
        'short_interest_pct': 0.02,
        'insider_buys_30d': 0,
        'insider_sells_30d': 3,
        'treasury_2y_yield': 0.043,
        'treasury_10y_yield': 0.048,
        'brand_reputation': 0.95,
        'innovation_score': 0.98,
        'trust_factor': 0.92,
        'hiring_growth': 0.25
    }

    current_date = datetime(2025, 1, 15)

    signals = detector.detect_all_patterns(
        symbol='NVDA',
        price_data=price_data,
        current_date=current_date,
        market_type='stocks',
        additional_data=additional_data
    )

    print(f"\n✓ Scanned {total_patterns} patterns")
    print(f"✓ Found {len(signals)} ACTIVE patterns")

    # Show breakdown
    categories = {}
    for s in signals:
        cat = s.pattern.category
        categories[cat] = categories.get(cat, 0) + 1

    print(f"\nActive Patterns by Category:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {cat.capitalize():15s} : {count}")

    # ===== 4. Top Patterns =====
    print_section("⭐ TOP 5 ACTIVE PATTERNS")

    for i, signal in enumerate(signals[:5], 1):
        direction = "📈 BULLISH" if signal.expected_return > 0 else "📉 BEARISH"

        print(f"\n{i}. {signal.pattern.name}")
        print(f"   {direction} │ {signal.pattern.category.upper()}")
        print(f"   ├─ Signal Strength  : {signal.signal_strength:.2f}/1.00  {'█' * int(signal.signal_strength * 20)}")
        print(f"   ├─ Confidence       : {signal.confidence:.0%}")
        print(f"   ├─ Expected Return  : {signal.expected_return:+.1%}")
        print(f"   ├─ Time Horizon     : {signal.expected_duration} days")
        print(f"   ├─ Historical Sharpe: {signal.pattern.sharpe_ratio:.2f}")

        if signal.strength_factors_present:
            print(f"   └─ Strength Factors:")
            for factor in signal.strength_factors_present[:3]:
                print(f"      • {factor}")

    # ===== 5. Combined Prediction =====
    print_section("🎯 COMBINED PATTERN PREDICTION")

    combined = detector.combine_pattern_signals(signals)

    # Visual representation
    pred = combined['prediction']
    conf = combined['confidence']

    direction_emoji = "🚀" if pred > 0.10 else "📈" if pred > 0 else "📉" if pred > -0.10 else "⚠️"

    print(f"\n{direction_emoji} OVERALL PREDICTION: {pred:+.2%}")
    print(f"   └─ Based on {combined['num_patterns']} active patterns")
    print(f"\n🎲 CONFIDENCE: {conf:.0%}")

    # Confidence bar
    conf_bar = int(conf * 50)
    print(f"   [{'█' * conf_bar}{'░' * (50 - conf_bar)}] {conf:.0%}")

    print(f"\n📊 Pattern Mix:")
    for category, count in sorted(combined['category_breakdown'].items(), key=lambda x: x[1], reverse=True):
        pct = count / combined['num_patterns'] * 100
        print(f"   • {category.capitalize():15s} : {count:2d} patterns ({pct:.0f}%)")

    # ===== 6. Black-Scholes Analysis =====
    print_section("📐 BLACK-SCHOLES OPTION PRICING")

    bs = BlackScholesMerton()

    # Calculate drift
    drift_params = bs.calculate_drift(price_data['close'].values)

    print(f"\nHistorical Drift Parameters:")
    print(f"   • Annual Return     : {drift_params['annual_return']:+.1%}")
    print(f"   • Annual Volatility : {drift_params['annual_volatility']:.1%}")
    print(f"   • Sharpe Ratio      : {drift_params['sharpe_ratio']:.2f}")

    # Price ATM call option (6 months)
    call_price = bs.black_scholes_call(
        S=current_price,
        K=current_price,
        T=0.5,
        r=0.05,
        sigma=drift_params['annual_volatility']
    )

    greeks = bs.calculate_greeks(
        S=current_price,
        K=current_price,
        T=0.5,
        r=0.05,
        sigma=drift_params['annual_volatility']
    )

    print(f"\nATM Call Option (6 months):")
    print(f"   • Price             : ${call_price:.2f}")
    print(f"   • Delta             : {greeks['delta']:.3f}")
    print(f"   • Gamma             : {greeks['gamma']:.4f}")
    print(f"   • Theta (daily)     : ${greeks['theta']:.2f}")
    print(f"   • Vega              : ${greeks['vega']:.2f}")

    # ===== 7. Behavioral Analysis =====
    print_section("🧠 BEHAVIORAL FINANCE FACTORS")

    behav_analyzer = BehavioralFactorAnalyzer()

    # Trust factor (NVIDIA example)
    trust_data = {
        'brand_reputation': additional_data['brand_reputation'],
        'innovation_score': additional_data['innovation_score'],
        'management_score': 0.90,
        'customer_satisfaction': 0.88,
        'employee_satisfaction': 0.85
    }

    trust = behav_analyzer.calculate_trust_factor(trust_data)

    print(f"\nCompany Trust Factor: {trust:.2f}/1.00")
    trust_bar = int(trust * 50)
    print(f"   [{'█' * trust_bar}{'░' * (50 - trust_bar)}] {trust:.0%}")

    # Fear & Greed
    fg = behav_analyzer.calculate_fear_greed_index(
        vix=additional_data['vix'],
        put_call_ratio=0.85,
        market_momentum=65,
        market_breadth=58,
        safe_haven_demand=35
    )

    print(f"\nFear & Greed Index: {fg['fear_greed_score']:.0f}/100")
    print(f"   Sentiment: {fg['sentiment']}")

    fg_bar = int(fg['fear_greed_score'] / 2)
    print(f"   Fear [{'█' * fg_bar}{'░' * (50 - fg_bar)}] Greed")

    # ===== 8. Final Recommendation =====
    print_section("💼 TRADING RECOMMENDATION")

    # Combine all factors
    pattern_weight = 0.40
    bs_weight = 0.25
    trust_weight = 0.20
    sentiment_weight = 0.15

    final_score = (
        pred * pattern_weight +
        drift_params['annual_return'] * bs_weight +
        (trust - 0.5) * 2 * trust_weight +  # Scale trust to ±1
        (fg['fear_greed_score'] / 100 - 0.5) * 2 * sentiment_weight
    )

    print(f"\nFinal Composite Score: {final_score:+.2%}")
    print(f"\nScore Breakdown:")
    print(f"   • Pattern Prediction   (40%): {pred:+.2%}")
    print(f"   • Historical Drift     (25%): {drift_params['annual_return']:+.2%}")
    print(f"   • Trust Factor         (20%): {trust:.2f}")
    print(f"   • Market Sentiment     (15%): {fg['fear_greed_score']:.0f}/100")

    # Recommendation
    if final_score > 0.15:
        recommendation = "🟢 STRONG BUY"
        rationale = "Multiple bullish patterns, strong fundamentals, high trust"
    elif final_score > 0.05:
        recommendation = "🟡 BUY"
        rationale = "Positive patterns, favorable conditions"
    elif final_score > -0.05:
        recommendation = "⚪ HOLD"
        rationale = "Mixed signals, neutral positioning"
    elif final_score > -0.15:
        recommendation = "🟠 SELL"
        rationale = "Negative patterns emerging"
    else:
        recommendation = "🔴 STRONG SELL"
        rationale = "Multiple bearish signals"

    print(f"\n{'─' * 80}")
    print(f"{recommendation}")
    print(f"{'─' * 80}")
    print(f"Rationale: {rationale}")
    print(f"\nTarget Return (1 year): {final_score:+.1%}")
    print(f"Risk Level: {'High' if vol > 0.40 else 'Medium' if vol > 0.20 else 'Low'}")
    print(f"Time Horizon: {np.mean([s.expected_duration for s in signals[:5]]):.0f} days average")

    # ===== 9. Risk Warnings =====
    print_section("⚠️  RISK FACTORS")

    print("\nIdentified Risks:")

    risk_count = 0
    if fg['fear_greed_score'] > 75:
        print("   ⚠️  Market sentiment in 'extreme greed' territory")
        risk_count += 1

    if vol > 0.40:
        print(f"   ⚠️  High volatility ({vol:.0%}) increases risk")
        risk_count += 1

    if additional_data['pe_ratio'] > 40:
        print(f"   ⚠️  High P/E ratio ({additional_data['pe_ratio']:.0f}) suggests rich valuation")
        risk_count += 1

    # Check for bearish patterns
    bearish_signals = [s for s in signals if s.expected_return < 0]
    if bearish_signals:
        print(f"   ⚠️  {len(bearish_signals)} bearish pattern(s) detected")
        risk_count += 1

    if risk_count == 0:
        print("   ✓ No major risk factors identified")

    # ===== Summary =====
    print_header("END OF ANALYSIS")
    print()
    print(f"Analysis Date: {current_date.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Patterns Scanned: {total_patterns}")
    print(f"Active Patterns: {len(signals)}")
    print(f"Recommendation: {recommendation}")
    print(f"Expected Return: {final_score:+.1%}")
    print()
    print("=" * 80)

    # Cleanup
    db.close()
    detector.db.close()


if __name__ == "__main__":
    run_comprehensive_demo()
