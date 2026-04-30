#!/usr/bin/env python3
"""
================================================================================
ELECTRODUCTION TOOLS SUITE - DATA SCIENCE TOOLKIT
================================================================================
A comprehensive data science and statistical analysis library without external
dependencies. Provides statistical functions, data manipulation, visualization
helpers, and machine learning primitives.

FEATURES:
- Descriptive statistics (mean, median, std, variance, quartiles)
- Inferential statistics (t-tests, chi-square, correlation)
- Data manipulation (filtering, sorting, grouping, pivoting)
- Linear regression and basic ML primitives
- Data normalization and scaling
- Outlier detection
- Time series analysis basics
- Data quality assessment

All functions work with pure Python - no numpy/pandas required.

Usage:
    from tools_suite.data_science.statistics_toolkit import StatisticsToolkit
    stats = StatisticsToolkit()
    result = stats.describe([1, 2, 3, 4, 5])
================================================================================
"""

# =============================================================================
# IMPORTS - Standard library only
# =============================================================================

import math                      # Mathematical functions
import random                    # Random number generation
import statistics as std_stats   # Python's built-in statistics
import json                      # JSON serialization
import csv                       # CSV file handling
import collections               # Specialized containers
from typing import (             # Type hints for documentation
    List, Dict, Tuple, Any, Optional, Union, Callable, Iterator
)
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import reduce
import itertools
import operator


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class DataColumn:
    """
    Represents a single column of data.

    Attributes:
        name: Column name/identifier
        data: List of values in the column
        dtype: Data type (numeric, string, datetime, boolean)
    """
    name: str                              # Column name
    data: List[Any]                        # Column values
    dtype: str = "auto"                    # Data type

    def __post_init__(self):
        """Automatically detect data type if set to auto."""
        if self.dtype == "auto":
            self.dtype = self._detect_type()

    def _detect_type(self) -> str:
        """
        Detect the data type of the column.

        Returns:
            String indicating data type
        """
        if not self.data:
            return "empty"

        # Sample first non-None value
        sample = None
        for val in self.data:
            if val is not None:
                sample = val
                break

        if sample is None:
            return "null"

        if isinstance(sample, bool):
            return "boolean"
        elif isinstance(sample, (int, float)):
            return "numeric"
        elif isinstance(sample, str):
            # Check if it might be a date
            try:
                datetime.fromisoformat(sample)
                return "datetime"
            except:
                return "string"
        else:
            return "object"

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


@dataclass
class DataFrame:
    """
    Simple DataFrame implementation for tabular data.

    Provides pandas-like functionality without external dependencies.

    Attributes:
        columns: Dictionary mapping column names to DataColumn objects
        index: Row index values
    """
    columns: Dict[str, DataColumn] = field(default_factory=dict)
    index: List[Any] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, List]) -> 'DataFrame':
        """
        Create DataFrame from dictionary.

        Args:
            data: Dictionary with column names as keys, lists as values

        Returns:
            New DataFrame instance
        """
        df = cls()
        for name, values in data.items():
            df.columns[name] = DataColumn(name=name, data=values)

        # Set default index
        if df.columns:
            first_col = list(df.columns.values())[0]
            df.index = list(range(len(first_col)))

        return df

    @classmethod
    def from_csv(cls, filepath: str, delimiter: str = ',',
                 has_header: bool = True) -> 'DataFrame':
        """
        Load DataFrame from CSV file.

        Args:
            filepath: Path to CSV file
            delimiter: Column delimiter
            has_header: Whether first row is header

        Returns:
            New DataFrame instance
        """
        data = {}

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            rows = list(reader)

        if not rows:
            return cls()

        # Get headers
        if has_header:
            headers = rows[0]
            data_rows = rows[1:]
        else:
            headers = [f"col_{i}" for i in range(len(rows[0]))]
            data_rows = rows

        # Initialize columns
        for header in headers:
            data[header] = []

        # Populate columns
        for row in data_rows:
            for i, value in enumerate(row):
                if i < len(headers):
                    # Try to convert to number
                    try:
                        if '.' in value:
                            data[headers[i]].append(float(value))
                        else:
                            data[headers[i]].append(int(value))
                    except ValueError:
                        data[headers[i]].append(value)

        return cls.from_dict(data)

    def to_csv(self, filepath: str, delimiter: str = ','):
        """
        Save DataFrame to CSV file.

        Args:
            filepath: Output file path
            delimiter: Column delimiter
        """
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, delimiter=delimiter)

            # Write header
            headers = list(self.columns.keys())
            writer.writerow(headers)

            # Write data rows
            for i in range(len(self)):
                row = [self.columns[h].data[i] for h in headers]
                writer.writerow(row)

    def __len__(self) -> int:
        """Return number of rows."""
        if not self.columns:
            return 0
        return len(list(self.columns.values())[0])

    def __getitem__(self, key: str) -> DataColumn:
        """Get column by name."""
        return self.columns[key]

    def head(self, n: int = 5) -> 'DataFrame':
        """Return first n rows."""
        new_data = {}
        for name, col in self.columns.items():
            new_data[name] = col.data[:n]
        return DataFrame.from_dict(new_data)

    def tail(self, n: int = 5) -> 'DataFrame':
        """Return last n rows."""
        new_data = {}
        for name, col in self.columns.items():
            new_data[name] = col.data[-n:]
        return DataFrame.from_dict(new_data)

    def select(self, columns: List[str]) -> 'DataFrame':
        """Select specific columns."""
        new_data = {name: self.columns[name].data for name in columns if name in self.columns}
        return DataFrame.from_dict(new_data)

    def filter(self, condition: Callable[[Dict], bool]) -> 'DataFrame':
        """
        Filter rows based on condition.

        Args:
            condition: Function that takes row dict and returns bool

        Returns:
            Filtered DataFrame
        """
        new_data = {name: [] for name in self.columns}

        for i in range(len(self)):
            row = {name: col.data[i] for name, col in self.columns.items()}
            if condition(row):
                for name in self.columns:
                    new_data[name].append(row[name])

        return DataFrame.from_dict(new_data)

    def sort_by(self, column: str, ascending: bool = True) -> 'DataFrame':
        """Sort by column."""
        if column not in self.columns:
            raise KeyError(f"Column '{column}' not found")

        # Get sort indices
        indexed = list(enumerate(self.columns[column].data))
        indexed.sort(key=lambda x: x[1], reverse=not ascending)
        indices = [i for i, _ in indexed]

        # Reorder all columns
        new_data = {}
        for name, col in self.columns.items():
            new_data[name] = [col.data[i] for i in indices]

        return DataFrame.from_dict(new_data)

    def group_by(self, column: str) -> Dict[Any, 'DataFrame']:
        """
        Group by column values.

        Args:
            column: Column to group by

        Returns:
            Dictionary mapping group values to DataFrames
        """
        groups = {}

        for i in range(len(self)):
            key = self.columns[column].data[i]
            if key not in groups:
                groups[key] = {name: [] for name in self.columns}

            for name, col in self.columns.items():
                groups[key][name].append(col.data[i])

        return {key: DataFrame.from_dict(data) for key, data in groups.items()}

    def describe(self) -> Dict[str, Dict[str, float]]:
        """
        Generate descriptive statistics for numeric columns.

        Returns:
            Dictionary of statistics per column
        """
        stats = StatisticsToolkit()
        result = {}

        for name, col in self.columns.items():
            if col.dtype == "numeric":
                numeric_data = [x for x in col.data if x is not None and isinstance(x, (int, float))]
                if numeric_data:
                    result[name] = stats.describe(numeric_data)

        return result

    def __str__(self) -> str:
        """String representation."""
        if not self.columns:
            return "Empty DataFrame"

        # Get column widths
        headers = list(self.columns.keys())
        widths = {h: max(len(str(h)), 8) for h in headers}

        for name, col in self.columns.items():
            for val in col.data[:10]:  # Sample first 10
                widths[name] = max(widths[name], len(str(val)[:20]))

        # Build output
        lines = []

        # Header
        header_line = " | ".join(f"{h:{widths[h]}}" for h in headers)
        lines.append(header_line)
        lines.append("-" * len(header_line))

        # Data rows (max 10)
        for i in range(min(len(self), 10)):
            row_vals = [str(self.columns[h].data[i])[:widths[h]] for h in headers]
            lines.append(" | ".join(f"{v:{widths[h]}}" for v, h in zip(row_vals, headers)))

        if len(self) > 10:
            lines.append(f"... ({len(self)} rows total)")

        return "\n".join(lines)


# =============================================================================
# STATISTICS TOOLKIT
# =============================================================================

class StatisticsToolkit:
    """
    Comprehensive statistics toolkit.

    Provides statistical functions for data analysis including:
    - Descriptive statistics
    - Inferential statistics
    - Correlation analysis
    - Distribution analysis
    """

    # -------------------------------------------------------------------------
    # DESCRIPTIVE STATISTICS
    # -------------------------------------------------------------------------

    def mean(self, data: List[float]) -> float:
        """
        Calculate arithmetic mean.

        The mean is the sum of all values divided by the count.
        Formula: μ = Σx / n

        Args:
            data: List of numeric values

        Returns:
            Arithmetic mean
        """
        if not data:
            return 0.0
        return sum(data) / len(data)

    def median(self, data: List[float]) -> float:
        """
        Calculate median (middle value).

        The median is the middle value when data is sorted.
        For even counts, it's the average of the two middle values.

        Args:
            data: List of numeric values

        Returns:
            Median value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        n = len(sorted_data)
        mid = n // 2

        if n % 2 == 0:
            return (sorted_data[mid - 1] + sorted_data[mid]) / 2
        else:
            return sorted_data[mid]

    def mode(self, data: List[Any]) -> List[Any]:
        """
        Calculate mode (most frequent value).

        Returns all values that appear with maximum frequency.

        Args:
            data: List of values

        Returns:
            List of mode values
        """
        if not data:
            return []

        counter = collections.Counter(data)
        max_count = max(counter.values())
        return [val for val, count in counter.items() if count == max_count]

    def variance(self, data: List[float], population: bool = False) -> float:
        """
        Calculate variance.

        Variance measures how spread out the data is from the mean.
        Formula: σ² = Σ(x - μ)² / n (population) or / (n-1) (sample)

        Args:
            data: List of numeric values
            population: If True, calculate population variance

        Returns:
            Variance value
        """
        if len(data) < 2:
            return 0.0

        mean_val = self.mean(data)
        squared_diffs = [(x - mean_val) ** 2 for x in data]

        if population:
            return sum(squared_diffs) / len(data)
        else:
            return sum(squared_diffs) / (len(data) - 1)

    def std_dev(self, data: List[float], population: bool = False) -> float:
        """
        Calculate standard deviation.

        Standard deviation is the square root of variance.
        It represents the average distance from the mean.

        Args:
            data: List of numeric values
            population: If True, calculate population std dev

        Returns:
            Standard deviation
        """
        return math.sqrt(self.variance(data, population))

    def quartiles(self, data: List[float]) -> Tuple[float, float, float]:
        """
        Calculate quartiles (Q1, Q2, Q3).

        Quartiles divide the data into four equal parts.
        Q1 = 25th percentile
        Q2 = 50th percentile (median)
        Q3 = 75th percentile

        Args:
            data: List of numeric values

        Returns:
            Tuple of (Q1, Q2, Q3)
        """
        if not data:
            return (0.0, 0.0, 0.0)

        sorted_data = sorted(data)
        n = len(sorted_data)

        q2 = self.median(sorted_data)

        # Split at median
        if n % 2 == 0:
            lower = sorted_data[:n//2]
            upper = sorted_data[n//2:]
        else:
            lower = sorted_data[:n//2]
            upper = sorted_data[n//2 + 1:]

        q1 = self.median(lower) if lower else q2
        q3 = self.median(upper) if upper else q2

        return (q1, q2, q3)

    def iqr(self, data: List[float]) -> float:
        """
        Calculate Interquartile Range (IQR).

        IQR = Q3 - Q1, measures the spread of the middle 50% of data.

        Args:
            data: List of numeric values

        Returns:
            Interquartile range
        """
        q1, _, q3 = self.quartiles(data)
        return q3 - q1

    def percentile(self, data: List[float], p: float) -> float:
        """
        Calculate the p-th percentile.

        The percentile is the value below which p% of data falls.

        Args:
            data: List of numeric values
            p: Percentile (0-100)

        Returns:
            Percentile value
        """
        if not data:
            return 0.0

        sorted_data = sorted(data)
        n = len(sorted_data)

        # Calculate index
        idx = (p / 100) * (n - 1)
        lower_idx = int(idx)
        upper_idx = min(lower_idx + 1, n - 1)

        # Interpolate
        fraction = idx - lower_idx
        return sorted_data[lower_idx] + fraction * (sorted_data[upper_idx] - sorted_data[lower_idx])

    def range(self, data: List[float]) -> float:
        """
        Calculate the range (max - min).

        Args:
            data: List of numeric values

        Returns:
            Range value
        """
        if not data:
            return 0.0
        return max(data) - min(data)

    def skewness(self, data: List[float]) -> float:
        """
        Calculate skewness (measure of asymmetry).

        Positive skew: tail extends to right
        Negative skew: tail extends to left
        Zero: symmetric distribution

        Args:
            data: List of numeric values

        Returns:
            Skewness coefficient
        """
        if len(data) < 3:
            return 0.0

        n = len(data)
        mean_val = self.mean(data)
        std_val = self.std_dev(data)

        if std_val == 0:
            return 0.0

        skew = sum(((x - mean_val) / std_val) ** 3 for x in data) * n / ((n-1) * (n-2))
        return skew

    def kurtosis(self, data: List[float]) -> float:
        """
        Calculate kurtosis (measure of tail heaviness).

        Higher kurtosis = heavier tails (more outliers)
        Normal distribution has kurtosis = 3 (excess kurtosis = 0)

        Args:
            data: List of numeric values

        Returns:
            Excess kurtosis
        """
        if len(data) < 4:
            return 0.0

        n = len(data)
        mean_val = self.mean(data)
        std_val = self.std_dev(data)

        if std_val == 0:
            return 0.0

        kurt = sum(((x - mean_val) / std_val) ** 4 for x in data) / n
        return kurt - 3  # Excess kurtosis

    def describe(self, data: List[float]) -> Dict[str, float]:
        """
        Generate comprehensive descriptive statistics.

        Args:
            data: List of numeric values

        Returns:
            Dictionary of statistics
        """
        if not data:
            return {}

        q1, q2, q3 = self.quartiles(data)

        return {
            'count': len(data),
            'mean': self.mean(data),
            'median': q2,
            'mode': self.mode(data)[0] if self.mode(data) else None,
            'std': self.std_dev(data),
            'variance': self.variance(data),
            'min': min(data),
            'max': max(data),
            'range': self.range(data),
            'q1': q1,
            'q2': q2,
            'q3': q3,
            'iqr': q3 - q1,
            'skewness': self.skewness(data),
            'kurtosis': self.kurtosis(data),
        }

    # -------------------------------------------------------------------------
    # CORRELATION AND RELATIONSHIP ANALYSIS
    # -------------------------------------------------------------------------

    def covariance(self, x: List[float], y: List[float]) -> float:
        """
        Calculate covariance between two variables.

        Covariance measures how two variables change together.
        Positive: move in same direction
        Negative: move in opposite directions

        Args:
            x: First variable
            y: Second variable

        Returns:
            Covariance value
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        n = len(x)
        mean_x = self.mean(x)
        mean_y = self.mean(y)

        cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / (n - 1)
        return cov

    def pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Pearson correlation coefficient.

        Measures linear correlation between -1 and 1.
        +1: perfect positive correlation
        -1: perfect negative correlation
        0: no linear correlation

        Args:
            x: First variable
            y: Second variable

        Returns:
            Correlation coefficient
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        cov = self.covariance(x, y)
        std_x = self.std_dev(x)
        std_y = self.std_dev(y)

        if std_x == 0 or std_y == 0:
            return 0.0

        return cov / (std_x * std_y)

    def spearman_correlation(self, x: List[float], y: List[float]) -> float:
        """
        Calculate Spearman rank correlation.

        Measures monotonic relationship using ranks.
        More robust to outliers than Pearson.

        Args:
            x: First variable
            y: Second variable

        Returns:
            Spearman correlation coefficient
        """
        if len(x) != len(y) or len(x) < 2:
            return 0.0

        # Convert to ranks
        def rank(data):
            indexed = list(enumerate(data))
            indexed.sort(key=lambda t: t[1])
            ranks = [0] * len(data)
            for rank_val, (orig_idx, _) in enumerate(indexed):
                ranks[orig_idx] = rank_val + 1
            return ranks

        rank_x = rank(x)
        rank_y = rank(y)

        return self.pearson_correlation(rank_x, rank_y)

    def correlation_matrix(self, data: Dict[str, List[float]]) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix for multiple variables.

        Args:
            data: Dictionary of variable names to values

        Returns:
            Matrix of correlations
        """
        variables = list(data.keys())
        matrix = {}

        for var1 in variables:
            matrix[var1] = {}
            for var2 in variables:
                matrix[var1][var2] = self.pearson_correlation(data[var1], data[var2])

        return matrix

    # -------------------------------------------------------------------------
    # INFERENTIAL STATISTICS
    # -------------------------------------------------------------------------

    def z_score(self, value: float, mean: float, std: float) -> float:
        """
        Calculate z-score (standard score).

        Z-score indicates how many standard deviations from the mean.

        Args:
            value: The value to standardize
            mean: Population/sample mean
            std: Population/sample standard deviation

        Returns:
            Z-score
        """
        if std == 0:
            return 0.0
        return (value - mean) / std

    def z_scores(self, data: List[float]) -> List[float]:
        """
        Calculate z-scores for all values.

        Args:
            data: List of values

        Returns:
            List of z-scores
        """
        mean_val = self.mean(data)
        std_val = self.std_dev(data)
        return [self.z_score(x, mean_val, std_val) for x in data]

    def t_statistic(self, sample: List[float], population_mean: float) -> float:
        """
        Calculate t-statistic for one-sample t-test.

        Tests if sample mean differs from hypothesized population mean.

        Args:
            sample: Sample data
            population_mean: Hypothesized population mean

        Returns:
            T-statistic
        """
        if len(sample) < 2:
            return 0.0

        sample_mean = self.mean(sample)
        sample_std = self.std_dev(sample)
        n = len(sample)

        if sample_std == 0:
            return 0.0

        se = sample_std / math.sqrt(n)
        return (sample_mean - population_mean) / se

    def two_sample_t_statistic(self, sample1: List[float],
                                sample2: List[float]) -> Tuple[float, float]:
        """
        Calculate t-statistic for two-sample t-test.

        Tests if two sample means are significantly different.

        Args:
            sample1: First sample
            sample2: Second sample

        Returns:
            Tuple of (t-statistic, degrees of freedom)
        """
        n1, n2 = len(sample1), len(sample2)
        if n1 < 2 or n2 < 2:
            return (0.0, 0)

        mean1, mean2 = self.mean(sample1), self.mean(sample2)
        var1, var2 = self.variance(sample1), self.variance(sample2)

        # Pooled standard error
        se = math.sqrt(var1/n1 + var2/n2)

        if se == 0:
            return (0.0, 0)

        t_stat = (mean1 - mean2) / se

        # Welch's degrees of freedom
        df = (var1/n1 + var2/n2)**2 / (
            (var1/n1)**2/(n1-1) + (var2/n2)**2/(n2-1)
        )

        return (t_stat, df)

    def chi_square_statistic(self, observed: List[float],
                              expected: List[float]) -> float:
        """
        Calculate chi-square statistic.

        Tests goodness of fit between observed and expected frequencies.

        Args:
            observed: Observed frequencies
            expected: Expected frequencies

        Returns:
            Chi-square statistic
        """
        if len(observed) != len(expected):
            return 0.0

        chi_sq = sum((o - e)**2 / e for o, e in zip(observed, expected) if e > 0)
        return chi_sq

    # -------------------------------------------------------------------------
    # OUTLIER DETECTION
    # -------------------------------------------------------------------------

    def detect_outliers_iqr(self, data: List[float],
                            multiplier: float = 1.5) -> List[Tuple[int, float]]:
        """
        Detect outliers using IQR method.

        Outliers are values outside [Q1 - k*IQR, Q3 + k*IQR]
        where k is the multiplier (typically 1.5 for outliers, 3 for extremes).

        Args:
            data: List of values
            multiplier: IQR multiplier

        Returns:
            List of (index, value) tuples for outliers
        """
        q1, _, q3 = self.quartiles(data)
        iqr_val = q3 - q1

        lower_bound = q1 - multiplier * iqr_val
        upper_bound = q3 + multiplier * iqr_val

        outliers = []
        for i, val in enumerate(data):
            if val < lower_bound or val > upper_bound:
                outliers.append((i, val))

        return outliers

    def detect_outliers_zscore(self, data: List[float],
                                threshold: float = 3.0) -> List[Tuple[int, float]]:
        """
        Detect outliers using z-score method.

        Values with |z-score| > threshold are outliers.

        Args:
            data: List of values
            threshold: Z-score threshold

        Returns:
            List of (index, value) tuples for outliers
        """
        z_scores = self.z_scores(data)

        outliers = []
        for i, (val, z) in enumerate(zip(data, z_scores)):
            if abs(z) > threshold:
                outliers.append((i, val))

        return outliers

    # -------------------------------------------------------------------------
    # DATA TRANSFORMATION
    # -------------------------------------------------------------------------

    def normalize(self, data: List[float]) -> List[float]:
        """
        Normalize data to [0, 1] range (min-max scaling).

        Formula: x_norm = (x - min) / (max - min)

        Args:
            data: List of values

        Returns:
            Normalized values
        """
        if not data:
            return []

        min_val = min(data)
        max_val = max(data)
        range_val = max_val - min_val

        if range_val == 0:
            return [0.5] * len(data)

        return [(x - min_val) / range_val for x in data]

    def standardize(self, data: List[float]) -> List[float]:
        """
        Standardize data (z-score normalization).

        Transforms to mean=0, std=1.

        Args:
            data: List of values

        Returns:
            Standardized values
        """
        return self.z_scores(data)

    def log_transform(self, data: List[float]) -> List[float]:
        """
        Apply log transformation.

        Useful for right-skewed data.

        Args:
            data: List of positive values

        Returns:
            Log-transformed values
        """
        return [math.log(x) if x > 0 else float('-inf') for x in data]

    def moving_average(self, data: List[float], window: int) -> List[float]:
        """
        Calculate simple moving average.

        Args:
            data: List of values
            window: Window size

        Returns:
            Moving average values
        """
        if window <= 0 or window > len(data):
            return data.copy()

        result = []
        for i in range(len(data)):
            if i < window - 1:
                result.append(None)
            else:
                window_data = data[i - window + 1:i + 1]
                result.append(self.mean(window_data))

        return result

    def exponential_moving_average(self, data: List[float],
                                    alpha: float = 0.3) -> List[float]:
        """
        Calculate exponential moving average.

        Args:
            data: List of values
            alpha: Smoothing factor (0 < alpha < 1)

        Returns:
            EMA values
        """
        if not data:
            return []

        result = [data[0]]
        for i in range(1, len(data)):
            ema = alpha * data[i] + (1 - alpha) * result[-1]
            result.append(ema)

        return result


# =============================================================================
# LINEAR REGRESSION
# =============================================================================

class LinearRegression:
    """
    Simple linear regression implementation.

    Fits a line y = mx + b to data using least squares method.
    """

    def __init__(self):
        """Initialize regression model."""
        self.slope = 0.0       # m coefficient
        self.intercept = 0.0   # b coefficient
        self.r_squared = 0.0   # Coefficient of determination
        self._fitted = False

    def fit(self, x: List[float], y: List[float]) -> 'LinearRegression':
        """
        Fit the regression model.

        Uses ordinary least squares (OLS) method.
        Formula: m = Σ(x-x̄)(y-ȳ) / Σ(x-x̄)²
                 b = ȳ - m*x̄

        Args:
            x: Independent variable values
            y: Dependent variable values

        Returns:
            Self for method chaining
        """
        if len(x) != len(y) or len(x) < 2:
            raise ValueError("Need at least 2 matching data points")

        n = len(x)
        stats = StatisticsToolkit()

        mean_x = stats.mean(x)
        mean_y = stats.mean(y)

        # Calculate slope
        numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
        denominator = sum((x[i] - mean_x) ** 2 for i in range(n))

        if denominator == 0:
            self.slope = 0.0
        else:
            self.slope = numerator / denominator

        # Calculate intercept
        self.intercept = mean_y - self.slope * mean_x

        # Calculate R-squared
        y_pred = self.predict(x)
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - mean_y) ** 2 for i in range(n))

        if ss_tot == 0:
            self.r_squared = 1.0
        else:
            self.r_squared = 1 - (ss_res / ss_tot)

        self._fitted = True
        return self

    def predict(self, x: Union[float, List[float]]) -> Union[float, List[float]]:
        """
        Make predictions.

        Args:
            x: Value(s) to predict

        Returns:
            Predicted y value(s)
        """
        if isinstance(x, list):
            return [self.slope * xi + self.intercept for xi in x]
        else:
            return self.slope * x + self.intercept

    def get_equation(self) -> str:
        """Get the regression equation as string."""
        sign = "+" if self.intercept >= 0 else "-"
        return f"y = {self.slope:.4f}x {sign} {abs(self.intercept):.4f}"

    def summary(self) -> Dict[str, float]:
        """Get model summary."""
        return {
            'slope': self.slope,
            'intercept': self.intercept,
            'r_squared': self.r_squared,
            'equation': self.get_equation()
        }


# =============================================================================
# DEMO AND TESTING
# =============================================================================

def run_demo():
    """Demonstrate the statistics toolkit."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║               ELECTRODUCTION DATA SCIENCE TOOLKIT                             ║
║                    Statistics & Analysis Demo                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)

    stats = StatisticsToolkit()

    # Sample data
    data = [23, 45, 67, 12, 89, 34, 56, 78, 90, 21, 43, 65, 87, 32, 54]

    print("[*] DESCRIPTIVE STATISTICS")
    print("-" * 60)
    print(f"Data: {data}\n")

    desc = stats.describe(data)
    for key, value in desc.items():
        if isinstance(value, float):
            print(f"  {key:15s}: {value:.4f}")
        else:
            print(f"  {key:15s}: {value}")

    # Correlation
    print("\n[*] CORRELATION ANALYSIS")
    print("-" * 60)
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    y = [2.1, 4.2, 5.8, 8.1, 9.9, 12.1, 14.0, 16.2, 17.9, 20.1]

    print(f"X: {x}")
    print(f"Y: {y}")
    print(f"  Pearson r:    {stats.pearson_correlation(x, y):.4f}")
    print(f"  Spearman r:   {stats.spearman_correlation(x, y):.4f}")
    print(f"  Covariance:   {stats.covariance(x, y):.4f}")

    # Linear Regression
    print("\n[*] LINEAR REGRESSION")
    print("-" * 60)

    lr = LinearRegression()
    lr.fit(x, y)
    summary = lr.summary()

    print(f"  Equation:     {summary['equation']}")
    print(f"  R-squared:    {summary['r_squared']:.4f}")
    print(f"  Prediction for x=15: {lr.predict(15):.2f}")

    # Outlier Detection
    print("\n[*] OUTLIER DETECTION")
    print("-" * 60)

    data_with_outliers = [10, 12, 14, 13, 11, 100, 12, 13, 14, -50]
    print(f"Data: {data_with_outliers}")

    outliers_iqr = stats.detect_outliers_iqr(data_with_outliers)
    outliers_zscore = stats.detect_outliers_zscore(data_with_outliers)

    print(f"  IQR outliers:     {[v for _, v in outliers_iqr]}")
    print(f"  Z-score outliers: {[v for _, v in outliers_zscore]}")

    # DataFrame Demo
    print("\n[*] DATAFRAME OPERATIONS")
    print("-" * 60)

    df = DataFrame.from_dict({
        'name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'age': [25, 30, 35, 28, 32],
        'salary': [50000, 60000, 75000, 55000, 70000],
        'department': ['IT', 'HR', 'IT', 'Finance', 'IT']
    })

    print("Original DataFrame:")
    print(df)

    print("\nFiltered (age > 28):")
    filtered = df.filter(lambda row: row['age'] > 28)
    print(filtered)

    print("\nGrouped by department:")
    groups = df.group_by('department')
    for dept, group_df in groups.items():
        print(f"  {dept}: {len(group_df)} employees")

    print("\n[*] Demo completed!")


if __name__ == "__main__":
    run_demo()
