// Gemini Interactions API（REST）— 和 src/fitwell/ai_coach.py 的 ai_settings／interaction_request／output_text 相同。
// 設定都可以在 Cloudflare Worker 的 Variables and Secrets 改，不用改程式：
//   GEMINI_API_KEY            Gemini API 金鑰（Secret）
//   FITWELL_AI_MODEL          模型，預設 models/gemini-3.8-flash
//   FITWELL_AI_THINKING       思考程度 minimal／low／medium／high，預設 low（越高越慢越貴）
//   FITWELL_AI_MAX_TOKENS     每次回覆最多幾個 token（含思考），預設 8192
//   FITWELL_AI_GOOGLE_SEARCH  1 = 允許模型用 Google 搜尋補充說明（會多收費），預設 0

export const DEFAULT_MODEL = "models/gemini-3.8-flash";
const API_URL = "https://generativelanguage.googleapis.com/v1beta/interactions";

export function aiSettings(env) {
  let thinking = String(env.FITWELL_AI_THINKING || "low").toLowerCase();
  if (!["minimal", "low", "medium", "high"].includes(thinking)) thinking = "low";
  let maxTokens = parseInt(env.FITWELL_AI_MAX_TOKENS || "8192", 10);
  if (!Number.isFinite(maxTokens)) maxTokens = 8192;
  return {
    model: env.FITWELL_AI_MODEL || DEFAULT_MODEL,
    thinking_level: thinking,
    max_output_tokens: Math.max(256, Math.min(65536, maxTokens)),
    google_search: ["1", "true", "yes"].includes(String(env.FITWELL_AI_GOOGLE_SEARCH || "0").toLowerCase()),
  };
}

// 請求內容：要求回傳符合 schema 的 JSON
export function interactionRequest(system, user, schema, settings) {
  const req = {
    model: settings.model,
    system_instruction: system,
    input: user,
    generation_config: { max_output_tokens: settings.max_output_tokens, thinking_level: settings.thinking_level },
    response_format: { type: "text", mime_type: "application/json", schema },
    response_mime_type: "application/json",
  };
  if (settings.google_search) req.tools = [{ type: "google_search" }];
  return req;
}

// 從回應的 steps 取出模型最後輸出的文字
export function outputText(interaction) {
  const steps = interaction?.steps || [];
  for (let i = steps.length - 1; i >= 0; i--) {
    if (steps[i].type === "model_output") return (steps[i].content || []).map((c) => c.text || "").join("");
  }
  return "";
}

export async function askJSON(env, system, user, schema, fetchImpl = fetch) {
  const r = await fetchImpl(API_URL, {
    method: "POST",
    headers: { "content-type": "application/json", "x-goog-api-key": env.GEMINI_API_KEY },
    body: JSON.stringify(interactionRequest(system, user, schema, aiSettings(env))),
  });
  if (!r.ok) throw new Error(`Gemini API ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const interaction = await r.json();
  if (interaction.status && interaction.status !== "completed") return null;
  const text = outputText(interaction);
  return text ? JSON.parse(text) : null;
}
