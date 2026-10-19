# Fit & Well 點餐導航 — micro:bit 控制端（MicroPython）v3.0
#
# 燒錄：https://python.microbit.org 貼上這個檔案 → Send to micro:bit。
#       燒錄後要「完全關掉瀏覽器，再拔插 USB」，電腦才收得到訊息。
# V1、V2 都可以用。V1 記憶體很小，加功能前請先實機測試。
#
# 接線（圖見 docs/images/wiring/）：
#   必接：P0 綠燈、P1 黃燈、P2 紅燈（各串電阻接 GND）
#   選用（沒接會自動略過）：P13 健身鈕、P14 養生鈕、P12 伺服馬達、P16 蜂鳴器、
#        P4 預算旋鈕、P10 辣度旋鈕（旋鈕中間腳都要串 10kΩ，並在設定打開）
#
# 操作：A 切模式（F/W）、B 推薦、健身／養生鈕直接推薦、
#       預算旋鈕：1~4 段 + A（不限）、辣度旋鈕：0 不辣 ~ 5 + A（都可以）

from microbit import *
import gc
import music

gc.collect()  # 先清掉編譯程式時留下的暫存，後面建立函式才有連續的記憶體（V1 必要）

# ============ 功能開關 ============
# 平常請改電腦上的 config/hardware.json：連上電腦時會自動把設定送過來（CFG 指令），不用重新燒錄。
# 下面是「沒接電腦時」用的預設值：
#   KNOB       有接「預算旋鈕」（P4）才改成 "1"（沒接卻打開，預算會亂跳）
#   SKNOB      有接「辣度旋鈕」（P10）才改成 "1"
#   BUZZER     蜂鳴器："passive" 無源（類比）／"active" 有源（數位）／"off" 不要聲音
#   SERVO_REV  指針方向相反時改成 "1"
#   BEEP       每一聲的長度（毫秒），越長聽起來越大聲
CFG = {"KNOB": "0", "SKNOB": "0", "BUZZER": "passive", "SERVO_REV": "0", "BEEP": "150"}
# 腳位：0 綠 1 黃 2 紅 3 健身鈕 4 養生鈕 5 伺服 6 蜂鳴器 7 預算旋鈕 8 辣度旋鈕
# 腳位：產生 .hex 時（scripts/build_microbit_hex.py）會依 config/hardware.json 的 pins 自動替換這一行。
# V1 記憶體很小，連「執行中換腳位」的程式都放不下，所以腳位在燒錄前就決定好。
P = [pin0, pin1, pin2, pin13, pin14, pin12, pin16, pin4, pin10]
for p in P[3:5]:  # 外接按鈕：內部上拉，沒接按鈕時一直讀到 1（= 沒按）
    p.read_digital()
    p.set_pull(p.PULL_UP)

mode = "FITNESS"
score = -1      # 電腦送來的健康百分比 0~100（-1 = 還沒收到）
waiting = 0     # 送出 GO 的時間（0 = 沒在等）
buf = b""
servo_off = 0
knob_t = 0
gc_t = 0
prev = [1, 1]   # 外接按鈕上一次的狀態
# 旋鈕：[段數, 上次讀到的段, 目前的段, 指令]；最後一段 = 不限／都可以
KN = [[5, -1, 2, "BUDGET:"], [7, -1, 2, "SPICY:"]]
MODES = ("FITNESS", "WELLNESS")
# 蜂鳴器在 2000~3000Hz 附近最響（共振頻率），所以音高都選在這附近
BEEPS = {"GREEN": (2637, 2), "YELLOW": (2093, 1)}





def beep(freq, n=1):
    for i in range(n):
        if CFG["BUZZER"] == "off":
            return
        if CFG["BUZZER"] == "active":
            P[6].write_digital(1)
            sleep(int(CFG["BEEP"]))
            P[6].write_digital(0)
        else:
            music.pitch(freq, int(CFG["BEEP"]), P[6])  # 從蜂鳴器腳位輸出，綠燈不會跟著閃
        sleep(40)


def set_light(c):
    P[0].write_digital(int(c == "GREEN"))
    P[1].write_digital(int(c == "YELLOW"))
    P[2].write_digital(int(c == "RED"))


def servo(a):
    # V1 的蜂鳴器聲音會改掉訊號節奏，所以要「先播聲音、再轉馬達」，每次都重設 20ms
    global servo_off
    if CFG["SERVO_REV"] == "1":
        a = 180 - a
    P[5].write_analog(26 + a * 102 // 180)  # 0.5ms ~ 2.5ms 脈波
    P[5].set_analog_period(20)
    servo_off = running_time() + 700         # 轉到定位後停止送訊號，避免抖動


def show_mode():
    display.show("F" if mode == "FITNESS" else "W")


def go(cmd):
    global waiting
    print(cmd)
    display.show(Image.ARROW_E)
    set_light("OFF")
    servo(0)
    waiting = running_time()


def level(i, z):
    # 旋鈕換段：告訴電腦，點陣顯示一下（最後一段顯示 A = 不限／都可以）
    k = KN[i]
    k[2] = z
    t = "ANY" if z == k[0] - 1 else str(z)
    print(k[3] + t)
    display.show("A" if t == "ANY" else str(z + 1 - i))  # 預算顯示 1~4、辣度顯示 0~5
    beep(2637)
    sleep(500)
    show_mode()


def handle(line):
    global waiting, score
    if line == "HELLO?":
        print("HELLO:3.0")
        print("MODE:" + mode)
    elif line[:4] == "CFG:":  # 電腦送來的設定（config/hardware.json），例如 CFG:KNOB:1
        k, v = line[4:].split(":", 1)
        if CFG.get(k) != v:  # 電腦每 15 秒重送一次，沒變就不重寫（省記憶體）
            CFG[k] = v
    elif line[:6] == "SCORE:":
        score = int(line[6:])
    elif line[:6] == "LIGHT:":
        c = line[6:]
        waiting = 0
        set_light(c)
        if c == "OFF":
            return
        beep(*BEEPS.get(c, (1047, 3)))
        if score >= 0:
            servo(score * 180 // 100)  # 聲音播完才轉，不然指針不會動
    elif line[:5] == "SHOW:":
        display.show(line[5:])


def buttons():
    global mode
    if button_a.was_pressed():
        mode = "WELLNESS" if mode == "FITNESS" else "FITNESS"
        print("MODE:" + mode)
        beep(2637)
        show_mode()
    if button_b.was_pressed():
        go("GO")
    # 外接按鈕：按下的瞬間（1 → 0）才觸發
    for i in (0, 1):
        v = P[3 + i].read_digital()
        if v < prev[i]:
            mode = MODES[i]
            go("GO:" + mode)
        prev[i] = v


def knobs(now):
    # 旋鈕預設接在 P4、P10（點陣也用這兩隻腳），要先關點陣才能讀
    global knob_t
    if waiting or now - knob_t < 500 or (CFG["KNOB"] + CFG["SKNOB"]) == "00":
        return
    knob_t = now
    display.off()
    a = P[7].read_analog()
    b = P[8].read_analog()
    display.on()
    for i in (0, 1):
        k = KN[i]
        if CFG["SKNOB" if i else "KNOB"] != "1":
            continue
        z = min(k[0] - 1, (b if i else a) * k[0] // 1024)
        if z == k[1] and z != k[2]:  # 連續兩次一樣才算數，避免抖動
            level(i, z)
        k[1] = z


def read_serial():
    # 讀電腦傳來的指令（一行一個）
    global buf
    if uart.any():
        buf += uart.read(32)  # 一次只讀一小段，記憶體不夠時也配得到
        while b"\n" in buf:
            raw, buf = buf.split(b"\n", 1)
            line = str(raw, "utf-8").strip()
            if line:
                handle(line)


def tick(now):
    # 等太久沒回應、伺服馬達停止訊號
    global waiting, servo_off
    if waiting and now - waiting > 3000:  # 3 秒沒回應：電腦端可能沒開
        waiting = 0
        display.show(Image.CONFUSED)  # 停在這個表情，下一次操作就會換掉
    if servo_off and now > servo_off:
        P[5].write_digital(0)
        servo_off = 0


def main():
    global buf, gc_t
    # ============ 開機自我檢查：每個零件動一下，看哪個沒接好 ============
    gc.collect()  # 先整理編譯程式後留下的零碎記憶體（V1 必要）
    for c in ("GREEN", "YELLOW", "RED"):
        set_light(c)
        sleep(250)
    set_light("OFF")
    beep(2637)
    servo(90)
    print("HELLO:3.0")
    print("MODE:" + mode)
    show_mode()

    # ============ 主迴圈 ============
    while True:
        try:
            now = running_time()
            buttons()
            knobs(now)
            read_serial()
            tick(now)
            if now - gc_t > 1000:  # 每秒整理一次記憶體
                gc.collect()
                gc_t = now
        except MemoryError:
            # V1 記憶體不夠時不要當機：清掉緩衝區、整理記憶體後繼續跑。
            # 一直不夠時，電腦端收到大量 WARN:MEMORY 會自動讓程式重開。
            buf = b""
            gc.collect()
            print("WARN:MEMORY")
        sleep(40)


main()
