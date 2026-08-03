# Stage 1: get the sensors reading

Written for someone who has never opened the Arduino IDE. Work through it in
order. Nothing here touches Wi-Fi yet, because the point of this stage is to
prove the wiring before adding anything else.

Around 20 minutes, most of it waiting for downloads.

---

## Part 1 - Install the Arduino IDE

1. Go to **arduino.cc/en/software**
2. Under *Downloads*, click **Windows** then **Win 10 and newer, 64 bits**
3. On the donation page click **Just Download**
4. Run the installer and accept the defaults
5. Open the Arduino IDE. It may take a minute the first time

---

## Part 2 - Teach it about the ESP32

Out of the box the IDE only knows Arduino boards. Yours needs adding.

1. **File** then **Preferences**
2. Find the box labelled **Additional boards manager URLs**
3. Paste this line into it:

   ```
   https://espressif.github.io/arduino-esp32/package_esp32_index.json
   ```

4. Click **OK**
5. **Tools** then **Board** then **Boards Manager**
6. In the search box type `esp32`
7. Find **esp32 by Espressif Systems** and click **Install**

This download is large, around 200 MB, so give it a few minutes. The progress
bar sits at the bottom of the window.

---

## Part 3 - Add the DHT22 library

The board needs a library to talk to the DHT22.

1. **Tools** then **Manage Libraries**
2. Search for `DHT sensor library`
3. Find **DHT sensor library by Adafruit** and click **Install**
4. A box appears asking about dependencies. Click **Install All**

That second library, Adafruit Unified Sensor, is required. Do not skip it.

---

## Part 4 - Choose the board and the port

1. Plug the ESP32 into your laptop with the USB-C cable
2. **Tools** then **Board** then **esp32** then pick **ESP32 Dev Module**
3. **Tools** then **Port** and pick the COM port that appeared

On the port step, look before and after plugging in. The port that appears when
you plug in is yours, usually something like COM3 or COM5.

**If no new port appears**, your board needs a USB driver. Look at the small chip
next to the USB socket:

- Marked **CH340** or **CH9102**: install the CH340 driver from
  `wch-ic.com/downloads/CH341SER_EXE.html`
- Marked **CP2102**: install the CP210x driver from Silicon Labs

Install it, unplug, plug back in, then check the Port menu again.

---

## Part 5 - Load the code

1. Open `stage1_sensor_test.ino` by double-clicking it, or copy its contents into
   a new sketch
2. Click the **arrow button** at the top left to upload
3. Watch the black panel at the bottom. It compiles, then shows dots and dashes
   as it writes to the board, then says **Done uploading**

**If it says "Failed to connect to ESP32"**, hold the **BOOT** button on the board
down, click upload again, and release BOOT once the dots start appearing. Some
boards need this every time.

---

## Part 6 - See the readings

1. Click the **magnifying glass** icon at the top right. That opens the Serial Monitor
2. In the dropdown at its right, set the speed to **115200**
3. Press the **EN** button on the board to restart it

You should see something like this, a new line every two seconds:

```
==============================================
 CROPIFY IoT NODE  -  Stage 1 sensor test
==============================================
 DHT22 on GPIO 4, soil sensor on GPIO 34
 Calibration in use: dry=3000  wet=1200
----------------------------------------------

#1  Temp 24.3 C   Humidity 51.2 %   Soil raw 2874   Soil 8 %
#2  Temp 24.3 C   Humidity 51.4 %   Soil raw 2871   Soil 8 %
#3  Temp 24.4 C   Humidity 51.1 %   Soil raw 2869   Soil 8 %
```

**Screenshot this.** It is your evidence that the hardware works.

If you see gibberish instead of words, the speed is wrong. Set it to 115200.

---

## Part 7 - Calibrate the soil sensor

The percentage means nothing until you do this. Right now the code is using
guessed numbers, and a marker will ask where they came from.

**Step 1, dry.** Hold the sensor in the air, touching nothing. Watch the
`Soil raw` number for a few readings. Write it down. Expect somewhere around
2700 to 3100.

**Step 2, wet.** Fill a glass with water. Stand the sensor in it **up to the
marked line only**. The line is printed on the board. Above the line are the
electronics, and water there will destroy the sensor. Watch `Soil raw` again and
write it down. Expect somewhere around 1100 to 1500.

**Step 3, put your numbers in.** Near the top of the code find these two lines:

```cpp
int SOIL_DRY = 3000;      // reading in dry air
int SOIL_WET = 1200;      // reading in water
```

Replace 3000 and 1200 with your own two numbers. Upload again.

**Step 4, check it.** In dry air the percentage should now read close to 0. In
water it should read close to 100.

Write both raw numbers in your report along with how you measured them. That
one paragraph is the difference between a calibrated sensor and a number you
cannot defend.

---

## What good readings look like

| Reading | Sensible range indoors | Something is wrong if |
|---|---|---|
| Temperature | 18 to 30 C | it reads 0, or jumps wildly |
| Humidity | 30 to 70 % | it reads 0 or 100 constantly |
| Soil raw, dry air | 2700 to 3100 | it reads 0 or 4095 |
| Soil raw, in water | 1100 to 1500 | it does not change when wet |

---

## If something is wrong

| What you see | What it means | What to do |
|---|---|---|
| `DHT22 NO READING` | the data wire or power is not connected | check `out` goes to D4, and `+` and `-` are on 3V3 and GND |
| `DHT22 NO READING` still | wrong sensor type | if your module is a DHT11, change `#define DHT_TYPE DHT22` to `DHT11` |
| Soil raw stuck at 4095 | AOUT not connected | check the yellow wire is on D34 |
| Soil raw stuck at 0 | sensor has no power | check the red wire reaches 3V3 |
| Soil raw does not move in water | you may be on the wrong pin | confirm D34, not D14 |
| Temperature reads but humidity does not | loose data wire | reseat the white wire |
| Nothing at all in the monitor | wrong port or speed | recheck Tools > Port, and set 115200 |
| Gibberish characters | wrong speed only | set the monitor to 115200 |

---

## When this works

Tell me and we move to Stage 2, which adds Wi-Fi and sends these readings to
Firebase. After that your dashboard bars start moving on their own.

Keep for the report:

- the Serial Monitor screenshot showing live readings
- your two calibration numbers, dry and wet
- a photo of the wired breadboard
