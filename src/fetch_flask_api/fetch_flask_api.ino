#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>

// Set up network credentials
const char* ssid = "YuLab_911";
const char* password = "911911911";

// Flask API URL
const char* api_url = "http://192.168.1.110:5000/current_warnings";

// Create an instance of the TFT_eSPI class
TFT_eSPI tft = TFT_eSPI();

// Interval between data fetches in seconds
const int fetchInterval = 120;

void setup() {
  Serial.begin(115200);

  // Initialize TFT display
  tft.init();
  tft.setRotation(3);  // adjust rotation
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi ...");
  }
  Serial.println("Connected to WiFi.");

  //Display initial message
  tft.setCursor(0, 0);
  tft.println("Fetching weather data ...");
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(api_url);
    int httpResponseCode = http.GET();

    if (httpResponseCode > 0) {
      String payload = http.getString();
      Serial.println(payload);

      // Parse JSON
      DynamicJsonDocument doc(1024);
      deserializeJson(doc, payload);

      const char* typeName = doc["typename"];
      const char* mark = doc["mark"];
      const char* color = doc["color"];

      // Display warning
      tft.fillScreen(TFT_BLACK);
      tft.setCursor(0, 0);
      tft.println("Current Warning:");
      tft.println(typeName);
      tft.println("Severity Level:");
      tft.println(color);
      tft.println("Warning Status:");
      tft.println(mark);
    } else {
      Serial.print("Error on HTTP request: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi not connected.");
  }

  // Countdown display
  for (int i = fetchInterval; i > 0; i--) {
    tft.fillRect(0, 200, 240, 40, TFT_BLACK);  // clear the countdown area
    tft.setCursor(0, 200);
    tft.setTextColor(TFT_WHITE);
    tft.setTextSize(2);
    tft.printf("Update in %d seconds..", i);
    delay(1000);
  }
}
