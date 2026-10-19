"""產生 micro:bit V1 用的 .hex（MicroPython v1.0.1，記憶體比網頁版多）。

    uv run python scripts/build_microbit_hex.py

main.py 的中文註解很長，超過 .hex 能放的 8KB，所以先拿掉註解和空行再打包；
原始的 firmware/microbit/main.py 保留註解給學生看。
"""

import io
import subprocess
import sys
import tempfile
import tokenize
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "firmware" / "microbit" / "main.py"
OUT = ROOT / "firmware" / "microbit" / "fitwell-microbit-v1.hex"


def strip_comments(code: str) -> str:
    toks = [t for t in tokenize.generate_tokens(io.StringIO(code).readline) if t.type != tokenize.COMMENT]
    out = tokenize.untokenize(toks)
    return "\n".join(line.rstrip() for line in out.splitlines() if line.strip()) + "\n"


def main() -> None:
    small = strip_comments(SRC.read_text(encoding="utf-8"))
    size = len(small.encode("utf-8"))
    print(f"main.py 去掉註解後 {size} bytes（上限 8188）")
    with tempfile.TemporaryDirectory() as d:
        script = Path(d) / "main.py"
        script.write_text(small, encoding="utf-8")
        subprocess.run(["uv", "tool", "run", "--from", "uflash==1.3.0", "uflash", str(script), d], check=True)
        OUT.write_bytes((Path(d) / "micropython.hex").read_bytes())
    print(f"✅ 已產生 {OUT.relative_to(ROOT)}，把它拖進 MICROBIT 磁碟即可燒錄")


if __name__ == "__main__":
    sys.exit(main())
