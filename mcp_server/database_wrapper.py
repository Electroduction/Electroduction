"""
Database Wrapper for Multi-Domain Knowledge System
Provides unified interface to all domain databases with weighted routing and algorithm integration
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np


class ConfidenceLevel(Enum):
    """Query matching confidence levels"""
    VERY_HIGH = "very_high"  # >0.9
    HIGH = "high"            # 0.7-0.9
    MEDIUM = "medium"        # 0.5-0.7
    LOW = "low"              # 0.3-0.5
    VERY_LOW = "very_low"    # <0.3


@dataclass
class DatabaseMatch:
    """Represents a database match for a query"""
    domain: str
    database_file: str
    confidence: float
    weight: float
    weighted_score: float
    matched_keywords: List[str]
    relevant_sections: List[str]
    algorithm_recommendations: List[str]


@dataclass
class QueryResult:
    """Result from database query with provenance"""
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    domains_consulted: List[str]
    verification_status: str
    recommended_algorithms: List[str]
    requires_human_review: bool


class DatabaseWrapper:
    """
    Unified wrapper for all domain-specific databases
    Handles routing, weighting, and algorithm selection
    """

    def __init__(self, data_dir: str = "data", config_dir: str = "config"):
        self.data_dir = Path(data_dir)
        self.config_dir = Path(config_dir)

        # Load configuration
        self.weights_config = self._load_weights_config()
        self.domain_databases = self._discover_databases()
        self.keyword_index = self._build_keyword_index()

    def _load_weights_config(self) -> Dict:
        """Load database weights configuration"""
        weights_file = self.config_dir / "database_weights.json"
        with open(weights_file, 'r') as f:
            return json.load(f)

    def _discover_databases(self) -> Dict[str, List[Path]]:
        """Discover all JSON databases in data directory"""
        databases = {}
        for domain_dir in self.data_dir.iterdir():
            if domain_dir.is_dir():
                domain_name = domain_dir.name
                json_files = list(domain_dir.glob("*.json"))
                if json_files:
                    databases[domain_name] = json_files
        return databases

    def _build_keyword_index(self) -> Dict[str, List[Tuple[str, str]]]:
        """Build inverted index: keyword -> [(domain, file), ...]"""
        index = {}

        for domain, files in self.domain_databases.items():
            for file_path in files:
                with open(file_path, 'r') as f:
                    content = json.load(f)

                # Extract keywords from keys and values
                keywords = self._extract_keywords(content)

                for keyword in keywords:
                    if keyword not in index:
                        index[keyword] = []
                    index[keyword].append((domain, file_path.name))

        return index

    def _extract_keywords(self, data: Any, keywords: set = None) -> set:
        """Recursively extract keywords from JSON data"""
        if keywords is None:
            keywords = set()

        if isinstance(data, dict):
            for key, value in data.items():
                # Add keys as keywords (split on underscore, camelCase)
                key_words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', key.replace('_', ' '))
                keywords.update(word.lower() for word in key_words if len(word) > 2)

                self._extract_keywords(value, keywords)
        elif isinstance(data, list):
            for item in data:
                self._extract_keywords(item, keywords)
        elif isinstance(data, str):
            # Extract significant words from string values
            words = re.findall(r'\b[a-z]{3,}\b', data.lower())
            keywords.update(words)

        return keywords

    def route_query(self, query: str, top_k: int = 3) -> List[DatabaseMatch]:
        """
        Route query to most relevant databases based on keywords and weights

        Args:
            query: User query string
            top_k: Number of top matches to return

        Returns:
            List of DatabaseMatch objects ranked by weighted_score
        """
        # Extract query keywords
        query_keywords = set(re.findall(r'\b[a-z]{3,}\b', query.lower()))

        # Calculate match scores for each database
        matches = []

        for domain, files in self.domain_databases.items():
            domain_weight = self.weights_config['domain_weights'].get(domain, {}).get('weight', 0.5)

            for file_path in files:
                file_name = file_path.name

                # Count keyword matches
                matched_keywords = []
                for keyword in query_keywords:
                    if keyword in self.keyword_index and (domain, file_name) in self.keyword_index[keyword]:
                        matched_keywords.append(keyword)

                if not matched_keywords:
                    continue

                # Calculate base confidence
                confidence = len(matched_keywords) / max(len(query_keywords), 1)

                # Apply safety-critical boost
                if any(kw in query.lower() for kw in self.weights_config['weight_adjustments']['safety_critical_boost']['keywords']):
                    confidence *= self.weights_config['weight_adjustments']['safety_critical_boost']['multiplier']

                # Apply compliance boost
                if any(kw in query.lower() for kw in self.weights_config['weight_adjustments']['compliance_boost']['keywords']):
                    confidence *= self.weights_config['weight_adjustments']['compliance_boost']['multiplier']

                # Cap confidence at 1.0
                confidence = min(confidence, 1.0)

                # Get database-specific weight
                db_config = self.weights_config['domain_weights'][domain]['databases'].get(
                    file_path.stem, {'weight': domain_weight}
                )
                db_weight = db_config.get('weight', domain_weight)

                # Calculate weighted score
                weighted_score = confidence * db_weight * domain_weight

                # Get algorithm recommendations
                algorithms = db_config.get('algorithms', [])

                matches.append(DatabaseMatch(
                    domain=domain,
                    database_file=file_name,
                    confidence=confidence,
                    weight=db_weight * domain_weight,
                    weighted_score=weighted_score,
                    matched_keywords=matched_keywords,
                    relevant_sections=[],
                    algorithm_recommendations=algorithms
                ))

        # Sort by weighted_score and return top_k
        matches.sort(key=lambda x: x.weighted_score, reverse=True)
        return matches[:top_k]

    def query(self, query: str, require_verification: bool = False) -> QueryResult:
        """
        Execute query across databases with weighted routing

        Args:
            query: User query string
            require_verification: If True, only return verified answers with source citations

        Returns:
            QueryResult with answer, sources, and metadata
        """
        # Route to top databases
        matches = self.route_query(query, top_k=3)

        if not matches:
            return QueryResult(
                answer="No relevant database found. Falling back to general LLM knowledge.",
                sources=[],
                confidence=0.0,
                domains_consulted=[],
                verification_status="no_database_match",
                recommended_algorithms=[],
                requires_human_review=True
            )

        # Determine if verification is required based on confidence
        top_match = matches[0]
        verification_threshold = self.weights_config['query_routing_thresholds']['verification_required']
        needs_verification = require_verification or top_match.weighted_score >= verification_threshold

        # Load relevant data from top matches
        sources = []
        domains_consulted = []
        all_algorithms = set()

        for match in matches:
            file_path = self.data_dir / match.domain / match.database_file
            with open(file_path, 'r') as f:
                data = json.load(f)

            sources.append({
                "domain": match.domain,
                "file": match.database_file,
                "confidence": match.confidence,
                "weight": match.weight,
                "weighted_score": match.weighted_score,
                "data": data
            })

            domains_consulted.append(match.domain)
            all_algorithms.update(match.algorithm_recommendations)

        # Synthesize answer from sources (simplified - in production would use LLM with CPO)
        answer = self._synthesize_answer(query, sources, needs_verification)

        # Determine if human review needed
        requires_review = (
            top_match.weighted_score < self.weights_config['query_routing_thresholds']['single_domain_confidence']
            or len(set(domains_consulted)) > 2  # Multiple domains = complex query
            or needs_verification
        )

        return QueryResult(
            answer=answer,
            sources=sources,
            confidence=top_match.weighted_score,
            domains_consulted=list(set(domains_consulted)),
            verification_status="verified" if needs_verification else "unverified",
            recommended_algorithms=list(all_algorithms),
            requires_human_review=requires_review
        )

    def _synthesize_answer(self, query: str, sources: List[Dict], require_citations: bool) -> str:
        """
        Synthesize answer from multiple sources
        In production: use LLM with CPO (database always wins over LLM knowledge)
        """
        # Simplified implementation - just returns guidance
        answer_parts = []

        for source in sources:
            domain = source['domain']
            file = source['file']
            answer_parts.append(f"[Source: {domain}/{file} | Confidence: {source['confidence']:.2f}]")

        if require_citations:
            answer_parts.append("Note: Citations required for this query due to high criticality/confidence.")

        answer_parts.append(f"\\nQuery: {query}")
        answer_parts.append(f"Relevant domains: {', '.join(s['domain'] for s in sources)}")
        answer_parts.append("\\n[Answer synthesis would happen here using LLM with database priority via CPO]")

        return "\\n".join(answer_parts)

    def get_domain_weight(self, domain: str) -> float:
        """Get weight for a specific domain"""
        return self.weights_config['domain_weights'].get(domain, {}).get('weight', 0.5)

    def adjust_weights(self, domain: str, new_weight: float):
        """Dynamically adjust domain weight (for runtime tuning)"""
        if domain in self.weights_config['domain_weights']:
            self.weights_config['domain_weights'][domain]['weight'] = min(max(new_weight, 0.0), 1.0)

    def get_algorithm_for_domain(self, domain: str, database: str) -> List[str]:
        """Get recommended algorithms for a domain/database"""
        domain_config = self.weights_config['domain_weights'].get(domain, {})
        db_config = domain_config.get('databases', {}).get(database, {})
        return db_config.get('algorithms', [])


# Example usage
if __name__ == "__main__":
    wrapper = DatabaseWrapper()

    # Example queries
    test_queries = [
        "How do I treat a patient with sepsis?",
        "What's the correct wire size for a 20A circuit?",
        "How to debug a Kubernetes pod stuck in CrashLoopBackOff?",
        "What are the best objection handling techniques in sales?",
        "How to calculate NOI for a rental property?"
    ]

    for query in test_queries:
        print(f"\\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        result = wrapper.query(query)

        print(f"Confidence: {result.confidence:.2f}")
        print(f"Domains: {', '.join(result.domains_consulted)}")
        print(f"Algorithms: {', '.join(result.recommended_algorithms)}")
        print(f"Verification: {result.verification_status}")
        print(f"Requires Review: {result.requires_human_review}")
        print(f"\\nAnswer Preview:\\n{result.answer[:500]}...")
