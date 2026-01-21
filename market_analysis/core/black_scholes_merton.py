"""
Black-Scholes-Merton Option Pricing Model with Enhanced Drift Calculations

Implements:
- Classic Black-Scholes for European options
- Merton jump-diffusion model
- Greeks calculation (Delta, Gamma, Theta, Vega, Rho)
- Implied volatility solver
- Multi-factor drift estimation
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize_scalar
from typing import Dict, Tuple, Optional
import warnings


class BlackScholesMerton:
    """
    Black-Scholes-Merton option pricing engine with enhanced drift calculations.
    """

    def __init__(self):
        self.risk_free_rate = 0.05  # Default 5% annual risk-free rate

    def black_scholes_call(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        Calculate Black-Scholes price for European call option.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free interest rate
            sigma: Volatility (annualized)

        Returns:
            Call option price
        """
        if T <= 0:
            return max(S - K, 0)

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call_price

    def black_scholes_put(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        Calculate Black-Scholes price for European put option.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free interest rate
            sigma: Volatility (annualized)

        Returns:
            Put option price
        """
        if T <= 0:
            return max(K - S, 0)

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        put_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put_price

    def calculate_greeks(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = 'call'
    ) -> Dict[str, float]:
        """
        Calculate option Greeks (sensitivities).

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free interest rate
            sigma: Volatility (annualized)
            option_type: 'call' or 'put'

        Returns:
            Dictionary containing Delta, Gamma, Theta, Vega, Rho
        """
        if T <= 0:
            return {
                'delta': 1.0 if option_type == 'call' and S > K else 0.0,
                'gamma': 0.0,
                'theta': 0.0,
                'vega': 0.0,
                'rho': 0.0
            }

        d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        # Delta
        if option_type == 'call':
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1

        # Gamma (same for call and put)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

        # Vega (same for call and put)
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # Divided by 100 for 1% change

        # Theta
        if option_type == 'call':
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        else:
            theta = (-S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                    + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365

        # Rho
        if option_type == 'call':
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }

    def implied_volatility(
        self,
        option_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = 'call',
        initial_guess: float = 0.3
    ) -> Optional[float]:
        """
        Calculate implied volatility using Newton-Raphson method.

        Args:
            option_price: Market price of option
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free interest rate
            option_type: 'call' or 'put'
            initial_guess: Starting volatility guess

        Returns:
            Implied volatility or None if failed to converge
        """
        if T <= 0:
            return None

        def objective(sigma):
            if option_type == 'call':
                model_price = self.black_scholes_call(S, K, T, r, sigma)
            else:
                model_price = self.black_scholes_put(S, K, T, r, sigma)
            return (model_price - option_price)**2

        try:
            result = minimize_scalar(objective, bounds=(0.01, 5.0), method='bounded')
            if result.success:
                return result.x
            return None
        except:
            return None

    def merton_jump_diffusion(
        self,
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        lambda_jump: float = 0.1,  # Jump frequency (per year)
        mu_jump: float = 0.0,      # Mean jump size
        sigma_jump: float = 0.1,    # Jump volatility
        n_terms: int = 50           # Number of Poisson terms
    ) -> float:
        """
        Merton jump-diffusion model for option pricing.

        Extends Black-Scholes to account for sudden price jumps.

        Args:
            S: Current stock price
            K: Strike price
            T: Time to expiration (years)
            r: Risk-free interest rate
            sigma: Diffusion volatility
            lambda_jump: Frequency of jumps per year
            mu_jump: Expected jump size (log scale)
            sigma_jump: Jump size volatility
            n_terms: Number of Poisson probability terms

        Returns:
            Option price under jump-diffusion
        """
        price = 0.0
        lambda_prime = lambda_jump * (1 + mu_jump)

        for n in range(n_terms):
            # Probability of n jumps
            prob_n = np.exp(-lambda_prime * T) * (lambda_prime * T)**n / np.math.factorial(n)

            # Adjusted volatility and rate for n jumps
            sigma_n = np.sqrt(sigma**2 + n * sigma_jump**2 / T)
            r_n = r - lambda_jump * mu_jump + n * np.log(1 + mu_jump) / T

            # Black-Scholes price with adjusted parameters
            bs_price = self.black_scholes_call(S, K, T, r_n, sigma_n)

            price += prob_n * bs_price

        return price

    def calculate_drift(
        self,
        prices: np.ndarray,
        time_delta: float = 1/252  # Default daily (252 trading days/year)
    ) -> Dict[str, float]:
        """
        Estimate drift and volatility from historical prices.

        Uses geometric Brownian motion: dS = μS dt + σS dW

        Args:
            prices: Array of historical prices
            time_delta: Time between observations (in years)

        Returns:
            Dictionary with drift, volatility, and annual estimates
        """
        if len(prices) < 2:
            raise ValueError("Need at least 2 prices for drift calculation")

        # Calculate log returns
        log_returns = np.log(prices[1:] / prices[:-1])

        # Estimate parameters
        mu = np.mean(log_returns) / time_delta  # Drift
        sigma = np.std(log_returns) / np.sqrt(time_delta)  # Volatility

        # Annualized values
        annual_return = (1 + np.mean(log_returns))**252 - 1
        annual_volatility = sigma * np.sqrt(252)

        return {
            'drift': mu,
            'volatility': sigma,
            'annual_return': annual_return,
            'annual_volatility': annual_volatility,
            'sharpe_ratio': annual_return / annual_volatility if annual_volatility > 0 else 0
        }

    def multi_factor_drift(
        self,
        prices: np.ndarray,
        factors: Dict[str, np.ndarray],
        time_delta: float = 1/252
    ) -> Dict[str, float]:
        """
        Enhanced drift calculation incorporating multiple factors.

        Extends simple drift to include factor loadings:
        Returns = α + β₁*Factor₁ + β₂*Factor₂ + ... + ε

        Args:
            prices: Array of historical prices
            factors: Dictionary of factor time series (e.g., {'market': [...], 'size': [...]})
            time_delta: Time between observations

        Returns:
            Dictionary with drift components and factor sensitivities
        """
        log_returns = np.log(prices[1:] / prices[:-1])

        # Ensure all factors have same length as returns
        factor_matrix = []
        factor_names = []
        for name, values in factors.items():
            if len(values) == len(log_returns):
                factor_matrix.append(values)
                factor_names.append(name)

        if len(factor_matrix) == 0:
            # Fall back to simple drift if no factors
            return self.calculate_drift(prices, time_delta)

        X = np.column_stack(factor_matrix)
        y = log_returns

        # Multiple regression: y = Xβ + ε
        try:
            # Add intercept
            X_with_intercept = np.column_stack([np.ones(len(X)), X])
            beta = np.linalg.lstsq(X_with_intercept, y, rcond=None)[0]

            # Predictions and residuals
            y_pred = X_with_intercept @ beta
            residuals = y - y_pred

            # R-squared
            ss_total = np.sum((y - np.mean(y))**2)
            ss_residual = np.sum(residuals**2)
            r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0

            result = {
                'alpha': beta[0] / time_delta,  # Excess return (drift)
                'residual_volatility': np.std(residuals) / np.sqrt(time_delta),
                'r_squared': r_squared
            }

            # Add factor loadings
            for i, name in enumerate(factor_names):
                result[f'beta_{name}'] = beta[i + 1]

            return result

        except np.linalg.LinAlgError:
            warnings.warn("Failed to compute multi-factor drift, using simple drift")
            return self.calculate_drift(prices, time_delta)


class HestonModel:
    """
    Heston stochastic volatility model.

    Models volatility as a stochastic process itself:
    dS = μS dt + √v S dW₁
    dv = κ(θ - v) dt + σ√v dW₂
    """

    def __init__(
        self,
        kappa: float = 2.0,    # Mean reversion speed
        theta: float = 0.04,   # Long-run variance
        sigma: float = 0.3,    # Volatility of volatility
        rho: float = -0.7      # Correlation between price and volatility
    ):
        self.kappa = kappa
        self.theta = theta
        self.sigma = sigma
        self.rho = rho

    def simulate_paths(
        self,
        S0: float,
        v0: float,
        T: float,
        r: float,
        n_steps: int = 252,
        n_paths: int = 1000
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Simulate stock price paths using Heston model.

        Args:
            S0: Initial stock price
            v0: Initial variance
            T: Time horizon (years)
            r: Risk-free rate
            n_steps: Number of time steps
            n_paths: Number of simulation paths

        Returns:
            Tuple of (price_paths, variance_paths)
        """
        dt = T / n_steps

        # Initialize arrays
        S = np.zeros((n_steps + 1, n_paths))
        v = np.zeros((n_steps + 1, n_paths))
        S[0] = S0
        v[0] = v0

        # Generate correlated Brownian motions
        for t in range(n_steps):
            # Generate independent normals
            Z1 = np.random.standard_normal(n_paths)
            Z2 = np.random.standard_normal(n_paths)

            # Make them correlated
            W1 = Z1
            W2 = self.rho * Z1 + np.sqrt(1 - self.rho**2) * Z2

            # Update variance (with reflection to keep positive)
            v[t + 1] = np.abs(
                v[t] + self.kappa * (self.theta - v[t]) * dt +
                self.sigma * np.sqrt(v[t]) * np.sqrt(dt) * W2
            )

            # Update stock price
            S[t + 1] = S[t] * np.exp(
                (r - 0.5 * v[t]) * dt + np.sqrt(v[t]) * np.sqrt(dt) * W1
            )

        return S, v


if __name__ == "__main__":
    # Example usage and tests
    bs = BlackScholesMerton()

    # Example 1: Price a call option
    S = 100  # Stock price
    K = 105  # Strike
    T = 0.5  # 6 months
    r = 0.05  # 5% risk-free rate
    sigma = 0.2  # 20% volatility

    call_price = bs.black_scholes_call(S, K, T, r, sigma)
    put_price = bs.black_scholes_put(S, K, T, r, sigma)

    print(f"Call price: ${call_price:.2f}")
    print(f"Put price: ${put_price:.2f}")

    # Example 2: Calculate Greeks
    greeks = bs.calculate_greeks(S, K, T, r, sigma, 'call')
    print(f"\nGreeks:")
    for greek, value in greeks.items():
        print(f"  {greek}: {value:.4f}")

    # Example 3: Implied volatility
    market_price = 5.0
    iv = bs.implied_volatility(market_price, S, K, T, r, 'call')
    print(f"\nImplied volatility: {iv:.2%}" if iv else "Failed to calculate IV")

    # Example 4: Drift calculation
    historical_prices = np.array([100, 102, 101, 105, 103, 107, 110])
    drift_params = bs.calculate_drift(historical_prices)
    print(f"\nDrift parameters:")
    for param, value in drift_params.items():
        print(f"  {param}: {value:.4f}")

    # Example 5: Heston model simulation
    heston = HestonModel()
    S_paths, v_paths = heston.simulate_paths(S0=100, v0=0.04, T=1.0, r=0.05, n_paths=10)
    print(f"\nHeston simulation (10 paths, 1 year):")
    print(f"  Final prices: {S_paths[-1]}")
    print(f"  Mean final price: ${np.mean(S_paths[-1]):.2f}")
