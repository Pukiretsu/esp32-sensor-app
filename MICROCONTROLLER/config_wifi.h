#ifndef CONFIG_WIFI_H
#define CONFIG_WIFI_H

#include <WiFi.h>

void configurarWiFi(const char* ssid, const char* password);
bool reconectarWiFi();
void apagarWiFi();    
void encenderWiFi();  
bool checkWifi();

#endif