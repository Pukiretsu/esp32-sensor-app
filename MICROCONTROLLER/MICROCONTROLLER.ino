#include "config_wifi.h"
#include "config_sd.h"
#include "config_api.h"
#include "logic_dht11.h"
#include "logic_event_logger.h"
#include "time_sync.h"
#include "esp_sleep.h"

const char* archivoSensor = "/dht11.csv";
const int BUZZER_PIN = 15;
const uint8_t pinDHT_1 = 27;
const uint8_t pinDHT_2 = 26;
const uint8_t pinDHT_3 = 25;
const uint8_t pinDHT_4 = 22;
const uint8_t dht_pins[4] = {pinDHT_1, pinDHT_2, pinDHT_3, pinDHT_4};

String SSID;
String PASSWORD;
uint32_t SLEEP_INTERVAL;
String ENDPOINT_SENSOR;
String SESSION;

void setup() {
  encenderWiFi();
  
  Serial.begin(115200);
  
  delay(1000); // pequeño delay para estabilizar todo
  String msg, tag;

  inicializarBuzzer(BUZZER_PIN);
  Serial.println("ESP-32 | Encendido, Configurandose ahora.");
  if (!inicializarSD()) {
      Serial.println("SD | Error con la SD, deteniendo ejecución");
      beepConCodigo(2);
      return;
  }
  
  // ----------- Cargar Configuraciones del Sistema
  // Wifi
  SSID = cargarConfigWifiSSID();
  PASSWORD = cargarConfigWifiPASWORD();
  msg = "SSID: " + SSID + "Passwd: " + PASSWORD;
  logEvent("ESP-32", msg.c_str());
  // Sleep
  SLEEP_INTERVAL = cargarConfigSLEEP();
  uint32_t TIEMPO_DORMIR_US = SLEEP_INTERVAL * 1000000UL;
  msg = "Tiempo de dormir" + String(TIEMPO_DORMIR_US) + "uS";
  logEvent("ESP-32", msg.c_str());
  // API
  SESSION = cargarConfigSensorSESSION();
  msg = "Sesion: " + SESSION;
  logEvent("ESP-32", msg.c_str()); 
  ENDPOINT_SENSOR = cargarConfigENDPOINT_SENSOR();
  msg = "Endpoints - Sensor: " + ENDPOINT_SENSOR; 
  logEvent("ESP-32", msg.c_str()); 


  if (!PASSWORD) {
    configurarWiFi_WPA2(SSID.c_str(), PASSWORD.c_str());
  } else {
    configurarWiFi_OPEN(SSID.c_str());
  }

  if (checkWifi()){
    sincronizarHoraNTP("UTC-5");
    reintentarEnvioBuffer();
  }

  logEvent("ESP-32", "Configurado y listo");
  beepConCodigo(0);
  
  msg = "Fecha y hora actual: " + obtenerFechaHora();
  logEvent("NTP", msg.c_str());

  for (int i = 0; i < 2; i++){
    iniciarDHT(dht_pins[i]);
    float temp = leerTemperatura();
    float hum = leerHumedad();
    tag = String("DHT11-") + String(i+1);

    if (!isnan(temp) && !isnan(hum)) {
      delay(2000); // pequeño delay para estabilizar todo
      msg = "Temp: " + String(temp) + " °C, Hum: " + String(hum) + "%";
      logEvent(tag.c_str(), msg.c_str());

      String datos = SESSION + "," + obtenerFechaHora() + " , " + String(i+1) + " , " + String(temp) + " , " + String(hum);
      escribirArchivo(archivoSensor, datos.c_str());

      String json = "{\"dht11_number\": " + String(i+1) + ", \"temperature\": " + String(temp, 2) + ", \"humidity\": " + String(hum, 2) + ", \"record_session\": \"" + SESSION + "\"}";
      Serial.println(json);
      if (!enviarDatosAPI(ENDPOINT_SENSOR.c_str(), json)) {
        storeBuffer(json.c_str());
        beepConCodigo(2);
      }
      beepConCodigo(1);

    } else {
      logEvent(tag.c_str(), "Error leyendo el DHT11");
      beepConCodigo(2);
    }
  }
  
  logEvent("ESP-32","Entrando en modo deep sleep...");
  apagarWiFi();
  beepConCodigo(3);
  esp_sleep_enable_timer_wakeup(TIEMPO_DORMIR_US); 
  esp_deep_sleep_start();
}

void loop() {
  // No se necesita, porque setup() corre al despertar
}