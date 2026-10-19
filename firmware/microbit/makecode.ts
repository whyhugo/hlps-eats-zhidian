// Fit & Well 點餐導航 — micro:bit 控制端（MakeCode 版本）v3.0
//
// ✅ micro:bit V1 和 V2 都可以用。功能和 main.py（MicroPython 版）相同。
// ✅ MakeCode 會編譯成機器碼，不用 MicroPython 直譯器，V1 不會有記憶體不足（MemoryError）的問題。
// ⚠️ MicroPython 版已實機測試；這個 MakeCode 版尚未實機測試。
//
// 使用方式：
//   1. 打開 https://makecode.microbit.org → 新增專案
//   2. 上方切到「JavaScript」，把這個檔案全部貼上，再切回「積木」
//   3. 下載到 micro:bit，完成後「完全關掉瀏覽器，再拔插 USB」
//
// 接線：
//   【基本】P0 綠 LED、P1 黃 LED、P2 紅 LED（各串一顆電阻接 GND）
//   【加分，可以不接】P13 健身按鈕、P14 養生按鈕（另一腳接 GND）、P12 伺服馬達、
//                    P16 蜂鳴器 +、P4 預算旋鈕、P10 辣度旋鈕（旋鈕中間腳都要串 10kΩ）

// 平常請改電腦上的 config/hardware.json：連上電腦時會自動把設定送過來，不用重新下載。
// 下面是「沒接電腦時」用的預設值。
let USE_BUDGET_KNOB = false  // 有接「預算旋鈕」（P4）才改成 true
let USE_SPICY_KNOB = false   // 有接「辣度旋鈕」（P10）才改成 true
let BUZZER = "passive"       // 蜂鳴器："passive" 無源（類比）／"active" 有源（數位）／"off" 不要聲音
let SERVO_REVERSE = false    // 指針方向相反時改成 true
let BEEP_MS = 150            // 每一聲的長度（毫秒），越長聽起來越大聲

let mode = "FITNESS"
let budget = 2   // 0~3 = 100以下、101-300、301-500、500以上；4 = 不限
let spicy = 2    // 0~5；6 = 都可以
let score = -1
let waiting = 0
let servoOff = 0
let budgetLast = -1
let spicyLast = -1
let b13 = 1
let b14 = 1

pins.analogSetPitchPin(AnalogPin.P16)   // 音樂從 P16 輸出，P0 的綠燈不會跟著閃
pins.setPull(DigitalPin.P13, PinPullMode.PullUp)
pins.setPull(DigitalPin.P14, PinPullMode.PullUp)

function beep(freq: number, n: number) {
    if (BUZZER == "off") {
        return
    }
    for (let i = 0; i < n; i++) {
        if (BUZZER == "active") {
            pins.digitalWritePin(DigitalPin.P16, 1)
            basic.pause(BEEP_MS)
            pins.digitalWritePin(DigitalPin.P16, 0)
        } else {
            music.playTone(freq, BEEP_MS)
        }
        basic.pause(40)
    }
}

function setLight(c: string) {
    pins.digitalWritePin(DigitalPin.P0, c == "GREEN" ? 1 : 0)
    pins.digitalWritePin(DigitalPin.P1, c == "YELLOW" ? 1 : 0)
    pins.digitalWritePin(DigitalPin.P2, c == "RED" ? 1 : 0)
}

function servo(a: number) {
    if (SERVO_REVERSE) {
        a = 180 - a
    }
    pins.servoWritePin(AnalogPin.P12, a)
    servoOff = input.runningTime() + 700   // 轉到定位後停止送訊號，避免抖動
}

function showMode() {
    if (mode == "FITNESS") {
        basic.showString("F")
    } else {
        basic.showString("W")
    }
}

function go(cmd: string) {
    serial.writeLine(cmd)
    basic.showArrow(ArrowNames.East)
    setLight("OFF")
    servo(0)
    waiting = input.runningTime()
}

// 預算換段：最後一段（4）= 不限，點陣顯示 A
function setBudget(z: number) {
    budget = z
    if (z == 4) {
        serial.writeLine("BUDGET:ANY")
        basic.showString("A")
    } else {
        serial.writeLine("BUDGET:" + z)
        basic.showNumber(z + 1)
    }
    beep(2637, 1)
    basic.pause(500)
    showMode()
}

// 辣度換段：最後一段（6）= 都可以，點陣顯示 A
function setSpicy(z: number) {
    spicy = z
    if (z == 6) {
        serial.writeLine("SPICY:ANY")
        basic.showString("A")
    } else {
        serial.writeLine("SPICY:" + z)
        basic.showNumber(z)
    }
    beep(2637, 1)
    basic.pause(500)
    showMode()
}

// 接收電腦傳來的指令
serial.onDataReceived(serial.delimiters(Delimiters.NewLine), function () {
    let line = serial.readUntil(serial.delimiters(Delimiters.NewLine)).trim()
    if (line == "HELLO?") {
        serial.writeLine("HELLO:3.0")
        serial.writeLine("MODE:" + mode)
    } else if (line.indexOf("CFG:") == 0) {   // 電腦送來的設定（config/hardware.json）
        let kv = line.substr(4, 30)
        let sep = kv.indexOf(":")
        let k = kv.substr(0, sep)
        let v = kv.substr(sep + 1, 20)
        if (k == "KNOB") {
            USE_BUDGET_KNOB = v == "1"
        } else if (k == "SKNOB") {
            USE_SPICY_KNOB = v == "1"
        } else if (k == "BUZZER") {
            BUZZER = v
        } else if (k == "SERVO_REV") {
            SERVO_REVERSE = v == "1"
        } else if (k == "BEEP") {
            BEEP_MS = parseInt(v)
        }
    } else if (line.indexOf("SCORE:") == 0) {
        score = parseInt(line.substr(6, 3))
    } else if (line.indexOf("LIGHT:") == 0) {
        let c = line.substr(6, 10)
        waiting = 0
        setLight(c)
        if (c == "OFF") {
            return
        }
        if (c == "GREEN") {
            beep(2637, 2)
        } else if (c == "YELLOW") {
            beep(2093, 1)
        } else {
            beep(1047, 3)
        }
        if (score >= 0) {
            servo(Math.idiv(score * 180, 100))   // 聲音播完才轉，V1 的聲音會打亂伺服馬達訊號
        }
    } else if (line.indexOf("SHOW:") == 0) {
        basic.showString(line.substr(5, 20))
    }
})

// A 鍵：切換模式
input.onButtonPressed(Button.A, function () {
    if (mode == "FITNESS") {
        mode = "WELLNESS"
    } else {
        mode = "FITNESS"
    }
    serial.writeLine("MODE:" + mode)
    beep(2637, 1)
    showMode()
})

// B 鍵：推薦
input.onButtonPressed(Button.B, function () {
    go("GO")
})

// A+B：切換預算（1=100以下 2=101-300 3=301-500 4=500以上 A=不限）
input.onButtonPressed(Button.AB, function () {
    setBudget((budget + 1) % 5)
})

// 外接按鈕、旋鈕、等太久沒回應
basic.forever(function () {
    let now = input.runningTime()

    // 外接按鈕：按下的瞬間（1 → 0）才觸發
    let v = pins.digitalReadPin(DigitalPin.P13)
    if (v == 0 && b13 == 1) {
        mode = "FITNESS"
        go("GO:FITNESS")
    }
    b13 = v
    v = pins.digitalReadPin(DigitalPin.P14)
    if (v == 0 && b14 == 1) {
        mode = "WELLNESS"
        go("GO:WELLNESS")
    }
    b14 = v

    // 旋鈕接在 P4、P10（點陣也用這兩隻腳），要先關點陣才能讀；連續兩次一樣才算數
    if ((USE_BUDGET_KNOB || USE_SPICY_KNOB) && waiting == 0) {
        led.enable(false)
        let rb = pins.analogReadPin(AnalogPin.P4)
        let rs = pins.analogReadPin(AnalogPin.P10)
        led.enable(true)
        showMode()
        if (USE_BUDGET_KNOB) {
            let zb = Math.min(4, Math.idiv(rb * 5, 1024))
            if (zb == budgetLast && zb != budget) {
                setBudget(zb)
            }
            budgetLast = zb
        }
        if (USE_SPICY_KNOB) {
            let zs = Math.min(6, Math.idiv(rs * 7, 1024))
            if (zs == spicyLast && zs != spicy) {
                setSpicy(zs)
            }
            spicyLast = zs
        }
    }

    if (waiting > 0 && now - waiting > 3000) {   // 3 秒沒回應：電腦端可能沒開
        waiting = 0
        basic.showIcon(IconNames.Confused)
        basic.pause(800)
        showMode()
    }
    if (servoOff > 0 && now > servoOff) {
        pins.digitalWritePin(DigitalPin.P12, 0)
        servoOff = 0
    }
    basic.pause(USE_BUDGET_KNOB || USE_SPICY_KNOB ? 500 : 60)
})

// ============ 開機自我檢查 ============
serial.redirectToUSB()
serial.setBaudRate(BaudRate.BaudRate115200)
serial.setRxBufferSize(128)   // 電腦一次會送 5 行設定，預設 20 bytes 的接收區會漏掉
setLight("GREEN")
basic.pause(250)
setLight("YELLOW")
basic.pause(250)
setLight("RED")
basic.pause(250)
setLight("OFF")
beep(2637, 1)
servo(90)
serial.writeLine("HELLO:3.0")
serial.writeLine("MODE:" + mode)
showMode()
