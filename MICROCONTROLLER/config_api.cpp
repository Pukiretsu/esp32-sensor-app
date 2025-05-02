#include "config_api.h"
#include "certs.h"
#include <WiFiClientSecure.h>
const char* root_ca = ROOT_CA_CERT;

void enviarDatosAPI(const char* url, String datos) {
  WiFiClientSecure cliente;
  cliente.setInsecure();
  //cliente.setCACert(root_ca);  // Aquí cargamos el certificado raíz

  HTTPClient http;
  http.begin(cliente, url);

  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(datos);
  if (httpResponseCode > 0) {
    Serial.print("Código de respuesta HTTP: ");
    Serial.println(httpResponseCode);
  } else {
    Serial.print("Error en la solicitud POST: ");
    Serial.println(httpResponseCode);
  }

  http.end();
}
