"""
Backtesting Engine

Validates trading strategies on historical data:
- Historical replay with transaction costs
- Performance metrics
- Walk-forward optimization
- Monte Carlo simulation
- Out-of-sample testing
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """Trading order"""
    symbol: str
    side: str  # 'buy' or 'sell'
    quantity: float
    order_type: OrderType
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_quantity: float = 0.0
    commission: float = 0.0


@dataclass
class Trade:
    """Executed trade"""
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime
    commission: float
    slippage: float = 0.0


@dataclass
class BacktestResults:
    """Backtest performance results"""
    total_return: float
    annual_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    avg_holding_period: float
    equity_curve: pd.Series
    trades: List[Trade]
    monthly_returns: pd.Series
    annual_returns: pd.Series


class Backtester:
    """
    Historical backtesting engine.
    """

    def __init__(
        self,
        initial_capital: float = 100000,
        commission_rate: float = 0.001,  # 0.1%
        slippage_rate: float = 0.0005,  # 0.05%
        margin_rate: float = 0.5  # 50% margin
    ):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # symbol -> quantity
        self.equity_curve = []
        self.trades = []
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.margin_rate = margin_rate

    def reset(self):
        """Reset backtest state"""
        self.cash = self.initial_capital
        self.positions = {}
        self.equity_curve = []
        self.trades = []

    def execute_order(
        self,
        order: Order,
        current_price: float
    ) -> bool:
        """
        Execute a trading order.

        Args:
            order: Order to execute
            current_price: Current market price

        Returns:
            True if order was filled
        """
        # Check if order should be filled
        should_fill = False

        if order.order_type == OrderType.MARKET:
            should_fill = True
            fill_price = current_price

        elif order.order_type == OrderType.LIMIT:
            if order.side == 'buy' and current_price <= order.price:
                should_fill = True
                fill_price = order.price
            elif order.side == 'sell' and current_price >= order.price:
                should_fill = True
                fill_price = order.price

        elif order.order_type == OrderType.STOP:
            if order.side == 'buy' and current_price >= order.stop_price:
                should_fill = True
                fill_price = current_price
            elif order.side == 'sell' and current_price <= order.stop_price:
                should_fill = True
                fill_price = current_price

        if not should_fill:
            return False

        # Apply slippage
        if order.side == 'buy':
            fill_price *= (1 + self.slippage_rate)
        else:
            fill_price *= (1 - self.slippage_rate)

        # Calculate commission
        commission = order.quantity * fill_price * self.commission_rate

        # Check if we have enough capital
        if order.side == 'buy':
            cost = order.quantity * fill_price + commission
            if cost > self.cash:
                order.status = OrderStatus.REJECTED
                return False

        # Execute trade
        if order.side == 'buy':
            self.cash -= order.quantity * fill_price + commission
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) + order.quantity
        else:  # sell
            self.cash += order.quantity * fill_price - commission
            self.positions[order.symbol] = self.positions.get(order.symbol, 0) - order.quantity

        # Record trade
        trade = Trade(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=fill_price,
            timestamp=order.timestamp,
            commission=commission,
            slippage=abs(fill_price - current_price)
        )
        self.trades.append(trade)

        order.status = OrderStatus.FILLED
        order.filled_price = fill_price
        order.filled_quantity = order.quantity
        order.commission = commission

        return True

    def get_portfolio_value(
        self,
        current_prices: Dict[str, float]
    ) -> float:
        """
        Calculate current portfolio value.

        Args:
            current_prices: Dict of symbol -> current price

        Returns:
            Total portfolio value
        """
        position_value = sum(
            qty * current_prices.get(symbol, 0)
            for symbol, qty in self.positions.items()
        )

        return self.cash + position_value

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: Callable[[pd.DataFrame, int, Any], Optional[Order]],
        strategy_params: Any = None
    ) -> BacktestResults:
        """
        Run backtest on historical data.

        Args:
            data: Historical OHLCV data (multi-symbol supported)
            strategy: Strategy function that generates orders
                      signature: strategy(data, current_index, params) -> Order or None
            strategy_params: Parameters to pass to strategy

        Returns:
            BacktestResults object
        """
        self.reset()

        # Record equity curve
        for i in range(len(data)):
            # Get current prices
            current_prices = {}
            if isinstance(data.index, pd.MultiIndex):
                # Multi-symbol data
                current_data = data.loc[data.index.get_level_values(0) == data.index.get_level_values(0)[i]]
                for symbol in current_data.index.get_level_values(1).unique():
                    current_prices[symbol] = current_data.loc[(slice(None), symbol), 'close'].iloc[0]
            else:
                # Single symbol
                current_prices['symbol'] = data['close'].iloc[i]

            # Generate signal from strategy
            order = strategy(data, i, strategy_params)

            # Execute order if generated
            if order:
                price = current_prices.get(order.symbol, data['close'].iloc[i])
                self.execute_order(order, price)

            # Record portfolio value
            portfolio_value = self.get_portfolio_value(current_prices)
            self.equity_curve.append({
                'timestamp': data.index[i],
                'value': portfolio_value,
                'cash': self.cash
            })

        # Calculate performance metrics
        return self._calculate_metrics()

    def _calculate_metrics(self) -> BacktestResults:
        """Calculate performance metrics from backtest"""
        equity_df = pd.DataFrame(self.equity_curve)
        equity_series = equity_df.set_index('timestamp')['value']

        # Returns
        returns = equity_series.pct_change().dropna()
        total_return = (equity_series.iloc[-1] / self.initial_capital) - 1

        # Annualized return
        days = (equity_series.index[-1] - equity_series.index[0]).days
        years = days / 365.25
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0

        # Sharpe ratio
        if len(returns) > 0 and returns.std() > 0:
            sharpe = returns.mean() / returns.std() * np.sqrt(252)
        else:
            sharpe = 0

        # Sortino ratio
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0 and downside_returns.std() > 0:
            sortino = returns.mean() / downside_returns.std() * np.sqrt(252)
        else:
            sortino = 0

        # Max drawdown
        cummax = equity_series.cummax()
        drawdown = (equity_series - cummax) / cummax
        max_drawdown = drawdown.min()

        # Trade statistics
        winning_trades = []
        losing_trades = []

        # Group trades into round trips
        for trade in self.trades:
            if trade.side == 'sell':
                # Find corresponding buy
                buy_trades = [t for t in self.trades
                             if t.symbol == trade.symbol and t.side == 'buy' and t.timestamp < trade.timestamp]
                if buy_trades:
                    buy_trade = buy_trades[-1]
                    pnl = (trade.price - buy_trade.price) * trade.quantity - trade.commission - buy_trade.commission

                    if pnl > 0:
                        winning_trades.append(pnl)
                    else:
                        losing_trades.append(pnl)

        total_trades = len(winning_trades) + len(losing_trades)
        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0

        avg_win = np.mean(winning_trades) if winning_trades else 0
        avg_loss = np.mean(losing_trades) if losing_trades else 0

        # Profit factor
        total_wins = sum(winning_trades) if winning_trades else 0
        total_losses = abs(sum(losing_trades)) if losing_trades else 0
        profit_factor = total_wins / total_losses if total_losses > 0 else float('inf')

        # Monthly and annual returns
        monthly_returns = equity_series.resample('M').last().pct_change().dropna()
        annual_returns = equity_series.resample('Y').last().pct_change().dropna()

        return BacktestResults(
            total_return=total_return,
            annual_return=annual_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=total_trades,
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=max(winning_trades) if winning_trades else 0,
            largest_loss=min(losing_trades) if losing_trades else 0,
            avg_holding_period=0,  # TODO: Calculate
            equity_curve=equity_series,
            trades=self.trades,
            monthly_returns=monthly_returns,
            annual_returns=annual_returns
        )

    def monte_carlo_simulation(
        self,
        results: BacktestResults,
        n_simulations: int = 1000
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation on backtest results.

        Randomly reorder trades to see distribution of outcomes.

        Args:
            results: BacktestResults from backtest
            n_simulations: Number of simulations

        Returns:
            Dictionary with simulation statistics
        """
        # Extract trade returns
        trade_returns = []
        for i in range(1, len(results.equity_curve)):
            ret = results.equity_curve.iloc[i] / results.equity_curve.iloc[i-1] - 1
            trade_returns.append(ret)

        # Run simulations
        final_values = []

        for _ in range(n_simulations):
            # Randomly sample returns with replacement
            simulated_returns = np.random.choice(trade_returns, size=len(trade_returns), replace=True)

            # Calculate final value
            final_value = self.initial_capital * np.prod(1 + simulated_returns)
            final_values.append(final_value)

        final_values = np.array(final_values)

        return {
            'mean_final_value': np.mean(final_values),
            'median_final_value': np.median(final_values),
            'std_final_value': np.std(final_values),
            'min_final_value': np.min(final_values),
            'max_final_value': np.max(final_values),
            'percentile_5': np.percentile(final_values, 5),
            'percentile_25': np.percentile(final_values, 25),
            'percentile_75': np.percentile(final_values, 75),
            'percentile_95': np.percentile(final_values, 95),
            'probability_of_profit': np.mean(final_values > self.initial_capital)
        }


def walk_forward_optimization(
    data: pd.DataFrame,
    strategy: Callable,
    param_grid: Dict[str, List[Any]],
    in_sample_period: int = 252,  # 1 year
    out_sample_period: int = 63  # 3 months
) -> Dict[str, Any]:
    """
    Walk-forward optimization to avoid overfitting.

    Args:
        data: Historical data
        strategy: Strategy function
        param_grid: Dictionary of parameter names to lists of values
        in_sample_period: Days for in-sample optimization
        out_sample_period: Days for out-of-sample testing

    Returns:
        Dictionary with optimization results
    """
    # TODO: Implement walk-forward optimization
    # 1. Split data into windows
    # 2. For each window:
    #    a. Optimize parameters on in-sample
    #    b. Test on out-of-sample
    # 3. Aggregate results

    return {
        'best_params': {},
        'in_sample_performance': {},
        'out_sample_performance': {},
        'degradation': 0.0
    }


if __name__ == "__main__":
    # Example usage
    print("=== Backtesting Engine Test ===\n")

    # Generate sample data
    dates = pd.date_range('2020-01-01', '2024-12-31', freq='D')
    np.random.seed(42)

    data = pd.DataFrame({
        'open': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'high': 102 + np.cumsum(np.random.randn(len(dates)) * 2),
        'low': 98 + np.cumsum(np.random.randn(len(dates)) * 2),
        'close': 100 + np.cumsum(np.random.randn(len(dates)) * 2),
        'volume': np.random.randint(1e6, 10e6, len(dates))
    }, index=dates)

    # Define simple moving average crossover strategy
    def ma_crossover_strategy(data, index, params):
        """Simple MA crossover strategy"""
        if index < params['long_ma']:
            return None

        short_ma = data['close'].iloc[index - params['short_ma']:index].mean()
        long_ma = data['close'].iloc[index - params['long_ma']:index].mean()

        # Previous values
        if index > params['long_ma']:
            prev_short = data['close'].iloc[index - params['short_ma'] - 1:index - 1].mean()
            prev_long = data['close'].iloc[index - params['long_ma'] - 1:index - 1].mean()

            # Crossover signals
            if prev_short <= prev_long and short_ma > long_ma:
                # Buy signal
                return Order(
                    symbol='TEST',
                    side='buy',
                    quantity=10,
                    order_type=OrderType.MARKET,
                    timestamp=data.index[index]
                )

            elif prev_short >= prev_long and short_ma < long_ma:
                # Sell signal
                return Order(
                    symbol='TEST',
                    side='sell',
                    quantity=10,
                    order_type=OrderType.MARKET,
                    timestamp=data.index[index]
                )

        return None

    # Run backtest
    backtester = Backtester(initial_capital=100000)
    results = backtester.run_backtest(
        data,
        ma_crossover_strategy,
        {'short_ma': 20, 'long_ma': 50}
    )

    # Print results
    print("Backtest Results:")
    print(f"  Total Return: {results.total_return:.2%}")
    print(f"  Annual Return: {results.annual_return:.2%}")
    print(f"  Sharpe Ratio: {results.sharpe_ratio:.2f}")
    print(f"  Sortino Ratio: {results.sortino_ratio:.2f}")
    print(f"  Max Drawdown: {results.max_drawdown:.2%}")
    print(f"  Win Rate: {results.win_rate:.2%}")
    print(f"  Profit Factor: {results.profit_factor:.2f}")
    print(f"  Total Trades: {results.total_trades}")
    print(f"  Winning Trades: {results.winning_trades}")
    print(f"  Losing Trades: {results.losing_trades}")
    print(f"  Avg Win: ${results.avg_win:.2f}")
    print(f"  Avg Loss: ${results.avg_loss:.2f}")

    # Monte Carlo simulation
    print("\n=== Monte Carlo Simulation (1000 runs) ===")
    mc_results = backtester.monte_carlo_simulation(results, n_simulations=1000)

    print(f"  Mean Final Value: ${mc_results['mean_final_value']:,.2f}")
    print(f"  Median Final Value: ${mc_results['median_final_value']:,.2f}")
    print(f"  5th Percentile: ${mc_results['percentile_5']:,.2f}")
    print(f"  95th Percentile: ${mc_results['percentile_95']:,.2f}")
    print(f"  Probability of Profit: {mc_results['probability_of_profit']:.1%}")
