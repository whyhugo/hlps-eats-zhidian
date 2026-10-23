"""匯出純靜態網頁版（Cloudflare Workers 等靜態網站）需要的資料。

    fitwell export-static

產生：
- web/data/bundle.json   菜單、推薦公式、硬體設定、資料報告（網頁直接讀，不需要伺服器）
- tests/golden_engine.json  Python 版推薦結果，用來檢查 JS 版（web/engine.js）算出一樣的分數

改了 data/、config/scoring.json 或 config/hardware.json 之後要重新執行，再 push 到 GitHub。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import REPORT_MD, ROOT
from .ai_coach import parse_rules
from .config import load_config, load_hardware
from .data import load_dishes
from .recommend import Query, Recommender

BUNDLE = ROOT / "web" / "data" / "bundle.json"
GOLDEN = ROOT / "tests" / "golden_engine.json"

# 拿來比對的查詢：涵蓋兩種模式、每個預算、辣度、類型、湊不滿 3 道的情況
GOLDEN_QUERIES: list[dict[str, Any]] = [
    {"mode": m, "budget": b, "max_spicy": s, "main_types": t}
    for m in ("fitness", "wellness")
    for b in (None, "100以下", "101-300", "301-500", "500以上")
    for s in (None, 0, 2, 5)
    for t in ([], ["海鮮類"], ["麵類", "飯類"])
] + [
    {"mode": "fitness", "budget": "100以下", "max_spicy": 0, "main_types": ["炸物類"]},
    {"mode": "wellness", "budget": "100以下", "max_spicy": 0, "main_types": ["肉類"], "formula": None},
    {"mode": "fitness", "budget": None, "max_spicy": None, "main_types": [], "formula": "fitness_v1"},
    {"mode": "fitness", "budget": "301-500", "max_spicy": 2, "main_types": [], "top_n": 8},
]

GOLDEN_TRAYS = [[1, 2], [1, 2, 3, 4, 5], [10, 20, 30], [7]]

GOLDEN_TEXTS = [
    "我剛跑完步，想吃高蛋白但不要太油，300 元以內",
    "帶阿嬤吃飯，要清淡、不辣、好咬",
    "想吃海鮮，養生一點，不要辣",
    "100 元以內有什麼健康的",
    "我想吃辣的麵",
    "Just finished a workout, want high protein under 300",
    "Taking grandma out, something light and not spicy",
    "Spicy seafood noodle soup, cheap please",
    "I want chicken or beef rice under NT$500",
]


def build_bundle() -> dict[str, Any]:
    cfg = load_config()
    dishes = [d for d in load_dishes() if d.duplicate_of is None]
    return {
        "_說明": "由 `uv run fitwell export-static` 產生，請不要手動修改。",
        "dishes": [d.to_dict() for d in dishes],
        "config": {k: v for k, v in cfg.items() if not k.startswith("_") and k != "cleaning"},
        "hardware": load_hardware(),
        "report": REPORT_MD.read_text(encoding="utf-8") if REPORT_MD.exists() else "",
    }


def _summary(r: dict[str, Any]) -> dict[str, Any]:
    return {
        "ids": [s["dish"]["id"] for s in r["items"]],
        "scores": [s["score"] for s in r["items"]],
        "lights": [s["light"] for s in r["items"]],
        "light": r["light"],
        "percent": r["percent"],
        "candidates": r["candidates"],
        "steps": r["steps"],
        "hints": r["hints"],
        "hint_codes": r["hint_codes"],
        "formula_id": r["formula_id"],
        "formula_text": r["formula_text"],
    }


def build_golden() -> dict[str, Any]:
    rec = Recommender(load_dishes(), load_config())
    recs = []
    for q in GOLDEN_QUERIES:
        recs.append({"query": q, "result": _summary(rec.recommend(Query(**q)).to_dict())})
    trays = []
    for ids in GOLDEN_TRAYS:
        for mode in ("fitness", "wellness"):
            t = rec.evaluate_tray(ids, mode)
            trays.append({"ids": ids, "mode": mode, "average": t["average"], "light": t["light"],
                          "percent": t["percent"], "warnings": t["warnings"], "warning_codes": t["warning_codes"]})
    texts = []
    for text in GOLDEN_TEXTS:
        q, reasons = parse_rules(text)
        texts.append({"text": text, "query": {k: q.__dict__[k] for k in ("mode", "budget", "max_spicy", "main_types")},
                      "reasons": reasons})
    return {"recommend": recs, "tray": trays, "parse": texts}


def export_static() -> tuple[Path, Path]:
    BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    BUNDLE.write_text(json.dumps(build_bundle(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    GOLDEN.write_text(json.dumps(build_golden(), ensure_ascii=False, indent=1), encoding="utf-8")
    return BUNDLE, GOLDEN
