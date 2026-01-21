"""
Risk Management and Position Sizing

Implements comprehensive risk management:
- Position sizing (Kelly Criterion, fixed fractional, etc.)
- Stop-loss management
- Portfolio risk (VaR, CVaR)
- Correlation hedging
- Aggressive position analyzer with risk mitigation
- Dynamic risk adjustment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from scipy.stats import norm
from datetime import datetime


@dataclass
class RiskMetrics:
    """Risk metrics for a position or portfolio"""
    value_at_risk_95: float  # 95% VaR
    value_at_risk_99: float  # 99% VaR
    conditional_var_95: float  # Expected Shortfall
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    beta: float
    volatility: float
    correlation_to_market: float


@dataclass
class PositionRisk:
    """Risk assessment for a trading position"""
    symbol: str
    position_size: float
    entry_price: float
    current_price: float
    stop_loss: float
    risk_amount: float  # $ at risk
    risk_percentage: float  # % of portfolio
    probability_of_loss: float
    expected_loss: float
    risk_reward_ratio: float
    recommendation: str  # 'approve', 'reduce', 'reject'


@dataclass
class AggressivePosition:
    """Aggressive trading position with risk mitigation"""
    symbol: str
    strategy: str
    entry_price: float
    position_size: float
    leverage: float
    target_return: float
    max_loss: float
    stop_loss_levels: List[float]  # Multiple stops
    hedge_positions: List[Dict[str, Any]]  # Offsetting positions
    risk_score: float  # 0-1
    kelly_fraction: float  # Optimal sizing
    margin_required: float


class RiskManager:
    """
    Comprehensive risk management system.
    """

    def __init__(
        self,
        portfolio_value: float = 100000,
        max_position_risk: float = 0.02,  # 2% per position
        max_portfolio_risk: float = 0.06,  # 6% total
        risk_free_rate: float = 0.05
    ):
        self.portfolio_value = portfolio_value
        self.max_position_risk = max_position_risk
        self.max_portfolio_risk = max_portfolio_risk
        self.risk_free_rate = risk_free_rate

    def calculate_position_size_kelly(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion.

        Kelly % = W - [(1 - W) / R]
        Where:
            W = Win probability
            R = Win/Loss ratio

        Args:
            win_rate: Probability of winning trade
            avg_win: Average win amount
            avg_loss: Average loss amount

        Returns:
            Kelly fraction (0-1)
        """
        if avg_loss == 0:
            return 0

        r = abs(avg_win / avg_loss)
        kelly = win_rate - ((1 - win_rate) / r)

        # Use fractional Kelly (1/2 or 1/4) for safety
        return max(0, kelly * 0.5)  # Half Kelly

    def calculate_position_size_fixed_fractional(
        self,
        entry_price: float,
        stop_loss: float,
        risk_per_trade: float = 0.01  # 1% of portfolio
    ) -> float:
        """
        Calculate position size using fixed fractional method.

        Position Size = (Portfolio × Risk%) / (Entry - Stop)

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            risk_per_trade: % of portfolio to risk

        Returns:
            Number of shares
        """
        if entry_price == stop_loss:
            return 0

        risk_amount = self.portfolio_value * risk_per_trade
        risk_per_share = abs(entry_price - stop_loss)

        return risk_amount / risk_per_share

    def calculate_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Value at Risk (VaR).

        Args:
            returns: Historical returns
            confidence: Confidence level (0.95 or 0.99)

        Returns:
            VaR (negative number)
        """
        return np.percentile(returns, (1 - confidence) * 100)

    def calculate_cvar(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        Calculate Conditional Value at Risk (CVaR / Expected Shortfall).

        Average loss beyond VaR.

        Args:
            returns: Historical returns
            confidence: Confidence level

        Returns:
            CVaR (negative number)
        """
        var = self.calculate_var(returns, confidence)
        return returns[returns <= var].mean()

    def calculate_max_drawdown(
        self,
        equity_curve: pd.Series
    ) -> float:
        """
        Calculate maximum drawdown.

        Args:
            equity_curve: Portfolio value over time

        Returns:
            Max drawdown (negative %)
        """
        cummax = equity_curve.cummax()
        drawdown = (equity_curve - cummax) / cummax
        return drawdown.min()

    def calculate_sharpe_ratio(
        self,
        returns: pd.Series,
        annualize: bool = True
    ) -> float:
        """
        Calculate Sharpe Ratio.

        Sharpe = (Return - RiskFree) / Volatility

        Args:
            returns: Period returns
            annualize: Whether to annualize

        Returns:
            Sharpe ratio
        """
        excess_return = returns.mean() - self.risk_free_rate / 252
        volatility = returns.std()

        if volatility == 0:
            return 0

        sharpe = excess_return / volatility

        if annualize:
            sharpe *= np.sqrt(252)

        return sharpe

    def calculate_sortino_ratio(
        self,
        returns: pd.Series,
        annualize: bool = True
    ) -> float:
        """
        Calculate Sortino Ratio (uses downside deviation instead of total volatility).

        Args:
            returns: Period returns
            annualize: Whether to annualize

        Returns:
            Sortino ratio
        """
        excess_return = returns.mean() - self.risk_free_rate / 252
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return float('inf')

        downside_dev = downside_returns.std()

        if downside_dev == 0:
            return float('inf')

        sortino = excess_return / downside_dev

        if annualize:
            sortino *= np.sqrt(252)

        return sortino

    def assess_position_risk(
        self,
        symbol: str,
        position_size: float,
        entry_price: float,
        current_price: float,
        stop_loss: float,
        win_probability: float = 0.55
    ) -> PositionRisk:
        """
        Comprehensive risk assessment for a position.

        Args:
            symbol: Trading symbol
            position_size: Number of shares/contracts
            entry_price: Entry price
            current_price: Current price
            stop_loss: Stop loss price
            win_probability: Estimated win rate

        Returns:
            PositionRisk object
        """
        # Calculate risk
        risk_per_share = abs(entry_price - stop_loss)
        risk_amount = position_size * risk_per_share
        risk_percentage = risk_amount / self.portfolio_value

        # Expected loss
        loss_probability = 1 - win_probability
        expected_loss = risk_amount * loss_probability

        # Risk/reward (assuming target is symmetric)
        target_price = entry_price + (entry_price - stop_loss) * 2  # 2:1 R/R
        potential_gain = abs(target_price - entry_price) * position_size
        risk_reward_ratio = potential_gain / risk_amount if risk_amount > 0 else 0

        # Recommendation
        if risk_percentage > self.max_position_risk:
            recommendation = 'reject'
        elif risk_percentage > self.max_position_risk * 0.75:
            recommendation = 'reduce'
        else:
            recommendation = 'approve'

        return PositionRisk(
            symbol=symbol,
            position_size=position_size,
            entry_price=entry_price,
            current_price=current_price,
            stop_loss=stop_loss,
            risk_amount=risk_amount,
            risk_percentage=risk_percentage,
            probability_of_loss=loss_probability,
            expected_loss=expected_loss,
            risk_reward_ratio=risk_reward_ratio,
            recommendation=recommendation
        )

    def design_aggressive_position(
        self,
        symbol: str,
        entry_price: float,
        target_return: float = 0.50,  # 50% target
        max_acceptable_loss: float = 0.10,  # 10% max loss
        win_rate: float = 0.45,
        use_leverage: bool = False
    ) -> AggressivePosition:
        """
        Design an aggressive trading position with proper risk mitigation.

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            target_return: Target return %
            max_acceptable_loss: Maximum acceptable loss %
            win_rate: Estimated probability of success
            use_leverage: Whether to use leverage

        Returns:
            AggressivePosition with risk mitigation plan
        """
        # Calculate Kelly fraction
        avg_win = target_return
        avg_loss = max_acceptable_loss
        kelly_fraction = self.calculate_position_size_kelly(win_rate, avg_win, avg_loss)

        # Adjust for leverage
        leverage = 1.0
        if use_leverage and kelly_fraction > 0.1:
            leverage = min(2.0, kelly_fraction * 10)  # Max 2x leverage
        elif kelly_fraction <= 0:
            kelly_fraction = 0.01  # Minimum position

        # Position size
        base_allocation = self.portfolio_value * kelly_fraction
        position_size = (base_allocation * leverage) / entry_price

        # Multiple stop-loss levels (trailing)
        stop_1 = entry_price * (1 - max_acceptable_loss)  # Hard stop
        stop_2 = entry_price * (1 - max_acceptable_loss * 0.5)  # Reduce position
        stop_3 = entry_price * (1 - max_acceptable_loss * 0.75)  # Warning level

        # Hedge positions (options for protection)
        hedge_positions = []

        if leverage > 1.0:
            # Protective puts if using leverage
            put_strike = entry_price * 0.95  # 5% OTM put
            hedge_positions.append({
                'type': 'protective_put',
                'strike': put_strike,
                'contracts': position_size / 100,  # 1 contract per 100 shares
                'cost': entry_price * 0.02  # ~2% premium
            })

        if target_return > 0.30:
            # Sell covered calls to reduce cost basis
            call_strike = entry_price * (1 + target_return)
            hedge_positions.append({
                'type': 'covered_call',
                'strike': call_strike,
                'contracts': position_size / 100,
                'premium_received': entry_price * 0.03  # ~3% premium
            })

        # Risk score
        risk_score = min(1.0, (
            0.3 * leverage / 2 +  # Leverage component
            0.3 * max_acceptable_loss / 0.20 +  # Loss tolerance
            0.2 * (1 - win_rate) +  # Win rate
            0.2 * target_return / 0.50  # Return target
        ))

        # Margin required
        margin_required = base_allocation if leverage <= 1 else base_allocation / leverage

        return AggressivePosition(
            symbol=symbol,
            strategy='aggressive_with_mitigation',
            entry_price=entry_price,
            position_size=position_size,
            leverage=leverage,
            target_return=target_return,
            max_loss=max_acceptable_loss,
            stop_loss_levels=[stop_1, stop_2, stop_3],
            hedge_positions=hedge_positions,
            risk_score=risk_score,
            kelly_fraction=kelly_fraction,
            margin_required=margin_required
        )

    def calculate_portfolio_correlation(
        self,
        returns_matrix: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix for portfolio positions.

        Args:
            returns_matrix: DataFrame with returns for each symbol

        Returns:
            Correlation matrix
        """
        return returns_matrix.corr()

    def optimize_hedge_ratios(
        self,
        position_returns: pd.Series,
        hedge_returns: pd.Series
    ) -> float:
        """
        Calculate optimal hedge ratio using linear regression.

        Hedge Ratio = Cov(Position, Hedge) / Var(Hedge)

        Args:
            position_returns: Returns of position to hedge
            hedge_returns: Returns of hedge instrument

        Returns:
            Optimal hedge ratio
        """
        covariance = np.cov(position_returns, hedge_returns)[0, 1]
        hedge_variance = np.var(hedge_returns)

        if hedge_variance == 0:
            return 0

        return covariance / hedge_variance

    def stress_test_position(
        self,
        position_value: float,
        scenarios: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Stress test a position under various scenarios.

        Args:
            position_value: Current position value
            scenarios: Dict of scenario_name -> price_change%

        Returns:
            Dict of scenario -> resulting P&L
        """
        results = {}

        for scenario_name, price_change in scenarios.items():
            pnl = position_value * price_change
            results[scenario_name] = pnl

        return results


if __name__ == "__main__":
    # Example usage
    print("=== Risk Management System Test ===\n")

    risk_mgr = RiskManager(portfolio_value=100000)

    # 1. Position sizing - Kelly Criterion
    print("1. Kelly Criterion Position Sizing")
    kelly = risk_mgr.calculate_position_size_kelly(
        win_rate=0.60,
        avg_win=0.10,
        avg_loss=0.05
    )
    print(f"   Kelly Fraction: {kelly:.2%}")
    print(f"   Position Size: ${100000 * kelly:,.2f}")

    # 2. Fixed fractional position sizing
    print("\n2. Fixed Fractional Position Sizing")
    shares = risk_mgr.calculate_position_size_fixed_fractional(
        entry_price=100,
        stop_loss=95,
        risk_per_trade=0.01
    )
    print(f"   Shares to buy: {shares:.0f}")
    print(f"   Position value: ${shares * 100:,.2f}")

    # 3. Risk metrics
    print("\n3. Risk Metrics")
    returns = pd.Series(np.random.randn(252) * 0.02)  # Simulated daily returns

    var_95 = risk_mgr.calculate_var(returns, 0.95)
    cvar_95 = risk_mgr.calculate_cvar(returns, 0.95)
    sharpe = risk_mgr.calculate_sharpe_ratio(returns)

    print(f"   95% VaR: {var_95:.2%}")
    print(f"   95% CVaR: {cvar_95:.2%}")
    print(f"   Sharpe Ratio: {sharpe:.2f}")

    # 4. Position risk assessment
    print("\n4. Position Risk Assessment")
    position_risk = risk_mgr.assess_position_risk(
        symbol='AAPL',
        position_size=100,
        entry_price=150,
        current_price=150,
        stop_loss=145,
        win_probability=0.65
    )

    print(f"   Risk Amount: ${position_risk.risk_amount:,.2f}")
    print(f"   Risk %: {position_risk.risk_percentage:.2%}")
    print(f"   R/R Ratio: {position_risk.risk_reward_ratio:.2f}")
    print(f"   Recommendation: {position_risk.recommendation}")

    # 5. Aggressive position design
    print("\n5. Aggressive Position with Risk Mitigation")
    aggressive_pos = risk_mgr.design_aggressive_position(
        symbol='TSLA',
        entry_price=200,
        target_return=0.50,  # 50% target
        max_acceptable_loss=0.15,  # 15% max loss
        win_rate=0.45,
        use_leverage=True
    )

    print(f"   Position Size: {aggressive_pos.position_size:.2f} shares")
    print(f"   Leverage: {aggressive_pos.leverage:.2f}x")
    print(f"   Kelly Fraction: {aggressive_pos.kelly_fraction:.2%}")
    print(f"   Stop Loss Levels: {[f'${sl:.2f}' for sl in aggressive_pos.stop_loss_levels]}")
    print(f"   Hedge Positions: {len(aggressive_pos.hedge_positions)}")
    print(f"   Risk Score: {aggressive_pos.risk_score:.2f}/1.0")
    print(f"   Margin Required: ${aggressive_pos.margin_required:,.2f}")

    # 6. Stress testing
    print("\n6. Stress Test Results")
    scenarios = {
        'Market crash -20%': -0.20,
        'Moderate decline -10%': -0.10,
        'Flat': 0.0,
        'Rally +15%': 0.15,
        'Bull run +30%': 0.30
    }

    position_value = 20000
    stress_results = risk_mgr.stress_test_position(position_value, scenarios)

    for scenario, pnl in stress_results.items():
        print(f"   {scenario}: {pnl:+,.2f} ({pnl/position_value:+.1%})")
