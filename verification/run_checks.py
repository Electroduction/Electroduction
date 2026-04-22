"""
Verification Checklist Runner
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Runs automated checks on all system components and prints a pass/fail summary.
Run this after any major change to verify system integrity.

Usage:
    python verification/run_checks.py
    python verification/run_checks.py --quick   # skip slow checks

SELF-CORRECTION BLOCK:
    What Could Break:
      1. Import errors for optional deps (mcp, torch) — gracefully skipped
      2. DB files missing — collected separately via scripts/collect_all_data.py
      3. Docker not running — Docker checks marked as SKIP, not FAIL
    How to Test:
      python verification/run_checks.py
    How to Fix:
      Install missing deps: pip install -r requirements.txt
"""

import sys
import json
import time
import shutil
import importlib
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


# ─── Color output helpers ────────────────────────────────────────────────────

def green(s): return f"\033[92m{s}\033[0m"
def red(s):   return f"\033[91m{s}\033[0m"
def yellow(s): return f"\033[93m{s}\033[0m"
def cyan(s):  return f"\033[96m{s}\033[0m"
def bold(s):  return f"\033[1m{s}\033[0m"


class CheckResult:
    def __init__(self, name: str, passed: bool, message: str, skipped: bool = False):
        self.name = name
        self.passed = passed
        self.message = message
        self.skipped = skipped

    def __str__(self):
        if self.skipped:
            icon = yellow("SKIP")
        elif self.passed:
            icon = green("PASS")
        else:
            icon = red("FAIL")
        return f"  [{icon}] {self.name}: {self.message}"


class VerificationRunner:
    def __init__(self, quick: bool = False):
        self.quick = quick
        self.results: list[CheckResult] = []
        self.root = Path(__file__).parent.parent

    def check(self, name: str, fn) -> CheckResult:
        """Run a single check and record result."""
        try:
            result = fn()
            if result is True:
                r = CheckResult(name, True, "OK")
            elif result is False:
                r = CheckResult(name, False, "Check returned False")
            elif isinstance(result, dict):
                passed = result.get("passed", False)
                msg = result.get("message", "")
                skipped = result.get("skipped", False)
                r = CheckResult(name, passed, msg, skipped)
            else:
                r = CheckResult(name, True, str(result))
        except Exception as e:
            r = CheckResult(name, False, f"Exception: {e}")
        self.results.append(r)
        print(r)
        return r

    # ─── Individual Checks ────────────────────────────────────────────────

    def check_python_version(self) -> dict:
        major, minor = sys.version_info[:2]
        if major == 3 and minor >= 11:
            return {"passed": True, "message": f"Python {major}.{minor} ✓"}
        return {"passed": False, "message": f"Python {major}.{minor} — need 3.11+"}

    def check_required_files(self) -> dict:
        required = [
            "algorithms/router_agent.py",
            "algorithms/cpo_engine.py",
            "mcp_server/mcp_skill_server.py",
            "prompts/MASTER_ARCHITECT_PROMPT.md",
            "requirements.txt",
        ]
        missing = [f for f in required if not (self.root / f).exists()]
        if missing:
            return {"passed": False, "message": f"Missing: {', '.join(missing)}"}
        return {"passed": True, "message": f"All {len(required)} required files present"}

    def check_database_directories(self) -> dict:
        domains = ["cybersecurity", "finance", "game_dev", "music", "video", "creativity"]
        missing = []
        for d in domains:
            p = self.root / "data" / d
            if not p.exists():
                missing.append(d)
        if missing:
            return {"passed": False, "message": f"Missing data dirs: {', '.join(missing)}"}
        return {"passed": True, "message": f"All {len(domains)} domain data dirs present"}

    def check_databases_by_source(self) -> dict:
        domains = ["cybersecurity", "finance", "game_dev", "music", "video", "creativity"]
        missing = []
        for d in domains:
            p = self.root / "databases" / d / "by_source"
            if not p.exists():
                missing.append(d)
        if missing:
            return {"passed": False, "message": f"Missing by_source dirs: {', '.join(missing)}"}
        return {"passed": True, "message": "All by_source directories present"}

    def check_router_agent_import(self) -> dict:
        sys.path.insert(0, str(self.root))
        try:
            from algorithms.router_agent import RouterAgent, DOMAIN_KEYWORDS
            router = RouterAgent()
            decision = router.route("detect a Falco intrusion log")
            assert decision.domain == "cybersecurity", f"Expected cybersecurity, got {decision.domain}"
            assert decision.confidence > 0.5
            return {"passed": True, "message": f"RouterAgent OK — routed to '{decision.domain}'"}
        except Exception as e:
            return {"passed": False, "message": str(e)}

    def check_router_multi_domain(self) -> dict:
        sys.path.insert(0, str(self.root))
        try:
            from algorithms.router_agent import RouterAgent
            router = RouterAgent()
            decisions = router.route_multi("jazz chord progression for a game soundtrack", top_n=2)
            domains = [d.domain for d in decisions]
            assert len(decisions) >= 1
            return {"passed": True, "message": f"Multi-route OK — top domains: {domains}"}
        except Exception as e:
            return {"passed": False, "message": str(e)}

    def check_cpo_engine_import(self) -> dict:
        sys.path.insert(0, str(self.root))
        try:
            from algorithms.cpo_engine import CPOEngine, ActiveLearner
            engine = CPOEngine("_verify_test")
            triplet = engine.record(
                query="verify test query",
                generic_answer="generic answer",
                expert_results=[{"fact": "db fact", "source_file": "test.json"}],
            )
            assert triplet.confidence > 0.5
            assert triplet.domain == "_verify_test"

            learner = ActiveLearner(confidence_threshold=0.5)
            gap = learner.check("obscure query", "_verify_test", confidence=0.1)
            assert gap["is_knowledge_gap"] is True

            # Cleanup test file
            import shutil as sh
            test_file = Path("databases/cpo_triplets/_verify_test_triplets.jsonl")
            if test_file.exists():
                test_file.unlink()
            conflict_file = Path("databases/cpo_triplets/_verify_test_conflicts.csv")
            if conflict_file.exists():
                conflict_file.unlink()

            return {"passed": True, "message": f"CPOEngine OK — confidence={triplet.confidence:.2f}"}
        except Exception as e:
            return {"passed": False, "message": str(e)}

    def check_mcp_server_classes(self) -> dict:
        sys.path.insert(0, str(self.root))
        try:
            from mcp_server.mcp_skill_server import DatabaseConnector, CPOResolver, VerifierAgent
            connector = DatabaseConnector(self.root / "data")
            cpo = CPOResolver()
            verifier = VerifierAgent()

            # Test with empty domain (should return [])
            results = connector.query("_nonexistent_domain", "test query", top_k=3)
            assert isinstance(results, list)

            # Test CPO resolver with no DB results
            resolved = cpo.resolve("test", [], generic_answer="generic text")
            assert resolved["source"] == "generic_llm"
            assert "warning" in resolved

            # Test VerifierAgent blocks rm -rf
            check = verifier.verify("run rm -rf /tmp/test", "cybersecurity")
            assert check["passed"] is False
            assert len(check["issues"]) > 0

            return {"passed": True, "message": "DatabaseConnector, CPOResolver, VerifierAgent all OK"}
        except Exception as e:
            return {"passed": False, "message": str(e)}

    def check_mcp_installed(self) -> dict:
        try:
            import mcp
            return {"passed": True, "message": f"mcp installed ({mcp.__version__ if hasattr(mcp, '__version__') else 'version unknown'})"}
        except ImportError:
            return {"passed": False, "message": "mcp not installed — run: pip install mcp", "skipped": False}

    def check_docker_available(self) -> dict:
        if shutil.which("docker") is None:
            return {"passed": False, "message": "docker not in PATH", "skipped": True}
        try:
            result = subprocess.run(
                ["docker", "info"], capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return {"passed": True, "message": "Docker daemon running"}
            return {"passed": False, "message": "Docker not running", "skipped": True}
        except Exception as e:
            return {"passed": False, "message": f"Docker check failed: {e}", "skipped": True}

    def check_sandbox_dockerfile(self) -> dict:
        df = self.root / "sandbox" / "Dockerfile"
        compose = self.root / "sandbox" / "docker-compose.yml"
        missing = []
        if not df.exists():
            missing.append("Dockerfile")
        if not compose.exists():
            missing.append("docker-compose.yml")
        if missing:
            return {"passed": False, "message": f"Missing: {', '.join(missing)}"}
        return {"passed": True, "message": "Sandbox Dockerfile and docker-compose.yml present"}

    def check_cpo_latency(self) -> dict:
        if self.quick:
            return {"passed": True, "message": "Skipped in quick mode", "skipped": True}
        sys.path.insert(0, str(self.root))
        try:
            from algorithms.router_agent import RouterAgent
            router = RouterAgent()
            start = time.perf_counter()
            for _ in range(100):
                router.route("detect a malware phishing attack via Falco intrusion log")
            elapsed = (time.perf_counter() - start) * 1000  # ms for 100 calls
            per_call = elapsed / 100
            if per_call < 5:
                return {"passed": True, "message": f"Router latency: {per_call:.2f}ms/call ✓"}
            return {"passed": False, "message": f"Router latency: {per_call:.2f}ms/call — too slow (>5ms)"}
        except Exception as e:
            return {"passed": False, "message": str(e)}

    def check_data_files_loadable(self) -> dict:
        test_files = [
            "data/finance/sample_metrics.json",
            "data/music/music_theory.json",
            "data/game_dev/genre_taxonomy.json",
            "data/creativity/story_structures_detailed.json",
        ]
        errors = []
        for rel_path in test_files:
            full = self.root / rel_path
            if not full.exists():
                errors.append(f"{rel_path} missing")
                continue
            try:
                with open(full) as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                errors.append(f"{rel_path}: {e}")
        if errors:
            return {"passed": False, "message": "; ".join(errors)}
        return {"passed": True, "message": f"{len(test_files)} JSON files valid"}

    def check_pytest_available(self) -> dict:
        if shutil.which("pytest") is None and importlib.util.find_spec("pytest") is None:
            return {"passed": False, "message": "pytest not installed — run: pip install pytest"}
        return {"passed": True, "message": "pytest available"}

    def check_tests_exist(self) -> dict:
        test_dir = self.root / "tests"
        if not test_dir.exists():
            return {"passed": False, "message": "tests/ directory missing"}
        test_files = list(test_dir.glob("test_*.py"))
        if not test_files:
            return {"passed": False, "message": "No test_*.py files in tests/"}
        return {"passed": True, "message": f"{len(test_files)} test file(s): {[f.name for f in test_files]}"}

    def check_env_file(self) -> dict:
        env = self.root / ".env"
        env_example = self.root / ".env.example"
        if env.exists():
            return {"passed": True, "message": ".env file present"}
        if env_example.exists():
            return {"passed": False, "message": ".env missing — copy .env.example and fill in keys"}
        return {"passed": False, "message": "Neither .env nor .env.example found"}

    def check_cpo_export_format(self) -> dict:
        """Verify CPO export produces valid HuggingFace DPO JSONL."""
        sys.path.insert(0, str(self.root))
        try:
            from algorithms.cpo_engine import CPOEngine
            engine = CPOEngine("_export_verify")
            engine.record("test export q", "generic", [{"data": "expert", "source_file": "x.json"}])
            out = engine.export_for_finetuning()
            with open(out) as f:
                record = json.loads(f.readline())
            assert "prompt" in record
            assert "chosen" in record
            assert "rejected" in record
            # Cleanup
            out.unlink(missing_ok=True)
            Path("databases/cpo_triplets/_export_verify_triplets.jsonl").unlink(missing_ok=True)
            Path("databases/cpo_triplets/_export_verify_conflicts.csv").unlink(missing_ok=True)
            return {"passed": True, "message": "DPO export format valid (prompt/chosen/rejected)"}
        except Exception as e:
            return {"passed": False, "message": str(e)}

    # ─── Runner ───────────────────────────────────────────────────────────

    def run_all(self):
        print(bold(cyan("\n" + "=" * 60)))
        print(bold(cyan("  ELECTRODUCTION SYSTEM VERIFICATION CHECKLIST")))
        print(bold(cyan("  " + datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"))))
        print(bold(cyan("=" * 60 + "\n")))

        sections = [
            ("Environment", [
                ("Python ≥ 3.11", self.check_python_version),
                ("pytest available", self.check_pytest_available),
                ("Docker available", self.check_docker_available),
                ("MCP installed", self.check_mcp_installed),
                (".env file", self.check_env_file),
            ]),
            ("Project Structure", [
                ("Required files", self.check_required_files),
                ("Data directories", self.check_database_directories),
                ("Databases by_source", self.check_databases_by_source),
                ("Sandbox Dockerfile", self.check_sandbox_dockerfile),
                ("Test files exist", self.check_tests_exist),
            ]),
            ("Algorithm Modules", [
                ("RouterAgent import + route", self.check_router_agent_import),
                ("RouterAgent multi-domain", self.check_router_multi_domain),
                ("CPOEngine record + ActiveLearner", self.check_cpo_engine_import),
                ("CPO export DPO format", self.check_cpo_export_format),
                ("MCP server classes", self.check_mcp_server_classes),
            ]),
            ("Data Quality", [
                ("JSON files loadable", self.check_data_files_loadable),
            ]),
            ("Performance", [
                ("Router latency <5ms", self.check_cpo_latency),
            ]),
        ]

        for section_name, checks in sections:
            print(bold(f"\n── {section_name} ──"))
            for check_name, fn in checks:
                self.check(check_name, fn)

        self._print_summary()

    def _print_summary(self):
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed and not r.skipped)
        skipped = sum(1 for r in self.results if r.skipped)
        failed = sum(1 for r in self.results if not r.passed and not r.skipped)

        print(bold(cyan("\n" + "=" * 60)))
        print(bold("  SUMMARY"))
        print(bold(cyan("=" * 60)))
        print(f"  {green(f'PASSED:  {passed}')}")
        print(f"  {yellow(f'SKIPPED: {skipped}')}")
        print(f"  {red(f'FAILED:  {failed}')}")
        print(f"  Total:   {total}")

        if failed > 0:
            print(bold(red("\nFailed checks:")))
            for r in self.results:
                if not r.passed and not r.skipped:
                    print(f"  • {r.name}: {r.message}")

        print(bold(cyan("=" * 60 + "\n")))

        if failed == 0:
            print(green("All checks passed. System ready.\n"))
        else:
            print(yellow(f"{failed} check(s) need attention. See above.\n"))

        # Save report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "passed": passed,
            "skipped": skipped,
            "failed": failed,
            "results": [
                {"name": r.name, "passed": r.passed, "skipped": r.skipped, "message": r.message}
                for r in self.results
            ],
        }
        report_path = Path("verification/last_report.json")
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {report_path}")

        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Electroduction system verification")
    parser.add_argument("--quick", action="store_true", help="Skip slow checks")
    args = parser.parse_args()
    runner = VerificationRunner(quick=args.quick)
    runner.run_all()
