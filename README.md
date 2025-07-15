Proyecto Secador Solar - Automatización y Monitoreo
Descripción
Este proyecto implementa un sistema de automatización y monitoreo para un secador solar, utilizando sensores DHT11 conectados a dispositivos ESP32. La solución incluye una API RESTful desarrollada con FastAPI para el registro y consulta de datos de humedad y temperatura en una base de datos SQLite, y un frontend web para visualizar el estado y las lecturas de los sensores en tiempo real.

El objetivo principal es proporcionar una plataforma ligera y eficiente, adecuada para ser desplegada en un VPS (Servidor Privado Virtual) con recursos limitados, garantizando la estabilidad y el rendimiento.

Características
API RESTful con FastAPI: Backend robusto y de alto rendimiento para la gestión de datos.

Base de Datos SQLite: Solución de almacenamiento ligera y sin servidor, ideal para entornos con recursos limitados.

Sistema CRUD: Operaciones completas (Crear, Leer, Actualizar, Eliminar) para lecturas de sensores y controladores.

Gestión de Conexiones: Pool de conexiones a SQLite para asegurar la estabilidad y eficiencia.

Timestamps en Zona Horaria de Colombia: Todas las marcas de tiempo se registran y muestran en formato ISO 8601 para la zona horaria de Bogotá (Colombia).

Frontend Web Interactivo: Interfaz de usuario para visualizar datos de sensores en tiempo real y explorar el historial.

Paginación: Implementación de paginación en los endpoints de lectura para manejar grandes volúmenes de datos eficientemente.

Documentación de API Interactiva: Generada automáticamente por FastAPI (Swagger UI).

Estructura del Proyecto
.
├── main.py             # Aplicación FastAPI principal (API y servidor frontend)
├── database.py         # Configuración y funciones de inicialización de SQLite
├── models.py           # Modelos de datos Pydantic para la validación de API
├── crud.py             # Funciones para las operaciones CRUD de la base de datos
├── templates/
│   └── index.html      # Plantilla HTML del frontend (con Jinja2)
└── static/
    ├── css/
    │   └── style.css   # Hoja de estilos CSS
    ├── js/
    │   └── app.js      # Lógica JavaScript del frontend (interacción con la API)
    ├── images/
    │   ├── gia-logo.png
    │   ├── Prototipo.webp
    │   └── montaje.webp
    └── favicon.png

Requisitos
Asegúrate de tener Python 3.8+ instalado en tu sistema.

Instalación y Ejecución
Sigue estos pasos para configurar y ejecutar el proyecto localmente:

1. Clonar el Repositorio
git clone <URL_DEL_REPOSITORIO>
cd secador-solar

2. Instalar Dependencias
Es recomendable crear un entorno virtual para gestionar las dependencias:

python -m venv venv
source venv/bin/activate  # En Linux/macOS
# venv\Scripts\activate   # En Windows

Luego, instala las librerías necesarias:

pip install fastapi uvicorn "pydantic[email]" pytz python-multipart jinja2

3. Ejecutar la Aplicación
Una vez instaladas las dependencias, puedes iniciar el servidor FastAPI:

uvicorn main:app --host 0.0.0.0 --port 8000 --reload

main:app: Indica a Uvicorn que ejecute la aplicación app definida en main.py.

--host 0.0.0.0: Permite que la aplicación sea accesible desde cualquier dirección IP (útil para despliegue).

--port 8000: El puerto en el que la aplicación escuchará las solicitudes.

--reload: Reinicia el servidor automáticamente cuando detecta cambios en el código (ideal para desarrollo).

La base de datos sensores.db se creará automáticamente en el directorio raíz del proyecto la primera vez que se ejecute la aplicación.

Uso de la API
Una vez que la aplicación esté en ejecución, puedes acceder a la documentación interactiva de la API (Swagger UI) en tu navegador:

http://127.0.0.1:8000/docs

Aquí se detallan los principales endpoints:

Endpoints de Sensores (/sensor/)
POST /sensor/: Registra una nueva lectura de sensor.

Cuerpo de la solicitud (JSON):

{
  "uuid_controlador": "string (UUID)",
  "id_sensor": "integer (1-4)",
  "uuid_ensayo": "string (UUID)",
  "nombre_ensayo": "string",
  "lectura_temperatura": "float",
  "lectura_humedad": "float"
}

GET /sensor/: Obtiene una lista de lecturas de sensores. Permite filtrar por uuid_controlador, id_sensor, uuid_ensayo y paginación (skip, limit).

GET /sensor/latest: Obtiene la lectura más reciente de cualquier sensor.

GET /sensor/{timestamp}/{uuid_controlador}/{id_sensor}: Obtiene una lectura específica por su clave primaria compuesta.

DELETE /sensor/{timestamp}/{uuid_controlador}/{id_sensor}: Elimina una lectura específica.

Endpoints de Controladores (/controladores/)
POST /controladores/: Registra un nuevo controlador.

Cuerpo de la solicitud (JSON):

{
  "nombre_controlador": "string"
}

GET /controladores/: Obtiene una lista de todos los controladores registrados. Soporta paginación (skip, limit).

GET /controladores/{uuid_controlador}: Obtiene los detalles de un controlador específico.

PUT /controladores/{uuid_controlador}: Actualiza el nombre de un controlador existente.

DELETE /controladores/{uuid_controlador}: Elimina un controlador.

Frontend
El frontend se sirve directamente desde la aplicación FastAPI en la ruta raíz (/). Proporciona las siguientes secciones:

Inicio: Muestra una descripción del proyecto, el estado actual del ESP32 y las últimas lecturas de temperatura y humedad.

Datos Sensor: Presenta una tabla con el historial de lecturas de los sensores, con opciones para refrescar y exportar a CSV.

Logs: (Nota: Esta sección está presente en el frontend, pero la API actual no tiene un endpoint dedicado para logs genéricos con la estructura esperada. Mostrará un mensaje de "No hay datos para mostrar".)

Acerca de: Información sobre el equipo del proyecto y las tecnologías utilizadas.

Consideraciones para Despliegue en VPS
Ligereza: El uso de FastAPI y SQLite hace que la aplicación sea muy ligera en consumo de RAM y CPU, ideal para VPS con recursos limitados.

Escalabilidad: Para proyectos más grandes o con mayor concurrencia, se podría considerar migrar a una base de datos más robusta (ej. PostgreSQL) y/o implementar un balanceador de carga.

Seguridad: Para un entorno de producción, se recomienda añadir autenticación/autorización a la API, usar HTTPS y configurar un servidor web como Nginx o Apache como proxy inverso.

Tecnologías Utilizadas
Backend: Python (FastAPI)

Base de Datos: SQLite

Frontend: HTML5, CSS3, JavaScript (jQuery)

Control de Versiones: Git

Contenedorización: Docker (opcional, pero recomendado para despliegue)

Manejo de Zonas Horarias: pytz

Equipo del Proyecto
Angie Katherine Hurtado Montañez: Ingeniera agrícola en formación

LinkedIn

Correo

Jhony Javier Patiño Alvira: Ingeniero agrícola en formación

LinkedIn

Correo

Angel Leonardo Gonzalez Padilla: Ingeniero agrícola en formación

LinkedIn

Correo

Licencia
Este proyecto se distribuye bajo la licencia MIT. Consulta el archivo LICENSE para más detalles.