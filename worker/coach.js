// AI 小教練（Cloudflare Worker）— 和 src/fitwell/ai_coach.py 的流程相同：
//   1. Claude 把一句話轉成篩選條件  2. 推薦引擎算候選  3. Claude 從候選中挑 3 道並說明
// API 金鑰只存在 Cloudflare 的環境變數（Secret），不會出現在網頁裡。
// 任何一步失敗都改用規則版，網頁一定有結果。
import "../web/engine.js";
import bundle from "../web/data/bundle.json";

const E = globalThis.FitwellEngine;
const rec = new E.Recommender(bundle.dishes, bundle.config);
const ALL_TYPES = [...new Set(rec.dishes.map((d) => d.main_type))].sort();

const PARSE_SCHEMA = {
  type: "object",
  properties: {
    mode: { type: "string", enum: ["fitness", "wellness"] },
    budget: { type: "string", enum: ["不限", "100以下", "101-300", "301-500", "500以上"] },
    max_spicy: { type: "integer", description: "-1=不限, 0=不辣, 1~5" },
    main_types: { type: "array", items: { type: "string" } },
  },
  required: ["mode", "budget", "max_spicy", "main_types"],
  additionalProperties: false,
};
const PICK_SCHEMA = {
  type: "object",
  properties: {
    picks: {
      type: "array",
      items: {
        type: "object",
        properties: { id: { type: "integer" }, reason: { type: "string" } },
        required: ["id", "reason"],
        additionalProperties: false,
      },
    },
    summary: { type: "string" },
  },
  required: ["picks", "summary"],
  additionalProperties: false,
};

const json = (data, status = 200) => Response.json(data, { status, headers: { "Cache-Control": "no-store" } });

async function askJSON(env, system, user, schema) {
  const r = await fetch("https://api.anthropic.com/v1/messages", {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": env.ANTHROPIC_API_KEY,
      "anthropic-version": "2023-06-01",
      "anthropic-beta": "server-side-fallback-2026-07-01",
    },
    body: JSON.stringify({
      model: env.FITWELL_AI_MODEL || "claude-opus-5-5",
      max_tokens: 4000,
      fallbacks: "default",
      output_config: { effort: "low", format: { type: "json_schema", schema } },
      system,
      messages: [{ role: "user", content: user }],
    }),
  });
  if (!r.ok) throw new Error(`Claude API ${r.status}: ${(await r.text()).slice(0, 200)}`);
  const resp = await r.json();
  if (resp.stop_reason === "refusal") return null;
  return JSON.parse(resp.content.filter((b) => b.type === "text").map((b) => b.text).join(""));
}

async function verifyTurnstile(env, token, ip) {
  if (!env.TURNSTILE_SECRET_KEY) return true; // 沒設定就不檢查
  if (!token) return false;
  const form = new FormData();
  form.append("secret", env.TURNSTILE_SECRET_KEY);
  form.append("response", token);
  if (ip) form.append("remoteip", ip);
  const r = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", { method: "POST", body: form });
  return (await r.json()).success === true;
}

export async function handleCoach(request, env) {
  const body = await request.json().catch(() => ({}));
  const text = String(body.text || "").trim().slice(0, 300);
  if (!text) return json({ detail: "請輸入想吃什麼" }, 400);
  if (!env.ANTHROPIC_API_KEY) return json({ detail: "這個網站沒有開啟 AI" }, 503);
  if (!(await verifyTurnstile(env, body.token, request.headers.get("CF-Connecting-IP")))) {
    return json({ detail: "人機驗證沒有通過，請重新整理再試" }, 403);
  }
  // 同一個 IP 呼叫太頻繁就擋下（wrangler.toml 的 ratelimits 設定）
  if (env.COACH_LIMITER?.limit) {
    const { success } = await env.COACH_LIMITER.limit({ key: request.headers.get("CF-Connecting-IP") || "anon" });
    if (!success) return json({ detail: "問得太快了，請稍等一下再試" }, 429);
  }

  let { query: q, reasons } = E.parseRules(text);
  let source = "rules";
  let ai = true;
  try {
    const parsed = await askJSON(env,
      "你把使用者想吃什麼的描述，轉成竹北遠百餐點推薦機的篩選條件。" +
      "fitness=健身（高蛋白、低油），wellness=養生（清淡、低鹽、少辣）。" +
      "budget 是價格上限區間，沒提到就填「不限」。max_spicy 0=不辣 5=最辣，沒提到填 -1。" +
      `main_types 只能從這些挑（沒指定就空陣列）：${ALL_TYPES.join("、")}。`,
      text, PARSE_SCHEMA);
    if (parsed) {
      q = {
        mode: parsed.mode,
        budget: parsed.budget === "不限" ? null : parsed.budget,
        max_spicy: parsed.max_spicy < 0 ? null : Math.min(5, parsed.max_spicy),
        main_types: parsed.main_types.filter((t) => ALL_TYPES.includes(t)),
      };
      reasons = ["由 AI 理解你的需求"];
      source = "claude";
    }
  } catch (e) {
    console.warn("AI 解析失敗，改用規則版", e.message);
    ai = false;
  }

  // 先多拿一些候選，再讓 AI 挑
  const result = rec.recommend({ ...q, top_n: ai ? 8 : 3 });
  let picks = result.items.slice(0, 3).map((s) => ({ id: s.dish.id, reason: E.ruleReason(s) }));
  let summary = reasons.join("、");

  if (ai && result.items.length) {
    try {
      const cands = result.items.map((s) => ({
        id: s.dish.id, 餐廳: s.dish.restaurant, 餐點: s.dish.name, 價格: s.dish.price_range, 類型: s.dish.main_type,
        烹調: s.dish.cooking, 辣度: s.dish.spicy_level, 標籤: s.dish.tags, 分數: s.score,
      }));
      const out = await askJSON(env,
        "你是給學生和一般民眾用的營養小教練。只能從提供的候選餐點中挑選最多 3 道（用 id），" +
        "每道用一句 30 字以內、親切易懂的繁體中文說明為什麼適合。不要編造營養數字（例如克數、卡路里），" +
        "只根據標籤、烹調方式和分數說明。summary 用一句話回應使用者的需求。",
        `使用者需求：${text}\n候選餐點（已依健康分數排序）：${JSON.stringify(cands)}`, PICK_SCHEMA);
      if (out) {
        const valid = new Set(result.items.map((s) => s.dish.id));
        const aiPicks = out.picks.filter((p) => valid.has(p.id)).slice(0, 3);
        if (aiPicks.length) { picks = aiPicks; summary = out.summary; }
      }
    } catch (e) {
      console.warn("AI 挑選失敗，改用分數排序", e.message);
    }
  }

  const byId = new Map(result.items.map((s) => [s.dish.id, s]));
  return json({
    source,
    query: result.query,
    summary,
    result,
    picks: picks.filter((p) => byId.has(p.id)).map((p) => ({ ...byId.get(p.id), reason: p.reason })),
  });
}
