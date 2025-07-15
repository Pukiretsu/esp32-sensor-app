#include "config_api.h"
#include "logic_event_logger.h"
#include "config_sd.h"

const char* logTag = "HTTP_CLIENT";
String msg;

bool enviarDatosAPI(const char* serverName, const String& payload) {
  char const* sslCert = cargarCertsSSL().c_str();
  WiFiClientSecure client;
  client.setCACert(sslCert);

  HTTPClient https;
  https.setTimeout(10000);

  // Iniciar conexión HTTPS con el servidor
  if (!https.begin(client, serverName)) {
    logEvent(logTag, "Error al conectar con el servidor.");
    return false;
  }

  // Establecer el tipo de contenido como JSON
  https.addHeader("Content-Type", "application/json");

  // Realizar la petición POST y capturar el código de respuesta
  int httpCode = https.POST(payload);

  if (httpCode > 0) {
    msg = "Código de respuesta: " + String(httpCode);
    logEvent(logTag, msg.c_str());

    // Leer respuesta si el código es 200 OK
    if (httpCode == HTTP_CODE_OK) {
      String response = https.getString();
      Serial.println("📥 Respuesta del servidor: " + response);
      https.end();
      return true;
    }
  } else {
    msg = "Error en la conexión: " + https.errorToString(httpCode); 
    logEvent(logTag, msg.c_str());
  }

  https.end(); // Finalizar la conexión
  return false;
}