"""網頁伺服器：提供 API、展示畫面，並串接 micro:bit。

啟動：  uv run fitwell serve        （預設 http://localhost:8000）
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import REPORT_MD, WEB_DIR, __version__
from .ai_coach import ai_available, coach
from .config import hardware_commands, load_config, load_hardware
from .data import build, load_dishes, write_csv, write_report
from .recommend import MODES, Query, Recommender
from .serial_bridge import SerialBridge, webusb_holders

log = logging.getLogger("fitwell.server")


# ---------------- 機台狀態 ----------------

@dataclass
class KioskState:
    mode: str = "fitness"
    budget: str | None = None
    max_spicy: int | None = None
    main_types: list[str] = field(default_factory=list)
    restaurants: list[str] = field(default_factory=list)
    formula_fitness: str | None = None
    formula_wellness: str | None = None

    def query(self) -> Query:
        return Query(
            mode=self.mode,
            budget=self.budget,
            max_spicy=self.max_spicy,
            main_types=list(self.main_types),
            restaurants=list(self.restaurants),
            formula=self.formula_fitness if self.mode == "fitness" else self.formula_wellness,
        )


class App:
    def __init__(self) -> None:
        self.lock = threading.RLock()
        self.reload()
        d = self.config["defaults"]
        self.state = KioskState(budget=d["budget"], max_spicy=d["max_spicy"], main_types=list(d["main_types"]))
        self.last_result: dict[str, Any] | None = None
        self.subscribers: set[asyncio.Queue] = set()
        self.loop: asyncio.AbstractEventLoop | None = None
        self.bridge = SerialBridge(self.on_microbit_line, port=os.environ.get("FITWELL_SERIAL_PORT") or None)

    def reload(self) -> None:
        with self.lock:
            self.config = load_config()
            self.hardware = load_hardware()
            self.dishes = load_dishes()
            self.rec = Recommender(self.dishes, self.config)

    # ----- 事件廣播（Server-Sent Events） -----

    def publish(self, kind: str, data: Any) -> None:
        msg = json.dumps({"type": kind, "data": data}, ensure_ascii=False)
        if self.loop is None:
            return
        for q in list(self.subscribers):
            self.loop.call_soon_threadsafe(q.put_nowait, msg)

    def status(self) -> dict[str, Any]:
        return {
            "microbit": {
                "connected": self.bridge.connected,
                "responding": self.bridge.responding,
                "port": self.bridge.port,
                "rx": self.bridge.rx_count,
                "tx": self.bridge.tx_count,
                "crashes": self.bridge.crashes,
                # 連上但沒回應時，查是不是被瀏覽器的 WebUSB 佔住（網頁會提示要關哪個程式）
                "webusb": webusb_holders() if self.bridge.connected and not self.bridge.responding else [],
            },
            "ai": ai_available(),
            "hardware": self.hardware,
            "state": self.state.__dict__,
        }

    # ----- 推薦並同步硬體 -----

    def run_recommend(self, q: Query, source: str) -> dict[str, Any]:
        with self.lock:
            result = self.rec.recommend(q).to_dict()
        result["source"] = source
        self.last_result = result
        self.send_light(result["light"], len(result["items"]), result["percent"])
        self.publish("result", result)
        return result

    def send_hardware_config(self) -> None:
        """把 config/hardware.json 的設定送給 micro:bit（每次握手都送，改設定不用重新燒錄）。"""
        for line in hardware_commands(self.hardware):
            self.bridge.send(line)

    def send_light(self, light: str, count: int | None = None, percent: int | None = None) -> None:
        if percent is not None:
            self.bridge.send(f"SCORE:{percent}")  # 先送 SCORE，micro:bit 收到 LIGHT 時一起更新指針和燈環
        self.bridge.send(f"LIGHT:{light.upper()}")
        if count is not None:
            self.bridge.send(f"SHOW:{count}")

    # ----- micro:bit 指令處理（真實硬體和網頁模擬器共用） -----

    def on_microbit_line(self, line: str) -> None:
        line = line.strip().upper()
        self.publish("microbit", {"line": line})
        prices = self.config["price_ranges"]
        cmd, _, arg = line.partition(":")
        st = self.state
        if cmd == "HELLO":
            self.bridge.send("ACK:HELLO")
            self.send_hardware_config()
            self.publish("status", self.status())
            return
        if cmd in ("MODE", "GO") and arg in ("FITNESS", "WELLNESS"):
            st.mode = arg.lower()
        elif cmd == "BUDGET" and arg == "ANY":
            st.budget = None  # 預算不限
        elif cmd == "BUDGET" and arg.isdigit() and int(arg) < len(prices):
            st.budget = prices[int(arg)]
        elif cmd == "SPICY" and arg == "ANY":
            st.max_spicy = None  # 辣度都可以
        elif cmd == "SPICY" and arg.isdigit():
            st.max_spicy = min(5, int(arg))
        elif cmd not in ("GO", "MODE"):
            log.info("未知的 micro:bit 指令：%s", line)
            return
        self.bridge.send(f"ACK:{cmd}")
        self.publish("state", st.__dict__)
        if cmd == "GO":
            self.run_recommend(st.query(), source="microbit")


app_state = App()


CONFIG_RESEND_SECONDS = 15


async def resend_hardware_config() -> None:
    """每隔一段時間重送 config/hardware.json 的設定。

    micro:bit 重新開機（例如剛燒錄完）時設定會回到預設值，而它開機時的 HELLO
    可能被瀏覽器的 WebUSB 拿走、伺服器沒收到。定期重送就能自動恢復。
    """
    while True:
        await asyncio.sleep(CONFIG_RESEND_SECONDS)
        if app_state.bridge.responding:
            await asyncio.to_thread(app_state.send_hardware_config)


@asynccontextmanager
async def lifespan(_: FastAPI):
    app_state.loop = asyncio.get_running_loop()
    task = None
    if os.environ.get("FITWELL_NO_SERIAL") != "1":
        app_state.bridge.start()
        task = asyncio.create_task(resend_hardware_config())
    yield
    if task:
        task.cancel()
    app_state.bridge.stop()


app = FastAPI(title="Fit & Well Menu Navigator", version=__version__, lifespan=lifespan)


# ---------------- API ----------------

class QueryIn(BaseModel):
    mode: str = "fitness"
    budget: str | None = None
    max_spicy: int | None = None
    main_types: list[str] = []
    exclude_types: list[str] | None = None
    restaurants: list[str] = []
    top_n: int | None = None
    formula: str | None = None


class StateIn(BaseModel):
    mode: str | None = None
    budget: str | None = None
    max_spicy: int | None = None
    main_types: list[str] | None = None
    restaurants: list[str] | None = None
    formula_fitness: str | None = None
    formula_wellness: str | None = None
    clear: list[str] = []  # 要設回「不限」的欄位，例如 ["budget"]


class TrayIn(BaseModel):
    ids: list[int]
    mode: str = "fitness"
    formula: str | None = None


class CoachIn(BaseModel):
    text: str
    lang: str = "zh"  # 網頁目前的語言：zh／en（AI 用這個語言說明）


class LineIn(BaseModel):
    line: str


@app.get("/api/meta")
def meta():
    cfg = app_state.config
    dishes = app_state.rec.dishes
    return {
        "version": __version__,
        "modes": MODES,
        "price_ranges": cfg["price_ranges"],
        "main_types": sorted({d.main_type for d in dishes}),
        "restaurants": sorted({d.restaurant for d in dishes}),
        "formulas": {
            k: {**v, "text": app_state.rec.scorer.formula_text(k), "lights": cfg["lights"][k]}
            for k, v in cfg["formulas"].items()
        },
        "active_formula": cfg["active_formula"],
        "defaults": cfg["defaults"],
        "dish_count": len(dishes),
        **app_state.status(),
    }


@app.get("/api/status")
def status():
    return app_state.status()


@app.get("/api/state")
def get_state():
    return app_state.state.__dict__


@app.post("/api/state")
def set_state(s: StateIn):
    st = app_state.state
    if s.mode is not None:
        if s.mode not in MODES:
            raise HTTPException(400, "模式錯誤")
        st.mode = s.mode
    for k in ("budget", "max_spicy", "main_types", "restaurants", "formula_fitness", "formula_wellness"):
        v = getattr(s, k)
        if v is not None:
            setattr(st, k, v)
    for k in s.clear:
        if k in ("budget", "max_spicy"):
            setattr(st, k, None)
        elif k in ("main_types", "restaurants"):
            setattr(st, k, [])
    app_state.publish("state", st.__dict__)
    return st.__dict__


@app.get("/api/result")
def last_result():
    """最近一次推薦結果（網頁重新整理後可以接著顯示）。"""
    return app_state.last_result or {}


@app.post("/api/go")
def go():
    """用目前機台狀態推薦（和按 micro:bit 的 B 鍵一樣）。"""
    return app_state.run_recommend(app_state.state.query(), source="web")


@app.post("/api/recommend")
def recommend(q: QueryIn):
    try:
        return app_state.run_recommend(Query(**q.model_dump()), source="api")
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.get("/api/dishes")
def dishes(mode: str = "fitness", formula: str | None = None):
    rec = app_state.rec
    try:
        fid = rec.scorer.formula_id(mode, formula)
    except ValueError as e:
        raise HTTPException(400, str(e))
    scored = sorted((rec.scorer.score(d, fid) for d in rec.dishes), key=lambda s: -s.score)
    return {"formula_id": fid, "items": [s.to_dict() for s in scored]}


@app.post("/api/tray")
def tray(t: TrayIn):
    try:
        res = app_state.rec.evaluate_tray(t.ids, t.mode, t.formula)
    except ValueError as e:
        raise HTTPException(400, str(e))
    app_state.send_light(res["light"], percent=res["percent"])
    app_state.publish("tray", res)
    return res


@app.post("/api/coach")
def ai_coach(c: CoachIn):
    if not c.text.strip():
        raise HTTPException(400, "請輸入想吃什麼")
    out = coach(c.text, app_state.rec, lang=c.lang)
    if out["picks"]:
        app_state.send_light(out["result"]["light"], len(out["picks"]), out["result"]["percent"])
    return out


@app.post("/api/microbit/simulate")
def simulate(l: LineIn):
    """網頁上的虛擬 micro:bit：送出和真的 micro:bit 一樣的指令。"""
    app_state.on_microbit_line(l.line)
    return app_state.status()


@app.post("/api/microbit/send")
def microbit_send(l: LineIn):
    """測試用：直接送一行指令給 micro:bit（例如 LIGHT:GREEN）。"""
    return {"sent": app_state.bridge.send(l.line)}


@app.post("/api/admin/rebuild")
def rebuild():
    """重新讀取 data/raw/ 的表單、產生 dishes.csv 與資料報告，並重新載入設定。"""
    res = build()
    write_csv(res.dishes)
    write_report(res)
    app_state.reload()
    app_state.send_hardware_config()
    return {"dishes": len(res.dishes), "issues": len(res.issues)}


@app.get("/api/report", response_class=PlainTextResponse)
def report():
    return REPORT_MD.read_text(encoding="utf-8") if REPORT_MD.exists() else "尚未產生報告"


@app.get("/api/events")
async def events():
    q: asyncio.Queue = asyncio.Queue()
    app_state.subscribers.add(q)

    async def stream():
        try:
            yield f"data: {json.dumps({'type': 'status', 'data': app_state.status()}, ensure_ascii=False)}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=5)
                    yield f"data: {msg}\n\n"
                except asyncio.TimeoutError:
                    # 每 5 秒送一次狀態，順便讓畫面知道 micro:bit 有沒有插著
                    yield f"data: {json.dumps({'type': 'status', 'data': app_state.status()}, ensure_ascii=False)}\n\n"
        finally:
            app_state.subscribers.discard(q)

    return StreamingResponse(stream(), media_type="text/event-stream", headers={"Cache-Control": "no-cache"})


@app.get("/")
def index():
    return FileResponse(WEB_DIR / "index.html")


app.mount("/", StaticFiles(directory=WEB_DIR), name="web")
