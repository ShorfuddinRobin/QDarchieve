print("🔥 NEW HALLE SCRAPER LOADED 🔥")

import sys, time, datetime
from pathlib import Path
from urllib.parse import urljoin
"""
main.py – Entry point for the QDArchive seeding pipeline.

Usage:
    python3 main.py                  # run all scrapers
    python3 main.py --repo dans      # run only DANS scraper
    python3 main.py --repo halle     # run only Uni Halle scraper
    python3 main.py --export-csv     # export DB tables to CSV
"""
import argparse
import sys

from db import database as db


def main():
    parser = argparse.ArgumentParser(description="QDArchive Seeding Pipeline")
    parser.add_argument(
        "--repo",
        choices=["dans", "halle", "all"],
        default="all",
        help="Which repository scraper to run (default: all)",
    )
    parser.add_argument(
        "--export-csv",
        action="store_true",
        help="Export all tables to CSV after scraping",
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Only initialise the database and seed repositories, then exit",
    )
    args = parser.parse_args()

    # Always initialise DB first
    db.init_db()
    db.seed_repositories()

    if args.init_only:
        print("[main] DB initialised. Exiting.")
        return

    if args.repo in ("dans", "all"):
        from scrapers.dans_scraper import run as run_dans
        run_dans()

    if args.repo in ("halle", "all"):
        from scrapers.uni_halle_scraper import run as run_halle
        run_halle()

    if args.export_csv:
        from export.export_csv import main as export_main
        export_main()

    print("\n[main] Pipeline complete.")


if __name__ == "__main__":
    main()
