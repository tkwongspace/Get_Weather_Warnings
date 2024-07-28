#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <TFT_eSPI.h>

// Set up network credentials
const char* ssid = "YuLab_911";
const char* password = "911911911";

// Flask API URL
const char* api_url = "http://172.20.108.112:171/current_warning";

// Create an instance of the TFT_eSPI class
TFT_eSPI tft = TFT_eSPI();

// To store the previous warnings downloaded from API
DynamicJsonDocument prevWarnings(2048);

// Define the pin for the buzzer
const int buzzerPin = 26;

// Function to manage the buzzer
void beep() {
  digitalWrite(buzzerPin, LOW);  // turn the buzzer on
  delay(500);                    // beep duration
  digitalWrite(buzzerPin, HIGH); // turn the buzzer off
}

// Function to compare warnings (to determine whether to beep)
bool compareWarnings(const JsonArray& newWarnings, const JsonArray& oldWarnings) {
  if (newWarnings.size() != oldWarnings.size()) {
    return false;
  }

  for (size_t i = 0; i < newWarnings.size(); ++i) {
    if (strcmp(newWarnings[i]["typename"], oldWarnings[i]["typename"]) != 0 ||
        strcmp(newWarnings[i]["mark"], oldWarnings[i]["mark"]) != 0 ||
        strcmp(newWarnings[i]["color"], oldWarnings[i]["color"]) != 0) {
      return false;
    }
  }

  return true;
}

// Function to scroll text
void scrollText(const char* text, int y) {
  int16_t x = tft.width();
  while (x > -tft.textWidth(text)) {
    tft.fillRect(80, y, tft.width() - 80, tft.fontHeight(), TFT_BLACK);
    tft.setCursor(x, y);
    tft.print(text);
    x -= 2;
    delay(30);  // scrolling speed
  }
}

// Function for warnings display
void displayWarnings(const JsonArray& warnings) {
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(0, 0);
  tft.println("Current Warnings:");

  for (JsonObject warning : warnings) {
    const char* typeName = warning["typename"];
    const char* mark = warning["mark"];
    const char* color = warning["color"];

    // display labels
    tft.setCursor(0, 40);
    tft.print("Type: ");
    tft.setCursor(0, 80);
    tft.print("Severity: ");
    tft.setCursor(0, 120);
    tft.print("Status: ");

    // display warning information
    scrollText(typeName, 40);
    scrollText(color, 80);
    scrollText(mark, 120);
  }
}

// Initial the display
void setup() {
  Serial.begin(115200);

  // Initialize TFT display
  tft.init();
  tft.setRotation(3);  // adjust rotation
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);

  // Initialize the buzzer pin
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, HIGH);  // turn off the buzzer initially

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
  static unsigned long lastFetchTime = 0;
  unsigned long currentTime = millis();

  if (currentTime - lastFetchTime >= 120000) {  //fetch data every 120 seconds
    lastFetchTime = currentTime;

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(api_url);
      int httpResponseCode = http.GET();

      if (httpResponseCode > 0) {
        String payload = http.getString();
        Serial.println(payload);

        // Parse JSON
        DynamicJsonDocument doc(2048);  // increase buffer size if neccesary
        deserializeJson(doc, payload);

        JsonArray newWarnings = doc.as<JsonArray>();

        // Compare with previous warnings
        if (!compareWarnings(newWarnings, prevWarnings.as<JsonArray>())) {
          beep(); // beep if there is a new or updated warning
        }

        // Update warnings on board
        prevWarnings = doc;

        // Display warnings
        displayWarnings(newWarnings);    
      } else {
        Serial.print("Error on HTTP request: ");
        Serial.println(httpResponseCode);
        tft.fillScreen(TFT_BLACK);
        tft.setCursor(0, 0);
        tft.println("Failed to fetch data.");
      }
      http.end();
    } else {
      Serial.println("WiFi not connected.");
      tft.fillScreen(TFT_BLACK);
      tft.setCursor(0, 0);
      tft.println("WiFi not connected.");
    }
  }  

  // Countdown display
  int secondsLeft = 120 - ((currentTime - lastFetchTime) / 1000);
  tft.setCursor(0, tft.height() - tft.fontHeight());
  tft.fillRect(0, tft.height() - tft.fontHeight(), tft.width(), tft.fontHeight(), TFT_BLACK);  // clear the countdown area
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(2);
  tft.printf("Update in %d seconds..", secondsLeft);
  delay(1000);
}
