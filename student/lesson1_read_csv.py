# 第 1 課：讀取我們調查的菜單資料
# 執行：python student/lesson1_read_csv.py
#
# 學習重點：CSV 檔就像 Excel 表格，每一列是一道菜，每一欄是一種資料。

import csv

with open("data/processed/dishes.csv", encoding="utf-8-sig") as f:
    dishes = list(csv.DictReader(f))  # 每道菜變成一個「字典」：{"餐廳": ..., "餐點名稱": ...}

print("總共有", len(dishes), "道菜")
print()

# 印出前 5 道菜
for dish in dishes[:5]:
    print(dish["餐廳"], "|", dish["餐點名稱"], "|", dish["價格區間"], "|", dish["健康標籤"])

# 🧪 練習：
#   1. 改成印出前 10 道菜
#   2. 只印出「72度C舒肥健康餐」的菜（提示：if dish["餐廳"] == "72度C舒肥健康餐":）
