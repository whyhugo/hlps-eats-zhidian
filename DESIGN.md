---
name: 「脂」點迷津！外食族吃什麼—智慧營養選餐解憂亭
description: 把透明的營養推薦，用求籤、解籤、蓋朱印的儀式交付。
colors:
  ink: "#1e1b18"
  ink-2: "#2a2520"
  ink-3: "#3a332c"
  paper: "#f6e7c8"
  paper-2: "#fbf3e1"
  paper-3: "#fffaf0"
  on-ink: "#f6e7c8"
  on-ink-2: "#d9c7a3"
  muted: "#5e5246"
  line-soft: "rgb(30 27 24 / 22%)"
  red: "#c8362b"
  red-ink: "#a8291f"
  red-tint: "#f3d6c8"
  gold: "#b98a2e"
  green: "#2f7d5b"
  yellow: "#b7791f"
  yellow-ink: "#8a5a10"
typography:
  display:
    fontFamily: "Jieyou Serif, Noto Serif TC, Songti TC, PMingLiU, serif"
    fontSize: "30px"
    fontWeight: 900
    lineHeight: 1.3
  headline:
    fontFamily: "Jieyou Serif, Noto Serif TC, Songti TC, PMingLiU, serif"
    fontSize: "24px"
    fontWeight: 900
    lineHeight: 1.2
    letterSpacing: "0.03em"
  title:
    fontFamily: "Jieyou Serif, Noto Serif TC, Songti TC, PMingLiU, serif"
    fontSize: "22px"
    fontWeight: 900
    lineHeight: 1.35
  numeral:
    fontFamily: "Jieyou Serif, Noto Serif TC, Songti TC, PMingLiU, serif"
    fontSize: "28px"
    fontWeight: 900
    lineHeight: 1.15
    fontFeature: "tnum"
  body:
    fontFamily: "PingFang TC, Noto Sans TC, Microsoft JhengHei, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.6
  label:
    fontFamily: "PingFang TC, Noto Sans TC, Microsoft JhengHei, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.5
  code:
    fontFamily: "ui-monospace, SF Mono, Menlo, monospace"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.5
rounded:
  none: "0"
  brand-seal: "6px"
  badge: "11px"
  round: "50%"
spacing:
  xs: "6px"
  sm: "8px"
  md: "14px"
  lg: "18px"
  xl: "24px"
  gutter: "32px"
components:
  button-draw:
    backgroundColor: "{colors.red}"
    textColor: "{colors.paper-3}"
    rounded: "{rounded.none}"
    padding: "14px"
  button-draw-hover:
    backgroundColor: "{colors.red-ink}"
    textColor: "{colors.paper-3}"
  mode-toggle:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-ink}"
    rounded: "{rounded.none}"
    padding: "10px 24px"
  mode-toggle-hover:
    backgroundColor: "{colors.ink-3}"
  mode-toggle-active:
    backgroundColor: "{colors.red}"
    textColor: "{colors.paper-3}"
  chip:
    backgroundColor: "{colors.paper-3}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "6px 13px"
  chip-hover:
    backgroundColor: "{colors.red-tint}"
  chip-active:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "6px 12px"
  button-ghost-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.paper}"
  tab:
    backgroundColor: "{colors.ink-2}"
    textColor: "{colors.on-ink-2}"
    padding: "12px 20px 11px"
  tab-active:
    textColor: "{colors.paper-3}"
  module:
    backgroundColor: "{colors.paper-2}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
  module-head-tag:
    backgroundColor: "{colors.red}"
    textColor: "{colors.paper-3}"
    padding: "4px 7px"
  slip:
    backgroundColor: "{colors.paper-3}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
  slip-first:
    backgroundColor: "{colors.red-tint}"
  slip-band:
    backgroundColor: "{colors.red}"
    textColor: "{colors.paper-3}"
    padding: "8px 14px"
  seal:
    size: "64px"
    rounded: "{rounded.none}"
  seal-first:
    size: "88px"
  seal-lg:
    size: "96px"
  tipcard:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-ink}"
    padding: "12px 14px"
  input:
    backgroundColor: "{colors.paper-3}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "12px 14px"
  table-head:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.on-ink}"
    padding: "8px 12px"
---

# Design System: 「脂」點迷津！外食族吃什麼—智慧營養選餐解憂亭

## Overview

**Creative North Star: "籤詩解憂亭"**

這套系統把一個資料透明的營養推薦，包裝成台灣人熟悉的「求籤、解籤」儀式：按下「求籤」，籤筒搖動，三支籤由下往上抽出，最後蓋上朱印燈號。整個畫面是一座小亭子：墨黑的殼層（頂部橫條、分頁列、資訊卡）框住米黃的籤紙工作區，朱紅是唯一會「說話」的顏色。

密度偏高、像日式資訊網頁：每個區塊都是 1px 墨線框住的方形模組，左上一個朱紅小籤頭標號，模組之間靠框線和留白分隔，而不是靠陰影或圓角卡片。標題、分數、籤名用極粗的宋體（楷明風），讓結果讀起來像一支籤；所有需要閱讀的說明文字則回到黑體，保持在 60–80 公分距離也清楚。

已確認拒絕的方向：一般「白底圓角卡片儀表板」式點餐介面。

**Key Characteristics:**
- 墨黑殼層＋米黃籤紙＋唯一的朱紅，金色只當框線。
- 方角、細墨線、平面模組；只有「籤」和浮層會浮起。
- 燈號一律是朱印：方框、微旋轉、圖示＋文字，從不只靠顏色。
- 粗宋體只給名字、數字、籤頭與印文；說明用黑體。
- 一個招牌動作：求籤（搖筒→抽籤→蓋印），其他動態都很短很安靜。

## Colors

色盤是「墨、紙、朱、金」四種傳統材料，加上三個燈號色；朱紅同時是主色與紅燈，因為在這個世界裡兩者都是同一盒印泥。

### Primary
- **朱砂印泥紅** (`red`)：唯一主色。求籤按鈕、啟用中的模式籤牌、籤頭（模組標號、籤條）、分頁底線、焦點框、選取反白，以及紅燈朱印。
- **深朱** (`red-ink`)：朱紅的文字與按下態。主按鈕 hover、米黃底上的紅色文字（被篩掉的數字、負分、警告），確保在淺底上的對比。
- **淡朱籤紙** (`red-tint`)：第一籤的底色、條件籤 hover 底色、致命錯誤提示底。

### Secondary
- **描金** (`gold`)：只做框線點綴。模式切換外框、啟用籤牌的內框、資訊卡與虛擬 micro:bit 的邊框、推薦理由的虛線框。

### Tertiary（燈號）
- **宜食綠** (`green`)：綠燈朱印與好標籤（如高蛋白）的線框文字。
- **適量黃** (`yellow`)：只用於填色面積（餐盤健康指針的長條）。
- **適量黃・墨** (`yellow-ink`)：黃燈的所有文字與印框，以及提醒框的邊線與圖示；`yellow` 在米黃底上當文字對比不足。

### Neutral
- **墨** (`ink`)：頂部殼層、資訊卡、表頭、啟用中的條件籤、主要文字與模組框線。
- **墨・二** (`ink-2`)：分頁列底色，讓分頁略退於頂部橫條。
- **墨・三** (`ink-3`)：殼層上的 hover 底與狀態框線。
- **籤紙** (`paper`)：頁面底色；同值的 `on-ink` 是墨底上的主要文字。
- **籤紙・二** (`paper-2`)：模組與流程數字列的底色。
- **籤紙・三** (`paper-3`)：籤、輸入框、條件籤等「可拿起來」的最淺紙。
- **舊紙墨字** (`on-ink-2`)：墨底上的次要文字（副標、未啟用分頁、狀態）。
- **淡墨** (`muted`)：米黃底上的次要說明、單位、資訊鈕。
- **淡墨線** (`line-soft`)：模組內部的分隔線、表格列線、次要框。

### Named Rules
**The One Vermilion Rule.** 朱紅是唯一主色。不要引入第二個強調色；需要「更強調」時用更大的朱紅面積或朱印，而不是新的顏色。

**The Gold Thread Rule.** 金色只是一條線：框線、內框、虛線框。金色不做底色面積，也不做文字。

**The Ink-for-Text Rule.** 黃燈與紅色文字在米黃底上一律用 `yellow-ink`／`red-ink`；`yellow` 與 `red` 只用在填色、印框和墨底上。

## Typography

**Display Font:** Jieyou Serif（自架的 Noto Serif TC Black 900 子集；退回 Noto Serif TC、Songti TC、PMingLiU）
**Body Font:** PingFang TC（退回 Noto Sans TC、Microsoft JhengHei、system-ui）
**Label/Mono Font:** ui-monospace（SF Mono、Menlo），只用於公式與資料報告

**Character:** 極粗的宋體像籤詩與印文，負責「結果」；黑體負責「說明」。兩者一硬一軟，評審一眼分得出哪裡是答案、哪裡是解釋。

### Hierarchy
- **Display** (900, 30px, 1.3)：第一籤的菜名。窄螢幕降為 24px。
- **Headline** (900, 24px, 1.2, 字距 0.03em)：頂部作品名。求籤按鈕同字族放大到 26px、字距 0.4em，是唯一拉開字距的大字。
- **Title** (900, 21–22px, 1.3–1.35)：結果標題、餐盤總結、一般籤的菜名、籤條（18–21px，字距 0.12em）。
- **Numeral** (900, 28px, 1.15, tabular)：篩選流程的剩餘道數。分數放大到 40px（一般籤）與 52px（第一籤）；分數拆解格 16–18px。
- **Body** (400, 16px, 1.6)：預設內文；說明段落與流程圖用 17px。模組標頭為黑體 700、16px。
- **Label** (400/700, 13–15px)：條件籤、籤的餐廳與標籤、狀態、單位、資訊卡（15px，1.65）。不使用全大寫或拉開字距的英文標籤。
- **Code** (600, 16px, 1.5)：加權公式。

### Named Rules
**The Brush-for-Verdicts Rule.** 粗宋體只給名字、數字、籤頭、印文與「求籤」動作。任何需要讀完一整句的文字都用黑體。

**The Subset Rule.** Jieyou Serif 是字型子集。新增任何用宋體顯示的字之前，先確認它在子集裡（或重新產生子集），否則會掉回系統宋體、筆畫粗細不一致。

**The Tabular Rule.** 會變動的數字（分數、剩餘道數、徽章、價格欄）一律 `tabular-nums`，翻動時不跳動。

## Layout

單頁、分頁切換（求籤推薦／我的餐盤／AI 小教練／全部菜單／怎麼運作）。頂部墨黑橫條為三欄格線（作品名｜模式切換置中｜狀態靠右），與下方分頁列一起 sticky。主區最寬 1500px 置中，左右 32px、上 24px，底部預留 120px 給右下角的虛擬 micro:bit 把手。

推薦頁為「340px 條件欄＋彈性結果區」兩欄，間距 24px；條件欄 sticky 跟著捲動。結果區上方是五格等寬的篩選流程數字列，下方三支籤以 1.5 : 1 : 1 排列、間距 18px，第一籤獨佔舞台。模組之間 14px，模組內 14px 留白，條件籤間 8px。

斷點：
- **≤1100px**：頂部改兩欄、模式切換換到第二列；分頁不再 sticky；條件與結果改單欄；三支籤直排；左右留白 20px。
- **≤600px**：模式切換撐滿寬、狀態只留圖示；分頁列右緣淡出提示可橫捲；流程數字縮到 20px；第一籤菜名 24px；左右留白 16px。

## Elevation & Depth

以平面為主，深度靠「墨框＋紙色深淺」表達：頁面 `paper`、模組 `paper-2`、可拿起的物件 `paper-3`。只有一組柔和陰影，給會「離開紙面」的東西：籤、資訊卡、虛擬 micro:bit。

### Shadow Vocabulary
- **籤影** (`box-shadow: 0 1px 0 rgb(30 27 24 / 8%), 0 8px 24px -12px rgb(30 27 24 / 28%)`)：籤、資訊卡、虛擬 micro:bit 的把手與面板。

### Named Rules
**The Paper-on-Paper Rule.** 模組、條件籤、流程列、表格都是平的。陰影只屬於「籤」與浮層；不要為了強調而給模組加陰影。

## Shapes

方角是預設：模組、籤、按鈕、條件籤、輸入框、資訊卡都是 0 圓角，邊框 1px（模組、條件籤）或 1.5px（籤、求籤按鈕、模式外框）。圓角只出現在有實物依據的地方：作品名朱印 6px、數字徽章膠囊 11px、資訊鈕與狀態點的圓形。

朱印燈號是方形印框（3px 印框＋內圈細線），旋轉 −8°，並套上 SVG `#ink` 噪點濾鏡讓邊緣有印泥不均的質感。籤頭與籤條是實心朱紅色塊。虛線用於「尚未決定」或「附註」：不限條件籤、空狀態框、推薦理由框、空餐盤印。

## Components

### Buttons
莊重、實心、像蓋章的力道。
- **Shape:** 方角（0）。
- **求籤（主要）:** 朱紅底、`paper-3` 字、1.5px 墨框，粗宋體 26px、字距 0.4em，左側一個 SVG 籤筒圖。hover 轉深朱，按下下沉 1px。小尺寸版（「問問看」）改黑體 700、16px。
- **Ghost:** 透明底、1px 墨框；hover 反轉為墨底米黃字。disabled 框線轉 `line-soft`、字轉 `muted`。表格內的「加入」按鈕是同一種語言的小號（14px）。
- **Hover / Focus:** 變色 0.15–0.2s；全站焦點為 3px 朱紅外框、外移 2px。

### Chips（條件籤）
- **Style:** `paper-3` 底、1px 墨框、15px 黑體，前綴朱紅 Lucide 圖示。
- **State:** hover 淡朱底；選取時反轉為墨底米黃字（圖示同步轉米黃）。「不限／都可以」這種收尾選項用虛線框，選取後轉實線。

### Cards / Containers（模組）
- **Corner Style:** 方角。
- **Background:** `paper-2`，1px 墨框。
- **Shadow Strategy:** 無（見 Paper-on-Paper Rule）。
- **Header:** 黑體 700、16px，下方 1px 墨線；最左一個朱紅實心籤頭（粗宋體 14px，一個字），資訊鈕推到最右。
- **Internal Padding:** 14px。

### Inputs / Fields
- **Style:** `paper-3` 底、1px 墨框、方角；AI 輸入框 17px、12px 14px 留白。搜尋與公式選單是「欄位外框＋朱紅前綴圖示＋無框輸入」。
- **Focus:** 外框整體出現 3px 朱紅焦點框（`:focus-within`）。

### Navigation
- **頂部模式切換:** 兩支大籤牌放在 1.5px 金框內，各有一圈半透明金內線。啟用的籤牌填朱紅、內框改為朱＋金雙線、上浮 1px；切換時以 GSAP 由 0.9 彈回 1。這是全站狀態，任何頁都看得到。
- **分頁:** `ink-2` 底，未啟用 `on-ink-2`，hover 轉 `on-ink`，啟用為 `paper-3` 粗體加 3px 朱紅底線。餐盤分頁帶朱紅膠囊數字徽章，數量變動時彈一下。

### 籤（Signature Component）
推薦、餐盤、AI 小教練共用同一張籤。`paper-3` 底、1.5px 墨框、籤影；頂端朱紅籤條寫「第一籤／第二籤」與「上籤／中籤／下籤」。內容依序：餐廳（label）、菜名（粗宋體）、標籤列（好標籤綠框、壞標籤紅框）、推薦理由（金虛線框）、大分數＋資訊鈕、分數拆解格（虛線分隔、tabular 數字、負分深朱）、右側朱印。第一籤底色轉淡朱、字級與印都放大。

### 朱印燈號（Signature Component）
64px（一般）／88px（第一籤）／96px（餐盤）方印，旋轉 −8°，印色依燈號：綠 `green`、黃 `yellow-ink`、紅 `red`；內含 Lucide 圖示＋「綠燈／宜食」兩行粗宋體。表格與說明中的小燈號是旋轉 45° 的空心菱形＋文字。

### 求籤動作（Signature Motion）
GSAP timeline：籤筒左右搖 6 次（每次 0.07s）、籤枝上跳 → 三支籤由下方 70px 升起並帶 −2.5°／2°／−1.5° 微斜回正（0.6s、間隔 0.14s、power3.out）→ 朱印由 1.9 倍放大蓋下（0.32s、back.out(2.2)）。流程數字以 0.7s 逐位滾動到新值。`prefers-reduced-motion` 時全部直接顯示最終狀態。

### 資訊卡
墨底、米黃字、1px 金框、籤影，最寬 300px；由資訊鈕或狀態鈕 hover／focus 打開，淡入並位移 4px（0.18s）。模組標頭右緣的資訊卡改向左展開。

### 虛擬 micro:bit
右下角固定的墨底金框把手，展開後是 264px 面板，內含模擬板（A／B 鍵、5×5 LED、三色燈、指令紀錄）。模擬板內的深色底、LED 紅與三色燈色是在模仿實體硬體，只限這塊模擬板使用，不屬於系統色。

## Do's and Don'ts

### Do:
- **Do** 讓朱紅 (`#c8362b`) 成為畫面上唯一的強調色，主動作、啟用狀態、籤頭、紅燈都用它。
- **Do** 把每個新區塊做成 1px 墨框的方形模組，左上放一個字的朱紅籤頭，說明收進右側資訊鈕。
- **Do** 用朱印呈現任何燈號判斷：方印、−8° 旋轉、圖示＋「X燈／判語」，永遠不只靠顏色。
- **Do** 名字與數字用 Jieyou Serif 900，句子用黑體 16–17px；變動數字加 `tabular-nums`。
- **Do** 在米黃底上的紅、黃文字改用 `red-ink` (`#a8291f`)、`yellow-ink` (`#8a5a10`)。
- **Do** 所有 GSAP 動態都檢查 `prefers-reduced-motion`，降級為直接顯示最終狀態。
- **Do** 第三方函式庫與字型放在本機（`web/vendor`、`web/fonts`），展場可能離線。

### Don't:
- **Don't** 做成白底、圓角、陰影卡片的點餐儀表板。
- **Don't** 引入第二個強調色，或把金色當底色、文字色使用。
- **Don't** 給模組、條件籤或表格加陰影或圓角；陰影只屬於籤與浮層。
- **Don't** 把籤頭做成標題上方獨立一行的小標（kicker／eyebrow）；它永遠與標題同一行、只有一個字或一個數字。
- **Don't** 用 emoji 取代 Lucide 圖示，除非情境真的無法用圖示表達。
- **Don't** 用 Jieyou Serif 顯示子集裡沒有的字。
