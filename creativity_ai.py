"""
Creativity & Idea Generation AI System
Generates creative ideas, stories, and concepts

Usage:
    python creativity_ai.py --mode ideate --problem "Need new product ideas"
    python creativity_ai.py --mode story --theme "space exploration"
"""

import os
import json
import argparse
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class CreativeIdea:
    """Represents a creative idea"""
    concept: str
    novelty_score: float
    feasibility_score: float
    description: str


class CreativeIdeaEngine:
    """Generate creative ideas"""

    def __init__(self):
        self.scamper_techniques = ["Substitute", "Combine", "Adapt", "Modify", "Put to other use", "Eliminate", "Reverse"]

    def generate_ideas(self, problem: str, count: int = 10) -> List[CreativeIdea]:
        """Generate creative ideas using divergent thinking"""
        print(f"Generating {count} ideas for: {problem}")

        ideas = []
        for i in range(count):
            idea = CreativeIdea(
                concept=f"Idea {i+1} for {problem}",
                novelty_score=0.7 + (i % 3) * 0.1,
                feasibility_score=0.6 + (i % 4) * 0.1,
                description=f"Creative solution combining multiple approaches"
            )
            ideas.append(idea)

        # In full implementation:
        # - Use LLM to generate diverse ideas
        # - Apply SCAMPER technique
        # - Cross-domain inspiration
        # - Evaluate novelty and feasibility

        return ideas


class NarrativeEngine:
    """Generate stories and narratives"""

    def __init__(self):
        self.story_structures = {
            "three_act": ["setup", "confrontation", "resolution"],
            "heros_journey": ["ordinary_world", "call_to_adventure", "refusal", "meeting_mentor",
                            "crossing_threshold", "tests", "ordeal", "reward", "road_back",
                            "resurrection", "return"]
        }

    def create_story(self, theme: str, structure: str = "three_act") -> Dict:
        """Generate a complete story"""
        print(f"Creating story with theme: {theme}")
        print(f"Structure: {structure}")

        acts = self.story_structures.get(structure, self.story_structures["three_act"])

        story = {
            "theme": theme,
            "structure": structure,
            "acts": acts,
            "characters": ["protagonist", "antagonist", "mentor"],
            "plot": "Generated plot would go here"
        }

        return story


class CreativityAISystem:
    """Main Creativity AI System"""

    def __init__(self):
        self.idea_engine = CreativeIdeaEngine()
        self.narrative_engine = NarrativeEngine()

    def ideate(self, problem: str, count: int = 10) -> List[CreativeIdea]:
        """Generate ideas for a problem"""
        return self.idea_engine.generate_ideas(problem, count)

    def tell_story(self, theme: str) -> Dict:
        """Generate a story"""
        return self.narrative_engine.create_story(theme)


def main():
    parser = argparse.ArgumentParser(description="Creativity AI System")
    parser.add_argument("--mode", choices=["ideate", "story"], default="ideate")
    parser.add_argument("--problem", help="Problem to solve")
    parser.add_argument("--theme", help="Story theme")
    parser.add_argument("--count", type=int, default=10, help="Number of ideas")

    args = parser.parse_args()

    system = CreativityAISystem()

    if args.mode == "ideate":
        problem = args.problem or "Create innovative product"
        ideas = system.ideate(problem, args.count)

        print(f"\n{'='*60}")
        print(f"GENERATED {len(ideas)} IDEAS")
        print(f"{'='*60}\n")

        for i, idea in enumerate(ideas, 1):
            print(f"{i}. {idea.concept}")
            print(f"   Novelty: {idea.novelty_score:.0%} | Feasibility: {idea.feasibility_score:.0%}")
            print()

    elif args.mode == "story":
        theme = args.theme or "adventure"
        story = system.tell_story(theme)

        print(f"\n{'='*60}")
        print(f"STORY: {story['theme'].upper()}")
        print(f"{'='*60}\n")
        print(json.dumps(story, indent=2))


if __name__ == "__main__":
    main()
