# Multi-Domain Knowledge System - Complete Documentation

## Overview

This system provides a database-driven AI assistant with 15+ specialized domains, weighted routing, and self-correcting validation. The architecture implements CPO-style training where **database answers always win over general LLM knowledge**.

## System Architecture

```
User Query
    ↓
Database Wrapper (keyword routing + weighting)
    ↓
Query Top 3 Databases (weighted scores)
    ↓
LLM Generates Answer (using database sources)
    ↓
Self-Correction Engine (validates + corrects)
    ↓
Final Answer (with citations + corrections)
```

## Components

### 1. Domain Databases (27 files across 15 domains)

#### Critical Domains (weights 0.85-0.98)
- **Healthcare** (0.95): Pharmacology, emergency protocols, ACLS, sepsis, stroke
- **Cybersecurity** (0.98): Attack techniques, CVEs, Falco rules, incident response
- **Electrical** (0.90): NEC codes, wire sizing, troubleshooting, load calculations
- **Accounting** (0.92): GAAP, bookkeeping, financial statements, tax

#### High-Priority Domains (weights 0.75-0.88)
- **Plumbing/HVAC** (0.88): Codes, pipe sizing, refrigeration, diagnostics
- **Legal** (0.88): Contract drafting, litigation procedures, legal research
- **Carpentry** (0.85): Framing, building codes, lumber grades
- **Data Science** (0.85): ML techniques, validation, feature engineering
- **DevOps** (0.83): Kubernetes, observability, security
- **Welding** (0.82): Processes, parameters, inspection
- **Finance** (0.80): Valuation, trading strategies, risk metrics
- **Automotive** (0.78): Diagnostics, OBD-II, sensors
- **Project Management** (0.77): Agile, PMP, risk management
- **Real Estate** (0.75): Investing, valuation, property management

#### Medium-Priority Domains (weights 0.55-0.72)
- **Sales** (0.72): SPIN selling, objection handling, negotiation
- **Marketing** (0.70): SEO, PPC, conversion optimization
- **Culinary** (0.68): Cooking techniques, flavor theory, food safety
- **Game Dev** (0.65): Mechanics, design principles
- **Music** (0.60): Chord theory, production, song structures
- **Video** (0.58): Platform specs, hooks, scripts
- **Creativity** (0.55): Innovation frameworks, story archetypes

### 2. Database Wrapper (`mcp_server/database_wrapper.py`)

**Purpose**: Unified interface for querying all databases with weighted routing

**Key Features**:
- Keyword-based query routing
- Weighted scoring (domain weight × database weight × confidence)
- Multi-database synthesis
- Algorithm recommendations per domain

**Usage**:
```python
from mcp_server.database_wrapper import DatabaseWrapper

wrapper = DatabaseWrapper()

# Query with automatic routing
result = wrapper.query("How do I treat sepsis?")

print(f"Confidence: {result.confidence}")
print(f"Domains: {result.domains_consulted}")
print(f"Algorithms: {result.recommended_algorithms}")
print(f"Answer: {result.answer}")
```

**Routing Logic**:
1. Extract keywords from query
2. Match keywords to databases (inverted index)
3. Calculate confidence = matched_keywords / query_keywords
4. Apply safety/compliance boosts if applicable
5. Weight score = confidence × db_weight × domain_weight
6. Return top K databases

### 3. Database Weights Config (`config/database_weights.json`)

**Purpose**: Configure domain priorities, algorithm assignments, routing thresholds

**Key Settings**:
```json
{
  "domain_weights": {
    "healthcare": {
      "weight": 0.95,
      "priority": "critical",
      "databases": {
        "pharmacology": {
          "weight": 1.0,
          "algorithms": ["weak_to_strong", "cot_verification"]
        }
      }
    }
  },
  "weight_adjustments": {
    "safety_critical_boost": {
      "keywords": ["emergency", "life-threatening", "critical"],
      "multiplier": 1.15
    }
  }
}
```

**Adjusting Weights**:
```python
# Runtime adjustment
wrapper.adjust_weights("healthcare", 0.98)

# Or edit config/database_weights.json directly
```

### 4. Self-Correction Engine (`verification/self_correction_engine.py`)

**Purpose**: Validate AI responses against databases and auto-correct errors

**Validation Modes**:
- **off**: No validation (fastest)
- **passive**: Log issues but don't block (monitoring)
- **active**: Flag issues with warnings
- **strict**: Block low-confidence responses (safety-critical)
- **full**: Complete validation + auto-correction (production)

**Usage**:
```python
from verification.self_correction_engine import SelfCorrectionEngine

engine = SelfCorrectionEngine()

# Process AI response
result = engine.process_response(
    ai_response="For 20A circuit use 14 AWG wire...",
    query="What wire for 20A circuit?",
    database_sources=sources,
    domain="electrical"
)

print(f"Validated: {result['validated']}")
print(f"Passed: {result['validation_passed']}")
print(f"Corrections: {result['corrections_applied']}")
print(f"\nCorrected Response:\n{result['response']}")
```

**Validation Checks**:
1. **Source Citation**: Ensures [Source: domain/file | Rule: name] format
2. **Numerical Accuracy**: Verifies numbers match database (0% tolerance for critical)
3. **Contradiction Detection**: Semantic similarity between answer and database
4. **Completeness**: Query keywords covered in response

**Correction Strategies**:
- **Inline**: `[CORRECTED: 12 AWG, not 14 AWG]`
- **Footnote**: Sources appended at end
- **Rewrite**: Complete answer regeneration
- **Warning**: `⚠️ WARNING: AI conflicts with database`

### 5. Self-Correction Config (`config/self_correction_config.json`)

**Purpose**: Configure validation behavior, domain-specific rules, metrics

**Toggle Validation Mode**:
```python
engine.toggle_mode("strict")  # For safety-critical queries
engine.toggle_mode("full")    # For production
engine.toggle_mode("off")     # For testing
```

**Domain-Specific Rules**:
```json
{
  "healthcare": {
    "validation_mode": "strict",
    "require_source_citation": true,
    "block_unverified": true,
    "numerical_tolerance": 0.0,
    "critical_fields": ["dosage", "temperature", "pressure"]
  }
}
```

## Algorithm Integration

Each database is assigned specific algorithms based on use case:

### Chain-of-Thought Verification (`cot_verification`)
**Domains**: Healthcare, Electrical, Legal, Accounting, Cybersecurity, Carpentry
**Purpose**: Verify each reasoning step cites database source
**Example**: 
```
Step 1: Check NEC Table 310.15(B)(16) for 12 AWG copper [Source: electrical/nec_code_essentials.json | Rule: copper_wire_ratings_75C]
Step 2: At 75°C, 12 AWG rated for 25A [Source: same]
Step 3: Use 20A breaker (80% of 25A) [Source: same]
```

### Anomaly-to-Signature Mapping (`anomaly_to_signature`)
**Domains**: Cybersecurity, Electrical (troubleshooting), HVAC, Automotive, DevOps
**Purpose**: Convert anomalies/failures to detection rules or diagnostic patterns
**Example**: Cluster similar OBD-II fault patterns → diagnostic decision tree

### Latent Space Interpolation (`latent_interpolation`)
**Domains**: Music, Game Dev, Creativity, Video
**Purpose**: Blend creative elements using SLERP/LERP
**Example**: Interpolate between two chord progressions, game mechanics, story beats

### PCG Logic Tables (`pcg_logic_tables`)
**Domains**: Game Dev, Music, Creativity
**Purpose**: Rule-based procedural generation
**Example**: IF difficulty=hard THEN enemy_density=0.6, platform_gap=4-7 tiles

### Weak-to-Strong Supervision (`weak_to_strong`)
**Domains**: All domains (training data generation)
**Purpose**: Small rule-based model labels data; large model learns reasoning
**Example**: Rule labels "PE > 30" as overvalued → LLM learns nuanced valuation

## Complete Workflow Example

```python
from mcp_server.database_wrapper import DatabaseWrapper
from verification.self_correction_engine import SelfCorrectionEngine

# Initialize
wrapper = DatabaseWrapper()
engine = SelfCorrectionEngine()

# Set strict mode for healthcare
engine.toggle_mode("strict")

# User query
query = "What's the epinephrine dose for cardiac arrest?"

# Route to databases
result = wrapper.query(query, require_verification=True)

# Simulate LLM response using database sources
llm_response = f"""
For cardiac arrest with shockable rhythm (VFib/VTach), give epinephrine 1mg IV/IO 
every 3-5 minutes after the 2nd shock.
[Source: healthcare/emergency_protocols.json | Rule: vfib_vtach]
"""

# Validate and correct
validated = engine.process_response(
    ai_response=llm_response,
    query=query,
    database_sources=result.sources,
    domain="healthcare"
)

if validated['validation_passed']:
    print("✓ Response validated and safe to use")
    print(validated['response'])
else:
    print("⚠ Validation failed - requires human review")
    print(f"Issues: {validated['validations']}")
```

## Configuration Files

### `/config/database_weights.json`
- Domain weights (0.0-1.0)
- Safety boosts
- Algorithm assignments
- Routing thresholds

### `/config/self_correction_config.json`
- Validation modes
- Correction strategies
- Domain-specific rules
- Metrics and logging

## Data Quality Monitoring

**Metrics Tracked**:
- `validation_pass_rate`: % of responses passing validation (target >95%)
- `correction_injection_rate`: % requiring corrections (target <5%)
- `database_coverage`: % of queries with database match (target >80%)
- `citation_compliance`: % with proper citations (target >95% for critical domains)

**Logs**:
- `logs/validation.log`: All validation events
- `logs/failed_validations.json`: Failed validation details
- `logs/corrections_applied.json`: Correction history

## Best Practices

### For Safety-Critical Queries
1. Use `strict` or `full` validation mode
2. Require source citations
3. Set numerical tolerance to 0.0
4. Block unverified responses

### For Creative Queries
1. Use `passive` or `active` mode
2. Allow AI flexibility
3. Use latent interpolation algorithms
4. Lower weight thresholds

### For Production Deployment
1. Use `full` validation mode
2. Monitor metrics daily
3. Review failed validations weekly
4. Adjust weights based on correction rates
5. Retrain weak-to-strong models quarterly

## Extending the System

### Adding a New Domain
1. Create `data/<domain>/<topic>.json` with structured data
2. Add domain to `config/database_weights.json`:
```json
"new_domain": {
  "weight": 0.75,
  "priority": "medium",
  "databases": {
    "topic": {"weight": 0.80, "algorithms": ["weak_to_strong"]}
  }
}
```
3. (Optional) Add domain-specific rules to `config/self_correction_config.json`
4. Restart system to rebuild keyword index

### Adding Algorithm Support
1. Implement algorithm in `algorithms/<algorithm_name>.py`
2. Assign to databases in `database_weights.json`
3. Call algorithm from wrapper or correction engine

## System Status

**Current Configuration**:
- Domains: 15 (21 counting subdivisions)
- Database Files: 27
- Validation Mode: `full`
- Total Algorithms: 5 (cot_verification, anomaly_to_signature, latent_interpolation, pcg_logic_tables, weak_to_strong)

**Performance**:
- Query routing: <50ms
- Validation: <200ms
- End-to-end: <2s (excluding LLM inference)

## Troubleshooting

### "No relevant database found"
- Query keywords don't match database content
- Check `wrapper.keyword_index` to see indexed keywords
- Add synonyms to database or adjust query

### High correction rate
- LLM knowledge outdated vs database
- Consider retraining with database as ground truth
- Increase domain weight to prioritize database earlier

### Validation blocking too many responses
- Mode too strict for domain
- Adjust to `active` instead of `strict`
- Lower confidence thresholds
- Review domain-specific rules

## API Endpoints (Future)

```
POST   /api/query              # Submit query
GET    /api/validation/status  # Check validation system status
POST   /api/validation/toggle  # Change validation mode
GET    /api/metrics            # Get data quality metrics
POST   /api/weights/adjust     # Adjust domain weights
```

## References

- Database Wrapper: `mcp_server/database_wrapper.py`
- Self-Correction Engine: `verification/self_correction_engine.py`
- Weights Config: `config/database_weights.json`
- Validation Config: `config/self_correction_config.json`
- Domain Databases: `data/*/`
- Algorithms: `algorithms/*/`
