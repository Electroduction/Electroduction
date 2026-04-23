"""
Self-Correction Engine
Validates AI responses against database sources and injects corrections
Implements CPO-style "database always wins" priority
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation failures"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CorrectionStrategy(Enum):
    """How to apply corrections"""
    INLINE = "inline"
    FOOTNOTE = "footnote"
    REWRITE = "rewrite"
    WARNING = "warning"


@dataclass
class ValidationResult:
    """Result of validating an AI response"""
    passed: bool
    severity: ValidationSeverity
    issue_type: str
    description: str
    expected_value: Any
    actual_value: Any
    source: str
    confidence: float


@dataclass
class Correction:
    """A correction to be applied to AI response"""
    strategy: CorrectionStrategy
    location: int  # Character position in response
    original_text: str
    corrected_text: str
    reason: str
    source: str
    severity: ValidationSeverity


class SelfCorrectionEngine:
    """
    Validates AI responses and injects corrections based on database sources
    """

    def __init__(self, config_path: str = "config/self_correction_config.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.validation_log = []
        self.correction_log = []

    def _load_config(self) -> Dict:
        """Load self-correction configuration"""
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def is_enabled(self) -> bool:
        """Check if validation system is enabled"""
        return self.config['system_status']['enabled']

    def get_mode(self) -> str:
        """Get current validation mode"""
        mode_config = self.config['validation_modes']
        for mode, settings in mode_config.items():
            if settings.get('enabled', False):
                return mode
        return 'off'

    def validate_response(
        self,
        ai_response: str,
        query: str,
        database_sources: List[Dict],
        domain: str
    ) -> Tuple[bool, List[ValidationResult]]:
        """
        Validate AI response against database sources

        Args:
            ai_response: The AI-generated answer
            query: Original user query
            database_sources: List of database sources consulted
            domain: Primary domain for the query

        Returns:
            Tuple of (validation_passed, list of validation results)
        """
        if not self.is_enabled():
            return True, []

        mode = self.get_mode()
        validations = []

        # Get domain-specific rules
        domain_rules = self.config['domain_specific_rules'].get(domain, {})
        mode_config = self.config['validation_modes'][mode]

        # Run validation checks
        validations.extend(self._check_source_citations(ai_response, database_sources, domain_rules))
        validations.extend(self._check_numerical_accuracy(ai_response, database_sources, domain_rules))
        validations.extend(self._check_contradictions(ai_response, database_sources))
        validations.extend(self._check_completeness(ai_response, query))

        # Log validations
        self.validation_log.extend(validations)

        # Determine if validation passed
        critical_failures = [v for v in validations if not v.passed and v.severity == ValidationSeverity.CRITICAL]
        high_failures = [v for v in validations if not v.passed and v.severity == ValidationSeverity.HIGH]

        validation_passed = len(critical_failures) == 0

        # Check if we should block based on mode
        if mode == 'strict' and (critical_failures or high_failures):
            validation_passed = False

        return validation_passed, validations

    def _check_source_citations(
        self,
        response: str,
        sources: List[Dict],
        domain_rules: Dict
    ) -> List[ValidationResult]:
        """Verify response contains proper source citations"""
        validations = []

        if not domain_rules.get('require_source_citation', False):
            return validations

        # Look for citation pattern: [Source: domain/file | Rule: rule_name]
        citation_pattern = r'\[Source:\s*([^\|]+)\s*\|\s*Rule:\s*([^\]]+)\]'
        citations = re.findall(citation_pattern, response)

        if not citations and domain_rules.get('require_source_citation'):
            validations.append(ValidationResult(
                passed=False,
                severity=ValidationSeverity.HIGH,
                issue_type="missing_citation",
                description="Response lacks required source citations",
                expected_value="Citations in format [Source: domain/file | Rule: name]",
                actual_value=f"Found {len(citations)} citations",
                source="citation_check",
                confidence=1.0
            ))

        return validations

    def _check_numerical_accuracy(
        self,
        response: str,
        sources: List[Dict],
        domain_rules: Dict
    ) -> List[ValidationResult]:
        """Verify numerical values match database exactly"""
        validations = []

        tolerance = domain_rules.get('numerical_tolerance', 0.0)
        critical_fields = domain_rules.get('critical_fields', [])

        # Extract numbers from response
        numbers_in_response = re.findall(r'\b\d+(?:\.\d+)?\b', response)

        # Compare with numbers in database (simplified - would need deeper extraction)
        for source in sources:
            data = source.get('data', {})
            # In production, would recursively search for numbers and compare
            # This is a simplified check

        return validations

    def _check_contradictions(
        self,
        response: str,
        sources: List[Dict]
    ) -> List[ValidationResult]:
        """Detect contradictions between response and database"""
        validations = []

        # Simplified semantic check
        # In production: use embedding similarity or LLM-based verification

        for source in sources:
            # Check if response contradicts database content
            # This would use semantic similarity in production
            pass

        return validations

    def _check_completeness(
        self,
        response: str,
        query: str
    ) -> List[ValidationResult]:
        """Check if response addresses all parts of query"""
        validations = []

        # Extract question keywords
        query_keywords = set(re.findall(r'\b[a-z]{4,}\b', query.lower()))
        response_keywords = set(re.findall(r'\b[a-z]{4,}\b', response.lower()))

        # Check coverage
        coverage = len(query_keywords & response_keywords) / max(len(query_keywords), 1)

        if coverage < 0.6:
            validations.append(ValidationResult(
                passed=False,
                severity=ValidationSeverity.MEDIUM,
                issue_type="incomplete_response",
                description="Response may not fully address query",
                expected_value=f"Coverage >60%",
                actual_value=f"Coverage {coverage*100:.0f}%",
                source="completeness_check",
                confidence=0.7
            ))

        return validations

    def generate_corrections(
        self,
        ai_response: str,
        validations: List[ValidationResult],
        database_sources: List[Dict]
    ) -> List[Correction]:
        """
        Generate corrections based on validation failures

        Args:
            ai_response: Original AI response
            validations: List of validation results
            database_sources: Database sources with correct information

        Returns:
            List of corrections to apply
        """
        if not self.config['correction_injection']['enabled']:
            return []

        corrections = []

        for validation in validations:
            if validation.passed:
                continue

            # Determine correction strategy
            strategy = self._select_correction_strategy(validation)

            # Generate correction
            correction = self._create_correction(
                ai_response,
                validation,
                strategy,
                database_sources
            )

            if correction:
                corrections.append(correction)

        return corrections

    def _select_correction_strategy(self, validation: ValidationResult) -> CorrectionStrategy:
        """Select appropriate correction strategy based on severity and type"""
        strategies = self.config['correction_injection']['strategies']

        if validation.severity == ValidationSeverity.CRITICAL:
            if strategies['warning_banner']['enabled']:
                return CorrectionStrategy.WARNING
            elif strategies['rewrite']['enabled']:
                return CorrectionStrategy.REWRITE

        if strategies['inline_correction']['enabled']:
            return CorrectionStrategy.INLINE

        if strategies['footnote_correction']['enabled']:
            return CorrectionStrategy.FOOTNOTE

        return CorrectionStrategy.INLINE

    def _create_correction(
        self,
        response: str,
        validation: ValidationResult,
        strategy: CorrectionStrategy,
        sources: List[Dict]
    ) -> Optional[Correction]:
        """Create a specific correction"""
        if validation.issue_type == "missing_citation":
            # Add source citations
            return Correction(
                strategy=CorrectionStrategy.FOOTNOTE,
                location=len(response),
                original_text="",
                corrected_text=f"\\n\\n[Sources: {', '.join(s['domain'] + '/' + s['file'] for s in sources)}]",
                reason="Added missing source citations",
                source=validation.source,
                severity=validation.severity
            )

        elif validation.issue_type == "numerical_mismatch":
            # Correct numerical value
            return Correction(
                strategy=CorrectionStrategy.INLINE,
                location=response.find(str(validation.actual_value)),
                original_text=str(validation.actual_value),
                corrected_text=f"{validation.expected_value} [CORRECTED from {validation.actual_value}]",
                reason=f"Database shows {validation.expected_value}",
                source=validation.source,
                severity=validation.severity
            )

        return None

    def apply_corrections(
        self,
        response: str,
        corrections: List[Correction]
    ) -> Tuple[str, List[str]]:
        """
        Apply corrections to AI response

        Args:
            response: Original AI response
            corrections: List of corrections to apply

        Returns:
            Tuple of (corrected_response, list of correction messages)
        """
        if not corrections:
            return response, []

        corrected = response
        messages = []

        # Sort corrections by location (reverse order to maintain positions)
        corrections.sort(key=lambda c: c.location, reverse=True)

        for correction in corrections:
            if correction.strategy == CorrectionStrategy.INLINE:
                corrected = (
                    corrected[:correction.location] +
                    correction.corrected_text +
                    corrected[correction.location + len(correction.original_text):]
                )
                messages.append(f"✓ Corrected: {correction.reason}")

            elif correction.strategy == CorrectionStrategy.FOOTNOTE:
                corrected += correction.corrected_text
                messages.append(f"ℹ Added: {correction.reason}")

            elif correction.strategy == CorrectionStrategy.WARNING:
                warning = f"\\n⚠️ WARNING: {correction.reason}\\n"
                corrected = warning + corrected
                messages.append(f"⚠ Warning added: {correction.reason}")

            # Log correction
            self.correction_log.append({
                "timestamp": datetime.now().isoformat(),
                "strategy": correction.strategy.value,
                "reason": correction.reason,
                "source": correction.source,
                "severity": correction.severity.value
            })

        return corrected, messages

    def process_response(
        self,
        ai_response: str,
        query: str,
        database_sources: List[Dict],
        domain: str
    ) -> Dict[str, Any]:
        """
        Complete validation and correction pipeline

        Args:
            ai_response: AI-generated response
            query: User query
            database_sources: Database sources used
            domain: Primary domain

        Returns:
            Dict with corrected response and metadata
        """
        mode = self.get_mode()

        if mode == 'off':
            return {
                "response": ai_response,
                "validated": False,
                "corrections_applied": [],
                "validation_passed": True
            }

        # Validate
        validation_passed, validations = self.validate_response(
            ai_response, query, database_sources, domain
        )

        # Generate corrections
        corrections = self.generate_corrections(
            ai_response, validations, database_sources
        )

        # Apply corrections if enabled
        mode_config = self.config['validation_modes'][mode]
        if mode_config.get('auto_correct', False):
            corrected_response, correction_messages = self.apply_corrections(
                ai_response, corrections
            )
        else:
            corrected_response = ai_response
            correction_messages = []

        # Log if needed
        if mode_config.get('log_failures', False):
            self._log_validation(validations, corrections)

        return {
            "response": corrected_response,
            "validated": True,
            "validation_passed": validation_passed,
            "validations": [{"type": v.issue_type, "severity": v.severity.value, "passed": v.passed} for v in validations],
            "corrections_applied": correction_messages,
            "mode": mode
        }

    def _log_validation(self, validations: List[ValidationResult], corrections: List[Correction]):
        """Log validation results and corrections"""
        log_file = Path(self.config['data_quality_monitoring']['logging']['failed_validations_file'])
        log_file.parent.mkdir(parents=True, exist_ok=True)

        failed_validations = [
            {
                "timestamp": datetime.now().isoformat(),
                "issue_type": v.issue_type,
                "severity": v.severity.value,
                "description": v.description,
                "source": v.source
            }
            for v in validations if not v.passed
        ]

        if failed_validations:
            with open(log_file, 'a') as f:
                for failure in failed_validations:
                    f.write(json.dumps(failure) + '\\n')

    def toggle_mode(self, new_mode: str):
        """Toggle validation mode"""
        if new_mode not in self.config['validation_modes']:
            raise ValueError(f"Invalid mode: {new_mode}")

        # Disable all modes
        for mode in self.config['validation_modes']:
            self.config['validation_modes'][mode]['enabled'] = False

        # Enable new mode
        self.config['validation_modes'][new_mode]['enabled'] = True

        # Save config
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=2)


# Example usage
if __name__ == "__main__":
    engine = SelfCorrectionEngine()

    # Example AI response with issues
    ai_response = """
    For a 20A circuit, you should use 12 AWG wire. The ampacity is approximately 25A.
    This is a common residential circuit size.
    """

    query = "What wire size for 20A circuit and what's the ampacity?"

    database_sources = [{
        "domain": "electrical",
        "file": "nec_code_essentials.json",
        "data": {
            "wire_sizing_and_ampacity": {
                "copper_wire_ratings_75C": {
                    "12_awg": {"ampacity": "25A", "common_breaker": "20A"}
                }
            }
        }
    }]

    result = engine.process_response(
        ai_response,
        query,
        database_sources,
        "electrical"
    )

    print(f"Validation passed: {result['validation_passed']}")
    print(f"Corrections applied: {result['corrections_applied']}")
    print(f"\\nCorrected response:\\n{result['response']}")
