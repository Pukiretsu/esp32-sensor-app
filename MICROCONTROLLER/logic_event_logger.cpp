#include "logic_event_logger.h"
#include "config_sd.h"
#include "config_api.h"
#include "config_wifi.h"
#include "secrets.h"
#include <Arduino.h>

const char* archivoLog = "/log.txt";
static int buzzerPin = -1;

void logEvent(const char* tag, const char* msg) {
  Serial.print(tag);
  Serial.print(" | ");
  Serial.println(msg);

  String log = String(tag) + String(" | ") + String(msg);
  escribirArchivo(archivoLog, log.c_str());
  
  if (checkWifi()) {
    String json = String("{\"tag\": ") + String(tag) + String(", \"evento\": ") + String(msg) + String("}");
    enviarDatosAPI(API_LOG, json);
  }
}

void inicializarBuzzer(int pin) {
  buzzerPin = pin;
  pinMode(buzzerPin, OUTPUT);
  digitalWrite(buzzerPin, LOW);
}

void beep(int duration) {
  if (buzzerPin == -1) return;
  digitalWrite(buzzerPin, HIGH);
  delay(duration);
  digitalWrite(buzzerPin, LOW);
  delay(50);
}

void beepConCodigo(int code) {
  // Por ejemplo: 1 = éxito, 2 = error
  switch (code) {
    case 0: // listo
      beep(50);
      delay(50);
      beep(50);
      delay(50);
      break;
    case 1: // Éxito
      beep(100);
      delay(100);
      beep(100);
      break;
    case 2: // Error
      beep(300);
      delay(200);
      beep(100);
      break;
    case 3: // entrando en sleep
      beep(50);
      delay(50);
      beep(50);
      delay(50);
      beep(50);
      break;
    default:
      beep(100);
      break;
  }
}