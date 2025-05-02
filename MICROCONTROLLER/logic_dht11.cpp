#include "logic_dht11.h"

#define DHTTYPE DHT11

DHT dht(0, DHTTYPE);  // pin 0 como valor inicial, se cambiará en iniciarDHT()

void iniciarDHT(uint8_t pin) {
  dht.~DHT();               // destruir objeto anterior
  new (&dht) DHT(pin, DHTTYPE);  // reconstruir objeto con nuevo pin
  dht.begin();
}

float leerTemperatura() {
  return dht.readTemperature();
}

float leerHumedad() {
  return dht.readHumidity();
}