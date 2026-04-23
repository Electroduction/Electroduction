# Domain Databases - Quick Reference

## Complete Database Inventory

### Healthcare (2 files)
- `emergency_protocols.json`: ACLS, sepsis hour-1 bundle, stroke tPA, high-alert meds, NEWS2
- `pharmacology.json`: Beta-blockers, ACE inhibitors, anticoagulants, antibiotics, drug calculations

### Electrical (2 files)
- `nec_code_essentials.json`: Wire ampacity, box fill, grounding, circuit design, conduit, violations
- `troubleshooting_diagnostics.json`: Multimeter use, failure modes, power quality, load testing, 3-phase

### Plumbing/HVAC (2 files)
- `plumbing_codes_sizing.json`: Pipe sizing, DWV, venting, trap requirements, water heater codes
- `hvac_systems_diagnostics.json`: Refrigeration cycle, diagnostics, airflow, heat pumps, psychrometrics

### Welding (1 file)
- `welding_processes_parameters.json`: SMAW/MIG/TIG/FCAW, joint prep, parameters, defects, inspection

### Automotive (1 file)
- `diagnostics_repair.json`: OBD-II codes, fuel trims, sensor testing, ignition, fuel systems, brakes

### Data Science (1 file)
- `ml_techniques_validation.json`: Feature engineering, model selection, validation, hyperparameter tuning, production

### DevOps (1 file)
- `kubernetes_troubleshooting.json`: Pod debugging, networking, resources, storage, observability, security

### Sales (1 file)
- `frameworks_objections.json`: SPIN/MEDDIC/BANT, objection handling, negotiation, closing, metrics

### Marketing (1 file)
- `seo_ppc_conversion.json`: Technical SEO, on-page, link building, Google Ads, CRO, analytics

### Accounting (1 file)
- `bookkeeping_gaap.json`: Journal entries, bank reconciliation, financial statements, inventory, ratios, tax

### Legal (1 file)
- `contract_litigation_procedures.json`: Contract drafting, pleadings, discovery, trial, research

### Real Estate (1 file)
- `investing_valuation.json`: Valuation methods, investment analysis, financing, property management, tax

### Culinary (1 file)
- `techniques_flavor_theory.json`: Cooking methods, knife skills, flavor theory, mother sauces, food safety, baking

### Carpentry (1 file)
- `framing_codes.json`: Lumber dimensions, wall/floor/roof framing, connections, code requirements, layout

### Project Management (1 file)
- `agile_pmp_risk.json`: Scrum/Kanban/SAFe, user stories, estimation, risk, stakeholders, PMBOK, EVM, CPM

### Cybersecurity (4 files - existing)
- `attack_techniques.json`, `cve_critical_catalog.json`, `falco_rules_extended.json`, `incident_response_playbooks.json`

### Finance (5 files - existing)
- `fundamental_metrics.json`, `valuation_rules.json`, `risk_metrics.json`, `macroeconomic_indicators.json`, `trading_strategies.json`

### Game Dev (2 files - existing)
- `genre_mechanics.json`, `game_design_principles.json`

### Music (3 files - existing)
- `chord_dictionary.json`, `production_techniques.json`, `song_structures.json`

### Video (2 files - existing)
- `platform_specs.json`, `hook_and_script_formulas.json`

### Creativity (2 files - existing)
- `innovation_frameworks.json`, `story_archetypes_extended.json`

---

**Total**: 27 database files across 15 domains

## Data Structure Patterns

All databases follow consistent structure:

```json
{
  "_source": "Authority sources",
  "_note": "Long-tail specific data",
  "category": {
    "subcategory": {
      "field": "value",
      "examples": {},
      "common_mistakes": [],
      "best_practices": []
    }
  }
}
```

## Key Differentiators

**Long-tail Knowledge**: Specific details not in general LLM training
- NEC Table 310.15(B)(16) wire ampacity values
- Specific drug dosages (epinephrine 1mg IV/IO q3-5min)
- Exact welding parameters (SMAW 7018: 90-120A for 1/8")
- Real estate formulas (NOI / Cap Rate = Value)

**Actionable Procedures**: Step-by-step how-to
- Bank reconciliation process
- Sprint planning ceremony structure
- Sepsis hour-1 bundle checklist
- PCG logic table rules

**Safety-Critical Data**: Zero-tolerance accuracy
- Drug dosages and contraindications
- Electrical ampacity and breaker sizing
- Food safety temperatures (165°F poultry)
- Structural load calculations

**Industry Standards**: Code/regulation compliance
- NEC electrical code
- IPC plumbing code
- IRC carpentry code
- GAAP accounting standards
- FRCP legal procedures

## Using the Databases

### Direct File Access
```python
import json
with open('data/healthcare/pharmacology.json') as f:
    data = json.load(f)
print(data['drug_classes']['ace_inhibitors']['black_box_warning'])
```

### Via Database Wrapper
```python
from mcp_server.database_wrapper import DatabaseWrapper
wrapper = DatabaseWrapper()
result = wrapper.query("What's the black box warning for ACE inhibitors?")
```

### Checking Coverage
```bash
# Count total data points
find data -name "*.json" -exec cat {} \; | grep -o '"[^"]*":' | wc -l

# List all domains
ls -1 data/

# Check specific domain
ls -lh data/healthcare/
```

## Data Sources

Each database cites authoritative sources:
- **Healthcare**: Davis's Drug Guide, AHA CPR Guidelines, Emergency Nursing Procedures
- **Electrical**: NEC 2023, Mike Holt's Guides, NECA standards
- **Legal**: FRCP, PMBOK, Contract law casebooks
- **Accounting**: GAAP, CPA exam materials, IRS publications
- **And more...**

See `_source` field in each JSON file for complete attribution.
