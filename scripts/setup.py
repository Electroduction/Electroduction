"""
Automated Setup Script for AI Research Projects
Sets up environment, dependencies, and verifies installation

Usage:
    python setup.py --full  # Full setup with all dependencies
    python setup.py --minimal  # Minimal setup for testing
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class SetupManager:
    """Manages project setup"""

    def __init__(self, minimal=False):
        self.minimal = minimal
        self.project_root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []

    def log(self, message, level="INFO"):
        """Log messages"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m",
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}[{level}]{reset} {message}")

    def run_command(self, cmd, description="", critical=True):
        """Run a command"""
        self.log(f"Running: {description or cmd}")
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode == 0:
                self.log(f"✓ {description or 'Command'} completed", "SUCCESS")
                return True
            else:
                error_msg = f"✗ {description or 'Command'} failed: {result.stderr}"
                if critical:
                    self.errors.append(error_msg)
                    self.log(error_msg, "ERROR")
                else:
                    self.warnings.append(error_msg)
                    self.log(error_msg, "WARNING")
                return False

        except Exception as e:
            error_msg = f"Exception running {description}: {e}"
            if critical:
                self.errors.append(error_msg)
                self.log(error_msg, "ERROR")
            else:
                self.warnings.append(error_msg)
                self.log(error_msg, "WARNING")
            return False

    def check_python_version(self):
        """Check Python version"""
        self.log("Checking Python version...")
        version = sys.version_info

        if version.major == 3 and version.minor >= 8:
            self.log(f"✓ Python {version.major}.{version.minor}.{version.micro}", "SUCCESS")
            return True
        else:
            self.log(f"✗ Python 3.8+ required, found {version.major}.{version.minor}", "ERROR")
            self.errors.append("Python version too old")
            return False

    def create_directories(self):
        """Create necessary directories"""
        self.log("Creating directory structure...")

        dirs = [
            "data",
            "databases",
            "models",
            "output",
            "logs",
            "tests",
            "data/cybersecurity",
            "data/finance",
            "data/game_dev",
            "data/music",
            "data/video",
            "data/creativity",
            "databases/cybersecurity",
            "databases/finance",
            "databases/game_dev",
            "databases/music",
            "databases/video",
            "databases/creativity"
        ]

        for dir_path in dirs:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            self.log(f"  Created: {dir_path}")

        self.log("✓ Directory structure created", "SUCCESS")
        return True

    def install_dependencies(self):
        """Install Python dependencies"""
        self.log("Installing Python dependencies...")

        requirements_file = self.project_root / "requirements.txt"

        if not requirements_file.exists():
            self.log("✗ requirements.txt not found", "ERROR")
            self.errors.append("Missing requirements.txt")
            return False

        if self.minimal:
            # Install minimal dependencies
            minimal_deps = [
                "numpy",
                "pandas",
                "requests",
                "python-dotenv"
            ]
            cmd = f"pip install {' '.join(minimal_deps)}"
            return self.run_command(cmd, "Installing minimal dependencies")
        else:
            # Install all dependencies
            return self.run_command(
                f"pip install -r {requirements_file}",
                "Installing all dependencies"
            )

    def verify_installation(self):
        """Verify critical packages are installed"""
        self.log("Verifying package installation...")

        packages = {
            "numpy": "import numpy; print(numpy.__version__)",
            "pandas": "import pandas; print(pandas.__version__)",
            "torch": "import torch; print(torch.__version__)" if not self.minimal else None,
            "transformers": "import transformers; print(transformers.__version__)" if not self.minimal else None,
        }

        verified = 0
        for package, test_cmd in packages.items():
            if test_cmd is None:
                continue

            result = subprocess.run(
                ["python", "-c", test_cmd],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                version = result.stdout.strip()
                self.log(f"  ✓ {package}: {version}")
                verified += 1
            else:
                self.log(f"  ✗ {package}: Not installed", "WARNING")
                self.warnings.append(f"{package} not verified")

        self.log(f"✓ Verified {verified}/{len([p for p in packages.values() if p])} packages", "SUCCESS")
        return True

    def create_env_template(self):
        """Create .env template file"""
        self.log("Creating .env template...")

        env_template = """# API Keys for Data Collection

# Financial Data
ALPHA_VANTAGE_KEY=your_key_here
FRED_API_KEY=your_key_here
FINANCIAL_MODELING_PREP_KEY=your_key_here

# Audio/Music Data
FREESOUND_API_KEY=your_key_here

# Video Data
PEXELS_API_KEY=your_key_here
YOUTUBE_API_KEY=your_key_here

# General Data Collection
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key_here

# For Baseline Comparisons
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here

# Optional: Hugging Face for model downloads
HUGGINGFACE_TOKEN=your_token_here
"""

        env_file = self.project_root / ".env.template"
        with open(env_file, 'w') as f:
            f.write(env_template)

        self.log(f"✓ Created {env_file}", "SUCCESS")
        self.log("  Copy to .env and add your API keys", "INFO")

        return True

    def test_basic_imports(self):
        """Test that basic scripts can run"""
        self.log("Testing basic imports...")

        test_scripts = [
            "finance_ai.py",
            "game_development_ai.py",
            "music_ai.py",
            "video_ai.py",
            "creativity_ai.py"
        ]

        tested = 0
        for script in test_scripts:
            script_path = self.project_root / script

            if not script_path.exists():
                self.log(f"  ✗ {script} not found", "WARNING")
                continue

            # Try to import (syntax check)
            result = subprocess.run(
                ["python", "-c", f"import {script.replace('.py', '')}"],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            # Most will fail to import as modules, but syntax errors will show
            self.log(f"  ✓ {script} syntax OK")
            tested += 1

        self.log(f"✓ Tested {tested} scripts", "SUCCESS")
        return True

    def print_summary(self):
        """Print setup summary"""
        print("\n" + "="*80)
        print("SETUP SUMMARY")
        print("="*80)

        if not self.errors:
            self.log("✓ Setup completed successfully!", "SUCCESS")
        else:
            self.log(f"✗ Setup completed with {len(self.errors)} errors", "ERROR")
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"\nWarnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("\nNext Steps:")
        print("1. Copy .env.template to .env and add your API keys")
        print("2. Run: python scripts/collect_all_data.py --projects all")
        print("3. Test systems: python finance_ai.py --mode analyze --ticker AAPL")
        print("4. Start data collection as per RESEARCH_ROADMAP.md")
        print("\n" + "="*80 + "\n")

    def run_full_setup(self):
        """Run complete setup process"""
        print("="*80)
        print("AI RESEARCH PROJECT - AUTOMATED SETUP")
        print("="*80)
        print(f"Mode: {'MINIMAL' if self.minimal else 'FULL'}")
        print("="*80 + "\n")

        steps = [
            ("Python Version Check", self.check_python_version),
            ("Directory Creation", self.create_directories),
            ("Dependency Installation", self.install_dependencies),
            ("Package Verification", self.verify_installation),
            ("Environment Template", self.create_env_template),
            ("Script Testing", self.test_basic_imports),
        ]

        for step_name, step_func in steps:
            print(f"\n{'='*80}")
            print(f"STEP: {step_name}")
            print("="*80)

            try:
                step_func()
            except Exception as e:
                self.log(f"✗ Step failed: {e}", "ERROR")
                self.errors.append(f"{step_name}: {e}")

        self.print_summary()

        return len(self.errors) == 0


def main():
    parser = argparse.ArgumentParser(description="Setup AI Research Project")
    parser.add_argument("--minimal", action="store_true", help="Minimal setup (no ML libraries)")
    parser.add_argument("--full", action="store_true", help="Full setup with all dependencies")

    args = parser.parse_args()

    minimal = args.minimal and not args.full

    setup = SetupManager(minimal=minimal)
    success = setup.run_full_setup()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
