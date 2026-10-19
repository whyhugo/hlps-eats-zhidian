"""加權評分與紅黃綠燈。

公式寫在 config/scoring.json，每一項是「加權欄位 × 倍數」：
    分數 = Σ (dish.加權[term] × 倍數[term])
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .data import Dish

TERM_LABELS = {
    "fat": "油脂",
    "protein": "蛋白質",
    "salt": "鹽分",
    "starch": "澱粉",
    "spicy": "辣度",
    "cooking": "烹調",
}

LIGHTS = ("green", "yellow", "red")
LIGHT_LABELS = {"green": "綠燈", "yellow": "黃燈", "red": "紅燈"}


@dataclass
class Term:
    key: str
    label: str
    weight: int  # 菜的加權值
    factor: int  # 公式倍數
    points: int  # weight × factor


@dataclass
class Scored:
    dish: Dish
    score: int
    light: str
    terms: list[Term]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dish": self.dish.to_dict(),
            "score": self.score,
            "light": self.light,
            "terms": [t.__dict__ for t in self.terms],
        }


class Scorer:
    def __init__(self, config: dict[str, Any]):
        self.config = config

    def formula_id(self, mode: str, override: str | None = None) -> str:
        fid = override or self.config["active_formula"][mode]
        f = self.config["formulas"].get(fid)
        if f is None:
            raise ValueError(f"找不到公式：{fid}")
        if f["mode"] != mode:
            raise ValueError(f"公式 {fid} 是給 {f['mode']} 模式用的，不是 {mode}")
        return fid

    def score(self, dish: Dish, formula_id: str) -> Scored:
        f = self.config["formulas"][formula_id]
        w = dish.weights()
        terms = [
            Term(k, TERM_LABELS.get(k, k), w[k], factor, w[k] * factor)
            for k, factor in f["terms"].items()
        ]
        total = sum(t.points for t in terms)
        return Scored(dish, total, self.light(total, formula_id), terms)

    def light(self, score: float, formula_id: str) -> str:
        th = self.config["lights"][formula_id]
        if score >= th["green"]:
            return "green"
        if score >= th["yellow"]:
            return "yellow"
        return "red"

    def formula_text(self, formula_id: str) -> str:
        f = self.config["formulas"][formula_id]
        parts = []
        for k, factor in f["terms"].items():
            sign = "−" if factor < 0 else "+"
            parts.append(f"{sign} {TERM_LABELS.get(k, k)}×{abs(factor)}")
        text = " ".join(parts)
        return text[2:] if text.startswith("+ ") else text
