"""
Multi-Factor Weighting System with Machine Learning

Combines disparate factors (technical, fundamental, seasonal, behavioral, macro)
into unified predictions using various ML approaches:
- Linear regression (baseline)
- Random Forest (non-linear relationships)
- Gradient Boosting (XGBoost/LightGBM)
- Neural Networks (LSTM for time-series)
- Ensemble methods
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import warnings

warnings.filterwarnings('ignore')


@dataclass
class FactorImportance:
    """Represents importance of a factor in predictions"""
    factor_name: str
    importance_score: float
    coefficient: Optional[float] = None
    p_value: Optional[float] = None
    confidence_interval: Optional[Tuple[float, float]] = None


@dataclass
class PredictionResult:
    """Result from factor-weighted prediction"""
    predicted_return: float
    predicted_direction: str  # 'up', 'down', 'neutral'
    confidence: float  # 0-1
    contributing_factors: List[Dict[str, float]]
    model_name: str
    timestamp: pd.Timestamp


class FactorWeightingEngine:
    """
    Combines multiple factors with learned weights to predict returns.
    """

    def __init__(self, model_type: str = 'ensemble'):
        """
        Args:
            model_type: 'linear', 'ridge', 'lasso', 'random_forest',
                       'gradient_boost', 'ensemble'
        """
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_fitted = False

    def prepare_features(
        self,
        technical_features: Dict[str, float],
        fundamental_features: Dict[str, float],
        seasonal_features: Dict[str, float],
        behavioral_features: Dict[str, float],
        macro_features: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Combine all factor types into feature matrix.

        Args:
            technical_features: Moving averages, RSI, MACD, etc.
            fundamental_features: P/E, revenue growth, margins, etc.
            seasonal_features: Month effect, day-of-week, etc.
            behavioral_features: Sentiment, fear/greed, trust, etc.
            macro_features: Interest rates, GDP, inflation, etc.

        Returns:
            DataFrame with all features
        """
        all_features = {}

        # Add prefix to distinguish factor types
        for k, v in technical_features.items():
            all_features[f'tech_{k}'] = v

        for k, v in fundamental_features.items():
            all_features[f'fund_{k}'] = v

        for k, v in seasonal_features.items():
            all_features[f'seas_{k}'] = v

        for k, v in behavioral_features.items():
            all_features[f'behav_{k}'] = v

        for k, v in macro_features.items():
            all_features[f'macro_{k}'] = v

        return pd.DataFrame([all_features])

    def train(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        validation_split: float = 0.2
    ) -> Dict[str, float]:
        """
        Train the factor weighting model.

        Args:
            X: Feature matrix (factors)
            y: Target variable (forward returns)
            validation_split: Fraction for validation

        Returns:
            Dictionary with training metrics
        """
        self.feature_names = X.columns.tolist()

        # Time-series split (preserve temporal order)
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)

        # Select and train model
        if self.model_type == 'linear':
            self.model = LinearRegression()
        elif self.model_type == 'ridge':
            self.model = Ridge(alpha=1.0)
        elif self.model_type == 'lasso':
            self.model = Lasso(alpha=0.01)
        elif self.model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=10,
                random_state=42
            )
        elif self.model_type == 'gradient_boost':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        elif self.model_type == 'ensemble':
            # Ensemble of multiple models
            self.model = self._create_ensemble_model()
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

        # Train
        if self.model_type == 'ensemble':
            self.model.fit(X_train_scaled, y_train, X_val_scaled, y_val)
        else:
            self.model.fit(X_train_scaled, y_train)

        # Evaluate
        y_train_pred = self.model.predict(X_train_scaled)
        y_val_pred = self.model.predict(X_val_scaled)

        self.is_fitted = True

        return {
            'train_r2': r2_score(y_train, y_train_pred),
            'val_r2': r2_score(y_val, y_val_pred),
            'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
            'val_rmse': np.sqrt(mean_squared_error(y_val, y_val_pred)),
            'train_mae': mean_absolute_error(y_train, y_train_pred),
            'val_mae': mean_absolute_error(y_val, y_val_pred)
        }

    def _create_ensemble_model(self):
        """Create ensemble of multiple models"""
        return EnsembleModel([
            LinearRegression(),
            Ridge(alpha=1.0),
            RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42),
            GradientBoostingRegressor(n_estimators=50, max_depth=4, random_state=42)
        ])

    def predict(
        self,
        X: pd.DataFrame,
        return_factors: bool = True
    ) -> PredictionResult:
        """
        Make prediction with factor contributions.

        Args:
            X: Feature matrix (single row)
            return_factors: Whether to return factor contributions

        Returns:
            PredictionResult with prediction and explanations
        """
        if not self.is_fitted:
            raise ValueError("Model not trained. Call train() first.")

        # Scale features
        X_scaled = self.scaler.transform(X)

        # Predict
        pred = self.model.predict(X_scaled)[0]

        # Direction
        if pred > 0.01:
            direction = 'up'
        elif pred < -0.01:
            direction = 'down'
        else:
            direction = 'neutral'

        # Confidence (based on prediction magnitude and historical accuracy)
        confidence = min(1.0, abs(pred) * 10)  # Simplified

        # Factor contributions
        contributing_factors = []
        if return_factors:
            contributing_factors = self._get_factor_contributions(X, X_scaled, pred)

        return PredictionResult(
            predicted_return=pred,
            predicted_direction=direction,
            confidence=confidence,
            contributing_factors=contributing_factors,
            model_name=self.model_type,
            timestamp=pd.Timestamp.now()
        )

    def _get_factor_contributions(
        self,
        X: pd.DataFrame,
        X_scaled: np.ndarray,
        prediction: float
    ) -> List[Dict[str, float]]:
        """
        Calculate how much each factor contributed to prediction.
        """
        contributions = []

        if hasattr(self.model, 'coef_'):
            # Linear models: contribution = feature_value * coefficient
            coefficients = self.model.coef_
            for i, feature_name in enumerate(self.feature_names):
                contribution = X_scaled[0, i] * coefficients[i]
                contributions.append({
                    'factor': feature_name,
                    'value': X.iloc[0, i],
                    'scaled_value': X_scaled[0, i],
                    'weight': coefficients[i],
                    'contribution': contribution,
                    'pct_of_prediction': contribution / prediction if prediction != 0 else 0
                })

        elif hasattr(self.model, 'feature_importances_'):
            # Tree-based models: use feature importances
            importances = self.model.feature_importances_
            for i, feature_name in enumerate(self.feature_names):
                contributions.append({
                    'factor': feature_name,
                    'value': X.iloc[0, i],
                    'importance': importances[i],
                    'contribution_estimate': importances[i] * X_scaled[0, i]
                })

        # Sort by absolute contribution
        contributions.sort(
            key=lambda x: abs(x.get('contribution', x.get('contribution_estimate', 0))),
            reverse=True
        )

        return contributions[:10]  # Top 10 factors

    def get_factor_importances(self) -> List[FactorImportance]:
        """
        Get importance scores for all factors.

        Returns:
            List of FactorImportance objects
        """
        if not self.is_fitted:
            raise ValueError("Model not trained")

        importances = []

        if hasattr(self.model, 'coef_'):
            # Linear models
            coefficients = self.model.coef_
            for i, name in enumerate(self.feature_names):
                importances.append(FactorImportance(
                    factor_name=name,
                    importance_score=abs(coefficients[i]),
                    coefficient=coefficients[i]
                ))

        elif hasattr(self.model, 'feature_importances_'):
            # Tree-based models
            feature_importances = self.model.feature_importances_
            for i, name in enumerate(self.feature_names):
                importances.append(FactorImportance(
                    factor_name=name,
                    importance_score=feature_importances[i]
                ))

        importances.sort(key=lambda x: x.importance_score, reverse=True)
        return importances

    def cross_validate(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        n_splits: int = 5
    ) -> Dict[str, float]:
        """
        Perform time-series cross-validation.

        Args:
            X: Feature matrix
            y: Target variable
            n_splits: Number of CV folds

        Returns:
            Dictionary with CV metrics
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        X_scaled = self.scaler.fit_transform(X)

        if self.model is None:
            self.model = self._create_model()

        scores = cross_val_score(
            self.model, X_scaled, y,
            cv=tscv, scoring='r2'
        )

        return {
            'mean_r2': scores.mean(),
            'std_r2': scores.std(),
            'min_r2': scores.min(),
            'max_r2': scores.max(),
            'all_scores': scores.tolist()
        }

    def _create_model(self):
        """Create model instance based on type"""
        if self.model_type == 'linear':
            return LinearRegression()
        elif self.model_type == 'ridge':
            return Ridge(alpha=1.0)
        elif self.model_type == 'lasso':
            return Lasso(alpha=0.01)
        elif self.model_type == 'random_forest':
            return RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
        elif self.model_type == 'gradient_boost':
            return GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
        elif self.model_type == 'ensemble':
            return self._create_ensemble_model()


class EnsembleModel:
    """
    Ensemble of multiple models with weighted averaging.
    """

    def __init__(self, models: List[Any], weights: Optional[List[float]] = None):
        self.models = models
        self.weights = weights if weights else [1.0 / len(models)] * len(models)

    def fit(self, X_train, y_train, X_val=None, y_val=None):
        """Train all models"""
        for model in self.models:
            model.fit(X_train, y_train)

        # Optimize weights based on validation performance
        if X_val is not None and y_val is not None:
            self._optimize_weights(X_val, y_val)

    def _optimize_weights(self, X_val, y_val):
        """Optimize ensemble weights based on validation performance"""
        predictions = np.column_stack([
            model.predict(X_val) for model in self.models
        ])

        # Simple optimization: weight by R² on validation set
        r2_scores = []
        for i, model in enumerate(self.models):
            pred = predictions[:, i]
            r2 = r2_score(y_val, pred)
            r2_scores.append(max(0, r2))  # Negative R² gets 0 weight

        total = sum(r2_scores)
        if total > 0:
            self.weights = [r2 / total for r2 in r2_scores]

    def predict(self, X):
        """Weighted average prediction"""
        predictions = np.column_stack([
            model.predict(X) for model in self.models
        ])

        return np.average(predictions, axis=1, weights=self.weights)

    @property
    def feature_importances_(self):
        """Average feature importances if available"""
        importances_list = []
        for model in self.models:
            if hasattr(model, 'feature_importances_'):
                importances_list.append(model.feature_importances_)

        if importances_list:
            return np.mean(importances_list, axis=0)
        return None


class AdaptiveFactorWeighting:
    """
    Adaptive weighting that adjusts to changing market regimes.
    """

    def __init__(self, regime_detector=None):
        self.models = {}  # model per regime
        self.current_regime = 'normal'
        self.regime_detector = regime_detector

    def detect_regime(
        self,
        market_data: pd.DataFrame
    ) -> str:
        """
        Detect current market regime.

        Regimes:
        - 'bull': Strong uptrend, low volatility
        - 'bear': Downtrend, high volatility
        - 'high_vol': High volatility, no clear trend
        - 'normal': Normal conditions

        Args:
            market_data: Recent market data

        Returns:
            Regime name
        """
        # Simple regime detection based on returns and volatility
        returns = market_data['close'].pct_change()
        recent_return = returns.tail(20).mean()
        recent_vol = returns.tail(20).std()

        avg_vol = returns.std()

        if recent_return > 0.001 and recent_vol < avg_vol:
            return 'bull'
        elif recent_return < -0.001 and recent_vol > avg_vol * 1.5:
            return 'bear'
        elif recent_vol > avg_vol * 2:
            return 'high_vol'
        else:
            return 'normal'

    def train_regime_models(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        regimes: pd.Series
    ):
        """
        Train separate models for each market regime.

        Args:
            X: Feature matrix
            y: Target variable
            regimes: Regime label for each observation
        """
        for regime in regimes.unique():
            mask = regimes == regime
            X_regime = X[mask]
            y_regime = y[mask]

            if len(X_regime) > 50:  # Minimum data requirement
                model = FactorWeightingEngine('ensemble')
                model.train(X_regime, y_regime)
                self.models[regime] = model

    def predict(
        self,
        X: pd.DataFrame,
        current_regime: str
    ) -> PredictionResult:
        """
        Predict using regime-specific model.

        Args:
            X: Feature matrix
            current_regime: Current market regime

        Returns:
            PredictionResult
        """
        if current_regime in self.models:
            return self.models[current_regime].predict(X)
        elif 'normal' in self.models:
            return self.models['normal'].predict(X)
        else:
            raise ValueError("No models trained")


if __name__ == "__main__":
    # Example usage
    print("=== Factor Weighting System Test ===\n")

    # Generate synthetic data
    np.random.seed(42)
    n_samples = 1000

    # Create features
    X = pd.DataFrame({
        'tech_ma_50': np.random.randn(n_samples),
        'tech_rsi': np.random.randn(n_samples),
        'fund_pe_ratio': np.random.randn(n_samples),
        'fund_revenue_growth': np.random.randn(n_samples),
        'seas_month_effect': np.random.randn(n_samples),
        'behav_sentiment': np.random.randn(n_samples),
        'macro_interest_rate': np.random.randn(n_samples)
    })

    # Create target (returns) with some relationship to features
    y = (
        0.3 * X['tech_ma_50'] +
        0.2 * X['fund_revenue_growth'] +
        0.1 * X['behav_sentiment'] +
        np.random.randn(n_samples) * 0.5
    )

    # Train model
    engine = FactorWeightingEngine('ensemble')
    metrics = engine.train(X, y)

    print("Training Metrics:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

    # Make prediction
    X_new = X.iloc[[-1]]
    prediction = engine.predict(X_new)

    print(f"\nPrediction:")
    print(f"  Expected Return: {prediction.predicted_return:+.2%}")
    print(f"  Direction: {prediction.predicted_direction}")
    print(f"  Confidence: {prediction.confidence:.2f}")

    print(f"\nTop Contributing Factors:")
    for factor in prediction.contributing_factors[:5]:
        print(f"  {factor['factor']}: {factor.get('contribution', factor.get('contribution_estimate', 0)):.4f}")

    # Feature importances
    print(f"\nFactor Importances:")
    importances = engine.get_factor_importances()
    for imp in importances[:5]:
        print(f"  {imp.factor_name}: {imp.importance_score:.4f}")
