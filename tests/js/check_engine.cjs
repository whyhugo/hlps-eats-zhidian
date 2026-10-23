// 比對 web/engine.js（JS 版）和 Python 版的推薦結果（tests/golden_engine.json）。
// 執行：node tests/js/check_engine.cjs（pytest 會自動呼叫）
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "../..");
require(path.join(root, "web/engine.js"));
const { Recommender, parseRules } = globalThis.FitwellEngine;
const bundle = JSON.parse(fs.readFileSync(path.join(root, "web/data/bundle.json"), "utf8"));
const golden = JSON.parse(fs.readFileSync(path.join(root, "tests/golden_engine.json"), "utf8"));
const rec = new Recommender(bundle.dishes, bundle.config);

let fail = 0;
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const check = (label, got, want) => {
  if (!same(got, want)) {
    fail++;
    if (fail <= 10) console.error(`✗ ${label}\n  JS:     ${JSON.stringify(got)}\n  Python: ${JSON.stringify(want)}`);
  }
};

for (const g of golden.recommend) {
  const r = rec.recommend(g.query);
  check(`recommend ${JSON.stringify(g.query)}`, {
    ids: r.items.map((s) => s.dish.id), scores: r.items.map((s) => s.score), lights: r.items.map((s) => s.light),
    light: r.light, percent: r.percent, candidates: r.candidates, steps: r.steps, hints: r.hints, hint_codes: r.hint_codes,
    formula_id: r.formula_id, formula_text: r.formula_text,
  }, g.result);
}
for (const g of golden.tray) {
  const t = rec.evaluateTray(g.ids, g.mode);
  check(`tray ${g.ids} ${g.mode}`, { average: t.average, light: t.light, percent: t.percent, warnings: t.warnings, warning_codes: t.warning_codes },
    { average: g.average, light: g.light, percent: g.percent, warnings: g.warnings, warning_codes: g.warning_codes });
}
for (const g of golden.parse) {
  const p = parseRules(g.text);
  check(`parse ${g.text}`, { query: p.query, reasons: p.reasons }, { query: g.query, reasons: g.reasons });
}
const total = golden.recommend.length + golden.tray.length + golden.parse.length;
if (fail) { console.error(`${fail}/${total} 不一致`); process.exit(1); }
console.log(`JS 與 Python 結果一致（${total} 項）`);
