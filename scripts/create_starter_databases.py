"""
Create starter databases for all projects
Generates initial training data when external sources are blocked

Usage:
    python scripts/create_starter_databases.py --projects all
"""

import os
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
import random

class StarterDatabaseCreator:
    """Create initial databases for training"""

    def __init__(self):
        self.data_dir = Path("data")
        self.db_dir = Path("databases")

    def create_finance_starter(self):
        """Create finance starter database"""
        print("\n=== Creating Finance Starter Database ===")

        finance_data = self.data_dir / "finance"
        finance_data.mkdir(parents=True, exist_ok=True)

        # 1. Sample stock data (synthetic but realistic)
        stocks_dir = finance_data / "stocks"
        stocks_dir.mkdir(exist_ok=True)

        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "JPM", "BAC", "WMT"]

        for ticker in tickers:
            stock_file = stocks_dir / f"{ticker}.csv"

            # Generate 1 year of synthetic data
            data = []
            base_price = random.uniform(50, 500)

            for i in range(252):  # Trading days in a year
                date = (datetime.now() - timedelta(days=252-i)).strftime("%Y-%m-%d")

                # Random walk with slight upward bias
                change = random.gauss(0.001, 0.02)
                base_price = base_price * (1 + change)

                high = base_price * (1 + abs(random.gauss(0, 0.01)))
                low = base_price * (1 - abs(random.gauss(0, 0.01)))
                volume = random.randint(10000000, 100000000)

                data.append({
                    "Date": date,
                    "Open": round(base_price, 2),
                    "High": round(high, 2),
                    "Low": round(low, 2),
                    "Close": round(base_price, 2),
                    "Volume": volume
                })

            with open(stock_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["Date", "Open", "High", "Low", "Close", "Volume"])
                writer.writeheader()
                writer.writerows(data)

            print(f"  ✓ Created {ticker}.csv (252 days)")

        # 2. Financial metrics examples
        metrics_file = finance_data / "sample_metrics.json"
        metrics_examples = {
            "AAPL": {
                "pe_ratio": 28.5,
                "pb_ratio": 39.8,
                "debt_to_equity": 1.73,
                "roe": 1.47,
                "current_ratio": 0.93,
                "market_cap": 2800000000000,
                "sector": "Technology"
            },
            "JPM": {
                "pe_ratio": 10.2,
                "pb_ratio": 1.5,
                "debt_to_equity": 1.2,
                "roe": 0.15,
                "current_ratio": 1.1,
                "market_cap": 450000000000,
                "sector": "Financials"
            }
        }

        with open(metrics_file, 'w') as f:
            json.dump(metrics_examples, f, indent=2)

        print(f"  ✓ Created sample metrics")

        # 3. Financial sentiment data
        sentiment_file = finance_data / "sentiment_samples.csv"
        sentiments = [
            {"text": "Company beats earnings expectations", "sentiment": "positive", "score": 0.85},
            {"text": "Stock plunges on poor guidance", "sentiment": "negative", "score": -0.75},
            {"text": "Analyst upgrades rating to buy", "sentiment": "positive", "score": 0.65},
            {"text": "Concerns over rising debt levels", "sentiment": "negative", "score": -0.55},
            {"text": "Neutral outlook for next quarter", "sentiment": "neutral", "score": 0.05},
        ]

        with open(sentiment_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["text", "sentiment", "score"])
            writer.writeheader()
            writer.writerows(sentiments)

        print(f"  ✓ Created sentiment samples")

        return {"datasets": 3, "files": len(tickers) + 2}

    def create_game_dev_starter(self):
        """Create game dev starter database"""
        print("\n=== Creating Game Dev Starter Database ===")

        game_data = self.data_dir / "game_dev"
        game_data.mkdir(parents=True, exist_ok=True)

        # 1. Asset descriptions for training
        assets_file = game_data / "asset_descriptions.json"
        assets = {
            "characters": [
                {
                    "type": "player_character",
                    "genre": "platformer",
                    "style": "pixel_art",
                    "description": "A brave knight with blue armor and a sword",
                    "movement": ["walk", "run", "jump", "attack"],
                    "size": "32x32"
                },
                {
                    "type": "enemy",
                    "genre": "rpg",
                    "style": "anime",
                    "description": "A fire demon with glowing red eyes",
                    "abilities": ["fireball", "teleport"],
                    "size": "64x64"
                },
                {
                    "type": "npc",
                    "genre": "adventure",
                    "style": "cartoon",
                    "description": "A friendly merchant with a large backpack",
                    "animations": ["idle", "wave", "talk"],
                    "size": "48x48"
                }
            ],
            "environments": [
                {
                    "type": "background",
                    "genre": "platformer",
                    "style": "pixel_art",
                    "description": "A forest scene with trees and clouds",
                    "layers": 3,
                    "size": "1920x1080"
                },
                {
                    "type": "tileset",
                    "genre": "rpg",
                    "style": "top_down",
                    "description": "Castle interior tiles with stone floor",
                    "tile_size": "16x16",
                    "count": 64
                }
            ]
        }

        with open(assets_file, 'w') as f:
            json.dump(assets, f, indent=2)

        print(f"  ✓ Created asset descriptions")

        # 2. Animation timing data
        animations_file = game_data / "animation_timing.json"
        animations = {
            "jump": {
                "genre": "platformer",
                "frames": 8,
                "duration_ms": 400,
                "keyframes": [
                    {"frame": 0, "event": "start", "y_offset": 0},
                    {"frame": 2, "event": "anticipation", "y_offset": -2},
                    {"frame": 4, "event": "peak", "y_offset": -20},
                    {"frame": 7, "event": "land", "y_offset": 0}
                ],
                "sound_sync": {"frame": 0, "sound": "jump_whoosh"}
            },
            "attack": {
                "genre": "action",
                "frames": 12,
                "duration_ms": 600,
                "keyframes": [
                    {"frame": 0, "event": "windup", "rotation": -30},
                    {"frame": 6, "event": "impact", "rotation": 45},
                    {"frame": 11, "event": "recovery", "rotation": 0}
                ],
                "sound_sync": {"frame": 6, "sound": "sword_slash"}
            }
        }

        with open(animations_file, 'w') as f:
            json.dump(animations, f, indent=2)

        print(f"  ✓ Created animation timing data")

        # 3. Sound effect metadata
        sfx_file = game_data / "sound_effects.json"
        sfx = {
            "jump": {"duration_ms": 200, "pitch": "high", "volume": 0.7},
            "land": {"duration_ms": 150, "pitch": "low", "volume": 0.8},
            "coin": {"duration_ms": 100, "pitch": "high", "volume": 0.6},
            "hit": {"duration_ms": 250, "pitch": "mid", "volume": 0.9},
            "powerup": {"duration_ms": 800, "pitch": "ascending", "volume": 0.7}
        }

        with open(sfx_file, 'w') as f:
            json.dump(sfx, f, indent=2)

        print(f"  ✓ Created sound effects metadata")

        return {"datasets": 3, "files": 3}

    def create_music_starter(self):
        """Create music starter database"""
        print("\n=== Creating Music Starter Database ===")

        music_data = self.data_dir / "music"
        music_data.mkdir(parents=True, exist_ok=True)

        # 1. Music theory training data
        theory_file = music_data / "music_theory.json"
        theory = {
            "chord_progressions": {
                "pop": {
                    "I-V-vi-IV": {
                        "examples": ["Let It Be", "Don't Stop Believin'", "Someone Like You"],
                        "key_C": ["C", "G", "Am", "F"],
                        "mood": "uplifting"
                    },
                    "vi-IV-I-V": {
                        "examples": ["Poker Face", "Grenade"],
                        "key_C": ["Am", "F", "C", "G"],
                        "mood": "emotional"
                    }
                },
                "jazz": {
                    "ii-V-I": {
                        "description": "Most common jazz progression",
                        "key_C": ["Dm7", "G7", "Cmaj7"],
                        "function": "turnaround"
                    }
                },
                "blues": {
                    "12_bar_blues": {
                        "bars": ["I", "I", "I", "I", "IV", "IV", "I", "I", "V", "IV", "I", "V"],
                        "key_C": ["C7", "C7", "C7", "C7", "F7", "F7", "C7", "C7", "G7", "F7", "C7", "G7"]
                    }
                }
            },
            "scales": {
                "C_major": {"notes": ["C", "D", "E", "F", "G", "A", "B"], "semitones": [0, 2, 4, 5, 7, 9, 11]},
                "A_minor": {"notes": ["A", "B", "C", "D", "E", "F", "G"], "semitones": [9, 11, 0, 2, 4, 5, 7]},
                "C_pentatonic": {"notes": ["C", "D", "E", "G", "A"], "semitones": [0, 2, 4, 7, 9]}
            }
        }

        with open(theory_file, 'w') as f:
            json.dump(theory, f, indent=2)

        print(f"  ✓ Created music theory data")

        # 2. Genre characteristics (already exists, enhance it)
        characteristics_file = music_data / "genre_characteristics_detailed.json"
        characteristics = {
            "lo-fi": {
                "tempo": {"min": 70, "max": 90, "typical": 80},
                "instruments": ["piano", "drums", "bass", "vinyl_crackle"],
                "production": ["low_pass_filter", "bit_crushing", "vinyl_noise"],
                "mood": ["relaxed", "nostalgic", "study"],
                "song_structure": ["intro", "verse", "chorus", "verse", "outro"],
                "typical_length_seconds": 180
            },
            "edm": {
                "tempo": {"min": 128, "max": 140, "typical": 130},
                "instruments": ["synth", "bass", "drums", "lead"],
                "production": ["sidechain", "build_up", "drop", "riser"],
                "mood": ["energetic", "euphoric", "danceable"],
                "song_structure": ["intro", "build", "drop", "breakdown", "build", "drop", "outro"],
                "typical_length_seconds": 210
            },
            "jazz": {
                "tempo": {"min": 90, "max": 180, "typical": 120},
                "instruments": ["piano", "saxophone", "double_bass", "drums"],
                "characteristics": ["improvisation", "swing", "complex_chords"],
                "mood": ["sophisticated", "smooth", "expressive"],
                "song_structure": ["head", "solos", "head"],
                "typical_length_seconds": 240
            }
        }

        with open(characteristics_file, 'w') as f:
            json.dump(characteristics, f, indent=2)

        print(f"  ✓ Created detailed genre characteristics")

        # 3. Sample lyrics/melodies for training
        training_file = music_data / "training_examples.json"
        examples = {
            "melodies": [
                {
                    "genre": "pop",
                    "notes": ["C4", "D4", "E4", "F4", "G4", "A4", "G4", "F4"],
                    "rhythm": [0.5, 0.5, 0.5, 0.5, 1.0, 1.0, 0.5, 0.5],
                    "mood": "happy"
                },
                {
                    "genre": "blues",
                    "notes": ["C4", "Eb4", "F4", "Gb4", "G4", "Bb4"],
                    "rhythm": [1.0, 0.5, 0.5, 1.0, 1.0, 1.0],
                    "mood": "melancholic"
                }
            ],
            "drum_patterns": [
                {
                    "genre": "rock",
                    "pattern": "four_on_floor",
                    "kick": [0, 0.5, 1, 1.5],
                    "snare": [0.5, 1.5],
                    "hihat": [0, 0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75]
                }
            ]
        }

        with open(training_file, 'w') as f:
            json.dump(examples, f, indent=2)

        print(f"  ✓ Created training examples")

        return {"datasets": 3, "files": 3}

    def create_video_starter(self):
        """Create video starter database"""
        print("\n=== Creating Video Starter Database ===")

        video_data = self.data_dir / "video"
        video_data.mkdir(parents=True, exist_ok=True)

        # 1. Video editing patterns (already exists, enhance)
        patterns_file = video_data / "editing_patterns_detailed.json"
        patterns = {
            "youtube_tutorial": {
                "structure": ["hook", "intro", "problem", "solution", "demo", "recap"],
                "timing": {
                    "hook": {"duration_seconds": 3, "purpose": "grab_attention"},
                    "intro": {"duration_seconds": 10, "purpose": "establish_credibility"},
                    "problem": {"duration_seconds": 30, "purpose": "create_need"},
                    "solution": {"duration_seconds": 60, "purpose": "provide_value"},
                    "demo": {"duration_seconds": 120, "purpose": "show_application"},
                    "recap": {"duration_seconds": 20, "purpose": "reinforce_learning"}
                },
                "cuts_per_minute": 20,
                "b_roll_frequency": "every_15_seconds",
                "text_overlays": True,
                "optimal_length": {"min": 480, "max": 720}
            },
            "short_form": {
                "structure": ["hook", "content", "payoff"],
                "timing": {
                    "hook": {"duration_seconds": 1, "purpose": "instant_grab"},
                    "content": {"duration_seconds": 10, "purpose": "deliver_message"},
                    "payoff": {"duration_seconds": 4, "purpose": "memorable_end"}
                },
                "cuts_per_minute": 40,
                "text_overlays": True,
                "music": "upbeat",
                "optimal_length": {"min": 15, "max": 60}
            },
            "product_review": {
                "structure": ["intro", "unboxing", "features", "testing", "verdict"],
                "b_roll_percentage": 0.4,
                "cuts_per_minute": 15,
                "optimal_length": {"min": 600, "max": 900}
            }
        }

        with open(patterns_file, 'w') as f:
            json.dump(patterns, f, indent=2)

        print(f"  ✓ Created detailed editing patterns")

        # 2. Successful video analysis
        success_file = video_data / "successful_video_patterns.json"
        success_patterns = {
            "high_retention_techniques": [
                {"technique": "pattern_interrupt", "description": "Change visuals every 3-5 seconds"},
                {"technique": "open_loop", "description": "Promise reveal later to keep watching"},
                {"technique": "music_build", "description": "Use music to build anticipation"},
                {"technique": "visual_effects", "description": "Add zooms, pans, transitions"}
            ],
            "hook_formulas": [
                {"formula": "unexpected_statement", "example": "You've been doing X wrong your entire life"},
                {"formula": "question", "example": "What if I told you..."},
                {"formula": "result_first", "example": "Here's the final result..."},
                {"formula": "controversy", "example": "Everyone says X, but they're wrong"}
            ],
            "retention_metrics": {
                "excellent": {">90%": "first_10_seconds", ">60%": "full_video"},
                "good": {">80%": "first_10_seconds", ">40%": "full_video"},
                "average": {">70%": "first_10_seconds", ">30%": "full_video"}
            }
        }

        with open(success_file, 'w') as f:
            json.dump(success_patterns, f, indent=2)

        print(f"  ✓ Created successful video patterns")

        # 3. Scene timing database
        scenes_file = video_data / "scene_timing.json"
        scenes = {
            "tutorial_intro": {"duration_seconds": 10, "shots": 3, "music": "upbeat"},
            "explanation": {"duration_seconds": 30, "shots": 5, "b_roll": True},
            "demo": {"duration_seconds": 45, "shots": 8, "screen_recording": True},
            "conclusion": {"duration_seconds": 15, "shots": 2, "cta": True}
        }

        with open(scenes_file, 'w') as f:
            json.dump(scenes, f, indent=2)

        print(f"  ✓ Created scene timing data")

        return {"datasets": 3, "files": 3}

    def create_creativity_starter(self):
        """Create creativity starter database"""
        print("\n=== Creating Creativity Starter Database ===")

        creativity_data = self.data_dir / "creativity"
        creativity_data.mkdir(parents=True, exist_ok=True)

        # 1. Story structures (already exists, enhance)
        structures_file = creativity_data / "story_structures_detailed.json"
        structures = {
            "three_act": {
                "acts": ["setup", "confrontation", "resolution"],
                "percentages": [0.25, 0.50, 0.25],
                "key_moments": {
                    "inciting_incident": 0.10,
                    "first_plot_point": 0.25,
                    "midpoint": 0.50,
                    "all_is_lost": 0.75,
                    "climax": 0.90
                },
                "examples": ["Star Wars", "The Matrix", "Die Hard"]
            },
            "heros_journey": {
                "stages": [
                    "ordinary_world", "call_to_adventure", "refusal_of_call",
                    "meeting_mentor", "crossing_threshold", "tests_allies_enemies",
                    "approach", "ordeal", "reward", "road_back",
                    "resurrection", "return_with_elixir"
                ],
                "examples": ["The Lord of the Rings", "Harry Potter", "The Lion King"]
            },
            "save_the_cat": {
                "beats": [
                    {"name": "opening_image", "page": 1},
                    {"name": "theme_stated", "page": 5},
                    {"name": "setup", "page": "1-10"},
                    {"name": "catalyst", "page": 12},
                    {"name": "debate", "page": "12-25"},
                    {"name": "break_into_two", "page": 25},
                    {"name": "b_story", "page": 30},
                    {"name": "fun_and_games", "page": "30-55"},
                    {"name": "midpoint", "page": 55},
                    {"name": "bad_guys_close_in", "page": "55-75"},
                    {"name": "all_is_lost", "page": 75},
                    {"name": "dark_night_of_soul", "page": "75-85"},
                    {"name": "break_into_three", "page": 85},
                    {"name": "finale", "page": "85-110"},
                    {"name": "final_image", "page": 110}
                ]
            }
        }

        with open(structures_file, 'w') as f:
            json.dump(structures, f, indent=2)

        print(f"  ✓ Created detailed story structures")

        # 2. Character archetypes
        archetypes_file = creativity_data / "character_archetypes.json"
        archetypes = {
            "hero": {
                "traits": ["brave", "determined", "flawed"],
                "arc": "growth_from_weakness_to_strength",
                "examples": ["Luke Skywalker", "Katniss Everdeen"]
            },
            "mentor": {
                "traits": ["wise", "experienced", "mysterious"],
                "role": "guide_hero",
                "examples": ["Gandalf", "Obi-Wan Kenobi"]
            },
            "shadow": {
                "traits": ["antagonistic", "powerful", "represents_hero_fear"],
                "role": "challenge_hero",
                "examples": ["Darth Vader", "Voldemort"]
            },
            "trickster": {
                "traits": ["unpredictable", "humorous", "chaotic"],
                "role": "comic_relief_and_wisdom",
                "examples": ["Loki", "Jack Sparrow"]
            }
        }

        with open(archetypes_file, 'w') as f:
            json.dump(archetypes, f, indent=2)

        print(f"  ✓ Created character archetypes")

        # 3. Idea generation techniques
        techniques_file = creativity_data / "ideation_techniques.json"
        techniques = {
            "scamper": {
                "substitute": {
                    "question": "What can be substituted?",
                    "example": "Replace X with Y"
                },
                "combine": {
                    "question": "What can be combined?",
                    "example": "Uber + Food = UberEats"
                },
                "adapt": {
                    "question": "What can be adapted from elsewhere?",
                    "example": "Apply Y industry solution to X industry"
                },
                "modify": {
                    "question": "What can be modified?",
                    "example": "Change size, color, shape"
                },
                "put_to_other_use": {
                    "question": "What else can this be used for?",
                    "example": "Repurpose existing product"
                },
                "eliminate": {
                    "question": "What can be removed?",
                    "example": "Simplify by removing features"
                },
                "reverse": {
                    "question": "What can be reversed or rearranged?",
                    "example": "Flip the process or order"
                }
            },
            "random_input": {
                "description": "Use random word to spark ideas",
                "process": ["Choose random word", "Force connection to problem", "Generate ideas from connection"]
            },
            "attribute_listing": {
                "description": "List attributes and modify each",
                "process": ["List all attributes", "Modify each attribute", "Evaluate modifications"]
            }
        }

        with open(techniques_file, 'w') as f:
            json.dump(techniques, f, indent=2)

        print(f"  ✓ Created ideation techniques")

        # 4. Sample creative prompts with responses
        prompts_file = creativity_data / "creative_prompts_samples.json"
        prompts = {
            "story_prompts": [
                {
                    "prompt": "A time traveler accidentally prevents their own birth",
                    "genre": "sci-fi",
                    "conflict": "paradox",
                    "sample_opening": "The moment I shook my grandmother's hand at the 1962 World's Fair, I felt myself beginning to fade..."
                },
                {
                    "prompt": "The last bookstore in a digital world",
                    "genre": "dystopian",
                    "theme": "preservation_vs_progress",
                    "sample_opening": "Marcus turned the sign to 'Open' knowing he might be the last person to ever do so..."
                }
            ],
            "product_ideas": [
                {
                    "problem": "People forget to water plants",
                    "solution": "Smart pot with sensors and auto-watering",
                    "target_market": "busy_professionals",
                    "features": ["moisture_sensor", "app_alerts", "auto_water_dispenser"]
                },
                {
                    "problem": "Hard to find parking",
                    "solution": "AR app showing available spots in real-time",
                    "target_market": "urban_drivers",
                    "features": ["real_time_availability", "reservation", "navigation"]
                }
            ]
        }

        with open(prompts_file, 'w') as f:
            json.dump(prompts, f, indent=2)

        print(f"  ✓ Created creative prompts samples")

        return {"datasets": 4, "files": 4}

    def run_all(self):
        """Create all starter databases"""
        print("\n" + "="*80)
        print("CREATING STARTER DATABASES FOR ALL PROJECTS")
        print("="*80)

        results = {}

        # Finance
        results["finance"] = self.create_finance_starter()

        # Game Dev
        results["game_dev"] = self.create_game_dev_starter()

        # Music
        results["music"] = self.create_music_starter()

        # Video
        results["video"] = self.create_video_starter()

        # Creativity
        results["creativity"] = self.create_creativity_starter()

        # Summary
        print("\n" + "="*80)
        print("STARTER DATABASES CREATION COMPLETE")
        print("="*80)

        total_datasets = sum(r["datasets"] for r in results.values())
        total_files = sum(r["files"] for r in results.values())

        print(f"\nTotal datasets created: {total_datasets}")
        print(f"Total files created: {total_files}")

        for project, stats in results.items():
            print(f"  {project}: {stats['datasets']} datasets, {stats['files']} files")

        # Save summary
        summary = {
            "creation_date": datetime.now().isoformat(),
            "projects": results,
            "total_datasets": total_datasets,
            "total_files": total_files,
            "note": "Starter databases with curated training data"
        }

        summary_file = self.db_dir / "starter_databases_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\nSummary saved to: {summary_file}")
        print("="*80 + "\n")

        return results


def main():
    creator = StarterDatabaseCreator()
    creator.run_all()


if __name__ == "__main__":
    main()
