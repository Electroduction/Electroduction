#!/usr/bin/env python3
"""
Research & Analysis Toolkit
===========================

A comprehensive toolkit for research, data analysis, and information processing.
Provides tools for text analysis, citation management, and research organization.

Author: Electroduction Security Team
Version: 1.0.0

Features:
---------
- Text Analysis: Word frequency, readability scores, sentiment analysis
- Citation Management: BibTeX parsing, citation formatting
- Document Comparison: Similarity analysis, plagiarism detection concepts
- Research Notes: Organize and search research notes
- Data Extraction: Pattern extraction from text

Usage:
------
    from research_toolkit import ResearchToolkit, TextAnalyzer, CitationManager

    # Analyze text
    analyzer = TextAnalyzer()
    stats = analyzer.analyze("Your research text here...")

    # Manage citations
    citations = CitationManager()
    citations.add_citation(author="Smith", title="Research Paper", year=2024)
"""

import re
import json
import math
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
import string


# =============================================================================
# TEXT ANALYSIS COMPONENTS
# =============================================================================

class TextAnalyzer:
    """
    Comprehensive text analysis tool for research documents.

    Provides various metrics including:
    - Word and sentence statistics
    - Readability scores (Flesch-Kincaid, Gunning Fog, etc.)
    - Word frequency analysis
    - N-gram extraction
    - Basic sentiment indicators

    Example:
        >>> analyzer = TextAnalyzer()
        >>> result = analyzer.analyze("The quick brown fox jumps over the lazy dog.")
        >>> print(result['word_count'])
        9
    """

    # Common English stop words for filtering
    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
        'she', 'we', 'they', 'what', 'which', 'who', 'whom', 'when', 'where',
        'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there'
    }

    # Positive and negative word lists for basic sentiment
    POSITIVE_WORDS = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'outstanding', 'brilliant', 'superb', 'positive', 'success', 'successful',
        'beneficial', 'advantage', 'improve', 'improvement', 'better', 'best',
        'effective', 'efficient', 'remarkable', 'significant', 'important',
        'innovative', 'creative', 'valuable', 'useful', 'helpful', 'promising'
    }

    NEGATIVE_WORDS = {
        'bad', 'poor', 'terrible', 'awful', 'horrible', 'negative', 'failure',
        'failed', 'worse', 'worst', 'harmful', 'disadvantage', 'problem',
        'problematic', 'difficult', 'challenging', 'issue', 'concern', 'risk',
        'danger', 'dangerous', 'ineffective', 'inefficient', 'limitation',
        'limited', 'weak', 'weakness', 'flaw', 'error', 'mistake'
    }

    def __init__(self):
        """Initialize the text analyzer."""
        # Syllable counting patterns
        self.vowels = set('aeiouy')
        self.special_syllables = {
            'ia': 2, 'iu': 2, 'io': 2, 'ua': 2, 'uo': 2,
            'eous': 2, 'ious': 2, 'uous': 2
        }

    def analyze(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on the given text.

        Args:
            text: The text to analyze

        Returns:
            Dictionary containing all analysis metrics
        """
        # Basic cleaning
        clean_text = self._clean_text(text)

        # Extract components
        words = self._get_words(clean_text)
        sentences = self._get_sentences(text)
        paragraphs = self._get_paragraphs(text)

        # Calculate all metrics
        result = {
            # Basic statistics
            'character_count': len(text),
            'character_count_no_spaces': len(text.replace(' ', '')),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),

            # Averages
            'avg_word_length': self._avg_word_length(words),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'avg_paragraph_length': len(sentences) / max(len(paragraphs), 1),

            # Readability scores
            'flesch_reading_ease': self._flesch_reading_ease(words, sentences),
            'flesch_kincaid_grade': self._flesch_kincaid_grade(words, sentences),
            'gunning_fog_index': self._gunning_fog_index(words, sentences),
            'smog_index': self._smog_index(words, sentences),
            'coleman_liau_index': self._coleman_liau_index(text, words, sentences),
            'automated_readability_index': self._ari(text, words, sentences),

            # Vocabulary analysis
            'unique_words': len(set(w.lower() for w in words)),
            'vocabulary_richness': len(set(w.lower() for w in words)) / max(len(words), 1),
            'lexical_density': self._lexical_density(words),

            # Word frequency
            'word_frequency': self._word_frequency(words, top_n=20),
            'bigrams': self._get_ngrams(words, 2, top_n=10),
            'trigrams': self._get_ngrams(words, 3, top_n=10),

            # Sentiment indicators
            'sentiment': self._basic_sentiment(words),

            # Reading time estimates (words per minute)
            'reading_time_minutes': len(words) / 200,  # Average adult reading speed
            'speaking_time_minutes': len(words) / 150,  # Average speaking speed
        }

        return result

    def _clean_text(self, text: str) -> str:
        """Remove special characters and normalize whitespace."""
        # Keep letters, numbers, and basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-]', ' ', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _get_words(self, text: str) -> List[str]:
        """Extract words from text."""
        # Split on whitespace and punctuation
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words

    def _get_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Split on sentence-ending punctuation
        sentences = re.split(r'[.!?]+', text)
        # Filter empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences

    def _get_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split on multiple newlines
        paragraphs = re.split(r'\n\s*\n', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        return paragraphs if paragraphs else [text]

    def _count_syllables(self, word: str) -> int:
        """
        Count syllables in a word using heuristic rules.

        This is an approximation that works well for most English words.
        """
        word = word.lower().strip()
        if len(word) <= 3:
            return 1

        # Check for special patterns
        for pattern, count in self.special_syllables.items():
            if pattern in word:
                word = word.replace(pattern, 'a' * count)

        # Count vowel groups
        count = 0
        prev_vowel = False

        for i, char in enumerate(word):
            is_vowel = char in self.vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel

        # Adjust for silent e
        if word.endswith('e') and count > 1:
            count -= 1

        # Adjust for -le endings
        if word.endswith('le') and len(word) > 2 and word[-3] not in self.vowels:
            count += 1

        return max(count, 1)

    def _avg_word_length(self, words: List[str]) -> float:
        """Calculate average word length."""
        if not words:
            return 0.0
        return sum(len(w) for w in words) / len(words)

    def _flesch_reading_ease(self, words: List[str], sentences: List[str]) -> float:
        """
        Calculate Flesch Reading Ease score.

        Score interpretation:
        - 90-100: Very Easy (5th grade)
        - 80-89: Easy (6th grade)
        - 70-79: Fairly Easy (7th grade)
        - 60-69: Standard (8th-9th grade)
        - 50-59: Fairly Difficult (10th-12th grade)
        - 30-49: Difficult (College)
        - 0-29: Very Difficult (College Graduate)
        """
        if not words or not sentences:
            return 0.0

        total_syllables = sum(self._count_syllables(w) for w in words)
        asl = len(words) / len(sentences)  # Average Sentence Length
        asw = total_syllables / len(words)  # Average Syllables per Word

        score = 206.835 - (1.015 * asl) - (84.6 * asw)
        return round(max(0, min(100, score)), 2)

    def _flesch_kincaid_grade(self, words: List[str], sentences: List[str]) -> float:
        """
        Calculate Flesch-Kincaid Grade Level.

        Returns the U.S. school grade level needed to understand the text.
        """
        if not words or not sentences:
            return 0.0

        total_syllables = sum(self._count_syllables(w) for w in words)
        asl = len(words) / len(sentences)
        asw = total_syllables / len(words)

        grade = (0.39 * asl) + (11.8 * asw) - 15.59
        return round(max(0, grade), 2)

    def _gunning_fog_index(self, words: List[str], sentences: List[str]) -> float:
        """
        Calculate Gunning Fog Index.

        Estimates years of formal education needed to understand the text.
        """
        if not words or not sentences:
            return 0.0

        # Count complex words (3+ syllables, excluding common suffixes)
        complex_words = sum(
            1 for w in words
            if self._count_syllables(w) >= 3
            and not w.endswith(('ing', 'ed', 'es', 'ly'))
        )

        asl = len(words) / len(sentences)
        pcw = (complex_words / len(words)) * 100  # Percentage of complex words

        fog = 0.4 * (asl + pcw)
        return round(fog, 2)

    def _smog_index(self, words: List[str], sentences: List[str]) -> float:
        """
        Calculate SMOG (Simple Measure of Gobbledygook) Index.

        Estimates years of education needed to understand the text.
        Most accurate for texts with 30+ sentences.
        """
        if not words or len(sentences) < 3:
            return 0.0

        # Count polysyllabic words (3+ syllables)
        polysyllables = sum(1 for w in words if self._count_syllables(w) >= 3)

        smog = 1.0430 * math.sqrt(polysyllables * (30 / len(sentences))) + 3.1291
        return round(smog, 2)

    def _coleman_liau_index(self, text: str, words: List[str], sentences: List[str]) -> float:
        """
        Calculate Coleman-Liau Index.

        Uses character count instead of syllables.
        """
        if not words or not sentences:
            return 0.0

        # Count letters only
        letters = sum(1 for c in text if c.isalpha())

        L = (letters / len(words)) * 100  # Average letters per 100 words
        S = (len(sentences) / len(words)) * 100  # Average sentences per 100 words

        cli = 0.0588 * L - 0.296 * S - 15.8
        return round(cli, 2)

    def _ari(self, text: str, words: List[str], sentences: List[str]) -> float:
        """
        Calculate Automated Readability Index.

        Returns U.S. grade level needed to understand the text.
        """
        if not words or not sentences:
            return 0.0

        characters = sum(1 for c in text if c.isalnum())

        ari = 4.71 * (characters / len(words)) + 0.5 * (len(words) / len(sentences)) - 21.43
        return round(max(0, ari), 2)

    def _lexical_density(self, words: List[str]) -> float:
        """
        Calculate lexical density (ratio of content words to total words).

        Higher density = more information-packed text.
        """
        if not words:
            return 0.0

        # Content words = words that aren't stop words
        content_words = [w for w in words if w.lower() not in self.STOP_WORDS]

        return round(len(content_words) / len(words), 4)

    def _word_frequency(self, words: List[str], top_n: int = 20) -> List[Tuple[str, int]]:
        """Get the most frequent words (excluding stop words)."""
        # Filter stop words and count
        filtered_words = [w.lower() for w in words if w.lower() not in self.STOP_WORDS]
        counter = Counter(filtered_words)
        return counter.most_common(top_n)

    def _get_ngrams(self, words: List[str], n: int, top_n: int = 10) -> List[Tuple[str, int]]:
        """Extract n-grams from text."""
        if len(words) < n:
            return []

        # Create n-grams
        ngrams = []
        for i in range(len(words) - n + 1):
            ngram = ' '.join(words[i:i+n])
            ngrams.append(ngram)

        counter = Counter(ngrams)
        return counter.most_common(top_n)

    def _basic_sentiment(self, words: List[str]) -> Dict[str, Any]:
        """
        Perform basic sentiment analysis using word lists.

        Note: This is a simple approach. For production use,
        consider dedicated NLP libraries.
        """
        word_set = set(w.lower() for w in words)

        positive_count = len(word_set & self.POSITIVE_WORDS)
        negative_count = len(word_set & self.NEGATIVE_WORDS)
        total = positive_count + negative_count

        if total == 0:
            polarity = 0.0
        else:
            polarity = (positive_count - negative_count) / total

        # Determine sentiment label
        if polarity > 0.1:
            label = 'positive'
        elif polarity < -0.1:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'polarity': round(polarity, 4),
            'label': label,
            'positive_words': positive_count,
            'negative_words': negative_count,
            'positive_words_found': list(word_set & self.POSITIVE_WORDS),
            'negative_words_found': list(word_set & self.NEGATIVE_WORDS)
        }

    def compare_texts(self, text1: str, text2: str) -> Dict[str, Any]:
        """
        Compare two texts for similarity.

        Uses multiple similarity metrics.
        """
        words1 = set(self._get_words(text1))
        words2 = set(self._get_words(text2))

        # Jaccard similarity
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        jaccard = intersection / max(union, 1)

        # Overlap coefficient
        overlap = intersection / min(len(words1), len(words2)) if min(len(words1), len(words2)) > 0 else 0

        # Dice coefficient
        dice = (2 * intersection) / (len(words1) + len(words2)) if (len(words1) + len(words2)) > 0 else 0

        # Cosine similarity using word frequency vectors
        freq1 = Counter(self._get_words(text1))
        freq2 = Counter(self._get_words(text2))

        all_words = set(freq1.keys()) | set(freq2.keys())

        dot_product = sum(freq1.get(w, 0) * freq2.get(w, 0) for w in all_words)
        magnitude1 = math.sqrt(sum(v**2 for v in freq1.values()))
        magnitude2 = math.sqrt(sum(v**2 for v in freq2.values()))

        cosine = dot_product / (magnitude1 * magnitude2) if magnitude1 * magnitude2 > 0 else 0

        return {
            'jaccard_similarity': round(jaccard, 4),
            'overlap_coefficient': round(overlap, 4),
            'dice_coefficient': round(dice, 4),
            'cosine_similarity': round(cosine, 4),
            'shared_words': len(words1 & words2),
            'unique_to_text1': len(words1 - words2),
            'unique_to_text2': len(words2 - words1)
        }


# =============================================================================
# CITATION MANAGEMENT
# =============================================================================

@dataclass
class Citation:
    """
    Represents a single citation/reference.

    Supports common citation types: article, book, inproceedings, etc.
    """
    id: str = ""
    entry_type: str = "article"  # article, book, inproceedings, misc, etc.
    author: str = ""
    title: str = ""
    year: int = 0
    journal: str = ""
    booktitle: str = ""
    publisher: str = ""
    volume: str = ""
    number: str = ""
    pages: str = ""
    doi: str = ""
    url: str = ""
    abstract: str = ""
    keywords: List[str] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            # Generate ID from author and year
            author_part = re.sub(r'[^a-zA-Z]', '', self.author.split(',')[0] if self.author else 'unknown')
            self.id = f"{author_part.lower()}{self.year}"


class CitationManager:
    """
    Manage research citations and references.

    Features:
    - Store and organize citations
    - Import/export BibTeX format
    - Generate formatted citations in various styles
    - Search and filter citations

    Example:
        >>> manager = CitationManager()
        >>> manager.add_citation(
        ...     author="Smith, John and Doe, Jane",
        ...     title="A Study of Something",
        ...     year=2024,
        ...     journal="Journal of Research"
        ... )
        >>> print(manager.format_citation("smith2024", style="apa"))
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the citation manager.

        Args:
            db_path: Optional path to SQLite database for persistence
        """
        self.citations: Dict[str, Citation] = {}
        self.db_path = db_path

        if db_path:
            self._init_database()
            self._load_from_database()

    def _init_database(self):
        """Initialize SQLite database for persistent storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS citations (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def _load_from_database(self):
        """Load citations from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, data FROM citations")
            for row in cursor:
                data = json.loads(row[1])
                self.citations[row[0]] = Citation(**data)

    def _save_to_database(self, citation: Citation):
        """Save a citation to the database."""
        if not self.db_path:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO citations (id, data, created_at) VALUES (?, ?, ?)",
                (citation.id, json.dumps(asdict(citation)), citation.created_at)
            )
            conn.commit()

    def add_citation(self, **kwargs) -> Citation:
        """
        Add a new citation.

        Args:
            **kwargs: Citation fields (author, title, year, etc.)

        Returns:
            The created Citation object
        """
        citation = Citation(**kwargs)

        # Ensure unique ID
        base_id = citation.id
        counter = 1
        while citation.id in self.citations:
            citation.id = f"{base_id}{chr(ord('a') + counter - 1)}"
            counter += 1

        self.citations[citation.id] = citation
        self._save_to_database(citation)

        return citation

    def get_citation(self, citation_id: str) -> Optional[Citation]:
        """Get a citation by ID."""
        return self.citations.get(citation_id)

    def remove_citation(self, citation_id: str) -> bool:
        """Remove a citation by ID."""
        if citation_id in self.citations:
            del self.citations[citation_id]

            if self.db_path:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM citations WHERE id = ?", (citation_id,))
                    conn.commit()

            return True
        return False

    def search(self, query: str, fields: Optional[List[str]] = None) -> List[Citation]:
        """
        Search citations by query string.

        Args:
            query: Search query (case-insensitive)
            fields: Fields to search (default: author, title, abstract, keywords)

        Returns:
            List of matching citations
        """
        if fields is None:
            fields = ['author', 'title', 'abstract', 'keywords', 'journal', 'booktitle']

        query_lower = query.lower()
        results = []

        for citation in self.citations.values():
            for field in fields:
                value = getattr(citation, field, '')
                if isinstance(value, list):
                    value = ' '.join(value)
                if query_lower in str(value).lower():
                    results.append(citation)
                    break

        return results

    def filter_by_year(self, start_year: int, end_year: Optional[int] = None) -> List[Citation]:
        """Filter citations by year range."""
        end_year = end_year or start_year
        return [
            c for c in self.citations.values()
            if start_year <= c.year <= end_year
        ]

    def format_citation(self, citation_id: str, style: str = 'apa') -> str:
        """
        Format a citation in the specified style.

        Supported styles: apa, mla, chicago, bibtex
        """
        citation = self.citations.get(citation_id)
        if not citation:
            return f"Citation not found: {citation_id}"

        formatters = {
            'apa': self._format_apa,
            'mla': self._format_mla,
            'chicago': self._format_chicago,
            'bibtex': self._format_bibtex
        }

        formatter = formatters.get(style.lower(), self._format_apa)
        return formatter(citation)

    def _format_apa(self, c: Citation) -> str:
        """Format citation in APA style."""
        # Parse authors for APA format
        authors = self._parse_authors_apa(c.author)

        if c.entry_type == 'article':
            parts = [
                f"{authors} ({c.year}).",
                f"{c.title}.",
                f"*{c.journal}*" if c.journal else "",
                f", {c.volume}" if c.volume else "",
                f"({c.number})" if c.number else "",
                f", {c.pages}." if c.pages else ".",
                f" https://doi.org/{c.doi}" if c.doi else ""
            ]
        elif c.entry_type == 'book':
            parts = [
                f"{authors} ({c.year}).",
                f"*{c.title}*.",
                f"{c.publisher}." if c.publisher else ""
            ]
        else:
            parts = [
                f"{authors} ({c.year}).",
                f"{c.title}.",
                f"*{c.booktitle}*" if c.booktitle else "",
                f" (pp. {c.pages})" if c.pages else "",
                f". {c.publisher}" if c.publisher else "."
            ]

        return ' '.join(p for p in parts if p)

    def _format_mla(self, c: Citation) -> str:
        """Format citation in MLA style."""
        authors = self._parse_authors_mla(c.author)

        if c.entry_type == 'article':
            return f'{authors}. "{c.title}." *{c.journal}*, vol. {c.volume}, no. {c.number}, {c.year}, pp. {c.pages}.'
        elif c.entry_type == 'book':
            return f'{authors}. *{c.title}*. {c.publisher}, {c.year}.'
        else:
            return f'{authors}. "{c.title}." *{c.booktitle}*, {c.year}, pp. {c.pages}.'

    def _format_chicago(self, c: Citation) -> str:
        """Format citation in Chicago style."""
        authors = c.author

        if c.entry_type == 'article':
            return f'{authors}. "{c.title}." {c.journal} {c.volume}, no. {c.number} ({c.year}): {c.pages}.'
        elif c.entry_type == 'book':
            return f'{authors}. {c.title}. {c.publisher}, {c.year}.'
        else:
            return f'{authors}. "{c.title}." In {c.booktitle}, {c.pages}. {c.publisher}, {c.year}.'

    def _format_bibtex(self, c: Citation) -> str:
        """Format citation in BibTeX format."""
        lines = [f"@{c.entry_type}{{{c.id},"]

        field_mapping = {
            'author': c.author,
            'title': c.title,
            'year': str(c.year),
            'journal': c.journal,
            'booktitle': c.booktitle,
            'publisher': c.publisher,
            'volume': c.volume,
            'number': c.number,
            'pages': c.pages,
            'doi': c.doi,
            'url': c.url
        }

        for field, value in field_mapping.items():
            if value:
                lines.append(f"  {field} = {{{value}}},")

        lines[-1] = lines[-1].rstrip(',')  # Remove trailing comma
        lines.append("}")

        return '\n'.join(lines)

    def _parse_authors_apa(self, author_str: str) -> str:
        """Parse author string to APA format."""
        if not author_str:
            return ""

        authors = [a.strip() for a in author_str.split(' and ')]
        formatted = []

        for author in authors:
            if ',' in author:
                # Already in "Last, First" format
                parts = author.split(',')
                last = parts[0].strip()
                first = parts[1].strip() if len(parts) > 1 else ""
                initials = '. '.join(n[0].upper() for n in first.split() if n) + '.'
                formatted.append(f"{last}, {initials}")
            else:
                # "First Last" format
                parts = author.split()
                if parts:
                    last = parts[-1]
                    initials = '. '.join(n[0].upper() for n in parts[:-1] if n) + '.'
                    formatted.append(f"{last}, {initials}")

        if len(formatted) == 1:
            return formatted[0]
        elif len(formatted) == 2:
            return f"{formatted[0]} & {formatted[1]}"
        else:
            return ', '.join(formatted[:-1]) + f", & {formatted[-1]}"

    def _parse_authors_mla(self, author_str: str) -> str:
        """Parse author string to MLA format."""
        if not author_str:
            return ""

        authors = [a.strip() for a in author_str.split(' and ')]

        if len(authors) == 1:
            return authors[0]
        elif len(authors) == 2:
            return f"{authors[0]} and {authors[1]}"
        else:
            return f"{authors[0]}, et al."

    def import_bibtex(self, bibtex_str: str) -> int:
        """
        Import citations from BibTeX format.

        Returns:
            Number of citations imported
        """
        # Simple BibTeX parser
        pattern = r'@(\w+)\s*\{\s*([^,]+)\s*,([^@]+)\}'
        matches = re.findall(pattern, bibtex_str, re.DOTALL)

        count = 0
        for entry_type, citation_id, fields_str in matches:
            # Parse fields
            fields = {}
            field_pattern = r'(\w+)\s*=\s*\{([^}]*)\}'

            for field_name, field_value in re.findall(field_pattern, fields_str):
                fields[field_name.lower()] = field_value.strip()

            # Create citation
            citation = Citation(
                id=citation_id.strip(),
                entry_type=entry_type.lower(),
                author=fields.get('author', ''),
                title=fields.get('title', ''),
                year=int(fields.get('year', 0)) if fields.get('year', '').isdigit() else 0,
                journal=fields.get('journal', ''),
                booktitle=fields.get('booktitle', ''),
                publisher=fields.get('publisher', ''),
                volume=fields.get('volume', ''),
                number=fields.get('number', ''),
                pages=fields.get('pages', ''),
                doi=fields.get('doi', ''),
                url=fields.get('url', ''),
                abstract=fields.get('abstract', '')
            )

            self.citations[citation.id] = citation
            self._save_to_database(citation)
            count += 1

        return count

    def export_bibtex(self) -> str:
        """Export all citations to BibTeX format."""
        return '\n\n'.join(
            self._format_bibtex(c) for c in self.citations.values()
        )

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the citation collection."""
        citations = list(self.citations.values())

        if not citations:
            return {'total': 0}

        years = [c.year for c in citations if c.year > 0]
        types = Counter(c.entry_type for c in citations)

        return {
            'total': len(citations),
            'by_type': dict(types),
            'year_range': (min(years), max(years)) if years else (0, 0),
            'years_distribution': Counter(years),
            'with_doi': sum(1 for c in citations if c.doi),
            'with_abstract': sum(1 for c in citations if c.abstract)
        }


# =============================================================================
# RESEARCH NOTES MANAGER
# =============================================================================

@dataclass
class ResearchNote:
    """Represents a research note."""
    id: str = ""
    title: str = ""
    content: str = ""
    tags: List[str] = field(default_factory=list)
    related_citations: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def __post_init__(self):
        if not self.id:
            self.id = hashlib.md5(
                f"{self.title}{self.created_at}".encode()
            ).hexdigest()[:12]


class NotesManager:
    """
    Manage research notes with tagging and search capabilities.

    Example:
        >>> notes = NotesManager()
        >>> notes.add_note(
        ...     title="Key Findings",
        ...     content="The study revealed significant correlations...",
        ...     tags=["findings", "correlation", "chapter3"]
        ... )
    """

    def __init__(self, db_path: Optional[str] = None):
        """Initialize the notes manager."""
        self.notes: Dict[str, ResearchNote] = {}
        self.db_path = db_path

        if db_path:
            self._init_database()
            self._load_from_database()

    def _init_database(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS note_tags (
                    note_id TEXT,
                    tag TEXT,
                    PRIMARY KEY (note_id, tag),
                    FOREIGN KEY (note_id) REFERENCES notes(id)
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON note_tags(tag)")
            conn.commit()

    def _load_from_database(self):
        """Load notes from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id, data FROM notes")
            for row in cursor:
                data = json.loads(row[1])
                self.notes[row[0]] = ResearchNote(**data)

    def _save_to_database(self, note: ResearchNote):
        """Save note to database."""
        if not self.db_path:
            return

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO notes (id, data, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (note.id, json.dumps(asdict(note)), note.created_at, note.updated_at)
            )

            # Update tags
            conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note.id,))
            for tag in note.tags:
                conn.execute(
                    "INSERT INTO note_tags (note_id, tag) VALUES (?, ?)",
                    (note.id, tag)
                )

            conn.commit()

    def add_note(self, **kwargs) -> ResearchNote:
        """Add a new research note."""
        note = ResearchNote(**kwargs)
        self.notes[note.id] = note
        self._save_to_database(note)
        return note

    def update_note(self, note_id: str, **kwargs) -> Optional[ResearchNote]:
        """Update an existing note."""
        if note_id not in self.notes:
            return None

        note = self.notes[note_id]

        for key, value in kwargs.items():
            if hasattr(note, key):
                setattr(note, key, value)

        note.updated_at = datetime.now().isoformat()
        self._save_to_database(note)

        return note

    def delete_note(self, note_id: str) -> bool:
        """Delete a note."""
        if note_id in self.notes:
            del self.notes[note_id]

            if self.db_path:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                    conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note_id,))
                    conn.commit()

            return True
        return False

    def search(self, query: str) -> List[ResearchNote]:
        """Search notes by title or content."""
        query_lower = query.lower()
        return [
            note for note in self.notes.values()
            if query_lower in note.title.lower() or query_lower in note.content.lower()
        ]

    def get_by_tag(self, tag: str) -> List[ResearchNote]:
        """Get all notes with a specific tag."""
        return [
            note for note in self.notes.values()
            if tag.lower() in [t.lower() for t in note.tags]
        ]

    def get_all_tags(self) -> Dict[str, int]:
        """Get all tags and their counts."""
        tag_counts = Counter()
        for note in self.notes.values():
            tag_counts.update(note.tags)
        return dict(tag_counts)


# =============================================================================
# DATA EXTRACTION PATTERNS
# =============================================================================

class DataExtractor:
    """
    Extract structured data from unstructured text.

    Supports extraction of:
    - Emails, URLs, phone numbers
    - Dates and times
    - Numbers and measurements
    - Custom patterns

    Example:
        >>> extractor = DataExtractor()
        >>> text = "Contact us at info@example.com or call 555-1234"
        >>> emails = extractor.extract_emails(text)
        >>> phones = extractor.extract_phone_numbers(text)
    """

    # Pre-compiled patterns for performance
    PATTERNS = {
        'email': re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        ),
        'url': re.compile(
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\-._~:/?#\[\]@!$&\'()*+,;=]*'
        ),
        'phone_us': re.compile(
            r'(?:\+1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}'
        ),
        'phone_intl': re.compile(
            r'\+[0-9]{1,3}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'
        ),
        'date_iso': re.compile(
            r'\b[0-9]{4}[-/][0-9]{1,2}[-/][0-9]{1,2}\b'
        ),
        'date_us': re.compile(
            r'\b[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4}\b'
        ),
        'time': re.compile(
            r'\b[0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?(?:\s?[AaPp][Mm])?\b'
        ),
        'number': re.compile(
            r'[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?'
        ),
        'percentage': re.compile(
            r'[-+]?[0-9]*\.?[0-9]+\s*%'
        ),
        'currency_usd': re.compile(
            r'\$[0-9]{1,3}(?:,?[0-9]{3})*(?:\.[0-9]{2})?'
        ),
        'ip_address': re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        ),
        'hashtag': re.compile(
            r'#[A-Za-z][A-Za-z0-9_]*'
        ),
        'mention': re.compile(
            r'@[A-Za-z][A-Za-z0-9_]*'
        )
    }

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        return self.PATTERNS['email'].findall(text)

    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text."""
        return self.PATTERNS['url'].findall(text)

    def extract_phone_numbers(self, text: str, region: str = 'us') -> List[str]:
        """Extract phone numbers from text."""
        pattern = self.PATTERNS[f'phone_{region}'] if f'phone_{region}' in self.PATTERNS else self.PATTERNS['phone_intl']
        return pattern.findall(text)

    def extract_dates(self, text: str) -> List[str]:
        """Extract dates from text."""
        dates = []
        dates.extend(self.PATTERNS['date_iso'].findall(text))
        dates.extend(self.PATTERNS['date_us'].findall(text))
        return dates

    def extract_times(self, text: str) -> List[str]:
        """Extract times from text."""
        return self.PATTERNS['time'].findall(text)

    def extract_numbers(self, text: str) -> List[float]:
        """Extract numerical values from text."""
        matches = self.PATTERNS['number'].findall(text)
        return [float(m) for m in matches if m and m not in ['-', '+', '.']]

    def extract_percentages(self, text: str) -> List[str]:
        """Extract percentages from text."""
        return self.PATTERNS['percentage'].findall(text)

    def extract_currency(self, text: str) -> List[str]:
        """Extract currency values from text."""
        return self.PATTERNS['currency_usd'].findall(text)

    def extract_ip_addresses(self, text: str) -> List[str]:
        """Extract IP addresses from text."""
        return self.PATTERNS['ip_address'].findall(text)

    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        return self.PATTERNS['hashtag'].findall(text)

    def extract_mentions(self, text: str) -> List[str]:
        """Extract @mentions from text."""
        return self.PATTERNS['mention'].findall(text)

    def extract_custom(self, text: str, pattern: str) -> List[str]:
        """Extract matches using a custom regex pattern."""
        try:
            compiled = re.compile(pattern)
            return compiled.findall(text)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")

    def extract_all(self, text: str) -> Dict[str, List]:
        """Extract all supported data types from text."""
        return {
            'emails': self.extract_emails(text),
            'urls': self.extract_urls(text),
            'phone_numbers': self.extract_phone_numbers(text),
            'dates': self.extract_dates(text),
            'times': self.extract_times(text),
            'percentages': self.extract_percentages(text),
            'currency': self.extract_currency(text),
            'ip_addresses': self.extract_ip_addresses(text),
            'hashtags': self.extract_hashtags(text),
            'mentions': self.extract_mentions(text)
        }


# =============================================================================
# RESEARCH TOOLKIT (MAIN CLASS)
# =============================================================================

class ResearchToolkit:
    """
    Main class that combines all research tools.

    Provides a unified interface for:
    - Text analysis
    - Citation management
    - Research notes
    - Data extraction

    Example:
        >>> toolkit = ResearchToolkit()
        >>>
        >>> # Analyze a research paper
        >>> analysis = toolkit.analyzer.analyze(paper_text)
        >>>
        >>> # Add citations
        >>> toolkit.citations.add_citation(author="Smith", title="Paper", year=2024)
        >>>
        >>> # Take notes
        >>> toolkit.notes.add_note(title="Key Finding", content="...")
        >>>
        >>> # Extract data
        >>> emails = toolkit.extractor.extract_emails(text)
    """

    def __init__(self, data_dir: Optional[str] = None):
        """
        Initialize the research toolkit.

        Args:
            data_dir: Optional directory for persistent storage
        """
        self.analyzer = TextAnalyzer()
        self.extractor = DataExtractor()

        if data_dir:
            data_path = Path(data_dir)
            data_path.mkdir(parents=True, exist_ok=True)

            self.citations = CitationManager(str(data_path / 'citations.db'))
            self.notes = NotesManager(str(data_path / 'notes.db'))
        else:
            self.citations = CitationManager()
            self.notes = NotesManager()

    def analyze_document(self, text: str) -> Dict[str, Any]:
        """
        Perform comprehensive document analysis.

        Combines text analysis and data extraction.
        """
        result = self.analyzer.analyze(text)
        result['extracted_data'] = self.extractor.extract_all(text)
        return result

    def compare_documents(self, text1: str, text2: str) -> Dict[str, Any]:
        """Compare two documents."""
        return self.analyzer.compare_texts(text1, text2)

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all research data."""
        return {
            'citations': self.citations.get_statistics(),
            'notes': {
                'total': len(self.notes.notes),
                'tags': self.notes.get_all_tags()
            }
        }


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Command-line interface for the Research Toolkit."""
    import sys

    print("=" * 60)
    print("RESEARCH & ANALYSIS TOOLKIT")
    print("=" * 60)
    print()

    # Initialize toolkit
    toolkit = ResearchToolkit()

    # Demo: Text Analysis
    print("1. TEXT ANALYSIS DEMO")
    print("-" * 40)

    sample_text = """
    Machine learning has revolutionized the field of artificial intelligence.
    Recent advances in deep learning have enabled significant breakthroughs
    in natural language processing, computer vision, and robotics. However,
    these powerful systems also raise important ethical concerns regarding
    bias, privacy, and accountability. Researchers must carefully consider
    these implications as they develop new AI systems.
    """

    analysis = toolkit.analyzer.analyze(sample_text)

    print(f"Word count: {analysis['word_count']}")
    print(f"Sentence count: {analysis['sentence_count']}")
    print(f"Flesch Reading Ease: {analysis['flesch_reading_ease']}")
    print(f"Flesch-Kincaid Grade: {analysis['flesch_kincaid_grade']}")
    print(f"Vocabulary Richness: {analysis['vocabulary_richness']:.4f}")
    print(f"Sentiment: {analysis['sentiment']['label']} ({analysis['sentiment']['polarity']:.2f})")
    print(f"Reading time: {analysis['reading_time_minutes']:.1f} minutes")
    print()

    print("Top Words:")
    for word, count in analysis['word_frequency'][:5]:
        print(f"  - {word}: {count}")
    print()

    # Demo: Citation Management
    print("2. CITATION MANAGEMENT DEMO")
    print("-" * 40)

    toolkit.citations.add_citation(
        author="Smith, John and Doe, Jane",
        title="Deep Learning for Natural Language Processing",
        year=2024,
        journal="Journal of Machine Learning",
        volume="15",
        number="3",
        pages="100-120",
        doi="10.1234/example"
    )

    toolkit.citations.add_citation(
        entry_type="book",
        author="Johnson, Alice",
        title="Fundamentals of Artificial Intelligence",
        year=2023,
        publisher="Academic Press"
    )

    print("Added 2 citations")
    print("\nAPA Format:")
    for cid in toolkit.citations.citations:
        print(f"  {toolkit.citations.format_citation(cid, 'apa')}")
    print()

    # Demo: Data Extraction
    print("3. DATA EXTRACTION DEMO")
    print("-" * 40)

    sample_data = """
    Contact our team at research@example.com or support@company.org.
    Call us at (555) 123-4567 or +1-800-555-9999.
    Visit https://example.com/research for more information.
    The study was conducted on 2024-03-15.
    Results showed a 45.5% improvement over baseline.
    Server IP: 192.168.1.100
    Follow us @ResearchTeam using #AIResearch #MachineLearning
    """

    extracted = toolkit.extractor.extract_all(sample_data)

    for dtype, values in extracted.items():
        if values:
            print(f"{dtype}: {values}")
    print()

    # Demo: Document Comparison
    print("4. DOCUMENT COMPARISON DEMO")
    print("-" * 40)

    text1 = "Machine learning enables computers to learn from data without explicit programming."
    text2 = "Computers can learn from data using machine learning algorithms without being explicitly programmed."

    comparison = toolkit.compare_documents(text1, text2)
    print(f"Cosine Similarity: {comparison['cosine_similarity']:.4f}")
    print(f"Jaccard Similarity: {comparison['jaccard_similarity']:.4f}")
    print(f"Shared Words: {comparison['shared_words']}")
    print()

    print("=" * 60)
    print("Research Toolkit Demo Complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    exit(main())
