"""
Semantic Search Engine for Curriculum
Enables intelligent topic search across all programs and lessons
Uses vector embeddings for semantic understanding
"""
import json
import sqlite3
from typing import List, Dict, Any
import re
from collections import Counter
import math

class SemanticSearchEngine:
    """
    Semantic search system for curriculum database
    Supports topic-based search with relevance ranking
    """

    def __init__(self, db_manager):
        self.db = db_manager
        # In production, use actual embeddings (sentence-transformers, OpenAI, etc.)
        # For now, implement TF-IDF based semantic search

    def search_topics(self, query: str, program_id: str = None,
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for topics across curriculum
        Returns ranked results based on semantic relevance
        """
        # Tokenize and clean query
        query_tokens = self._tokenize(query)

        # Get all curriculum items
        curriculum_items = self._get_all_curriculum(program_id)

        # Calculate relevance scores
        results = []
        for item in curriculum_items:
            score = self._calculate_relevance(query_tokens, item)
            if score > 0:
                results.append({
                    **item,
                    'relevance_score': score
                })

        # Sort by relevance
        results.sort(key=lambda x: x['relevance_score'], reverse=True)

        return results[:limit]

    def search_by_keywords(self, keywords: List[str], program_id: str = None) -> List[Dict[str, Any]]:
        """Search using multiple keywords with AND/OR logic"""
        all_results = []

        for keyword in keywords:
            results = self.search_topics(keyword, program_id, limit=50)
            all_results.extend(results)

        # Merge and deduplicate results
        merged = {}
        for result in all_results:
            lesson_id = result['lesson_id']
            if lesson_id in merged:
                merged[lesson_id]['relevance_score'] += result['relevance_score']
            else:
                merged[lesson_id] = result

        # Sort by combined relevance
        final_results = list(merged.values())
        final_results.sort(key=lambda x: x['relevance_score'], reverse=True)

        return final_results

    def search_by_learning_objective(self, objective: str, program_id: str = None) -> List[Dict[str, Any]]:
        """Search for lessons by specific learning objective"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT * FROM curriculum
            WHERE learning_objectives LIKE ?
        '''
        params = [f'%{objective}%']

        if program_id:
            query += ' AND program_id = ?'
            params.append(program_id)

        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def find_prerequisites(self, lesson_id: str) -> List[Dict[str, Any]]:
        """Find prerequisite lessons for a given lesson"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get lesson's parent and prior lessons
        cursor.execute('''
            SELECT c1.* FROM curriculum c1
            JOIN curriculum c2 ON c1.order_index < c2.order_index
            WHERE c2.lesson_id = ?
            AND c1.program_id = c2.program_id
            ORDER BY c1.order_index DESC
            LIMIT 3
        ''', (lesson_id,))

        prerequisites = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return prerequisites

    def find_related_topics(self, lesson_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find related lessons based on content similarity"""
        # Get current lesson
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM curriculum WHERE lesson_id = ?', (lesson_id,))
        current_lesson = dict(cursor.fetchone())

        # Extract keywords from current lesson
        current_text = f"{current_lesson['title']} {current_lesson.get('content', '')}"
        current_tokens = self._tokenize(current_text)

        # Find similar lessons
        cursor.execute('''
            SELECT * FROM curriculum
            WHERE lesson_id != ? AND program_id = ?
        ''', (lesson_id, current_lesson['program_id']))

        all_lessons = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Calculate similarity scores
        related = []
        for lesson in all_lessons:
            lesson_text = f"{lesson['title']} {lesson.get('content', '')}"
            lesson_tokens = self._tokenize(lesson_text)

            similarity = self._calculate_similarity(current_tokens, lesson_tokens)
            if similarity > 0:
                related.append({
                    **lesson,
                    'similarity_score': similarity
                })

        related.sort(key=lambda x: x['similarity_score'], reverse=True)
        return related[:limit]

    def search_across_programs(self, topic: str) -> Dict[str, List[Dict]]:
        """Search for a topic across all programs"""
        programs = [
            'cybersecurity', 'it_software', 'nursing', 'electrician',
            'hvac', 'mechanical_engineering', 'cooking', 'finance',
            'accounting', 'business', 'education', 'ai_education'
        ]

        results_by_program = {}

        for program_id in programs:
            program_results = self.search_topics(topic, program_id, limit=3)
            if program_results:
                results_by_program[program_id] = program_results

        return results_by_program

    def get_curriculum_hierarchy(self, program_id: str) -> Dict[str, Any]:
        """Get complete hierarchical structure of curriculum"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM curriculum
            WHERE program_id = ?
            ORDER BY order_index
        ''', (program_id,))

        items = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Build hierarchy
        hierarchy = {
            'program_id': program_id,
            'main_topics': [],
            'total_lessons': len(items),
            'total_hours': sum(item.get('estimated_hours', 0) for item in items)
        }

        # Group by hierarchy level
        for item in items:
            level = item.get('hierarchy_level', 'lesson')
            if level == 'main':
                hierarchy['main_topics'].append({
                    'id': item['id'],
                    'title': item['title'],
                    'sections': []
                })

        return hierarchy

    def search_by_difficulty(self, program_id: str, difficulty: str) -> List[Dict[str, Any]]:
        """Search lessons by estimated difficulty level"""
        # Difficulty based on word count, hierarchy level, prerequisites
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if difficulty == 'beginner':
            cursor.execute('''
                SELECT * FROM curriculum
                WHERE program_id = ?
                AND order_index < 8
                ORDER BY order_index
            ''', (program_id,))
        elif difficulty == 'intermediate':
            cursor.execute('''
                SELECT * FROM curriculum
                WHERE program_id = ?
                AND order_index BETWEEN 8 AND 15
                ORDER BY order_index
            ''', (program_id,))
        else:  # advanced
            cursor.execute('''
                SELECT * FROM curriculum
                WHERE program_id = ?
                AND order_index > 15
                ORDER BY order_index
            ''', (program_id,))

        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize and clean text"""
        # Convert to lowercase
        text = text.lower()

        # Remove special characters
        text = re.sub(r'[^a-z0-9\s]', '', text)

        # Split into words
        tokens = text.split()

        # Remove stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
                     'to', 'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was',
                     'are', 'were', 'been', 'be', 'have', 'has', 'had', 'do',
                     'does', 'did', 'will', 'would', 'should', 'could', 'may',
                     'might', 'must', 'can', 'this', 'that', 'these', 'those'}

        tokens = [t for t in tokens if t not in stop_words and len(t) > 2]

        return tokens

    def _get_all_curriculum(self, program_id: str = None) -> List[Dict[str, Any]]:
        """Get all curriculum items"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if program_id:
            cursor.execute('SELECT * FROM curriculum WHERE program_id = ?', (program_id,))
        else:
            cursor.execute('SELECT * FROM curriculum')

        items = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return items

    def _calculate_relevance(self, query_tokens: List[str], item: Dict[str, Any]) -> float:
        """Calculate relevance score using TF-IDF approach"""
        # Combine title and content for searching
        item_text = f"{item['title']} {item.get('content', '')} {item.get('learning_objectives', '')}"
        item_tokens = self._tokenize(item_text)

        if not item_tokens:
            return 0.0

        # Calculate term frequency
        item_token_counts = Counter(item_tokens)
        query_token_counts = Counter(query_tokens)

        score = 0.0

        # Title match (higher weight)
        title_tokens = self._tokenize(item['title'])
        title_matches = len(set(query_tokens) & set(title_tokens))
        score += title_matches * 3.0

        # Content match
        for token in query_tokens:
            if token in item_token_counts:
                # TF-IDF score
                tf = item_token_counts[token] / len(item_tokens)
                # Simplified IDF (in production, calculate across all documents)
                idf = math.log(100 / (item_token_counts[token] + 1))
                score += tf * idf

        # Learning objectives match (medium weight)
        objectives_text = str(item.get('learning_objectives', ''))
        objectives_tokens = self._tokenize(objectives_text)
        objectives_matches = len(set(query_tokens) & set(objectives_tokens))
        score += objectives_matches * 2.0

        return score

    def _calculate_similarity(self, tokens1: List[str], tokens2: List[str]) -> float:
        """Calculate cosine similarity between two token sets"""
        if not tokens1 or not tokens2:
            return 0.0

        # Create term frequency vectors
        all_tokens = set(tokens1 + tokens2)

        vec1 = [tokens1.count(token) for token in all_tokens]
        vec2 = [tokens2.count(token) for token in all_tokens]

        # Calculate cosine similarity
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        similarity = dot_product / (magnitude1 * magnitude2)
        return similarity

    def export_search_index(self, output_file: str):
        """Export search index for faster querying"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM curriculum')
        all_items = [dict(row) for row in cursor.fetchall()]
        conn.close()

        # Build search index
        index = {
            'programs': {},
            'keywords': {},
            'total_lessons': len(all_items)
        }

        for item in all_items:
            program_id = item['program_id']

            if program_id not in index['programs']:
                index['programs'][program_id] = []

            index['programs'][program_id].append({
                'lesson_id': item['lesson_id'],
                'title': item['title'],
                'keywords': self._tokenize(item['title'])
            })

        with open(output_file, 'w') as f:
            json.dump(index, f, indent=2)

        return index
