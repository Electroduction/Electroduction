"""
Behavioral Finance Factors Module

Models human psychology and decision-making patterns in markets:
- Investor demographics (age, gender, location)
- Personality traits (Big Five model)
- Psychological biases (fear, greed, FOMO, loss aversion)
- Herd behavior and sentiment
- Trust and reputation factors
- Trading behavior patterns
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta


class PersonalityTrait(Enum):
    """Big Five personality traits"""
    OPENNESS = "openness"
    CONSCIENTIOUSNESS = "conscientiousness"
    EXTRAVERSION = "extraversion"
    AGREEABLENESS = "agreeableness"
    NEUROTICISM = "neuroticism"


class InvestorType(Enum):
    """Types of market participants"""
    RETAIL = "retail"
    INSTITUTIONAL = "institutional"
    HIGH_FREQUENCY = "high_frequency"
    MARKET_MAKER = "market_maker"
    LONG_TERM = "long_term"


@dataclass
class InvestorProfile:
    """Profile of an investor or investor segment"""
    age: Optional[int] = None
    gender: Optional[str] = None
    location: Optional[str] = None
    occupation: Optional[str] = None
    income_level: Optional[str] = None
    education: Optional[str] = None

    # Big Five scores (0-100)
    openness: float = 50.0
    conscientiousness: float = 50.0
    extraversion: float = 50.0
    agreeableness: float = 50.0
    neuroticism: float = 50.0

    # Trading behavior
    trading_frequency: str = "medium"  # low, medium, high
    risk_tolerance: float = 0.5  # 0.0 (conservative) to 1.0 (aggressive)
    loss_aversion_coefficient: float = 2.0  # Typically 2-2.5x

    # Experience
    years_investing: int = 0
    previous_crashes_experienced: int = 0


class BehavioralFactorAnalyzer:
    """
    Analyzes behavioral finance factors and their impact on markets.
    """

    def __init__(self):
        # Sentiment thresholds
        self.extreme_fear_threshold = 20  # VIX-like scale
        self.extreme_greed_threshold = 80

        # Herd behavior parameters
        self.herd_threshold = 0.7  # % of traders moving same direction

    def calculate_fear_greed_index(
        self,
        vix: float,
        put_call_ratio: float,
        market_momentum: float,
        market_breadth: float,
        safe_haven_demand: float
    ) -> Dict[str, float]:
        """
        Calculate Fear & Greed Index combining multiple indicators.

        Args:
            vix: VIX volatility index (0-100)
            put_call_ratio: Put/Call volume ratio (0.5-2.0 typical)
            market_momentum: % stocks above 125-day MA (0-100)
            market_breadth: Advance/Decline ratio (0-100)
            safe_haven_demand: Treasury/Gold demand indicator (0-100)

        Returns:
            Dictionary with fear/greed score and components
        """
        # Normalize VIX (inverse: high VIX = fear = low score)
        vix_score = max(0, min(100, 100 - vix))

        # Put/Call ratio (high ratio = fear = low score)
        pc_score = max(0, min(100, 100 - (put_call_ratio - 0.5) * 100))

        # Market momentum (% stocks above MA)
        momentum_score = market_momentum

        # Market breadth (advances vs declines)
        breadth_score = market_breadth

        # Safe haven (inverse: high demand = fear)
        safe_haven_score = 100 - safe_haven_demand

        # Weighted average
        weights = {
            'vix': 0.30,
            'put_call': 0.20,
            'momentum': 0.25,
            'breadth': 0.15,
            'safe_haven': 0.10
        }

        fear_greed_score = (
            vix_score * weights['vix'] +
            pc_score * weights['put_call'] +
            momentum_score * weights['momentum'] +
            breadth_score * weights['breadth'] +
            safe_haven_score * weights['safe_haven']
        )

        # Classify sentiment
        if fear_greed_score < self.extreme_fear_threshold:
            sentiment = "Extreme Fear"
        elif fear_greed_score < 45:
            sentiment = "Fear"
        elif fear_greed_score < 55:
            sentiment = "Neutral"
        elif fear_greed_score < self.extreme_greed_threshold:
            sentiment = "Greed"
        else:
            sentiment = "Extreme Greed"

        return {
            'fear_greed_score': fear_greed_score,
            'sentiment': sentiment,
            'vix_component': vix_score,
            'put_call_component': pc_score,
            'momentum_component': momentum_score,
            'breadth_component': breadth_score,
            'safe_haven_component': safe_haven_score
        }

    def detect_herd_behavior(
        self,
        order_flow: pd.DataFrame,
        window: int = 20
    ) -> Dict[str, float]:
        """
        Detect herd behavior from order flow data.

        When large % of participants move together, often signals:
        - FOMO (during rallies)
        - Panic (during selloffs)
        - Potential reversals (contrarian signal)

        Args:
            order_flow: DataFrame with 'buy_volume', 'sell_volume', 'timestamp'
            window: Rolling window for analysis

        Returns:
            Dictionary with herd behavior metrics
        """
        # Calculate buy/sell imbalance
        total_volume = order_flow['buy_volume'] + order_flow['sell_volume']
        buy_ratio = order_flow['buy_volume'] / total_volume

        # Rolling statistics
        rolling_mean = buy_ratio.rolling(window).mean()
        rolling_std = buy_ratio.rolling(window).std()

        # Detect herding (low dispersion, extreme ratio)
        current_ratio = buy_ratio.iloc[-1]
        current_std = rolling_std.iloc[-1]

        # High conviction (> 70% one direction)
        is_herding = (current_ratio > 0.7 or current_ratio < 0.3) and current_std < 0.15

        # Direction
        if current_ratio > 0.6:
            direction = "bullish"
            intensity = (current_ratio - 0.5) * 2  # 0-1 scale
        elif current_ratio < 0.4:
            direction = "bearish"
            intensity = (0.5 - current_ratio) * 2
        else:
            direction = "neutral"
            intensity = 0

        return {
            'is_herding': is_herding,
            'buy_ratio': current_ratio,
            'direction': direction,
            'intensity': intensity,
            'volatility': current_std,
            'contrarian_signal': is_herding  # Extreme herding often precedes reversal
        }

    def calculate_trust_factor(
        self,
        company_data: Dict[str, any]
    ) -> float:
        """
        Calculate "trust factor" for a company based on multiple dimensions.

        Example: NVIDIA's high trust from reliability, innovation, reputation.

        Args:
            company_data: Dictionary with company metrics

        Returns:
            Trust score 0.0 (low trust) to 1.0 (high trust)
        """
        score = 0.0
        weights = 0.0

        # Brand reputation (surveys, ratings)
        if 'brand_reputation' in company_data:
            score += company_data['brand_reputation'] * 0.20
            weights += 0.20

        # Financial stability (credit rating)
        if 'credit_rating' in company_data:
            # AAA=1.0, AA=0.9, A=0.8, BBB=0.7, etc.
            rating_score = company_data.get('credit_rating_score', 0.5)
            score += rating_score * 0.15
            weights += 0.15

        # Innovation (R&D, patents)
        if 'innovation_score' in company_data:
            score += company_data['innovation_score'] * 0.15
            weights += 0.15

        # Management quality (tenure, track record)
        if 'management_score' in company_data:
            score += company_data['management_score'] * 0.15
            weights += 0.15

        # Customer satisfaction (NPS, reviews)
        if 'customer_satisfaction' in company_data:
            score += company_data['customer_satisfaction'] * 0.10
            weights += 0.10

        # Employee satisfaction (Glassdoor rating)
        if 'employee_satisfaction' in company_data:
            score += company_data['employee_satisfaction'] * 0.10
            weights += 0.10

        # Regulatory compliance (violations, fines)
        if 'compliance_score' in company_data:
            score += company_data['compliance_score'] * 0.10
            weights += 0.10

        # ESG score
        if 'esg_score' in company_data:
            score += company_data['esg_score'] * 0.05
            weights += 0.05

        if weights == 0:
            return 0.5  # Default neutral

        return score / weights

    def analyze_loss_aversion(
        self,
        returns: pd.Series,
        investor_profile: InvestorProfile
    ) -> Dict[str, float]:
        """
        Analyze loss aversion behavior: pain from losses > pleasure from gains.

        Kahneman & Tversky: losses hurt 2-2.5x more than equivalent gains feel good.

        Args:
            returns: Historical return series
            investor_profile: Investor personality profile

        Returns:
            Dictionary with loss aversion metrics
        """
        gains = returns[returns > 0]
        losses = returns[returns < 0]

        if len(gains) == 0 or len(losses) == 0:
            return {'error': 'Insufficient gain/loss data'}

        avg_gain = gains.mean()
        avg_loss = abs(losses.mean())

        # Expected utility with loss aversion
        lambda_coef = investor_profile.loss_aversion_coefficient

        # Utility = sum of gains - λ * sum of losses
        total_utility = gains.sum() - lambda_coef * abs(losses.sum())

        # Risk-adjusted preference
        expected_return = returns.mean()
        risk = returns.std()

        # Loss aversion adjusted Sharpe
        loss_aversion_sharpe = (
            (gains.mean() - lambda_coef * abs(losses.mean())) / risk
            if risk > 0 else 0
        )

        # Probability of loss
        loss_probability = len(losses) / len(returns)

        # Minimum gain needed to offset one loss
        required_gain_loss_ratio = lambda_coef

        return {
            'avg_gain': avg_gain,
            'avg_loss': avg_loss,
            'loss_aversion_coef': lambda_coef,
            'total_utility': total_utility,
            'loss_aversion_sharpe': loss_aversion_sharpe,
            'loss_probability': loss_probability,
            'required_gain_loss_ratio': required_gain_loss_ratio,
            'is_acceptable_trade': total_utility > 0
        }

    def model_personality_trading_style(
        self,
        profile: InvestorProfile
    ) -> Dict[str, any]:
        """
        Predict trading behavior based on Big Five personality traits.

        Research findings:
        - High Openness → Innovation stocks, higher risk
        - High Conscientiousness → Buy-and-hold, less trading
        - High Extraversion → More active trading, social influence
        - High Agreeableness → Herd behavior susceptibility
        - High Neuroticism → Panic selling, emotional trading

        Args:
            profile: Investor personality profile

        Returns:
            Dictionary with predicted trading characteristics
        """
        # Risk tolerance (Openness +, Neuroticism -)
        risk_score = (
            profile.openness * 0.4 +
            (100 - profile.neuroticism) * 0.4 +
            profile.extraversion * 0.2
        ) / 100

        # Trading frequency (Extraversion +, Conscientiousness -)
        frequency_score = (
            profile.extraversion * 0.5 +
            (100 - profile.conscientiousness) * 0.3 +
            profile.openness * 0.2
        ) / 100

        # Herd behavior susceptibility (Agreeableness +, Openness -)
        herd_susceptibility = (
            profile.agreeableness * 0.6 +
            (100 - profile.openness) * 0.4
        ) / 100

        # Emotional trading (Neuroticism +)
        emotional_trading_score = profile.neuroticism / 100

        # Innovation preference (Openness +)
        innovation_preference = profile.openness / 100

        # Holding period (inverse of frequency)
        if frequency_score < 0.3:
            typical_holding = "Long-term (>1 year)"
        elif frequency_score < 0.6:
            typical_holding = "Medium-term (1-12 months)"
        else:
            typical_holding = "Short-term (<1 month)"

        # Stock preferences
        if innovation_preference > 0.7:
            stock_preference = "Growth & Tech"
        elif risk_score < 0.4:
            stock_preference = "Value & Dividends"
        else:
            stock_preference = "Balanced"

        return {
            'risk_tolerance': risk_score,
            'trading_frequency_score': frequency_score,
            'typical_holding_period': typical_holding,
            'herd_susceptibility': herd_susceptibility,
            'emotional_trading_tendency': emotional_trading_score,
            'innovation_preference': innovation_preference,
            'preferred_stock_type': stock_preference,
            'panic_sell_probability': emotional_trading_score * herd_susceptibility,
            'contrarian_potential': (100 - profile.agreeableness) / 100
        }

    def analyze_social_sentiment(
        self,
        mentions: int,
        positive_mentions: int,
        negative_mentions: int,
        search_volume_trend: float,
        influencer_sentiment: float = 0.5
    ) -> Dict[str, float]:
        """
        Analyze social media and search sentiment.

        High search volume + positive sentiment = FOMO potential
        High search volume + negative sentiment = Panic potential

        Args:
            mentions: Total social media mentions
            positive_mentions: Positive sentiment mentions
            negative_mentions: Negative sentiment mentions
            search_volume_trend: Change in search volume (1.0 = no change)
            influencer_sentiment: 0-1 score from key influencers

        Returns:
            Dictionary with sentiment metrics
        """
        if mentions == 0:
            return {
                'sentiment_score': 0.5,
                'buzz_level': 0.0,
                'fomo_risk': 0.0,
                'panic_risk': 0.0
            }

        # Sentiment ratio
        neutral_mentions = mentions - positive_mentions - negative_mentions
        sentiment_score = (
            (positive_mentions - negative_mentions) / mentions + 1
        ) / 2  # Normalize to 0-1

        # Buzz level (normalized mentions + search trend)
        buzz_level = min(1.0, (mentions / 10000) * search_volume_trend)

        # FOMO risk (high buzz + positive sentiment)
        fomo_risk = buzz_level * sentiment_score if sentiment_score > 0.6 else 0

        # Panic risk (high buzz + negative sentiment)
        panic_risk = buzz_level * (1 - sentiment_score) if sentiment_score < 0.4 else 0

        # Weighted sentiment (include influencers)
        weighted_sentiment = sentiment_score * 0.7 + influencer_sentiment * 0.3

        return {
            'sentiment_score': weighted_sentiment,
            'buzz_level': buzz_level,
            'fomo_risk': fomo_risk,
            'panic_risk': panic_risk,
            'positive_ratio': positive_mentions / mentions,
            'negative_ratio': negative_mentions / mentions,
            'search_trend': search_volume_trend
        }

    def estimate_market_participant_mix(
        self,
        volume_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Estimate proportion of different trader types from volume patterns.

        - HFT: Lots of small trades, rapid fire
        - Retail: Medium trades, clustered at market open/close
        - Institutional: Large block trades, midday

        Args:
            volume_data: DataFrame with 'volume', 'trade_size', 'timestamp'

        Returns:
            Dictionary with estimated participant percentages
        """
        if 'trade_size' not in volume_data.columns:
            return {'error': 'Need trade size data'}

        # Classify trades by size
        small_trades = volume_data[volume_data['trade_size'] < 100]
        medium_trades = volume_data[
            (volume_data['trade_size'] >= 100) &
            (volume_data['trade_size'] < 10000)
        ]
        large_trades = volume_data[volume_data['trade_size'] >= 10000]

        total_volume = volume_data['volume'].sum()

        # Estimate participant types by volume
        hft_volume = small_trades['volume'].sum() * 0.7  # 70% of small trades
        retail_volume = (
            small_trades['volume'].sum() * 0.3 +
            medium_trades['volume'].sum() * 0.6
        )
        institutional_volume = (
            medium_trades['volume'].sum() * 0.4 +
            large_trades['volume'].sum()
        )

        estimated_total = hft_volume + retail_volume + institutional_volume

        return {
            'hft_percentage': hft_volume / estimated_total if estimated_total > 0 else 0,
            'retail_percentage': retail_volume / estimated_total if estimated_total > 0 else 0,
            'institutional_percentage': institutional_volume / estimated_total if estimated_total > 0 else 0,
            'avg_trade_size': volume_data['trade_size'].mean(),
            'large_trade_count': len(large_trades)
        }


class DemographicAnalyzer:
    """
    Analyzes demographic factors affecting market behavior.
    """

    def analyze_age_cohort_behavior(
        self,
        age_group: str
    ) -> Dict[str, any]:
        """
        Model typical investment behavior by age group.

        Args:
            age_group: '18-30', '31-50', '51-65', '66+'

        Returns:
            Dictionary with typical behavior characteristics
        """
        behaviors = {
            '18-30': {
                'risk_tolerance': 0.8,
                'tech_preference': 0.9,
                'trading_frequency': 'high',
                'crypto_adoption': 0.7,
                'social_media_influence': 0.8,
                'esg_importance': 0.7,
                'typical_allocation': {
                    'stocks': 0.70,
                    'crypto': 0.15,
                    'bonds': 0.05,
                    'cash': 0.10
                }
            },
            '31-50': {
                'risk_tolerance': 0.6,
                'tech_preference': 0.6,
                'trading_frequency': 'medium',
                'crypto_adoption': 0.4,
                'social_media_influence': 0.5,
                'esg_importance': 0.6,
                'typical_allocation': {
                    'stocks': 0.60,
                    'crypto': 0.05,
                    'bonds': 0.20,
                    'cash': 0.15
                }
            },
            '51-65': {
                'risk_tolerance': 0.4,
                'tech_preference': 0.4,
                'trading_frequency': 'low',
                'crypto_adoption': 0.2,
                'social_media_influence': 0.3,
                'esg_importance': 0.5,
                'typical_allocation': {
                    'stocks': 0.45,
                    'crypto': 0.02,
                    'bonds': 0.35,
                    'cash': 0.18
                }
            },
            '66+': {
                'risk_tolerance': 0.2,
                'tech_preference': 0.2,
                'trading_frequency': 'very_low',
                'crypto_adoption': 0.05,
                'social_media_influence': 0.1,
                'esg_importance': 0.4,
                'typical_allocation': {
                    'stocks': 0.30,
                    'crypto': 0.01,
                    'bonds': 0.50,
                    'cash': 0.19
                }
            }
        }

        return behaviors.get(age_group, behaviors['31-50'])  # Default to middle age


if __name__ == "__main__":
    # Example usage
    analyzer = BehavioralFactorAnalyzer()

    # Example 1: Fear & Greed Index
    print("=== Fear & Greed Index ===")
    fg_index = analyzer.calculate_fear_greed_index(
        vix=25,
        put_call_ratio=1.1,
        market_momentum=45,
        market_breadth=48,
        safe_haven_demand=55
    )
    print(f"Score: {fg_index['fear_greed_score']:.1f}")
    print(f"Sentiment: {fg_index['sentiment']}")

    # Example 2: Investor Profile & Trading Style
    print("\n=== Investor Profile Analysis ===")
    profile = InvestorProfile(
        age=35,
        openness=75,
        conscientiousness=60,
        extraversion=70,
        agreeableness=55,
        neuroticism=40,
        years_investing=10
    )

    trading_style = analyzer.model_personality_trading_style(profile)
    print(f"Risk Tolerance: {trading_style['risk_tolerance']:.2f}")
    print(f"Trading Frequency: {trading_style['typical_holding_period']}")
    print(f"Preferred Stocks: {trading_style['preferred_stock_type']}")
    print(f"Panic Sell Probability: {trading_style['panic_sell_probability']:.2f}")

    # Example 3: Trust Factor (e.g., NVIDIA)
    print("\n=== Company Trust Factor (NVIDIA Example) ===")
    nvidia_data = {
        'brand_reputation': 0.9,
        'credit_rating_score': 0.85,
        'innovation_score': 0.95,
        'management_score': 0.88,
        'customer_satisfaction': 0.82,
        'employee_satisfaction': 0.80,
        'compliance_score': 0.90,
        'esg_score': 0.75
    }
    trust_score = analyzer.calculate_trust_factor(nvidia_data)
    print(f"Trust Factor: {trust_score:.2f} (0.0-1.0)")

    # Example 4: Social Sentiment
    print("\n=== Social Sentiment Analysis ===")
    sentiment = analyzer.analyze_social_sentiment(
        mentions=5000,
        positive_mentions=3500,
        negative_mentions=800,
        search_volume_trend=1.5,
        influencer_sentiment=0.75
    )
    print(f"Sentiment Score: {sentiment['sentiment_score']:.2f}")
    print(f"FOMO Risk: {sentiment['fomo_risk']:.2f}")
    print(f"Panic Risk: {sentiment['panic_risk']:.2f}")
