"""讀取 config/scoring.json（推薦公式）與 config/hardware.json（micro:bit 零件設定）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import CONFIG_PATH, HARDWARE_PATH


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


HARDWARE_DEFAULTS: dict[str, Any] = {
    "use_budget_knob": False,
    "use_spicy_knob": False,
    "buzzer": "passive",
    "servo_reverse": False,
    "beep_ms": 150,
}


def load_hardware(path: Path = HARDWARE_PATH) -> dict[str, Any]:
    """讀 config/hardware.json（底線開頭的是說明文字，略過）；檔案不存在就用預設值。"""
    hw = dict(HARDWARE_DEFAULTS)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    if "use_knob" in data:  # 舊版設定名稱
        data.setdefault("use_budget_knob", data.pop("use_knob"))
    data.pop("ring_brightness", None)  # 燈環已拿掉（V1 記憶體不夠）
    hw.update(data)
    if hw["buzzer"] not in ("passive", "active", "off"):
        raise ValueError(f"hardware.json 的 buzzer 只能是 passive、active 或 off，現在是 {hw['buzzer']!r}")
    hw["beep_ms"] = max(30, min(500, int(hw["beep_ms"])))
    return hw


def hardware_commands(hw: dict[str, Any]) -> list[str]:
    """把硬體設定轉成送給 micro:bit 的 CFG 指令（見 docs/ARCHITECTURE.md 第 5 節）。"""
    return [
        f"CFG:KNOB:{int(bool(hw['use_budget_knob']))}",
        f"CFG:SKNOB:{int(bool(hw['use_spicy_knob']))}",
        f"CFG:BUZZER:{hw['buzzer']}",
        f"CFG:SERVO_REV:{int(bool(hw['servo_reverse']))}",
        f"CFG:BEEP:{hw['beep_ms']}",
    ]
