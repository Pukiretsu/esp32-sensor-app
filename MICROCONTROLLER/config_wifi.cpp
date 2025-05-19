#include "HardwareSerial.h"
#include "config_wifi.h"
#include "logic_event_logger.h"

const char* WIFI_TAG = "WIFI"; 

void configurarWiFi_WPA2(const char* ssid, const char* password) {
  WiFi.mode(WIFI_STA); 
  WiFi.begin(ssid, password);

  unsigned long startAttemptTime = millis();
  unsigned long timeout = 10000; // 10 segundos

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < timeout) {
    Serial.println(".");
    delay(500);
  }

  if (WiFi.status() == WL_CONNECTED) {
    logEvent(WIFI_TAG, "Conectado al WiFi!");
  } else {
    logEvent(WIFI_TAG, "Error: no se pudo conectar al WiFi.");
  }
}

void configurarWiFi_OPEN(const char* ssid) {
  WiFi.mode(WIFI_STA); 
  WiFi.begin(ssid);

  unsigned long startAttemptTime = millis();
  unsigned long timeout = 10000; // 10 segundos

  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < timeout) {
    Serial.println(".");
    delay(500);
  }

  if (WiFi.status() == WL_CONNECTED) {
    logEvent(WIFI_TAG, "Conectado al WiFi!");
  } else {
    logEvent(WIFI_TAG, "Error: no se pudo conectar al WiFi.");
  }
}

bool reconectarWiFi() {
  if (WiFi.status() != WL_CONNECTED) {
    logEvent(WIFI_TAG, "Desconectado. Intentando reconectar...");
    WiFi.reconnect();
    return true;
  }
  return false;
}

void apagarWiFi() {
  logEvent(WIFI_TAG, "Apagando WiFi...");
  WiFi.disconnect(true);
  WiFi.mode(WIFI_OFF);
}

void encenderWiFi() {
  WiFi.mode(WIFI_STA);  // Modo cliente
  logEvent(WIFI_TAG, "Encendiendo WiFi...");
}

bool checkWifi() {
  return (WiFi.status() == WL_CONNECTED);
}