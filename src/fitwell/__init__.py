"""Fit & Well Menu Navigator — 竹北遠百健身／養生餐點推薦機。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config" / "scoring.json"
HARDWARE_PATH = ROOT / "config" / "hardware.json"
RAW_FITNESS = ROOT / "data" / "raw" / "menu_fitness.csv"
RAW_WELLNESS = ROOT / "data" / "raw" / "menu_wellness.csv"
PROCESSED_CSV = ROOT / "data" / "processed" / "dishes.csv"
REPORT_MD = ROOT / "data" / "processed" / "data_report.md"
WEB_DIR = ROOT / "web"

__version__ = "0.1.0"
