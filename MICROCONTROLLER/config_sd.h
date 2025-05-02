#ifndef CONFIG_SD_H
#define CONFIG_SD_H

#include <SD.h>
#include <SPI.h>

bool inicializarSD();
void escribirArchivo(const char* path, const char* mensaje);

#endif
