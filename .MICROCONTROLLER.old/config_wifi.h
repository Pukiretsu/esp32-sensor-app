#ifndef CONFIG_WIFI_H
#define CONFIG_WIFI_H

#include <WiFi.h>

void configurarWiFi_WPA2(const char* ssid, const char* password);
void configurarWiFi_OPEN(const char* ssid);
bool reconectarWiFi();
void apagarWiFi();    
void encenderWiFi();  
bool checkWifi();

#endif