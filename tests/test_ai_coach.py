"""AI 小教練（Gemini）：設定、請求格式、回應解析；Python 與 Worker（JS）版必須一致。"""

import json
import shutil
import subprocess

import pytest

from fitwell import ai_coach
from fitwell.ai_coach import ai_settings, coach, interaction_request, output_text
from fitwell.config import load_config
from fitwell.data import load_dishes
from fitwell.recommend import Recommender

ENVS = [
    {},
    {"FITWELL_AI_MODEL": "models/x", "FITWELL_AI_THINKING": "HIGH", "FITWELL_AI_MAX_TOKENS": "100",
     "FITWELL_AI_GOOGLE_SEARCH": "1"},
    {"FITWELL_AI_THINKING": "weird", "FITWELL_AI_MAX_TOKENS": "abc"},
    {"FITWELL_AI_MODEL": "models/gemini-3.5-flash", "FITWELL_AI_MAX_TOKENS": "99999oops"},
    {"FITWELL_AI_MODEL": "  ", "FITWELL_AI_MAX_TOKENS": " 2048 "},
    {"FITWELL_AI_MAX_TOKENS": "1_000"},
    {"FITWELL_AI_MAX_TOKENS": "+500"},
    {"FITWELL_AI_MAX_TOKENS": "99999"},
]
INTERACTION = {
    "status": "completed",
    "steps": [
        {"type": "thought", "content": [{"type": "text", "text": "想一下"}]},
        {"type": "model_output", "content": [{"type": "text", "text": '{"a":'}, {"type": "text", "text": " 1}"}]},
    ],
}


def test_settings_and_request():
    s = ai_settings({})
    assert s == {"model": "gemini-3.8-flash", "thinking_level": "low", "max_output_tokens": 8192,
                 "google_search": False}
    s2 = ai_settings(ENVS[1])
    assert s2["thinking_level"] == "high" and s2["max_output_tokens"] == 256 and s2["google_search"]
    assert ai_settings(ENVS[2])["thinking_level"] == "low"
    # 模型名稱去掉 models/ 前綴；token 數只接受整串數字（打錯字用預設值）
    s3 = ai_settings(ENVS[3])
    assert s3["model"] == "gemini-3.5-flash" and s3["max_output_tokens"] == 8192
    assert ai_settings(ENVS[4])["model"] == "gemini-3.8-flash" and ai_settings(ENVS[4])["max_output_tokens"] == 2048
    assert [ai_settings(e)["max_output_tokens"] for e in ENVS[5:]] == [8192, 8192, 65536]
    req = interaction_request("sys", "hi", {"type": "object"}, s2)
    assert req["response_format"]["schema"] == {"type": "object"} and req["tools"] == [{"type": "google_search"}]
    assert "tools" not in interaction_request("sys", "hi", {}, s)
    assert output_text(INTERACTION) == '{"a": 1}'


class FakeClient:
    """假的 genai.Client：第一次回條件，第二次回挑選結果。"""

    def __init__(self, answers):
        self.answers = list(answers)
        self.requests = []
        self.interactions = self

    def create(self, **req):
        self.requests.append(req)
        text = json.dumps(self.answers.pop(0), ensure_ascii=False)
        return {"status": "completed", "steps": [{"type": "model_output", "content": [{"type": "text", "text": text}]}]}


def test_coach_with_gemini(monkeypatch):
    rec = Recommender(load_dishes(), load_config())
    first = rec.recommend(ai_coach.Query(mode="wellness", max_spicy=0, top_n=8)).items[1].dish.id
    fake = FakeClient([
        {"mode": "wellness", "budget": "不限", "max_spicy": 0, "main_types": []},
        {"picks": [{"id": first, "reason": "清淡"}, {"id": 999999, "reason": "不存在"}], "summary": "幫你挑好了"},
    ])
    monkeypatch.setenv("GEMINI_API_KEY", "test")
    monkeypatch.setattr(ai_coach, "genai", type("G", (), {"Client": lambda api_key: fake}))
    out = coach("帶阿嬤吃飯，不要辣", rec)
    assert out["source"] == "gemini" and out["summary"] == "幫你挑好了"
    assert [p["dish"]["id"] for p in out["picks"]] == [first]  # 不在候選裡的 id 會被丟掉
    assert fake.requests[0]["model"] == "gemini-3.8-flash"


def test_coach_falls_back_to_rules(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    out = coach("100 元以內有什麼健康的", Recommender(load_dishes(), load_config()))
    assert out["source"] == "rules" and len(out["picks"]) == 3


def test_worker_gemini_matches_python():
    node = ["node"] if shutil.which("node") else (["mise", "exec", "--", "node"] if shutil.which("mise") else None)
    if node is None:
        pytest.skip("沒有安裝 Node.js，略過 Worker 版比對")
    arg = json.dumps({"envs": ENVS, "interaction": INTERACTION}, ensure_ascii=False)
    r = subprocess.run([*node, "tests/js/check_gemini.mjs", arg], capture_output=True, text=True,
                       cwd=ai_coach.__file__.rsplit("/src/", 1)[0])
    assert r.returncode == 0, r.stderr
    js = json.loads(r.stdout)
    assert js["settings"] == [ai_settings(e) for e in ENVS]
    assert js["request"] == interaction_request("sys", "user", {"type": "object"}, ai_settings(ENVS[0]))
    assert js["text"] == output_text(INTERACTION)
    assert js["ask"] == {"a": 1}
    assert js["seen"] == {"url": "https://generativelanguage.googleapis.com/v1beta/interactions", "key": "k",
                          "model": "gemini-3.8-flash"}
