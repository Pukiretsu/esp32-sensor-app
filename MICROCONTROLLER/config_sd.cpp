#include "config_sd.h"

bool inicializarSD() {
  if (!SD.begin()) {
    Serial.println("SD | Fallo al iniciar SD");
    return false;
  }
  Serial.println("SD | SD inicializada correctamente");
  return true;
}

void escribirArchivo(const char* path, const char* mensaje) {
  File archivo = SD.open(path, FILE_APPEND);
  
  int intentos = 0;
  while (!archivo && intentos < 3) {
    Serial.println("SD | Error abriendo el archivo, reintentando...");
    delay(1000);
    archivo = SD.open(path, FILE_APPEND);
    intentos++;
  }
  
  if (!archivo) {
    Serial.println("SD | Error al abrir el archivo tras 3 intentos.");
    return;
  }

  archivo.println(mensaje);
  archivo.close();
}
