"""產生接線圖 SVG（docs/images/wiring/*.svg）。

    uv run python scripts/gen_wiring.py

每張圖：左邊是 micro:bit 擴充板的腳位，右邊是零件，中間用彩色線連起來。
改腳位或零件時改這支程式再重新產生，不要手改 SVG。
"""

from __future__ import annotations

from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "docs" / "images" / "wiring"
FONT = "'PingFang TC','Noto Sans TC','Microsoft JhengHei',sans-serif"

C = {
    "ink": "#1f2a24",
    "muted": "#6b746e",
    "line": "#e3dfd6",
    "card": "#ffffff",
    "bg": "#f6f4ef",
    "pcb": "#1f5f46",
    "pcb2": "#2b7a5b",
    "gold": "#e8b64c",
    "gnd": "#2b2b2b",
    "v3": "#d6402f",
    "green": "#22b35e",
    "yellow": "#f2b705",
    "red": "#e5483b",
    "blue": "#2f6fdf",
    "purple": "#8b5cf6",
    "orange": "#f08c1a",
    "brown": "#7a4a22",
    "teal": "#0f9b8e",
    "pink": "#e0457b",
    "warn": "#c2410c",
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=15, color=None, weight="normal", anchor="start"):
    return (
        f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{color or C["ink"]}" '
        f'font-weight="{weight}" text-anchor="{anchor}">{esc(s)}</text>'
    )


def wire(x1, y1, x2, y2, color, bend=0.5):
    """平滑的 S 形導線（外框深色、內層彩色，看起來像真的杜邦線）。"""
    dx = (x2 - x1) * bend
    d = f"M{x1},{y1} C{x1 + dx},{y1} {x2 - dx},{y2} {x2},{y2}"
    return (
        f'<path d="{d}" fill="none" stroke="#00000033" stroke-width="8" stroke-linecap="round"/>'
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>'
    )


def poly(points, color):
    """直角導線（給 GND 匯流排等需要整齊的地方）。"""
    d = "M" + " L".join(f"{x},{y}" for x, y in points)
    return (
        f'<path d="{d}" fill="none" stroke="#00000033" stroke-width="8" stroke-linejoin="round" stroke-linecap="round"/>'
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="5" stroke-linejoin="round" stroke-linecap="round"/>'
    )


def dot(x, y, color=C["gold"]):
    return f'<circle cx="{x}" cy="{y}" r="6" fill="{color}" stroke="#7a5a12" stroke-width="1.5"/>'


# ---------------- 擴充板 ----------------

def board(x, y, pins, title="micro:bit 擴充板", row=46):
    """pins: [(名稱, 說明, 顏色或 None)]。回傳 (svg, {名稱: (x, y)})。"""
    h = 70 + row * len(pins)
    w = 230
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{C["pcb"]}"/>',
        f'<rect x="{x + 8}" y="{y + 8}" width="{w - 16}" height="{h - 16}" rx="11" fill="none" stroke="{C["pcb2"]}" stroke-width="2"/>',
        text(x + 22, y + 38, title, 16, "#ffffff", "bold"),
    ]
    anchors = {}
    for i, (name, note, color) in enumerate(pins):
        py = y + 70 + i * row
        px = x + w - 4
        tag_color = color or "#3d8b6d"
        out.append(f'<rect x="{x + 18}" y="{py - 17}" width="58" height="30" rx="8" fill="{tag_color}"/>')
        out.append(text(x + 47, py + 4, name, 15, "#ffffff", "bold", "middle"))
        out.append(text(x + 86, py + 5, note, 13, "#d9efe5"))
        out.append(dot(px, py))
        anchors[name] = (px, py)
    return "".join(out), anchors


# ---------------- 零件 ----------------

BANDS = {"220": ["#d6402f", "#d6402f", "#7a4a22", "#c9a227"], "100": ["#7a4a22", "#1f1f1f", "#7a4a22", "#c9a227"],
         "10k": ["#7a4a22", "#1f1f1f", "#f08c1a", "#c9a227"]}


def resistor(x, y, value="220", label=None):
    """水平電阻，左端 (x, y)，右端 (x+110, y)。"""
    out = [f'<line x1="{x}" y1="{y}" x2="{x + 110}" y2="{y}" stroke="#9aa0a6" stroke-width="3"/>',
           f'<rect x="{x + 25}" y="{y - 12}" width="60" height="24" rx="11" fill="#e9d3a7" stroke="#b9975b" stroke-width="1.5"/>']
    for i, col in enumerate(BANDS[value]):
        bx = x + 35 + i * 11 + (6 if i == 3 else 0)
        out.append(f'<rect x="{bx}" y="{y - 12}" width="6" height="24" fill="{col}"/>')
    out.append(text(x + 55, y - 20, label or f"{value}Ω", 13, C["muted"], anchor="middle"))
    return "".join(out), (x, y), (x + 110, y)


def led(x, y, color, name):
    """水平 LED 符號（三角形＋橫線），左邊 + 長腳、右邊 − 短腳。左端 (x, y)、右端 (x+120, y)。"""
    cx = x + 60
    out = [
        f'<circle cx="{cx}" cy="{y}" r="30" fill="{color}" opacity="0.16"/>',
        f'<line x1="{x}" y1="{y}" x2="{cx - 16}" y2="{y}" stroke="#9aa0a6" stroke-width="3"/>',
        f'<line x1="{cx + 14}" y1="{y}" x2="{x + 120}" y2="{y}" stroke="#9aa0a6" stroke-width="3"/>',
        f'<path d="M{cx - 16},{y - 15} L{cx + 12},{y} L{cx - 16},{y + 15} Z" fill="{color}" stroke="#00000055" stroke-width="1.5"/>',
        f'<rect x="{cx + 12}" y="{y - 16}" width="4" height="32" fill="{C["ink"]}"/>',
        f'<path d="M{cx + 2},{y - 20} l9,-10 M{cx + 9},{y - 22} l9,-10" stroke="{color}" stroke-width="2.5" stroke-linecap="round"/>',
        text(x + 4, y + 22, "+ 長腳", 12, C["muted"]),
        text(x + 116, y + 22, "− 短腳", 12, C["muted"], anchor="end"),
        text(cx, y + 46, name, 14, C["ink"], "bold", "middle"),
    ]
    return "".join(out), (x, y), (x + 120, y)


def button(x, y, label):
    """2 腳按鈕，左腳 (x, y)、右腳 (x+110, y)。"""
    cx = x + 55
    out = [
        f'<line x1="{x}" y1="{y}" x2="{x + 110}" y2="{y}" stroke="#9aa0a6" stroke-width="3"/>',
        f'<rect x="{cx - 26}" y="{y - 26}" width="52" height="52" rx="6" fill="#2d2f33"/>',
        f'<circle cx="{cx}" cy="{y}" r="17" fill="{C["blue"]}" stroke="#ffffff55" stroke-width="2"/>',
        text(cx, y + 46, label, 14, C["ink"], "bold", "middle"),
    ]
    return "".join(out), (x, y), (x + 110, y)


def gnd_rail(x, y1, y2):
    return (
        f'<rect x="{x - 9}" y="{y1}" width="18" height="{y2 - y1}" rx="9" fill="#dfe7f5" stroke="{C["blue"]}" stroke-width="2"/>'
        + text(x, y1 - 12, "GND（−）", 14, C["blue"], "bold", "middle")
    )


def note_box(x, y, w, lines, title="注意"):
    h = 44 + 26 * len(lines)
    out = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="#fff7ec" stroke="#f3c98b" stroke-width="1.5"/>',
        text(x + 20, y + 30, title, 15, C["warn"], "bold"),
    ]
    for i, s in enumerate(lines):
        out.append(text(x + 20, y + 58 + i * 26, s, 14, C["ink"]))
    return "".join(out), h


def page(w, h, title, subtitle, body):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {w} {h}">'
        f'<rect width="{w}" height="{h}" rx="22" fill="{C["bg"]}"/>'
        f'<rect x="16" y="16" width="{w - 32}" height="{h - 32}" rx="18" fill="{C["card"]}" stroke="{C["line"]}"/>'
        + text(44, 62, title, 24, C["ink"], "bold")
        + text(44, 90, subtitle, 15, C["muted"])
        + body
        + "</svg>"
    )


# ---------------- 各張圖 ----------------

def fig_base():
    b, a = board(44, 120, [("P0", "綠燈", C["green"]), ("P1", "黃燈", "#c99700"), ("P2", "紅燈", C["red"]),
                           ("3V", "不要接！", "#9b9b9b"), ("GND", "接地", C["gnd"])])
    out = [b]
    rail_x = 900
    rows = [("P0", C["green"], "綠 LED", 190), ("P1", C["yellow"], "黃 LED", 290), ("P2", C["red"], "紅 LED", 390)]
    for pin, col, name, y in rows:
        r, rl, rr = resistor(380, y)
        l, ll, lr = led(560, y, col, name)
        px, py = a[pin]
        out += [wire(px, py, rl[0], rl[1], col), r, wire(rr[0], rr[1], ll[0], ll[1], col, 0.3), l,
                poly([(lr[0], lr[1]), (rail_x, lr[1])], C["gnd"])]
    gx, gy = a["GND"]
    out.append(poly([(gx, gy), (gx + 40, gy), (gx + 40, 460), (rail_x, 460)], C["gnd"]))
    out.append(gnd_rail(rail_x, 160, 472))
    # 3V 打叉
    vx, vy = a["3V"]
    out.append(f'<path d="M{vx + 18},{vy - 10} l20,20 M{vx + 38},{vy - 10} l-20,20" stroke="{C["warn"]}" stroke-width="4" stroke-linecap="round"/>')
    n, _ = note_box(44, 500, 872, [
        "① 三顆燈的電阻接 P0、P1、P2，不可以接 3V（3V 一直有電，燈會一直亮、程式控制不了）。",
        "② LED 長腳（+）接電阻，短腳（−）接 GND；LED 邊緣切平的那一側是短腳。",
        "③ 電阻：220Ω（紅紅棕）或套件的 100Ω（棕黑棕）都可以；不要用 10kΩ（棕黑橙），燈會幾乎不亮。",
        "④ 這是「基本電路」：只接這三顆燈，micro:bit 程式就能完整運作。",
    ], "接線重點")
    out.append(n)
    return page(960, 500 + 168, "① 基本電路：紅黃綠三顆燈", "必接 · 用到 P0、P1、P2、GND", "".join(out))


def fig_buttons():
    b, a = board(44, 120, [("P13", "健身", C["blue"]), ("P14", "養生", C["teal"]), ("GND", "接地", C["gnd"])])
    out = [b]
    rail_x = 860
    for pin, col, name, y in [("P13", C["blue"], "💪 健身按鈕", 190), ("P14", C["teal"], "🍵 養生按鈕", 300)]:
        bt, bl, br = button(520, y, name)
        px, py = a[pin]
        out += [wire(px, py, bl[0], bl[1], col), bt, poly([(br[0], br[1]), (rail_x, br[1])], C["gnd"])]
    gx, gy = a["GND"]
    out.append(poly([(gx, gy), (gx + 40, gy), (gx + 40, 380), (rail_x, 380)], C["gnd"]))
    out.append(gnd_rail(rail_x, 160, 392))
    n, _ = note_box(44, 430, 872, [
        "① 按鈕一腳接腳位、另一腳接 GND，不用電阻（程式會開啟內部上拉）。",
        "② 2 腳按鈕：兩腳各接一邊。4 腳按鈕：跨在麵包板中間凹槽上，取「對角線」的兩隻腳。",
        "③ 按下「健身」＝ 切到健身並立刻推薦；「養生」同理。沒接按鈕程式也照常運作。",
    ], "接線重點")
    out.append(n)
    return page(960, 430 + 142, "② 加分：健身／養生實體按鈕", "選用 · P13、P14、GND", "".join(out))


def fig_servo():
    b, a = board(44, 120, [("P12", "訊號", C["orange"]), ("GND", "接地", C["gnd"])])
    out = [b]
    py_sig, py_gnd = a["P12"][1], a["GND"][1]
    ys = {"sig": py_sig - 14, "pwr": py_sig + 16, "gnd": py_gnd}
    cx = 560  # 3 pin 接頭
    sx, sy = 640, 140  # 伺服馬達本體
    out += [
        f'<rect x="{sx}" y="{sy}" width="150" height="120" rx="12" fill="{C["blue"]}"/>',
        f'<rect x="{sx + 40}" y="{sy - 20}" width="56" height="24" rx="6" fill="{C["blue"]}"/>',
        f'<circle cx="{sx + 68}" cy="{sy - 20}" r="12" fill="#ffffff"/>',
        f'<rect x="{sx + 60}" y="{sy - 36}" width="90" height="12" rx="6" fill="#ffffff" stroke="#c9d6f2"/>',
        text(sx + 75, sy + 66, "SG90", 18, "#ffffff", "bold", "middle"),
        text(sx + 75, sy + 90, "伺服馬達", 13, "#dbe6ff", anchor="middle"),
        f'<rect x="{cx - 6}" y="{ys["sig"] - 16}" width="22" height="{ys["gnd"] - ys["sig"] + 32}" rx="5" fill="#2d2f33"/>',
    ]
    for key, col in (("sig", C["orange"]), ("pwr", C["v3"]), ("gnd", C["brown"])):
        out.append(f'<line x1="{cx + 16}" y1="{ys[key]}" x2="{sx}" y2="{ys[key]}" stroke="{col}" stroke-width="6"/>')
        out.append(dot(cx + 5, ys[key]))
    # 線色說明
    lx = 812
    for i, (col, lab, to) in enumerate([(C["orange"], "橘線 訊號", "→ P12"), (C["v3"], "紅線 電源 +", "→ 電池 +"), (C["brown"], "棕線 GND", "→ GND")]):
        y = sy + 10 + i * 40
        out.append(f'<rect x="{lx}" y="{y}" width="14" height="14" rx="3" fill="{col}"/>')
        out.append(text(lx + 22, y + 12, lab, 13, C["ink"], "bold"))
        out.append(text(lx + 22, y + 30, to, 12, C["muted"]))
    # 電池盒
    bx, by = 600, 330
    out += [
        f'<rect x="{bx}" y="{by}" width="170" height="70" rx="10" fill="#2d2f33"/>',
        f'<rect x="{bx + 12}" y="{by + 14}" width="66" height="42" rx="8" fill="{C["gold"]}"/>',
        f'<rect x="{bx + 92}" y="{by + 14}" width="66" height="42" rx="8" fill="{C["gold"]}"/>',
        text(bx + 45, by + 41, "AA", 14, C["ink"], "bold", "middle"),
        text(bx + 125, by + 41, "AA", 14, C["ink"], "bold", "middle"),
        text(bx + 85, by + 92, "2 顆 AA 電池盒（3V）", 14, C["ink"], "bold", "middle"),
        text(bx + 184, by + 22, "+", 20, C["v3"], "bold"),
        text(bx - 14, by + 50, "−", 20, C["gnd"], "bold", "end"),
    ]
    px, py = a["P12"]
    out.append(wire(px, py, cx + 5, ys["sig"], C["orange"]))
    gx, gy = a["GND"]
    jx = 520
    out.append(poly([(gx, gy), (cx + 5, gy)], C["gnd"]))
    out.append(poly([(bx, by + 45), (jx, by + 45), (jx, gy)], C["gnd"]))
    out.append(f'<circle cx="{jx}" cy="{gy}" r="7" fill="{C["gnd"]}"/>')
    # 電池 + → 紅線（白色描邊表示從黑線上方跨過）
    red = [(bx + 170, by + 16), (bx + 210, by + 16), (bx + 210, 300), (540, 300), (540, ys["pwr"]), (cx + 5, ys["pwr"])]
    d = "M" + " L".join(f"{x},{y}" for x, y in red)
    out.append(f'<path d="{d}" fill="none" stroke="#ffffff" stroke-width="13" stroke-linejoin="round"/>')
    out.append(poly(red, C["v3"]))
    n, _ = note_box(44, 450, 872, [
        "① 橘線（訊號）接 P12；棕線（GND）、電池盒 − 和 micro:bit 的 GND 要接在一起（共地）。",
        "② 紅線（電源 +）接電池盒 +。不要接 3V 或 IOBIT 的 5V（啟動電流大，會讓 micro:bit 重開或 IOBIT 斷電）。",
        "③ 推薦結果越健康，指針越往右（綠色區）；方向相反時把 config/hardware.json 的 servo_reverse 改成 true。",
        "④ 開機時指針會轉到正中間（90°），用來對齊紙板刻度；按推薦時先歸零再轉到結果。",
    ], "接線重點")
    out.append(n)
    return page(960, 450 + 168, "③ 加分：健康指針（伺服馬達）", "選用 · P12、GND、外接電池", "".join(out))


def fig_ring():
    b, a = board(44, 120, [("P8", "資料", C["purple"]), ("3V", "電源", C["v3"]), ("GND", "接地", C["gnd"])])
    out = [b]
    cx, cy, r = 820, 200, 72
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r + 22}" fill="#2d2f33"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{r - 22}" fill="{C["card"]}"/>')
    import math
    rainbow = ["#e5483b", "#f08c1a", "#f2b705", "#22b35e", "#0f9b8e", "#2f6fdf", "#8b5cf6", "#e0457b"]
    for i, col in enumerate(rainbow):
        ang = -math.pi / 2 + i * 2 * math.pi / 8
        x, y = cx + r * math.cos(ang), cy + r * math.sin(ang)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="15" fill="{col}" opacity="0.25"/>')
        out.append(f'<rect x="{x - 9:.1f}" y="{y - 9:.1f}" width="18" height="18" rx="3" fill="#fafafa"/>')
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{col}"/>')
    out.append(text(cx, cy + 6, "WS2812", 15, C["ink"], "bold", "middle"))
    out.append(text(cx, cy + 26, "8 燈", 13, C["muted"], anchor="middle"))
    pads = [("DIN", "P8", C["purple"], 300), ("VCC（4-7VDC / 5V）", "3V", C["v3"], 350), ("GND", "GND", C["gnd"], 400)]
    for lab, pin, col, y in pads:
        px, py = a[pin]
        out.append(f'<rect x="490" y="{y - 13}" width="22" height="26" rx="4" fill="{C["gold"]}"/>')
        out.append(text(522, y + 5, lab, 14, C["ink"], "bold"))
        out.append(wire(px, py, 490, y, col))
    out.append(f'<rect x="480" y="268" width="250" height="150" rx="12" fill="none" stroke="#9aa0a6" stroke-dasharray="6 5"/>')
    out.append(text(490, 262, "燈環背面的 3 個焊點", 13, C["muted"]))
    n, _ = note_box(44, 450, 872, [
        "① 燈環背面有 DIN、VCC（或 5V）、GND 焊點；DIN（IN／DI）接 P8，DOUT 不要接；箭頭從 IN 指向 OUT。",
        "② VCC 先接 3V；不亮再改接 5V（IOBIT 要另外插 USB 並按電源鈕）。5V 時可在 VCC 串 1N4007 二極體。",
        "③ 等待推薦時燈環會轉圈；結果出來後，亮幾顆＝多健康，顏色＝紅黃綠燈號。",
    ], "接線重點")
    out.append(n)
    return page(960, 450 + 142, "④ 加分：健康量表燈環（WS2812）", "選用 · P8、3V、GND", "".join(out))


def fig_buzzer():
    b, a = board(44, 120, [("P16", "聲音", C["pink"]), ("GND", "接地", C["gnd"])])
    out = [b]
    cx, cy = 600, 190
    out += [
        f'<circle cx="{cx}" cy="{cy}" r="44" fill="#2d2f33"/>',
        f'<circle cx="{cx}" cy="{cy}" r="8" fill="#111"/>',
        text(cx + 30, cy - 30, "+", 22, C["v3"], "bold"),
        text(cx + 56, cy + 6, "蜂鳴器", 15, C["ink"], "bold"),
        f'<line x1="{cx - 14}" y1="{cy + 40}" x2="{cx - 14}" y2="{cy + 100}" stroke="#9aa0a6" stroke-width="3"/>',
        f'<line x1="{cx + 14}" y1="{cy + 40}" x2="{cx + 14}" y2="{cy + 100}" stroke="#9aa0a6" stroke-width="3"/>',
        text(cx - 20, cy + 118, "+ 長腳", 12, C["muted"], anchor="end"),
        text(cx + 20, cy + 118, "− 短腳", 12, C["muted"]),
    ]
    px, py = a["P16"]
    out.append(wire(px, py, cx - 14, cy + 100, C["pink"], 0.6))
    gx, gy = a["GND"]
    out.append(poly([(gx, gy), (gx + 34, gy), (gx + 34, cy + 150), (cx + 14, cy + 150), (cx + 14, cy + 100)], C["gnd"]))
    # 種類對照
    tx = 740
    out += [
        f'<rect x="{tx - 10}" y="130" width="170" height="150" rx="12" fill="#f3f6fb" stroke="#d6e0f0"/>',
        text(tx, 156, "怎麼分辨？", 14, C["blue"], "bold"),
        text(tx, 182, "無源（類比）：", 13, C["ink"], "bold"),
        text(tx, 202, "底部看得到電路板", 12, C["muted"]),
        text(tx, 222, "buzzer: \"passive\"", 12, C["ink"]),
        text(tx, 248, "有源（數位）：", 13, C["ink"], "bold"),
        text(tx, 268, "底部封黑膠、接 3V 會叫", 12, C["muted"]),
    ]
    n, _ = note_box(44, 410, 872, [
        "① 蜂鳴器 + 接 P16、− 接 GND。程式已把聲音改從 P16 輸出，P0 的綠燈不會跟著閃。",
        "② 無源（類比）蜂鳴器：能發出不同音高（建議）。有源（數位）蜂鳴器：只會「嗶」，要把",
        "    config/hardware.json 的 buzzer 改成 \"active\"。不確定時先用 \"passive\"，怪怪的再改。",
        "③ micro:bit V2 本身有喇叭，不接蜂鳴器也有聲音；V1 一定要外接才有聲音。",
    ], "接線重點")
    out.append(n)
    return page(960, 410 + 168, "⑤ 加分：音效（蜂鳴器）", "選用 · P16、GND", "".join(out))


def fig_knob(pin="P4", what="預算", key="use_budget_knob", zones="1～4 段＋A（不限）", num="⑥"):
    b, a = board(44, 120, [("3V", "電源", C["v3"]), (pin, f"讀{what}", C["teal"]), ("GND", "接地", C["gnd"])])
    out = [b]
    kx = 700
    ys = [a["3V"][1], a[pin][1], a["GND"][1]]
    out += [
        f'<rect x="{kx}" y="{ys[0] - 40}" width="150" height="{ys[2] - ys[0] + 80}" rx="14" fill="{C["blue"]}"/>',
        f'<circle cx="{kx + 80}" cy="{ys[1]}" r="38" fill="#e8ecf2" stroke="#ffffff" stroke-width="3"/>',
        f'<rect x="{kx + 77}" y="{ys[1] - 34}" width="6" height="30" rx="3" fill="{C["ink"]}"/>',
        text(kx + 75, ys[2] + 70, "10K 可變電阻（3 腳）", 14, C["ink"], "bold", "middle"),
    ]
    for lab, y in zip(["腳 1", "腳 2（中間）", "腳 3"], ys):
        out.append(f'<line x1="{kx - 30}" y1="{y}" x2="{kx}" y2="{y}" stroke="#9aa0a6" stroke-width="3"/>')
        out.append(text(kx - 36, y - 10, lab, 12, C["muted"], anchor="end"))
    out.append(poly([a["3V"], (kx - 30, ys[0])], C["v3"]))
    out.append(poly([a["GND"], (kx - 30, ys[2])], C["gnd"]))
    r, rl, rr = resistor(420, ys[1], "10k", "10kΩ 保護電阻（必接）")
    out.append(poly([a[pin], rl], C["teal"]))
    out.append(r)
    out.append(poly([rr, (kx - 30, ys[1])], C["teal"]))
    n, _ = note_box(44, 420, 872, [
        f"① 中間腳要先串一顆 10kΩ（棕黑橙）再接 {pin}。{pin} 同時是點陣的腳位，不串電阻可能傷到 micro:bit。",
        "② 旁邊兩腳分別接 3V 和 GND（順序相反只是旋轉方向相反）。",
        f"③ 接好後要把 config/hardware.json 的 {key} 改成 true，旋鈕才會作用；沒接卻打開，數值會亂跳。",
        f"④ 轉旋鈕選{what}：{zones}；讀旋鈕時點陣會極短暫熄滅一下，是正常的。",
    ], "接線重點")
    out.append(n)
    return page(960, 420 + 168, f"{num} 加分：{what}旋鈕（可變電阻）", f"選用 · {pin}、3V、GND，需要 10kΩ 電阻", "".join(out))


def fig_spicy_knob():
    return fig_knob("P10", "辣度", "use_spicy_knob", "0 不辣、1～5、A（都可以）", "⑦")


def fig_overview():
    b, a = board(340, 110, [
        ("P0", "綠燈", C["green"]), ("P1", "黃燈", "#c99700"), ("P2", "紅燈", C["red"]),
        ("P13", "健身鈕", C["blue"]), ("P14", "養生鈕", C["teal"]), ("P12", "指針", C["orange"]),
        ("P16", "蜂鳴器", C["pink"]), ("P4", "預算鈕", C["teal"]), ("P10", "辣度鈕", C["purple"]),
        ("3V", "電源", C["v3"]), ("GND", "接地", C["gnd"]),
    ], "micro:bit 擴充板", row=56)
    out = [b]

    def chip(x, y, w, title, sub, col, tag):
        return (
            f'<rect x="{x}" y="{y - 23}" width="{w}" height="46" rx="12" fill="{C["card"]}" stroke="{col}" stroke-width="2.5"/>'
            f'<rect x="{x}" y="{y - 23}" width="10" height="46" rx="5" fill="{col}"/>'
            + text(x + 22, y - 3, title, 15, C["ink"], "bold")
            + text(x + 22, y + 15, sub, 12, C["muted"])
            + f'<rect x="{x + w - 54}" y="{y - 18}" width="44" height="22" rx="11" fill="{"#e6f6ec" if tag == "必接" else "#f1ecfe"}"/>'
            + text(x + w - 32, y - 2, tag, 12, C["green"] if tag == "必接" else C["purple"], "bold", "middle")
        )

    items = [
        ("P0", "綠 LED ＋ 電阻", "→ GND", C["green"], "必接"),
        ("P1", "黃 LED ＋ 電阻", "→ GND", C["yellow"], "必接"),
        ("P2", "紅 LED ＋ 電阻", "→ GND", C["red"], "必接"),
        ("P13", "健身按鈕", "另一腳 → GND", C["blue"], "選用"),
        ("P14", "養生按鈕", "另一腳 → GND", C["teal"], "選用"),
        ("P12", "SG90 伺服馬達（橘線）", "紅線 → 電池 +、棕線 → GND", C["orange"], "選用"),
        ("P16", "蜂鳴器 +", "− → GND", C["pink"], "選用"),
        ("P4", "預算旋鈕中間腳（串 10kΩ）", "兩側 → 3V、GND；開 use_budget_knob", C["teal"], "選用"),
        ("P10", "辣度旋鈕中間腳（串 10kΩ）", "兩側 → 3V、GND；開 use_spicy_knob", C["purple"], "選用"),
    ]
    for pin, title, sub, col, tag in items:
        px, py = a[pin]
        out.append(wire(px, py, 640, py, col, 0.5))
        out.append(chip(640, py, 280, title, sub, col, tag))
    # 左側：說明
    out += [
        text(44, 150, "只接「必接」三顆燈", 17, C["ink"], "bold"),
        text(44, 176, "就能完整運作。", 17, C["ink"], "bold"),
        text(44, 214, "「選用」零件想加哪個", 14, C["muted"]),
        text(44, 236, "就接哪個，沒接的程式", 14, C["muted"]),
        text(44, 258, "會自動略過。", 14, C["muted"]),
        text(44, 300, "只有兩個旋鈕要在", 14, C["muted"]),
        text(44, 322, "hardware.json 打開。", 14, C["ink"], "bold"),
        text(44, 364, "所有零件的 GND", 14, C["muted"]),
        text(44, 386, "都接到同一條 GND。", 14, C["muted"]),
        text(44, 428, "⚠️ 3V 只給旋鈕當電源，", 14, C["warn"], "bold"),
        text(44, 450, "LED 不能接 3V。", 14, C["warn"], "bold"),
    ]
    h = 110 + 70 + 56 * 11 + 40
    return page(960, h, "總覽：腳位配置", "micro:bit V1、V2 通用 · 韌體 v3.0", "".join(out))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    figs = {
        "00_overview.svg": fig_overview,
        "01_base_leds.svg": fig_base,
        "02_buttons.svg": fig_buttons,
        "03_servo.svg": fig_servo,
        "05_buzzer.svg": fig_buzzer,
        "06_budget_knob.svg": fig_knob,
        "07_spicy_knob.svg": fig_spicy_knob,
    }
    for name, fn in figs.items():
        (OUT / name).write_text(fn(), encoding="utf-8")
        print("✅", OUT / name)


if __name__ == "__main__":
    main()
