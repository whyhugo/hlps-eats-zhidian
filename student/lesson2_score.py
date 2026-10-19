# 第 2 課：用加權公式幫每道菜算分數
# 執行：python student/lesson2_score.py
#
# 健身分數 = 油脂×2 + 蛋白質×3 + 鹽分×1 + 澱粉×1

import csv

with open("data/processed/dishes.csv", encoding="utf-8-sig") as f:
    dishes = list(csv.DictReader(f))


def fitness_score(dish):
    fat = int(dish["油脂加權"])
    protein = int(dish["蛋白質加權"])
    salt = int(dish["鹽分加權"])
    starch = int(dish["澱粉加權"])
    return fat * 2 + protein * 3 + salt * 1 + starch * 1


def wellness_score(dish):
    fat = int(dish["油脂加權"])
    spicy = int(dish["辣度加權"])
    salt = int(dish["鹽分加權"])
    starch = int(dish["澱粉加權"])
    cooking = int(dish["烹調加權"])
    return fat * 1 - spicy * 1 + salt * 1 + starch * 1 + cooking * 3


# 幫每道菜加上分數
for dish in dishes:
    dish["分數"] = fitness_score(dish)

# 依分數由高到低排序
dishes.sort(key=lambda d: d["分數"], reverse=True)

print("健身分數前 10 名：")
for i, dish in enumerate(dishes[:10], start=1):
    print(i, dish["分數"], "分", dish["餐廳"], dish["餐點名稱"])

# 🧪 練習：
#   1. 改成用 wellness_score 算養生分數，看看排名有什麼不同
#   2. 把鹽分改成「−鹽分×1」（學生原版公式），看看哪些很鹹的菜跑到前面？為什麼？
