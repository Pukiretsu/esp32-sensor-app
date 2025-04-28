# esp32-sensor-app 📡🦀

Sistema automatizado de toma de datos desde sensores utilizando un ESP32, una API escrita en Rust y una interfaz web para monitoreo. Todo el ecosistema está orquestado mediante Docker Compose para facilitar el despliegue.

## 📦 Descripción

Este proyecto integra diferentes componentes para capturar, almacenar y visualizar datos de sensores:

- **ESP32**: Dispositivo físico que toma los datos de los sensores.
- **API en Rust**: Recibe los datos del ESP32 y los almacena en una base de datos PostgreSQL.
- **PostgreSQL**: Base de datos relacional para persistir los datos.
- **Frontend (Web Estática)**: Visualiza los datos de forma amigable.
- **Docker Compose**: Orquesta todos los servicios para facilitar el despliegue local o en servidores.

## 🗂️ Estructura del Repositorio

```bash
-
├── SERVER/             # Código fuente de la API en Rust
├──-- src/            # Página web estática para visualización
├──-- web/            # Página web estática para visualización
├──-- docker-compose.yml
├── .env.example        # Variables de entorno de ejemplo
└── README.md
