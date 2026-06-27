"""
Adaptive Learning System
Personalizes learning paths based on student performance and feedback
"""
from typing import Dict, List, Any
import json
from datetime import datetime

class AdaptiveLearningSystem:
    """
    Creates personalized learning paths and adapts based on student feedback
    """

    def __init__(self):
        self.learning_styles = ['visual', 'auditory', 'reading', 'kinesthetic']
        self.difficulty_levels = ['beginner', 'intermediate', 'advanced']

    def create_learning_path(self, student_id: int, program_id: str,
                           prior_knowledge: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create personalized learning path based on student's prior knowledge
        """
        if prior_knowledge is None:
            prior_knowledge = {}

        # Assess student's starting level
        starting_level = self._assess_level(prior_knowledge)

        # Get recommended path
        path = {
            "student_id": student_id,
            "program_id": program_id,
            "starting_level": starting_level,
            "customized_modules": [],
            "recommended_pace": self._calculate_pace(prior_knowledge),
            "learning_style": prior_knowledge.get('learning_style', 'mixed'),
            "created_at": datetime.now().isoformat()
        }

        # Customize module order based on prerequisites and level
        path['customized_modules'] = self._customize_module_order(
            program_id,
            starting_level,
            prior_knowledge
        )

        return path

    def _assess_level(self, prior_knowledge: Dict[str, Any]) -> str:
        """Assess student's starting level"""
        experience = prior_knowledge.get('years_experience', 0)
        education = prior_knowledge.get('education_level', 'none')
        related_skills = prior_knowledge.get('related_skills', [])

        score = 0

        # Score based on experience
        if experience > 5:
            score += 3
        elif experience > 2:
            score += 2
        elif experience > 0:
            score += 1

        # Score based on education
        education_scores = {
            'doctorate': 3,
            'masters': 3,
            'bachelors': 2,
            'associates': 1,
            'high_school': 0,
            'none': 0
        }
        score += education_scores.get(education.lower(), 0)

        # Score based on related skills
        score += min(len(related_skills), 3)

        # Determine level
        if score >= 6:
            return 'advanced'
        elif score >= 3:
            return 'intermediate'
        else:
            return 'beginner'

    def _calculate_pace(self, prior_knowledge: Dict[str, Any]) -> str:
        """Calculate recommended learning pace"""
        time_available = prior_knowledge.get('hours_per_week', 10)

        if time_available >= 20:
            return 'accelerated'  # 8-10 weeks
        elif time_available >= 10:
            return 'standard'  # 12-16 weeks
        else:
            return 'extended'  # 16-20 weeks

    def _customize_module_order(self, program_id: str, level: str,
                                prior_knowledge: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Customize module order based on student level and knowledge
        """
        # Base modules would come from education_engine
        # Here we add customization metadata

        customized = []

        # If advanced, can skip some foundational content
        if level == 'advanced':
            customized.append({
                "module_id": "assessment_1",
                "type": "assessment",
                "reason": "Verify advanced knowledge",
                "skip_if_passed": ["module_1", "module_2"]
            })

        # Add focus areas based on career goals
        career_goal = prior_knowledge.get('career_goal')
        if career_goal:
            customized.append({
                "module_id": f"specialized_{career_goal}",
                "type": "specialization",
                "reason": f"Aligned with career goal: {career_goal}"
            })

        # Add practice modules based on learning style
        learning_style = prior_knowledge.get('learning_style', 'mixed')
        customized.append({
            "module_id": f"practice_{learning_style}",
            "type": "practice",
            "reason": f"Optimized for {learning_style} learners"
        })

        return customized

    def process_feedback(self, feedback_data: Dict[str, Any]):
        """
        Process student feedback and update learning path
        """
        student_id = feedback_data.get('student_id')
        rating = feedback_data.get('rating')
        difficulty_rating = feedback_data.get('difficulty_rating', 3)

        # Adjust difficulty if content is too hard or too easy
        adjustments = {
            "student_id": student_id,
            "adjustments": []
        }

        # Too difficult
        if rating < 3 and difficulty_rating > 4:
            adjustments['adjustments'].append({
                "type": "add_prerequisite",
                "reason": "Content too difficult - adding foundational material"
            })
            adjustments['adjustments'].append({
                "type": "slow_pace",
                "reason": "Reducing pace to allow more time for understanding"
            })

        # Too easy
        elif rating >= 4 and difficulty_rating < 2:
            adjustments['adjustments'].append({
                "type": "skip_similar",
                "reason": "Content too easy - skipping redundant modules"
            })
            adjustments['adjustments'].append({
                "type": "accelerate",
                "reason": "Student ready for advanced content"
            })

        # Content not helpful
        elif not feedback_data.get('helpful', True):
            adjustments['adjustments'].append({
                "type": "alternative_resources",
                "reason": "Providing alternative learning materials"
            })

        return adjustments

    def get_next_lessons(self, student_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recommended next lessons for a student
        Uses spaced repetition and mastery-based progression
        """
        # In production, would query database for:
        # 1. Student's progress
        # 2. Performance on previous lessons
        # 3. Time since last review
        # 4. Learning path customization

        next_lessons = [
            {
                "lesson_id": "next_1",
                "priority": "high",
                "reason": "Next in sequence",
                "estimated_time": "2 hours"
            },
            {
                "lesson_id": "review_1",
                "priority": "medium",
                "reason": "Spaced repetition review",
                "estimated_time": "30 minutes"
            }
        ]

        return next_lessons[:limit]

    def calculate_mastery_score(self, student_id: int, program_id: str,
                                module_id: str) -> float:
        """
        Calculate student's mastery score for a module
        """
        # Factors:
        # - Assessment scores
        # - Time to complete
        # - Number of attempts
        # - Practical exercise quality
        # - Retention over time

        # Placeholder calculation
        base_score = 0.75
        return base_score

    def recommend_review_sessions(self, student_id: int) -> List[Dict[str, Any]]:
        """
        Recommend review sessions based on spaced repetition algorithm
        """
        review_sessions = [
            {
                "module_id": "module_1",
                "last_reviewed": "2 weeks ago",
                "recommended_date": "today",
                "reason": "Spaced repetition interval reached"
            }
        ]

        return review_sessions

    def generate_study_plan(self, student_id: int, target_completion_date: str) -> Dict[str, Any]:
        """
        Generate a week-by-week study plan
        """
        # Calculate weeks available
        # Distribute modules across weeks
        # Account for review sessions
        # Include buffer time for projects

        study_plan = {
            "student_id": student_id,
            "target_date": target_completion_date,
            "weekly_schedule": [
                {
                    "week": 1,
                    "modules": ["module_1", "module_2"],
                    "estimated_hours": 10,
                    "milestones": ["Complete foundational assessment"]
                }
            ],
            "total_estimated_hours": 120,
            "completion_probability": 0.85
        }

        return study_plan

    def identify_struggling_students(self, program_id: str) -> List[Dict[str, Any]]:
        """
        Identify students who may need additional support
        """
        # Criteria:
        # - Low assessment scores
        # - Slow progress
        # - Negative feedback
        # - Long time since last login

        struggling_students = [
            {
                "student_id": 123,
                "issues": ["Low quiz scores", "Inactive for 7 days"],
                "recommendations": [
                    "Offer 1-on-1 tutoring",
                    "Provide additional resources",
                    "Send encouragement email"
                ]
            }
        ]

        return struggling_students

    def predict_completion_probability(self, student_id: int,
                                      program_id: str) -> float:
        """
        Predict probability of student completing program
        Uses machine learning model trained on historical data
        """
        # Features:
        # - Engagement metrics (login frequency, time spent)
        # - Performance metrics (assessment scores)
        # - Progress rate
        # - Demographic factors
        # - Prior education/experience

        # Placeholder prediction
        return 0.78

    def generate_personalized_encouragement(self, student_id: int,
                                           progress: Dict[str, Any]) -> str:
        """
        Generate personalized encouragement message
        """
        completion = progress.get('completion_percentage', 0)

        if completion < 25:
            return "Great start! You're building a strong foundation. Keep up the excellent work!"
        elif completion < 50:
            return "You're making solid progress! You're almost halfway there. Your dedication is paying off!"
        elif completion < 75:
            return "Outstanding progress! You're in the home stretch. Your certification is within reach!"
        else:
            return "Incredible work! You're nearly certified. Finish strong and achieve your goal!"
