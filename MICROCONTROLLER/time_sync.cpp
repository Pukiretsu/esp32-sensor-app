#include "time_sync.h"
#include <time.h>
#include <WiFi.h>
#include <Arduino.h>

void sincronizarHoraNTP(const char* zonaHoraria) {
  configTzTime(zonaHoraria, "pool.ntp.org", "time.nist.gov");

  Serial.print("Sincronizando hora NTP");
  struct tm tiempo;
  while (true) {
    if (getLocalTime(&tiempo)) break;
    Serial.print(".");
    delay(500);
  }
  Serial.println("\nHora sincronizada correctamente.");
}

String obtenerFechaHora() {
  struct tm tiempo;
  if (!getLocalTime(&tiempo)) return "Error obteniendo hora";

  char buffer[25];
  strftime(buffer, sizeof(buffer), "%Y-%m-%d %H:%M:%S", &tiempo);
  return String(buffer);
}
