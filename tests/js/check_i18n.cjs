// 檢查雙語字典：中英文的 key 一樣多、網頁用到的 key 都存在、菜單詞彙都有英文。
// 執行：node tests/js/check_i18n.cjs（pytest 會自動呼叫）
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "../..");
const src = fs.readFileSync(path.join(root, "web/i18n.js"), "utf8");

// 在沙盒裡執行 i18n.js，取出字典
const store = {};
const sandbox = {
  location: { search: "" },
  localStorage: { getItem: () => null, setItem: () => {} },
  document: { querySelectorAll: () => [], querySelector: () => null, documentElement: {}, title: "" },
};
sandbox.globalThis = sandbox;
new Function("globalThis", "window", "location", "localStorage", "document", src)(
  sandbox, sandbox, sandbox.location, sandbox.localStorage, sandbox.document);
const I = sandbox.I18N;

const errors = [];
// 1. 兩種語言的 key 相同：從原始碼抓出 zh、en 物件的 key
const block = (name) => src.slice(src.indexOf(`const ${name} = {`), src.indexOf("};", src.indexOf(`const ${name} = {`)));
const keysOf = (name) => new Set([...block(name).matchAll(/"([\w.]+)":/g)].map((m) => m[1]));
const zh = keysOf("zh"), en = keysOf("en");
for (const k of zh) if (!en.has(k)) errors.push(`英文缺少 ${k}`);
for (const k of en) if (!zh.has(k)) errors.push(`中文缺少 ${k}`);

// 2. index.html 與 app.js 用到的 key 都存在
const html = fs.readFileSync(path.join(root, "web/index.html"), "utf8");
const app = fs.readFileSync(path.join(root, "web/app.js"), "utf8");
const used = new Set([
  ...[...html.matchAll(/data-i18n(?:-html)?="([\w.]+)"/g)].map((m) => m[1]),
  ...[...html.matchAll(/data-i18n-attr="([^"]+)"/g)].flatMap((m) => m[1].split(";").map((p) => p.split(":")[1])),
  ...[...html.matchAll(/data-example="([\w.]+)"/g)].map((m) => m[1]),
  ...[...app.matchAll(/\bt\("([\w.]+)"/g)].map((m) => m[1]),
]);
// t("mode." + m) 這類組合出來的 key：列出所有可能值逐一檢查
const families = {
  "mode.": ["fitness", "wellness"], "light.": ["green", "yellow", "red"], "verdict.": ["green", "yellow", "red"],
  "lot.": ["green", "yellow", "red"], "flow.": ["0", "1", "2", "3", "4"],
  "hint.": ["budget", "spicy", "types", "restaurants", "none"], "warn.": ["fat", "salt", "starch", "protein", "spicy", "empty"],
};
for (const k of used) {
  if (k.endsWith(".")) {
    if (!families[k]) errors.push(`無法檢查的組合 key：${k}`);
    else families[k].forEach((v) => { if (!zh.has(k + v)) errors.push(`缺少 ${k + v}`); });
  } else if (!zh.has(k)) errors.push(`網頁用到不存在的 key：${k}`);
}

// 3. 菜單詞彙（類型、烹調方式、標籤、價格）都有英文
const bundle = JSON.parse(fs.readFileSync(path.join(root, "web/data/bundle.json"), "utf8"));
I.setLang = I.setLang; // 不呼叫（沙盒沒有 DOM）
sandbox.location.search = "?lang=en";
new Function("globalThis", "window", "location", "localStorage", "document", src)(
  sandbox, sandbox, sandbox.location, sandbox.localStorage, sandbox.document);
const E = sandbox.I18N;
const cjk = /[一-鿿]/;
const check = (kind, v) => { const out = E.term(kind, v); if (cjk.test(out)) errors.push(`${kind}「${v}」沒有英文`); };
for (const d of bundle.dishes) {
  check("type", d.main_type);
  if (d.cooking) check("cooking", d.cooking);
  d.tags.forEach((x) => check("tag", x));
  if (d.price_range) check("price", d.price_range);
}
for (const id of Object.keys(bundle.config.formulas)) if (cjk.test(E.formula(id, {}).label || "中")) errors.push(`公式 ${id} 沒有英文名稱`);

const uniq = [...new Set(errors)];
if (uniq.length) { console.error(uniq.join("\n")); process.exit(1); }
console.log(`雙語字典完整（${zh.size} 個 key，網頁用到 ${used.size} 個）`);
