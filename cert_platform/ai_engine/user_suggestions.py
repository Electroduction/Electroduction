"""
User Suggestion and Voting System
Allows users to suggest changes to curriculum
When 75%+ of users agree, change is flagged for admin review
Self-tuning database learns from user consensus
"""
from typing import Dict, List, Any
from datetime import datetime
import json

class UserSuggestionSystem:
    """
    Manages user-suggested changes to curriculum content
    Implements voting threshold system (75% agreement triggers admin review)
    """

    def __init__(self, db_manager):
        self.db = db_manager
        self.vote_threshold = 0.75  # 75% agreement needed

    def submit_suggestion(self, student_id: int, program_id: str,
                         lesson_id: str, suggestion_data: Dict[str, Any]) -> int:
        """
        Submit a suggestion for curriculum change
        Returns suggestion_id
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO content_suggestions (
                student_id, program_id, lesson_id,
                suggestion_type, current_content, suggested_content,
                reason, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            student_id,
            program_id,
            lesson_id,
            suggestion_data.get('type', 'content_update'),
            suggestion_data.get('current_content'),
            suggestion_data.get('suggested_content'),
            suggestion_data.get('reason')
        ))

        suggestion_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return suggestion_id

    def vote_on_suggestion(self, suggestion_id: int, student_id: int,
                          vote: bool, comment: str = None) -> Dict[str, Any]:
        """
        Vote on a suggestion (True = agree, False = disagree)
        Returns updated vote statistics and whether threshold was met
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Record vote
        cursor.execute('''
            INSERT INTO suggestion_votes (suggestion_id, student_id, vote, comment)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(suggestion_id, student_id) DO UPDATE SET
                vote = excluded.vote,
                comment = excluded.comment,
                voted_at = CURRENT_TIMESTAMP
        ''', (suggestion_id, student_id, vote, comment))

        # Get vote statistics
        cursor.execute('''
            SELECT
                COUNT(*) as total_votes,
                SUM(CASE WHEN vote = 1 THEN 1 ELSE 0 END) as agree_votes,
                SUM(CASE WHEN vote = 0 THEN 1 ELSE 0 END) as disagree_votes
            FROM suggestion_votes
            WHERE suggestion_id = ?
        ''', (suggestion_id,))

        stats = dict(cursor.fetchone())

        # Calculate agreement percentage
        agreement_pct = (stats['agree_votes'] / stats['total_votes']
                        if stats['total_votes'] > 0 else 0)

        # Check if threshold met
        threshold_met = agreement_pct >= self.vote_threshold

        result = {
            'suggestion_id': suggestion_id,
            'total_votes': stats['total_votes'],
            'agree_votes': stats['agree_votes'],
            'disagree_votes': stats['disagree_votes'],
            'agreement_percentage': round(agreement_pct * 100, 2),
            'threshold_met': threshold_met,
            'threshold': self.vote_threshold * 100
        }

        # If threshold met, flag for admin review
        if threshold_met and stats['total_votes'] >= 10:  # Minimum 10 votes
            self._flag_for_admin_review(suggestion_id, agreement_pct)
            result['status'] = 'flagged_for_admin_review'

        conn.commit()
        conn.close()

        return result

    def _flag_for_admin_review(self, suggestion_id: int, agreement_pct: float):
        """Flag suggestion for admin review when threshold is met"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE content_suggestions
            SET status = 'pending_admin_review',
                flagged_at = CURRENT_TIMESTAMP,
                agreement_percentage = ?
            WHERE id = ?
        ''', (agreement_pct, suggestion_id))

        # Create admin notification
        cursor.execute('''
            INSERT INTO admin_notifications (
                type, reference_id, message, priority
            ) VALUES (?, ?, ?, ?)
        ''', (
            'suggestion_threshold_met',
            suggestion_id,
            f'Content suggestion #{suggestion_id} has reached {agreement_pct*100:.1f}% agreement (threshold: {self.vote_threshold*100}%)',
            'high'
        ))

        conn.commit()
        conn.close()

    def get_suggestion_details(self, suggestion_id: int) -> Dict[str, Any]:
        """Get complete details about a suggestion including votes"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get suggestion
        cursor.execute('''
            SELECT s.*, st.name as student_name, p.name as program_name
            FROM content_suggestions s
            LEFT JOIN students st ON s.student_id = st.id
            LEFT JOIN programs p ON s.program_id = p.id
            WHERE s.id = ?
        ''', (suggestion_id,))

        suggestion = dict(cursor.fetchone())

        # Get vote breakdown
        cursor.execute('''
            SELECT
                COUNT(*) as total_votes,
                SUM(CASE WHEN vote = 1 THEN 1 ELSE 0 END) as agree_votes,
                SUM(CASE WHEN vote = 0 THEN 1 ELSE 0 END) as disagree_votes
            FROM suggestion_votes
            WHERE suggestion_id = ?
        ''', (suggestion_id,))

        vote_stats = dict(cursor.fetchone())

        # Get recent comments
        cursor.execute('''
            SELECT v.comment, v.vote, v.voted_at, s.name as voter_name
            FROM suggestion_votes v
            LEFT JOIN students s ON v.student_id = s.id
            WHERE v.suggestion_id = ? AND v.comment IS NOT NULL
            ORDER BY v.voted_at DESC
            LIMIT 10
        ''', (suggestion_id,))

        comments = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            **suggestion,
            'vote_stats': vote_stats,
            'recent_comments': comments,
            'agreement_percentage': (
                vote_stats['agree_votes'] / vote_stats['total_votes'] * 100
                if vote_stats['total_votes'] > 0 else 0
            )
        }

    def get_pending_admin_suggestions(self) -> List[Dict[str, Any]]:
        """Get all suggestions pending admin review"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT s.*, COUNT(v.id) as total_votes,
                   SUM(CASE WHEN v.vote = 1 THEN 1 ELSE 0 END) as agree_votes
            FROM content_suggestions s
            LEFT JOIN suggestion_votes v ON s.id = v.suggestion_id
            WHERE s.status = 'pending_admin_review'
            GROUP BY s.id
            ORDER BY s.flagged_at DESC
        ''')

        suggestions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return suggestions

    def admin_review_suggestion(self, suggestion_id: int, admin_id: int,
                               action: str, admin_notes: str = None) -> Dict[str, Any]:
        """
        Admin reviews and takes action on suggestion
        Actions: 'approve', 'reject', 'modify'
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Update suggestion status
        cursor.execute('''
            UPDATE content_suggestions
            SET status = ?,
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                admin_notes = ?
            WHERE id = ?
        ''', (f'admin_{action}', admin_id, admin_notes, suggestion_id))

        # If approved, apply the change
        if action == 'approve':
            self._apply_approved_suggestion(suggestion_id)

        conn.commit()
        conn.close()

        return {
            'suggestion_id': suggestion_id,
            'action': action,
            'message': f'Suggestion {action}ed successfully'
        }

    def _apply_approved_suggestion(self, suggestion_id: int):
        """Apply an approved suggestion to the curriculum"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Get suggestion details
        cursor.execute('''
            SELECT program_id, lesson_id, suggested_content, suggestion_type
            FROM content_suggestions
            WHERE id = ?
        ''', (suggestion_id,))

        suggestion = dict(cursor.fetchone())

        # Get current lesson
        cursor.execute('''
            SELECT content FROM curriculum
            WHERE program_id = ? AND lesson_id = ?
        ''', (suggestion['program_id'], suggestion['lesson_id']))

        current = cursor.fetchone()

        if current:
            # Save old version for rollback
            cursor.execute('''
                INSERT INTO content_improvements (
                    program_id, lesson_id, previous_version,
                    new_version, improvement_reason, feedback_ids
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                suggestion['program_id'],
                suggestion['lesson_id'],
                current['content'],
                suggestion['suggested_content'],
                f"User suggestion #{suggestion_id} approved",
                json.dumps([suggestion_id])
            ))

            # Update curriculum with new content
            cursor.execute('''
                UPDATE curriculum
                SET content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE program_id = ? AND lesson_id = ?
            ''', (
                suggestion['suggested_content'],
                suggestion['program_id'],
                suggestion['lesson_id']
            ))

        conn.commit()
        conn.close()

    def get_user_suggestion_history(self, student_id: int) -> List[Dict[str, Any]]:
        """Get all suggestions submitted by a user"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT s.*,
                   COUNT(v.id) as total_votes,
                   SUM(CASE WHEN v.vote = 1 THEN 1 ELSE 0 END) as agree_votes
            FROM content_suggestions s
            LEFT JOIN suggestion_votes v ON s.id = v.suggestion_id
            WHERE s.student_id = ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
        ''', (student_id,))

        history = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return history

    def get_trending_suggestions(self, program_id: str = None,
                                limit: int = 10) -> List[Dict[str, Any]]:
        """Get suggestions with most recent voting activity"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        query = '''
            SELECT s.*,
                   COUNT(v.id) as total_votes,
                   SUM(CASE WHEN v.vote = 1 THEN 1 ELSE 0 END) as agree_votes,
                   MAX(v.voted_at) as last_vote_at
            FROM content_suggestions s
            LEFT JOIN suggestion_votes v ON s.id = v.suggestion_id
            WHERE s.status = 'pending'
        '''

        params = []
        if program_id:
            query += ' AND s.program_id = ?'
            params.append(program_id)

        query += '''
            GROUP BY s.id
            HAVING total_votes >= 3
            ORDER BY last_vote_at DESC
            LIMIT ?
        '''
        params.append(limit)

        cursor.execute(query, params)

        trending = [dict(row) for row in cursor.fetchall()]

        # Calculate agreement percentage for each
        for suggestion in trending:
            if suggestion['total_votes'] > 0:
                suggestion['agreement_percentage'] = (
                    suggestion['agree_votes'] / suggestion['total_votes'] * 100
                )

        conn.close()

        return trending

    def get_suggestion_statistics(self, program_id: str = None) -> Dict[str, Any]:
        """Get overall statistics about suggestions"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        base_query = 'FROM content_suggestions WHERE 1=1'
        params = []

        if program_id:
            base_query += ' AND program_id = ?'
            params.append(program_id)

        # Total suggestions
        cursor.execute(f'SELECT COUNT(*) as count {base_query}', params)
        total = cursor.fetchone()['count']

        # By status
        cursor.execute(f'''
            SELECT status, COUNT(*) as count
            {base_query}
            GROUP BY status
        ''', params)
        by_status = {row['status']: row['count'] for row in cursor.fetchall()}

        # Average agreement percentage for flagged items
        cursor.execute(f'''
            SELECT AVG(agreement_percentage) as avg_agreement
            {base_query}
            AND status = 'pending_admin_review'
        ''', params)
        avg_agreement = cursor.fetchone()['avg_agreement'] or 0

        conn.close()

        return {
            'total_suggestions': total,
            'by_status': by_status,
            'pending_admin_review': by_status.get('pending_admin_review', 0),
            'approved': by_status.get('admin_approve', 0),
            'rejected': by_status.get('admin_reject', 0),
            'average_agreement_flagged': round(avg_agreement, 2) if avg_agreement else 0
        }
