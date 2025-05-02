#include "config_wifi.h"
#include "config_sd.h"
#include "config_api.h"
#include "logic_dht11.h"
#include "logic_event_logger.h"
#include "time_sync.h"
#include "esp_sleep.h"
#include "secrets.h"

const char* archivoSensor = "/dht11.csv";
const int BUZZER_PIN = 15;
const uint8_t pinDHT_1 = 27;
const uint8_t pinDHT_2 = 26;
const uint8_t pinDHT_3 = 25;
const uint8_t dht_pins[3] = {pinDHT_1, pinDHT_2, pinDHT_3};

// Tiempo en microsegundos para dormir
#define TIEMPO_DORMIR_US 50e6

void setup() {
  encenderWiFi();
  Serial.begin(115200);
  delay(1000); // pequeño delay para estabilizar todo
  inicializarBuzzer(BUZZER_PIN);
  Serial.println("ESP-32 | Encendido, Configurandose ahora.");
  if (!inicializarSD()) {
      Serial.println("SD | Error con la SD, deteniendo ejecución");
      beepConCodigo(2);
      return;
  }
  
  configurarWiFi(SSID, PASSWORD);
  sincronizarHoraNTP("UTC-5");
  logEvent("ESP-32", "Configurado y listo");
  beepConCodigo(0);

  String msg;
  String tag;
  
  msg = "Fecha y hora actual: " + obtenerFechaHora();
  logEvent("NTP", msg.c_str());

  
  
  for (int i = 0; i < 2; i++){
    iniciarDHT(dht_pins[i]);
    float temp = leerTemperatura();
    float hum = leerHumedad();

    if (!isnan(temp) && !isnan(hum)) {
      delay(2000); // pequeño delay para estabilizar todo
      msg = "Temp: " + String(temp) + " °C, Hum: " + String(hum) + "%";
      tag = String("DHT11-") + String(i+1);
      logEvent(tag.c_str(), msg.c_str());

      String datos =  ,String(i+1) + " , " + String(temp) + " , " + String(hum);
      escribirArchivo(archivoSensor, datos.c_str());

      String json = String("{\"tipo\": ") + String(i+1) + String(", \"temperatura\": ") + String(temp) + String(", \"humedad\": ") + String(hum) + String("}");
      Serial.println(json);
      enviarDatosAPI(API_SENSOR, json);
      beepConCodigo(1);
    } else {
      logEvent(tag.c_str(), "Error leyendo el DHT11");
      beepConCodigo(2);
    }
  }
  

  logEvent("ESP-32","Entrando en modo deep sleep...");
  apagarWiFi();
  beepConCodigo(3);
  esp_sleep_enable_timer_wakeup(TIEMPO_DORMIR_US); // Configura tiempo de sueño
  esp_deep_sleep_start(); // Entra en modo deep sleep
}

void loop() {
  // No se necesita, porque setup() corre al despertar
}