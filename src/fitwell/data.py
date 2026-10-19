"""資料清理管線：把學生的兩份 Google 表單 CSV 合併成一份乾淨的 dishes.csv。

來源取捨（理由見 docs/ARCHITECTURE.md 第 4 節）：
- 基本欄位（餐廳、菜名、價格、類型）以「健身表」為主，空白時用「養生表」補。
- 烹調方法、辣度、口感以「養生表」為主（養生表補過飲品等空白，且辣度與辣度加權一致）。
- 油脂／蛋白質／鹽分／澱粉加權用「健身表」（養生表後半段的油脂加權沒有更新，全部是 1）。
- 辣度加權、烹調加權用「養生表」。
- 表單裡的「總加權」不採用，一律由 scoring.py 依公式重新計算（養生表有一半列的辣度是用加的）。
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import PROCESSED_CSV, RAW_FITNESS, RAW_WELLNESS, REPORT_MD
from .config import load_config

INVISIBLE = "⁠​‌‍﻿"

# 處理後 CSV 的欄位（中文表頭，方便學生用 Excel 打開或寫程式讀）
COLUMNS = [
    ("id", "編號"),
    ("restaurant", "餐廳"),
    ("name", "餐點名稱"),
    ("price_range", "價格區間"),
    ("main_type", "主餐類型"),
    ("cooking", "烹調方法"),
    ("spicy_level", "辣度"),
    ("texture", "口感"),
    ("tags", "健康標籤"),
    ("fat", "油脂加權"),
    ("protein", "蛋白質加權"),
    ("salt", "鹽分加權"),
    ("starch", "澱粉加權"),
    ("spicy", "辣度加權"),
    ("cooking_w", "烹調加權"),
    ("duplicate_of", "重複於"),
]


@dataclass
class Dish:
    id: int
    restaurant: str
    name: str
    price_range: str
    main_type: str
    cooking: str
    spicy_level: int  # 0 = 不辣，1~5
    texture: int
    tags: list[str]
    fat: int
    protein: int
    salt: int
    starch: int
    spicy: int
    cooking_w: int
    duplicate_of: int | None = None

    def weights(self) -> dict[str, int]:
        """給 scoring 用的各項加權（名稱對應 scoring.json 的 terms）。"""
        return {
            "fat": self.fat,
            "protein": self.protein,
            "salt": self.salt,
            "starch": self.starch,
            "spicy": self.spicy,
            "cooking": self.cooking_w,
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Issue:
    kind: str
    row: int  # 原始表單第幾列（含表頭，所以第一筆資料是第 2 列）
    detail: str


@dataclass
class BuildResult:
    dishes: list[Dish]
    issues: list[Issue] = field(default_factory=list)


# ---------- 小工具 ----------

def clean_text(s: str) -> str:
    for ch in INVISIBLE:
        s = s.replace(ch, "")
    return " ".join(s.split())


def split_list(s: str) -> list[str]:
    return [clean_text(x) for x in s.replace("，", ",").split(",") if clean_text(x)]


def parse_spicy(s: str) -> int:
    s = clean_text(s)
    if s in ("", "不辣"):
        return 0
    try:
        return max(0, min(5, int(s)))
    except ValueError:
        return 0


def parse_int(s: str, default: int = 0) -> int:
    try:
        return int(clean_text(s))
    except ValueError:
        return default


def read_rows(path: Path) -> tuple[list[str], list[list[str]]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    header = [clean_text(h) for h in rows[0]]
    return header, rows[1:]


def col(header: list[str], startswith: str) -> int:
    for i, h in enumerate(header):
        if h.startswith(startswith):
            return i
    raise KeyError(f"找不到欄位：{startswith}（表頭：{header}）")


# ---------- 主流程 ----------

def build(
    fitness_path: Path = RAW_FITNESS,
    wellness_path: Path = RAW_WELLNESS,
    config: dict[str, Any] | None = None,
) -> BuildResult:
    cfg = config or load_config()
    r_alias = cfg["cleaning"]["restaurant_aliases"]
    t_alias = cfg["cleaning"]["main_type_aliases"]
    price_ranges = cfg["price_ranges"]

    fh, frows = read_rows(fitness_path)
    wh, wrows = read_rows(wellness_path)
    issues: list[Issue] = []

    if len(frows) != len(wrows):
        issues.append(Issue("兩表筆數不同", 0, f"健身表 {len(frows)} 筆、養生表 {len(wrows)} 筆，只合併前 {min(len(frows), len(wrows))} 筆"))

    F = {k: col(fh, k) for k in ["第 1 欄", "餐點名稱", "價格區間", "主餐類型", "烹調方法", "辣度(", "口感", "健康程度", "油脂加權", "蛋白質加權", "鹽分加權", "澱粉加權", "總加權"]}
    W = {k: col(wh, k) for k in ["第 1 欄", "餐點名稱", "價格區間", "主餐類型", "烹調方法", "辣度(", "口感", "油脂加權", "辣度加權", "鹽分加權", "澱粉加權", "烹調加權", "總加權"]}

    dishes: list[Dish] = []
    seen: dict[tuple[str, str], int] = {}

    for i, (fr, wr) in enumerate(zip(frows, wrows)):
        rownum = i + 2

        def pick(fkey: str, wkey: str | None = None, prefer: str = "f") -> str:
            fv = clean_text(fr[F[fkey]])
            wv = clean_text(wr[W[wkey or fkey]])
            first, second = (fv, wv) if prefer == "f" else (wv, fv)
            return first or second

        raw_rest = clean_text(fr[F["第 1 欄"]])
        restaurant = r_alias.get(raw_rest, raw_rest)
        if raw_rest != restaurant or raw_rest != fr[F["第 1 欄"]].strip():
            issues.append(Issue("餐廳名稱不一致", rownum, f"「{fr[F['第 1 欄']].strip()}」→ 統一為「{restaurant}」"))

        name = pick("餐點名稱")
        price = pick("價格區間")
        if price not in price_ranges:
            issues.append(Issue("價格區間空白或無法辨識", rownum, f"{restaurant}／{name}：「{price}」"))
            price = ""
        raw_type = clean_text(fr[F["主餐類型"]])
        main_type = t_alias.get(raw_type, raw_type) or clean_text(wr[W["主餐類型"]])
        if raw_type in t_alias:
            issues.append(Issue("主餐類型合併", rownum, f"{name}：「{raw_type}」→「{main_type}」"))

        cooking = pick("烹調方法", prefer="w")
        if cooking in ("無", ""):
            cooking = ""
            issues.append(Issue("烹調方法空白", rownum, f"{restaurant}／{name}"))

        spicy_level = parse_spicy(wr[W["辣度("]])
        f_spicy = parse_spicy(fr[F["辣度("]])
        if f_spicy != spicy_level:
            issues.append(Issue("兩表辣度不同", rownum, f"{name}：健身表 {f_spicy}、養生表 {spicy_level}（採用養生表）"))

        texture = parse_int(wr[W["口感"]], 3)
        if not 1 <= texture <= 5:
            issues.append(Issue("口感超出 1~5", rownum, f"{name}：{texture}（改成 3）"))
            texture = 3

        tags = split_list(fr[F["健康程度"]])

        fat = parse_int(fr[F["油脂加權"]])
        protein = parse_int(fr[F["蛋白質加權"]])
        salt = parse_int(fr[F["鹽分加權"]])
        starch = parse_int(fr[F["澱粉加權"]])
        spicy_w = parse_int(wr[W["辣度加權"]], 1)
        cooking_w = parse_int(wr[W["烹調加權"]], 1)

        w_fat = parse_int(wr[W["油脂加權"]])
        if w_fat != fat:
            issues.append(Issue("養生表油脂加權未更新", rownum, f"{name}：健身表 {fat}、養生表 {w_fat}（採用健身表）"))

        # 標籤 vs 加權 一致性檢查（規則見 docs/ARCHITECTURE.md 第 4 節）
        for label, expect, got in tag_rule_checks(tags, fat, protein, salt, starch):
            issues.append(Issue("標籤與加權不一致", rownum, f"{restaurant}／{name}：標籤「{'、'.join(tags) or '（空）'}」→ {label}應為 {expect}，表單是 {got}"))

        expect_spicy_w = max(1, spicy_level)
        if spicy_w != expect_spicy_w:
            issues.append(Issue("辣度與辣度加權不一致", rownum, f"{name}：辣度 {spicy_level or '不辣'}、辣度加權 {spicy_w}"))

        # 表單總加權驗算
        f_total = parse_int(fr[F["總加權"]])
        f_calc = fat * 2 + protein * 3 - salt + starch
        if f_total != f_calc:
            issues.append(Issue("健身總加權算錯", rownum, f"{name}：表單 {f_total}、驗算 {f_calc}"))
        w_total = parse_int(wr[W["總加權"]])
        w_calc = w_fat - spicy_w + salt + starch + cooking_w * 3
        if w_total != w_calc:
            issues.append(Issue("養生總加權算錯", rownum, f"{name}：表單 {w_total}、驗算（油脂−辣度+鹽分+澱粉+烹調×3）{w_calc}"))

        dish = Dish(
            id=len(dishes) + 1,
            restaurant=restaurant,
            name=name,
            price_range=price,
            main_type=main_type,
            cooking=cooking,
            spicy_level=spicy_level,
            texture=texture,
            tags=tags,
            fat=fat,
            protein=protein,
            salt=salt,
            starch=starch,
            spicy=spicy_w,
            cooking_w=cooking_w,
        )
        key = (restaurant, name)
        if key in seen:
            dish.duplicate_of = seen[key]
            issues.append(Issue("重複的餐點", rownum, f"{restaurant}／{name}（與編號 {seen[key]} 重複，推薦時略過）"))
        else:
            seen[key] = dish.id
        dishes.append(dish)

    return BuildResult(dishes, issues)


def tag_rule_checks(tags: list[str], fat: int, protein: int, salt: int, starch: int):
    """依學生自己的換算規則，檢查健康標籤和加權是否一致。"""
    rules = [
        ("油脂加權", -1 if "高油" in tags else 2 if "低油" in tags else 1, fat),
        ("蛋白質加權", 3 if "高蛋白質" in tags else 1, protein),
        ("鹽分加權", -1 if "高鹽" in tags else 2 if "低鹽" in tags else 1, salt),
        ("澱粉加權", -3 if "多澱粉" in tags else 1, starch),
    ]
    return [(label, e, g) for label, e, g in rules if e != g and not (label == "澱粉加權" and "低澱粉" in tags and g == 2)]


# ---------- 讀寫處理後的檔案 ----------

def write_csv(dishes: list[Dish], path: Path = PROCESSED_CSV) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow([zh for _, zh in COLUMNS])
        for d in dishes:
            row = d.to_dict()
            row["tags"] = "、".join(d.tags)
            row["duplicate_of"] = d.duplicate_of or ""
            w.writerow([row[k] for k, _ in COLUMNS])


def load_dishes(path: Path = PROCESSED_CSV) -> list[Dish]:
    """讀取處理後的 dishes.csv；如果還沒產生，就直接從原始表單建一次。"""
    if not path.exists():
        result = build()
        write_csv(result.dishes, path)
        write_report(result, REPORT_MD)
        return result.dishes
    zh2en = {zh: en for en, zh in COLUMNS}
    out: list[Dish] = []
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            v = {zh2en[k]: val for k, val in r.items() if k in zh2en}
            out.append(
                Dish(
                    id=int(v["id"]),
                    restaurant=v["restaurant"],
                    name=v["name"],
                    price_range=v["price_range"],
                    main_type=v["main_type"],
                    cooking=v["cooking"],
                    spicy_level=int(v["spicy_level"]),
                    texture=int(v["texture"]),
                    tags=[t for t in v["tags"].split("、") if t],
                    fat=int(v["fat"]),
                    protein=int(v["protein"]),
                    salt=int(v["salt"]),
                    starch=int(v["starch"]),
                    spicy=int(v["spicy"]),
                    cooking_w=int(v["cooking_w"]),
                    duplicate_of=int(v["duplicate_of"]) if v.get("duplicate_of") else None,
                )
            )
    return out


def write_report(result: BuildResult, path: Path = REPORT_MD) -> None:
    by_kind: dict[str, list[Issue]] = defaultdict(list)
    for it in result.issues:
        by_kind[it.kind].append(it)
    rest = Counter(d.restaurant for d in result.dishes if d.duplicate_of is None)
    types = Counter(d.main_type for d in result.dishes if d.duplicate_of is None)

    lines = [
        "# 資料檢查報告（自動產生）",
        "",
        "> 由 `fitwell build-data` 產生。請勿手動修改，修正請改 `data/raw/` 的原始表單後重新產生。",
        "",
        f"- 總筆數：{len(result.dishes)}（去除重複後 {sum(rest.values())} 道）",
        f"- 餐廳數：{len(rest)}",
        "",
        "## 各餐廳餐點數",
        "",
        "| 餐廳 | 道數 |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in rest.most_common()],
        "",
        "## 各主餐類型",
        "",
        "| 類型 | 道數 |",
        "|---|---|",
        *[f"| {k} | {v} |" for k, v in types.most_common()],
        "",
        "## 發現的問題（給學生修正用）",
        "",
        "| 問題類型 | 數量 |",
        "|---|---|",
        *[f"| {k} | {len(v)} |" for k, v in sorted(by_kind.items(), key=lambda kv: -len(kv[1]))],
        "",
    ]
    for kind, items in sorted(by_kind.items(), key=lambda kv: -len(kv[1])):
        lines += [f"### {kind}（{len(items)}）", ""]
        lines += [f"- 第 {it.row} 列：{it.detail}" if it.row else f"- {it.detail}" for it in items]
        lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
