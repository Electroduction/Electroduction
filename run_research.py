"""
Master Script for AI Research Project
Runs the complete research pipeline: setup → data collection → testing

Usage:
    python run_research.py --phase setup
    python run_research.py --phase collect --projects all
    python run_research.py --phase test --project finance
    python run_research.py --phase full  # Run everything
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


class ResearchPipeline:
    """Manages the complete research pipeline"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.scripts_dir = self.project_root / "scripts"

    def log(self, message, level="INFO"):
        """Log messages with color"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "HEADER": "\033[95m",
            "RESET": "\033[0m"
        }
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}{message}{reset}")

    def run_command(self, cmd, description=""):
        """Run a command"""
        self.log(f"\n{'='*80}", "HEADER")
        self.log(f"RUNNING: {description or cmd}", "HEADER")
        self.log(f"{'='*80}\n", "HEADER")

        result = subprocess.run(cmd, shell=True, cwd=self.project_root)

        if result.returncode == 0:
            self.log(f"\n✓ {description or 'Command'} completed successfully", "SUCCESS")
            return True
        else:
            self.log(f"\n✗ {description or 'Command'} failed", "ERROR")
            return False

    def phase_setup(self, minimal=False):
        """Phase 1: Environment setup"""
        self.log("\n" + "="*80, "HEADER")
        self.log("PHASE 1: ENVIRONMENT SETUP", "HEADER")
        self.log("="*80 + "\n", "HEADER")

        mode = "--minimal" if minimal else "--full"
        return self.run_command(
            f"python {self.scripts_dir}/setup.py {mode}",
            "Setting up environment"
        )

    def phase_collect(self, projects=["all"]):
        """Phase 2: Data collection"""
        self.log("\n" + "="*80, "HEADER")
        self.log("PHASE 2: DATA COLLECTION", "HEADER")
        self.log("="*80 + "\n", "HEADER")

        projects_str = " ".join(projects)
        return self.run_command(
            f"python {self.scripts_dir}/collect_all_data.py --projects {projects_str}",
            f"Collecting data for: {projects_str}"
        )

    def phase_test(self, project="finance", models=["gpt4", "finetuned"], test_count=5):
        """Phase 3: Baseline testing"""
        self.log("\n" + "="*80, "HEADER")
        self.log("PHASE 3: BASELINE COMPARISON", "HEADER")
        self.log("="*80 + "\n", "HEADER")

        models_str = " ".join(models)
        return self.run_command(
            f"python {self.scripts_dir}/baseline_comparison.py --project {project} --models {models_str} --test-cases {test_count}",
            f"Testing {project} against {models_str}"
        )

    def phase_demo(self, project="finance"):
        """Demo phase: Run project demos"""
        self.log("\n" + "="*80, "HEADER")
        self.log(f"DEMO: {project.upper()} PROJECT", "HEADER")
        self.log("="*80 + "\n", "HEADER")

        demos = {
            "finance": "python finance_ai.py --mode analyze --ticker AAPL",
            "game_dev": "python game_development_ai.py --mode info",
            "music": "python music_ai.py --mode beat --genre lo-fi --tempo 80",
            "creativity": "python creativity_ai.py --mode ideate --problem 'Create new mobile app' --count 5"
        }

        cmd = demos.get(project, demos["finance"])
        return self.run_command(cmd, f"Running {project} demo")

    def run_full_pipeline(self, minimal=False, test_project="finance"):
        """Run the complete research pipeline"""
        self.log("\n" + "="*100, "HEADER")
        self.log("  AI RESEARCH PROJECT - FULL PIPELINE", "HEADER")
        self.log("="*100 + "\n", "HEADER")

        phases = [
            ("Setup", lambda: self.phase_setup(minimal)),
            ("Data Collection", lambda: self.phase_collect(["all"])),
            ("Demo", lambda: self.phase_demo(test_project)),
            ("Baseline Test", lambda: self.phase_test(test_project, test_count=3)),
        ]

        completed = 0
        failed = 0

        for phase_name, phase_func in phases:
            self.log(f"\n\n{'#'*100}", "HEADER")
            self.log(f"# PHASE: {phase_name}", "HEADER")
            self.log(f"{'#'*100}\n", "HEADER")

            try:
                success = phase_func()
                if success:
                    completed += 1
                    self.log(f"\n✓ Phase '{phase_name}' completed", "SUCCESS")
                else:
                    failed += 1
                    self.log(f"\n✗ Phase '{phase_name}' failed", "ERROR")
                    self.log("Continuing to next phase...", "WARNING")

            except Exception as e:
                failed += 1
                self.log(f"\n✗ Phase '{phase_name}' error: {e}", "ERROR")

        # Summary
        self.log("\n\n" + "="*100, "HEADER")
        self.log("PIPELINE SUMMARY", "HEADER")
        self.log("="*100, "HEADER")
        self.log(f"\nCompleted: {completed}/{len(phases)}", "SUCCESS" if failed == 0 else "WARNING")
        self.log(f"Failed: {failed}/{len(phases)}", "ERROR" if failed > 0 else "INFO")

        if failed == 0:
            self.log("\n✓ All phases completed successfully!", "SUCCESS")
            self.log("\nNext Steps:", "INFO")
            self.log("1. Review test results in: test_results/", "INFO")
            self.log("2. Check collected data in: data/ and databases/", "INFO")
            self.log("3. Begin fine-tuning as per RESEARCH_ROADMAP.md", "INFO")
        else:
            self.log("\n⚠ Some phases failed. Check logs above.", "WARNING")

        self.log("\n" + "="*100 + "\n", "HEADER")


def main():
    parser = argparse.ArgumentParser(description="AI Research Master Script")

    parser.add_argument(
        "--phase",
        choices=["setup", "collect", "test", "demo", "full"],
        default="full",
        help="Which phase to run"
    )

    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Minimal setup (no ML libraries)"
    )

    parser.add_argument(
        "--projects",
        nargs="+",
        default=["all"],
        help="Projects for data collection"
    )

    parser.add_argument(
        "--project",
        default="finance",
        help="Single project for testing/demo"
    )

    parser.add_argument(
        "--models",
        nargs="+",
        default=["gpt4", "finetuned"],
        help="Models to compare in testing"
    )

    parser.add_argument(
        "--test-count",
        type=int,
        default=5,
        help="Number of test cases"
    )

    args = parser.parse_args()

    pipeline = ResearchPipeline()

    if args.phase == "setup":
        pipeline.phase_setup(args.minimal)

    elif args.phase == "collect":
        pipeline.phase_collect(args.projects)

    elif args.phase == "test":
        pipeline.phase_test(args.project, args.models, args.test_count)

    elif args.phase == "demo":
        pipeline.phase_demo(args.project)

    elif args.phase == "full":
        pipeline.run_full_pipeline(args.minimal, args.project)


if __name__ == "__main__":
    main()
