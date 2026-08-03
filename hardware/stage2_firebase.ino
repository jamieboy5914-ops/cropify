/*
  ============================================================
  CROPIFY IoT NODE  -  STAGE 2: send readings to Firebase
  ============================================================

  What this adds to Stage 1
    Connects to Wi-Fi, then uploads temperature, humidity and soil moisture
    to a Firebase Realtime Database every 15 seconds. Readings still print
    to the Serial Monitor so you can watch what is happening.

  How it talks to Firebase
    Through Firebase's REST interface using a plain HTTPS request. No extra
    library is needed beyond the DHT one you already have. Fewer moving parts
    than the large Firebase libraries, and easier to debug, because you can
    paste the same URL into a browser and see the data.

  Wiring, unchanged from Stage 1
    DHT11  +    -> ESP32 3V3
    DHT11  out  -> ESP32 D14    (GPIO 14)
    DHT11  -    -> ESP32 GND
    Soil   VCC  -> ESP32 3V3
    Soil   AOUT -> ESP32 D32    (GPIO 32)
    Soil   GND  -> ESP32 GND

  Arduino IDE settings
    Board                ESP32 Dev Module
    Serial Monitor baud  115200
  ============================================================
*/

#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include "DHT.h"

// ============================================================
//  EDIT THESE THREE LINES, THEN UPLOAD
// ============================================================

// Your Wi-Fi. The ESP32 only joins 2.4 GHz networks, not 5 GHz.
// Replace both of these with placeholders before pushing this file to a
// public repository. A committed password stays in the git history forever.
const char *WIFI_SSID = "PUT_YOUR_WIFI_NAME_HERE";
const char *WIFI_PASS = "PUT_YOUR_WIFI_PASSWORD_HERE";

// Your database host, taken from the Firebase console without https:// and
// without a trailing slash. This is filled in from project id cropify-9980a.
//
// This database sits in the Singapore region, so the host carries
// asia-southeast1 in it rather than the plain firebaseio.com form.
//
// CHECK IT FIRST. Paste the line below into a browser:
//    https://cropify-9980a-default-rtdb.asia-southeast1.firebasedatabase.app/sensors.json
// A reply of  null  means the host is right and the rules allow access.
// An error page means the host is wrong, so open the Realtime Database page in
// the console and copy the exact URL shown at the top of the data view.
const char *FIREBASE_HOST = "cropify-9980a-default-rtdb.asia-southeast1.firebasedatabase.app";

// ============================================================

// Where the readings are stored inside the database.
const char *FIREBASE_PATH = "/sensors.json";

// ------------------------------------------------------------ pins
#define DHT_PIN    14
#define DHT_TYPE   DHT11
#define SOIL_PIN   32

// ------------------------------------------------------------ soil calibration
// Measured on this board with this probe: held in dry air, then stood in water
// up to the printed line. A capacitive probe reads higher when dry.
int SOIL_DRY = 4095;
int SOIL_WET = 1648;

// ------------------------------------------------------------ timing
const unsigned long READ_EVERY   = 2000;    // print locally every 2 s
const unsigned long UPLOAD_EVERY = 15000;   // send to Firebase every 15 s

DHT dht(DHT_PIN, DHT_TYPE);
unsigned long lastRead = 0;
unsigned long lastUpload = 0;
int readingCount = 0;
int uploadCount = 0;
int uploadFails = 0;

// latest values, shared between the read step and the upload step
float lastTemp = 0;
float lastHum = 0;
int lastSoilPct = 0;
int lastSoilRaw = 0;
bool haveReading = false;


// ------------------------------------------------------------ Wi-Fi
void connectWiFi() {
  Serial.print("Connecting to Wi-Fi \"");
  Serial.print(WIFI_SSID);
  Serial.print("\" ");

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  int tries = 0;
  while (WiFi.status() != WL_CONNECTED && tries < 40) {   // wait up to 20 s
    delay(500);
    Serial.print(".");
    tries++;
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("Connected. This board's address is ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("Wi-Fi FAILED. Check three things:");
    Serial.println("  1. the network name and password above, spelling and case");
    Serial.println("  2. the network is 2.4 GHz, because the ESP32 cannot join 5 GHz");
    Serial.println("  3. you are in range");
  }
}


// ------------------------------------------------------------ soil
int readSoilRaw() {
  long total = 0;
  const int samples = 20;
  for (int i = 0; i < samples; i++) {
    total += analogRead(SOIL_PIN);
    delay(5);
  }
  return total / samples;
}


// ------------------------------------------------------------ upload
bool uploadToFirebase(float t, float h, int soilPct, int soilRaw) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("   upload skipped, Wi-Fi is down");
    return false;
  }

  // Build the JSON by hand. Small and clear, no library needed.
  String json = "{";
  json += "\"temperature\":" + String(t, 1) + ",";
  json += "\"humidity\":"    + String(h, 1) + ",";
  json += "\"soil_moisture\":" + String(soilPct) + ",";
  json += "\"soil_raw\":"    + String(soilRaw) + ",";
  json += "\"uptime_s\":"    + String(millis() / 1000);
  json += "}";

  String url = "https://" + String(FIREBASE_HOST) + String(FIREBASE_PATH);

  WiFiClientSecure client;
  client.setInsecure();          // skip certificate checking, fine for this project

  HTTPClient http;
  if (!http.begin(client, url)) {
    Serial.println("   upload failed, could not start the request");
    return false;
  }
  http.addHeader("Content-Type", "application/json");

  // PUT replaces whatever is at that path, so the database always holds the
  // most recent reading rather than a growing pile of old ones.
  int code = http.PUT(json);
  String reply = http.getString();
  http.end();

  if (code == 200) {
    Serial.println("   uploaded to Firebase");
    return true;
  }

  Serial.print("   upload failed, HTTP code ");
  Serial.println(code);
  if (code == 401 || code == 403) {
    Serial.println("   permission denied. Set the database rules to test mode.");
  } else if (code == 404) {
    Serial.println("   not found. Check FIREBASE_HOST is exactly right.");
  } else if (code < 0) {
    Serial.println("   could not reach the server. Check the host and your Wi-Fi.");
  }
  if (reply.length() > 0 && reply.length() < 200) {
    Serial.print("   server said: ");
    Serial.println(reply);
  }
  return false;
}


// ------------------------------------------------------------ setup
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println("==============================================");
  Serial.println(" CROPIFY IoT NODE  -  Stage 2, Firebase upload");
  Serial.println("==============================================");
  Serial.print(" DHT11 on GPIO ");
  Serial.print(DHT_PIN);
  Serial.print(", soil probe on GPIO ");
  Serial.println(SOIL_PIN);
  Serial.print(" Soil calibration: dry=");
  Serial.print(SOIL_DRY);
  Serial.print("  wet=");
  Serial.println(SOIL_WET);
  Serial.print(" Database host: ");
  Serial.println(FIREBASE_HOST);
  Serial.println("----------------------------------------------");

  dht.begin();
  delay(2000);                     // let the DHT11 settle
  analogReadResolution(12);

  connectWiFi();
  Serial.println();
}


// ------------------------------------------------------------ loop
void loop() {
  // --- rejoin Wi-Fi if it drops ---
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastRetry = 0;
    if (millis() - lastRetry > 20000) {
      lastRetry = millis();
      Serial.println("Wi-Fi dropped, reconnecting");
      connectWiFi();
    }
  }

  // --- read the sensors and print ---
  if (millis() - lastRead >= READ_EVERY) {
    lastRead = millis();
    readingCount++;

    float t = dht.readTemperature();
    float h = dht.readHumidity();
    int raw = readSoilRaw();
    int pct = constrain((int)map(raw, SOIL_DRY, SOIL_WET, 0, 100), 0, 100);

    Serial.print("#");
    Serial.print(readingCount);
    Serial.print("  ");

    if (isnan(t) || isnan(h)) {
      Serial.print("DHT11 NO READING            ");
    } else {
      Serial.print("Temp ");
      Serial.print(t, 1);
      Serial.print(" C   Humidity ");
      Serial.print(h, 1);
      Serial.print(" %   ");
      lastTemp = t;
      lastHum = h;
      haveReading = true;
    }

    lastSoilRaw = raw;
    lastSoilPct = pct;

    Serial.print("Soil raw ");
    Serial.print(raw);
    Serial.print("   Soil ");
    Serial.print(pct);
    Serial.println(" %");
  }

  // --- upload every 15 s ---
  if (millis() - lastUpload >= UPLOAD_EVERY) {
    lastUpload = millis();

    if (!haveReading) {
      Serial.println("   nothing to upload yet, waiting for a valid DHT reading");
    } else {
      uploadCount++;
      Serial.print("   upload #");
      Serial.print(uploadCount);
      Serial.print("  ");
      if (!uploadToFirebase(lastTemp, lastHum, lastSoilPct, lastSoilRaw)) {
        uploadFails++;
      }
      Serial.print("   (");
      Serial.print(uploadCount - uploadFails);
      Serial.print(" succeeded, ");
      Serial.print(uploadFails);
      Serial.println(" failed)");
    }
  }
}
