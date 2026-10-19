import os

os.environ["FITWELL_NO_SERIAL"] = "1"

from fastapi.testclient import TestClient  # noqa: E402

from fitwell.server import app, app_state  # noqa: E402


def test_meta_and_go():
    with TestClient(app) as c:
        m = c.get("/api/meta").json()
        assert m["dish_count"] == 224
        assert "fitness_v2" in m["formulas"]
        r = c.post("/api/go", json={}).json()
        assert len(r["items"]) == 3 and r["light"] in ("green", "yellow", "red")


def test_microbit_commands_drive_state():
    with TestClient(app) as c:
        c.post("/api/microbit/simulate", json={"line": "MODE:WELLNESS"})
        c.post("/api/microbit/simulate", json={"line": "BUDGET:1"})
        c.post("/api/microbit/simulate", json={"line": "SPICY:0"})
        st = c.get("/api/state").json()
        assert st["mode"] == "wellness" and st["budget"] == "101-300" and st["max_spicy"] == 0
        c.post("/api/microbit/simulate", json={"line": "GO"})
        assert app_state.last_result["source"] == "microbit"
        assert app_state.last_result["query"]["mode"] == "wellness"


def test_recommend_validation():
    with TestClient(app) as c:
        assert c.post("/api/recommend", json={"mode": "x"}).status_code == 400
        assert c.post("/api/recommend", json={"mode": "fitness", "budget": "999"}).status_code == 400


def test_hello_sends_hardware_config(monkeypatch):
    sent = []
    monkeypatch.setattr(app_state.bridge, "send", lambda line: sent.append(line) or True)
    monkeypatch.setattr(app_state, "hardware", {"use_budget_knob": True, "use_spicy_knob": True, "buzzer": "active", "servo_reverse": False, "beep_ms": 200})
    with TestClient(app) as c:
        c.post("/api/microbit/simulate", json={"line": "HELLO:3.0"})
    assert "CFG:KNOB:1" in sent and "CFG:SKNOB:1" in sent and "CFG:BUZZER:active" in sent


def test_crash_output_triggers_restart(monkeypatch):
    from fitwell.serial_bridge import SerialBridge

    got = []
    b = SerialBridge(on_command=got.append)
    restarted = []
    monkeypatch.setattr(b, "restart_program", lambda: restarted.append(True))
    for line in ["Traceback (most recent call last):", 'File "__main__", line 99, in <module>',
                 "MemoryError: memory allocation failed, allocating 256 bytes", "WARN:MEMORY"]:
        assert b._is_crash_output(line)
    assert restarted == [True]
    assert not b._is_crash_output("GO:FITNESS")


def test_knob_any_values():
    with TestClient(app) as c:
        c.post("/api/microbit/simulate", json={"line": "BUDGET:ANY"})
        c.post("/api/microbit/simulate", json={"line": "SPICY:ANY"})
        st = c.get("/api/state").json()
        assert st["budget"] is None and st["max_spicy"] is None
        c.post("/api/microbit/simulate", json={"line": "BUDGET:0"})
        c.post("/api/microbit/simulate", json={"line": "SPICY:0"})
        st = c.get("/api/state").json()
        assert st["budget"] == "100以下" and st["max_spicy"] == 0
