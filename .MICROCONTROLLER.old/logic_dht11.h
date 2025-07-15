#ifndef DHT11_LOGIC_H
#define DHT11_LOGIC_H

#include <DHT.h>

void iniciarDHT(uint8_t pin);
float leerTemperatura();
float leerHumedad();

#endif