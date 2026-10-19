import csv

import pytest

from fitwell import RAW_FITNESS
from fitwell.ai_coach import parse_rules
from fitwell.config import load_config
from fitwell.data import build
from fitwell.recommend import Query, Recommender
from fitwell.scoring import Scorer


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def built():
    return build()


@pytest.fixture(scope="module")
def rec(built, cfg):
    return Recommender(built.dishes, cfg)


def test_build_merges_all_rows(built):
    assert len(built.dishes) == 231
    rests = {d.restaurant for d in built.dishes}
    assert "勝博店" not in rests and "饗泰多" not in rests
    assert not any("⁠" in r for r in rests)
    assert sum(d.duplicate_of is not None for d in built.dishes) == 7


def test_fitness_v1_matches_student_sheet(built, cfg):
    """學生原版公式算出的分數，要和學生 Excel 的總加權一模一樣。"""
    with open(RAW_FITNESS, encoding="utf-8-sig") as f:
        totals = [int(r[-1]) for r in list(csv.reader(f))[1:]]
    s = Scorer(cfg)
    assert [s.score(d, "fitness_v1").score for d in built.dishes] == totals


def test_score_breakdown_sums(rec):
    for s in rec.recommend(Query("wellness")).items:
        assert sum(t.points for t in s.terms) == s.score


def test_filters_follow_flowchart(rec):
    r = rec.recommend(Query("fitness", budget="101-300", max_spicy=0, main_types=["海鮮類"]))
    assert len(r.items) == 3
    for s in r.items:
        assert s.dish.price_range in ("100以下", "101-300")
        assert s.dish.spicy_level == 0
        assert s.dish.main_type == "海鮮類"
    scores = [s.score for s in r.items]
    assert scores == sorted(scores, reverse=True)


def test_default_excludes_drinks_and_desserts(rec):
    r = rec.recommend(Query("wellness", top_n=50))
    assert not {s.dish.main_type for s in r.items} & {"飲料類", "甜點類"}


def test_not_enough_gives_hints(rec):
    r = rec.recommend(Query("wellness", budget="100以下", max_spicy=0, main_types=["海鮮類"]))
    assert not r.enough
    assert r.hints


def test_fitness_prefers_lean_protein_over_fatty_meat(rec):
    top = rec.recommend(Query("fitness", top_n=10)).items
    assert all("高油" not in s.dish.tags for s in top)


def test_tray_warns_on_greasy_combo(rec, built):
    greasy = [d.id for d in built.dishes if "高油" in d.tags and "多澱粉" in d.tags and d.duplicate_of is None][:3]
    res = rec.evaluate_tray(greasy, "fitness")
    assert res["light"] == "red"
    assert res["warnings"]


def test_rule_parser():
    q, _ = parse_rules("帶阿嬤吃飯，要清淡、不辣，300 元以內")
    assert q.mode == "wellness" and q.budget == "101-300" and q.max_spicy == 0 and q.main_types == []
    q, _ = parse_rules("剛重訓完想吃雞肉")
    assert q.mode == "fitness" and q.main_types == ["肉類"]


def test_hardware_config_file(tmp_path):
    import json

    from fitwell.config import hardware_commands, load_hardware

    p = tmp_path / "hw.json"
    p.write_text(json.dumps({"_說明": "x", "use_knob": True, "buzzer": "off", "ring_brightness": 9}), encoding="utf-8")
    hw = load_hardware(p)  # 舊名稱 use_knob 會轉成 use_budget_knob，ring_brightness 忽略
    assert hw["use_budget_knob"] is True and hw["use_spicy_knob"] is False
    assert hardware_commands(hw) == ["CFG:KNOB:1", "CFG:SKNOB:0", "CFG:BUZZER:off", "CFG:SERVO_REV:0", "CFG:BEEP:150",
                                     "CFG:PINS:0,1,2,13,14,12,16,4,10"]
    p.write_text(json.dumps({"buzzer": "loud"}), encoding="utf-8")
    with pytest.raises(ValueError):
        load_hardware(p)


def test_pins_config():
    import pytest

    from fitwell.config import check_pins

    assert check_pins({"green": 8, "budget_knob": 1, "yellow": 15})["green"] == 8
    with pytest.raises(ValueError, match="重複"):
        check_pins({"red": 0})  # 綠燈預設就在 P0
    with pytest.raises(ValueError, match="類比"):
        check_pins({"budget_knob": 8})
    with pytest.raises(ValueError, match="點陣"):
        check_pins({"servo": 6})
    with pytest.raises(ValueError, match="不能接"):
        check_pins({"buzzer": 5})
