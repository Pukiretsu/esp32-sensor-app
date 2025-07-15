# database.py
import sqlite3
from contextlib import contextmanager

# Define el nombre del archivo de la base de datos SQLite
DATABASE_URL = "data/sensores.db"

def init_db():
    """
    Inicializa la base de datos creando las tablas si no existen.
    """
    with sqlite3.connect(DATABASE_URL) as conn:
        cursor = conn.cursor()
        # Tabla para los controladores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS controladores (
                uuid_controlador TEXT PRIMARY KEY,    -- UUID único del controlador
                nombre_controlador TEXT NOT NULL,     -- Nombre asociado al controlador
                timestamp_registro TEXT NOT NULL      -- Fecha y hora de registro del controlador (zona horaria Colombia)
            )
        """)
        # Nueva tabla para los ensayos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ensayos (
                uuid_ensayo TEXT PRIMARY KEY,         -- UUID único del ensayo
                nombre_ensayo TEXT NOT NULL,          -- Nombre del ensayo
                uuid_controlador TEXT NOT NULL,       -- Nuevo: UUID del controlador asociado
                timestamp_registro TEXT NOT NULL,     -- Fecha y hora de registro del ensayo (zona horaria Colombia)
                FOREIGN KEY (uuid_controlador) REFERENCES controladores(uuid_controlador) ON DELETE CASCADE
            )
        """)
        # Tabla para las lecturas de los sensores
        # Se asegura que se cree DESPUÉS de 'controladores' y 'ensayos'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS lecturas_sensor (
                timestamp TEXT NOT NULL,          -- Fecha y hora de la lectura en formato ISO (zona horaria Colombia)
                uuid_controlador TEXT NOT NULL,   -- UUID único del controlador
                id_sensor INTEGER NOT NULL,       -- ID del sensor (1 a 4)
                uuid_ensayo TEXT NOT NULL,        -- UUID del ensayo asociado
                nombre_ensayo TEXT NOT NULL,      -- Nombre del ensayo
                lectura_temperatura REAL NOT NULL,-- Medida de temperatura en Celsius
                lectura_humedad REAL NOT NULL,    -- Medida de humedad
                PRIMARY KEY (timestamp, uuid_controlador, id_sensor), -- Clave primaria compuesta para unicidad
                FOREIGN KEY (uuid_controlador) REFERENCES controladores(uuid_controlador) ON DELETE CASCADE,
                FOREIGN KEY (uuid_ensayo) REFERENCES ensayos(uuid_ensayo) ON DELETE CASCADE
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
    conn = sqlite3.connect(DATABASE_URL)
    try:
        yield conn # Retorna la conexión para ser usada
    finally:
        conn.close() # Asegura que la conexión se cierre al salir del bloque 'with'

# Inicializa la base de datos al importar este módulo
init_db()
