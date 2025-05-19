#ifndef CONFIG_API_H
#define CONFIG_API_H

#include <WiFiClientSecure.h>
#include <HTTPClient.h>
#include <Arduino.h>

bool enviarDatosAPI(const char* serverName, const String& payload);

#endif
