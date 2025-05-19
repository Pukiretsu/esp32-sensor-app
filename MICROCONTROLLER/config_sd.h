#ifndef CONFIG_SD_H
#define CONFIG_SD_H

#include <SD.h>
#include <SPI.h>

bool inicializarSD();
void escribirArchivo(const char* path, const char* mensaje);

String cargarConfigWifiSSID();
String cargarConfigWifiPASWORD();
String cargarConfigSensorSESSION();
uint16_t cargarConfigSLEEP();
String cargarConfigENDPOINT_LOG();
String cargarConfigENDPOINT_SENSOR();
String cargarCertsSSL();

void storeBuffer(const char* json);
void reintentarEnvioBuffer();

#endif
