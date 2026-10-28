"""推薦引擎：完全照學生流程圖的順序。

    輸入模式 → 用該模式的加權公式計分 → 依分數排序
    → 是否超出預算？ → 是否超出可接受辣度？ → 是否符合主餐類型？
    → 取前 3 道 → 顯示推薦結果（紅／黃／綠燈）
    → 不足 3 道時，告訴使用者可以放寬哪個條件
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .data import Dish
from .scoring import Scored, Scorer

MODES = {"fitness": "健身", "wellness": "養生"}


@dataclass
class Query:
    mode: str = "fitness"
    budget: str | None = None  # 價格上限（含），None = 不限
    max_spicy: int | None = None  # 0 = 只要不辣，None = 不限
    main_types: list[str] = field(default_factory=list)  # 空 = 不限
    exclude_types: list[str] | None = None  # None = 用預設（飲料、甜點）
    restaurants: list[str] = field(default_factory=list)  # 空 = 不限
    top_n: int | None = None
    formula: str | None = None


@dataclass
class Result:
    query: Query
    formula_id: str
    formula_label: str
    formula_text: str
    items: list[Scored]
    light: str
    candidates: int
    steps: list[dict[str, Any]]
    hints: list[str]
    percent: int = 0  # 推薦結果平均分數在所有餐點分數中的位置 0~100（給燈環、伺服馬達指針用）
    hint_codes: list[dict[str, Any]] = field(default_factory=list)  # 和 hints 一一對應，給網頁翻譯用

    @property
    def enough(self) -> bool:
        return len(self.items) >= (self.query.top_n or 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query.__dict__,
            "mode_label": MODES[self.query.mode],
            "formula_id": self.formula_id,
            "formula_label": self.formula_label,
            "formula_text": self.formula_text,
            "items": [s.to_dict() for s in self.items],
            "light": self.light,
            "percent": self.percent,
            "enough": self.enough,
            "candidates": self.candidates,
            "steps": self.steps,
            "hints": self.hints,
            "hint_codes": self.hint_codes,
        }


class Recommender:
    def __init__(self, dishes: list[Dish], config: dict[str, Any]):
        self.dishes = [d for d in dishes if d.duplicate_of is None]
        self.config = config
        self.scorer = Scorer(config)
        self.price_ranges: list[str] = config["price_ranges"]

    # ----- 單一條件判斷（拆開寫，方便對照流程圖的菱形） -----

    def over_budget(self, d: Dish, budget: str | None) -> bool:
        if not budget:
            return False
        if not d.price_range:
            return True  # 價格不明就不推薦，避免超支
        return self.price_ranges.index(d.price_range) > self.price_ranges.index(budget)

    @staticmethod
    def too_spicy(d: Dish, max_spicy: int | None) -> bool:
        return max_spicy is not None and d.spicy_level > max_spicy

    @staticmethod
    def type_mismatch(d: Dish, q: Query, exclude: list[str]) -> bool:
        if q.main_types:
            return d.main_type not in q.main_types
        return d.main_type in exclude

    @staticmethod
    def restaurant_mismatch(d: Dish, q: Query) -> bool:
        return bool(q.restaurants) and d.restaurant not in q.restaurants

    # ----- 主流程 -----

    def recommend(self, q: Query) -> Result:
        if q.mode not in MODES:
            raise ValueError(f"模式只能是 {list(MODES)}")
        if q.budget and q.budget not in self.price_ranges:
            raise ValueError(f"預算只能是 {self.price_ranges}")
        defaults = self.config["defaults"]
        top_n = q.top_n or defaults["top_n"]
        exclude = defaults["exclude_types"] if q.exclude_types is None else q.exclude_types
        fid = self.scorer.formula_id(q.mode, q.formula)
        formula = self.config["formulas"][fid]

        # 1~2. 計分、依分數排序（同分時：辣度低、價格低的優先，再依編號）
        scored = [self.scorer.score(d, fid) for d in self.dishes]
        scored.sort(key=lambda s: (-s.score, s.dish.spicy_level, self._price_idx(s.dish), s.dish.id))

        # 3. 依序過濾，記錄每一步剩幾道（給畫面上的「流程圖動畫」用）
        steps = [{"step": "計分排序", "remaining": len(scored)}]
        pool = [s for s in scored if not self.over_budget(s.dish, q.budget)]
        steps.append({"step": "預算", "remaining": len(pool)})
        pool = [s for s in pool if not self.too_spicy(s.dish, q.max_spicy)]
        steps.append({"step": "辣度", "remaining": len(pool)})
        pool = [s for s in pool if not self.type_mismatch(s.dish, q, exclude)]
        steps.append({"step": "主餐類型", "remaining": len(pool)})
        if q.restaurants:
            pool = [s for s in pool if not self.restaurant_mismatch(s.dish, q)]
            steps.append({"step": "餐廳", "remaining": len(pool)})

        items = pool[:top_n]
        steps.append({"step": f"取前 {top_n} 名", "remaining": len(items)})

        light = self._overall_light(items, fid)
        relax = [] if len(items) >= top_n else self._relax_hints(q, scored, exclude, top_n)

        percent = self.percent_of(sum(s.score for s in items) / len(items), fid) if items else 0

        return Result(
            percent=percent,
            query=Query(**{**q.__dict__, "top_n": top_n}),
            formula_id=fid,
            formula_label=formula["label"],
            formula_text=self.scorer.formula_text(fid),
            items=items,
            light=light,
            candidates=len(pool),
            steps=steps,
            hints=[text for text, _ in relax],
            hint_codes=[code for _, code in relax],
        )

    def evaluate_tray(self, dish_ids: list[int], mode: str, formula: str | None = None) -> dict[str, Any]:
        """「我的餐盤」：把幾道菜組合起來，看整餐是綠／黃／紅燈。"""
        fid = self.scorer.formula_id(mode, formula)
        by_id = {d.id: d for d in self.dishes}
        picked = [self.scorer.score(by_id[i], fid) for i in dish_ids if i in by_id]
        if not picked:
            return {"items": [], "average": 0, "light": "red", "percent": 0, "warnings": ["餐盤是空的"],
                    "warning_codes": [{"code": "empty"}]}
        avg = sum(s.score for s in picked) / len(picked)
        warnings = []
        codes: list[dict[str, Any]] = []  # 和 warnings 一一對應，給網頁翻譯用
        n_fat = sum(1 for s in picked if "高油" in s.dish.tags)
        n_salt = sum(1 for s in picked if "高鹽" in s.dish.tags)
        n_starch = sum(1 for s in picked if "多澱粉" in s.dish.tags)
        if n_fat >= 2:
            warnings.append(f"有 {n_fat} 道高油餐點，油脂可能過量")
            codes.append({"code": "fat", "n": n_fat})
        if n_salt >= 2:
            warnings.append(f"有 {n_salt} 道高鹽餐點，鈉含量偏高")
            codes.append({"code": "salt", "n": n_salt})
        if n_starch >= 2:
            warnings.append(f"有 {n_starch} 道多澱粉餐點，澱粉偏多")
            codes.append({"code": "starch", "n": n_starch})
        if mode == "fitness" and not any("高蛋白質" in s.dish.tags for s in picked):
            warnings.append("健身模式建議至少一道高蛋白質餐點")
            codes.append({"code": "protein"})
        if mode == "wellness" and any(s.dish.spicy_level >= 3 for s in picked):
            warnings.append("養生模式建議避免太辣的餐點")
            codes.append({"code": "spicy"})
        light = self.scorer.light(avg, fid)
        percent = self.percent_of(avg, fid)
        # 有兩個以上警告時，整餐最多黃燈；三個以上就是紅燈
        if len(warnings) >= 3:
            light = "red"
        elif len(warnings) >= 2 and light == "green":
            light = "yellow"
        return {
            "items": [s.to_dict() for s in picked],
            "average": round(avg, 1),
            "light": light,
            "percent": percent,
            "warnings": warnings,
            "warning_codes": codes,
            "formula_id": fid,
        }

    # ----- 輔助 -----

    def percent_of(self, score: float, fid: str) -> int:
        """分數換算成 0~100（在所有餐點分數中的位置），給伺服馬達指針、燈環用。"""
        scores = [self.scorer.score(d, fid).score for d in self.dishes]
        lo, hi = min(scores), max(scores)
        if hi <= lo:
            return 100
        return max(0, min(100, round(100 * (score - lo) / (hi - lo))))

    def _price_idx(self, d: Dish) -> int:
        return self.price_ranges.index(d.price_range) if d.price_range in self.price_ranges else len(self.price_ranges)

    def _overall_light(self, items: list[Scored], fid: str) -> str:
        if not items:
            return "red"
        avg = sum(s.score for s in items) / len(items)
        return self.scorer.light(avg, fid)

    def _relax_hints(
        self, q: Query, scored: list[Scored], exclude: list[str], top_n: int
    ) -> list[tuple[str, dict[str, Any]]]:
        """推薦不到足夠道數時，試著各自放寬一個條件，看能多出幾道。"""

        def count(budget=q.budget, max_spicy=q.max_spicy, types=True, rest=True) -> int:
            n = 0
            for s in scored:
                d = s.dish
                if self.over_budget(d, budget) or self.too_spicy(d, max_spicy):
                    continue
                if types and self.type_mismatch(d, q, exclude):
                    continue
                if rest and self.restaurant_mismatch(d, q):
                    continue
                n += 1
            return n

        hints = []
        if q.budget and q.budget != self.price_ranges[-1]:
            nxt = self.price_ranges[self.price_ranges.index(q.budget) + 1]
            n = count(budget=nxt)
            if n > 0:
                hints.append((f"把預算提高到「{nxt}」可以找到 {n} 道", {"code": "budget", "value": nxt, "n": n}))
        if q.max_spicy is not None and q.max_spicy < 5:
            n = count(max_spicy=q.max_spicy + 1)
            if n > 0:
                hints.append((f"可接受辣度放寬到 {q.max_spicy + 1} 可以找到 {n} 道",
                              {"code": "spicy", "value": q.max_spicy + 1, "n": n}))
        if q.main_types:
            n = count(types=False)
            if n > 0:
                hints.append((f"主餐類型改成「不限」可以找到 {n} 道", {"code": "types", "n": n}))
        if q.restaurants:
            n = count(rest=False)
            if n > 0:
                hints.append((f"餐廳改成「不限」可以找到 {n} 道", {"code": "restaurants", "n": n}))
        if not hints:
            hints.append(("請換一個模式或放寬多個條件再試一次", {"code": "none"}))
        return hints
