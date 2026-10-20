// Cloudflare Worker 入口：網頁檔案（web/）由靜態資源直接提供，只有 /api/* 會進到這裡。
import { handleCoach } from "./coach.js";

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    // 告訴網頁：有沒有開 AI 小教練、Turnstile 人機驗證的 site key（公開值）
    if (pathname === "/api/cloud-config") {
      return Response.json(
        { ai: Boolean(env.GEMINI_API_KEY), turnstileSiteKey: env.TURNSTILE_SITE_KEY || null },
        { headers: { "Cache-Control": "no-store" } }
      );
    }
    if (pathname === "/api/coach" && request.method === "POST") return handleCoach(request, env);
    // 其他 /api 一律 404（網頁靠這個判斷「沒有 Python 伺服器」而改用瀏覽器內的推薦引擎）
    if (pathname.startsWith("/api/")) return Response.json({ detail: "not found" }, { status: 404 });
    return env.ASSETS.fetch(request);
  },
};
