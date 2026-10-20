"""產生 micro:bit V1 用的 .hex（MicroPython v1.0.1，記憶體比網頁版多）。
腳位依 config/hardware.json 的 pins 寫進程式裡；改了腳位就重新執行一次。

    uv run python scripts/build_microbit_hex.py           產生並覆蓋 fitwell-microbit-v1.hex
    uv run python scripts/build_microbit_hex.py --check   只檢查 .hex 是不是最新的（CI 用）

V1 只有 16KB 記憶體，連「把程式編譯起來」都會不夠（MemoryError）。
所以打包前用 python-minifier 拿掉註解、把變數名稱縮短（省下存名稱的記憶體）；
原始的 firmware/microbit/main.py 保留完整註解給學生看。
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "firmware" / "microbit" / "main.py"
OUT = ROOT / "firmware" / "microbit" / "fitwell-microbit-v1.hex"


def minify(path: Path) -> str:
    out = subprocess.run(
        ["uv", "tool", "run", "--from", "python-minifier==3.4.0", "pyminify",
         "--rename-globals", "--no-hoist-literals", "--remove-literal-statements", str(path)],
        check=True, capture_output=True, text=True,
    ).stdout
    return out


PIN_LINE = "P = [pin0, pin1, pin2, pin13, pin14, pin12, pin16, pin4, pin10]"


def with_pins(code: str) -> str:
    """把 main.py 的預設腳位換成 config/hardware.json 的 pins。"""
    sys.path.insert(0, str(ROOT / "src"))
    from fitwell.config import load_hardware

    pins = load_hardware()["pins"]  # 已經檢查過：不重複、旋鈕接類比腳位⋯⋯
    if PIN_LINE not in code:
        raise SystemExit("main.py 找不到腳位那一行，請不要改它的寫法：" + PIN_LINE)
    line = "P = [" + ", ".join(f"pin{n}" for n in pins.values()) + "]"
    print("腳位：" + "、".join(f"{k}=P{n}" for k, n in pins.items()))
    return code.replace(PIN_LINE, line)


def main() -> int:
    with tempfile.TemporaryDirectory() as d:
        src = Path(d) / "src.py"
        src.write_text(with_pins(SRC.read_text(encoding="utf-8")), encoding="utf-8")
        small = minify(src)
    size = len(small.encode("utf-8"))
    print(f"main.py 縮小後 {size} bytes")
    with tempfile.TemporaryDirectory() as d:
        script = Path(d) / "main.py"
        script.write_text(small, encoding="utf-8")
        subprocess.run(["uv", "tool", "run", "--from", "uflash==1.3.0", "uflash", str(script), d], check=True,
                       stdout=subprocess.DEVNULL)
        hex_bytes = (Path(d) / "micropython.hex").read_bytes()
    if "--check" in sys.argv:
        if OUT.read_bytes() != hex_bytes:
            print(f"❌ {OUT.relative_to(ROOT)} 不是最新的：改了 main.py 或 hardware.json 的 pins 後，"
                  "請執行 uv run python scripts/build_microbit_hex.py 並提交")
            return 1
        print(f"✅ {OUT.relative_to(ROOT)} 是最新的")
        return 0
    OUT.write_bytes(hex_bytes)
    print(f"✅ 已產生 {OUT.relative_to(ROOT)}，把它拖進 MICROBIT 磁碟即可燒錄")


if __name__ == "__main__":
    sys.exit(main())
