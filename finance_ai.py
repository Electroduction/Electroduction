"""
Finance AI Education Tool
Provides fundamental analysis and financial education using AI

Usage:
    python finance_ai.py --mode analyze --ticker AAPL
    python finance_ai.py --mode learn --topic "PE ratio"
"""

import os
import json
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import numpy as np

# Financial data libraries
try:
    import yfinance as yf
    import pandas as pd
    HAS_FINANCE_LIBS = True
except ImportError:
    print("Finance libraries not installed.")
    print("Install with: pip install yfinance pandas numpy")
    HAS_FINANCE_LIBS = False

# ML libraries
try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    import torch
    HAS_ML = True
except ImportError:
    print("ML libraries not installed. Running in demo mode.")
    print("Install with: pip install transformers torch")
    HAS_ML = False


@dataclass
class FinancialMetrics:
    """Container for financial metrics"""
    ticker: str
    price: float
    market_cap: float
    pe_ratio: Optional[float]
    pb_ratio: Optional[float]
    debt_to_equity: Optional[float]
    roe: Optional[float]
    current_ratio: Optional[float]
    quick_ratio: Optional[float]


@dataclass
class AnalysisResult:
    """Complete financial analysis result"""
    ticker: str
    metrics: FinancialMetrics
    valuation_assessment: str
    financial_health: str
    ai_insights: str
    educational_notes: Dict[str, str]
    risk_assessment: Dict
    probability_distribution: Dict


class FinancialKnowledgeBase:
    """Knowledge base of financial concepts and metrics"""

    def __init__(self):
        self.concepts = {
            "pe_ratio": {
                "name": "Price-to-Earnings Ratio",
                "formula": "Stock Price / Earnings Per Share",
                "interpretation": {
                    "low": "< 15: Potentially undervalued or low growth expectations",
                    "average": "15-25: Fair valuation for average company",
                    "high": "> 25: High growth expectations or potentially overvalued"
                },
                "limitations": "Doesn't work for companies with no earnings. Varies by industry.",
                "examples": "Tech companies often have higher P/E ratios than utilities."
            },
            "pb_ratio": {
                "name": "Price-to-Book Ratio",
                "formula": "Stock Price / Book Value Per Share",
                "interpretation": {
                    "low": "< 1: Trading below book value, possible value opportunity",
                    "average": "1-3: Reasonable valuation",
                    "high": "> 3: Premium valuation, investors expect growth"
                },
                "limitations": "Book value may not reflect true asset value. Less relevant for service companies.",
                "examples": "Manufacturing companies typically have lower P/B than software companies."
            },
            "debt_to_equity": {
                "name": "Debt-to-Equity Ratio",
                "formula": "Total Debt / Total Equity",
                "interpretation": {
                    "low": "< 0.5: Conservative, low financial risk",
                    "average": "0.5-2.0: Reasonable leverage",
                    "high": "> 2.0: High leverage, increased financial risk"
                },
                "limitations": "Optimal level varies by industry. Capital-intensive industries naturally have higher ratios.",
                "examples": "Utilities often have higher D/E than tech companies."
            },
            "roe": {
                "name": "Return on Equity",
                "formula": "(Net Income / Shareholder Equity) * 100",
                "interpretation": {
                    "low": "< 10%: Poor returns for shareholders",
                    "average": "10-20%: Good returns",
                    "high": "> 20%: Excellent returns"
                },
                "limitations": "Can be inflated by high debt. One-time events can distort.",
                "examples": "Banks typically have lower ROE than tech companies."
            }
        }

    def get_concept(self, concept_key: str) -> Optional[Dict]:
        return self.concepts.get(concept_key.lower().replace(" ", "_"))

    def explain_metric(self, metric_name: str, value: float, industry: str = "general") -> str:
        """Provide educational explanation of a metric"""
        concept = self.get_concept(metric_name)
        if not concept:
            return f"No explanation available for {metric_name}"

        explanation = f"\n{concept['name']}\n"
        explanation += f"Formula: {concept['formula']}\n"
        explanation += f"Your value: {value:.2f}\n\n"

        # Interpret the value
        explanation += "Interpretation:\n"
        for level, desc in concept['interpretation'].items():
            explanation += f"  • {desc}\n"

        explanation += f"\nLimitations: {concept['limitations']}\n"
        explanation += f"Example: {concept['examples']}\n"

        return explanation


class FinancialAnalyzer:
    """Performs fundamental financial analysis"""

    def __init__(self):
        self.knowledge_base = FinancialKnowledgeBase()

    def fetch_stock_data(self, ticker: str) -> Optional[yf.Ticker]:
        """Fetch stock data from Yahoo Finance"""
        if not HAS_FINANCE_LIBS:
            print("yfinance not available")
            return None

        try:
            stock = yf.Ticker(ticker)
            # Test if valid
            _ = stock.info
            return stock
        except Exception as e:
            print(f"Error fetching {ticker}: {e}")
            return None

    def calculate_metrics(self, ticker: str) -> Optional[FinancialMetrics]:
        """Calculate key financial metrics"""
        stock = self.fetch_stock_data(ticker)
        if not stock:
            return None

        try:
            info = stock.info

            metrics = FinancialMetrics(
                ticker=ticker,
                price=info.get('currentPrice', info.get('regularMarketPrice', 0)),
                market_cap=info.get('marketCap', 0),
                pe_ratio=info.get('trailingPE'),
                pb_ratio=info.get('priceToBook'),
                debt_to_equity=info.get('debtToEquity'),
                roe=info.get('returnOnEquity'),
                current_ratio=info.get('currentRatio'),
                quick_ratio=info.get('quickRatio')
            )

            return metrics

        except Exception as e:
            print(f"Error calculating metrics: {e}")
            return None

    def assess_valuation(self, metrics: FinancialMetrics) -> str:
        """Assess company valuation"""
        assessment = []

        # P/E Analysis
        if metrics.pe_ratio:
            if metrics.pe_ratio < 15:
                assessment.append(f"P/E of {metrics.pe_ratio:.2f} suggests potential undervaluation or low growth expectations")
            elif metrics.pe_ratio > 25:
                assessment.append(f"P/E of {metrics.pe_ratio:.2f} indicates high growth expectations or potential overvaluation")
            else:
                assessment.append(f"P/E of {metrics.pe_ratio:.2f} is in reasonable range")

        # P/B Analysis
        if metrics.pb_ratio:
            if metrics.pb_ratio < 1:
                assessment.append(f"P/B of {metrics.pb_ratio:.2f} - trading below book value")
            elif metrics.pb_ratio > 3:
                assessment.append(f"P/B of {metrics.pb_ratio:.2f} - premium valuation")

        return "\n".join(assessment) if assessment else "Insufficient data for valuation assessment"

    def assess_financial_health(self, metrics: FinancialMetrics) -> str:
        """Assess company's financial health"""
        health = []

        # Debt Analysis
        if metrics.debt_to_equity is not None:
            if metrics.debt_to_equity < 0.5:
                health.append(f"D/E of {metrics.debt_to_equity:.2f} - Conservative debt levels, low financial risk")
            elif metrics.debt_to_equity > 2.0:
                health.append(f"D/E of {metrics.debt_to_equity:.2f} - High leverage, elevated financial risk")
            else:
                health.append(f"D/E of {metrics.debt_to_equity:.2f} - Reasonable debt levels")

        # Profitability
        if metrics.roe:
            roe_pct = metrics.roe * 100
            if roe_pct > 20:
                health.append(f"ROE of {roe_pct:.1f}% - Excellent returns on equity")
            elif roe_pct > 10:
                health.append(f"ROE of {roe_pct:.1f}% - Good returns on equity")
            else:
                health.append(f"ROE of {roe_pct:.1f}% - Below average returns")

        # Liquidity
        if metrics.current_ratio:
            if metrics.current_ratio > 2.0:
                health.append(f"Current ratio of {metrics.current_ratio:.2f} - Strong liquidity position")
            elif metrics.current_ratio < 1.0:
                health.append(f"Current ratio of {metrics.current_ratio:.2f} - Potential liquidity concerns")

        return "\n".join(health) if health else "Insufficient data for health assessment"

    def calculate_risk_metrics(self, ticker: str) -> Dict:
        """Calculate risk-related metrics"""
        stock = self.fetch_stock_data(ticker)
        if not stock:
            return {"error": "Unable to fetch data"}

        try:
            # Get historical data
            hist = stock.history(period="1y")

            if hist.empty:
                return {"error": "No historical data"}

            returns = hist['Close'].pct_change().dropna()

            # Calculate metrics
            volatility = returns.std() * np.sqrt(252)  # Annualized
            max_drawdown = (hist['Close'] / hist['Close'].cummax() - 1).min()
            sharpe_ratio = (returns.mean() * 252) / (returns.std() * np.sqrt(252)) if returns.std() > 0 else 0

            # Value at Risk (simple historical method)
            var_95 = np.percentile(returns, 5)
            var_99 = np.percentile(returns, 1)

            return {
                "volatility": volatility,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
                "value_at_risk": {
                    "95%": var_95,
                    "99%": var_99
                }
            }

        except Exception as e:
            return {"error": str(e)}


class FinancialAITutor:
    """AI-powered financial education tutor"""

    def __init__(self, use_gpu: bool = True):
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.knowledge_base = FinancialKnowledgeBase()

        if HAS_ML:
            self._load_model()
        else:
            self.model = None

    def _load_model(self):
        """Load fine-tuned financial LLM"""
        print(f"Loading financial AI model on {self.device}...")

        try:
            # In production, this would be a fine-tuned model
            model_name = "meta-llama/Llama-2-7b-chat-hf"  # Placeholder

            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto"
            )

            print("Model loaded successfully")
        except Exception as e:
            print(f"Error loading model: {e}")
            self.model = None

    def generate_insights(self, metrics: FinancialMetrics, context: Dict) -> str:
        """Generate AI insights about the company"""

        if not HAS_ML or not self.model:
            # Rule-based fallback
            insights = f"Analysis of {metrics.ticker}:\n"
            insights += f"Market Cap: ${metrics.market_cap/1e9:.2f}B\n"

            if metrics.pe_ratio and metrics.pb_ratio:
                insights += f"Valuation appears "
                if metrics.pe_ratio < 15 and metrics.pb_ratio < 2:
                    insights += "potentially undervalued based on traditional metrics.\n"
                elif metrics.pe_ratio > 25:
                    insights += "expensive, suggesting high growth expectations.\n"
                else:
                    insights += "fairly valued by traditional metrics.\n"

            return insights

        # AI-generated insights
        prompt = f"""As a financial educator, analyze this company:

Ticker: {metrics.ticker}
Price: ${metrics.price}
P/E Ratio: {metrics.pe_ratio}
P/B Ratio: {metrics.pb_ratio}
Debt/Equity: {metrics.debt_to_equity}
ROE: {metrics.roe}

Risk Metrics:
Volatility: {context.get('volatility', 'N/A')}
Max Drawdown: {context.get('max_drawdown', 'N/A')}
Sharpe Ratio: {context.get('sharpe_ratio', 'N/A')}

Provide educational insights focusing on:
1. What these metrics tell us
2. Risks to consider
3. What questions an investor should ask

Insights:"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_length=500,
            temperature=0.7,
            do_sample=True
        )

        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response.split("Insights:")[-1].strip()

    def create_learning_module(self, concept: str) -> str:
        """Create an educational module about a financial concept"""
        concept_data = self.knowledge_base.get_concept(concept)

        if not concept_data:
            return f"No educational content available for '{concept}'"

        module = f"\n{'='*60}\n"
        module += f"LEARNING MODULE: {concept_data['name']}\n"
        module += f"{'='*60}\n\n"

        module += f"FORMULA:\n{concept_data['formula']}\n\n"

        module += "INTERPRETATION GUIDE:\n"
        for level, desc in concept_data['interpretation'].items():
            module += f"  {level.upper()}: {desc}\n"

        module += f"\nIMPORTANT LIMITATIONS:\n{concept_data['limitations']}\n"

        module += f"\nPRACTICAL EXAMPLE:\n{concept_data['examples']}\n"

        module += f"\n{'='*60}\n"

        return module


class FinanceAISystem:
    """Main Finance AI Education System"""

    def __init__(self, use_gpu: bool = True):
        self.analyzer = FinancialAnalyzer()
        self.ai_tutor = FinancialAITutor(use_gpu=use_gpu)

    def analyze_stock(self, ticker: str) -> Optional[AnalysisResult]:
        """Perform complete stock analysis"""
        print(f"\nAnalyzing {ticker}...")

        # Calculate metrics
        metrics = self.analyzer.calculate_metrics(ticker)
        if not metrics:
            print(f"Unable to analyze {ticker}")
            return None

        # Valuation assessment
        valuation = self.analyzer.assess_valuation(metrics)

        # Financial health
        health = self.analyzer.assess_financial_health(metrics)

        # Risk metrics
        risk = self.analyzer.calculate_risk_metrics(ticker)

        # AI insights
        context = {
            "volatility": risk.get("volatility"),
            "max_drawdown": risk.get("max_drawdown"),
            "sharpe_ratio": risk.get("sharpe_ratio")
        }
        ai_insights = self.ai_tutor.generate_insights(metrics, context)

        # Educational notes
        educational_notes = {}
        if metrics.pe_ratio:
            educational_notes["pe_ratio"] = self.analyzer.knowledge_base.explain_metric(
                "pe_ratio", metrics.pe_ratio
            )
        if metrics.debt_to_equity:
            educational_notes["debt_to_equity"] = self.analyzer.knowledge_base.explain_metric(
                "debt_to_equity", metrics.debt_to_equity
            )

        # Probability distribution (Jane Street-inspired)
        probability_dist = {
            "expected_return": 0.08,  # Placeholder - would be ML-predicted
            "confidence_interval": [0.02, 0.15],
            "probability_of_loss": 0.25,
            "uncertainty_factors": ["market volatility", "earnings uncertainty"]
        }

        result = AnalysisResult(
            ticker=ticker,
            metrics=metrics,
            valuation_assessment=valuation,
            financial_health=health,
            ai_insights=ai_insights,
            educational_notes=educational_notes,
            risk_assessment=risk,
            probability_distribution=probability_dist
        )

        return result

    def learn_concept(self, concept: str) -> str:
        """Learn about a financial concept"""
        return self.ai_tutor.create_learning_module(concept)

    def compare_stocks(self, tickers: List[str]) -> pd.DataFrame:
        """Compare multiple stocks"""
        if not HAS_FINANCE_LIBS:
            print("pandas required for comparison")
            return None

        comparison_data = []

        for ticker in tickers:
            metrics = self.analyzer.calculate_metrics(ticker)
            if metrics:
                comparison_data.append({
                    "Ticker": ticker,
                    "Price": metrics.price,
                    "P/E": metrics.pe_ratio,
                    "P/B": metrics.pb_ratio,
                    "D/E": metrics.debt_to_equity,
                    "ROE": metrics.roe
                })

        df = pd.DataFrame(comparison_data)
        return df

    def save_analysis(self, result: AnalysisResult, output_dir: str = "output"):
        """Save analysis to file"""
        os.makedirs(output_dir, exist_ok=True)

        filename = os.path.join(output_dir, f"{result.ticker}_analysis_{datetime.now().strftime('%Y%m%d')}.json")

        data = {
            "ticker": result.ticker,
            "analysis_date": datetime.now().isoformat(),
            "metrics": {
                "price": result.metrics.price,
                "market_cap": result.metrics.market_cap,
                "pe_ratio": result.metrics.pe_ratio,
                "pb_ratio": result.metrics.pb_ratio,
                "debt_to_equity": result.metrics.debt_to_equity,
                "roe": result.metrics.roe
            },
            "valuation": result.valuation_assessment,
            "health": result.financial_health,
            "ai_insights": result.ai_insights,
            "risk_assessment": result.risk_assessment,
            "probability_distribution": result.probability_distribution
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nAnalysis saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Finance AI Education Tool")
    parser.add_argument("--mode", choices=["analyze", "learn", "compare"], default="analyze")
    parser.add_argument("--ticker", help="Stock ticker to analyze")
    parser.add_argument("--tickers", nargs="+", help="Multiple tickers to compare")
    parser.add_argument("--topic", help="Financial concept to learn")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU")

    args = parser.parse_args()

    # Initialize system
    print("Initializing Finance AI System...")
    system = FinanceAISystem(use_gpu=not args.no_gpu)

    if args.mode == "analyze":
        if not args.ticker:
            print("Please provide --ticker for analysis")
            return

        result = system.analyze_stock(args.ticker)

        if result:
            print(f"\n{'='*60}")
            print(f"FINANCIAL ANALYSIS: {result.ticker}")
            print(f"{'='*60}\n")

            print(f"Price: ${result.metrics.price:.2f}")
            print(f"Market Cap: ${result.metrics.market_cap/1e9:.2f}B\n")

            print("VALUATION:")
            print(result.valuation_assessment)

            print("\nFINANCIAL HEALTH:")
            print(result.financial_health)

            print("\nRISK ASSESSMENT:")
            if "volatility" in result.risk_assessment:
                print(f"  Volatility: {result.risk_assessment['volatility']:.2%}")
                print(f"  Max Drawdown: {result.risk_assessment['max_drawdown']:.2%}")
                print(f"  Sharpe Ratio: {result.risk_assessment['sharpe_ratio']:.2f}")

            print("\nAI INSIGHTS:")
            print(result.ai_insights)

            print(f"\n{'='*60}")

            # Save analysis
            system.save_analysis(result)

    elif args.mode == "learn":
        if not args.topic:
            print("Available topics: pe_ratio, pb_ratio, debt_to_equity, roe")
            return

        module = system.learn_concept(args.topic)
        print(module)

    elif args.mode == "compare":
        if not args.tickers or len(args.tickers) < 2:
            print("Please provide --tickers for comparison (e.g., --tickers AAPL MSFT GOOGL)")
            return

        comparison = system.compare_stocks(args.tickers)
        if comparison is not None:
            print("\nCOMPARATIVE ANALYSIS:")
            print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
