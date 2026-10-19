# 第 3 課：把我們畫的流程圖變成程式
# 執行：python student/lesson3_flowchart.py
#
#   輸入模式 → 計算分數 → 排序 → 超出預算？→ 超出辣度？→ 符合類型？→ 取前 3 → 紅黃綠燈

import csv

PRICES = ["100以下", "101-300", "301-500", "500以上"]

with open("data/processed/dishes.csv", encoding="utf-8-sig") as f:
    dishes = [d for d in csv.DictReader(f) if not d["重複於"]]  # 去掉重複的菜


def score(dish, mode):
    fat, salt, starch = int(dish["油脂加權"]), int(dish["鹽分加權"]), int(dish["澱粉加權"])
    if mode == "健身":
        return fat * 2 + int(dish["蛋白質加權"]) * 3 + salt + starch
    else:
        return fat - int(dish["辣度加權"]) + salt + starch + int(dish["烹調加權"]) * 3


def light(points, mode):
    green, yellow = (13, 9) if mode == "健身" else (8, 4)
    if points >= green:
        return "🟢 綠燈"
    if points >= yellow:
        return "🟡 黃燈"
    return "🔴 紅燈"


# 1. 輸入模式和條件
mode = input("請選擇模式（健身／養生）：").strip() or "健身"
budget = input("預算上限（100以下／101-300／301-500／500以上，直接按 Enter = 不限）：").strip()
max_spicy = input("最多可以接受幾辣？（0 = 不辣 ~ 5，直接按 Enter = 不限）：").strip()
main_type = input("想吃的類型（例如 肉類、海鮮類，直接按 Enter = 不限）：").strip()

# 2. 計算每道菜的分數，並依分數排序
for d in dishes:
    d["分數"] = score(d, mode)
dishes.sort(key=lambda d: d["分數"], reverse=True)

# 3. 一道一道檢查：是否加入候選？
result = []
for d in dishes:
    if budget and (not d["價格區間"] or PRICES.index(d["價格區間"]) > PRICES.index(budget)):
        continue  # 超出預算 → 不加入候選
    if max_spicy and int(d["辣度"]) > int(max_spicy):
        continue  # 太辣 → 不加入候選
    if main_type and d["主餐類型"] != main_type:
        continue  # 類型不符 → 不加入候選
    if not main_type and d["主餐類型"] in ("飲料類", "甜點類"):
        continue  # 沒指定類型時，主餐不推薦飲料和甜點
    result.append(d)
    if len(result) == 3:
        break  # 選到 3 道就停

# 4. 顯示結果
print()
if len(result) < 3:
    print(f"⚠️ 只找到 {len(result)} 道，試試看放寬預算或辣度！")
for i, d in enumerate(result, start=1):
    print(f"第 {i} 名：{d['餐廳']} - {d['餐點名稱']}（{d['價格區間']}）{d['分數']} 分 {light(d['分數'], mode)}")
