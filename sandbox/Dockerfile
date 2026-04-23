# Electroduction AI Sandbox
# Safe isolated execution environment for testing AI outputs
# Usage: docker build -t electroduction-sandbox . && docker run --rm electroduction-sandbox
#
# NEVER run AI-generated code outside this container on live systems.
# Cybersecurity auto-resolve ALWAYS runs here first (SYSTEM RULE #3).

FROM python:3.11-slim

# Security: non-root user
RUN useradd -m -u 1000 sandbox
WORKDIR /app

# System deps (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code (not raw data — mount that via volume)
COPY algorithms/ algorithms/
COPY mcp_server/ mcp_server/
COPY verification/ verification/
COPY tests/ tests/

# Create data directories for mounted volumes
RUN mkdir -p data databases/cpo_triplets

# Drop to non-root
USER sandbox

# Default: run verification checklist
CMD ["python", "verification/run_checks.py", "--quick"]
