"""讀取 config/scoring.json（推薦公式）與 config/hardware.json（micro:bit 零件設定）。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import CONFIG_PATH, HARDWARE_PATH


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# 腳位：名稱 → 預設腳位（順序就是送給 micro:bit 的 CFG:PINS 順序，不能改）
PIN_DEFAULTS: dict[str, int] = {
    "green": 0,
    "yellow": 1,
    "red": 2,
    "fitness_button": 13,
    "wellness_button": 14,
    "servo": 12,
    "buzzer": 16,
    "budget_knob": 4,
    "spicy_knob": 10,
}
PIN_LABELS = {
    "green": "綠燈", "yellow": "黃燈", "red": "紅燈", "fitness_button": "健身鈕", "wellness_button": "養生鈕",
    "servo": "伺服馬達", "buzzer": "蜂鳴器", "budget_knob": "預算旋鈕", "spicy_knob": "辣度旋鈕",
}
USABLE_PINS = {0, 1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16}  # 5、11 是 A／B 鍵，19、20 是 I2C
ANALOG_PINS = {0, 1, 2, 3, 4, 10}  # 只有這些腳位能讀旋鈕（類比）
DISPLAY_PINS = {3, 4, 6, 7, 9, 10}  # 點陣也用這些腳位，只能接旋鈕


def check_pins(pins: dict[str, Any]) -> dict[str, int]:
    """檢查 hardware.json 的 pins：腳位存在、沒有重複、旋鈕接在類比腳位、其他零件不接點陣腳位。"""
    unknown = set(pins) - set(PIN_DEFAULTS)
    if unknown:
        raise ValueError(f"hardware.json 的 pins 有不認識的名稱：{'、'.join(sorted(unknown))}（可用：{'、'.join(PIN_DEFAULTS)}）")
    out = {**PIN_DEFAULTS, **{k: int(v) for k, v in pins.items()}}
    seen: dict[int, str] = {}
    for k, n in out.items():
        name = f"{PIN_LABELS[k]}（{k}）"
        if n not in USABLE_PINS:
            raise ValueError(f"{name} 不能接 P{n}；可用的腳位：{sorted(USABLE_PINS)}")
        if k.endswith("_knob"):
            if n not in ANALOG_PINS:
                raise ValueError(f"{name} 要接能讀類比的腳位：{sorted(ANALOG_PINS)}，現在是 P{n}")
        elif n in DISPLAY_PINS:
            raise ValueError(f"{name} 不能接 P{n}：那是點陣的腳位，會和點陣互相干擾")
        if n in seen:
            raise ValueError(f"{name} 和 {seen[n]} 都接在 P{n}，腳位不能重複")
        seen[n] = name
    return out


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
    data: dict[str, Any] = {}
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
    hw["pins"] = check_pins(hw.get("pins") or {})
    return hw


def hardware_commands(hw: dict[str, Any]) -> list[str]:
    """把硬體設定轉成送給 micro:bit 的 CFG 指令（見 docs/ARCHITECTURE.md 第 5 節）。"""
    return [
        f"CFG:KNOB:{int(bool(hw['use_budget_knob']))}",
        f"CFG:SKNOB:{int(bool(hw['use_spicy_knob']))}",
        f"CFG:BUZZER:{hw['buzzer']}",
        f"CFG:SERVO_REV:{int(bool(hw['servo_reverse']))}",
        f"CFG:BEEP:{hw['beep_ms']}",
        "CFG:PINS:" + ",".join(str(n) for n in check_pins(hw.get("pins") or {}).values()),
    ]
