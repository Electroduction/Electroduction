"""
Baseline Comparison Testing System
Compares fine-tuned models against GPT-4 and Claude

Usage:
    python baseline_comparison.py --project finance --test-cases 100
    python baseline_comparison.py --project all --models gpt4 claude
"""

import os
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import statistics

# Optional AI libraries
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    print("OpenAI library not installed. Install: pip install openai")

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = False
except ImportError:
    HAS_ANTHROPIC = False
    print("Anthropic library not installed. Install: pip install anthropic")

from dotenv import load_dotenv

load_dotenv()


@dataclass
class TestCase:
    """Single test case"""
    id: str
    project: str
    task_type: str
    input_data: Dict
    expected_output: Optional[Dict] = None
    ground_truth: Optional[str] = None


@dataclass
class ModelResponse:
    """Response from a model"""
    model_name: str
    response: str
    latency_ms: float
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None


@dataclass
class ComparisonResult:
    """Results of comparing models on a test case"""
    test_case_id: str
    project: str
    task_type: str
    responses: Dict[str, ModelResponse]
    scores: Dict[str, float]
    winner: Optional[str] = None
    human_preference: Optional[str] = None


class BaselineModel:
    """Base class for baseline models"""

    def __init__(self, model_name: str):
        self.model_name = model_name

    def generate(self, prompt: str) -> tuple[str, float]:
        """Generate response. Returns (response, latency_ms)"""
        raise NotImplementedError


class GPT4Model(BaselineModel):
    """GPT-4 baseline model"""

    def __init__(self):
        super().__init__("gpt-4")
        if not HAS_OPENAI:
            raise ImportError("OpenAI library required")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.client = OpenAI(api_key=api_key)

    def generate(self, prompt: str) -> tuple[str, float, int, float]:
        """Generate with GPT-4"""
        start_time = time.time()

        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7
        )

        latency_ms = (time.time() - start_time) * 1000

        tokens = response.usage.total_tokens
        # GPT-4 pricing: ~$0.03/1K input, ~$0.06/1K output tokens
        cost = (response.usage.prompt_tokens * 0.03 + response.usage.completion_tokens * 0.06) / 1000

        return response.choices[0].message.content, latency_ms, tokens, cost


class ClaudeModel(BaselineModel):
    """Claude baseline model"""

    def __init__(self):
        super().__init__("claude-3-sonnet")

        if not HAS_ANTHROPIC:
            raise ImportError("Anthropic library required")

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")

        self.client = Anthropic(api_key=api_key)

    def generate(self, prompt: str) -> tuple[str, float, int, float]:
        """Generate with Claude"""
        start_time = time.time()

        response = self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        latency_ms = (time.time() - start_time) * 1000

        tokens = response.usage.input_tokens + response.usage.output_tokens
        # Claude pricing: ~$0.003/1K input, ~$0.015/1K output
        cost = (response.usage.input_tokens * 0.003 + response.usage.output_tokens * 0.015) / 1000

        return response.content[0].text, latency_ms, tokens, cost


class FineTunedModel(BaselineModel):
    """Our fine-tuned model"""

    def __init__(self, project: str):
        super().__init__(f"finetuned-{project}")
        self.project = project

        # In production, load actual fine-tuned model
        # For now, simulate with project-specific responses

    def generate(self, prompt: str) -> tuple[str, float, int, float]:
        """Generate with fine-tuned model"""
        start_time = time.time()

        # Simulate generation (replace with actual model inference)
        response = f"[Fine-tuned {self.project} model response to: {prompt[:100]}...]"

        # Simulate latency (fine-tuned should be faster)
        time.sleep(0.1)  # Simulate 100ms inference

        latency_ms = (time.time() - start_time) * 1000

        # Estimate tokens and cost
        tokens = len(prompt.split()) + 50  # Rough estimate
        cost = 0.001  # Fine-tuned typically cheaper

        return response, latency_ms, tokens, cost


class TestCaseGenerator:
    """Generate test cases for each project"""

    @staticmethod
    def generate_finance_tests(count: int = 10) -> List[TestCase]:
        """Generate finance test cases"""
        tests = []

        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA", "AMD", "INTC", "NFLX"]

        for i, ticker in enumerate(tickers[:count]):
            tests.append(TestCase(
                id=f"finance_{i+1}",
                project="finance",
                task_type="stock_analysis",
                input_data={
                    "ticker": ticker,
                    "question": f"Analyze {ticker} from a fundamental perspective. What are the key metrics?"
                },
                expected_output={
                    "metrics": ["PE_ratio", "PB_ratio", "debt_to_equity", "ROE"],
                    "assessment": "valuation_and_health"
                }
            ))

        return tests

    @staticmethod
    def generate_game_dev_tests(count: int = 10) -> List[TestCase]:
        """Generate game dev test cases"""
        tests = []

        scenarios = [
            ("platformer", "pixel_art", "character"),
            ("rpg", "anime", "warrior"),
            ("fps", "realistic", "weapon"),
            ("puzzle", "minimalist", "block"),
            ("racing", "low_poly", "car"),
        ]

        for i, (genre, style, asset_type) in enumerate(scenarios[:count]):
            tests.append(TestCase(
                id=f"gamedev_{i+1}",
                project="game_dev",
                task_type="asset_generation",
                input_data={
                    "genre": genre,
                    "style": style,
                    "asset_type": asset_type,
                    "question": f"Generate a {asset_type} for a {genre} game in {style} style"
                }
            ))

        return tests

    @staticmethod
    def generate_music_tests(count: int = 10) -> List[TestCase]:
        """Generate music test cases"""
        tests = []

        genres = ["lo-fi", "edm", "jazz", "rock", "classical", "hip-hop", "blues", "reggae"]

        for i, genre in enumerate(genres[:count]):
            tests.append(TestCase(
                id=f"music_{i+1}",
                project="music",
                task_type="music_generation",
                input_data={
                    "genre": genre,
                    "duration": 30,
                    "question": f"Generate a {genre} track with appropriate tempo and feel"
                }
            ))

        return tests

    @staticmethod
    def generate_creativity_tests(count: int = 10) -> List[TestCase]:
        """Generate creativity test cases"""
        tests = []

        problems = [
            "Create a new social media app concept",
            "Design an innovative kitchen gadget",
            "Invent a new board game",
            "Brainstorm eco-friendly packaging solutions",
            "Generate story ideas for a sci-fi novel",
        ]

        for i, problem in enumerate(problems[:count]):
            tests.append(TestCase(
                id=f"creativity_{i+1}",
                project="creativity",
                task_type="idea_generation",
                input_data={
                    "problem": problem,
                    "question": f"Generate 5 creative ideas for: {problem}"
                }
            ))

        return tests


class ComparisonEngine:
    """Compare models on test cases"""

    def __init__(self, output_dir: str = "test_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.models = {}

    def add_model(self, model: BaselineModel):
        """Add a model to compare"""
        self.models[model.model_name] = model

    def run_test_case(self, test_case: TestCase) -> ComparisonResult:
        """Run a single test case"""
        print(f"\nTesting: {test_case.id} - {test_case.task_type}")

        # Build prompt
        prompt = test_case.input_data.get("question", str(test_case.input_data))

        responses = {}

        # Run each model
        for model_name, model in self.models.items():
            print(f"  Running {model_name}...", end=" ")

            try:
                response_text, latency, tokens, cost = model.generate(prompt)

                responses[model_name] = ModelResponse(
                    model_name=model_name,
                    response=response_text,
                    latency_ms=latency,
                    tokens_used=tokens,
                    cost_usd=cost
                )

                print(f"✓ ({latency:.0f}ms, ${cost:.4f})")

            except Exception as e:
                print(f"✗ Error: {e}")
                responses[model_name] = ModelResponse(
                    model_name=model_name,
                    response=f"ERROR: {e}",
                    latency_ms=0,
                    tokens_used=0,
                    cost_usd=0
                )

        # Score responses (simplified - in production use proper metrics)
        scores = self._score_responses(test_case, responses)

        # Determine winner
        winner = max(scores.items(), key=lambda x: x[1])[0] if scores else None

        result = ComparisonResult(
            test_case_id=test_case.id,
            project=test_case.project,
            task_type=test_case.task_type,
            responses=responses,
            scores=scores,
            winner=winner
        )

        return result

    def _score_responses(self, test_case: TestCase, responses: Dict[str, ModelResponse]) -> Dict[str, float]:
        """Score responses (simplified scoring)"""
        scores = {}

        for model_name, response in responses.items():
            score = 0.5  # Base score

            # Length check (prefer substantial responses)
            if len(response.response) > 100:
                score += 0.1

            # Latency bonus (faster is better)
            if response.latency_ms < 2000:
                score += 0.1

            # Cost bonus (cheaper is better)
            if response.cost_usd and response.cost_usd < 0.01:
                score += 0.1

            # Project-specific bonuses
            if test_case.project == "finance":
                # Check for financial terms
                terms = ["P/E", "ratio", "debt", "equity", "ROE", "valuation"]
                if any(term.lower() in response.response.lower() for term in terms):
                    score += 0.2

            scores[model_name] = min(score, 1.0)

        return scores

    def run_comparison(self, test_cases: List[TestCase]) -> List[ComparisonResult]:
        """Run comparison on all test cases"""
        results = []

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"Test Case {i}/{len(test_cases)}")
            print(f"{'='*80}")

            result = self.run_test_case(test_case)
            results.append(result)

            # Save intermediate results
            self._save_result(result)

        return results

    def _save_result(self, result: ComparisonResult):
        """Save individual result"""
        filename = f"{result.project}_{result.test_case_id}.json"
        filepath = self.output_dir / filename

        # Convert to dict (simplified)
        result_dict = {
            "test_case_id": result.test_case_id,
            "project": result.project,
            "task_type": result.task_type,
            "winner": result.winner,
            "scores": result.scores,
            "responses": {
                name: {
                    "model": resp.model_name,
                    "response_preview": resp.response[:200],
                    "latency_ms": resp.latency_ms,
                    "tokens": resp.tokens_used,
                    "cost_usd": resp.cost_usd
                }
                for name, resp in result.responses.items()
            }
        }

        with open(filepath, 'w') as f:
            json.dump(result_dict, f, indent=2)

    def generate_report(self, results: List[ComparisonResult]):
        """Generate comparison report"""
        print(f"\n{'='*80}")
        print("COMPARISON REPORT")
        print(f"{'='*80}\n")

        # Overall statistics
        total_tests = len(results)
        projects = list(set(r.project for r in results))

        print(f"Total Tests: {total_tests}")
        print(f"Projects: {', '.join(projects)}")
        print(f"\nModels Compared: {', '.join(self.models.keys())}\n")

        # Win rates
        wins = {model: 0 for model in self.models.keys()}
        for result in results:
            if result.winner:
                wins[result.winner] += 1

        print("Win Rates:")
        for model, win_count in sorted(wins.items(), key=lambda x: x[1], reverse=True):
            win_rate = (win_count / total_tests * 100) if total_tests > 0 else 0
            print(f"  {model:30s}: {win_count:3d} wins ({win_rate:5.1f}%)")

        # Average scores
        avg_scores = {model: [] for model in self.models.keys()}
        for result in results:
            for model, score in result.scores.items():
                avg_scores[model].append(score)

        print("\nAverage Scores:")
        for model in self.models.keys():
            if avg_scores[model]:
                avg = statistics.mean(avg_scores[model])
                print(f"  {model:30s}: {avg:.3f}")

        # Performance metrics
        latencies = {model: [] for model in self.models.keys()}
        costs = {model: [] for model in self.models.keys()}

        for result in results:
            for model_name, response in result.responses.items():
                latencies[model_name].append(response.latency_ms)
                if response.cost_usd:
                    costs[model_name].append(response.cost_usd)

        print("\nAverage Latency (ms):")
        for model in self.models.keys():
            if latencies[model]:
                avg_latency = statistics.mean(latencies[model])
                print(f"  {model:30s}: {avg_latency:7.1f} ms")

        print("\nAverage Cost (USD):")
        for model in self.models.keys():
            if costs[model]:
                avg_cost = statistics.mean(costs[model])
                total_cost = sum(costs[model])
                print(f"  {model:30s}: ${avg_cost:.5f} per test (Total: ${total_cost:.4f})")

        # Save report
        report_file = self.output_dir / "comparison_report.json"
        report_data = {
            "total_tests": total_tests,
            "projects": projects,
            "models": list(self.models.keys()),
            "win_rates": {model: wins[model] / total_tests for model in wins.keys()},
            "average_scores": {model: statistics.mean(scores) for model, scores in avg_scores.items() if scores},
            "average_latency": {model: statistics.mean(lat) for model, lat in latencies.items() if lat},
            "average_cost": {model: statistics.mean(c) for model, c in costs.items() if c}
        }

        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        print(f"\nDetailed report saved to: {report_file}")
        print(f"{'='*80}\n")


def main():
    parser = argparse.ArgumentParser(description="Baseline Comparison Testing")
    parser.add_argument(
        "--project",
        choices=["all", "finance", "game_dev", "music", "creativity"],
        default="finance",
        help="Which project to test"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        choices=["gpt4", "claude", "finetuned"],
        default=["gpt4", "finetuned"],
        help="Models to compare"
    )
    parser.add_argument("--test-cases", type=int, default=5, help="Number of test cases")
    parser.add_argument("--output-dir", default="test_results", help="Output directory")

    args = parser.parse_args()

    # Initialize comparison engine
    engine = ComparisonEngine(output_dir=args.output_dir)

    # Add models
    if "gpt4" in args.models:
        try:
            engine.add_model(GPT4Model())
        except Exception as e:
            print(f"Warning: Could not initialize GPT-4: {e}")

    if "claude" in args.models:
        try:
            engine.add_model(ClaudeModel())
        except Exception as e:
            print(f"Warning: Could not initialize Claude: {e}")

    if "finetuned" in args.models:
        engine.add_model(FineTunedModel(args.project))

    # Generate test cases
    generator = TestCaseGenerator()

    if args.project == "finance":
        test_cases = generator.generate_finance_tests(args.test_cases)
    elif args.project == "game_dev":
        test_cases = generator.generate_game_dev_tests(args.test_cases)
    elif args.project == "music":
        test_cases = generator.generate_music_tests(args.test_cases)
    elif args.project == "creativity":
        test_cases = generator.generate_creativity_tests(args.test_cases)
    else:  # all
        test_cases = (
            generator.generate_finance_tests(2) +
            generator.generate_game_dev_tests(2) +
            generator.generate_music_tests(2) +
            generator.generate_creativity_tests(2)
        )

    # Run comparison
    print(f"\n{'='*80}")
    print("BASELINE COMPARISON TEST")
    print(f"{'='*80}")
    print(f"Project: {args.project}")
    print(f"Models: {', '.join(args.models)}")
    print(f"Test Cases: {len(test_cases)}")
    print(f"{'='*80}\n")

    results = engine.run_comparison(test_cases)

    # Generate report
    engine.generate_report(results)


if __name__ == "__main__":
    main()
