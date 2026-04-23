"""
Automated Data Collection for ALL AI Projects
Downloads and organizes datasets for fine-tuning

Usage:
    python collect_all_data.py --projects all
    python collect_all_data.py --projects cybersecurity finance
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict
import urllib.request
import time

# Configuration
DATA_DIR = "data"
DATABASE_DIR = "databases"

class DataCollector:
    """Base class for data collection"""

    def __init__(self, project_name: str):
        self.project_name = project_name
        self.data_path = Path(DATA_DIR) / project_name
        self.db_path = Path(DATABASE_DIR) / project_name
        self.stats = {"downloaded": 0, "failed": 0, "skipped": 0}

        # Create directories
        self.data_path.mkdir(parents=True, exist_ok=True)
        self.db_path.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level="INFO"):
        """Log messages"""
        print(f"[{level}] {self.project_name}: {message}")

    def download_file(self, url: str, output_path: str, description: str = "") -> bool:
        """Download a file with progress"""
        try:
            self.log(f"Downloading {description or url}...")
            urllib.request.urlretrieve(url, output_path)
            self.stats["downloaded"] += 1
            self.log(f"✓ Downloaded to {output_path}")
            return True
        except Exception as e:
            self.log(f"✗ Failed: {e}", "ERROR")
            self.stats["failed"] += 1
            return False

    def run_command(self, cmd: str, description: str = "") -> bool:
        """Run shell command"""
        try:
            self.log(f"Running: {description or cmd}")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                self.stats["downloaded"] += 1
                self.log(f"✓ Success")
                return True
            else:
                self.log(f"✗ Failed: {result.stderr}", "ERROR")
                self.stats["failed"] += 1
                return False
        except Exception as e:
            self.log(f"✗ Error: {e}", "ERROR")
            self.stats["failed"] += 1
            return False

    def save_metadata(self, metadata: Dict):
        """Save collection metadata"""
        meta_file = self.db_path / "metadata.json"
        with open(meta_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        self.log(f"Metadata saved to {meta_file}")


class CybersecurityDataCollector(DataCollector):
    """Collect cybersecurity datasets"""

    def __init__(self):
        super().__init__("cybersecurity")

    def collect(self):
        """Collect cybersecurity data"""
        self.log("=== Starting Cybersecurity Data Collection ===")

        datasets = []

        # 1. NSL-KDD Dataset (Smaller, manageable)
        self.log("\n[1/5] NSL-KDD Dataset")
        nsl_kdd_url = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain+.txt"
        nsl_kdd_test = "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest+.txt"

        if self.download_file(nsl_kdd_url, self.data_path / "KDDTrain.txt", "NSL-KDD Training"):
            datasets.append("NSL-KDD")
        self.download_file(nsl_kdd_test, self.data_path / "KDDTest.txt", "NSL-KDD Test")

        # 2. Exploit Database (Clone repo - contains POCs)
        self.log("\n[2/5] Exploit Database")
        exploit_db_path = self.data_path / "exploitdb"
        if not exploit_db_path.exists():
            if self.run_command(
                f"git clone --depth 1 https://github.com/offensive-security/exploitdb.git {exploit_db_path}",
                "Cloning Exploit Database"
            ):
                datasets.append("ExploitDB")
        else:
            self.log("ExploitDB already exists, skipping")
            self.stats["skipped"] += 1

        # 3. MITRE ATT&CK Data
        self.log("\n[3/5] MITRE ATT&CK Framework")
        attack_url = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
        if self.download_file(attack_url, self.data_path / "mitre-attack.json", "MITRE ATT&CK"):
            datasets.append("MITRE-ATTACK")

        # 4. CVE Data (Sample - full dataset is huge)
        self.log("\n[4/5] CVE Sample Data")
        cve_url = "https://cve.mitre.org/data/downloads/allitems.csv"
        if self.download_file(cve_url, self.data_path / "cve-all.csv", "CVE List"):
            datasets.append("CVE-Data")

        # 5. Falco Rules (for training)
        self.log("\n[5/5] Falco Rules")
        falco_rules_path = self.data_path / "falco-rules"
        if not falco_rules_path.exists():
            if self.run_command(
                f"git clone --depth 1 https://github.com/falcosecurity/rules.git {falco_rules_path}",
                "Cloning Falco Rules"
            ):
                datasets.append("Falco-Rules")
        else:
            self.log("Falco rules already exist")
            self.stats["skipped"] += 1

        metadata = {
            "project": "cybersecurity",
            "datasets_collected": datasets,
            "stats": self.stats,
            "total_datasets": len(datasets),
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_metadata(metadata)

        return metadata


class FinanceDataCollector(DataCollector):
    """Collect finance datasets"""

    def __init__(self):
        super().__init__("finance")

    def collect(self):
        """Collect finance data"""
        self.log("=== Starting Finance Data Collection ===")

        datasets = []

        # 1. Download S&P 500 data using yfinance
        self.log("\n[1/4] S&P 500 Stock Data (yfinance)")
        yf_script = f"""
import yfinance as yf
import pandas as pd

# Download S&P 500 tickers
sp500_url = 'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv'
tickers_df = pd.read_csv(sp500_url)

# Download sample data (top 50 to save time/space)
for ticker in tickers_df['Symbol'][:50]:
    try:
        data = yf.download(ticker, start='2020-01-01', end='2024-01-01')
        data.to_csv('{self.data_path}/stocks/{{ticker}}.csv')
        print(f'Downloaded {{ticker}}')
    except Exception as e:
        print(f'Failed {{ticker}}: {{e}}')
"""

        script_path = self.data_path / "download_stocks.py"
        with open(script_path, 'w') as f:
            f.write(yf_script)

        (self.data_path / "stocks").mkdir(exist_ok=True)

        if self.run_command(f"python {script_path}", "Downloading stock data"):
            datasets.append("SP500-Stocks")

        # 2. Economic indicators list (lightweight)
        self.log("\n[2/4] FRED Economic Indicators")
        fred_script = f"""
import pandas as pd

# Download list of FRED series
indicators = {{
    'GDP': 'Gross Domestic Product',
    'UNRATE': 'Unemployment Rate',
    'CPIAUCSL': 'Consumer Price Index',
    'FEDFUNDS': 'Federal Funds Rate'
}}

# Save indicator list
pd.DataFrame(list(indicators.items()), columns=['Code', 'Description']).to_csv('{self.data_path}/fred_indicators.csv', index=False)
print('FRED indicator list created')
"""

        fred_script_path = self.data_path / "setup_fred.py"
        with open(fred_script_path, 'w') as f:
            f.write(fred_script)

        if self.run_command(f"python {fred_script_path}", "Setting up FRED indicators"):
            datasets.append("FRED-Indicators")

        # 3. Financial news sentiment dataset (Kaggle - requires manual setup)
        self.log("\n[3/4] Financial Sentiment Dataset")
        sentiment_url = "https://raw.githubusercontent.com/yya518/FinBERT/master/data/sentiment_data/train.csv"
        if self.download_file(sentiment_url, self.data_path / "sentiment_train.csv", "Financial Sentiment"):
            datasets.append("Financial-Sentiment")

        # 4. Company financials structure (template)
        self.log("\n[4/4] Creating Financial Data Structure")
        (self.data_path / "fundamentals").mkdir(exist_ok=True)
        (self.data_path / "news").mkdir(exist_ok=True)
        (self.data_path / "processed").mkdir(exist_ok=True)
        datasets.append("Data-Structure")

        metadata = {
            "project": "finance",
            "datasets_collected": datasets,
            "stats": self.stats,
            "total_datasets": len(datasets),
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": "Run with API keys for full data: ALPHA_VANTAGE_KEY, FRED_API_KEY"
        }
        self.save_metadata(metadata)

        return metadata


class GameDevDataCollector(DataCollector):
    """Collect game development datasets"""

    def __init__(self):
        super().__init__("game_dev")

    def collect(self):
        """Collect game dev data"""
        self.log("=== Starting Game Development Data Collection ===")

        datasets = []

        # 1. Kenney Assets (Free game assets)
        self.log("\n[1/4] Kenney Game Assets")
        kenney_urls = [
            "https://kenney.nl/content/3-assets/1/platformercharacters1.zip",
            "https://kenney.nl/content/3-assets/2/abstractplatformer.zip",
        ]

        (self.data_path / "kenney").mkdir(exist_ok=True)
        for i, url in enumerate(kenney_urls):
            filename = f"kenney_pack_{i+1}.zip"
            if self.download_file(url, self.data_path / "kenney" / filename, f"Kenney Pack {i+1}"):
                datasets.append(f"Kenney-Pack-{i+1}")

        # 2. OpenGameArt metadata (create structure)
        self.log("\n[2/4] OpenGameArt Structure")
        (self.data_path / "opengameart" / "sprites").mkdir(parents=True, exist_ok=True)
        (self.data_path / "opengameart" / "audio").mkdir(parents=True, exist_ok=True)
        (self.data_path / "opengameart" / "3d").mkdir(parents=True, exist_ok=True)
        self.log("Created OpenGameArt directory structure")
        datasets.append("OpenGameArt-Structure")

        # 3. CMU Motion Capture (sample)
        self.log("\n[3/4] CMU Motion Capture Sample")
        mocap_url = "http://mocap.cs.cmu.edu/subjects/16/16_02.bvh"
        if self.download_file(mocap_url, self.data_path / "mocap_sample.bvh", "CMU MoCap Sample"):
            datasets.append("CMU-MoCap-Sample")

        # 4. Game genre taxonomy
        self.log("\n[4/4] Game Genre Taxonomy")
        genre_data = {
            "platformer": ["jump", "run", "climb"],
            "rpg": ["combat", "magic", "inventory"],
            "fps": ["shoot", "aim", "reload"],
            "puzzle": ["match", "solve", "rotate"]
        }

        with open(self.data_path / "genre_taxonomy.json", 'w') as f:
            json.dump(genre_data, f, indent=2)
        datasets.append("Genre-Taxonomy")

        metadata = {
            "project": "game_dev",
            "datasets_collected": datasets,
            "stats": self.stats,
            "total_datasets": len(datasets),
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": "Manual downloads needed: Mixamo (requires Adobe account)"
        }
        self.save_metadata(metadata)

        return metadata


class MusicDataCollector(DataCollector):
    """Collect music datasets"""

    def __init__(self):
        super().__init__("music")

    def collect(self):
        """Collect music data"""
        self.log("=== Starting Music Data Collection ===")

        datasets = []

        # 1. FMA Small subset (8GB - manageable)
        self.log("\n[1/3] Free Music Archive (FMA) - Small")
        self.log("Note: FMA Small is 8GB. This will take time...")
        fma_url = "https://os.unil.cloud.switch.ch/fma/fma_small.zip"
        fma_path = self.data_path / "fma_small.zip"

        # Only download if doesn't exist
        if not fma_path.exists():
            if self.download_file(fma_url, fma_path, "FMA Small Dataset"):
                datasets.append("FMA-Small")
                self.log("Extracting FMA Small...")
                self.run_command(f"unzip -q {fma_path} -d {self.data_path}/fma", "Extracting FMA")
        else:
            self.log("FMA Small already downloaded")
            datasets.append("FMA-Small")
            self.stats["skipped"] += 1

        # 2. MAESTRO MIDI files (smaller subset)
        self.log("\n[2/3] MAESTRO Dataset Info")
        maestro_url = "https://storage.googleapis.com/magentadata/datasets/maestro/v3.0.0/maestro-v3.0.0.json"
        if self.download_file(maestro_url, self.data_path / "maestro_metadata.json", "MAESTRO Metadata"):
            datasets.append("MAESTRO-Metadata")

        # 3. Genre classification data
        self.log("\n[3/3] Music Genre Taxonomy")
        genre_structure = {
            "edm": {"tempo": [128, 140], "energy": "high"},
            "lo-fi": {"tempo": [70, 90], "energy": "relaxed"},
            "jazz": {"tempo": [90, 180], "complexity": "high"},
            "rock": {"tempo": [110, 140], "energy": "high"},
            "classical": {"tempo": [60, 120], "complexity": "very_high"}
        }

        with open(self.data_path / "genre_characteristics.json", 'w') as f:
            json.dump(genre_structure, f, indent=2)
        datasets.append("Genre-Characteristics")

        metadata = {
            "project": "music",
            "datasets_collected": datasets,
            "stats": self.stats,
            "total_datasets": len(datasets),
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": "Large downloads: FMA Medium (25GB), FMA Large (93GB) available separately"
        }
        self.save_metadata(metadata)

        return metadata


class VideoDataCollector(DataCollector):
    """Collect video datasets"""

    def __init__(self):
        super().__init__("video")

    def collect(self):
        """Collect video data"""
        self.log("=== Starting Video Data Collection ===")

        datasets = []

        # 1. YouTube trending metadata (from Kaggle - lightweight)
        self.log("\n[1/3] YouTube Trending Metadata")
        yt_url = "https://raw.githubusercontent.com/GitHubProgrammerNamed/youtube-trending/master/USvideos.csv"
        if self.download_file(yt_url, self.data_path / "youtube_trending.csv", "YouTube Trending Data"):
            datasets.append("YouTube-Trending")

        # 2. Video patterns structure
        self.log("\n[2/3] Video Pattern Templates")
        patterns = {
            "tutorial": {
                "structure": ["hook", "intro", "problem", "solution", "demo", "recap"],
                "pacing": "fast",
                "cuts_per_minute": 20
            },
            "short_form": {
                "structure": ["hook", "content", "payoff"],
                "pacing": "very_fast",
                "cuts_per_minute": 30
            }
        }

        with open(self.data_path / "video_patterns.json", 'w') as f:
            json.dump(patterns, f, indent=2)
        datasets.append("Video-Patterns")

        # 3. Create directory structure
        self.log("\n[3/3] Video Data Structure")
        (self.data_path / "raw_videos").mkdir(exist_ok=True)
        (self.data_path / "processed").mkdir(exist_ok=True)
        (self.data_path / "metadata").mkdir(exist_ok=True)
        datasets.append("Data-Structure")

        metadata = {
            "project": "video",
            "datasets_collected": datasets,
            "stats": self.stats,
            "total_datasets": len(datasets),
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "notes": "API keys needed: PEXELS_API_KEY, YOUTUBE_API_KEY for full data"
        }
        self.save_metadata(metadata)

        return metadata


class CreativityDataCollector(DataCollector):
    """Collect creativity datasets"""

    def __init__(self):
        super().__init__("creativity")

    def collect(self):
        """Collect creativity data"""
        self.log("=== Starting Creativity Data Collection ===")

        datasets = []

        # 1. WritingPrompts dataset
        self.log("\n[1/4] Writing Prompts Dataset")
        wp_url = "https://raw.githubusercontent.com/facebookresearch/ParlAI/main/parlai/tasks/writingprompts/README.md"
        if self.download_file(wp_url, self.data_path / "writingprompts_info.md", "WritingPrompts Info"):
            datasets.append("WritingPrompts-Info")

        # 2. Project Gutenberg samples
        self.log("\n[2/4] Project Gutenberg Samples")
        gutenberg_samples = [
            ("https://www.gutenberg.org/files/1342/1342-0.txt", "pride_and_prejudice.txt"),
            ("https://www.gutenberg.org/files/84/84-0.txt", "frankenstein.txt"),
            ("https://www.gutenberg.org/files/11/11-0.txt", "alice_in_wonderland.txt"),
        ]

        (self.data_path / "books").mkdir(exist_ok=True)
        for url, filename in gutenberg_samples:
            if self.download_file(url, self.data_path / "books" / filename, filename):
                datasets.append(f"Gutenberg-{filename.split('.')[0]}")

        # 3. Creative patterns and structures
        self.log("\n[3/4] Story Structure Templates")
        story_structures = {
            "three_act": ["setup", "confrontation", "resolution"],
            "heros_journey": [
                "ordinary_world", "call_to_adventure", "refusal",
                "meeting_mentor", "crossing_threshold", "tests",
                "ordeal", "reward", "road_back", "resurrection", "return"
            ],
            "save_the_cat": [
                "opening_image", "setup", "theme_stated", "catalyst",
                "debate", "break_into_two", "b_story", "fun_and_games",
                "midpoint", "bad_guys_close_in", "all_is_lost",
                "dark_night", "break_into_three", "finale", "final_image"
            ]
        }

        with open(self.data_path / "story_structures.json", 'w') as f:
            json.dump(story_structures, f, indent=2)
        datasets.append("Story-Structures")

        # 4. Innovation patterns
        self.log("\n[4/4] Innovation Patterns (SCAMPER)")
        innovation_patterns = {
            "scamper": {
                "substitute": "Replace component with alternative",
                "combine": "Merge with other ideas",
                "adapt": "Adjust for different context",
                "modify": "Change size, shape, attributes",
                "put_to_other_use": "Repurpose for new application",
                "eliminate": "Remove unnecessary elements",
                "reverse": "Flip or rearrange"
            }
        }

        with open(self.data_path / "innovation_patterns.json", 'w') as f:
            json.dump(innovation_patterns, f, indent=2)
        datasets.append("Innovation-Patterns")

        metadata = {
            "project": "creativity",
            "datasets_collected": datasets,
            "stats": self.stats,
            "total_datasets": len(datasets),
            "collection_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.save_metadata(metadata)

        return metadata


def main():
    parser = argparse.ArgumentParser(description="Collect data for all AI projects")
    parser.add_argument(
        "--projects",
        nargs="+",
        choices=["all", "cybersecurity", "finance", "game_dev", "music", "video", "creativity"],
        default=["all"],
        help="Which projects to collect data for"
    )
    parser.add_argument("--skip-large", action="store_true", help="Skip large downloads (>1GB)")

    args = parser.parse_args()

    # Determine which projects to run
    if "all" in args.projects:
        projects = ["cybersecurity", "finance", "game_dev", "music", "video", "creativity"]
    else:
        projects = args.projects

    print("="*80)
    print("AUTOMATED DATA COLLECTION FOR AI RESEARCH PROJECTS")
    print("="*80)
    print(f"\nProjects to collect: {', '.join(projects)}")
    print(f"Data directory: {DATA_DIR}")
    print(f"Database directory: {DATABASE_DIR}")
    print("\n" + "="*80 + "\n")

    # Create main directories
    Path(DATA_DIR).mkdir(exist_ok=True)
    Path(DATABASE_DIR).mkdir(exist_ok=True)

    collectors = {
        "cybersecurity": CybersecurityDataCollector,
        "finance": FinanceDataCollector,
        "game_dev": GameDevDataCollector,
        "music": MusicDataCollector,
        "video": VideoDataCollector,
        "creativity": CreativityDataCollector
    }

    results = {}

    # Run collectors
    for project in projects:
        collector_class = collectors.get(project)
        if collector_class:
            print(f"\n{'='*80}")
            print(f"PROJECT: {project.upper()}")
            print(f"{'='*80}\n")

            collector = collector_class()
            try:
                metadata = collector.collect()
                results[project] = metadata

                print(f"\n{'='*80}")
                print(f"✓ {project.upper()} COLLECTION COMPLETE")
                print(f"{'='*80}")
                print(f"Downloaded: {metadata['stats']['downloaded']}")
                print(f"Failed: {metadata['stats']['failed']}")
                print(f"Skipped: {metadata['stats']['skipped']}")
                print(f"Total Datasets: {metadata['total_datasets']}")

            except Exception as e:
                print(f"\n✗ Error collecting {project}: {e}")
                results[project] = {"error": str(e)}

    # Save overall summary
    summary = {
        "collection_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "projects": results,
        "total_projects": len(results)
    }

    summary_file = Path(DATABASE_DIR) / "collection_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)

    print(f"\n{'='*80}")
    print("OVERALL SUMMARY")
    print(f"{'='*80}")
    print(f"Total projects: {len(results)}")
    print(f"Summary saved to: {summary_file}")
    print(f"\nData location: {Path(DATA_DIR).absolute()}")
    print(f"Database location: {Path(DATABASE_DIR).absolute()}")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
