// 檢查 worker/gemini.js 和 Python 版（src/fitwell/ai_coach.py）產生一樣的請求、解析一樣的回應。
// 由 tests/test_ai_coach.py 呼叫：node tests/js/check_gemini.mjs '<json>'
import { aiSettings, interactionRequest, outputText, askJSON } from "../../worker/gemini.js";

const input = JSON.parse(process.argv[2]);
const out = {
  settings: input.envs.map((env) => aiSettings(env)),
  request: interactionRequest("sys", "user", { type: "object" }, aiSettings(input.envs[0])),
  text: outputText(input.interaction),
};
// askJSON：用假的 fetch 檢查網址、標頭與解析
let seen = null;
const fakeFetch = async (url, opt) => {
  seen = { url, key: opt.headers["x-goog-api-key"], body: JSON.parse(opt.body) };
  return { ok: true, json: async () => input.interaction };
};
out.ask = await askJSON({ GEMINI_API_KEY: "k" }, "sys", "user", { type: "object" }, fakeFetch);
out.seen = { url: seen.url, key: seen.key, model: seen.body.model };
console.log(JSON.stringify(out));
