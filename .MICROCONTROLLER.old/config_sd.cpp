#include "config_sd.h"
#include "config_api.h"
#include <Arduino.h>
#include <SD.h>

const char* CONFIGS_FILE = "/config.conf"; 
const char* BUFFER_FILE = "/buffer.jsonl"; 

String config_return;

bool inicializarSD() {
  if (!SD.begin()) {
    Serial.println("-->> [SD]\t\t| Fallo al iniciar SD.");
    return false;
  }

  Serial.println("-->> [SD]\t\t| SD inicializada correctamente.");
  return true;
}

void escribirArchivo(const char* path, const char* mensaje) {
  File archivo = SD.open(path, FILE_APPEND);
  
  int intentos = 0;
  while (!archivo && intentos < 3) {
    Serial.println("-->> [SD]\t\t| Error abriendo el archivo, reintentando...");
    delay(1000);
    archivo = SD.open(path, FILE_APPEND);
    intentos++;
  }
  
  if (!archivo) {
    Serial.println("-->> [SD]\t\t| Error al abrir el archivo tras 3 intentos.");
    return;
  }

  archivo.println(mensaje);
  archivo.close();
}

String leerConfiguraciones(String option) {
  String data = "";
  uint8_t option_length = option.length();

  File file = SD.open(CONFIGS_FILE);
  if (!file) {
    Serial.println("-->> [SD]\t\t| No se pudo abrir config.txt");
    return "";
  }

  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();
    if (line.startsWith(option)) {
      data = line.substring(option_length);
      break;
    }
  }

  file.close();
  return data;
}

String cargarConfigWifiSSID() {
  config_return = leerConfiguraciones("ssid=");
  return config_return;
}

String cargarConfigWifiPASWORD() {
  return leerConfiguraciones("password=");
}

String cargarConfigSensorSESSION() {
  return leerConfiguraciones("session=");
}

uint16_t cargarConfigSLEEP() {
  String data = leerConfiguraciones("sleep_time=");
  return data.toInt();
}

String cargarConfigENDPOINT_LOG() {
  return leerConfiguraciones("url_logs=");
}

String cargarConfigENDPOINT_SENSOR() {
  return leerConfiguraciones("url_sensor=");
}

String cargarCertsSSL() {
  File certFile = SD.open("/cert.pem");
  if (!certFile) {
    Serial.println("-->> [SD]\t\t| No se pudo abrir cert.pem");
    return "";
  }

  String certificado = "";
  while (certFile.available()) {
    certificado += certFile.readStringUntil('\n') + "\n";
  }

  certFile.close();
  return certificado;
}

void storeBuffer(const char* json) {
  File file = SD.open(BUFFER_FILE, FILE_APPEND);
  
  if (!file) {
    Serial.println("-->> [SD]\t\t| Error al abrir buffer.jsonl para escribir.");
    return;
  }

  file.println(json);  // guarda el JSON como línea separada
  file.close();
  Serial.println("-->> [SD]\t\t| JSON almacenado en buffer.");
}

void reintentarEnvioBuffer() {
  const char* sensor_api = cargarConfigENDPOINT_SENSOR().c_str();
  File file = SD.open(BUFFER_FILE, FILE_READ);
  if (!file) {
    Serial.println("-->> [SD]\t\t| No se encontró buffer para reintentar.");
  return;
  }

  File temp = SD.open("/temp.jsonl", FILE_WRITE);  // archivo temporal
  if (!temp) {
    Serial.println("-->> [SD]\t\t| Error creando archivo temporal.");
    file.close();
    return;
  }

  while (file.available()) {
    String line = file.readStringUntil('\n');
    line.trim();
    
    if (line.length() == 0) continue;

    bool exito = false;
    exito = enviarDatosAPI(sensor_api, line.c_str());

    if (!exito) {
      temp.println(line);  // si falla, lo volvemos a guardar
    }
  }

  file.close();
  temp.close();

  // Reemplazamos el archivo original por el temporal
  SD.remove(BUFFER_FILE);
  SD.rename("/temp.jsonl", BUFFER_FILE);
}