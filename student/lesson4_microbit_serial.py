# 第 4 課：讓電腦聽到 micro:bit 說話
# 先安裝：pip install pyserial    （或在專案資料夾執行 uv sync）
# 執行：python student/lesson4_microbit_serial.py
#
# 把 micro:bit 用 USB 接上電腦，燒錄 firmware/microbit/main.py 之後執行這支程式，
# 按 micro:bit 的 A、B 鍵，電腦就會印出 micro:bit 傳來的指令；
# 按 B 時，電腦會回傳 LIGHT:GREEN，micro:bit 的綠燈就會亮。

import glob
import sys

import serial
from serial.tools import list_ports

# 找 micro:bit 的序列埠（Windows 是 COM3 這種名字，Mac 是 /dev/cu.usbmodem...）
port = None
for p in list_ports.comports():
    if p.vid == 0x0D28:  # micro:bit 的 USB 編號
        port = p.device
if port is None:
    ports = glob.glob("/dev/cu.usbmodem*") + glob.glob("/dev/ttyACM*")
    port = ports[0] if ports else None
if port is None:
    sys.exit("找不到 micro:bit，請確認 USB 線有接好（有些 USB 線只能充電不能傳資料）")

print("連接到", port, "，請按 micro:bit 的按鈕（Ctrl+C 結束）")
ser = serial.Serial(port, 115200, timeout=1)

colors = ["GREEN", "YELLOW", "RED"]
n = 0
while True:
    line = ser.readline().decode("utf-8", "ignore").strip()
    if not line:
        continue
    print("micro:bit 說：", line)
    if line == "GO":
        color = colors[n % 3]  # 輪流回傳綠、黃、紅，測試三顆燈
        ser.write(("LIGHT:" + color + "\n").encode())
        print("  → 電腦回覆：LIGHT:" + color)
        n += 1
