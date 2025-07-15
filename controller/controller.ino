#include <WiFi.h>           
#include <HTTPClient.h>     
#include <DHT.h>            
#include <ArduinoJson.h>    

// --- Configuración de WiFi ---
const char* WIFI_SSID = "TU_NOMBRE_DE_RED"; // ¡CAMBIA ESTO por el nombre de tu red WiFi!
const char* WIFI_PASSWORD = ""; // ¡CAMBIA ESTO por una cadena vacía para redes abiertas!

// --- Configuración de la API ---
const char* API_HOST = "secador-solar-gia.online"; // O la IP de tu servidor si no usas dominio/Traefik
const int API_PORT = 443; // Usar 443 para HTTPS con Traefik
const char* API_PATH = "/api/sensor/"; // Ruta del endpoint para enviar lecturas

// --- UUIDs del Controlador y Ensayo ---
// ¡IMPORTANTE! Genera estos UUIDs en tu frontend o en línea y pégalos aquí.
// Asegúrate de que el UUID del controlador ya esté registrado en tu sistema.
// Asegúrate de que el UUID del ensayo ya esté registrado en tu sistema y asociado al controlador.
const char* CONTROLLER_UUID = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"; // Reemplaza con el UUID de tu controlador
const char* ENSAYO_UUID = "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy";     // Reemplaza con el UUID de tu ensayo
const char* ENSAYO_NOMBRE = "Ensayo_Secado_Inicial"; // ¡IMPORTANTE! Asegúrate de que este nombre coincida con el ensayo registrado con el UUID anterior

// --- Configuración de Sensores DHT11 ---
#define DHTTYPE DHT11 // Tipo de sensor: DHT11 (también puede ser DHT22)

// Definir los pines a los que están conectados los 4 sensores DHT11
// CAMBIAR A LOS PINES CONECTADOS
#define DHTPIN1 4  // GPIO 4
#define DHTPIN2 16 // GPIO 16
#define DHTPIN3 17 // GPIO 17
#define DHTPIN4 5  // GPIO 5

// Inicializar los objetos DHT para cada sensor
DHT dht1(DHTPIN1, DHTTYPE);
DHT dht2(DHTPIN2, DHTTYPE);
DHT dht3(DHTPIN3, DHTTYPE);
DHT dht4(DHTPIN4, DHTTYPE);

// Frecuencia de envío de datos (en milisegundos)
const long SEND_INTERVAL_MS = 60000; // Enviar datos cada 60 segundos (60000 ms)
unsigned long lastSendTime = 0; // Para controlar el tiempo del último envío

void setup() {
    Serial.begin(115200); // Inicializar comunicación serial para depuración
    delay(100);
    Serial.println("\nIniciando ESP32...");

    // Conectar a WiFi
    Serial.print("Conectando a WiFi: ");
    Serial.println(WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi conectado!");
    Serial.print("Dirección IP: ");
    Serial.println(WiFi.localIP());

    // Inicializar los sensores DHT
    dht1.begin();
    dht2.begin();
    dht3.begin();
    dht4.begin();
    Serial.println("Sensores DHT inicializados.");
}

void loop() {
    // Solo enviar datos si ha pasado el intervalo de tiempo
    if (millis() - lastSendTime >= SEND_INTERVAL_MS) {
        lastSendTime = millis(); // Actualizar el tiempo del último envío

        Serial.println("\n--- Leyendo datos de sensores ---");

        // Array para almacenar los objetos DHT y sus pines
        DHT* dhts[] = {&dht1, &dht2, &dht3, &dht4};
        int dhtPins[] = {DHTPIN1, DHTPIN2, DHTPIN3, DHTPIN4};

        for (int i = 0; i < 4; i++) {
            int sensorId = i + 1; // ID del sensor (1 a 4)

            // Leer humedad y temperatura
            float h = dhts[i]->readHumidity();
            float t = dhts[i]->readTemperature();

            // Comprobar si alguna lectura falló
            if (isnan(h) || isnan(t)) {
                Serial.print("Error al leer del sensor DHT");
                Serial.println(sensorId);
                continue; // Saltar a la siguiente iteración si la lectura falló
            }

            Serial.print("Sensor "); Serial.print(sensorId);
            Serial.print(" (Pin "); Serial.print(dhtPins[i]);
            Serial.print("): Humedad = "); Serial.print(h);
            Serial.print("%, Temperatura = "); Serial.print(t);
            Serial.println("°C");

            // Construir el JSON para enviar a la API
            StaticJsonDocument<256> doc; // Tamaño del documento JSON (ajustar si es necesario)
            doc["uuid_controlador"] = CONTROLLER_UUID;
            doc["id_sensor"] = sensorId;
            doc["uuid_ensayo"] = ENSAYO_UUID;
            doc["nombre_ensayo"] = ENSAYO_NOMBRE;
            doc["lectura_temperatura"] = t;
            doc["lectura_humedad"] = h;

            String jsonPayload;
            serializeJson(doc, jsonPayload); // Serializar el JSON a un String
            Serial.print("Payload JSON: ");
            Serial.println(jsonPayload);

            // Enviar datos a la API
            HTTPClient http;

            // Para HTTPS, usar http.begin(url) con un host y puerto separados.
            // Esto permite que la librería maneje la conexión segura.
            http.begin(API_HOST, API_PORT, API_PATH);
            http.addHeader("Content-Type", "application/json"); // Establecer el tipo de contenido

            Serial.print("Enviando POST al servidor...");
            int httpResponseCode = http.POST(jsonPayload); // Enviar la solicitud POST

            if (httpResponseCode > 0) {
                Serial.print("Código de respuesta HTTP: ");
                Serial.println(httpResponseCode);
                String response = http.getString(); // Obtener la respuesta del servidor
                Serial.print("Respuesta del servidor: ");
                Serial.println(response);
            } else {
                Serial.print("Error en la solicitud HTTP: ");
                Serial.println(http.errorToString(httpResponseCode).c_str());
            }

            http.end(); // Cerrar la conexión
            delay(100); // Pequeña pausa entre envíos de sensores para evitar saturación
        }
    }
}
