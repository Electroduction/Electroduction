"""
Game State - Persistent progression and account data
"""

import json
import os

class GameState:
    """Manages account-level progression and meta systems"""

    def __init__(self):
        # Account progression
        self.echo_rank = 1  # Account level
        self.total_xp = 0
        self.xp_to_next_rank = 1000

        # Run stats
        self.current_floor = 1
        self.current_biome = "Corrupted Void Ruins"
        self.enemies_killed_this_run = 0
        self.dungeons_cleared = 0

        # Unlocks
        self.unlocked_fragments = []
        self.unlocked_biomes = ["Corrupted Void Ruins"]
        self.discovered_enemies = set()

        # Legacy system
        self.legacy_points = []  # Death markers with fragment data

        # Resources
        self.echo_shards = 0  # Currency
        self.void_essence = 0
        self.solar_essence = 0
        self.temporal_essence = 0

        # Mastery
        self.fragment_mastery = {
            "Void": 0,
            "Solar": 0,
            "Temporal": 0,
            "Aether": 0,
            "Blood": 0
        }

        # Load saved progress if exists
        self.load_progress()

    def add_xp(self, amount):
        """Add experience and handle level ups"""
        self.total_xp += amount

        while self.total_xp >= self.xp_to_next_rank:
            self.total_xp -= self.xp_to_next_rank
            self.echo_rank += 1
            self.xp_to_next_rank = int(self.xp_to_next_rank * 1.5)
            print(f"Echo Rank increased to {self.echo_rank}!")

            # Unlock rewards
            self.grant_rank_rewards()

    def grant_rank_rewards(self):
        """Grant rewards for leveling up"""
        self.echo_shards += 100 * self.echo_rank

        # Unlock new biomes at certain ranks
        if self.echo_rank == 3 and "Lush Floating Forests" not in self.unlocked_biomes:
            self.unlocked_biomes.append("Lush Floating Forests")
            print("Unlocked biome: Lush Floating Forests")

        if self.echo_rank == 5 and "Crystallized Reality Tears" not in self.unlocked_biomes:
            self.unlocked_biomes.append("Crystallized Reality Tears")
            print("Unlocked biome: Crystallized Reality Tears")

    def add_fragment_mastery(self, fragment_type, amount):
        """Increase mastery for a fragment type"""
        if fragment_type in self.fragment_mastery:
            self.fragment_mastery[fragment_type] += amount

            # Check for mastery milestones
            mastery = self.fragment_mastery[fragment_type]
            if mastery % 100 == 0:
                print(f"{fragment_type} mastery reached {mastery}!")

    def add_legacy_point(self, x, y, fragment):
        """Add a death marker"""
        self.legacy_points.append({
            'x': x,
            'y': y,
            'fragment': fragment,
            'floor': self.current_floor,
            'biome': self.current_biome
        })

    def start_new_run(self):
        """Reset run-specific stats"""
        self.current_floor = 1
        self.enemies_killed_this_run = 0

    def save_progress(self):
        """Save game state to file"""
        try:
            save_data = {
                'echo_rank': self.echo_rank,
                'total_xp': self.total_xp,
                'xp_to_next_rank': self.xp_to_next_rank,
                'dungeons_cleared': self.dungeons_cleared,
                'unlocked_fragments': self.unlocked_fragments,
                'unlocked_biomes': self.unlocked_biomes,
                'echo_shards': self.echo_shards,
                'fragment_mastery': self.fragment_mastery
            }

            os.makedirs('save', exist_ok=True)
            with open('save/progress.json', 'w') as f:
                json.dump(save_data, f, indent=2)

            print("Progress saved")
        except Exception as e:
            print(f"Error saving progress: {e}")

    def load_progress(self):
        """Load game state from file"""
        try:
            if os.path.exists('save/progress.json'):
                with open('save/progress.json', 'r') as f:
                    save_data = json.load(f)

                self.echo_rank = save_data.get('echo_rank', 1)
                self.total_xp = save_data.get('total_xp', 0)
                self.xp_to_next_rank = save_data.get('xp_to_next_rank', 1000)
                self.dungeons_cleared = save_data.get('dungeons_cleared', 0)
                self.unlocked_fragments = save_data.get('unlocked_fragments', [])
                self.unlocked_biomes = save_data.get('unlocked_biomes', ["Corrupted Void Ruins"])
                self.echo_shards = save_data.get('echo_shards', 0)
                self.fragment_mastery = save_data.get('fragment_mastery', {
                    "Void": 0, "Solar": 0, "Temporal": 0, "Aether": 0, "Blood": 0
                })

                print(f"Progress loaded - Echo Rank {self.echo_rank}")
        except Exception as e:
            print(f"Error loading progress: {e}")
