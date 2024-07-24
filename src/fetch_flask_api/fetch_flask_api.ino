#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>

// Set up network credentials
const char* ssid = "SSID";
const char* password = "PW";

// Flask API URL
const char* api_url = "http://Raspberry_pi_ip:5000/weather_warnings_db";

// Create an instance of the TFT_eSPI class
TFT_eSPI tft = TFT_eSPI();

void setup() {
  Serial.begin(115200);

  // Initialize TFT display
  tft.init();
  tft.setRotation(1);  // adjust rotation
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

      const char* typename = doc["typename"];
      const char* status = doc["status"];
      const char* color = doc["color"];

      // Display warning
      tft.fillScreen(TFT_BLACK);
      tft.setCursor(0, 0);
      tft.println("Current Warning:");
      tft.println(typename);
      tft.println("Severity Level:")
      tft.println(color);
      tft.println("Warning Status:");
      tft.println(status);
    } else {
      Serial.print("Error on HTTP request: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi not connected.");
  }

  // Fetch data every 90 seconds
  delay(90000);
}
