#include <WiFi.h>
#include <WebServer.h>
#include <Preferences.h>
#include <WiFiUdp.h>
#include <BLEDevice.h>
#include <BLEScan.h>

//KONFIGURACJA
const int BUTTON_PIN = 4;     // Przycisk między PIN 4 a GND
const int UDP_PORT = 5005;
WebServer server(80);
Preferences preferences;
WiFiUDP udp;
BLEScan* pBLEScan;

// Zmienne globalne
String savedSSID, savedPass, savedUDPIP;
bool isConfigMode = false;

// OBSŁUGA STRONY WWW (TRYB AP)
void handleRoot() {
  server.send(200, "text/html", html);
}

void handleConfig() {
  if (server.hasArg("ssid") && server.hasArg("pass") && server.hasArg("ip")) {
    preferences.begin("wifi", false);
    preferences.putString("ssid", server.arg("ssid"));
    preferences.putString("pass", server.arg("pass"));
    preferences.putString("udp_ip", server.arg("ip"));
    preferences.end();

    server.send(200, "application/json", "{\"status\":\"ok\"}");
    Serial.println("Zapisano nowe dane. Restart...");
    delay(2000);
    ESP.restart();
  }
}

//tryb AP
void startAP() {
  isConfigMode = true;
  WiFi.mode(WIFI_AP);
  WiFi.softAP("ESP_AP", "123454321");
  Serial.println("Tryb AP Aktywny. Polacz sie z 'ESP_AP'");
  Serial.print("IP serwera: ");
  Serial.println(WiFi.softAPIP());
  
  server.on("/", handleRoot);
  server.on("/set_wifi", HTTP_POST, handleConfig);
  server.begin();
}

//SETUP
void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  preferences.begin("wifi", true);
  savedSSID = preferences.getString("ssid", "");
  savedPass = preferences.getString("pass", "");
  savedUDPIP = preferences.getString("udp_ip", "192.168.1.100");
  preferences.end();

  //Przełącznie na AP jeżeli brak danych lub przycisk resetu
  if (savedSSID == "" || digitalRead(BUTTON_PIN) == LOW) {
    startAP();
  } 
  else {
    // próba połączenia z wifi
    WiFi.mode(WIFI_STA);
    WiFi.begin(savedSSID.c_str(), savedPass.c_str());
    Serial.println("Laczenie z: " + savedSSID);

    int attempts = 0;
    // próba połączenia (40)
    while (WiFi.status() != WL_CONNECTED && attempts < 40) {
      delay(500);
      Serial.print(".");
      attempts++;

      // REAKCJA NA GUZIK PODCZAS KROPEK
      if (digitalRead(BUTTON_PIN) == LOW) {
        Serial.println("\n[RESET] Przerwano przyciskiem!");
        preferences.begin("wifi", false);
        preferences.remove("ssid"); // Czyścimy SSID, by wejść w AP
        preferences.end();
        ESP.restart();
      }
    }

    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("\n[ERROR] Timeout WiFi! Powrot do AP...");
      startAP();
    } else {
      Serial.println("\n Polaczono! IP: " + WiFi.localIP().toString());
      udp.begin(UDP_PORT);
      BLEDevice::init("");
      pBLEScan = BLEDevice::getScan();
      pBLEScan->setActiveScan(true);
      isConfigMode = false;
    }
  }
}

void loop() {
  if (isConfigMode) {
    server.handleClient();
  } 
  else {
    // RESET W TRAKCIE PRACY (Trzymanie 2 sekundy)
    if (digitalRead(BUTTON_PIN) == LOW) {
      delay(2000);
      if (digitalRead(BUTTON_PIN) == LOW) {
        Serial.println("Wymuszanie resetu do AP...");
        preferences.begin("wifi", false);
        preferences.remove("ssid");
        preferences.end();
        ESP.restart();
      }
    }

    // SKANOWANIE I WYSYŁKA
    if (WiFi.status() == WL_CONNECTED) {
      BLEScanResults foundDevices = pBLEScan->start(1, false); 
      String json = "{";
      bool first = true;

      for (int i = 0; i < foundDevices.getCount(); i++) {
        BLEAdvertisedDevice device = foundDevices.getDevice(i);
        String name = device.getName().c_str();
        
        if (name == "BEACON_1" || name == "BEACON_2" || name == "BEACON_3") {
          if (!first) json += ",";
          json += "\"" + name + "\":" + String(device.getRSSI());
          first = false;
        }
      }
      json += "}";

      if (!first) {
        udp.beginPacket("255.255.255.255", 5005); //broadcast - w celu uniknięcia sztywnego wpisywania IP (do ewentualnej zmiany)
        udp.print(json);
        udp.endPacket();
        Serial.println("UDP -> " + savedUDPIP + ": " + json);
      }
      pBLEScan->clearResults(); 
    } else {
      Serial.println("WiFi zgubione!");
      delay(1000);
    }
  }
}