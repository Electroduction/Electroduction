"""
Organize collected data into databases by SOURCE ORIGIN
Groups data by where it came from for better organization

Usage:
    python scripts/organize_databases.py --projects all
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List

# Database organization by SOURCE
DATABASE_SOURCES = {
    "cybersecurity": {
        "github": {
            "description": "Data from GitHub repositories",
            "datasets": [
                {
                    "name": "ExploitDB",
                    "source": "https://github.com/offensive-security/exploitdb",
                    "path": "exploitdb",
                    "format": "git_repo",
                    "size_mb": "~100MB"
                },
                {
                    "name": "Falco-Rules",
                    "source": "https://github.com/falcosecurity/rules",
                    "path": "falco-rules",
                    "format": "yaml",
                    "size_mb": "~5MB"
                }
            ]
        },
        "mitre": {
            "description": "MITRE Corporation data",
            "datasets": [
                {
                    "name": "ATT&CK-Framework",
                    "source": "https://github.com/mitre/cti",
                    "path": "mitre-attack.json",
                    "format": "json",
                    "size_mb": "44MB"
                }
            ]
        },
        "academic": {
            "description": "Academic research datasets",
            "datasets": [
                {
                    "name": "NSL-KDD",
                    "source": "Canadian Institute for Cybersecurity",
                    "paths": ["KDDTrain.txt", "KDDTest.txt"],
                    "format": "csv",
                    "size_mb": "22MB",
                    "records": "148,517 total"
                }
            ]
        },
        "government": {
            "description": "Government vulnerability databases",
            "datasets": [
                {
                    "name": "CVE-Database",
                    "source": "NIST NVD / CVE.org",
                    "path": "cve-all.csv",
                    "format": "csv",
                    "size_mb": "varies",
                    "note": "May require API access"
                }
            ]
        }
    },
    "finance": {
        "yahoo_finance": {
            "description": "Yahoo Finance stock data",
            "datasets": [
                {
                    "name": "SP500-Stocks",
                    "source": "yfinance library",
                    "path": "stocks/",
                    "format": "csv",
                    "records": "50 stocks x 1000+ days"
                }
            ]
        },
        "federal_reserve": {
            "description": "US Federal Reserve economic data",
            "datasets": [
                {
                    "name": "FRED-Indicators",
                    "source": "FRED API",
                    "path": "fred_indicators.csv",
                    "format": "csv",
                    "note": "Requires FRED_API_KEY"
                }
            ]
        },
        "academic": {
            "description": "Financial research datasets",
            "datasets": [
                {
                    "name": "Financial-Sentiment",
                    "source": "FinBERT project",
                    "path": "sentiment_train.csv",
                    "format": "csv"
                }
            ]
        }
    },
    "game_dev": {
        "kenney": {
            "description": "Kenney game assets (CC0)",
            "datasets": [
                {
                    "name": "Kenney-Assets",
                    "source": "https://kenney.nl",
                    "path": "kenney/",
                    "format": "png/zip",
                    "license": "CC0"
                }
            ]
        },
        "cmu": {
            "description": "Carnegie Mellon University",
            "datasets": [
                {
                    "name": "CMU-MoCap",
                    "source": "http://mocap.cs.cmu.edu",
                    "path": "mocap_sample.bvh",
                    "format": "bvh",
                    "note": "Motion capture data"
                }
            ]
        },
        "opengameart": {
            "description": "Open source game art",
            "datasets": [
                {
                    "name": "OpenGameArt",
                    "source": "https://opengameart.org",
                    "path": "opengameart/",
                    "format": "various",
                    "note": "Manual downloads required"
                }
            ]
        }
    },
    "music": {
        "fma": {
            "description": "Free Music Archive",
            "datasets": [
                {
                    "name": "FMA-Small",
                    "source": "https://github.com/mdeff/fma",
                    "path": "fma_small.zip",
                    "format": "mp3",
                    "size_mb": "8000MB",
                    "tracks": "8,000 tracks"
                }
            ]
        },
        "google_magenta": {
            "description": "Google Magenta datasets",
            "datasets": [
                {
                    "name": "MAESTRO",
                    "source": "https://magenta.tensorflow.org",
                    "path": "maestro_metadata.json",
                    "format": "midi/wav",
                    "note": "Piano performances"
                }
            ]
        }
    },
    "video": {
        "youtube": {
            "description": "YouTube trending data",
            "datasets": [
                {
                    "name": "YouTube-Trending",
                    "source": "GitHub dataset",
                    "path": "youtube_trending.csv",
                    "format": "csv"
                }
            ]
        }
    },
    "creativity": {
        "gutenberg": {
            "description": "Project Gutenberg",
            "datasets": [
                {
                    "name": "Classic-Books",
                    "source": "https://www.gutenberg.org",
                    "path": "books/",
                    "format": "txt",
                    "count": "3 samples"
                }
            ]
        },
        "reddit": {
            "description": "Reddit writing prompts",
            "datasets": [
                {
                    "name": "WritingPrompts",
                    "source": "r/WritingPrompts",
                    "path": "writingprompts_info.md",
                    "format": "text"
                }
            ]
        }
    }
}


class DatabaseOrganizer:
    """Organize databases by data source origin"""

    def __init__(self):
        self.data_dir = Path("data")
        self.db_dir = Path("databases")
        self.report = {}

    def organize_project(self, project: str):
        """Organize a project's data by source"""
        print(f"\n{'='*80}")
        print(f"ORGANIZING: {project.upper()}")
        print(f"{'='*80}\n")

        if project not in DATABASE_SOURCES:
            print(f"No organization defined for {project}")
            return

        project_data = self.data_dir / project
        project_db = self.db_dir / project

        if not project_data.exists():
            print(f"No data found for {project}")
            return

        # Create organized structure
        sources = DATABASE_SOURCES[project]
        organized_db = project_db / "by_source"
        organized_db.mkdir(parents=True, exist_ok=True)

        project_report = {
            "project": project,
            "sources": {},
            "total_datasets": 0,
            "total_size_mb": 0
        }

        # Organize by source
        for source_name, source_info in sources.items():
            print(f"Source: {source_name}")
            print(f"  Description: {source_info['description']}")

            source_dir = organized_db / source_name
            source_dir.mkdir(parents=True, exist_ok=True)

            source_report = {
                "description": source_info["description"],
                "datasets": []
            }

            # Copy/link datasets to organized location
            for dataset in source_info["datasets"]:
                print(f"  Dataset: {dataset['name']}")

                # Check if data exists
                if "paths" in dataset:
                    paths = dataset["paths"]
                elif "path" in dataset:
                    paths = [dataset["path"]]
                else:
                    paths = []

                found = False
                for path in paths:
                    src_path = project_data / path
                    if src_path.exists():
                        found = True
                        print(f"    ✓ Found: {path}")

                        # Create metadata file in organized location
                        meta_file = source_dir / f"{dataset['name']}_metadata.json"
                        with open(meta_file, 'w') as f:
                            json.dump(dataset, f, indent=2)

                        source_report["datasets"].append({
                            "name": dataset["name"],
                            "original_path": str(src_path),
                            "metadata": str(meta_file),
                            "status": "found"
                        })
                    else:
                        print(f"    ✗ Not found: {path}")
                        source_report["datasets"].append({
                            "name": dataset["name"],
                            "expected_path": path,
                            "status": "missing"
                        })

            project_report["sources"][source_name] = source_report
            project_report["total_datasets"] += len(source_info["datasets"])

        # Save organization report
        report_file = organized_db / "organization_report.json"
        with open(report_file, 'w') as f:
            json.dump(project_report, f, indent=2)

        print(f"\n✓ Organization report saved: {report_file}")

        self.report[project] = project_report

    def generate_summary(self):
        """Generate summary of database organization"""
        print(f"\n{'='*80}")
        print("DATABASE ORGANIZATION SUMMARY")
        print(f"{'='*80}\n")

        for project, report in self.report.items():
            print(f"\n{project.upper()}:")
            print(f"  Total sources: {len(report['sources'])}")
            print(f"  Total datasets: {report['total_datasets']}")

            print(f"\n  By Source:")
            for source_name, source_data in report["sources"].items():
                found = sum(1 for d in source_data["datasets"] if d.get("status") == "found")
                total = len(source_data["datasets"])
                print(f"    {source_name:20s}: {found}/{total} datasets found")

        # Save overall summary
        summary_file = self.db_dir / "organization_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(self.report, f, indent=2)

        print(f"\n✓ Overall summary: {summary_file}")
        print(f"{'='*80}\n")

    def print_database_structure(self):
        """Print the organized database structure"""
        print(f"\n{'='*80}")
        print("ORGANIZED DATABASE STRUCTURE")
        print(f"{'='*80}\n")

        print("databases/")
        print("├── collection_summary.json         # Collection statistics")
        print("├── organization_summary.json       # Organization summary")
        print("│")

        for project in DATABASE_SOURCES.keys():
            print(f"├── {project}/")
            print(f"│   ├── metadata.json              # Collection metadata")
            print(f"│   └── by_source/                 # ← ORGANIZED BY DATA SOURCE")

            if project in DATABASE_SOURCES:
                sources = list(DATABASE_SOURCES[project].keys())
                for i, source in enumerate(sources):
                    is_last = (i == len(sources) - 1)
                    prefix = "└──" if is_last else "├──"
                    print(f"│       {prefix} {source}/              # {DATABASE_SOURCES[project][source]['description']}")

                    datasets = DATABASE_SOURCES[project][source]["datasets"]
                    for j, dataset in enumerate(datasets):
                        is_last_ds = (j == len(datasets) - 1)
                        ds_prefix = "    └──" if is_last else "│   └──"
                        if not is_last:
                            ds_prefix = "│   ├──" if not is_last_ds else "│   └──"
                        else:
                            ds_prefix = "    ├──" if not is_last_ds else "    └──"

                        print(f"│       {ds_prefix} {dataset['name']}_metadata.json")

            print("│")

        print(f"\n{'='*80}\n")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Organize databases by source origin")
    parser.add_argument(
        "--projects",
        nargs="+",
        choices=["all", "cybersecurity", "finance", "game_dev", "music", "video", "creativity"],
        default=["all"]
    )

    args = parser.parse_args()

    projects = list(DATABASE_SOURCES.keys()) if "all" in args.projects else args.projects

    organizer = DatabaseOrganizer()

    # Show what the structure will look like
    organizer.print_database_structure()

    # Organize each project
    for project in projects:
        organizer.organize_project(project)

    # Generate summary
    organizer.generate_summary()


if __name__ == "__main__":
    main()
