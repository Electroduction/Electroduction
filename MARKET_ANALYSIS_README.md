# Market Analysis System

A comprehensive algorithmic trading platform combining seasonal patterns, behavioral finance, quantitative models, and machine learning to predict market movements and generate trading signals.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Modules](#modules)
- [Usage Examples](#usage-examples)
- [Performance Metrics](#performance-metrics)
- [Contributing](#contributing)

## 🎯 Overview

This system integrates multiple disciplines to create a sophisticated market analysis and trading platform:

- **Classical Finance**: Black-Scholes-Merton option pricing, portfolio theory
- **Behavioral Finance**: Psychology, demographics, sentiment analysis
- **Machine Learning**: Neural networks, ensemble methods, factor weighting
- **Alternative Data**: News, social media, hiring trends, economic indicators

### Key Differentiator

Multi-disciplinary approach that combines dozens of factors (seasonal effects, geopolitical tensions, behavioral biases, etc.) using machine learning to find optimal trading strategies across multiple market regimes.

## ✨ Features

### Core Capabilities

1. **Black-Scholes-Merton Option Pricing**
   - Classic Black-Scholes for European options
   - Merton jump-diffusion model
   - Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
   - Implied volatility solver
   - Heston stochastic volatility model
   - Multi-factor drift estimation

2. **Seasonal Pattern Analysis**
   - January Effect (small-cap outperformance)
   - MLK Day reversal patterns
   - Monthly seasonality
   - Day-of-week effects
   - Dividend calendar integration
   - Quarter-end window dressing

3. **Behavioral Finance Engine**
   - Fear & Greed Index
   - Herd behavior detection
   - Company trust factor scoring
   - Loss aversion modeling
   - Big Five personality trait analysis
   - Social sentiment analysis

4. **Multi-Factor ML Model**
   - Linear regression, Ridge, Lasso
   - Random Forest
   - Gradient Boosting (XGBoost/LightGBM compatible)
   - Ensemble methods with adaptive weighting
   - Regime-switching models

5. **Data Collection Apparatus**
   - Market data (OHLCV, options chains)
   - Fundamental data (financials, ratios)
   - News sentiment
   - Social media (Twitter, Reddit)
   - Economic indicators (GDP, CPI, rates)
   - Alternative data (hiring, web traffic)

6. **Trading Strategies**
   - Multi-market algorithm (stocks, futures, indexes)
   - High-frequency trading (HFT) strategies
   - Options strategies (spreads, straddles)
   - Pattern recognition (head & shoulders, double bottom)
   - Long-term position trading

7. **Risk Management**
   - Position sizing (Kelly Criterion, fixed fractional)
   - Value at Risk (VaR) and CVaR
   - Maximum drawdown tracking
   - Sharpe and Sortino ratios
   - Aggressive position analyzer with mitigation
   - Correlation hedging

8. **Backtesting Engine**
   - Historical replay with transaction costs
   - Multiple order types (market, limit, stop)
   - Commission and slippage modeling
   - Walk-forward optimization
   - Monte Carlo simulation
   - Out-of-sample testing

## 🏗️ System Architecture

```
market_analysis/
├── core/
│   ├── black_scholes_merton.py    # Option pricing models
│   ├── seasonal_patterns.py        # Calendar effects
│   └── behavioral_factors.py       # Psychology & sentiment
├── models/
│   └── factor_weighting.py         # ML factor combination
├── data/
│   └── data_collector.py           # Multi-source data gathering
├── strategies/
│   └── trading_strategies.py       # Signal generation
├── utils/
│   ├── risk_management.py          # Position sizing & risk
│   └── backtesting.py              # Performance validation
└── main.py                         # Integration script
```

## 📦 Installation

### Requirements

- Python 3.8+
- NumPy
- Pandas
- SciPy
- Scikit-learn

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Optional Dependencies (for production use)

```bash
# For faster gradient boosting
pip install xgboost lightgbm

# For deep learning
pip install tensorflow

# For additional data sources
pip install yfinance alpha_vantage pandas_datareader
```

## 🚀 Quick Start

### Run Comprehensive Demo

```bash
cd market_analysis
python main.py
```

This will run a full analysis on NVIDIA (NVDA) demonstrating all system components.

### Basic Usage

```python
from market_analysis.main import MarketAnalysisSystem
from datetime import datetime, timedelta

# Initialize system
system = MarketAnalysisSystem(initial_capital=100000)

# Analyze a symbol
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

analysis = system.analyze_symbol('AAPL', start_date, end_date)

# Get trading signal
if analysis['signal']:
    print(f"Signal: {analysis['signal']['direction']}")
    print(f"Entry: ${analysis['signal']['entry_price']:.2f}")
    print(f"Target: ${analysis['signal']['target_price']:.2f}")
```

## 📚 Modules

### 1. Black-Scholes-Merton (`core/black_scholes_merton.py`)

```python
from market_analysis.core.black_scholes_merton import BlackScholesMerton

bs = BlackScholesMerton()

# Price a call option
call_price = bs.black_scholes_call(S=100, K=105, T=0.5, r=0.05, sigma=0.2)

# Calculate Greeks
greeks = bs.calculate_greeks(S=100, K=105, T=0.5, r=0.05, sigma=0.2)

# Calculate drift from historical data
import numpy as np
prices = np.array([100, 102, 101, 105, 103, 107, 110])
drift_params = bs.calculate_drift(prices)
```

### 2. Seasonal Patterns (`core/seasonal_patterns.py`)

```python
from market_analysis.core.seasonal_patterns import SeasonalPatternAnalyzer
from datetime import datetime

analyzer = SeasonalPatternAnalyzer()

# Get seasonal signals for current date
signals = analyzer.generate_seasonal_signals(datetime.now())

for signal in signals:
    print(f"{signal.pattern_name}: {signal.signal_strength:+.2f}")

# Calculate overall seasonal favorability
score = analyzer.calculate_seasonal_score(datetime.now())
```

### 3. Behavioral Factors (`core/behavioral_factors.py`)

```python
from market_analysis.core.behavioral_factors import BehavioralFactorAnalyzer

analyzer = BehavioralFactorAnalyzer()

# Calculate Fear & Greed Index
fg_index = analyzer.calculate_fear_greed_index(
    vix=25, put_call_ratio=1.1, market_momentum=45,
    market_breadth=48, safe_haven_demand=55
)

# Calculate company trust factor
trust_data = {
    'brand_reputation': 0.9,
    'innovation_score': 0.95,
    'management_score': 0.88
}
trust_score = analyzer.calculate_trust_factor(trust_data)
```

### 4. Factor Weighting (`models/factor_weighting.py`)

```python
from market_analysis.models.factor_weighting import FactorWeightingEngine
import pandas as pd

# Create and train model
engine = FactorWeightingEngine('ensemble')

# Train on historical data
X = pd.DataFrame({...})  # Features
y = pd.Series([...])     # Returns

metrics = engine.train(X, y)

# Make prediction
prediction = engine.predict(X_new)
```

### 5. Trading Strategies (`strategies/trading_strategies.py`)

```python
from market_analysis.strategies.trading_strategies import MultiMarketAlgorithm, MarketType

algo = MultiMarketAlgorithm(MarketType.STOCK)

signal = algo.generate_signal(
    symbol='AAPL',
    price_data=price_df,
    factors={'prediction': 0.05}
)

if signal:
    print(f"Trade {signal.direction.value} at ${signal.entry_price:.2f}")
```

### 6. Risk Management (`utils/risk_management.py`)

```python
from market_analysis.utils.risk_management import RiskManager

risk_mgr = RiskManager(portfolio_value=100000)

# Kelly Criterion position sizing
kelly = risk_mgr.calculate_position_size_kelly(
    win_rate=0.60, avg_win=0.10, avg_loss=0.05
)

# Design aggressive position with risk mitigation
aggressive_pos = risk_mgr.design_aggressive_position(
    symbol='TSLA',
    entry_price=200,
    target_return=0.50,
    max_acceptable_loss=0.15,
    use_leverage=True
)
```

### 7. Backtesting (`utils/backtesting.py`)

```python
from market_analysis.utils.backtesting import Backtester, Order, OrderType

backtester = Backtester(initial_capital=100000)

def my_strategy(data, index, params):
    # Your strategy logic
    if condition:
        return Order(symbol='AAPL', side='buy', quantity=10, order_type=OrderType.MARKET)
    return None

results = backtester.run_backtest(data, my_strategy, params={})

print(f"Total Return: {results.total_return:.2%}")
print(f"Sharpe Ratio: {results.sharpe_ratio:.2f}")
```

## 📊 Usage Examples

### Example 1: Complete Analysis Pipeline

```python
from market_analysis.main import MarketAnalysisSystem
from datetime import datetime, timedelta

system = MarketAnalysisSystem(initial_capital=100000)

# Analyze NVIDIA
analysis = system.analyze_symbol(
    'NVDA',
    start_date=datetime(2024, 1, 1),
    end_date=datetime.now()
)

# Check all components
print(f"Seasonal Score: {analysis['seasonal']['score']}")
print(f"Trust Factor: {analysis['behavioral']['trust_score']}")
print(f"Prediction: {analysis['prediction']['direction']}")

if analysis['signal']:
    print(f"Trade: {analysis['signal']['direction']}")
    print(f"Risk: {analysis['risk']['risk_percentage']:.2%}")
```

### Example 2: Custom Strategy Backtest

```python
from market_analysis.utils.backtesting import Backtester, Order, OrderType
from market_analysis.core.seasonal_patterns import SeasonalPatternAnalyzer
import pandas as pd

# Define seasonal strategy
def seasonal_strategy(data, index, params):
    analyzer = SeasonalPatternAnalyzer()
    date = data.index[index]

    score = analyzer.calculate_seasonal_score(date)

    if score > 0.5:
        return Order('SPY', 'buy', 100, OrderType.MARKET, timestamp=date)
    elif score < -0.5:
        return Order('SPY', 'sell', 100, OrderType.MARKET, timestamp=date)

    return None

# Run backtest
backtester = Backtester(initial_capital=100000)
results = backtester.run_backtest(historical_data, seasonal_strategy)

print(f"Annual Return: {results.annual_return:.2%}")
print(f"Max Drawdown: {results.max_drawdown:.2%}")
print(f"Win Rate: {results.win_rate:.2%}")
```

### Example 3: Multi-Factor Signal Generation

```python
from market_analysis.models.factor_weighting import FactorWeightingEngine
import pandas as pd

# Collect factors for a symbol
technical_factors = {'ma_50': 0.5, 'rsi': 55, 'macd': 0.02}
fundamental_factors = {'pe_ratio': 25, 'revenue_growth': 0.20}
seasonal_factors = {'january_effect': 1, 'seasonal_score': 0.3}
behavioral_factors = {'fear_greed': 65, 'trust': 0.85}
macro_factors = {'gdp_growth': 0.03, 'interest_rate': 0.05}

# Combine into features
X = pd.DataFrame([{
    **{f'tech_{k}': v for k, v in technical_factors.items()},
    **{f'fund_{k}': v for k, v in fundamental_factors.items()},
    **{f'seas_{k}': v for k, v in seasonal_factors.items()},
    **{f'behav_{k}': v for k, v in behavioral_factors.items()},
    **{f'macro_{k}': v for k, v in macro_factors.items()}
}])

# Get prediction (after training model)
engine = FactorWeightingEngine('ensemble')
# engine.train(X_historical, y_historical)  # Train first
# prediction = engine.predict(X)
```

## 📈 Performance Metrics

The system tracks comprehensive performance metrics:

### Return Metrics
- Total Return
- Annualized Return (CAGR)
- Monthly/Annual Returns

### Risk Metrics
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Value at Risk (VaR)
- Conditional VaR (CVaR)

### Trade Metrics
- Win Rate
- Profit Factor
- Average Win/Loss
- Risk/Reward Ratio
- Average Holding Period

## 🔬 Testing

Each module includes standalone tests. Run them individually:

```bash
python market_analysis/core/black_scholes_merton.py
python market_analysis/core/seasonal_patterns.py
python market_analysis/core/behavioral_factors.py
python market_analysis/models/factor_weighting.py
python market_analysis/strategies/trading_strategies.py
python market_analysis/utils/risk_management.py
python market_analysis/utils/backtesting.py
```

## 📖 Research References

This system is built on established research:

1. **Options Pricing**: Black, F. & Scholes, M. (1973), Merton, R.C. (1973)
2. **Behavioral Finance**: Kahneman & Tversky (1979), Thaler, R.H.
3. **Seasonal Effects**: Rozeff & Kinney (1976), Keim (1983)
4. **Risk Management**: Kelly, J. (1956), Markowitz, H. (1952)
5. **Market Microstructure**: O'Hara, M. (1995)

## ⚠️ Disclaimer

This system is for educational and research purposes. Trading involves substantial risk of loss. Past performance does not guarantee future results. Always:

- Test thoroughly before live trading
- Start with paper trading
- Use proper risk management
- Understand all strategies before implementation
- Comply with all applicable regulations

## 🤝 Contributing

This is a research project. Future enhancements could include:

- Integration with live data APIs (Alpha Vantage, IEX Cloud)
- Real-time WebSocket data streaming
- Deep learning models (LSTM, Transformers)
- Reinforcement learning for strategy optimization
- Cryptocurrency market support
- Advanced portfolio optimization (Black-Litterman)
- Automated model retraining
- Production-ready execution system

## 📄 License

Educational and research use. Commercial use requires additional licensing.

## 📞 Support

For questions or issues, please refer to the PRD document (`MARKET_ANALYSIS_PRD.md`) for detailed specifications.

---

**Built with**: Python, NumPy, Pandas, SciPy, Scikit-learn

**Author**: Market Analysis Team

**Last Updated**: 2026-01-21
