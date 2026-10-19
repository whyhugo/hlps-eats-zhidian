# 「脂」點迷津！外食族吃什麼—智慧營養選餐解憂亭

智慧營養選餐系統。在竹北遠百美食街，選「健身」或「養生」、轉旋鈕設定預算與辣度，按一下就推薦最適合的 3 道餐點，並用紅黃綠燈、聲音與健康指針告訴你健不健康。

學生親自調查 **12 家餐廳、231 道餐點**，幫每道菜標記油脂、蛋白質、鹽分、澱粉、辣度與烹調方式，並設計加權公式與推薦流程圖；本專案把它們做成可實際操作的作品。

![系統架構](docs/images/diagrams/system.svg)

## 功能

| 功能 | 說明 |
|---|---|
| 推薦引擎 | 依學生流程圖：選模式 → 加權計分 → 排序 → 預算／辣度／類型篩選 → 前 3 名 → 紅黃綠燈 |
| 展示網頁 | 推薦結果、每一步篩選剩幾道、分數拆解；我的餐盤、AI 小教練、全部菜單 |
| micro:bit | 按鈕、旋鈕輸入；LED 燈號、蜂鳴器、伺服馬達指針輸出；V1、V2 皆可，零件全部選用 |
| 資料檢查 | 自動合併學生的兩份表單，產生問題報告 |

## 快速開始

```bash
uv sync --all-extras
```

```bash
uv run fitwell serve
```

開啟 http://localhost:8000 。沒有 micro:bit 時可用網頁右下角的虛擬 micro:bit。

不想安裝任何東西？線上版（Cloudflare Pages + Web Serial）用 Chrome／Edge 打開網址就能連 micro:bit，見 [操作手冊 12](docs/MANUAL.md#12-cloudflare-線上版學生免安裝)。

全新 Windows 電腦的安裝步驟見 [操作手冊 2.1](docs/MANUAL.md#21-windows-1011全新電腦)；micro:bit 燒錄（拖曳 .hex 或 MakeCode）見 [操作手冊 4](docs/MANUAL.md#4-燒錄-microbit)。

## 文件

| 文件 | 內容 |
|---|---|
| [docs/MANUAL.md](docs/MANUAL.md) | **操作手冊**：材料、安裝、接線、燒錄、啟動、使用、設定、展示、疑難排解 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | **系統架構與原理**：架構圖、推薦演算法、資料管線、通訊協定、硬體設計、擴充方向 |

## 專案結構

```
config/scoring.json      加權公式、燈號門檻、預設條件
config/hardware.json     micro:bit 零件設定（旋鈕、蜂鳴器、指針方向），不用重新燒錄
.env.example             電腦端設定範本（埠號、序列埠、AI 金鑰）
data/raw/                學生的原始表單（健身表、養生表）
data/processed/          清理後的 dishes.csv 與資料檢查報告（自動產生）
src/fitwell/             Python 程式：資料、評分、推薦、伺服器、序列埠、AI
web/                     展示網頁（免編譯）
firmware/microbit/       micro:bit 韌體：main.py、makecode.ts、V1 用 fitwell-microbit-v1.hex
scripts/                 產生接線圖與架構圖
student/                 給學生的程式小課（讀資料 → 算分數 → 流程圖 → micro:bit 通訊）
docs/                    操作手冊、系統架構、圖表、原始參考資料
tests/                   自動測試
```
