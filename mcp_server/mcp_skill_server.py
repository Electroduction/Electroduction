"""
MCP Skill Server — Expert Database Connector
DRAFT ALPHA — REQUIRES TESTING AND ITERATION

Bridges all 6 domain databases to a local Claude/LLM agent via MCP.
Each domain is a Tool the AI can call. The database answer ALWAYS wins
over generic LLM knowledge (CPO principle).

Env vars required:
    DB_ROOT_PATH  — path to /data directory (default: ./data)
    LOG_LEVEL     — DEBUG | INFO | WARNING (default: INFO)

Run:
    pip install mcp
    python mcp_server/mcp_skill_server.py

SELF-CORRECTION BLOCK:
    What Could Break:
      1. mcp library not installed — pip install mcp
      2. DB path wrong — set DB_ROOT_PATH env var
      3. JSON parse error in DB files — validate JSON before serving
    How to Test:
      pytest tests/test_mcp_server.py -v
    How to Fix:
      Check DB file paths, ensure JSON is valid, check mcp version
"""

import asyncio
import json
import os
import logging
from pathlib import Path
from typing import Any

try:
    from mcp.server.models import InitializationOptions
    from mcp.server import NotificationOptions, Server
    from mcp.server.stdio import stdio_server
    import mcp.types as types
    HAS_MCP = True
except ImportError:
    HAS_MCP = False
    print("MCP not installed. Run: pip install mcp")

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
log = logging.getLogger("mcp-skill-server")

DB_ROOT = Path(os.getenv("DB_ROOT_PATH", "./data"))
DOMAINS = ["cybersecurity", "finance", "game_dev", "music", "video", "creativity"]


class DatabaseConnector:
    """Connects to domain databases and retrieves expert data."""

    def __init__(self, db_root: Path):
        self.db_root = db_root
        self._cache: dict[str, list[dict]] = {}

    def load_domain(self, domain: str) -> list[dict]:
        """Load all JSON files for a domain into memory."""
        if domain in self._cache:
            return self._cache[domain]

        domain_path = self.db_root / domain
        records = []

        if not domain_path.exists():
            log.warning(f"Domain path not found: {domain_path}")
            return []

        for json_file in domain_path.rglob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        records.extend(data)
                    elif isinstance(data, dict):
                        records.append({"source_file": str(json_file), **data})
            except json.JSONDecodeError as e:
                log.error(f"Bad JSON in {json_file}: {e}")

        self._cache[domain] = records
        log.info(f"Loaded {len(records)} records from {domain}")
        return records

    def query(self, domain: str, query: str, top_k: int = 3) -> list[dict]:
        """Simple keyword search across domain records. Upgrade to vector search later."""
        records = self.load_domain(domain)
        query_lower = query.lower()
        scored = []

        for record in records:
            record_str = json.dumps(record).lower()
            # Count keyword matches as basic relevance score
            score = sum(1 for word in query_lower.split() if word in record_str)
            if score > 0:
                scored.append((score, record))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored[:top_k]]

    def get_stats(self) -> dict:
        """Return database statistics."""
        stats = {}
        for domain in DOMAINS:
            records = self.load_domain(domain)
            stats[domain] = {"records": len(records), "loaded": domain in self._cache}
        return stats


class CPOResolver:
    """
    Contrastive Preference Optimization resolver.
    When DB has an answer, it ALWAYS wins over generic LLM output.
    Logs all conflicts for review.
    """

    def __init__(self):
        self.conflicts_log: list[dict] = []

    def resolve(self, query: str, db_results: list[dict], generic_answer: str = "") -> dict:
        """Resolve between DB answer and generic LLM answer."""
        if not db_results:
            return {
                "source": "generic_llm",
                "confidence": 0.3,
                "answer": generic_answer or "No data found in database.",
                "warning": "No DB match — answer may be inaccurate.",
            }

        db_answer = json.dumps(db_results, indent=2)

        # Log conflict if both sources have answers
        if generic_answer and generic_answer != db_answer:
            conflict = {"query": query, "db_answer": db_answer[:200], "generic": generic_answer[:200]}
            self.conflicts_log.append(conflict)
            log.info(f"CPO Conflict logged: {conflict['query'][:50]}")

        return {
            "source": "expert_database",
            "confidence": min(0.6 + len(db_results) * 0.1, 0.99),
            "answer": db_answer,
            "results_count": len(db_results),
            "cpo_applied": True,
        }


class VerifierAgent:
    """Checks AI output for safety and correctness before returning to user."""

    BLOCKED_COMMANDS = ["rm -rf", "DROP TABLE", "format c:", "del /f /s /q"]

    def verify(self, output: str, domain: str) -> dict:
        """Run safety and logic checks on generated output."""
        issues = []

        # Safety check: block destructive commands
        for cmd in self.BLOCKED_COMMANDS:
            if cmd.lower() in output.lower():
                issues.append(f"BLOCKED: Dangerous command detected: {cmd}")

        # Domain-specific checks
        if domain == "cybersecurity":
            if "sudo" in output and "sandbox" not in output.lower():
                issues.append("WARNING: sudo command outside sandbox context")

        if domain == "finance":
            if "guaranteed" in output.lower() or "100% return" in output.lower():
                issues.append("WARNING: Absolute financial claim detected")

        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "safe_to_show": len([i for i in issues if i.startswith("BLOCKED")]) == 0,
        }


# ─── MCP Server Setup ───────────────────────────────────────────────────────

db = DatabaseConnector(DB_ROOT)
cpo = CPOResolver()
verifier = VerifierAgent()

if HAS_MCP:
    server = Server("expert-skill-connector")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="query_expert_db",
                description=(
                    "Query the expert long-tail database for a specific domain. "
                    "Always use this before giving a domain-specific answer. "
                    "The database answer overrides generic LLM knowledge."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "enum": DOMAINS,
                            "description": "The knowledge domain to search",
                        },
                        "query": {
                            "type": "string",
                            "description": "Natural language query to search the database",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of results to return (default: 3)",
                            "default": 3,
                        },
                    },
                    "required": ["domain", "query"],
                },
            ),
            types.Tool(
                name="get_db_stats",
                description="Get statistics about all loaded databases.",
                inputSchema={"type": "object", "properties": {}},
            ),
            types.Tool(
                name="verify_output",
                description="Run safety and logic checks on a generated output.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "output": {"type": "string"},
                        "domain": {"type": "string", "enum": DOMAINS},
                    },
                    "required": ["output", "domain"],
                },
            ),
        ]

    @server.call_tool()
    async def handle_call_tool(
        name: str, arguments: dict | None
    ) -> list[types.TextContent]:
        args = arguments or {}

        if name == "query_expert_db":
            domain = args.get("domain", "cybersecurity")
            query = args.get("query", "")
            top_k = args.get("top_k", 3)

            results = db.query(domain, query, top_k)
            resolved = cpo.resolve(query, results)

            return [types.TextContent(type="text", text=json.dumps(resolved, indent=2))]

        if name == "get_db_stats":
            stats = db.get_stats()
            return [types.TextContent(type="text", text=json.dumps(stats, indent=2))]

        if name == "verify_output":
            result = verifier.verify(args.get("output", ""), args.get("domain", ""))
            return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

        raise ValueError(f"Unknown tool: {name}")

    async def main():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="expert-skill-connector",
                    server_version="0.2.0",
                    capabilities=server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={},
                    ),
                ),
            )

    if __name__ == "__main__":
        asyncio.run(main())

else:
    # Fallback: run as standalone tool without MCP
    if __name__ == "__main__":
        print("Running in standalone mode (MCP not installed)")
        print("DB Stats:", json.dumps(db.get_stats(), indent=2))
        print("\nTest query — cybersecurity:")
        results = db.query("cybersecurity", "attack detection", top_k=2)
        resolved = cpo.resolve("attack detection", results)
        print(json.dumps(resolved, indent=2))
