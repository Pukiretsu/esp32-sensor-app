#ifndef LOGIC_EVENT_LOGGER_H
#define LOGIC_EVENT_LOGGER_H

#include <Arduino.h>

void logEvent(const char* tag, const char* msg);
void inicializarBuzzer(int pin);
void beep(int duration = 100);
void beepConCodigo(int code);

#endif