// 推薦引擎（JS 版）— 和 src/fitwell/scoring.py、recommend.py、ai_coach.py 的規則版一模一樣。
// 純靜態網頁（Cloudflare Pages）在瀏覽器裡直接計算，不需要 Python 伺服器。
// 改這裡就要一起改 Python 版；tests/test_engine_js.py 會檢查兩邊算出的結果完全相同。
"use strict";

(function (root) {
  const TERM_LABELS = { fat: "油脂", protein: "蛋白質", salt: "鹽分", starch: "澱粉", spicy: "辣度", cooking: "烹調" };
  const MODES = { fitness: "健身", wellness: "養生" };

  // Python 的 round()：剛好在一半時取偶數（banker's rounding）
  function pyRound(x, nd = 0) {
    const m = 10 ** nd;
    const y = x * m;
    const f = Math.floor(y);
    if (y - f === 0.5) return (f % 2 === 0 ? f : f + 1) / m;
    return Number(x.toFixed(nd));
  }

  const weights = (d) => ({ fat: d.fat, protein: d.protein, salt: d.salt, starch: d.starch, spicy: d.spicy, cooking: d.cooking_w });

  class Scorer {
    constructor(config) { this.config = config; }

    formulaId(mode, override) {
      const fid = override || this.config.active_formula[mode];
      const f = this.config.formulas[fid];
      if (!f) throw new Error(`找不到公式：${fid}`);
      if (f.mode !== mode) throw new Error(`公式 ${fid} 是給 ${f.mode} 模式用的，不是 ${mode}`);
      return fid;
    }

    score(dish, fid) {
      const f = this.config.formulas[fid];
      const w = weights(dish);
      const terms = Object.entries(f.terms).map(([k, factor]) => ({
        key: k, label: TERM_LABELS[k] || k, weight: w[k], factor, points: w[k] * factor,
      }));
      const total = terms.reduce((a, t) => a + t.points, 0);
      return { dish, score: total, light: this.light(total, fid), terms };
    }

    light(score, fid) {
      const th = this.config.lights[fid];
      if (score >= th.green) return "green";
      if (score >= th.yellow) return "yellow";
      return "red";
    }

    formulaText(fid) {
      const parts = Object.entries(this.config.formulas[fid].terms).map(
        ([k, factor]) => `${factor < 0 ? "−" : "+"} ${TERM_LABELS[k] || k}×${Math.abs(factor)}`
      );
      const text = parts.join(" ");
      return text.startsWith("+ ") ? text.slice(2) : text;
    }
  }

  class Recommender {
    constructor(dishes, config) {
      this.dishes = dishes.filter((d) => d.duplicate_of == null);
      this.config = config;
      this.scorer = new Scorer(config);
      this.priceRanges = config.price_ranges;
      this._percentCache = {};
    }

    overBudget(d, budget) {
      if (!budget) return false;
      if (!d.price_range) return true;
      return this.priceRanges.indexOf(d.price_range) > this.priceRanges.indexOf(budget);
    }
    tooSpicy(d, maxSpicy) { return maxSpicy != null && d.spicy_level > maxSpicy; }
    typeMismatch(d, q, exclude) { return q.main_types.length ? !q.main_types.includes(d.main_type) : exclude.includes(d.main_type); }
    restaurantMismatch(d, q) { return q.restaurants.length > 0 && !q.restaurants.includes(d.restaurant); }
    priceIdx(d) { const i = this.priceRanges.indexOf(d.price_range); return i < 0 ? this.priceRanges.length : i; }

    normalize(q) {
      return {
        mode: q.mode || "fitness",
        budget: q.budget || null,
        max_spicy: q.max_spicy ?? null,
        main_types: q.main_types || [],
        exclude_types: q.exclude_types ?? null,
        restaurants: q.restaurants || [],
        top_n: q.top_n || null,
        formula: q.formula || null,
      };
    }

    recommend(query) {
      const q = this.normalize(query);
      if (!MODES[q.mode]) throw new Error(`模式只能是 ${Object.keys(MODES)}`);
      if (q.budget && !this.priceRanges.includes(q.budget)) throw new Error(`預算只能是 ${this.priceRanges}`);
      const defaults = this.config.defaults;
      const topN = q.top_n || defaults.top_n;
      const exclude = q.exclude_types == null ? defaults.exclude_types : q.exclude_types;
      const fid = this.scorer.formulaId(q.mode, q.formula);
      const formula = this.config.formulas[fid];

      // 1~2. 計分、依分數排序（同分時：辣度低、價格低的優先，再依編號）
      const scored = this.dishes.map((d) => this.scorer.score(d, fid));
      scored.sort((a, b) => b.score - a.score || a.dish.spicy_level - b.dish.spicy_level ||
        this.priceIdx(a.dish) - this.priceIdx(b.dish) || a.dish.id - b.dish.id);

      // 3. 依序過濾，記錄每一步剩幾道
      const steps = [{ step: "計分排序", remaining: scored.length }];
      let pool = scored.filter((s) => !this.overBudget(s.dish, q.budget));
      steps.push({ step: "預算", remaining: pool.length });
      pool = pool.filter((s) => !this.tooSpicy(s.dish, q.max_spicy));
      steps.push({ step: "辣度", remaining: pool.length });
      pool = pool.filter((s) => !this.typeMismatch(s.dish, q, exclude));
      steps.push({ step: "主餐類型", remaining: pool.length });
      if (q.restaurants.length) {
        pool = pool.filter((s) => !this.restaurantMismatch(s.dish, q));
        steps.push({ step: "餐廳", remaining: pool.length });
      }
      const items = pool.slice(0, topN);
      steps.push({ step: `取前 ${topN} 名`, remaining: items.length });

      const avg = items.length ? items.reduce((a, s) => a + s.score, 0) / items.length : 0;
      const light = items.length ? this.scorer.light(avg, fid) : "red";
      const relax = items.length >= topN ? [] : this.relaxHints(q, scored, exclude);
      return {
        query: { ...q, top_n: topN },
        mode_label: MODES[q.mode],
        formula_id: fid,
        formula_label: formula.label,
        formula_text: this.scorer.formulaText(fid),
        items,
        light,
        percent: items.length ? this.percentOf(avg, fid) : 0,
        enough: items.length >= topN,
        candidates: pool.length,
        steps,
        hints: relax.map(([text]) => text),
        hint_codes: relax.map(([, code]) => code), // 和 hints 一一對應，給網頁翻譯用
      };
    }

    evaluateTray(ids, mode, formula) {
      const fid = this.scorer.formulaId(mode, formula);
      const byId = new Map(this.dishes.map((d) => [d.id, d]));
      const picked = ids.filter((i) => byId.has(i)).map((i) => this.scorer.score(byId.get(i), fid));
      if (!picked.length) return { items: [], average: 0, light: "red", percent: 0, warnings: ["餐盤是空的"], warning_codes: [{ code: "empty" }] };
      const avg = picked.reduce((a, s) => a + s.score, 0) / picked.length;
      const has = (s, t) => s.dish.tags.includes(t);
      const nFat = picked.filter((s) => has(s, "高油")).length;
      const nSalt = picked.filter((s) => has(s, "高鹽")).length;
      const nStarch = picked.filter((s) => has(s, "多澱粉")).length;
      const warnings = [];
      const codes = []; // 和 warnings 一一對應，給網頁翻譯用
      const warn = (text, code) => { warnings.push(text); codes.push(code); };
      if (nFat >= 2) warn(`有 ${nFat} 道高油餐點，油脂可能過量`, { code: "fat", n: nFat });
      if (nSalt >= 2) warn(`有 ${nSalt} 道高鹽餐點，鈉含量偏高`, { code: "salt", n: nSalt });
      if (nStarch >= 2) warn(`有 ${nStarch} 道多澱粉餐點，澱粉偏多`, { code: "starch", n: nStarch });
      if (mode === "fitness" && !picked.some((s) => has(s, "高蛋白質"))) warn("健身模式建議至少一道高蛋白質餐點", { code: "protein" });
      if (mode === "wellness" && picked.some((s) => s.dish.spicy_level >= 3)) warn("養生模式建議避免太辣的餐點", { code: "spicy" });
      let light = this.scorer.light(avg, fid);
      if (warnings.length >= 3) light = "red";
      else if (warnings.length >= 2 && light === "green") light = "yellow";
      return { items: picked, average: pyRound(avg, 1), light, percent: this.percentOf(avg, fid), warnings, warning_codes: codes, formula_id: fid };
    }

    // 分數換算成 0~100（在所有餐點分數中的位置），給伺服馬達指針用
    percentOf(score, fid) {
      if (!this._percentCache[fid]) {
        const all = this.dishes.map((d) => this.scorer.score(d, fid).score);
        this._percentCache[fid] = [Math.min(...all), Math.max(...all)];
      }
      const [lo, hi] = this._percentCache[fid];
      if (hi <= lo) return 100;
      return Math.max(0, Math.min(100, pyRound((100 * (score - lo)) / (hi - lo))));
    }

    relaxHints(q, scored, exclude) {
      const count = ({ budget = q.budget, maxSpicy = q.max_spicy, types = true, rest = true } = {}) =>
        scored.filter((s) => {
          const d = s.dish;
          if (this.overBudget(d, budget) || this.tooSpicy(d, maxSpicy)) return false;
          if (types && this.typeMismatch(d, q, exclude)) return false;
          if (rest && this.restaurantMismatch(d, q)) return false;
          return true;
        }).length;
      const hints = [];
      const pr = this.priceRanges;
      if (q.budget && q.budget !== pr[pr.length - 1]) {
        const nxt = pr[pr.indexOf(q.budget) + 1];
        const n = count({ budget: nxt });
        if (n > 0) hints.push([`把預算提高到「${nxt}」可以找到 ${n} 道`, { code: "budget", value: nxt, n }]);
      }
      if (q.max_spicy != null && q.max_spicy < 5) {
        const n = count({ maxSpicy: q.max_spicy + 1 });
        if (n > 0) hints.push([`可接受辣度放寬到 ${q.max_spicy + 1} 可以找到 ${n} 道`, { code: "spicy", value: q.max_spicy + 1, n }]);
      }
      if (q.main_types.length) {
        const n = count({ types: false });
        if (n > 0) hints.push([`主餐類型改成「不限」可以找到 ${n} 道`, { code: "types", n }]);
      }
      if (q.restaurants.length) {
        const n = count({ rest: false });
        if (n > 0) hints.push([`餐廳改成「不限」可以找到 ${n} 道`, { code: "restaurants", n }]);
      }
      if (!hints.length) hints.push(["請換一個模式或放寬多個條件再試一次", { code: "none" }]);
      return hints;
    }
  }

  // ---------------- AI 小教練：規則版（關鍵字 → 條件） ----------------
  // 中文和英文關鍵字都比對（英文先轉小寫）；改這裡要一起改 ai_coach.py 的 parse_rules
  const UNDER = String.raw`(under|below|within|less than|up to|max)\s*(nt\$|\$)?\s*`;
  const PRICE_WORDS = [
    [new RegExp(String.raw`(100|一百)\s*(元|塊)?\s*(以下|以內|內)|便宜|` + UNDER + String.raw`100\b|\bcheap`), "100以下"],
    [new RegExp(String.raw`(300|三百)\s*(元|塊)?\s*(以下|以內|內)|` + UNDER + String.raw`300\b`), "101-300"],
    [new RegExp(String.raw`(500|五百)\s*(元|塊)?\s*(以下|以內|內)|` + UNDER + String.raw`500\b`), "301-500"],
  ];
  const TYPE_WORDS = {
    "海鮮": "海鮮類", "魚": "海鮮類", "蝦": "海鮮類",
    "吃肉": "肉類", "牛": "肉類", "雞": "肉類", "豬": "肉類",
    "蔬菜": "蔬果類", "青菜": "蔬果類", "沙拉": "蔬果類", "素食": "蔬果類",
    "燉飯": "飯類", "炒飯": "飯類", "丼": "飯類", "飯糰": "飯類",
    "麵": "麵類", "湯": "湯類",
    seafood: "海鮮類", fish: "海鮮類", shrimp: "海鮮類",
    meat: "肉類", beef: "肉類", chicken: "肉類", pork: "肉類",
    vegetable: "蔬果類", veggie: "蔬果類", salad: "蔬果類", vegetarian: "蔬果類",
    rice: "飯類", noodle: "麵類", ramen: "麵類", pasta: "麵類", soup: "湯類",
  };
  const FITNESS_WORDS = ["健身", "增肌", "運動", "重訓", "跑步", "跑完", "打球", "蛋白", "肌肉", "練",
    "gym", "workout", "work out", "exercise", "muscle", "protein", "running", "training"];
  const WELLNESS_WORDS = ["養生", "清淡", "長輩", "阿嬤", "阿公", "爺爺", "奶奶", "腸胃", "低鹽", "少油", "血壓", "健康",
    "light", "grandma", "grandpa", "elderly", "senior", "low salt", "low-salt", "healthy", "bland"];
  const NO_SPICY = /不(要|吃|能吃)?辣|怕辣|not spicy|no spic|non-spicy|mild/;
  const SPICY = /辣|spicy/;

  function parseRules(text) {
    text = text.toLowerCase();
    const reasons = [];
    const f = FITNESS_WORDS.filter((w) => text.includes(w)).length;
    const w = WELLNESS_WORDS.filter((x) => text.includes(x)).length;
    const mode = w > f ? "wellness" : "fitness";
    reasons.push(`判斷為${mode === "wellness" ? "養生" : "健身"}模式`);
    let budget = null;
    for (const [pat, b] of PRICE_WORDS) {
      if (pat.test(text)) { budget = b; reasons.push(`預算 ${b}`); break; }
    }
    let maxSpicy = null;
    if (NO_SPICY.test(text)) { maxSpicy = 0; reasons.push("不吃辣"); }
    else if (SPICY.test(text)) { maxSpicy = 5; reasons.push("可以吃辣"); }
    else if (mode === "wellness") maxSpicy = 1;
    const types = [...new Set(Object.entries(TYPE_WORDS).filter(([k]) => text.includes(k)).map(([, t]) => t))].sort();
    if (types.length) reasons.push("想吃 " + types.join("、"));
    return { query: { mode, budget, max_spicy: maxSpicy, main_types: types }, reasons };
  }

  function ruleReason(s) {
    const good = s.dish.tags.filter((t) => t.startsWith("低") || t === "高蛋白質");
    const bits = [];
    if (good.length) bits.push(good.join("、"));
    if (s.dish.cooking) bits.push(`烹調方式是${s.dish.cooking}`);
    return (bits.join("，") || "加權分數高") + `（${s.score} 分）`;
  }

  // 和 /api/coach 回傳格式相同（規則版）
  function coachRules(text, rec) {
    text = text.trim().slice(0, 300);
    const { query, reasons } = parseRules(text);
    const result = rec.recommend({ ...query, top_n: 3 });
    return {
      source: "rules",
      query: result.query,
      summary: reasons.join("、"),
      result,
      picks: result.items.slice(0, 3).map((s) => ({ ...s, reason: ruleReason(s) })),
    };
  }

  root.FitwellEngine = { Scorer, Recommender, parseRules, coachRules, ruleReason, pyRound, MODES, TERM_LABELS };
})(typeof globalThis !== "undefined" ? globalThis : window);
