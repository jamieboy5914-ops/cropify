/*
  ============================================================
  SOIL SENSOR DIAGNOSTIC  -  finds the problem for you
  ============================================================

  Upload this instead of the Stage 1 sketch. It reads EVERY analogue
  input pin the ESP32 has available with Wi-Fi, then tells you which
  one your yellow wire is actually on.

  Leave all wiring exactly as it is. Change nothing.

  Open the Serial Monitor at 115200 and read the verdict.
  ============================================================
*/

// Every ADC1 pin. These are the only analogue pins that keep working
// once Wi-Fi is switched on.
const int PINS[]  = {32, 33, 34, 35, 36, 39};
const int N_PINS  = 6;

int readAvg(int pin) {
  long total = 0;
  for (int i = 0; i < 16; i++) {
    total += analogRead(pin);
    delay(3);
  }
  return total / 16;
}

void setup() {
  Serial.begin(115200);
  delay(1200);
  analogReadResolution(12);            // 0 to 4095

  Serial.println();
  Serial.println("=================================================");
  Serial.println("  SOIL SENSOR DIAGNOSTIC");
  Serial.println("=================================================");
  Serial.println("  Reading every analogue pin.");
  Serial.println("  Hold the soil sensor in DRY AIR while this runs.");
  Serial.println("=================================================");
  Serial.println();
}

void loop() {
  int best = -1;
  int bestVal = 0;

  Serial.println("---- pin readings ----");
  for (int i = 0; i < N_PINS; i++) {
    int v = readAvg(PINS[i]);

    Serial.print("  GPIO ");
    if (PINS[i] < 10) Serial.print(" ");
    Serial.print(PINS[i]);
    Serial.print("  =  ");
    if (v < 1000) Serial.print(" ");
    Serial.print(v);

    // a floating, unconnected pin sits near zero and twitches
    if (v < 100) {
      Serial.println("    (nothing connected)");
    } else if (v > 4000) {
      Serial.println("    <-- sitting at full 3.3V");
    } else {
      Serial.println("    <-- SIGNAL HERE");
    }

    if (v > bestVal) {
      bestVal = v;
      best = PINS[i];
    }
  }

  Serial.println();
  Serial.println("---- verdict ----");

  if (bestVal < 100) {
    Serial.println("  No signal on ANY analogue pin.");
    Serial.println("  The sensor is not powered, or the yellow wire is loose.");
    Serial.println("  Check: red wire on the 3V3 rail, black wire on the GND rail,");
    Serial.println("  and the white plug pushed fully into the sensor board.");
  }
  else if (bestVal > 4000) {
    Serial.print("  GPIO ");
    Serial.print(best);
    Serial.println(" is at full voltage.");
    Serial.println("  That is the yellow wire touching 3V3, not the sensor output.");
  }
  else {
    Serial.print("  Your soil signal is on GPIO ");
    Serial.println(best);
    Serial.print("  Dry-air reading: ");
    Serial.println(bestVal);
    if (best != 34) {
      Serial.println();
      Serial.print("  NOTE: the Stage 1 sketch expects GPIO 34, but the wire is on ");
      Serial.println(best);
      Serial.print("  Either move the yellow wire to D34, or change SOIL_PIN to ");
      Serial.println(best);
    } else {
      Serial.println("  This matches the Stage 1 sketch. Good.");
    }
    Serial.println();
    Serial.println("  Now dip the sensor in water to the line. The number should DROP.");
  }

  Serial.println();
  Serial.println("=================================================");
  Serial.println();
  delay(3000);
}
