#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION TOOLS SUITE - FINANCIAL TOOLKIT
================================================================================
Comprehensive financial analysis and calculation tools. Provides functions for
investment analysis, risk assessment, portfolio management, and financial metrics.

FEATURES:
- Time Value of Money (TVM) calculations
- Investment return metrics (ROI, IRR, NPV)
- Risk metrics (VaR, Sharpe ratio, Beta)
- Portfolio analysis and optimization
- Bond pricing and yield calculations
- Option pricing (Black-Scholes)
- Financial ratios and statements analysis
- Loan/mortgage calculations
- Currency conversion helpers

All calculations use pure Python - no external dependencies required.

Usage:
    from tools_suite.finance.financial_toolkit import FinancialToolkit
    ft = FinancialToolkit()
    npv = ft.net_present_value(0.10, [-1000, 300, 400, 500])
================================================================================
"""

# =============================================================================
# IMPORTS
# =============================================================================

import math                      # Mathematical functions
import statistics                # Statistical calculations
from typing import List, Dict, Tuple, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json


# =============================================================================
# ENUMERATIONS
# =============================================================================

class CompoundingFrequency(Enum):
    """Compounding frequency options."""
    ANNUAL = 1
    SEMI_ANNUAL = 2
    QUARTERLY = 4
    MONTHLY = 12
    WEEKLY = 52
    DAILY = 365
    CONTINUOUS = 0  # Special case


class RiskLevel(Enum):
    """Risk level classifications."""
    VERY_LOW = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    VERY_HIGH = 5


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Investment:
    """
    Represents an investment holding.

    Attributes:
        symbol: Ticker symbol or identifier
        name: Investment name
        quantity: Number of shares/units
        purchase_price: Price per share at purchase
        current_price: Current price per share
        purchase_date: Date of purchase
        asset_class: Type of asset (stock, bond, etc.)
    """
    symbol: str                              # Ticker symbol
    name: str                                # Full name
    quantity: float                          # Shares/units
    purchase_price: float                    # Purchase price per unit
    current_price: float                     # Current price per unit
    purchase_date: str = ""                  # YYYY-MM-DD
    asset_class: str = "stock"               # Asset type

    @property
    def cost_basis(self) -> float:
        """Total cost of investment."""
        return self.quantity * self.purchase_price

    @property
    def current_value(self) -> float:
        """Current market value."""
        return self.quantity * self.current_price

    @property
    def gain_loss(self) -> float:
        """Unrealized gain or loss."""
        return self.current_value - self.cost_basis

    @property
    def return_percent(self) -> float:
        """Return as percentage."""
        if self.cost_basis == 0:
            return 0.0
        return (self.gain_loss / self.cost_basis) * 100


@dataclass
class Portfolio:
    """
    Represents an investment portfolio.

    Attributes:
        name: Portfolio name
        investments: List of Investment objects
        cash: Cash balance
        currency: Base currency
    """
    name: str                                # Portfolio name
    investments: List[Investment] = field(default_factory=list)
    cash: float = 0.0                        # Cash balance
    currency: str = "USD"                    # Base currency

    @property
    def total_value(self) -> float:
        """Total portfolio value including cash."""
        return sum(inv.current_value for inv in self.investments) + self.cash

    @property
    def total_cost(self) -> float:
        """Total cost basis of investments."""
        return sum(inv.cost_basis for inv in self.investments)

    @property
    def total_gain_loss(self) -> float:
        """Total unrealized gain/loss."""
        return sum(inv.gain_loss for inv in self.investments)

    def add_investment(self, investment: Investment):
        """Add investment to portfolio."""
        self.investments.append(investment)

    def get_allocation(self) -> Dict[str, float]:
        """Get asset allocation percentages."""
        total = self.total_value
        if total == 0:
            return {}

        allocation = {}
        for inv in self.investments:
            if inv.asset_class not in allocation:
                allocation[inv.asset_class] = 0
            allocation[inv.asset_class] += inv.current_value / total * 100

        if self.cash > 0:
            allocation['cash'] = self.cash / total * 100

        return allocation


@dataclass
class Loan:
    """
    Represents a loan or mortgage.

    Attributes:
        principal: Loan amount
        annual_rate: Annual interest rate (as decimal)
        term_months: Loan term in months
        start_date: Loan start date
    """
    principal: float                         # Loan amount
    annual_rate: float                       # Annual interest rate
    term_months: int                         # Term in months
    start_date: str = ""                     # YYYY-MM-DD

    @property
    def monthly_rate(self) -> float:
        """Monthly interest rate."""
        return self.annual_rate / 12

    @property
    def monthly_payment(self) -> float:
        """Calculate monthly payment."""
        r = self.monthly_rate
        n = self.term_months
        if r == 0:
            return self.principal / n
        return self.principal * (r * (1 + r)**n) / ((1 + r)**n - 1)

    @property
    def total_payment(self) -> float:
        """Total amount paid over loan life."""
        return self.monthly_payment * self.term_months

    @property
    def total_interest(self) -> float:
        """Total interest paid."""
        return self.total_payment - self.principal


# =============================================================================
# FINANCIAL TOOLKIT
# =============================================================================

class FinancialToolkit:
    """
    Comprehensive financial calculations toolkit.

    Provides methods for:
    - Time value of money
    - Investment analysis
    - Risk metrics
    - Portfolio analysis
    - Loan calculations
    """

    # -------------------------------------------------------------------------
    # TIME VALUE OF MONEY
    # -------------------------------------------------------------------------

    def future_value(self, pv: float, rate: float, periods: int,
                     compounding: CompoundingFrequency = CompoundingFrequency.ANNUAL) -> float:
        """
        Calculate future value of a present sum.

        Formula: FV = PV × (1 + r/n)^(n×t)

        Args:
            pv: Present value
            rate: Annual interest rate (decimal)
            periods: Number of years
            compounding: Compounding frequency

        Returns:
            Future value
        """
        if compounding == CompoundingFrequency.CONTINUOUS:
            # FV = PV × e^(r×t)
            return pv * math.exp(rate * periods)
        else:
            n = compounding.value
            return pv * (1 + rate/n) ** (n * periods)

    def present_value(self, fv: float, rate: float, periods: int,
                      compounding: CompoundingFrequency = CompoundingFrequency.ANNUAL) -> float:
        """
        Calculate present value of a future sum.

        Formula: PV = FV / (1 + r/n)^(n×t)

        Args:
            fv: Future value
            rate: Annual interest rate (decimal)
            periods: Number of years
            compounding: Compounding frequency

        Returns:
            Present value
        """
        if compounding == CompoundingFrequency.CONTINUOUS:
            return fv * math.exp(-rate * periods)
        else:
            n = compounding.value
            return fv / (1 + rate/n) ** (n * periods)

    def future_value_annuity(self, payment: float, rate: float,
                              periods: int, annuity_due: bool = False) -> float:
        """
        Calculate future value of an annuity.

        Regular annuity: payments at end of each period
        Annuity due: payments at beginning of each period

        Args:
            payment: Regular payment amount
            rate: Interest rate per period
            periods: Number of periods
            annuity_due: If True, payments at beginning

        Returns:
            Future value of annuity
        """
        if rate == 0:
            return payment * periods

        fv = payment * ((1 + rate)**periods - 1) / rate

        if annuity_due:
            fv *= (1 + rate)

        return fv

    def present_value_annuity(self, payment: float, rate: float,
                               periods: int, annuity_due: bool = False) -> float:
        """
        Calculate present value of an annuity.

        Args:
            payment: Regular payment amount
            rate: Interest rate per period
            periods: Number of periods
            annuity_due: If True, payments at beginning

        Returns:
            Present value of annuity
        """
        if rate == 0:
            return payment * periods

        pv = payment * (1 - (1 + rate)**-periods) / rate

        if annuity_due:
            pv *= (1 + rate)

        return pv

    def net_present_value(self, rate: float, cash_flows: List[float]) -> float:
        """
        Calculate Net Present Value (NPV).

        NPV is the sum of present values of all cash flows.
        Positive NPV indicates a profitable investment.

        Args:
            rate: Discount rate per period
            cash_flows: List of cash flows (negative for outflows)

        Returns:
            Net present value
        """
        npv = 0.0
        for t, cf in enumerate(cash_flows):
            npv += cf / (1 + rate) ** t
        return npv

    def internal_rate_of_return(self, cash_flows: List[float],
                                 guess: float = 0.1,
                                 tolerance: float = 1e-6,
                                 max_iterations: int = 100) -> float:
        """
        Calculate Internal Rate of Return (IRR).

        IRR is the discount rate that makes NPV = 0.
        Uses Newton-Raphson method for calculation.

        Args:
            cash_flows: List of cash flows
            guess: Initial rate guess
            tolerance: Convergence tolerance
            max_iterations: Maximum iterations

        Returns:
            Internal rate of return
        """
        rate = guess

        for _ in range(max_iterations):
            # Calculate NPV and its derivative
            npv = self.net_present_value(rate, cash_flows)

            # Derivative of NPV with respect to rate
            npv_derivative = 0.0
            for t, cf in enumerate(cash_flows):
                if t > 0:
                    npv_derivative -= t * cf / (1 + rate) ** (t + 1)

            if abs(npv_derivative) < 1e-10:
                break

            # Newton-Raphson update
            new_rate = rate - npv / npv_derivative

            if abs(new_rate - rate) < tolerance:
                return new_rate

            rate = new_rate

        return rate

    def payback_period(self, initial_investment: float,
                        cash_flows: List[float]) -> float:
        """
        Calculate payback period.

        Time required to recover the initial investment.

        Args:
            initial_investment: Initial outlay (positive number)
            cash_flows: List of periodic cash inflows

        Returns:
            Payback period in periods
        """
        cumulative = -initial_investment

        for t, cf in enumerate(cash_flows):
            cumulative += cf
            if cumulative >= 0:
                # Calculate fractional period
                if cf > 0:
                    return t + (cumulative - cf) / (-cf) + 1
                return t + 1

        return float('inf')  # Never pays back

    def discounted_payback_period(self, initial_investment: float,
                                   cash_flows: List[float],
                                   rate: float) -> float:
        """
        Calculate discounted payback period.

        Payback period using present values.

        Args:
            initial_investment: Initial outlay
            cash_flows: List of cash inflows
            rate: Discount rate

        Returns:
            Discounted payback period
        """
        cumulative = -initial_investment

        for t, cf in enumerate(cash_flows):
            pv_cf = cf / (1 + rate) ** (t + 1)
            cumulative += pv_cf
            if cumulative >= 0:
                return t + 1

        return float('inf')

    # -------------------------------------------------------------------------
    # INVESTMENT RETURNS
    # -------------------------------------------------------------------------

    def roi(self, initial_value: float, final_value: float) -> float:
        """
        Calculate Return on Investment (ROI).

        Formula: ROI = (Final - Initial) / Initial × 100

        Args:
            initial_value: Starting value
            final_value: Ending value

        Returns:
            ROI as percentage
        """
        if initial_value == 0:
            return 0.0
        return ((final_value - initial_value) / initial_value) * 100

    def annualized_return(self, total_return: float, years: float) -> float:
        """
        Calculate annualized return (CAGR).

        Compound Annual Growth Rate.
        Formula: CAGR = (1 + total_return)^(1/years) - 1

        Args:
            total_return: Total return as decimal
            years: Investment period in years

        Returns:
            Annualized return as decimal
        """
        if years <= 0:
            return 0.0
        return (1 + total_return) ** (1 / years) - 1

    def holding_period_return(self, beginning_value: float,
                               ending_value: float,
                               income: float = 0) -> float:
        """
        Calculate Holding Period Return (HPR).

        Includes both capital gains and income.

        Args:
            beginning_value: Starting value
            ending_value: Ending value
            income: Dividends/interest received

        Returns:
            HPR as decimal
        """
        if beginning_value == 0:
            return 0.0
        return (ending_value - beginning_value + income) / beginning_value

    def time_weighted_return(self, period_returns: List[float]) -> float:
        """
        Calculate Time-Weighted Return (TWR).

        Eliminates effect of cash flows, measures manager performance.

        Args:
            period_returns: List of periodic returns (as decimals)

        Returns:
            TWR as decimal
        """
        if not period_returns:
            return 0.0

        cumulative = 1.0
        for r in period_returns:
            cumulative *= (1 + r)

        return cumulative - 1

    def money_weighted_return(self, cash_flows: List[Tuple[float, float]],
                               ending_value: float) -> float:
        """
        Calculate Money-Weighted Return (MWR).

        Similar to IRR, accounts for timing of cash flows.

        Args:
            cash_flows: List of (time, amount) tuples
            ending_value: Final portfolio value

        Returns:
            MWR as decimal
        """
        # Build cash flow list with ending value
        all_flows = []
        times = []
        for t, cf in cash_flows:
            all_flows.append(cf)
            times.append(t)

        # Add ending value as final cash flow
        if times:
            all_flows.append(-ending_value)
            times.append(max(times) + 1)

        return self.internal_rate_of_return(all_flows)

    # -------------------------------------------------------------------------
    # RISK METRICS
    # -------------------------------------------------------------------------

    def standard_deviation(self, returns: List[float]) -> float:
        """
        Calculate standard deviation of returns.

        Measures volatility/risk.

        Args:
            returns: List of periodic returns

        Returns:
            Standard deviation
        """
        if len(returns) < 2:
            return 0.0
        return statistics.stdev(returns)

    def variance(self, returns: List[float]) -> float:
        """
        Calculate variance of returns.

        Args:
            returns: List of periodic returns

        Returns:
            Variance
        """
        if len(returns) < 2:
            return 0.0
        return statistics.variance(returns)

    def sharpe_ratio(self, returns: List[float], risk_free_rate: float) -> float:
        """
        Calculate Sharpe Ratio.

        Measures risk-adjusted return.
        Formula: (Rp - Rf) / σp

        Args:
            returns: List of portfolio returns
            risk_free_rate: Risk-free rate for the period

        Returns:
            Sharpe ratio
        """
        if len(returns) < 2:
            return 0.0

        avg_return = statistics.mean(returns)
        std_dev = self.standard_deviation(returns)

        if std_dev == 0:
            return 0.0

        return (avg_return - risk_free_rate) / std_dev

    def sortino_ratio(self, returns: List[float], risk_free_rate: float,
                       target_return: float = 0) -> float:
        """
        Calculate Sortino Ratio.

        Like Sharpe but only considers downside risk.

        Args:
            returns: List of portfolio returns
            risk_free_rate: Risk-free rate
            target_return: Minimum acceptable return

        Returns:
            Sortino ratio
        """
        if len(returns) < 2:
            return 0.0

        avg_return = statistics.mean(returns)

        # Calculate downside deviation
        downside_returns = [r for r in returns if r < target_return]
        if not downside_returns:
            return float('inf')  # No downside

        downside_deviation = math.sqrt(
            sum((r - target_return)**2 for r in downside_returns) / len(downside_returns)
        )

        if downside_deviation == 0:
            return float('inf')

        return (avg_return - risk_free_rate) / downside_deviation

    def beta(self, asset_returns: List[float],
              market_returns: List[float]) -> float:
        """
        Calculate Beta coefficient.

        Measures systematic risk relative to market.
        Beta = Cov(Ra, Rm) / Var(Rm)

        Args:
            asset_returns: List of asset returns
            market_returns: List of market returns

        Returns:
            Beta coefficient
        """
        if len(asset_returns) != len(market_returns) or len(asset_returns) < 2:
            return 0.0

        # Calculate covariance
        mean_asset = statistics.mean(asset_returns)
        mean_market = statistics.mean(market_returns)

        covariance = sum(
            (asset_returns[i] - mean_asset) * (market_returns[i] - mean_market)
            for i in range(len(asset_returns))
        ) / (len(asset_returns) - 1)

        market_variance = self.variance(market_returns)

        if market_variance == 0:
            return 0.0

        return covariance / market_variance

    def alpha(self, asset_return: float, market_return: float,
               risk_free_rate: float, beta: float) -> float:
        """
        Calculate Jensen's Alpha.

        Measures excess return vs. CAPM expected return.

        Args:
            asset_return: Actual asset return
            market_return: Market return
            risk_free_rate: Risk-free rate
            beta: Asset beta

        Returns:
            Alpha value
        """
        expected_return = risk_free_rate + beta * (market_return - risk_free_rate)
        return asset_return - expected_return

    def value_at_risk(self, returns: List[float],
                       confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR).

        Maximum expected loss at given confidence level.
        Uses historical simulation method.

        Args:
            returns: List of historical returns
            confidence: Confidence level (e.g., 0.95)

        Returns:
            VaR as percentage loss
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        index = int((1 - confidence) * len(sorted_returns))
        return -sorted_returns[index]  # Return positive number

    def conditional_var(self, returns: List[float],
                         confidence: float = 0.95) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).

        Average loss beyond VaR.

        Args:
            returns: List of historical returns
            confidence: Confidence level

        Returns:
            CVaR as percentage loss
        """
        if not returns:
            return 0.0

        sorted_returns = sorted(returns)
        cutoff_index = int((1 - confidence) * len(sorted_returns))

        tail_losses = sorted_returns[:cutoff_index + 1]
        if not tail_losses:
            return 0.0

        return -statistics.mean(tail_losses)

    def max_drawdown(self, values: List[float]) -> Tuple[float, int, int]:
        """
        Calculate Maximum Drawdown.

        Largest peak-to-trough decline.

        Args:
            values: List of portfolio values over time

        Returns:
            Tuple of (max_drawdown, peak_index, trough_index)
        """
        if not values:
            return (0.0, 0, 0)

        max_dd = 0.0
        peak_idx = 0
        trough_idx = 0
        peak = values[0]
        peak_i = 0

        for i, value in enumerate(values):
            if value > peak:
                peak = value
                peak_i = i
            else:
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
                    peak_idx = peak_i
                    trough_idx = i

        return (max_dd, peak_idx, trough_idx)

    # -------------------------------------------------------------------------
    # LOAN AND MORTGAGE CALCULATIONS
    # -------------------------------------------------------------------------

    def mortgage_payment(self, principal: float, annual_rate: float,
                          term_years: int) -> float:
        """
        Calculate monthly mortgage payment.

        Uses standard amortization formula.

        Args:
            principal: Loan amount
            annual_rate: Annual interest rate (decimal)
            term_years: Loan term in years

        Returns:
            Monthly payment amount
        """
        monthly_rate = annual_rate / 12
        n_payments = term_years * 12

        if monthly_rate == 0:
            return principal / n_payments

        return principal * (
            monthly_rate * (1 + monthly_rate)**n_payments
        ) / (
            (1 + monthly_rate)**n_payments - 1
        )

    def amortization_schedule(self, principal: float, annual_rate: float,
                               term_years: int) -> List[Dict[str, float]]:
        """
        Generate amortization schedule.

        Shows payment breakdown by period.

        Args:
            principal: Loan amount
            annual_rate: Annual interest rate
            term_years: Loan term in years

        Returns:
            List of payment dictionaries
        """
        monthly_payment = self.mortgage_payment(principal, annual_rate, term_years)
        monthly_rate = annual_rate / 12
        balance = principal
        schedule = []

        for month in range(1, term_years * 12 + 1):
            interest_payment = balance * monthly_rate
            principal_payment = monthly_payment - interest_payment
            balance -= principal_payment

            schedule.append({
                'month': month,
                'payment': monthly_payment,
                'principal': principal_payment,
                'interest': interest_payment,
                'balance': max(0, balance)
            })

        return schedule

    def loan_affordability(self, monthly_income: float,
                            debt_to_income_ratio: float = 0.36,
                            annual_rate: float = 0.05,
                            term_years: int = 30) -> float:
        """
        Calculate maximum affordable loan amount.

        Args:
            monthly_income: Gross monthly income
            debt_to_income_ratio: Max DTI ratio
            annual_rate: Expected interest rate
            term_years: Loan term

        Returns:
            Maximum loan amount
        """
        max_payment = monthly_income * debt_to_income_ratio
        monthly_rate = annual_rate / 12
        n_payments = term_years * 12

        if monthly_rate == 0:
            return max_payment * n_payments

        return max_payment * (
            (1 + monthly_rate)**n_payments - 1
        ) / (
            monthly_rate * (1 + monthly_rate)**n_payments
        )

    # -------------------------------------------------------------------------
    # BOND CALCULATIONS
    # -------------------------------------------------------------------------

    def bond_price(self, face_value: float, coupon_rate: float,
                    yield_rate: float, years_to_maturity: int,
                    payments_per_year: int = 2) -> float:
        """
        Calculate bond price.

        Price = PV of coupon payments + PV of face value

        Args:
            face_value: Bond face/par value
            coupon_rate: Annual coupon rate
            yield_rate: Required yield/market rate
            years_to_maturity: Years until maturity
            payments_per_year: Coupon frequency

        Returns:
            Bond price
        """
        coupon_payment = (face_value * coupon_rate) / payments_per_year
        n_payments = years_to_maturity * payments_per_year
        rate_per_period = yield_rate / payments_per_year

        # PV of coupons
        pv_coupons = self.present_value_annuity(
            coupon_payment, rate_per_period, n_payments
        )

        # PV of face value
        pv_face = face_value / (1 + rate_per_period)**n_payments

        return pv_coupons + pv_face

    def bond_yield_to_maturity(self, price: float, face_value: float,
                                coupon_rate: float, years_to_maturity: int,
                                payments_per_year: int = 2) -> float:
        """
        Calculate yield to maturity.

        Uses iterative approach.

        Args:
            price: Current bond price
            face_value: Face value
            coupon_rate: Coupon rate
            years_to_maturity: Years to maturity
            payments_per_year: Coupon frequency

        Returns:
            Yield to maturity
        """
        # Use Newton-Raphson or bisection
        low, high = 0.0, 1.0
        tolerance = 0.0001

        while high - low > tolerance:
            mid = (low + high) / 2
            calc_price = self.bond_price(
                face_value, coupon_rate, mid, years_to_maturity, payments_per_year
            )

            if calc_price > price:
                low = mid
            else:
                high = mid

        return (low + high) / 2

    def bond_duration(self, face_value: float, coupon_rate: float,
                       yield_rate: float, years_to_maturity: int,
                       payments_per_year: int = 2) -> float:
        """
        Calculate Macaulay duration.

        Weighted average time to receive cash flows.

        Args:
            face_value: Face value
            coupon_rate: Coupon rate
            yield_rate: Yield rate
            years_to_maturity: Years to maturity
            payments_per_year: Coupon frequency

        Returns:
            Macaulay duration in years
        """
        price = self.bond_price(
            face_value, coupon_rate, yield_rate, years_to_maturity, payments_per_year
        )

        coupon_payment = (face_value * coupon_rate) / payments_per_year
        n_payments = years_to_maturity * payments_per_year
        rate_per_period = yield_rate / payments_per_year

        weighted_sum = 0.0
        for t in range(1, n_payments + 1):
            cf = coupon_payment
            if t == n_payments:
                cf += face_value

            pv = cf / (1 + rate_per_period)**t
            weighted_sum += (t / payments_per_year) * pv

        return weighted_sum / price

    # -------------------------------------------------------------------------
    # OPTION PRICING (Black-Scholes)
    # -------------------------------------------------------------------------

    def _norm_cdf(self, x: float) -> float:
        """Standard normal cumulative distribution function."""
        return (1.0 + math.erf(x / math.sqrt(2.0))) / 2.0

    def black_scholes_call(self, S: float, K: float, T: float,
                            r: float, sigma: float) -> float:
        """
        Calculate Black-Scholes call option price.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Call option price
        """
        if T <= 0:
            return max(0, S - K)

        d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        call_price = S * self._norm_cdf(d1) - K * math.exp(-r * T) * self._norm_cdf(d2)
        return call_price

    def black_scholes_put(self, S: float, K: float, T: float,
                           r: float, sigma: float) -> float:
        """
        Calculate Black-Scholes put option price.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free rate
            sigma: Volatility

        Returns:
            Put option price
        """
        if T <= 0:
            return max(0, K - S)

        d1 = (math.log(S / K) + (r + sigma**2 / 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        put_price = K * math.exp(-r * T) * self._norm_cdf(-d2) - S * self._norm_cdf(-d1)
        return put_price

    # -------------------------------------------------------------------------
    # FINANCIAL RATIOS
    # -------------------------------------------------------------------------

    def current_ratio(self, current_assets: float,
                       current_liabilities: float) -> float:
        """
        Calculate current ratio (liquidity).

        Args:
            current_assets: Total current assets
            current_liabilities: Total current liabilities

        Returns:
            Current ratio
        """
        if current_liabilities == 0:
            return float('inf')
        return current_assets / current_liabilities

    def quick_ratio(self, current_assets: float, inventory: float,
                     current_liabilities: float) -> float:
        """
        Calculate quick ratio (acid-test ratio).

        Args:
            current_assets: Total current assets
            inventory: Inventory value
            current_liabilities: Total current liabilities

        Returns:
            Quick ratio
        """
        if current_liabilities == 0:
            return float('inf')
        return (current_assets - inventory) / current_liabilities

    def debt_to_equity(self, total_debt: float, total_equity: float) -> float:
        """
        Calculate debt-to-equity ratio.

        Args:
            total_debt: Total liabilities
            total_equity: Total equity

        Returns:
            D/E ratio
        """
        if total_equity == 0:
            return float('inf')
        return total_debt / total_equity

    def return_on_equity(self, net_income: float, total_equity: float) -> float:
        """
        Calculate Return on Equity (ROE).

        Args:
            net_income: Net income
            total_equity: Total equity

        Returns:
            ROE as decimal
        """
        if total_equity == 0:
            return 0.0
        return net_income / total_equity

    def return_on_assets(self, net_income: float, total_assets: float) -> float:
        """
        Calculate Return on Assets (ROA).

        Args:
            net_income: Net income
            total_assets: Total assets

        Returns:
            ROA as decimal
        """
        if total_assets == 0:
            return 0.0
        return net_income / total_assets

    def price_to_earnings(self, stock_price: float,
                           earnings_per_share: float) -> float:
        """
        Calculate P/E ratio.

        Args:
            stock_price: Current stock price
            earnings_per_share: EPS

        Returns:
            P/E ratio
        """
        if earnings_per_share == 0:
            return float('inf')
        return stock_price / earnings_per_share

    def earnings_per_share(self, net_income: float,
                            shares_outstanding: float) -> float:
        """
        Calculate Earnings Per Share (EPS).

        Args:
            net_income: Net income
            shares_outstanding: Number of shares

        Returns:
            EPS
        """
        if shares_outstanding == 0:
            return 0.0
        return net_income / shares_outstanding


# =============================================================================
# DEMO
# =============================================================================

def run_demo():
    """Demonstrate the financial toolkit."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               ELECTRODUCTION FINANCIAL TOOLKIT                                ║
║                    Finance & Investment Demo                                  ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    ft = FinancialToolkit()

    # Time Value of Money
    print("[*] TIME VALUE OF MONEY")
    print("-" * 60)
    pv = 10000
    rate = 0.08
    years = 5
    fv = ft.future_value(pv, rate, years)
    print(f"  Present Value: ${pv:,.2f}")
    print(f"  Rate: {rate*100:.1f}% annual")
    print(f"  Years: {years}")
    print(f"  Future Value: ${fv:,.2f}")

    # NPV and IRR
    print("\n[*] INVESTMENT ANALYSIS")
    print("-" * 60)
    cash_flows = [-100000, 30000, 35000, 40000, 45000]
    print(f"  Cash Flows: {cash_flows}")

    npv = ft.net_present_value(0.10, cash_flows)
    irr = ft.internal_rate_of_return(cash_flows)
    payback = ft.payback_period(100000, cash_flows[1:])

    print(f"  NPV (at 10%): ${npv:,.2f}")
    print(f"  IRR: {irr*100:.2f}%")
    print(f"  Payback Period: {payback:.2f} years")

    # Risk Metrics
    print("\n[*] RISK ANALYSIS")
    print("-" * 60)
    returns = [0.05, -0.02, 0.08, 0.03, -0.01, 0.06, 0.04, -0.03, 0.07, 0.02]
    print(f"  Monthly Returns: {returns}")

    sharpe = ft.sharpe_ratio(returns, 0.002)  # 0.2% risk-free monthly
    var = ft.value_at_risk(returns, 0.95)
    std = ft.standard_deviation(returns)

    print(f"  Volatility (Std Dev): {std*100:.2f}%")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f"  VaR (95%): {var*100:.2f}%")

    # Mortgage Calculation
    print("\n[*] MORTGAGE ANALYSIS")
    print("-" * 60)
    principal = 300000
    annual_rate = 0.065
    term_years = 30

    monthly_payment = ft.mortgage_payment(principal, annual_rate, term_years)
    total_paid = monthly_payment * 12 * term_years
    total_interest = total_paid - principal

    print(f"  Loan Amount: ${principal:,.2f}")
    print(f"  Rate: {annual_rate*100:.2f}%")
    print(f"  Term: {term_years} years")
    print(f"  Monthly Payment: ${monthly_payment:,.2f}")
    print(f"  Total Interest: ${total_interest:,.2f}")

    # Bond Pricing
    print("\n[*] BOND ANALYSIS")
    print("-" * 60)
    face = 1000
    coupon = 0.05
    yield_rate = 0.04
    maturity = 10

    price = ft.bond_price(face, coupon, yield_rate, maturity)
    duration = ft.bond_duration(face, coupon, yield_rate, maturity)

    print(f"  Face Value: ${face:,.2f}")
    print(f"  Coupon Rate: {coupon*100:.1f}%")
    print(f"  Yield: {yield_rate*100:.1f}%")
    print(f"  Bond Price: ${price:,.2f}")
    print(f"  Duration: {duration:.2f} years")

    # Option Pricing
    print("\n[*] OPTION PRICING (Black-Scholes)")
    print("-" * 60)
    S = 100  # Stock price
    K = 105  # Strike
    T = 0.5  # 6 months
    r = 0.05  # Risk-free rate
    sigma = 0.20  # Volatility

    call = ft.black_scholes_call(S, K, T, r, sigma)
    put = ft.black_scholes_put(S, K, T, r, sigma)

    print(f"  Stock Price: ${S}")
    print(f"  Strike: ${K}")
    print(f"  Time to Expiry: {T*12:.0f} months")
    print(f"  Volatility: {sigma*100:.0f}%")
    print(f"  Call Price: ${call:.2f}")
    print(f"  Put Price: ${put:.2f}")

    print("\n[*] Demo completed!")


if __name__ == "__main__":
    run_demo()
