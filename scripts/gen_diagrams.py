"""產生系統架構圖表 SVG（docs/images/diagrams/*.svg）。

    uv run python scripts/gen_diagrams.py

風格（字型、配色）與 scripts/gen_wiring.py 的接線圖一致。
"""

from __future__ import annotations

from pathlib import Path

from gen_wiring import C, esc, text

OUT = Path(__file__).resolve().parents[1] / "docs" / "images" / "diagrams"

DEFS = f"""<defs>
<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="{C['ink']}"/></marker>
<marker id="ahm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
  <path d="M0,0 L10,5 L0,10 z" fill="{C['muted']}"/></marker>
</defs>"""


def page(w, h, title, subtitle, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {w} {h}">{DEFS}'
        f'<rect width="{w}" height="{h}" rx="22" fill="{C["bg"]}"/>'
        f'<rect x="16" y="16" width="{w - 32}" height="{h - 32}" rx="18" fill="{C["card"]}" stroke="{C["line"]}"/>'
        + text(44, 62, title, 24, C["ink"], "bold")
        + text(44, 90, subtitle, 15, C["muted"])
        + body
        + "</svg>"
    )


def box(x, y, w, h, title, lines=(), color=C["blue"], fill=None, title_size=15, line_size=13):
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill or C["card"]}" stroke="{color}" stroke-width="2"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="6" rx="3" fill="{color}"/>',
        text(x + 14, y + 28, title, title_size, C["ink"], "bold"),
    ]
    for i, s in enumerate(lines):
        out.append(text(x + 14, y + 50 + i * 20, s, line_size, C["muted"]))
    return "".join(out)


def group(x, y, w, h, title, color):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{color}0f" stroke="{color}" stroke-width="1.5" stroke-dasharray="6 5"/>'
        + text(x + 16, y + 26, title, 14, color, "bold")
    )


def arrow(x1, y1, x2, y2, label=None, color=None, both=False, dashed=False, lx=None, ly=None, anchor="middle"):
    col = color or C["ink"]
    marker = "ah" if col == C["ink"] else "ahm"
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    start = f' marker-start="url(#{marker})"' if both else ""
    out = f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="2"{dash}{start} marker-end="url(#{marker})"/>'
    if label:
        tx = lx if lx is not None else (x1 + x2) / 2
        ty = ly if ly is not None else (y1 + y2) / 2 - 8
        for i, part in enumerate(label.split("\n")):
            out += text(tx, ty + i * 17, part, 12, C["ink"], anchor=anchor)
    return out


def chip(x, y, w, label, color):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="28" rx="14" fill="{color}1a" stroke="{color}" stroke-width="1.2"/>'
        + text(x + w / 2, y + 19, label, 12.5, C["ink"], anchor="middle")
    )


def diamond(cx, cy, w, h, label, color=C["orange"]):
    pts = f"{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}"
    return (
        f'<polygon points="{pts}" fill="{color}14" stroke="{color}" stroke-width="2"/>'
        + text(cx, cy + 5, label, 13.5, C["ink"], "bold", "middle")
    )


def pill(cx, cy, w, label, color=C["ink"]):
    return (
        f'<rect x="{cx - w / 2}" y="{cy - 18}" width="{w}" height="36" rx="18" fill="{color}" />'
        + text(cx, cy + 5, label, 14, "#ffffff", "bold", "middle")
    )


# ---------------- 1. 系統架構 ----------------

def fig_system():
    o = []
    # 硬體層
    o.append(group(40, 120, 250, 470, "① 硬體層 micro:bit V1／V2", C["green"]))
    o.append(text(58, 168, "輸入", 13, C["muted"], "bold"))
    for i, s in enumerate(["A／B 鍵", "健身鈕 P13／養生鈕 P14", "預算旋鈕 P4", "辣度旋鈕 P10"]):
        o.append(chip(58, 178 + i * 36, 214, s, C["blue"]))
    o.append(text(58, 344, "輸出", 13, C["muted"], "bold"))
    for i, s in enumerate(["紅黃綠 LED P0～P2", "伺服馬達指針 P12", "蜂鳴器 P16", "5×5 點陣"]):
        o.append(chip(58, 354 + i * 36, 214, s, C["orange"]))
    o.append(text(58, 516, "韌體只負責輸入與輸出", 12.5, C["ink"], "bold"))
    o.append(text(58, 540, "↑ MODE／GO／BUDGET／SPICY", 11.5, C["muted"]))
    o.append(text(58, 560, "↓ CFG／SCORE／LIGHT／SHOW", 11.5, C["muted"]))

    # 伺服器層
    o.append(group(340, 120, 330, 470, "② 電腦：fitwell serve（Python）", C["blue"]))
    o.append(box(360, 156, 290, 70, "serial_bridge 序列埠橋接", ["自動偵測、握手、斷線重連、當機自動重啟"], C["blue"]))
    o.append(box(360, 240, 290, 70, "機台狀態 KioskState", ["模式、預算、辣度、類型（網頁與硬體共用）"], C["blue"]))
    o.append(box(360, 324, 140, 90, "recommend", ["過濾、排序", "前 3 名、燈號"], C["green"]))
    o.append(box(510, 324, 140, 90, "scoring", ["加權公式", "分數拆解"], C["green"]))
    o.append(box(360, 428, 140, 70, "ai_coach", ["一句話 → 條件"], C["purple"]))
    o.append(box(510, 428, 140, 70, "FastAPI", ["REST＋SSE"], C["teal"]))
    o.append(text(360, 530, "data.py：資料清理與檢查", 12.5, C["ink"], "bold"))
    o.append(text(360, 550, "config.py：讀取設定檔", 12.5, C["ink"], "bold"))
    o.append(text(360, 570, "cli.py：build-data／serve／monitor", 12.5, C["ink"], "bold"))

    # 瀏覽器
    o.append(group(720, 120, 200, 300, "③ 瀏覽器展示畫面", C["purple"]))
    for i, s in enumerate(["🎯 推薦", "🍽️ 我的餐盤", "🤖 AI 小教練", "📋 全部菜單", "🧭 怎麼運作", "🟦 虛擬 micro:bit"]):
        o.append(chip(738, 158 + i * 40, 164, s, C["purple"]))

    # 雲端
    o.append(group(720, 440, 200, 150, "④ 雲端（選用）", C["muted"]))
    o.append(box(738, 476, 164, 90, "Claude API", ["理解需求、挑菜解釋", "沒金鑰時改用規則版"], C["muted"]))

    # 資料層
    o.append(group(40, 620, 880, 150, "⑤ 資料與設定（檔案）", C["warn"]))
    o.append(box(60, 656, 190, 92, "data/raw/*.csv", ["學生調查的", "健身表＋養生表"], C["warn"]))
    o.append(box(300, 656, 190, 92, "data/processed/", ["dishes.csv（清理後）", "data_report.md（問題）"], C["warn"]))
    o.append(box(540, 656, 170, 92, "config/scoring.json", ["加權公式", "燈號門檻、預設條件"], C["warn"]))
    o.append(box(730, 656, 170, 92, "hardware.json／.env", ["零件開關、蜂鳴器", "埠號、AI 金鑰"], C["warn"]))
    o.append(arrow(250, 702, 300, 702, None))
    o.append(text(275, 694, "清理", 11, C["muted"], anchor="middle"))

    # 連線
    o.append(arrow(290, 191, 360, 191, "USB", both=True, lx=325, ly=182))
    o.append(text(325, 214, "序列埠", 12, C["ink"], anchor="middle"))
    o.append(arrow(505, 226, 505, 240, None))
    o.append(arrow(505, 310, 505, 324, None))
    o.append(arrow(500, 369, 510, 369, None))
    o.append(arrow(650, 463, 720, 380, None, both=True))
    o.append(text(690, 452, "HTTP", 12, C["ink"], anchor="middle"))
    o.append(text(690, 468, "SSE", 12, C["ink"], anchor="middle"))
    o.append(arrow(650, 463, 738, 520, None, color=C["muted"], dashed=True))
    o.append(arrow(505, 620, 505, 592, None, color=C["muted"]))
    o.append(text(515, 612, "伺服器啟動時讀取（修改後重開 fitwell serve）", 12, C["muted"]))
    return page(960, 800, "系統架構", "micro:bit 只做輸入輸出；資料、計算、AI 都在電腦上；網頁和硬體共用同一份機台狀態", "".join(o))


# ---------------- 2. 推薦流程 ----------------

def fig_flow():
    o = []
    cx = 300
    o.append(pill(cx, 140, 120, "開始"))
    o.append(arrow(cx, 158, cx, 186))
    o.append(box(cx - 150, 186, 300, 56, "選擇模式：健身 或 養生", [], C["blue"]))
    o.append(arrow(cx, 242, cx, 266))
    o.append(box(cx - 150, 266, 300, 56, "用該模式的加權公式幫每道菜計分", [], C["blue"]))
    o.append(arrow(cx, 322, cx, 346))
    o.append(box(cx - 150, 346, 300, 56, "依分數由高到低排序", [], C["blue"]))
    o.append(arrow(cx, 402, cx, 424))
    ys = [462, 552, 642]
    for i, (y, label) in enumerate(zip(ys, ["超出預算？", "超出可接受辣度？", "不符合主餐類型？"])):
        o.append(diamond(cx, y, 230, 76, label))
        if i == 0:
            o.append(arrow(cx + 115, y, cx + 200, y, "是", lx=cx + 158, ly=y - 8))
        else:
            o.append(f'<line x1="{cx + 115}" y1="{y}" x2="{cx + 260}" y2="{y}" stroke="{C["ink"]}" stroke-width="2"/>')
            o.append(text(cx + 158, y - 8, "是", 12, C["ink"], anchor="middle"))
        o.append(arrow(cx, y + 38, cx, y + 52, "否", lx=cx + 16, ly=y + 50, anchor="start"))
    o.append(box(cx + 200, 432, 120, 60, "不加入候選", [], C["red"]))
    o.append(f'<line x1="{cx + 260}" y1="{ys[1]}" x2="{cx + 260}" y2="492" stroke="{C["ink"]}" stroke-width="2" marker-end="url(#ah)"/>')
    o.append(f'<line x1="{cx + 260}" y1="{ys[2]}" x2="{cx + 260}" y2="{ys[1]}" stroke="{C["ink"]}" stroke-width="2"/>')
    o.append(box(cx - 150, 694, 300, 56, "取前 3 名，計算紅黃綠燈號", [], C["green"]))
    o.append(arrow(cx, 750, cx, 774))
    o.append(diamond(cx, 812, 230, 76, "找到 3 道？"))
    o.append(arrow(cx + 115, 812, cx + 200, 812, "否", lx=cx + 158, ly=804))
    o.append(box(cx + 200, 784, 150, 56, "提示放寬哪個條件", [], C["orange"]))
    o.append(arrow(cx, 850, cx, 880, "是", lx=cx + 16, ly=872, anchor="start"))
    o.append(box(cx - 150, 880, 300, 74, "輸出結果", ["網頁卡片＋燈號；micro:bit 亮燈、", "嗶聲、指針轉到健康百分比"], C["purple"]))

    # 右側：公式與門檻
    px = 690
    o.append(group(px, 120, 230, 836, "評分規則（config/scoring.json）", C["blue"]))
    rows = [
        ("健身 v2（預設）", ["油脂×2 + 蛋白質×3", "+ 鹽分×1 + 澱粉×1"]),
        ("健身 v1（學生原版）", ["油脂×2 + 蛋白質×3", "− 鹽分×1 + 澱粉×1"]),
        ("養生 v1", ["油脂 − 辣度 + 鹽分", "+ 澱粉 + 烹調×3"]),
    ]
    y = 156
    for title, lines in rows:
        o.append(box(px + 16, y, 198, 92, title, lines, C["blue"], line_size=12.5))
        y += 108
    o.append(text(px + 16, y + 10, "各項加權（學生標記）", 13, C["ink"], "bold"))
    for i, s in enumerate(["高油 −1／低油 +2／其他 +1", "高蛋白 +3／其他 +1", "高鹽 −1／低鹽 +2／其他 +1",
                           "多澱粉 −3／其他 +1", "辣度 1～5（公式中扣分）", "蒸 +3、煮 +2、炸 −2…"]):
        o.append(text(px + 16, y + 36 + i * 22, s, 12, C["muted"]))
    y += 180
    o.append(text(px + 16, y, "燈號門檻（分數）", 13, C["ink"], "bold"))
    for i, (lab, col, s) in enumerate([("綠", C["green"], "健身 ≥13、養生 ≥8"), ("黃", C["yellow"], "健身 ≥9、養生 ≥4"), ("紅", C["red"], "其餘")]):
        o.append(f'<circle cx="{px + 26}" cy="{y + 24 + i * 26}" r="8" fill="{col}"/>')
        o.append(text(px + 42, y + 29 + i * 26, s, 12, C["muted"]))
    y += 110
    o.append(text(px + 16, y, "健康百分比（指針）", 13, C["ink"], "bold"))
    o.append(text(px + 16, y + 24, "前 3 名平均分在全部菜色", 12, C["muted"]))
    o.append(text(px + 16, y + 44, "分數範圍中的位置 0～100", 12, C["muted"]))
    return page(960, 990, "推薦流程", "依學生流程圖實作（src/fitwell/recommend.py）；預設排除飲料與甜點", "".join(o))


# ---------------- 3. 通訊時序 ----------------

def fig_sequence():
    o = []
    lanes = [("micro:bit", 170, C["green"]), ("電腦 fitwell serve", 480, C["blue"]), ("瀏覽器", 790, C["purple"])]
    top, bottom = 130, 960
    for name, x, col in lanes:
        o.append(f'<rect x="{x - 90}" y="{top}" width="180" height="40" rx="10" fill="{col}"/>')
        o.append(text(x, top + 26, name, 14, "#ffffff", "bold", "middle"))
        o.append(f'<line x1="{x}" y1="{top + 40}" x2="{x}" y2="{bottom}" stroke="{C["line"]}" stroke-width="2" stroke-dasharray="5 5"/>')
    M, S, B = 170, 480, 790

    def msg(y, a, b, label, dashed=False):
        return arrow(a, y, b, y, label, color=C["muted"] if dashed else None, dashed=dashed, ly=y - 8)

    def phase(y, label):
        return (f'<rect x="40" y="{y - 18}" width="880" height="28" rx="8" fill="{C["bg"]}"/>'
                + text(56, y + 1, label, 13, C["ink"], "bold"))

    def note(x, y, w, label):
        return (f'<rect x="{x - w / 2}" y="{y - 16}" width="{w}" height="28" rx="8" fill="#fff7ec" stroke="#f3c98b"/>'
                + text(x, y + 3, label, 12, C["ink"], anchor="middle"))

    y = 210
    o.append(phase(y, "① 連線與設定")); y += 40
    o.append(msg(y, S, M, "HELLO?（每 3 秒，直到有回應）")); y += 44
    o.append(msg(y, M, S, "HELLO:3.0、MODE:FITNESS")); y += 44
    o.append(arrow(S, y + 8, M, y + 8, "CFG 設定 × 5 行（config/hardware.json）\n旋鈕開關、蜂鳴器種類與長度、指針方向", ly=y - 26)); y += 44
    o.append(note(S - 155, y, 300, "之後每 15 秒重送一次 CFG")); y += 50
    o.append(phase(y, "② 調整條件（轉旋鈕／按 A）")); y += 40
    o.append(msg(y, M, S, "BUDGET:1、SPICY:ANY、MODE:WELLNESS")); y += 44
    o.append(msg(y, S, B, "SSE：state（網頁同步切換）")); y += 54
    o.append(phase(y, "③ 推薦（按健身鈕；網頁按鈕也走同一條路）")); y += 40
    o.append(msg(y, M, S, "GO:FITNESS")); y += 36
    o.append(note(S, y, 240, "推薦引擎：過濾 → 排序 → 前 3 名")); y += 44
    o.append(msg(y, S, B, "SSE：result（卡片、燈號、流程）")); y += 44
    o.append(msg(y, S, M, "SCORE:92 → LIGHT:GREEN → SHOW:3")); y += 36
    o.append(note(M + 10, y, 280, "亮綠燈 → 嗶 → 指針轉到 92%")); y += 54
    o.append(phase(y, "④ 例外處理")); y += 40
    o.append(msg(y, M, S, "Traceback／MemoryError（程式當掉）", dashed=True)); y += 44
    o.append(msg(y, S, M, "Ctrl+C、Ctrl+D（自動軟重開）→ 回到 ①", dashed=True)); y += 44
    o.append(note(M + 10, y, 300, "3 秒沒收到 LIGHT → 點陣顯示 😕"))
    return page(960, 990, "通訊時序", "USB 序列埠 115200 baud，一行一個指令；網頁上的虛擬 micro:bit 走同一套指令", "".join(o))


# ---------------- 4. 資料管線 ----------------

def fig_data():
    o = []
    o.append(box(40, 150, 200, 110, "健身表 CSV", ["menu_fitness.csv", "油脂／蛋白質／", "鹽分／澱粉加權"], C["warn"]))
    o.append(box(40, 290, 200, 110, "養生表 CSV", ["menu_wellness.csv", "辣度／烹調加權、", "烹調方法、辣度"], C["warn"]))
    o.append(box(300, 150, 300, 250, "fitwell build-data（data.py）", [
        "1. 兩表逐列合併（同一批 231 道）",
        "2. 餐廳名稱統一、去除隱形字元",
        "3. 營養加權取健身表、辣度與烹調",
        "    取養生表（較完整的一方）",
        "4. 重新計算總分（不用表單總加權）",
        "5. 標記重複菜色（推薦時略過）",
        "6. 檢查標籤與加權是否一致",
    ], C["blue"], line_size=12.5))
    o.append(arrow(240, 205, 300, 240))
    o.append(arrow(240, 345, 300, 310))
    o.append(box(660, 290, 260, 110, "dishes.csv", ["224 道可推薦（231 − 7 重複）", "中文表頭，Excel 可直接打開"], C["green"]))
    o.append(box(660, 150, 260, 110, "data_report.md", ["自動產生的問題清單", "給學生修正原始表單"], C["orange"]))
    o.append(arrow(600, 240, 660, 205))
    o.append(arrow(600, 310, 660, 345))
    o.append(box(300, 450, 300, 110, "評分與推薦（執行時）", ["scoring.py 依公式計分", "recommend.py 過濾、排序、燈號"], C["green"]))
    o.append(box(660, 450, 260, 110, "config/scoring.json", ["公式（v1／v2／養生）", "燈號門檻、預設條件"], C["blue"]))
    o.append(arrow(700, 400, 560, 450, "讀取", color=C["muted"], lx=655, ly=440, anchor="start"))
    o.append(arrow(660, 505, 600, 505))
    o.append(box(40, 450, 200, 110, "更新資料", ["改原始表單 → 匯出 CSV", "→ build-data", "（或網頁後台重建）"], C["muted"]))
    o.append(arrow(140, 450, 140, 400, None, color=C["muted"], dashed=True))
    return page(960, 600, "資料管線", "學生調查的兩份 Google 表單 → 清理合併 → 推薦引擎使用的 dishes.csv", "".join(o))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fn in {
        "system.svg": fig_system,
        "recommend_flow.svg": fig_flow,
        "sequence.svg": fig_sequence,
        "data_pipeline.svg": fig_data,
    }.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
        print("✅", OUT / name)


if __name__ == "__main__":
    main()
