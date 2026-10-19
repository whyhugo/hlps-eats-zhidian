// 純靜態網頁版的「本機後端」：在瀏覽器裡做 Python 伺服器（src/fitwell/server.py）做的事。
// - 推薦、餐盤、菜單：web/engine.js 直接計算（資料在 web/data/bundle.json）
// - micro:bit：Chrome／Edge 的 Web Serial 直接連 USB 序列埠，指令和 Python 版完全相同
// - AI 小教練：部署在 Cloudflare 時呼叫 /api/coach（Cloudflare Worker），否則用規則版
"use strict";

(function (root) {
  const E = root.FitwellEngine;
  const STATE_KEY = "fitwell-state";
  const PING_MS = 3000;          // 還沒回應時，每 3 秒問一次 HELLO?
  const CONFIG_RESEND_MS = 15000; // 每 15 秒重送硬體設定（micro:bit 重開後會恢復預設）

  // ---------------- Web Serial：和 micro:bit 的 USB 序列埠 ----------------
  class MicrobitLink {
    constructor(onLine, onChange) {
      this.onLine = onLine;
      this.onChange = onChange;
      this.supported = "serial" in navigator;
      this.port = null;
      this.reader = null;
      this.responding = false;
      this.rx = 0;
      this.tx = 0;
      this.crashes = 0;
      this.warns = [];
      this.queue = Promise.resolve();
      this.lastPing = 0;
      if (this.supported) {
        navigator.serial.addEventListener("disconnect", (e) => { if (e.target === this.port) this.close(); });
        navigator.serial.addEventListener("connect", () => this.autoConnect());
      }
    }

    get connected() { return this.port !== null; }

    // 之前允許過的 micro:bit 會自動連上（不用再按按鈕）
    async autoConnect() {
      if (!this.supported || this.port) return false;
      const ports = await navigator.serial.getPorts();
      const mb = ports.find((p) => p.getInfo().usbVendorId === 0x0d28) || ports[0];
      return mb ? this.open(mb) : false;
    }

    // 使用者按「連接 micro:bit」：跳出瀏覽器的選擇視窗
    async request() {
      if (!this.supported) throw new Error("這個瀏覽器不支援 Web Serial，請用電腦版 Chrome 或 Edge");
      const port = await navigator.serial.requestPort({ filters: [{ usbVendorId: 0x0d28 }] });
      return this.open(port);
    }

    async open(port) {
      try {
        await port.open({ baudRate: 115200 });
      } catch (e) {
        throw new Error("打不開 micro:bit 的序列埠：可能有其他程式（MakeCode、另一個分頁、fitwell serve）正在使用。" + e.message);
      }
      this.port = port;
      this.responding = false;
      this.lastPing = 0;
      this.onChange();
      this.readLoop(port);
      this.timer = setInterval(() => this.tick(), 1000);
      this.tick();
      return true;
    }

    async readLoop(port) {
      const decoder = new TextDecoderStream();
      const done = port.readable.pipeTo(decoder.writable).catch(() => {});
      this.reader = decoder.readable.getReader();
      let buf = "";
      try {
        for (;;) {
          const { value, done: end } = await this.reader.read();
          if (end) break;
          buf += value;
          let i;
          while ((i = buf.indexOf("\n")) >= 0) {
            const line = buf.slice(0, i).trim();
            buf = buf.slice(i + 1);
            if (line) this.receive(line);
          }
        }
      } catch { /* 拔掉線 */ }
      await done;
    }

    receive(line) {
      this.rx++;
      if (!this.responding) { this.responding = true; this.onChange(); }
      if (this.isCrashOutput(line)) return;
      this.onLine(line);
    }

    // micro:bit 程式出錯時的輸出不是指令：記錄下來，必要時讓程式重新開始
    isCrashOutput(line) {
      if (line.startsWith("WARN:")) {
        const now = Date.now();
        this.warns = this.warns.filter((t) => now - t < 10000).concat(now);
        if (this.warns.length >= 20) { this.warns = []; this.restartProgram(); }
        return true;
      }
      if (/^(Traceback|File "|>>>|MicroPython v|Type "help\(\)"|soft reboot)/.test(line)) return true;
      if (line.includes("Error")) { this.restartProgram(); return true; }
      return false;
    }

    restartProgram() {
      this.write("\x03\r\x04"); // Ctrl+C 中斷、Ctrl+D 重開（MicroPython 版）
      this.responding = false;
      this.crashes++;
      this.onChange();
    }

    tick() {
      const now = Date.now();
      if (!this.responding && now - this.lastPing > PING_MS) {
        this.lastPing = now;
        this.send("HELLO?");
      } else if (this.responding && now - this.lastPing > CONFIG_RESEND_MS) {
        this.lastPing = now;
        this.onResend?.();
      }
    }

    send(line) {
      if (!this.port) return false;
      this.tx++;
      this.write(line.trim() + "\n");
      return true;
    }

    // 依序寫入（同時只能有一個 writer）
    write(text) {
      const port = this.port;
      this.queue = this.queue.then(async () => {
        if (!port?.writable) return;
        const w = port.writable.getWriter();
        try { await w.write(new TextEncoder().encode(text)); } finally { w.releaseLock(); }
      }).catch(() => {});
    }

    async close() {
      const port = this.port;
      if (!port) return;
      this.port = null;
      this.responding = false;
      clearInterval(this.timer);
      try { await this.reader?.cancel(); } catch {}
      try { await port.close(); } catch {}
      this.onChange();
    }
  }

  // ---------------- 本機後端（取代 /api/*） ----------------
  class LocalServer {
    constructor(bundle, cloud = {}) {
      this.bundle = bundle;
      this.config = bundle.config;
      this.hardware = bundle.hardware;
      this.cloud = cloud;
      this.rec = new E.Recommender(bundle.dishes, bundle.config);
      this.listeners = [];
      this.lastResult = null;
      const d = this.config.defaults;
      this.state = Object.assign(
        { mode: "fitness", budget: d.budget, max_spicy: d.max_spicy, main_types: [...d.main_types], restaurants: [], formula_fitness: null, formula_wellness: null },
        loadJSON(STATE_KEY)
      );
      this.link = new MicrobitLink((line) => this.onMicrobitLine(line), () => this.publish("status", this.status()));
      this.link.onResend = () => this.sendHardwareConfig();
      this.link.autoConnect().catch(() => {});
    }

    on(fn) { this.listeners.push(fn); }
    publish(type, data) { this.listeners.forEach((fn) => fn({ type, data })); }
    saveState() { saveJSON(STATE_KEY, this.state); }
    connect() { return this.link.request(); }
    disconnect() { return this.link.close(); }

    status() {
      const l = this.link;
      return {
        microbit: { connected: l.connected, responding: l.connected && l.responding, port: l.connected ? "Web Serial" : null,
          rx: l.rx, tx: l.tx, crashes: l.crashes, webusb: [], webserial: true, supported: l.supported },
        ai: Boolean(this.cloud.ai),
        hardware: this.hardware,
        state: this.state,
        static: true,
      };
    }

    meta() {
      const cfg = this.config;
      const dishes = this.rec.dishes;
      const formulas = {};
      for (const [k, v] of Object.entries(cfg.formulas)) formulas[k] = { ...v, text: this.rec.scorer.formulaText(k), lights: cfg.lights[k] };
      return {
        version: "static",
        modes: E.MODES,
        price_ranges: cfg.price_ranges,
        main_types: [...new Set(dishes.map((d) => d.main_type))].sort(),
        restaurants: [...new Set(dishes.map((d) => d.restaurant))].sort(),
        formulas,
        active_formula: cfg.active_formula,
        defaults: cfg.defaults,
        dish_count: dishes.length,
        ...this.status(),
      };
    }

    query() {
      const s = this.state;
      return { mode: s.mode, budget: s.budget, max_spicy: s.max_spicy, main_types: s.main_types, restaurants: s.restaurants,
        formula: s.mode === "fitness" ? s.formula_fitness : s.formula_wellness };
    }

    runRecommend(q, source) {
      const result = { ...this.rec.recommend(q), source };
      this.lastResult = result;
      this.sendLight(result.light, result.items.length, result.percent);
      this.publish("result", result);
      return result;
    }

    sendHardwareConfig() {
      const hw = this.hardware;
      [`CFG:KNOB:${+!!hw.use_budget_knob}`, `CFG:SKNOB:${+!!hw.use_spicy_knob}`, `CFG:BUZZER:${hw.buzzer}`,
        `CFG:SERVO_REV:${+!!hw.servo_reverse}`, `CFG:BEEP:${hw.beep_ms}`].forEach((l) => this.link.send(l));
    }

    sendLight(light, count, percent) {
      if (percent != null) this.link.send(`SCORE:${percent}`);
      this.link.send(`LIGHT:${light.toUpperCase()}`);
      if (count != null) this.link.send(`SHOW:${count}`);
    }

    // micro:bit 指令（真實硬體和虛擬 micro:bit 共用），和 server.py 的 on_microbit_line 相同
    onMicrobitLine(raw) {
      const line = raw.trim().toUpperCase();
      this.publish("microbit", { line });
      const i = line.indexOf(":");
      const cmd = i < 0 ? line : line.slice(0, i);
      const arg = i < 0 ? "" : line.slice(i + 1);
      const st = this.state;
      const prices = this.config.price_ranges;
      if (cmd === "HELLO") {
        this.link.send("ACK:HELLO");
        this.sendHardwareConfig();
        this.publish("status", this.status());
        return;
      }
      if ((cmd === "MODE" || cmd === "GO") && (arg === "FITNESS" || arg === "WELLNESS")) st.mode = arg.toLowerCase();
      else if (cmd === "BUDGET" && arg === "ANY") st.budget = null;
      else if (cmd === "BUDGET" && /^\d+$/.test(arg) && +arg < prices.length) st.budget = prices[+arg];
      else if (cmd === "SPICY" && arg === "ANY") st.max_spicy = null;
      else if (cmd === "SPICY" && /^\d+$/.test(arg)) st.max_spicy = Math.min(5, +arg);
      else if (cmd !== "GO" && cmd !== "MODE") return;
      this.link.send(`ACK:${cmd}`);
      this.saveState();
      this.publish("state", st);
      if (cmd === "GO") this.runRecommend(this.query(), "microbit");
    }

    // 和 Python 伺服器相同的 API 路徑，app.js 不用分兩套
    async handle(path, body) {
      const [p, qs] = path.split("?");
      const params = new URLSearchParams(qs || "");
      const clone = (x) => JSON.parse(JSON.stringify(x));
      switch (p) {
        case "/api/meta": return clone(this.meta());
        case "/api/status": return clone(this.status());
        case "/api/state":
          if (body !== undefined) this.setState(body);
          return clone(this.state);
        case "/api/go": return clone(this.runRecommend(this.query(), "web"));
        case "/api/result": return clone(this.lastResult || {});
        case "/api/dishes": {
          const fid = this.rec.scorer.formulaId(params.get("mode") || "fitness", params.get("formula"));
          const items = this.rec.dishes.map((d) => this.rec.scorer.score(d, fid)).sort((a, b) => b.score - a.score);
          return clone({ formula_id: fid, items });
        }
        case "/api/tray": {
          const res = this.rec.evaluateTray(body.ids, body.mode, body.formula);
          this.sendLight(res.light, null, res.percent);
          return clone(res);
        }
        case "/api/coach": return clone(await this.coach(body.text, body.token));
        case "/api/microbit/simulate":
          this.onMicrobitLine(body.line);
          return clone(this.status());
        case "/api/microbit/send": return { sent: this.link.send(body.line) };
        case "/api/report": return this.bundle.report || "尚未產生報告";
      }
      throw new Error("找不到 " + p);
    }

    setState(s) {
      const st = this.state;
      if (s.mode != null) {
        if (!E.MODES[s.mode]) throw new Error("模式錯誤");
        st.mode = s.mode;
      }
      for (const k of ["budget", "max_spicy", "main_types", "restaurants", "formula_fitness", "formula_wellness"]) if (s[k] != null) st[k] = s[k];
      for (const k of s.clear || []) {
        if (k === "budget" || k === "max_spicy") st[k] = null;
        else if (k === "main_types" || k === "restaurants") st[k] = [];
      }
      this.saveState();
      this.publish("state", st);
    }

    // AI 小教練：Cloudflare 上有 /api/coach（Claude）就用，否則或失敗時用規則版
    async coach(text, token) {
      if (!text?.trim()) throw new Error("請輸入想吃什麼");
      let out = null;
      if (this.cloud.ai) {
        try {
          const r = await fetch("/api/coach", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text, token }) });
          const j = await r.json();
          if (!r.ok) throw new Error(j.detail || r.statusText);
          out = j;
        } catch (e) {
          console.warn("AI 小教練失敗，改用規則版：", e);
          var note = e.message;
        }
      }
      if (!out) {
        out = E.coachRules(text, this.rec);
        if (note) out.summary = `（AI 暫時不能用：${note}，改用關鍵字判斷）${out.summary}`;
      }
      if (out.picks.length) this.sendLight(out.result.light, out.picks.length, out.result.percent);
      return out;
    }
  }

  function loadJSON(k) { try { return JSON.parse(localStorage.getItem(k) || "{}"); } catch { return {}; } }
  function saveJSON(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch {} }

  root.FitwellLocal = LocalServer;
})(typeof globalThis !== "undefined" ? globalThis : window);
