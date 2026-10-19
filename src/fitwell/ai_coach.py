"""AI 營養小教練（選用功能）。

使用者用一句話描述需求（例如「我剛跑完步，想吃清淡一點、300 元以內」），
1. 先把句子轉成篩選條件（有 API 金鑰時用 Claude，沒有時用關鍵字規則）
2. 用和按鈕一樣的推薦引擎算出候選菜
3. 有 API 金鑰時，再請 Claude 從候選菜中挑選並用小學生聽得懂的話解釋

重點：AI 只能從「我們自己的資料庫」裡挑菜，不會自己編造餐點。
沒有設定 ANTHROPIC_API_KEY 時，整個功能仍然可以用（規則版）。
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from .recommend import Query, Recommender

log = logging.getLogger("fitwell.ai")

MODEL = os.environ.get("FITWELL_AI_MODEL", "claude-opus-5-5")

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None


def ai_available() -> bool:
    return anthropic is not None and bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"))


# ---------------- 規則版：關鍵字 → 條件 ----------------

PRICE_WORDS = [
    (r"(100|一百)\s*(元|塊)?\s*(以下|以內|內)|便宜", "100以下"),
    (r"(300|三百)\s*(元|塊)?\s*(以下|以內|內)", "101-300"),
    (r"(500|五百)\s*(元|塊)?\s*(以下|以內|內)", "301-500"),
]
TYPE_WORDS = {
    "海鮮": "海鮮類", "魚": "海鮮類", "蝦": "海鮮類",
    "吃肉": "肉類", "牛": "肉類", "雞": "肉類", "豬": "肉類",
    "蔬菜": "蔬果類", "青菜": "蔬果類", "沙拉": "蔬果類", "素食": "蔬果類",
    "燉飯": "飯類", "炒飯": "飯類", "丼": "飯類", "飯糰": "飯類",
    "麵": "麵類", "湯": "湯類",
}
FITNESS_WORDS = ["健身", "增肌", "運動", "重訓", "跑步", "跑完", "打球", "蛋白", "肌肉", "練"]
WELLNESS_WORDS = ["養生", "清淡", "長輩", "阿嬤", "阿公", "爺爺", "奶奶", "腸胃", "低鹽", "少油", "血壓", "健康"]


def parse_rules(text: str) -> tuple[Query, list[str]]:
    reasons = []
    f = sum(w in text for w in FITNESS_WORDS)
    w = sum(w in text for w in WELLNESS_WORDS)
    mode = "wellness" if w > f else "fitness"
    reasons.append(f"判斷為{'養生' if mode == 'wellness' else '健身'}模式")
    budget = None
    for pat, b in PRICE_WORDS:
        if re.search(pat, text):
            budget = b
            reasons.append(f"預算 {b}")
            break
    max_spicy = None
    if re.search(r"不(要|吃|能吃)?辣|怕辣", text):
        max_spicy = 0
        reasons.append("不吃辣")
    elif "辣" in text:
        max_spicy = 5
        reasons.append("可以吃辣")
    elif mode == "wellness":
        max_spicy = 1
    types = sorted({t for k, t in TYPE_WORDS.items() if k in text})
    if types:
        reasons.append("想吃 " + "、".join(types))
    return Query(mode=mode, budget=budget, max_spicy=max_spicy, main_types=types), reasons


# ---------------- Claude 版 ----------------

PARSE_SCHEMA = {
    "type": "object",
    "properties": {
        "mode": {"type": "string", "enum": ["fitness", "wellness"]},
        "budget": {"type": "string", "enum": ["不限", "100以下", "101-300", "301-500", "500以上"]},
        "max_spicy": {"type": "integer", "description": "-1=不限, 0=不辣, 1~5"},
        "main_types": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["mode", "budget", "max_spicy", "main_types"],
    "additionalProperties": False,
}

PICK_SCHEMA = {
    "type": "object",
    "properties": {
        "picks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"id": {"type": "integer"}, "reason": {"type": "string"}},
                "required": ["id", "reason"],
                "additionalProperties": False,
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["picks", "summary"],
    "additionalProperties": False,
}


def _ask_json(client: Any, system: str, user: str, schema: dict) -> dict | None:
    resp = client.beta.messages.create(
        model=MODEL,
        max_tokens=4000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        output_config={"effort": "low", "format": {"type": "json_schema", "schema": schema}},
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    if resp.stop_reason == "refusal":
        log.warning("Claude 拒絕回答：%s", getattr(resp, "stop_details", None))
        return None
    text = "".join(b.text for b in resp.content if b.type == "text")
    return json.loads(text)


def coach(text: str, rec: Recommender) -> dict[str, Any]:
    """回傳 {source, query, reasons, result, picks, summary}。"""
    text = text.strip()[:300]
    q, reasons = parse_rules(text)
    source = "rules"
    client = None

    if ai_available():
        try:
            client = anthropic.Anthropic()
            all_types = sorted({d.main_type for d in rec.dishes})
            parsed = _ask_json(
                client,
                "你把使用者想吃什麼的描述，轉成竹北遠百餐點推薦機的篩選條件。"
                "fitness=健身（高蛋白、低油），wellness=養生（清淡、低鹽、少辣）。"
                "budget 是價格上限區間，沒提到就填「不限」。max_spicy 0=不辣 5=最辣，沒提到填 -1。"
                f"main_types 只能從這些挑（沒指定就空陣列）：{'、'.join(all_types)}。",
                text,
                PARSE_SCHEMA,
            )
            if parsed:
                q = Query(
                    mode=parsed["mode"],
                    budget=None if parsed["budget"] == "不限" else parsed["budget"],
                    max_spicy=None if parsed["max_spicy"] < 0 else min(5, parsed["max_spicy"]),
                    main_types=[t for t in parsed["main_types"] if t in all_types],
                )
                reasons = ["由 AI 理解你的需求"]
                source = "claude"
        except Exception as e:
            log.warning("AI 解析失敗，改用規則版：%s", e)

    # 先多拿一些候選，再讓 AI 挑
    q.top_n = 8 if client else 3
    result = rec.recommend(q)
    picks = [{"id": s.dish.id, "reason": _rule_reason(s)} for s in result.items[:3]]
    summary = "、".join(reasons)

    if client and result.items:
        try:
            cands = [
                {
                    "id": s.dish.id,
                    "餐廳": s.dish.restaurant,
                    "餐點": s.dish.name,
                    "價格": s.dish.price_range,
                    "類型": s.dish.main_type,
                    "烹調": s.dish.cooking,
                    "辣度": s.dish.spicy_level,
                    "標籤": s.dish.tags,
                    "分數": s.score,
                }
                for s in result.items
            ]
            out = _ask_json(
                client,
                "你是給學生和一般民眾用的營養小教練。只能從提供的候選餐點中挑選最多 3 道（用 id），"
                "每道用一句 30 字以內、親切易懂的繁體中文說明為什麼適合。不要編造營養數字（例如克數、卡路里），"
                "只根據標籤、烹調方式和分數說明。summary 用一句話回應使用者的需求。",
                f"使用者需求：{text}\n候選餐點（已依健康分數排序）：{json.dumps(cands, ensure_ascii=False)}",
                PICK_SCHEMA,
            )
            if out:
                valid = {s.dish.id for s in result.items}
                ai_picks = [p for p in out["picks"] if p["id"] in valid][:3]
                if ai_picks:
                    picks = ai_picks
                    summary = out["summary"]
        except Exception as e:
            log.warning("AI 挑選失敗，改用分數排序：%s", e)

    by_id = {s.dish.id: s for s in result.items}
    return {
        "source": source,
        "query": q.__dict__,
        "summary": summary,
        "result": result.to_dict(),
        "picks": [{**by_id[p["id"]].to_dict(), "reason": p["reason"]} for p in picks if p["id"] in by_id],
    }


def _rule_reason(s) -> str:
    good = [t for t in s.dish.tags if t.startswith("低") or t == "高蛋白質"]
    bits = []
    if good:
        bits.append("、".join(good))
    if s.dish.cooking:
        bits.append(f"烹調方式是{s.dish.cooking}")
    return ("，".join(bits) or "加權分數高") + f"（{s.score} 分）"
