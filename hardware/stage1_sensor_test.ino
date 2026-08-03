/*
  ============================================================
  CROPIFY IoT NODE  -  STAGE 1: sensor test
  ============================================================

  What this does
    Reads the DHT11 and the capacitive soil moisture probe, then prints both
    to the Serial Monitor once every two seconds.

  What this does NOT do
    No Wi-Fi. No Firebase. Nothing leaves the board. That is Stage 2.
    This stage exists to prove the wiring and the sensors before anything
    else is built on top of them.

  Wiring as built
    DHT11  +    -> ESP32 3V3
    DHT11  out  -> ESP32 D4     (GPIO 4)
    DHT11  -    -> ESP32 GND
    Soil   VCC  -> ESP32 3V3
    Soil   AOUT -> ESP32 D32    (GPIO 32)
    Soil   GND  -> ESP32 GND

  Why GPIO 32 for the probe
    GPIO 32 sits on the first analogue converter, ADC1. The second converter,
    ADC2, stops working the moment Wi-Fi switches on, which would silently kill
    the soil readings in Stage 2. Pins 32 to 39 are all safe.

  DHT11 specification, for the report
    Temperature range     0 to 50 C,  accuracy plus or minus 2 C
    Humidity range        20 to 90 %, accuracy plus or minus 5 %
    Minimum read interval 1 second

  Arduino IDE settings
    Board                ESP32 Dev Module
    Serial Monitor baud  115200

  Libraries needed
    DHT sensor library       by Adafruit
    Adafruit Unified Sensor  by Adafruit  (installs alongside the above)
  ============================================================
*/

#include "DHT.h"

// ------------------------------------------------------------ pins
#define DHT_PIN    4        // DHT11 data line
#define DHT_TYPE   DHT11    // this build uses a DHT11
#define SOIL_PIN   32       // soil AOUT, on ADC1 so Wi-Fi does not disturb it

// ------------------------------------------------------------ soil calibration
// Measured on this board with this probe.
//   Method: hold the probe in dry air and record the raw value, then stand it
//   in water up to the printed line and record the raw value again.
//
// A capacitive probe reads HIGHER when dry and LOWER when wet, so the dry
// figure is the larger of the two. Put both numbers in the report beside a
// sentence describing how they were taken.
//
// On the dry figure: 4095 is the largest value the converter can return, so the
// probe saturates the input in open air. Dry soil reads below that, which keeps
// the working range wide, but a value of exactly 4095 means "at least as dry as
// air" rather than a precise measurement.
int SOIL_DRY = 4095;      // probe in dry air
int SOIL_WET = 1648;      // probe in water, to the printed line

// ------------------------------------------------------------ state
DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastRead = 0;
const unsigned long INTERVAL = 2000;   // 2 s is comfortably above the DHT11 minimum
int readingCount = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);                         // let the Serial Monitor attach

  Serial.println();
  Serial.println("==============================================");
  Serial.println(" CROPIFY IoT NODE  -  Stage 1 sensor test");
  Serial.println("==============================================");
  Serial.print(" DHT11 on GPIO ");
  Serial.print(DHT_PIN);
  Serial.print(", soil probe on GPIO ");
  Serial.println(SOIL_PIN);
  Serial.print(" Soil calibration: dry=");
  Serial.print(SOIL_DRY);
  Serial.print("  wet=");
  Serial.println(SOIL_WET);
  Serial.println("----------------------------------------------");
  Serial.println();

  dht.begin();
  analogReadResolution(12);            // ESP32 returns 0 to 4095
}

// ------------------------------------------------------------ soil reading
int readSoilRaw() {
  // A single analogue sample jumps around, so average a batch.
  long total = 0;
  const int samples = 20;
  for (int i = 0; i < samples; i++) {
    total += analogRead(SOIL_PIN);
    delay(5);
  }
  return total / samples;
}

// ------------------------------------------------------------ loop
void loop() {
  if (millis() - lastRead < INTERVAL) return;
  lastRead = millis();
  readingCount++;

  // ---- DHT11 ----
  float temperature = dht.readTemperature();   // degrees C
  float humidity    = dht.readHumidity();      // percent

  // ---- soil ----
  int soilRaw = readSoilRaw();
  int soilPercent = map(soilRaw, SOIL_DRY, SOIL_WET, 0, 100);
  soilPercent = constrain(soilPercent, 0, 100);

  // ---- one tidy line per reading ----
  Serial.print("#");
  Serial.print(readingCount);
  Serial.print("  ");

  if (isnan(temperature) || isnan(humidity)) {
    Serial.print("DHT11 NO READING            ");
  } else {
    Serial.print("Temp ");
    Serial.print(temperature, 1);
    Serial.print(" C   Humidity ");
    Serial.print(humidity, 1);
    Serial.print(" %   ");

    // A DHT11 cannot physically report outside these bounds. Values beyond
    // them mean the wrong sensor type is selected, so flag it rather than
    // record a figure that cannot be defended later.
    if (temperature < -5 || temperature > 60 || humidity < 5 || humidity > 100) {
      Serial.print("[OUT OF DHT11 RANGE, check DHT_TYPE]  ");
    }
  }

  Serial.print("Soil raw ");
  Serial.print(soilRaw);
  Serial.print("   Soil ");
  Serial.print(soilPercent);
  Serial.println(" %");

  // Printed once, as a reminder while calibrating.
  if (readingCount == 3) {
    Serial.println();
    Serial.println(">> Soil raw should be high in dry air and drop in water.");
    Serial.println(">> Temperature and humidity should match the room.");
    Serial.println(">> If either looks wrong, stop and check the wiring first.");
    Serial.println();
  }
}
