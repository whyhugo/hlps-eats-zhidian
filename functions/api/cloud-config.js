// 告訴網頁：這個 Cloudflare 部署有沒有開 AI 小教練、Turnstile 人機驗證的 site key（公開值）
export function onRequestGet({ env }) {
  return Response.json(
    { ai: Boolean(env.ANTHROPIC_API_KEY), turnstileSiteKey: env.TURNSTILE_SITE_KEY || null },
    { headers: { "Cache-Control": "no-store" } }
  );
}
