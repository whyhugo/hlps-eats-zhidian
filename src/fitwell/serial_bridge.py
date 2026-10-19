"""micro:bit ↔ 電腦 的 USB 序列埠橋接。

通訊協定（一行一個指令，\n 結尾，115200 baud）— 完整指令表見 docs/ARCHITECTURE.md 第 5 節。

micro:bit → 電腦：HELLO、MODE、GO、BUDGET（0~3／ANY）、SPICY（0~5／ANY）、WARN
電腦 → micro:bit：HELLO?、CFG、SCORE、LIGHT、SHOW、ACK
"""

from __future__ import annotations

import glob
import logging
import sys
import threading
import time
from typing import Callable

log = logging.getLogger("fitwell.serial")

try:
    import serial  # pyserial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    serial = None
    list_ports = None


def find_microbit_port() -> str | None:
    """自動尋找 micro:bit 的序列埠。"""
    if list_ports is not None:
        for p in list_ports.comports():
            desc = f"{p.description} {p.manufacturer} {p.product}".lower()
            # micro:bit 的 USB VID:PID = 0D28:0204（DAPLink）
            if p.vid == 0x0D28 or "micro:bit" in desc or "mbed" in desc or "daplink" in desc:
                return p.device
    if sys.platform == "darwin":
        cands = sorted(glob.glob("/dev/cu.usbmodem*"))
    elif sys.platform.startswith("linux"):
        cands = sorted(glob.glob("/dev/ttyACM*"))
    else:
        cands = []
    return cands[0] if cands else None


def webusb_holders() -> list[str]:
    """macOS：找出用 WebUSB 佔住 micro:bit 的程式（例如開著 MakeCode 的 Chrome）。

    瀏覽器透過 WebUSB 連著 micro:bit 時，micro:bit 傳出的資料會被瀏覽器拿走，
    序列埠雖然打得開，卻什麼都收不到。
    """
    if sys.platform != "darwin":
        return []
    import re
    import subprocess

    try:
        out = subprocess.run(
            ["ioreg", "-p", "IOService", "-l", "-w0", "-r", "-n", "WebUSB: CMSIS-DAP@4"],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except Exception:
        return []
    return sorted(set(re.findall(r'"IOUserClientCreator" = "pid \d+, ([^"]+)"', out)))


class SerialBridge:
    """背景執行緒：持續讀 micro:bit 傳來的指令，交給 on_command 處理。"""

    def __init__(self, on_command: Callable[[str], None], port: str | None = None, baud: int = 115200):
        self.on_command = on_command
        self.port_hint = port
        self.baud = baud
        self.ser = None
        self.port: str | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        self.last_rx: float = 0.0  # 最後一次收到 micro:bit 訊息的時間
        self.rx_count = 0
        self.tx_count = 0
        self.crashes = 0  # micro:bit 程式當掉、被自動重開的次數

    @property
    def connected(self) -> bool:
        """USB 序列埠已開啟（不代表 micro:bit 程式有在跑）。"""
        return self.ser is not None

    @property
    def responding(self) -> bool:
        """連上之後有收到 micro:bit 程式傳來的任何訊息。"""
        return self.connected and self.last_rx > 0

    def start(self) -> None:
        if serial is None:
            log.warning("沒有安裝 pyserial，略過 micro:bit 連線")
            return
        self._thread = threading.Thread(target=self._run, name="microbit-serial", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._close()

    def send(self, line: str) -> bool:
        with self._lock:
            if self.ser is None:
                return False
            try:
                self.ser.write((line.strip() + "\n").encode("ascii", "ignore"))
                self.tx_count += 1
                log.info("→ micro:bit：%s", line.strip())
                return True
            except Exception as e:  # 拔掉線之類
                log.warning("寫入 micro:bit 失敗：%s", e)
                self._close()
                return False

    # ----- 內部 -----

    def _open(self) -> bool:
        port = self.port_hint or find_microbit_port()
        if not port:
            return False
        try:
            self.ser = serial.Serial(port, self.baud, timeout=0.2, write_timeout=1, exclusive=True)
            self.port = port
            self.last_rx = 0.0
            log.info("已開啟序列埠 %s，等待 micro:bit 程式回應…", port)
            return True
        except Exception as e:
            log.debug("開啟 %s 失敗：%s", port, e)
            self.ser = None
            return False

    def _close(self) -> None:
        if self.ser is not None:
            try:
                self.ser.close()
            except Exception:
                pass
        if self.port:
            log.info("micro:bit 已中斷連線")
        self.ser = None
        self.port = None

    def restart_program(self) -> None:
        """讓 micro:bit 上的 MicroPython 重新執行程式（軟重開機，不用拔插 USB）。"""
        with self._lock:
            if self.ser is None:
                return
            try:
                self.ser.write(b"\x03\r\x04")  # Ctrl+C 中斷、Ctrl+D 重開
            except Exception as e:
                log.warning("重新啟動 micro:bit 程式失敗：%s", e)
                return
        self.last_rx = 0.0  # 等重開後的 HELLO 再算「有回應」
        self.crashes += 1

    def _is_crash_output(self, line: str) -> bool:
        """micro:bit 程式出錯時會印出 Traceback／Error，或回到 >>> 提示字元。
        這些不是指令：記錄下來，必要時自動讓程式重新開始。"""
        if line.startswith("WARN:"):
            # 偶爾一次沒關係；10 秒內一直報，代表 micro:bit 卡在記憶體不足的迴圈，收不到電腦指令 → 重開程式
            now = time.time()
            self._warns = [t for t in getattr(self, "_warns", []) if now - t < 10] + [now]
            if len(self._warns) >= 20:
                log.error("❌ micro:bit 一直回報記憶體不足（收不到電腦指令）→ 自動重新啟動程式")
                self._warns = []
                self.restart_program()
            else:
                log.warning("⚠️ micro:bit 回報：%s（記憶體不足，已自動整理，程式仍在執行）", line)
            return True
        if line.startswith(("Traceback", 'File "', ">>>", "MicroPython v", 'Type "help()"', "soft reboot")):
            log.warning("micro:bit 輸出：%s", line)
            return True
        if "Error" in line:
            log.error("❌ micro:bit 程式當掉了：%s → 自動重新啟動程式", line)
            self.restart_program()
            return True
        return False

    def _run(self) -> None:
        buf = b""
        last_ping = 0.0
        while not self._stop.is_set():
            if self.ser is None:
                if not self._open():
                    time.sleep(2)  # 每 2 秒重試，插上 micro:bit 就會自動連上
                    continue
                last_ping = 0.0
            # 還沒收到回應時，每 3 秒問一次 micro:bit 程式在不在
            if not self.last_rx and time.time() - last_ping > 3:
                if last_ping and int(time.time()) % 15 < 3:
                    holders = webusb_holders()
                    if holders:
                        log.warning("⚠️ %s 正透過 WebUSB 佔用 micro:bit，資料會被它拿走。請關掉 MakeCode／python.microbit.org 並完全結束瀏覽器（Cmd+Q），再重新插拔 USB", "、".join(holders))
                last_ping = time.time()
                if not self.send("HELLO?"):
                    continue
            try:
                chunk = self.ser.read(64)
            except Exception as e:
                log.warning("讀取 micro:bit 失敗：%s", e)
                self._close()
                continue
            if not chunk:
                continue
            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode("utf-8", "ignore").strip()
                if line:
                    if self._is_crash_output(line):
                        continue
                    if not self.last_rx:
                        log.info("✅ micro:bit 程式有回應")
                    self.last_rx = time.time()
                    self.rx_count += 1
                    log.info("← micro:bit：%s", line)
                    try:
                        self.on_command(line)
                    except Exception:
                        log.exception("處理 micro:bit 指令失敗：%s", line)
