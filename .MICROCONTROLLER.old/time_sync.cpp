#include "time_sync.h"
#include <time.h>
#include <WiFi.h>
#include <Arduino.h>
#include "logic_event_logger.h"

void sincronizarHoraNTP(const char* zonaHoraria) {
  configTzTime(zonaHoraria, "pool.ntp.org", "time.nist.gov");
  logEvent("NTP","Sincronizando hora NTP");
  struct tm tiempo;
  while (true) {
    if (getLocalTime(&tiempo)) break;
    Serial.print(".");
    delay(500);
  }
  
}

String obtenerFechaHora() {
  struct tm tiempo;
  if (!getLocalTime(&tiempo)) return "Error obteniendo hora";

  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &tiempo);
  return String(buffer);
}
