// 「脂」點迷津！外食族吃什麼—智慧營養選餐解憂亭 — 前端（不需要編譯，直接由伺服器提供）
"use strict";

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];

// 雙語：文字都從 web/i18n.js 取（I18N.t），菜單詞彙用 I18N.term
const t = (key, vars) => I18N.t(key, vars);
const term = (kind, value) => I18N.term(kind, value);
const modeName = (m) => t("mode." + m);

// 燈號 = 朱印：顏色 + 文字 + 圖示，不只靠顏色
const LIGHT_ICON = { green: "circle-check", yellow: "circle-alert", red: "circle-x" };
const light = (l) => ({ word: t("light." + l), verdict: t("verdict." + l), lot: t("lot." + l), icon: LIGHT_ICON[l] });
const MODE_ICON = { fitness: "dumbbell", wellness: "leaf" };
const GOOD_TAGS = (tag) => tag.startsWith("低") || tag === "高蛋白質";

let META = null;
let STATE = null;
let LAST_RESULT = null;
let LAST_STATUS = null;
let LAST_COACH = null;
let TRAY = loadTray();

const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const icons = () => window.lucide?.createIcons({ icons: lucide.icons, attrs: { "aria-hidden": "true" } });
const ic = (name) => `<i data-lucide="${name}"></i>`;

// ---------------- API ----------------
// 兩種執行方式共用同一組 /api 路徑：
//   伺服器版：uv run fitwell serve（Python，micro:bit 由電腦端程式連線）
//   靜態版：Cloudflare Workers 等純靜態網站（web/local.js 在瀏覽器裡計算，micro:bit 用 Web Serial 連線）
let LOCAL = null;
let CLOUD = {};

async function api(path, body) {
  if (LOCAL) return LOCAL.handle(path, body);
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const r = await fetch(path, opt);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.headers.get("content-type")?.includes("json") ? r.json() : r.text();
}
const setState = (patch) => api("/api/state", patch).then(renderState);

// ---------------- 初始化 ----------------
async function init() {
  I18N.apply();
  trackHeaderHeight();
  icons();
  await detectBackend();
  META = await api("/api/meta");
  buildChips();
  renderState(META.state);
  renderStatus(META);
  renderFormulas();
  renderTray();
  initTabs();
  initVirtualMicrobit();
  listen();
  api("/api/result").then((r) => r.items && renderResult(r, { quiet: true })).catch(() => {});

  $$(".mode").forEach((b) => (b.onclick = () => setState({ mode: b.dataset.mode })));
  $("#go").onclick = () => api("/api/go", {}).catch((e) => showError(e.message));
  $("#tray-clear").onclick = () => { TRAY = []; saveTray(); renderTray(); refreshAddButtons(); };
  $("#coach-form").onsubmit = (e) => { e.preventDefault(); askCoach($("#coach-input").value); };
  $$("[data-example]").forEach((b) => (b.onclick = () => { const text = t(b.dataset.example); $("#coach-input").value = text; askCoach(text); }));
  $("#lang-toggle").onclick = () => I18N.setLang(I18N.lang === "en" ? "zh" : "en");
  I18N.onChange(rerenderLanguage);
  $("#menu-search").oninput = renderMenuRows;
  $("#menu-formula").onchange = loadMenu;
}

// 有 Python 伺服器就用伺服器；否則（Cloudflare 線上版）改用瀏覽器內的本機後端
async function detectBackend() {
  const json = async (url) => {
    const r = await fetch(url, { cache: "no-store" }).catch(() => null);
    return r?.ok && r.headers.get("content-type")?.includes("json") ? r.json() : null;
  };
  if (await json("/api/meta")) return;
  const bundle = await json("data/bundle.json");
  if (!bundle) throw new Error(t("err.bundle"));
  CLOUD = (await json("/api/cloud-config")) || {};
  LOCAL = new FitwellLocal(bundle, CLOUD);
  document.body.classList.add("static-mode");
  initSerialButton();
  initTurnstile();
}

// 靜態版：右上角「連接 micro:bit」按鈕（Web Serial）
function initSerialButton() {
  const btn = $("#mb-connect");
  btn.hidden = false;
  btn.onclick = async () => {
    try {
      if (LOCAL.link.connected) await LOCAL.disconnect();
      else await LOCAL.connect();
    } catch (e) {
      if (e.name !== "NotFoundError") showError(e.message); // NotFoundError = 使用者按了取消
    }
  };
}

// 靜態版的 AI 小教練：Cloudflare Turnstile 人機驗證（有設定 site key 才會出現）
let TURNSTILE_ID = null;
function initTurnstile() {
  if (!CLOUD.ai || !CLOUD.turnstileSiteKey) return;
  window.onTurnstileLoad = renderTurnstile;
  const s = document.createElement("script");
  s.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?onload=onTurnstileLoad&render=explicit";
  s.async = true;
  document.head.append(s);
}
// 驗證框的語言跟著網頁語言；切換語言時重畫
function renderTurnstile() {
  if (!window.turnstile) return;
  if (TURNSTILE_ID !== null) turnstile.remove(TURNSTILE_ID);
  TURNSTILE_ID = turnstile.render("#coach-turnstile", {
    sitekey: CLOUD.turnstileSiteKey, size: "flexible", theme: "light", language: I18N.lang === "en" ? "en" : "zh-tw",
  });
}
function turnstileToken() {
  if (TURNSTILE_ID === null || !window.turnstile) return undefined;
  return turnstile.getResponse(TURNSTILE_ID) || undefined;
}

// 頂部高度會因換行改變，分頁列與左側條件黏在它下面
function trackHeaderHeight() {
  const top = $(".top");
  const set = () => document.documentElement.style.setProperty("--top-h", top.offsetHeight + "px");
  new ResizeObserver(set).observe(top);
  set();
}

// ---------------- 條件 ----------------
function buildChips() {
  // 預算：順序和實體旋鈕一致，「不限」在最後
  const budget = $("#budget-chips");
  budget.innerHTML = "";
  META.price_ranges.forEach((p) => budget.append(chip(esc(term("priceShort", p)), () => setState({ budget: p }), { budget: p })));
  budget.append(chip(t("chip.any"), () => setState({ clear: ["budget"] }), { budget: "" }, "chip-end"));

  // 辣度：不辣 → 1～5 → 都可以
  const spicy = $("#spicy-chips");
  spicy.innerHTML = "";
  spicy.append(chip(t("chip.noSpicy"), () => setState({ max_spicy: 0 }), { spicy: 0 }));
  for (let i = 1; i <= 5; i++) spicy.append(chip(ic("flame") + i, () => setState({ max_spicy: i }), { spicy: i }, "", t("chip.spicyLabel", { n: i })));
  spicy.append(chip(t("chip.spicyAny"), () => setState({ clear: ["max_spicy"] }), { spicy: "any" }, "chip-end"));

  const types = $("#type-chips");
  types.innerHTML = "";
  types.append(chip(t("chip.any"), () => setState({ clear: ["main_types"] }), { type: "" }));
  const excluded = new Set(META.defaults.exclude_types || []);
  META.main_types.filter((ty) => !excluded.has(ty)).forEach((ty) =>
    types.append(chip(esc(term("type", ty)), () => {
      const cur = new Set(STATE.main_types);
      cur.has(ty) ? cur.delete(ty) : cur.add(ty);
      setState({ main_types: [...cur] });
    }, { type: ty }))
  );
  icons();
}

function chip(html, onclick, data, extra = "", label = "") {
  const b = document.createElement("button");
  b.type = "button";
  b.className = "chip " + extra;
  b.innerHTML = html;
  if (label) b.setAttribute("aria-label", label);
  b.onclick = onclick;
  Object.entries(data).forEach(([k, v]) => (b.dataset[k] = v ?? ""));
  return b;
}

function renderState(st) {
  const modeChanged = STATE && STATE.mode !== st.mode;
  STATE = st;
  $$(".mode").forEach((b) => {
    const on = b.dataset.mode === st.mode;
    b.classList.toggle("active", on);
    b.setAttribute("aria-checked", on);
  });
  const mark = (sel, test) => $$(sel).forEach((b) => { const on = test(b); b.classList.toggle("active", on); b.setAttribute("aria-pressed", on); });
  mark("#budget-chips .chip", (b) => (b.dataset.budget || null) === st.budget);
  mark("#spicy-chips .chip", (b) => (b.dataset.spicy === "any" ? st.max_spicy === null : Number(b.dataset.spicy) === st.max_spicy));
  mark("#type-chips .chip", (b) => (b.dataset.type === "" ? st.main_types.length === 0 : st.main_types.includes(b.dataset.type)));
  vmbShow(st.mode === "fitness" ? "F" : "W");
  $("#tray-mode").innerHTML = `${ic(MODE_ICON[st.mode])}${esc(t("tray.mode", { mode: modeName(st.mode) }))}`;
  icons();
  if (modeChanged) {
    flashMode();
    if (TRAY.length) renderTray(); // 餐盤跟著模式重新評估
    $("#menu-formula").value = META.active_formula[st.mode]; // 菜單也換成該模式的公式
    if (MENU.length) loadMenu();
  }
}

// 模式切換時，模式按鈕蓋一下章
function flashMode() {
  if (reduced() || !window.gsap) return;
  gsap.fromTo(".mode.active", { scale: 0.9 }, { scale: 1, duration: 0.35, ease: "back.out(3)" });
}

function renderStatus(s) {
  LAST_STATUS = s;
  const m = s.microbit;
  const mb = $("#mb-status");
  mb.className = "stat " + (m.responding ? "on" : m.connected ? "warn" : "off");
  if (m.webserial) return renderSerialStatus(m, mb, s);
  const mbText = m.responding
    ? t("status.mbOk", { port: esc(m.port), rx: m.rx, tx: m.tx })
    : m.connected
      ? m.webusb?.length
        ? t("status.mbWebusb", { who: esc(m.webusb.join(", ")) })
        : t("status.mbSilent")
      : t("status.mbNone");
  $("#mb-tip").innerHTML = mbText;
  mb.setAttribute("aria-label", mbText.replace(/<br>/g, " "));
  const ai = $("#ai-status");
  ai.className = "stat " + (s.ai ? "on" : "off");
  const aiText = s.ai ? t("status.aiOn") : t("status.aiOff");
  $("#ai-tip").textContent = aiText;
  ai.setAttribute("aria-label", aiText);
}

// 靜態版的 micro:bit 狀態（Web Serial）
function renderSerialStatus(m, mb, s) {
  const btn = $("#mb-connect");
  btn.innerHTML = m.connected ? `${ic("unplug")}<span>${t("status.disconnect")}</span>` : `${ic("usb")}<span>${t("status.connect")}</span>`;
  btn.classList.toggle("ghost-ink", m.connected);
  btn.disabled = !m.supported;
  const mbText = !m.supported
    ? t("status.wsUnsupported")
    : m.responding
      ? t("status.wsOk", { rx: m.rx, tx: m.tx })
      : m.connected
        ? t("status.wsSilent")
        : t("status.wsNone");
  mb.className = "stat " + (m.responding ? "on" : m.connected ? "warn" : "off");
  $("#mb-tip").innerHTML = mbText;
  mb.setAttribute("aria-label", mbText.replace(/<br>/g, " "));
  const ai = $("#ai-status");
  ai.className = "stat " + (s.ai ? "on" : "off");
  const aiText = s.ai ? t("status.aiOn") : t("status.aiOff");
  $("#ai-tip").textContent = aiText;
  ai.setAttribute("aria-label", aiText);
  icons();
}

// ---------------- 即時事件（micro:bit 按鍵也會推到這裡） ----------------
function listen() {
  if (LOCAL) { LOCAL.on(onEvent); return; }
  const es = new EventSource("/api/events");
  es.onmessage = (e) => onEvent(JSON.parse(e.data));
}
function onEvent({ type, data }) {
  if (type === "status") { renderStatus(data); if (data.state) renderState(data.state); }
  if (type === "state") renderState(data);
  if (type === "result") { switchTab("recommend"); renderResult(data); }
  if (type === "microbit") vmbLog("← " + data.line);
}

// ---------------- 推薦結果（求籤） ----------------
function renderResult(r, { quiet = false } = {}) {
  LAST_RESULT = r;
  vmbLight(r.light);
  vmbShow(String(r.items.length));
  const L = light(r.light);
  const mode = modeName(r.query.mode);
  $("#result-title").innerHTML = r.items.length
    ? `${esc(t("result.title", { mode, n: r.items.length }))}<span class="dot ${r.light}">${L.word}</span>`
    : esc(t("result.none", { mode }));
  $("#result-formula").hidden = false;
  const f = META.formulas[r.formula_id];
  $("#result-formula-text").innerHTML =
    `<b>${esc(I18N.formula(r.formula_id, { label: r.formula_label }).label)}</b><br>` +
    esc(t("result.score", { text: I18N.formulaText(f?.terms, r.formula_text) })) +
    (r.source === "microbit" ? `<br>${t("result.byMicrobit")}` : "");

  renderFlow(r.steps, quiet);

  $("#hints").innerHTML = r.hints.length
    ? `<div class="hint">${ic("lightbulb")}<div>${esc(t("result.hintsHead", { n: r.items.length }))}<ul>${hintTexts(r).map((h) => `<li>${esc(h)}</li>`).join("")}</ul></div></div>`
    : "";

  const cards = $("#cards");
  cards.innerHTML = "";
  r.items.forEach((s, i) => cards.append(slip(s, { rank: i })));
  if (!r.items.length) cards.innerHTML = `<div class="slips-empty">${ic("search-x")}<p>${t("slips.none")}</p></div>`;
  icons();
  if (!quiet) drawLots(cards);
}

// 推薦引擎的提示有代碼（hint_codes），英文版依代碼翻譯；中文版直接用原句
function hintTexts(r) {
  if (I18N.lang !== "en" || !r.hint_codes) return r.hints;
  return r.hint_codes.map((c, i) =>
    c.code === "budget" ? t("hint.budget", { value: term("price", c.value), n: c.n }) :
    ["spicy", "types", "restaurants", "none"].includes(c.code) ? t("hint." + c.code, c) : r.hints[i]);
}

// 篩選步驟名稱（引擎傳回的是中文）
const STEP_KEYS = { "計分排序": "step.score", "預算": "step.budget", "辣度": "step.spicy", "主餐類型": "step.type", "餐廳": "step.restaurant" };
function stepName(step) {
  const top = /^取前 (\d+) 名$/.exec(step);
  if (top) return t("step.top", { n: top[1] });
  return STEP_KEYS[step] ? t(STEP_KEYS[step]) : step;
}

function renderFlow(steps, quiet = false) {
  const flow = $("#flow");
  const old = $$("li b", flow).map((b) => Number(b.textContent) || 0);
  flow.innerHTML = steps.map((s, i) => `
    <li class="${i && s.remaining < steps[i - 1].remaining ? "cut" : ""}" title="${esc(stepName(s.step))}">
      ${esc(i < 5 ? t("flow." + i) : stepName(s.step))}<b>${old[i] ?? 0}</b></li>`).join("");
  $$("li b", flow).forEach((b, i) => (quiet ? (b.textContent = steps[i].remaining) : rollNumber(b, steps[i].remaining)));
}

// 數字滾動到新值
function rollNumber(el, to) {
  if (reduced() || !window.gsap) { el.textContent = to; return; }
  const o = { v: Number(el.textContent) || 0 };
  gsap.to(o, { v: to, duration: 0.7, ease: "power2.out", snap: { v: 1 }, onUpdate: () => (el.textContent = o.v) });
}

// 招牌動作：籤筒搖一搖 → 三支籤依序升起 → 朱印蓋下
function drawLots(container) {
  const slips = $$(".slip", container);
  if (!slips.length || reduced() || !window.gsap) return;
  const tl = gsap.timeline({ defaults: { ease: "power3.out" } });
  tl.to(".go-tube", { rotation: 14, duration: 0.07, repeat: 5, yoyo: true, ease: "sine.inOut" })
    .to(".go-tube .sticks", { y: -5, duration: 0.12, yoyo: true, repeat: 1 }, "<")
    .set(".go-tube", { rotation: 0 })
    .from(slips, { ...fromTube(slips, container), autoAlpha: 0, rotation: (i) => [-2.5, 2, -1.5][i % 3], duration: 0.6, stagger: 0.14 }, "-=0.05")
    .from($$(".seal", container), { scale: 1.9, autoAlpha: 0, duration: 0.32, ease: "back.out(2.2)", stagger: 0.14 }, "-=0.3");
}

// 推薦頁的籤從籤筒飛出；其他頁（AI 小教練）從下方升起
function fromTube(slips, container) {
  const tube = $(".go-tube");
  const r = tube?.getBoundingClientRect();
  if (container.id !== "cards" || !r?.width) return { y: 70 };
  const at = (el, k) => { const b = el.getBoundingClientRect(); return k === "x" ? r.left + r.width / 2 - (b.left + b.width / 2) : r.top - b.top; };
  return { x: (i) => at(slips[i], "x"), y: (i) => at(slips[i], "y"), scale: 0.25, transformOrigin: "50% 0%" };
}

// ---------------- 籤（推薦、餐盤、AI 共用） ----------------
function slip(s, { rank, reason, inTrayMode } = {}) {
  const d = s.dish;
  const L = light(s.light);
  const isFirst = rank === 0;
  const el = document.createElement("article");
  el.className = "slip" + (isFirst ? " first" : "");
  el.dataset.id = d.id;
  const tags = d.tags.map((tag) => `<span class="${GOOD_TAGS(tag) ? "good" : "bad"}">${esc(term("tag", tag))}</span>`).join("");
  const sign = (n) => (n > 0 ? "+" : "") + n;
  el.innerHTML = `
    <div class="slip-band"><span>${rank !== undefined ? esc(t("slip.rank", { cn: I18N.CN_NUM[rank], n: rank + 1 })) : esc(term("type", d.main_type))}</span><span>${L.lot}</span></div>
    <div class="slip-body">
      <div class="slip-rest">${ic("store")}${esc(d.restaurant)}</div>
      <h3 class="slip-name">${esc(d.name)}</h3>
      <div class="slip-meta">
        <span>${ic("wallet")}${esc(d.price_range ? term("price", d.price_range) : t("slip.priceUnknown"))}</span>
        <span>${esc(term("type", d.main_type))}</span>
        ${d.cooking ? `<span>${ic("chef-hat")}${esc(term("cooking", d.cooking))}</span>` : ""}
        <span>${d.spicy_level ? `${ic("flame")}${esc(t("slip.spicy", { n: d.spicy_level }))}` : esc(t("slip.notSpicy"))}</span>
        ${tags}
      </div>
      ${reason ? `<div class="slip-reason">${ic("message-circle")}<span>${esc(reason)}</span></div>` : ""}
      <div class="slip-score"><b>${s.score}</b>${t("slip.pts")}
        <span class="info" tabindex="0" aria-label="${esc(t("slip.howScore"))}">${ic("calculator")}
          <span class="tipcard" role="tooltip">${s.terms.map((x) => `${esc(t("slip.term", { label: termLabel(x), w: x.weight, f: x.factor }))}<b>${sign(x.points)}</b>`).join("<br>")}<br>${t("slip.total")} <b>${s.score}</b></span>
        </span>
        <div class="seal" data-light="${s.light}" role="img" aria-label="${L.word}，${L.verdict}">${ic(L.icon)}<span>${L.word}<br>${L.verdict}</span></div>
      </div>
      <div class="terms" style="--n:${s.terms.length}">${s.terms.map((x) => `<div>${esc(termLabel(x))}<b class="${x.points < 0 ? "neg" : ""}">${sign(x.points)}</b></div>`).join("")}</div>
      <div class="slip-foot"></div>
    </div>`;
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "ghost add";
  if (inTrayMode) {
    btn.innerHTML = `${ic("minus")}${t("slip.remove")}`;
    btn.onclick = () => { TRAY = TRAY.filter((t) => t.id !== d.id); saveTray(); renderTray(); refreshAddButtons(); };
  } else {
    setAddButton(btn, d);
  }
  $(".slip-foot", el).append(btn);
  return el;
}

// 計分項目名稱（油脂、蛋白質…）
const termLabel = (x) => term("term", x.key) || x.label;

function setAddButton(btn, d) {
  const inTray = TRAY.some((x) => x.id === d.id);
  btn.innerHTML = inTray ? `${ic("check")}${t("slip.inTray")}` : `${ic("plus")}${t("slip.add")}`;
  btn.disabled = inTray;
  btn.onclick = () => { addToTray(d); setAddButton(btn, d); icons(); };
}

// 餐盤變動後，推薦與 AI 的「加入餐盤」按鈕跟著更新
function refreshAddButtons() {
  const all = [...(LAST_RESULT?.items || []), ...(COACH_PICKS || [])];
  $$("#cards .slip, #coach-out .slip").forEach((el) => {
    const s = all.find((x) => x.dish.id === Number(el.dataset.id));
    if (s) setAddButton($(".add", el), s.dish);
  });
  if (MENU.length) renderMenuRows();
  icons();
}

// ---------------- 餐盤 ----------------
function loadTray() { try { return JSON.parse(localStorage.getItem("fitwell-tray") || "[]"); } catch { return []; } }
function saveTray() { try { localStorage.setItem("fitwell-tray", JSON.stringify(TRAY)); } catch {} }
function addToTray(d) {
  if (!TRAY.some((t) => t.id === d.id)) TRAY.push({ id: d.id, name: d.name });
  saveTray();
  renderTray();
}
async function renderTray() {
  const count = $("#tray-count");
  if (count.textContent !== String(TRAY.length)) {
    count.textContent = TRAY.length;
    if (!reduced() && window.gsap) gsap.fromTo(count, { scale: 1.5 }, { scale: 1, duration: 0.4, ease: "back.out(3)" });
  }
  const items = $("#tray-items");
  const seal = $("#tray-seal");
  const meter = $("#tray-meter");
  if (!TRAY.length) {
    $("#tray-summary").textContent = t("tray.empty");
    seal.dataset.light = "";
    seal.innerHTML = `${ic("utensils")}<span>${t("tray.emptySeal")}</span>`;
    meter.style.width = "0";
    $("#tray-warnings").innerHTML = "";
    items.innerHTML = "";
    icons();
    return;
  }
  const res = await api("/api/tray", { ids: TRAY.map((t) => t.id), mode: STATE?.mode || "fitness" });
  const L = light(res.light);
  vmbLight(res.light);
  seal.dataset.light = res.light;
  seal.setAttribute("aria-label", `${L.word}，${L.verdict}`);
  seal.innerHTML = `${ic(L.icon)}<span>${L.word}<br>${L.verdict}</span>`;
  meter.dataset.light = res.light;
  meter.style.width = Math.max(0, Math.min(100, res.percent)) + "%";
  $("#tray-summary").innerHTML = t("tray.summary", { n: TRAY.length, avg: res.average, p: res.percent });
  const warnings = I18N.lang === "en" && res.warning_codes ? res.warning_codes.map((c) => t("warn." + c.code, c)) : res.warnings;
  $("#tray-warnings").innerHTML = warnings.map((w) => `<li>${ic("triangle-alert")}<span>${esc(w)}</span></li>`).join("");
  items.innerHTML = "";
  res.items.forEach((s) => items.append(slip(s, { inTrayMode: true })));
  icons();
}

// ---------------- AI 小教練 ----------------
let COACH_PICKS = [];
async function askCoach(text) {
  if (!text.trim()) return;
  const out = $("#coach-out");
  const token = turnstileToken();
  if (TURNSTILE_ID !== null && !token) {
    // 線上版有人機驗證：還沒勾選就先提醒，不要偷偷改用規則版
    out.innerHTML = `<div class="hint">${ic("shield-check")}<div>${esc(t("coach.verify"))}</div></div>`;
    icons();
    return;
  }
  out.innerHTML = `<p class="thinking">${ic("loader")}${t("coach.thinking")}</p>`;
  icons();
  try {
    const r = await api("/api/coach", { text, token, lang: I18N.lang });
    if (TURNSTILE_ID !== null) turnstile.reset(TURNSTILE_ID); // 每個驗證只能用一次
    renderCoach(r);
    drawLots($("#coach-out .slips"));
  } catch (e) {
    out.innerHTML = `<div class="hint">${ic("circle-x")}<div>${esc(t("coach.error", { msg: e.message }))}</div></div>`;
    icons();
  }
}

function renderCoach(r) {
  LAST_COACH = r;
  COACH_PICKS = r.picks;
  const out = $("#coach-out");
  const fallback = r.fallback_note ? t("coach.fallback", { msg: r.fallback_note }) : "";
  out.innerHTML = `<div class="coach-summary">${ic(r.source === "rules" ? "search" : "sparkles")}<span>${esc(fallback + coachSummary(r))}</span></div>`;
  if (!r.picks.length) out.innerHTML += `<div class="hint">${ic("lightbulb")}<div>${esc(t("coach.none"))}${hintTexts(r.result).map(esc).join(I18N.lang === "en" ? "; " : "；")}</div></div>`;
  const cards = document.createElement("div");
  cards.className = "slips";
  r.picks.forEach((p, i) => cards.append(slip(p, { rank: i, reason: coachReason(r, p) })));
  out.append(cards);
  icons();
}

// 規則版（或 AI 只負責理解條件時）的說明是中文；英文介面改用條件重新組成
function coachSummary(r) {
  if (I18N.lang !== "en" || !/[一-龥]/.test(r.summary)) return r.summary;
  const q = r.query || {};
  const parts = [`${modeName(q.mode || "fitness")} mode`];
  if (q.budget) parts.push(`budget ${term("price", q.budget)}`);
  if (q.max_spicy === 0) parts.push("not spicy");
  else if (q.max_spicy != null) parts.push(`spice up to ${q.max_spicy}`);
  if (q.main_types?.length) parts.push(q.main_types.map((x) => term("type", x)).join(", "));
  return (r.source === "rules" ? "Keyword match: " : "Understood by AI: ") + parts.join(" · ");
}

function coachReason(r, p) {
  if (I18N.lang !== "en" || !/[一-龥]/.test(p.reason || "")) return p.reason;
  const d = p.dish;
  const bits = d.tags.filter(GOOD_TAGS).map((x) => term("tag", x));
  if (d.cooking) bits.push(term("cooking", d.cooking).toLowerCase());
  return `${bits.join(", ") || "High weighted score"} (${p.score} pts)`;
}

// ---------------- 全部菜單 ----------------
let MENU = [];
async function loadMenu() {
  const fid = $("#menu-formula").value;
  const mode = META.formulas[fid].mode;
  MENU = (await api(`/api/dishes?mode=${mode}&formula=${fid}`)).items;
  renderMenuRows();
}
function renderMenuRows() {
  const q = $("#menu-search").value.trim();
  const ql = q.toLowerCase();
  const rows = MENU.filter((s) => !q || (s.dish.restaurant + s.dish.name + s.dish.main_type + term("type", s.dish.main_type)).toLowerCase().includes(ql));
  $("#menu-count").textContent = t("menu.count", { n: rows.length });
  const tb = $("#menu-table tbody");
  tb.innerHTML = rows.map((s) => {
    const d = s.dish;
    const inTray = TRAY.some((x) => x.id === d.id);
    const tags = d.tags.map((x) => term("tag", x)).join(I18N.lang === "en" ? ", " : "、");
    return `<tr><td><span class="dot ${s.light}">${light(s.light).word}</span></td><td class="num"><b>${s.score}</b></td><td>${esc(d.restaurant)}</td>
      <td class="wrap">${esc(d.name)}</td><td>${esc(term("price", d.price_range))}</td><td>${esc(term("type", d.main_type))}</td><td>${esc(term("cooking", d.cooking))}</td>
      <td class="num">${d.spicy_level || ""}</td><td class="wrap">${esc(tags)}</td>
      <td><button type="button" class="mini" data-add="${d.id}" ${inTray ? "disabled" : ""} aria-label="${esc(t(inTray ? "slip.inTray" : "slip.add"))}: ${esc(d.name)}">${ic(inTray ? "check" : "plus")}${t("menu.addShort")}</button></td></tr>`;
  }).join("");
  $$("[data-add]", tb).forEach((b) => (b.onclick = () => {
    const s = MENU.find((m) => m.dish.id === Number(b.dataset.add));
    addToTray(s.dish);
    refreshAddButtons();
  }));
  icons();
}

function renderFormulas() {
  const sel = $("#menu-formula");
  const keep = sel.value;
  sel.innerHTML = Object.entries(META.formulas).map(([k, f]) => `<option value="${k}">${esc(I18N.formula(k, f).label)}</option>`).join("");
  sel.value = keep || META.active_formula[STATE?.mode || "fitness"];
  $("#formulas").innerHTML = Object.entries(META.formulas).map(([k, f]) => `
    <div class="fbox">
      <div class="fbox-head">${ic(MODE_ICON[f.mode])}${esc(I18N.formula(k, f).label)}
        ${Object.values(META.active_formula).includes(k) ? `<span class="on">${t("formula.inUse")}</span>` : ""}
        <span class="info" tabindex="0" aria-label="${esc(t("formula.info"))}">${ic("info")}<span class="tipcard tipcard-end" role="tooltip">${esc(I18N.formula(k, f).note)}</span></span>
      </div>
      <code>${esc(t("result.score", { text: I18N.formulaText(f.terms, f.text) }))}</code>
      <div class="lights"><span class="dot green">${t("formula.green", { n: f.lights.green })}</span><span class="dot yellow">${t("formula.yellow", { n: f.lights.yellow })}</span><span class="dot red">${t("formula.red")}</span></div>
    </div>`).join("");
  icons();
}

// ---------------- 分頁 ----------------
function initTabs() {
  $$(".tab").forEach((t) => (t.onclick = () => switchTab(t.dataset.tab)));
}
function switchTab(name) {
  $$(".tab").forEach((t) => {
    const on = t.dataset.tab === name;
    t.classList.toggle("active", on);
    t.setAttribute("aria-selected", on);
  });
  $$(".panel").forEach((p) => p.classList.toggle("active", p.id === "tab-" + name));
  if (name === "menu" && !MENU.length) loadMenu();
  if (name === "tray") renderTray();
  if (name === "about" && !$("#report").textContent) api("/api/report").then((t) => ($("#report").textContent = t));
}

// ---------------- 虛擬 micro:bit ----------------
const FONT = {
  F: ["11111", "10000", "11110", "10000", "10000"],
  W: ["10001", "10001", "10101", "11011", "10001"],
  A: ["01110", "10001", "11111", "10001", "10001"],
  0: ["01110", "10011", "10101", "11001", "01110"],
  1: ["00100", "01100", "00100", "00100", "01110"],
  2: ["11100", "00010", "01100", "10000", "11110"],
  3: ["11110", "00010", "00100", "10010", "01100"],
  4: ["00110", "01010", "10010", "11111", "00010"],
  5: ["11111", "10000", "11110", "00001", "11110"],
  6: ["00010", "00100", "01110", "10001", "01110"],
  7: ["11111", "00010", "00100", "01000", "10000"],
  8: ["01110", "10001", "01110", "10001", "01110"],
  9: ["01110", "10001", "01110", "00100", "01000"],
};
function initVirtualMicrobit() {
  const grid = $("#vmb-grid");
  for (let i = 0; i < 25; i++) grid.append(document.createElement("i"));
  const send = (line) => { vmbLog("→ " + line); return api("/api/microbit/simulate", { line }); };
  $("#vmb-a").onclick = () => send(STATE.mode === "fitness" ? "MODE:WELLNESS" : "MODE:FITNESS");
  $("#vmb-b").onclick = () => send("GO");
  // 模擬預算旋鈕：和實體旋鈕同順序循環，最後一格是「不限」（點陣顯示 A）
  $("#vmb-ab").onclick = () => {
    const n = META.price_ranges.length;
    const cur = STATE.budget === null ? n : META.price_ranges.indexOf(STATE.budget);
    const next = (cur + 1) % (n + 1);
    vmbShow(next === n ? "A" : String(next + 1));
    send(next === n ? "BUDGET:ANY" : "BUDGET:" + next);
  };
  $("#vmb-toggle").onclick = toggleVmb;
  vmbShow(STATE.mode === "fitness" ? "F" : "W");
}

function toggleVmb() {
  const btn = $("#vmb-toggle");
  const body = $("#vmb-body");
  const open = btn.getAttribute("aria-expanded") !== "true";
  btn.setAttribute("aria-expanded", open);
  if (!window.gsap || reduced()) { body.hidden = !open; return; }
  gsap.killTweensOf(body);
  if (open) {
    body.hidden = false;
    gsap.fromTo(body, { autoAlpha: 0, y: 18, scale: 0.9 }, { autoAlpha: 1, y: 0, scale: 1, duration: 0.34, ease: "power3.out" });
    gsap.from($$(".vmb-board, .vmb-ab, .vmb-leds, .vmb-log", body), { autoAlpha: 0, y: 8, duration: 0.25, stagger: 0.04, delay: 0.08, ease: "power2.out" });
  } else {
    gsap.to(body, { autoAlpha: 0, y: 14, scale: 0.92, duration: 0.22, ease: "power2.in", onComplete: () => (body.hidden = true) });
  }
}
function vmbShow(ch) {
  const rows = FONT[ch] || FONT[0];
  $$("#vmb-grid i").forEach((el, i) => el.classList.toggle("on", rows[Math.floor(i / 5)][i % 5] === "1"));
}
function vmbLight(light) {
  ["green", "yellow", "red"].forEach((c) => $("#led-" + c).classList.toggle("on", c === light));
}
function vmbLog(s) {
  const log = $("#vmb-log");
  log.textContent = (s + "\n" + log.textContent).split("\n").slice(0, 3).join("\n");
}

// 切換語言：固定文字由 I18N.apply 換好，這裡重畫程式產生的部分
function rerenderLanguage() {
  icons();
  buildChips();
  renderState(STATE);
  if (LAST_STATUS) renderStatus(LAST_STATUS);
  renderFormulas();
  renderTray();
  if (LAST_RESULT) renderResult(LAST_RESULT, { quiet: true });
  if (MENU.length) renderMenuRows();
  if (LAST_COACH) renderCoach(LAST_COACH);
  if (TURNSTILE_ID !== null) renderTurnstile();
}

function showError(msg) {
  $(".fatal")?.remove();
  $("main").insertAdjacentHTML("beforebegin", `<div class="fatal" role="alert">${esc(msg)}</div>`);
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

init().catch((e) => {
  document.body.insertAdjacentHTML("afterbegin", `<div class="fatal" role="alert">${t("err.server", { msg: esc(e.message) })}</div>`);
});
