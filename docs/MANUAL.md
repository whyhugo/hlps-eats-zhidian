# 操作手冊

> 從零開始組裝、燒錄、啟動與展示「Fit & Well 點餐導航」。系統原理見 [ARCHITECTURE.md](ARCHITECTURE.md)。

![系統架構](images/diagrams/system.svg)

## 1. 材料

| 類別 | 零件 | 規格 | 數量 | 必要性 |
|---|---|---|---|---|
| 主控 | micro:bit | V1 或 V2 | 1 | 必要 |
| 主控 | USB 線 | Micro-USB，**可傳資料** | 1 | 必要 |
| 主控 | 擴充板 | KittenBot IOBIT V2.0 或 ELECFREAKS Breadboard Adapter | 1 | 必要 |
| 基本電路 | LED | 5mm 紅、黃、綠 | 各 1 | 必要 |
| 基本電路 | 電阻 | 100Ω～220Ω | 3 | 必要 |
| 加分 | 按鈕 | 輕觸按鈕（2 腳或 4 腳） | 2 | 選用 |
| 加分 | 伺服馬達 | SG90／EF92A（180°） | 1 | 選用 |
| 加分 | 電池盒 | 2～3 顆 AA | 1 | 接伺服馬達時必要 |
| 加分 | 蜂鳴器 | 無源（類比）或有源（數位） | 1 | 選用 |
| 加分 | 可變電阻 | B10K，3 腳 | 2 | 選用（預算、辣度旋鈕各 1） |
| 加分 | 電阻 | 10kΩ | 2 | 接旋鈕時必要 |
| 電腦 | 筆電 | macOS／Windows，可安裝 Python 3.10+ | 1 | 必要 |

ELECFREAKS micro:bit Starter Kit 內含上表除 micro:bit、電腦外的零件，但**可變電阻只有 1 顆**，要做兩個旋鈕需另購 1 顆。

## 2. 安裝電腦端程式

電腦只需要 **uv**（它會自動下載正確版本的 Python）。不需要另外安裝 Python、Node.js 或任何驅動程式（Windows 10／11、macOS 都內建 micro:bit 的 USB 序列埠驅動）。

### 2.1 Windows 10／11（全新電腦）

1. **複製專案**：把整個專案資料夾複製到電腦，例如 `C:\fitwell`（路徑盡量不要有中文或空白）。
2. **開啟 PowerShell**：開始選單搜尋「PowerShell」→ 開啟（不需要系統管理員）。
3. **安裝 uv**（官方安裝指令，裝在使用者資料夾，不影響系統）：
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   裝完**關掉 PowerShell 再重開一次**，輸入 `uv --version` 有出現版本號就成功。
4. **安裝專案需要的套件**（第一次需要網路，約 1～2 分鐘）：
   ```powershell
   cd C:\fitwell
   uv sync --all-extras
   ```
5. **插上 micro:bit 確認偵測得到**：
   ```powershell
   uv run fitwell ports
   ```
   會看到類似 `COM3  mbed Serial Port` 的一行。
6. **啟動**：
   ```powershell
   uv run fitwell serve
   ```
   第一次啟動若跳出「Windows 安全性警示（防火牆）」：只在這台電腦上用就按「取消」也沒關係；要讓同網路的平板連進來才選「允許（私人網路）」。
7. 用 Edge 或 Chrome 開啟 http://localhost:8000 ，按 F11 全螢幕。

> 展場沒有網路也能用：第 4 步裝好之後，啟動與網頁都不需要網路（字型、圖示、動畫都放在專案裡）；只有 AI 小教練會自動改用規則版。

### 2.2 macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh   # 安裝 uv（裝完重開終端機）
cd 專案資料夾
uv sync --all-extras
uv run fitwell serve
```

### 2.3 電腦端設定（選用）

埠號、指定序列埠（例如 Windows 的 `COM3`）、AI 金鑰寫在 `.env`，範本見 `.env.example`；不建立也能使用。

## 3. 接線

### 3.1 基本電路（必接）

![基本電路](images/wiring/01_base_leds.svg)

- LED 長腳（+）接電阻，短腳（−）接 GND。
- **LED 不可接 3V**：3V 是常時供電，燈會一直亮、程式無法控制。
- 使用 IOBIT 時，板上 **P0 蜂鳴器開關要撥到「關」**（P0 接了綠燈）。

### 3.2 加分零件（選用）

沒接的零件程式會自動略過；只接基本電路即可完整運作。

![腳位總覽](images/wiring/00_overview.svg)

| 零件 | 腳位 | 接線圖 | 設定（`config/hardware.json`） |
|---|---|---|---|
| 健身／養生按鈕 | P13、P14，另一腳 GND | [02](images/wiring/02_buttons.svg) | — |
| 伺服馬達指針 | 橘 P12、棕 GND、紅 電池 + | [03](images/wiring/03_servo.svg) | `servo_reverse` |
| 蜂鳴器 | + P16、− GND | [05](images/wiring/05_buzzer.svg) | `buzzer`、`beep_ms` |
| 預算旋鈕 | 中間腳 → 10kΩ → P4；兩側 3V、GND | [06](images/wiring/06_budget_knob.svg) | `use_budget_knob: true` |
| 辣度旋鈕 | 中間腳 → 10kΩ → P10；兩側 3V、GND | [07](images/wiring/07_spicy_knob.svg) | `use_spicy_knob: true` |

- **伺服馬達**用電池盒供電，電池盒 − 與 micro:bit GND 共地；不要接 micro:bit 3V 或 IOBIT 5V（啟動電流會讓系統重開或斷電）。
- **旋鈕一定要串 10kΩ**：P4、P10 同時是點陣腳位，直接相接可能損壞 micro:bit。
- 4 腳按鈕跨在麵包板中間凹槽上，取對角線兩腳。

## 4. 燒錄 micro:bit

兩種程式擇一即可，功能與電腦溝通方式完全相同：

| 程式 | 檔案 | 適合 | 說明 |
|---|---|---|---|
| **MicroPython .hex**（已實機測試） | `firmware/microbit/fitwell-microbit-v1.hex` | V1、V2 | 拖曳燒錄，不用開網頁 |
| **MakeCode** | `firmware/microbit/makecode.ts` | V1、V2 | 編譯成機器碼，**V1 也不會記憶體不足**；學生可切成積木看程式 |

### 4.1 拖曳 .hex（Windows／macOS 相同，最簡單）

1. 用 USB 線接上 micro:bit，電腦會出現名為 **MICROBIT** 的隨身碟。
2. 把 `fitwell-microbit-v1.hex` 拖進 **MICROBIT**（Windows：檔案總管；macOS：Finder）。
3. micro:bit 背面黃燈閃爍約 10 秒，完成後自動重開：三顆燈依序亮、嗶一聲、點陣顯示 `F`。

不要用 python.microbit.org 燒錄 V1：網頁版的 MicroPython 比較新、可用記憶體更少，V1 很容易出現 `WARN:MEMORY`。

### 4.2 MakeCode（避開 V1 記憶體限制）

1. 用 Edge 或 Chrome 開啟 https://makecode.microbit.org → **新增專案**。
2. 上方切到 **JavaScript**，刪掉原本內容，貼上 `makecode.ts` 全部內容，再切回 **積木** 確認沒有錯誤。
3. 按左下 **下載**，會得到一個 `.hex` 檔（例如 `microbit-專案名稱.hex`）。
4. 把這個 `.hex` 照 4.1 拖進 **MICROBIT** 磁碟。
5. 第一次開機做完自我檢查後，執行 `uv run fitwell serve` 確認網頁顯示「micro:bit 已連接」。

建議用「下載 .hex 再拖曳」，**不要按 MakeCode 的「配對裝置／連線」**：配對後瀏覽器會用 WebUSB 佔住 micro:bit，電腦收不到任何按鍵（見第 10 節）。若已經配對過，請**完全結束瀏覽器**（Windows：關閉所有視窗並確認工作列沒有殘留；macOS：Cmd+Q），再拔插 USB。

> MakeCode 版功能與 MicroPython 版相同，但目前展示用的是已實機測試的 MicroPython .hex；換成 MakeCode 前請在展示前完整測一次按鍵、燈號、蜂鳴器、指針與兩個旋鈕。

### 4.3 修改 MicroPython 程式後重新產生 .hex

```bash
uv tool run --from uflash==1.3.0 uflash firmware/microbit/main.py 輸出資料夾
```

把產生的 `micropython.hex` 改名覆蓋 `fitwell-microbit-v1.hex`。V1 記憶體很小，加功能後一定要實機測試。

## 5. 啟動與檢查

```bash
uv run fitwell serve
```

開啟 http://localhost:8000 ，依序確認：

| 檢查項目 | 正常狀態 |
|---|---|
| 開機自我檢查 | 綠、黃、紅燈依序亮一下後熄滅；指針轉到中間；嗶一聲；點陣顯示 `F` |
| 網頁右上角 | 「micro:bit 已連接」 |
| 按 A | 點陣在 `F`（健身）與 `W`（養生）切換，網頁同步 |
| 按 B 或健身／養生鈕 | 網頁出現前 3 名；micro:bit 亮燈、嗶聲、指針轉動、點陣顯示 3 |
| 轉預算旋鈕 | 點陣顯示 `1`～`4`、`A`（不限），網頁同步 |
| 轉辣度旋鈕 | 點陣顯示 `0`～`5`、`A`（都可以），網頁同步 |

沒有 micro:bit 時，網頁右下角的**虛擬 micro:bit** 可完成相同操作。

## 6. 使用方式

### 6.1 micro:bit

| 操作 | 功能 |
|---|---|
| A 鍵 | 切換模式：健身 `F`／養生 `W` |
| B 鍵 | 用目前條件推薦 |
| A+B | 切換預算：1=100以下、2=101-300、3=301-500、4=500以上、A=不限 |
| 健身鈕／養生鈕 | 切到該模式並立即推薦 |
| 預算旋鈕 | 5 段：100以下 → 101-300 → 301-500 → 500以上 → 不限 |
| 辣度旋鈕 | 7 段：不辣 → 1 → 2 → 3 → 4 → 5 → 都可以 |

| 回饋 | 意義 |
|---|---|
| 綠／黃／紅燈 | 推薦結果的健康等級 |
| 指針角度 | 健康百分比，越右越健康 |
| 綠燈「叮叮」、黃燈「嗶」、紅燈低音三聲 | 同燈號 |
| 點陣 😕 | 3 秒沒收到電腦回應（電腦端未啟動） |

### 6.2 網頁

**頂部**：作品名稱、全站「健身／養生」模式切換（同時影響推薦、我的餐盤、全部菜單的公式）、micro:bit 與 AI 連線狀態（滑鼠移到圖示上看詳細說明）。畫面上的 ⓘ 圖示都可以滑過或用 Tab 鍵聚焦，展開說明卡。

| 分頁 | 功能 |
|---|---|
| 求籤推薦 | 選預算（順序同旋鈕：100以下→101–300→301–500→500以上→不限）、辣度（不辣→1～5→都可以）、主餐類型（可複選）→ 按「求籤」：籤筒搖動，三支籤依序飛出並蓋上燈號朱印；上方顯示每一步篩選剩幾道；點分數旁的計算機圖示看加權拆解；不足 3 道時提示可放寬的條件。重新整理網頁會保留上一次結果 |
| 我的餐盤 | 把多道菜組成一餐，用**目前模式**計算平均分數、健康指數與燈號；切換模式會自動重新評估。2 道以上高油、高鹽或多澱粉、健身模式缺蛋白質、養生模式太辣時提出警告。結果同步到 micro:bit 燈號與指針。餐盤存在這台電腦的瀏覽器裡 |
| AI 小教練 | 用一句話描述需求（例：「帶阿嬤吃飯，要清淡不辣」），轉成篩選條件並從菜單中挑選、說明理由。設定 `ANTHROPIC_API_KEY` 時使用 Claude，否則使用關鍵字規則；兩者都只會推薦資料庫裡的菜 |
| 全部菜單 | 所有菜色與分數，可搜尋、切換公式（健身 v1／v2、養生）比較排名；切換模式時自動換成該模式的公式 |
| 怎麼運作 | 流程圖、公式（滑過 ⓘ 看公式說明）、資料檢查報告 |

**虛擬 micro:bit**：右下角「虛擬 micro:bit」按鈕，預設收合，點一下展開。A 鍵切換模式、B 鍵求籤、A+B 依旋鈕順序切換預算（最後一格為不限，點陣顯示 `A`）。

> 介面視覺規範見專案根目錄 `DESIGN.md`；標題字型為 Noto Serif TC Black 子集（`web/fonts/`，SIL OFL 授權）。若資料新增了新字的菜名，在 macOS 執行 `bash scripts/build_font_subset.sh` 重新產生（Windows 可用 Git Bash 執行；平常不用動）。

## 7. 設定檔

| 檔案 | 用途 | 生效方式 |
|---|---|---|
| `config/hardware.json` | `use_budget_knob`、`use_spicy_knob`、`buzzer`（passive／active／off）、`beep_ms`（每聲毫秒，30～500，越長越響）、`servo_reverse` | 重開 `fitwell serve`；電腦會自動送到 micro:bit，**不用重新燒錄** |
| `config/scoring.json` | 加權公式、使用中的公式、燈號門檻、預設條件、排除類型 | 重開 `fitwell serve` |
| `.env` | `FITWELL_PORT`、`FITWELL_HOST`、`FITWELL_SERIAL_PORT`、`FITWELL_NO_SERIAL`、`ANTHROPIC_API_KEY` | 重開 `fitwell serve` |

## 8. 更新菜單資料

1. 在 Google 試算表修正健身表、養生表 → 下載為 CSV。
2. 覆蓋 `data/raw/menu_fitness.csv`、`data/raw/menu_wellness.csv`。
3. 執行 `uv run fitwell build-data`，產生 `data/processed/dishes.csv` 與問題清單 `data_report.md`。

## 9. 展示流程

1. **開場（30 秒）**：「我們調查竹北遠百 12 家餐廳、231 道菜，幫每道菜依油脂、蛋白質、鹽分、澱粉、辣度、烹調方式打分數。選健身或養生，按一下就推薦最適合的 3 道，並用紅綠燈與指針告訴你健不健康。」
2. 請評審按 **健身／養生鈕**，轉 **預算、辣度旋鈕** 調整條件。
3. 說明螢幕上的篩選流程與「為什麼是這個分數？」。
4. **我的餐盤**：主餐加上炸物與甜點，燈號變差，說明「單點健康 ≠ 整餐健康」。
5. **AI 小教練**：輸入一句需求，AI 從資料庫挑菜並解釋。

| 評審常問 | 回答重點 |
|---|---|
| 分數怎麼算？ | 依標籤給加權，再乘上模式倍數：健身重蛋白質（×3）、油脂（×2）；養生重烹調方式（×3）並扣辣度 |
| 燒肉為什麼不會排第一？ | 高油扣分且油脂 ×2，舒肥雞胸、板腱牛排在前面 |
| 發現過什麼問題？ | 原公式「減鹽分」會讓越鹹分數越高，改為加鹽分；程式會自動檢查表單的重複與矛盾 |
| 換一家百貨公司？ | 用同一份表單調查新餐廳，程式不用改 |
| micro:bit 做什麼？ | 負責輸入（按鈕、旋鈕）與輸出（燈號、聲音、指針、點陣），透過 USB 和電腦用自訂指令溝通 |

**展示前檢查**：備用 USB 線、電池；瀏覽器沒有開著燒錄網頁；`fitwell serve` 已啟動且顯示「已連接」；開機自我檢查正常；瀏覽器全螢幕（F11）。

## 10. 疑難排解

| 狀況 | 原因與處理 |
|---|---|
| 網頁顯示「micro:bit 未連接」 | 換一條可傳資料的 USB 線；`uv run fitwell ports` 檢查是否偵測到 |
| 「USB 已連接，但 micro:bit 程式沒回應」 | 瀏覽器（MakeCode／python.microbit.org）佔住 micro:bit：完全結束瀏覽器再拔插 USB。`uv run fitwell monitor` 會指出佔用的程式 |
| 按鈕沒反應、點陣出現 😕 | `fitwell serve` 沒在執行 |
| 三顆燈一直亮、不會熄 | LED 接到 3V，改接 P0、P1、P2 |
| 某顆燈不亮 | LED 方向反了、電阻未插好、電阻與 LED 不在同一排 |
| 燈很暗 | 誤用 10kΩ（棕黑橙），換 100Ω～220Ω |
| 旋鈕沒反應 | `hardware.json` 未開啟該旋鈕；確認 10kΩ 與腳位（P4／P10）；設定最多 15 秒內自動同步到 micro:bit |
| 旋鈕亂跳或出現 `WARN:MEMORY` | V1 請改用 `fitwell-microbit-v1.hex` 燒錄（見第 4 節） |
| A／B 鍵有反應，但燈、聲音、指針、旋鈕都沒反應 | micro:bit 記憶體不足、卡住收不到電腦指令。按 micro:bit 背面 reset 鍵；新版程式與伺服器會自動偵測並重開。常發生請改用 MakeCode 版（4.2） |
| Windows 找不到 micro:bit（`fitwell ports` 沒有 COM） | 換可傳資料的 USB 線；Windows 7／8 需另裝 mbed 序列埠驅動，建議改用 Windows 10 以上 |
| Windows 執行 `uv` 顯示找不到指令 | 安裝 uv 後要關掉 PowerShell 重開 |
| 指針不動 | 確認電池盒有電、與 micro:bit 共地；方向相反改 `servo_reverse` |
| 蜂鳴器太小聲 | 加大 `beep_ms`；有源蜂鳴器設 `buzzer: "active"` |
| 拖曳 .hex 後出現 `FAIL.TXT`／`ASSERT.TXT` | 拔插 USB 再試；仍失敗可更新 micro:bit USB 韌體：https://microbit.org/get-started/user-guide/firmware/ |
| MakeCode 下載時「不相容的程式碼」 | 使用最新的 `makecode.ts`（只用 V1、V2 共通的積木） |

## 11. 指令速查

| 指令 | 用途 |
|---|---|
| `uv run fitwell serve` | 啟動網頁與 micro:bit 連線（`--port`、`--serial-port`、`--no-serial`） |
| `uv run fitwell build-data` | 重新清理資料並產生問題報告 |
| `uv run fitwell recommend -m fitness -b 101-300 -s 2` | 在終端機試推薦 |
| `uv run fitwell monitor` | 不經伺服器直接與 micro:bit 對話（診斷用，需先關閉 serve） |
| `uv run fitwell ports` | 列出序列埠 |
| `uv run pytest` | 自動測試 |
| `uv run python scripts/gen_wiring.py`、`gen_diagrams.py` | 重新產生接線圖、架構圖 |
