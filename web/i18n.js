// 網頁雙語（繁體中文／English）。
// - 固定文字：index.html 用 data-i18n（文字）、data-i18n-html（含 <b> 等標籤）、data-i18n-attr（屬性，例：aria-label:key;placeholder:key）
// - 程式產生的文字：app.js 用 I18N.t("key", { 變數 })
// - 菜單資料：菜名、餐廳名保留中文；類型、烹調方式、標籤、價格區間用 I18N.term() 翻譯
// 新增文字時兩種語言都要加；英文缺了會顯示中文。
"use strict";

(function (root) {
  const STORE_KEY = "fitwell-lang";

  const zh = {
    "meta.title": "「脂」點迷津！外食族吃什麼—智慧營養選餐解憂亭",
    "meta.desc": "依健身或養生目標，從竹北遠百 12 家餐廳推薦最適合的 3 道菜，並與 micro:bit 燈號連動。",
    "lang.switch": "EN",
    "lang.switchLabel": "Switch to English",
    "skip": "跳到主要內容",
    "brand.sub": "智慧營養選餐解憂亭",

    "mode.group": "目前模式（影響推薦與我的餐盤）",
    "mode.current": "目前模式",
    "mode.fitness": "健身",
    "mode.wellness": "養生",
    "mode.info": "模式說明",
    "mode.tip": "<b>健身</b>：高蛋白、低油優先。<br><b>養生</b>：清淡、低鹽、少辣優先。<br>切換模式會同時改變「推薦」的計分公式與「我的餐盤」的評估標準。micro:bit 按 A 鍵也能切換。",

    "status.connect": "連接 micro:bit",
    "status.disconnect": "中斷連線",
    "status.mbOk": "micro:bit 已連接<br>{port}｜收到 {rx} 則、送出 {tx} 則",
    "status.mbWebusb": "micro:bit 被 <b>{who}</b> 的 WebUSB 佔住，收不到按鍵。<br>請關閉燒錄網頁（MakeCode／Python Editor）或結束該程式，再重新插拔 USB。",
    "status.mbSilent": "USB 已連接，但 micro:bit 程式沒回應。<br>請重新插拔 USB，並關閉使用 WebUSB 的瀏覽器分頁。",
    "status.mbNone": "micro:bit 未連接。<br>可以展開右下角的虛擬 micro:bit 示範。",
    "status.wsUnsupported": "這個瀏覽器不能連接 micro:bit（需要 Web Serial）。<br>請用電腦版 Chrome 或 Edge；也可以展開右下角的虛擬 micro:bit。",
    "status.wsOk": "micro:bit 已連接（Web Serial）<br>收到 {rx} 則、送出 {tx} 則",
    "status.wsSilent": "已連接，但 micro:bit 程式沒回應。<br>請確認已把本專案的 .hex 燒進 micro:bit，並關閉 MakeCode 等燒錄網頁。",
    "status.wsNone": "尚未連接 micro:bit。<br>插上 USB 後按「連接 micro:bit」，選擇清單中的 micro:bit。",
    "status.aiOn": "AI 小教練已連線（Gemini）",
    "status.aiOff": "AI 小教練使用關鍵字規則版（未連上 AI）",

    "tabs": "功能",
    "tab.recommend": "求籤推薦",
    "tab.tray": "我的餐盤",
    "tab.coach": "AI 小教練",
    "tab.menu": "全部菜單",
    "tab.about": "怎麼運作",

    "num.1": "一", "num.2": "二", "num.3": "三",
    "f.budget": "預算上限",
    "f.budgetInfo": "預算說明",
    "f.budgetTip": "只推薦這個價位以內的餐點。順序和 micro:bit 預算旋鈕一樣：往右轉越貴，轉到底是「不限」。",
    "f.spicy": "可接受辣度",
    "f.spicyInfo": "辣度說明",
    "f.spicyTip": "辣度 0～5 由學生實地標記。選 2 代表 2 辣以下都可以；轉辣度旋鈕也能選，轉到底是「都可以」。",
    "f.type": "想吃的類型",
    "f.typeInfo": "類型說明",
    "f.typeTip": "可以複選。全部不選就是「不限」。飲料和甜點不列入主餐推薦。",
    "chip.any": "不限",
    "chip.noSpicy": "不辣",
    "chip.spicyAny": "都可以",
    "chip.spicyLabel": "{n} 辣以下",
    "go": "求籤",
    "hw.hint": "也能用 micro:bit 操作",
    "hw.info": "micro:bit 操作方式",
    "hw.tip": "<b>A 鍵</b> 切換健身／養生<br><b>B 鍵</b> 求籤推薦<br><b>旋鈕</b> 左邊選預算、右邊選辣度",

    "flow.aria": "篩選流程：每一步剩下幾道",
    "flow.0": "計分", "flow.1": "預算", "flow.2": "辣度", "flow.3": "類型", "flow.4": "取前",
    "step.score": "計分排序", "step.budget": "預算", "step.spicy": "辣度", "step.type": "主餐類型", "step.restaurant": "餐廳", "step.top": "取前 {n} 名",
    "result.empty": "選好條件，按「求籤」",
    "result.formulaAria": "使用的計分公式",
    "result.title": "{mode}・抽到 {n} 支籤・",
    "result.none": "{mode}：找不到符合條件的餐點",
    "result.score": "分數 = {text}",
    "result.byMicrobit": "由 micro:bit 觸發",
    "result.hintsHead": "只找到 {n} 道，試試看：",
    "slips.empty": "三支籤會出現在這裡",
    "slips.none": "沒有抽到籤，放寬條件再試一次",

    "hint.budget": "把預算提高到「{value}」可以找到 {n} 道",
    "hint.spicy": "可接受辣度放寬到 {value} 可以找到 {n} 道",
    "hint.types": "主餐類型改成「不限」可以找到 {n} 道",
    "hint.restaurants": "餐廳改成「不限」可以找到 {n} 道",
    "hint.none": "請換一個模式或放寬多個條件再試一次",

    "light.green": "綠燈", "light.yellow": "黃燈", "light.red": "紅燈",
    "verdict.green": "宜食", "verdict.yellow": "適量", "verdict.red": "少吃",
    "lot.green": "上籤", "lot.yellow": "中籤", "lot.red": "下籤",
    "slip.rank": "第{cn}籤",
    "slip.priceUnknown": "價格未知",
    "slip.spicy": "{n} 辣",
    "slip.notSpicy": "不辣",
    "slip.pts": "分",
    "slip.howScore": "分數怎麼算",
    "slip.term": "{label}：加權 {w} × {f} = ",
    "slip.total": "總分",
    "slip.remove": "移出餐盤",
    "slip.inTray": "已在餐盤",
    "slip.add": "加入餐盤",

    "tray.title": "我的餐盤：整餐健康嗎？",
    "tray.info": "餐盤說明",
    "tray.tip": "單點主餐很健康，但加了炸物、甜點，整餐可能就爆表。把籤或菜單裡的餐點「加入餐盤」，用目前模式的公式看整餐燈號。",
    "tray.clear": "清空",
    "tray.emptyTitle": "餐盤是空的",
    "tray.empty": "餐盤是空的，到「求籤推薦」或「全部菜單」加入餐點",
    "tray.emptySeal": "空盤",
    "tray.summary": "{n} 道・平均 <span class=\"avg\">{avg}</span> 分・健康指數 {p}%",
    "tray.mode": "以{mode}模式評估",
    "warn.fat": "有 {n} 道高油餐點，油脂可能過量",
    "warn.salt": "有 {n} 道高鹽餐點，鈉含量偏高",
    "warn.starch": "有 {n} 道多澱粉餐點，澱粉偏多",
    "warn.protein": "健身模式建議至少一道高蛋白質餐點",
    "warn.spicy": "養生模式建議避免太辣的餐點",
    "warn.empty": "餐盤是空的",

    "coach.title": "用一句話告訴我你想吃什麼",
    "coach.info": "AI 小教練說明",
    "coach.tip": "AI 只會從學生調查的竹北遠百菜單裡挑選，不會編造餐點。沒有網路時會改用關鍵字規則。",
    "coach.inputLabel": "想吃什麼",
    "coach.placeholder": "例如：剛打完球，想吃高蛋白但不要太油，300 元以內",
    "coach.ask": "問問看",
    "coach.verify": "請先勾選輸入框下方的「驗證您是人類」，再按「問問看」。",
    "coach.thinking": "思考中…",
    "coach.none": "找不到符合的餐點。",
    "coach.error": "出錯了：{msg}",
    "coach.fallback": "（AI 暫時不能用：{msg}，改用關鍵字判斷）",
    "coach.aiParsed": "由 AI 理解你的需求",
    "ex.run": "跑完步", "ex.runText": "我剛跑完步，想吃高蛋白但不要太油，300 元以內",
    "ex.grandma": "帶阿嬤", "ex.grandmaText": "帶阿嬤吃飯，要清淡、不辣、好咬",
    "ex.seafood": "清淡海鮮", "ex.seafoodText": "想吃海鮮，養生一點，不要辣",
    "ex.cheap": "100 元以內", "ex.cheapText": "100 元以內有什麼健康的",

    "menu.formula": "計分公式",
    "menu.search": "搜尋餐廳、菜名或類型",
    "menu.count": "{n} 道",
    "menu.addShort": "餐盤",
    "th.light": "燈號", "th.score": "分數", "th.rest": "餐廳", "th.dish": "餐點", "th.price": "價格",
    "th.type": "類型", "th.cook": "烹調", "th.spicy": "辣", "th.tags": "標籤", "th.add": "加入餐盤",

    "about.flowTitle": "推薦流程（學生設計的流程圖）",
    "about.s1": "選擇模式：健身 或 養生",
    "about.s2": "用該模式的加權公式，幫每道餐點算分數",
    "about.s3": "依分數從高排到低",
    "about.s4": "超出預算？→ 不加入候選",
    "about.s5": "超出可接受辣度？→ 不加入候選",
    "about.s6": "不符合主餐類型？→ 不加入候選",
    "about.s7": "取前 3 名，亮起 綠／黃／紅 燈",
    "about.s8": "不足 3 道？→ 提示可以放寬哪個條件",
    "about.formulas": "加權公式",
    "about.data": "資料來源",
    "about.dataText": "學生親自到竹北遠百調查了 <b>12</b> 家餐廳、<b>231</b> 道餐點，並幫每道菜標記油脂、蛋白質、鹽分、澱粉、辣度與烹調方式。",
    "about.report": "查看資料檢查報告",
    "formula.inUse": "使用中",
    "formula.info": "公式說明",
    "formula.green": "綠燈 ≥ {n}",
    "formula.yellow": "黃燈 ≥ {n}",
    "formula.red": "其餘紅燈",

    "vmb.title": "虛擬 micro:bit",
    "vmb.info": "虛擬 micro:bit 說明",
    "vmb.tip": "沒有接硬體時，用這塊模擬板示範。按鈕送出的指令和真的 micro:bit 一模一樣。",
    "vmb.a": "A 鍵：切換模式",
    "vmb.b": "B 鍵：求籤",
    "vmb.budget": "切換預算（模擬旋鈕）",

    "err.server": "無法連到伺服器：{msg}。請先執行 <code>uv run fitwell serve</code>",
    "err.bundle": "找不到 data/bundle.json，請執行 uv run fitwell export-static",
  };

  const en = {
    "meta.title": "「脂」點迷津 — Smart Nutrition Meal Picker",
    "meta.desc": "Pick the 3 best dishes from 12 food-court restaurants for a fitness or wellness goal, with live micro:bit lights.",
    "lang.switch": "中文",
    "lang.switchLabel": "切換成中文",
    "skip": "Skip to main content",
    "brand.sub": "Smart Nutrition Meal Picker",

    "mode.group": "Current mode (affects picks and My Tray)",
    "mode.current": "Current mode",
    "mode.fitness": "Fitness",
    "mode.wellness": "Wellness",
    "mode.info": "About modes",
    "mode.tip": "<b>Fitness</b>: high protein, low fat first.<br><b>Wellness</b>: light, low salt, less spicy first.<br>Switching mode changes both the scoring formula for picks and how My Tray is rated. Button A on the micro:bit switches it too.",

    "status.connect": "Connect micro:bit",
    "status.disconnect": "Disconnect",
    "status.mbOk": "micro:bit connected<br>{port} · {rx} received, {tx} sent",
    "status.mbWebusb": "The micro:bit is held by <b>{who}</b> over WebUSB, so button presses can't get through.<br>Close the flashing page (MakeCode / Python Editor) or quit that app, then replug the USB.",
    "status.mbSilent": "USB is connected, but the micro:bit program isn't answering.<br>Replug the USB and close any browser tab using WebUSB.",
    "status.mbNone": "No micro:bit connected.<br>Open the virtual micro:bit at the bottom right to try it out.",
    "status.wsUnsupported": "This browser can't connect to a micro:bit (Web Serial is required).<br>Use desktop Chrome or Edge, or open the virtual micro:bit at the bottom right.",
    "status.wsOk": "micro:bit connected (Web Serial)<br>{rx} received, {tx} sent",
    "status.wsSilent": "Connected, but the micro:bit program isn't answering.<br>Make sure this project's .hex is flashed, and close MakeCode or other flashing pages.",
    "status.wsNone": "No micro:bit connected yet.<br>Plug in the USB, press “Connect micro:bit”, and choose the micro:bit from the list.",
    "status.aiOn": "AI Coach is online (Gemini)",
    "status.aiOff": "AI Coach is using keyword rules (no AI connection)",

    "tabs": "Features",
    "tab.recommend": "Draw a Pick",
    "tab.tray": "My Tray",
    "tab.coach": "AI Coach",
    "tab.menu": "Full Menu",
    "tab.about": "How It Works",

    "num.1": "1", "num.2": "2", "num.3": "3",
    "f.budget": "Budget",
    "f.budgetInfo": "About budget",
    "f.budgetTip": "Only dishes in this price range or cheaper. Same order as the micro:bit budget knob: turn right for pricier; all the way is “Any”.",
    "f.spicy": "Spice tolerance",
    "f.spicyInfo": "About spice",
    "f.spicyTip": "Spice levels 0–5 were rated by students on site. Picking 2 means level 2 or milder. The spice knob works too; all the way is “Any”.",
    "f.type": "Food type",
    "f.typeInfo": "About food type",
    "f.typeTip": "Pick several, or none for “Any”. Drinks and desserts aren't recommended as mains.",
    "chip.any": "Any",
    "chip.noSpicy": "None",
    "chip.spicyAny": "Any",
    "chip.spicyLabel": "Spice level {n} or milder",
    "go": "Draw",
    "hw.hint": "Works with the micro:bit too",
    "hw.info": "micro:bit controls",
    "hw.tip": "<b>Button A</b> switch Fitness / Wellness<br><b>Button B</b> draw a pick<br><b>Knobs</b> left = budget, right = spice",

    "flow.aria": "Filter steps: dishes left after each step",
    "flow.0": "Scored", "flow.1": "Budget", "flow.2": "Spice", "flow.3": "Type", "flow.4": "Top",
    "step.score": "Score & sort", "step.budget": "Budget", "step.spicy": "Spice", "step.type": "Food type", "step.restaurant": "Restaurant", "step.top": "Top {n}",
    "result.empty": "Set your filters, then press “Draw”",
    "result.formulaAria": "Scoring formula used",
    "result.title": "{mode} · {n} picks · ",
    "result.none": "{mode}: no dishes match",
    "result.score": "Score = {text}",
    "result.byMicrobit": "Triggered by the micro:bit",
    "result.hintsHead": "Only found {n}. Try:",
    "slips.empty": "Your three picks will appear here",
    "slips.none": "No picks — relax a filter and try again",

    "hint.budget": "Raise the budget to {value} to find {n}",
    "hint.spicy": "Allow spice level {value} to find {n}",
    "hint.types": "Set food type to “Any” to find {n}",
    "hint.restaurants": "Set restaurant to “Any” to find {n}",
    "hint.none": "Try the other mode or relax several filters",

    "light.green": "Green", "light.yellow": "Yellow", "light.red": "Red",
    "verdict.green": "Go for it", "verdict.yellow": "Moderate", "verdict.red": "Go easy",
    "lot.green": "Top lot", "lot.yellow": "Fair lot", "lot.red": "Low lot",
    "slip.rank": "Pick #{n}",
    "slip.priceUnknown": "Price unknown",
    "slip.spicy": "Spice {n}",
    "slip.notSpicy": "Not spicy",
    "slip.pts": "pts",
    "slip.howScore": "How the score works",
    "slip.term": "{label}: weight {w} × {f} = ",
    "slip.total": "Total",
    "slip.remove": "Remove",
    "slip.inTray": "In tray",
    "slip.add": "Add to tray",

    "tray.title": "My Tray: is the whole meal healthy?",
    "tray.info": "About My Tray",
    "tray.tip": "A healthy main can still add up to too much with fried sides and desserts. Add dishes from your picks or the menu to see the whole meal's light, scored with the current mode.",
    "tray.clear": "Clear",
    "tray.emptyTitle": "Your tray is empty",
    "tray.empty": "Your tray is empty — add dishes from Draw a Pick or Full Menu",
    "tray.emptySeal": "Empty",
    "tray.summary": "{n} dishes · avg <span class=\"avg\">{avg}</span> pts · health index {p}%",
    "tray.mode": "Rated in {mode} mode",
    "warn.fat": "{n} high-fat dishes — that may be too much fat",
    "warn.salt": "{n} high-salt dishes — sodium is high",
    "warn.starch": "{n} high-carb dishes — that's a lot of starch",
    "warn.protein": "Fitness mode: add at least one high-protein dish",
    "warn.spicy": "Wellness mode: avoid very spicy dishes",
    "warn.empty": "Your tray is empty",

    "coach.title": "Tell me what you feel like eating",
    "coach.info": "About the AI Coach",
    "coach.tip": "The AI only picks from the student-surveyed food court menu and never makes up dishes. Without internet it falls back to keyword rules.",
    "coach.inputLabel": "What do you want to eat?",
    "coach.placeholder": "e.g. Just played ball, want high protein but not oily, under 300",
    "coach.ask": "Ask",
    "coach.verify": "Please tick “Verify you are human” below the input first, then press “Ask”.",
    "coach.thinking": "Thinking…",
    "coach.none": "No matching dishes. ",
    "coach.error": "Something went wrong: {msg}",
    "coach.fallback": "(AI unavailable: {msg}. Used keyword rules instead.) ",
    "coach.aiParsed": "Understood by AI",
    "ex.run": "After a run", "ex.runText": "I just went running, want high protein but not too oily, under 300",
    "ex.grandma": "With grandma", "ex.grandmaText": "Taking grandma out, something light, not spicy and easy to chew",
    "ex.seafood": "Light seafood", "ex.seafoodText": "I want seafood, something light and healthy, not spicy",
    "ex.cheap": "Under NT$100", "ex.cheapText": "Anything healthy under 100?",

    "menu.formula": "Scoring formula",
    "menu.search": "Search restaurant, dish or type",
    "menu.count": "{n} dishes",
    "menu.addShort": "Tray",
    "th.light": "Light", "th.score": "Score", "th.rest": "Restaurant", "th.dish": "Dish", "th.price": "Price",
    "th.type": "Type", "th.cook": "Cooking", "th.spicy": "Spice", "th.tags": "Tags", "th.add": "Add to tray",

    "about.flowTitle": "How picks are made (the students' flowchart)",
    "about.s1": "Choose a mode: Fitness or Wellness",
    "about.s2": "Score every dish with that mode's weighted formula",
    "about.s3": "Sort by score, highest first",
    "about.s4": "Over budget? → drop it",
    "about.s5": "Too spicy? → drop it",
    "about.s6": "Wrong food type? → drop it",
    "about.s7": "Take the top 3 and light green / yellow / red",
    "about.s8": "Fewer than 3? → suggest which filter to relax",
    "about.formulas": "Weighted formulas",
    "about.data": "Data source",
    "about.dataText": "Students surveyed <b>12</b> restaurants and <b>231</b> dishes at the Zhubei department-store food court in person, rating each dish's fat, protein, salt, starch, spice and cooking method. Dish and restaurant names are kept in Chinese as surveyed.",
    "about.report": "View the data check report (in Chinese)",
    "formula.inUse": "In use",
    "formula.info": "About this formula",
    "formula.green": "Green ≥ {n}",
    "formula.yellow": "Yellow ≥ {n}",
    "formula.red": "Otherwise red",

    "vmb.title": "Virtual micro:bit",
    "vmb.info": "About the virtual micro:bit",
    "vmb.tip": "No hardware? Use this simulated board. Its buttons send exactly the same commands as a real micro:bit.",
    "vmb.a": "Button A: switch mode",
    "vmb.b": "Button B: draw",
    "vmb.budget": "Change budget (simulated knob)",

    "err.server": "Can't reach the server: {msg}. Run <code>uv run fitwell serve</code> first.",
    "err.bundle": "data/bundle.json not found. Run uv run fitwell export-static",
  };

  // 菜單資料的固定詞彙（中文 → 英文）；中文介面直接顯示原文
  const VOCAB = {
    type: {
      "海鮮類": "Seafood", "湯類": "Soup", "漢堡類": "Burgers", "炸物類": "Fried food", "甜點類": "Desserts",
      "肉類": "Meat", "蔬果類": "Veggies & fruit", "蛋白質": "Protein", "韓式泡菜類": "Korean kimchi",
      "飯類": "Rice", "飲料類": "Drinks", "麵類": "Noodles",
    },
    cooking: {
      "水煮": "Boiled", "炸": "Fried", "烤": "Grilled", "煎": "Pan-fried", "炒": "Stir-fried", "蒸": "Steamed",
      "飲品": "Drink", "生食": "Raw", "煮": "Cooked", "滷": "Braised", "醃製": "Pickled", "涼拌": "Cold-dressed",
      "醬燒": "Sauce-glazed", "煙燻": "Smoked", "特製": "House style", "奶酪": "Panna cotta", "熬煮": "Simmered",
      "燒": "Roasted", "燒燙": "Seared", "爆": "Flash-fried", "燙": "Blanched", "炙燒": "Torched", "燉": "Stewed",
      "打拋": "Thai basil stir-fry",
    },
    tag: {
      "低油": "Low fat", "低澱粉": "Low carb", "低鹽": "Low salt", "多澱粉": "High carb",
      "高油": "High fat", "高蛋白質": "High protein", "高鹽": "High salt",
    },
    price: { "100以下": "≤ NT$100", "101-300": "NT$101–300", "301-500": "NT$301–500", "500以上": "NT$500+" },
    priceShort: { "100以下": "≤100", "101-300": "101–300", "301-500": "301–500", "500以上": "500+" },
    term: { fat: "Fat", protein: "Protein", salt: "Salt", starch: "Starch", spicy: "Spice", cooking: "Cooking" },
  };

  // 公式名稱與說明（config/scoring.json 的內容是中文；英文版依公式代號翻譯）
  const FORMULAS_EN = {
    fitness_v1: { label: "Fitness v1 (students' original)", note: "The students' Excel formula: fat×2 + protein×3 − salt×1 + starch×1. Note: the salt weight already means “good = positive”, so subtracting it makes saltier dishes score higher." },
    fitness_v2: { label: "Fitness v2 (salt direction fixed)", note: "Salt becomes +1, so low salt (+2) adds points and high salt (−1) takes points away. Everything else follows the students' design." },
    wellness_v1: { label: "Wellness v1 (students' version)", note: "The students' Excel formula: fat×1 − spice×1 + salt×1 + starch×1 + cooking×3." },
  };

  const DICTS = { zh, en };
  const listeners = [];

  function initialLang() {
    const q = new URLSearchParams(location.search).get("lang");
    if (q === "en" || q === "zh") return q;
    try {
      const saved = localStorage.getItem(STORE_KEY);
      if (saved === "en" || saved === "zh") return saved;
    } catch {}
    return "zh";
  }

  let lang = initialLang();

  function t(key, vars = {}) {
    const s = DICTS[lang][key] ?? zh[key] ?? key;
    return s.replace(/\{(\w+)\}/g, (_, k) => (vars[k] ?? ""));
  }

  // 菜單詞彙：kind = type／cooking／tag／price／priceShort／term
  function term(kind, value) {
    if (value == null || value === "") return value ?? "";
    if (kind === "term") return lang === "en" ? VOCAB.term[value] || value : null;
    if (lang !== "en") return kind === "priceShort" ? String(value).replace("-", "–") : value;
    if (kind === "cooking") return String(value).split(/\s*[,，]\s*/).map((c) => VOCAB.cooking[c] || c).join(", ");
    return VOCAB[kind]?.[value] || value;
  }

  function formula(id, f) {
    if (lang === "en" && FORMULAS_EN[id]) return FORMULAS_EN[id];
    return { label: f.label, note: f.note };
  }

  // 英文版的公式文字（中文版直接用伺服器算好的 formula_text）
  function formulaText(terms, zhText) {
    if (lang !== "en" || !terms) return zhText;
    const parts = Object.entries(terms).map(([k, f]) => `${f < 0 ? "−" : "+"} ${VOCAB.term[k] || k}×${Math.abs(f)}`);
    const text = parts.join(" ");
    return text.startsWith("+ ") ? text.slice(2) : text;
  }

  function apply(root = document) {
    root.querySelectorAll("[data-i18n]").forEach((el) => (el.textContent = t(el.dataset.i18n)));
    root.querySelectorAll("[data-i18n-html]").forEach((el) => (el.innerHTML = t(el.dataset.i18nHtml)));
    root.querySelectorAll("[data-i18n-attr]").forEach((el) => {
      el.dataset.i18nAttr.split(";").forEach((pair) => {
        const [attr, key] = pair.split(":");
        if (attr && key) el.setAttribute(attr.trim(), t(key.trim()));
      });
    });
    document.documentElement.lang = lang === "en" ? "en" : "zh-Hant";
    document.title = t("meta.title");
    document.querySelector('meta[name="description"]')?.setAttribute("content", t("meta.desc"));
  }

  function setLang(next) {
    if (next !== "en" && next !== "zh") return;
    lang = next;
    try { localStorage.setItem(STORE_KEY, lang); } catch {}
    apply();
    listeners.forEach((fn) => fn(lang));
  }

  root.I18N = {
    t, term, formula, formulaText, apply, setLang,
    get lang() { return lang; },
    onChange: (fn) => listeners.push(fn),
    CN_NUM: ["一", "二", "三", "四", "五"],
  };
})(typeof globalThis !== "undefined" ? globalThis : window);
