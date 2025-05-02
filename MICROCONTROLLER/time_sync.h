#ifndef TIME_SYNC_H
#define TIME_SYNC_H
#include <Arduino.h>

void sincronizarHoraNTP(const char* zonaHoraria = "CET-1CEST,M3.5.0,M10.5.0/3");
String obtenerFechaHora();

#endif
