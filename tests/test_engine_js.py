"""靜態網頁版（Cloudflare 線上版）的檢查。"""

import json
import shutil
import subprocess

import pytest

from fitwell.static_export import BUNDLE, GOLDEN, build_bundle, build_golden


def test_bundle_is_up_to_date():
    """改了菜單或設定卻忘了執行 `uv run fitwell export-static`，網站就會是舊資料。"""
    assert json.loads(BUNDLE.read_text(encoding="utf-8")) == json.loads(json.dumps(build_bundle(), ensure_ascii=False)), \
        "web/data/bundle.json 過期了，請執行 uv run fitwell export-static"
    assert json.loads(GOLDEN.read_text(encoding="utf-8")) == json.loads(json.dumps(build_golden(), ensure_ascii=False)), \
        "tests/golden_engine.json 過期了，請執行 uv run fitwell export-static"


def _node() -> list[str] | None:
    if shutil.which("node"):
        return ["node"]
    if shutil.which("mise"):
        return ["mise", "exec", "--", "node"]
    return None


def test_js_engine_matches_python():
    """web/engine.js 和 Python 推薦引擎算出的結果必須完全相同。"""
    node = _node()
    if node is None:
        pytest.skip("沒有安裝 Node.js，略過 JS 版比對")
    r = subprocess.run([*node, "tests/js/check_engine.cjs"], capture_output=True, text=True, cwd=BUNDLE.parents[2])
    assert r.returncode == 0, r.stderr or r.stdout


def test_i18n_dictionary_complete():
    """雙語字典：中英文 key 相同、網頁用到的 key 都存在、菜單詞彙都有英文。"""
    node = _node()
    if node is None:
        pytest.skip("沒有安裝 Node.js，略過雙語字典檢查")
    r = subprocess.run([*node, "tests/js/check_i18n.cjs"], capture_output=True, text=True, cwd=BUNDLE.parents[2])
    assert r.returncode == 0, r.stderr or r.stdout
