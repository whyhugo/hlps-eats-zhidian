"""指令列工具。

    fitwell build-data                 重新產生 data/processed/dishes.csv 與資料報告
    fitwell recommend -m fitness -b 101-300 -s 2
    fitwell serve [--port 8000]        啟動網頁展示畫面 + micro:bit 串接
    fitwell ports                      列出電腦上的序列埠（找 micro:bit 用）
    fitwell export-static              匯出純靜態網頁版資料（Cloudflare 線上版用）
"""

from __future__ import annotations

import argparse
import os
import logging
import sys
from collections import Counter

LIGHT_ICON = {"green": "🟢", "yellow": "🟡", "red": "🔴"}


def cmd_build(_: argparse.Namespace) -> None:
    from . import PROCESSED_CSV, REPORT_MD
    from .data import build, write_csv, write_report

    res = build()
    write_csv(res.dishes)
    write_report(res)
    print(f"✅ 已產生 {PROCESSED_CSV.relative_to(PROCESSED_CSV.parents[2])}（{len(res.dishes)} 筆）")
    print(f"📝 資料報告 {REPORT_MD.relative_to(REPORT_MD.parents[2])}，發現 {len(res.issues)} 個問題：")
    for k, v in Counter(i.kind for i in res.issues).most_common():
        print(f"   - {k}：{v}")


def cmd_recommend(a: argparse.Namespace) -> None:
    from .config import load_config
    from .data import load_dishes
    from .recommend import Query, Recommender

    rec = Recommender(load_dishes(), load_config())
    q = Query(
        mode=a.mode,
        budget=a.budget,
        max_spicy=a.spicy,
        main_types=a.type or [],
        top_n=a.top,
        formula=a.formula,
    )
    r = rec.recommend(q)
    print(f"\n【{'健身' if q.mode == 'fitness' else '養生'}模式】{r.formula_label}")
    print(f"公式：{r.formula_text}")
    print("篩選：" + " → ".join(f"{s['step']}({s['remaining']})" for s in r.steps))
    print()
    for i, s in enumerate(r.items, 1):
        d = s.dish
        print(f" {i}. {LIGHT_ICON[s.light]} {s.score:>3} 分  {d.restaurant}｜{d.name}  [{d.price_range}] {d.main_type} {d.cooking}")
    if not r.items:
        print(" ⚠️ 找不到符合條件的餐點")
    for h in r.hints:
        print(f" 💡 {h}")
    print(f"\n整體燈號：{LIGHT_ICON[r.light]}\n")


def cmd_export_static(_: argparse.Namespace) -> None:
    from .static_export import export_static

    bundle, golden = export_static()
    print(f"✅ 已產生 {bundle.relative_to(bundle.parents[2])}（靜態網頁版資料）與 {golden.relative_to(golden.parents[1])}")
    print("   推上 GitHub 後，Cloudflare 會自動更新網站")


def cmd_serve(a: argparse.Namespace) -> None:
    import os

    import uvicorn

    if a.no_serial:
        os.environ["FITWELL_NO_SERIAL"] = "1"
    if a.serial_port:
        os.environ["FITWELL_SERIAL_PORT"] = a.serial_port
    print(f"🍱 Fit & Well Menu Navigator：http://localhost:{a.port}")
    uvicorn.run(
        "fitwell.server:app",
        host=a.host,
        port=a.port,
        reload=a.reload,
        log_level="info",
        timeout_graceful_shutdown=2,  # 網頁的即時連線（SSE）不會自己斷，不設的話 Ctrl+C 會卡住
    )


def cmd_ports(_: argparse.Namespace) -> None:
    from .serial_bridge import find_microbit_port, list_ports

    if list_ports is None:
        print("請先安裝 pyserial")
        return
    for p in list_ports.comports():
        print(f"{p.device}\t{p.description}\tVID={p.vid}")
    print(f"\n自動偵測到的 micro:bit：{find_microbit_port() or '（沒有）'}")


def cmd_monitor(a: argparse.Namespace) -> None:
    """直接和 micro:bit 對話（不經過網頁伺服器），用來檢查接線與韌體。"""
    import threading
    import time

    from .serial_bridge import find_microbit_port, serial, webusb_holders

    if serial is None:
        print("請先安裝 pyserial")
        return
    port = a.serial_port or find_microbit_port()
    if not port:
        print("❌ 找不到 micro:bit：請確認 USB 線可以傳資料，並執行 fitwell ports 查看")
        return
    try:
        ser = serial.Serial(port, 115200, timeout=0.2, exclusive=True)
    except Exception as e:
        print(f"❌ 無法開啟 {port}：{e}")
        print("   可能 fitwell serve、MakeCode 或 python.microbit.org 網頁正在使用這個序列埠，請先關掉")
        return
    print(f"已開啟 {port}。按 micro:bit 的 A、B 鍵，這裡應該會出現 MODE:… / GO")
    print("也可以輸入指令送給 micro:bit，例如 LIGHT:GREEN、SHOW:5、HELLO?（Ctrl+C 結束）\n")
    got = threading.Event()

    def reader() -> None:
        buf = b""
        while True:
            try:
                buf += ser.read(64)
            except Exception as e:
                print(f"\n❌ 讀取失敗：{e}")
                return
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode("utf-8", "ignore").strip()
                if line:
                    got.set()
                    print(f"← micro:bit：{line}")

    threading.Thread(target=reader, daemon=True).start()
    ser.write(b"HELLO?\n")
    print("→ HELLO?")
    if not got.wait(3):
        holders = webusb_holders()
        if holders:
            print(f"⚠️ {'、'.join(holders)} 正透過 WebUSB 佔用 micro:bit，資料會被它拿走。")
            print("   請關掉 MakeCode／python.microbit.org，完全結束瀏覽器（Cmd+Q），再重新插拔 USB。")
        print("⚠️ 3 秒內沒收到回應：micro:bit 可能還沒燒錄最新程式、程式出錯（LED 點陣會捲動錯誤訊息），或燒錄的是舊版")
    try:
        while True:
            line = input().strip()
            if line:
                ser.write((line + "\n").encode())
                print(f"→ {line}")
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        ser.close()


def load_dotenv() -> None:
    """讀取專案根目錄的 .env（不覆蓋已經設定的環境變數）。"""
    import os

    from . import ROOT

    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip())


def main(argv: list[str] | None = None) -> None:
    load_dotenv()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 終端機顯示中文
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    p = argparse.ArgumentParser(prog="fitwell", description="Fit & Well Menu Navigator")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("build-data", help="清理原始表單，產生 dishes.csv 與資料報告").set_defaults(func=cmd_build)

    r = sub.add_parser("recommend", help="在終端機試推薦")
    r.add_argument("-m", "--mode", choices=["fitness", "wellness"], default="fitness")
    r.add_argument("-b", "--budget", choices=["100以下", "101-300", "301-500", "500以上"])
    r.add_argument("-s", "--spicy", type=int, help="可接受辣度 0~5")
    r.add_argument("-t", "--type", action="append", help="主餐類型，可重複")
    r.add_argument("-n", "--top", type=int)
    r.add_argument("-f", "--formula", help="公式代號，例如 fitness_v1")
    r.set_defaults(func=cmd_recommend)

    s = sub.add_parser("serve", help="啟動網頁 + micro:bit 串接")
    s.add_argument("--host", default=os.environ.get("FITWELL_HOST", "0.0.0.0"))
    s.add_argument("--port", type=int, default=int(os.environ.get("FITWELL_PORT", "8000")))
    s.add_argument("--serial-port", help="指定 micro:bit 序列埠，例如 COM3 或 /dev/cu.usbmodem1102")
    s.add_argument("--no-serial", action="store_true", help="不連接 micro:bit（只用網頁模擬器）")
    s.add_argument("--reload", action="store_true", help="開發用：程式改了自動重啟")
    s.set_defaults(func=cmd_serve)

    sub.add_parser("ports", help="列出序列埠").set_defaults(func=cmd_ports)
    sub.add_parser("export-static", help="匯出純靜態網頁版資料（Cloudflare 線上版用）").set_defaults(func=cmd_export_static)

    mo = sub.add_parser("monitor", help="直接和 micro:bit 對話（檢查接線與韌體用，請先關掉 fitwell serve）")
    mo.add_argument("--serial-port")
    mo.set_defaults(func=cmd_monitor)

    a = p.parse_args(argv)
    a.func(a)


if __name__ == "__main__":
    main()
