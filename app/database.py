# database.py
import sqlite3
from contextlib import contextmanager
from datetime import datetime
import pytz
import uuid
from pathlib import Path # Importar Path

# Define la zona horaria de Colombia
COLOMBIA_TIMEZONE = pytz.timezone('America/Bogota')

# El ensayo genérico global (UUID 0000...0000) ya no se creará aquí,
# cada controlador tendrá su propio ensayo genérico único.
# Sin embargo, mantenemos la definición por si se hace referencia en otros lugares
# para claridad, aunque su creación se moverá.
# GENERIC_ENSAYO_UUID = uuid.UUID("00000000-0000-0000-0000-000000000000")
# GENERIC_ENSAYO_NOMBRE = "Ensayo Genérico"

# Define el nombre del archivo de la base de datos SQLite
# Obtener el directorio base del archivo database.py
BASE_DIR = Path(__file__).resolve().parent
# Construir la ruta al directorio 'data' dentro de 'app'
DATABASE_DIR = BASE_DIR / "data"
# Asegurarse de que el directorio 'data' exista
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
# Ruta completa al archivo de la base de datos
DATABASE_URL = DATABASE_DIR / "sensores.db"

def get_colombia_timestamp():
    return datetime.now(COLOMBIA_TIMEZONE).isoformat()

def init_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    La creación de ensayos genéricos específicos por controlador se manejará en el CRUD.
    """
    with sqlite3.connect(DATABASE_URL) as conn: # Usar DATABASE_URL como Path o string
        cursor = conn.cursor()

        # Tabla para los usuarios (la creamos primero por si se necesita para otras tablas)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                uuid_usuario TEXT PRIMARY KEY,        -- UUID único del usuario
                nombre_usuario TEXT NOT NULL UNIQUE,  -- Nombre de usuario único
                correo TEXT NOT NULL UNIQUE,          -- Correo electrónico único
                hashed_password TEXT NOT NULL         -- Contraseña hasheada
            )
        """)

        # Tabla para los ensayos
        # uuid_controlador puede ser NULL para ensayos genéricos o no asociados directamente
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ensayos (
                uuid_ensayo TEXT PRIMARY KEY,         -- UUID único del ensayo
                nombre_ensayo TEXT NOT NULL,          -- Nombre del ensayo
                uuid_controlador TEXT,                -- Ahora puede ser NULL (para ensayo genérico)
                timestamp_registro TEXT NOT NULL,     -- Fecha y hora de registro del ensayo (zona horaria Colombia)
                estado TEXT NOT NULL DEFAULT 'Parado', -- Estado del ensayo (Parado, Corriendo, Finalizado, Default)
                FOREIGN KEY (uuid_controlador) REFERENCES controladores(uuid_controlador) ON DELETE SET NULL
            )
        """)

        # Tabla para los controladores
        # Añadimos uuid_ensayo_generico y uuid_ensayo_activo
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS controladores (
                uuid_controlador TEXT PRIMARY KEY,    -- UUID único del controlador
                uuid_ensayo_generico TEXT NOT NULL,   -- Llave foránea de un ensayo genérico asignado (por controlador)
                uuid_ensayo_activo TEXT,              -- UUID del ensayo activo actualmente en este controlador
                nombre_controlador TEXT NOT NULL,     -- Nombre asociado al controlador
                timestamp_registro TEXT NOT NULL,     -- Fecha y hora de registro del controlador (zona horaria Colombia)
                estado TEXT NOT NULL DEFAULT 'Inactivo', -- Estado del controlador (Activo, En ensayo, Inactivo)
                bateria REAL,                         -- Voltaje de la batería
                FOREIGN KEY (uuid_ensayo_generico) REFERENCES ensayos(uuid_ensayo) ON DELETE RESTRICT,
                FOREIGN KEY (uuid_ensayo_activo) REFERENCES ensayos(uuid_ensayo) ON DELETE SET NULL
            )
        """)

        # Tabla para las lecturas de los sensores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lecturas_sensor (
                uuid_lectura TEXT PRIMARY KEY,        -- Llave primaria única para identificar la lectura
                uuid_controlador TEXT NOT NULL,       -- Llave foránea del controlador desde el cual se realizó la lectura
                uuid_ensayo TEXT,                     -- Llave foránea del ensayo asociado a esta lectura (puede ser NULL para genérico)
                id_sensor INTEGER NOT NULL,           -- Número del 1-4 para identificar el sensor
                timestamp TEXT NOT NULL,              -- Fecha y hora de la medición en formato ISO8601 huso horario de Colombia UTC-5
                lectura_temperatura REAL NOT NULL,    -- Lectura de temperatura en °C
                lectura_humedad REAL NOT NULL,        -- Porcentaje de humedad relativa del aire
                lectura_bateria REAL,                 -- Voltaje de batería reportado
                FOREIGN KEY (uuid_controlador) REFERENCES controladores(uuid_controlador) ON DELETE CASCADE,
                FOREIGN KEY (uuid_ensayo) REFERENCES ensayos(uuid_ensayo) ON DELETE SET NULL
            )
        """)
        conn.commit() # Guarda los cambios en la base de datos

@contextmanager
def get_db_connection():
    """
    Proporciona una conexión a la base de datos SQLite.
    Utiliza un context manager para asegurar que la conexión se cierre automáticamente.
    Esto ayuda a mantener la estabilidad y gestionar el pool de conexiones de forma implícita.
    """
    conn = sqlite3.connect(DATABASE_URL) # Usar DATABASE_URL como Path o string
    try:
        yield conn # Retorna la conexión para ser usada
    finally:
        conn.close() # Asegura que la conexión se cierre al salir del bloque 'with'

# Inicializa la base de datos al importar este módulo
init_db()

