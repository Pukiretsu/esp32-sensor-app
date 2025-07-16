# crud.py
import sqlite3
from typing import List, Optional
from datetime import datetime
import uuid
import pytz

from database import get_db_connection
from models import LecturaSensorCreate, LecturaSensor, ControladorCreate, Controlador, EnsayoCreate, Ensayo

# Define la zona horaria de Colombia
COLOMBIA_TIMEZONE = pytz.timezone('America/Bogota')

def get_colombia_timestamp():
    return datetime.now(COLOMBIA_TIMEZONE).isoformat()

## Funciones para Lecturas de Sensores

def create_lectura_sensor(lectura: LecturaSensorCreate) -> LecturaSensor:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        timestamp = get_colombia_timestamp() # Genera el timestamp en zona horaria de Colombia
        cursor.execute(
            """
            INSERT INTO lecturas_sensor (timestamp, uuid_controlador, id_sensor, uuid_ensayo, nombre_ensayo, lectura_temperatura, lectura_humedad)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                str(lectura.uuid_controlador), # Convierte UUID a string para SQLite
                lectura.id_sensor,
                str(lectura.uuid_ensayo),     # Convierte UUID a string para SQLite
                lectura.nombre_ensayo,
                lectura.lectura_temperatura,
                lectura.lectura_humedad,
            ),
        )
        conn.commit() # Confirma la transacción
        # Retorna el objeto LecturaSensor completo, incluyendo el timestamp generado
        return LecturaSensor(
            timestamp=datetime.fromisoformat(timestamp),
            uuid_controlador=lectura.uuid_controlador,
            id_sensor=lectura.id_sensor,
            uuid_ensayo=lectura.uuid_ensayo,
            nombre_ensayo=lectura.nombre_ensayo,
            lectura_temperatura=lectura.lectura_temperatura,
            lectura_humedad=lectura.lectura_humedad,
        )

def get_lecturas_sensor(
    uuid_controlador: Optional[uuid.UUID] = None,
    id_sensor: Optional[int] = None,
    uuid_ensayo: Optional[uuid.UUID] = None,
    skip: int = 0,
    limit: int = 100
) -> List[LecturaSensor]:
    """
    Recupera lecturas de sensores de la base de datos, con opciones de filtrado y paginación.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row # Permite acceder a las columnas por nombre (ej. row['timestamp'])
        cursor = conn.cursor()
        query = "SELECT * FROM lecturas_sensor WHERE 1=1" # 1=1 para facilitar la adición de condiciones WHERE
        params = []

        # Añade condiciones de filtro si se proporcionan los parámetros
        if uuid_controlador:
            query += " AND uuid_controlador = ?"
            params.append(str(uuid_controlador))
        if id_sensor:
            query += " AND id_sensor = ?"
            params.append(id_sensor)
        if uuid_ensayo:
            query += " AND uuid_ensayo = ?"
            params.append(str(uuid_ensayo))
        
        # Ordenar por timestamp de forma descendente para obtener las más recientes primero
        query += " ORDER BY timestamp DESC" 
        
        query += f" LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cursor.execute(query, params)
        rows = cursor.fetchall() # Obtiene todas las filas que coinciden
        # Convierte cada fila (sqlite3.Row) a un objeto LecturaSensor Pydantic
        return [LecturaSensor(**row) for row in rows]

def get_latest_lectura_sensor() -> Optional[LecturaSensor]:
    """
    Obtiene la última lectura de sensor registrada en la base de datos.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Selecciona la lectura más reciente ordenando por timestamp descendente y limitando a 1
        cursor.execute("SELECT * FROM lecturas_sensor ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        return LecturaSensor(**row) if row else None


def get_lectura_sensor_by_pk(timestamp: str, uuid_controlador: uuid.UUID, id_sensor: int) -> Optional[LecturaSensor]:
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM lecturas_sensor
            WHERE timestamp = ? AND uuid_controlador = ? AND id_sensor = ?
            """,
            (timestamp, str(uuid_controlador), id_sensor),
        )
        row = cursor.fetchone()
        return LecturaSensor(**row) if row else None

def delete_lectura_sensor(timestamp: str, uuid_controlador: uuid.UUID, id_sensor: int) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM lecturas_sensor
            WHERE timestamp = ? AND uuid_controlador = ? AND id_sensor = ?
            """,
            (timestamp, str(uuid_controlador), id_sensor),
        )
        conn.commit()
        return cursor.rowcount > 0

## Funciones para Controladores

def create_controlador(controlador: ControladorCreate) -> Controlador:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        uuid_c = uuid.uuid4()
        timestamp_registro = get_colombia_timestamp()
        cursor.execute(
            """
            INSERT INTO controladores (uuid_controlador, nombre_controlador, timestamp_registro)
            VALUES (?, ?, ?)
            """,
            (str(uuid_c), controlador.nombre_controlador, timestamp_registro),
        )
        conn.commit()
        return Controlador(
            uuid_controlador=uuid_c,
            nombre_controlador=controlador.nombre_controlador,
            timestamp_registro=datetime.fromisoformat(timestamp_registro),
        )

def get_controladores(skip: int = 0, limit: int = 100) -> List[Controlador]:
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM controladores LIMIT ? OFFSET ?", (limit, skip))
        rows = cursor.fetchall()
        return [Controlador(**row) for row in rows]

def get_controlador(uuid_controlador: uuid.UUID) -> Optional[Controlador]:
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM controladores WHERE uuid_controlador = ?",
            (str(uuid_controlador),),
        )
        row = cursor.fetchone()
        return Controlador(**row) if row else None

def update_controlador(uuid_controlador: uuid.UUID, controlador: ControladorCreate) -> Optional[Controlador]:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE controladores
            SET nombre_controlador = ?
            WHERE uuid_controlador = ?
            """,
            (controlador.nombre_controlador, str(uuid_controlador)),
        )
        conn.commit()
        if cursor.rowcount > 0:
            return get_controlador(uuid_controlador)
        return None

def delete_controlador(uuid_controlador: uuid.UUID) -> bool:
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Debido a ON DELETE CASCADE en la DB, las entradas de ensayos y lecturas
        # asociadas a este controlador se eliminarán automáticamente.
        cursor.execute(
            "DELETE FROM controladores WHERE uuid_controlador = ?",
            (str(uuid_controlador),),
        )
        conn.commit()
        return cursor.rowcount > 0

## Nuevas Funciones para Ensayos

def create_ensayo(ensayo: EnsayoCreate) -> Ensayo:
    """
    Inserta un nuevo ensayo en la base de datos, asociado a un controlador.
    Se genera un nuevo UUID y el timestamp de registro.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        uuid_e = uuid.uuid4()
        timestamp_registro = get_colombia_timestamp()
        cursor.execute(
            """
            INSERT INTO ensayos (uuid_ensayo, nombre_ensayo, uuid_controlador, timestamp_registro)
            VALUES (?, ?, ?, ?)
            """,
            (str(uuid_e), ensayo.nombre_ensayo, str(ensayo.uuid_controlador), timestamp_registro),
        )
        conn.commit()
        return Ensayo(
            uuid_ensayo=uuid_e,
            nombre_ensayo=ensayo.nombre_ensayo,
            uuid_controlador=ensayo.uuid_controlador,
            timestamp_registro=datetime.fromisoformat(timestamp_registro),
        )

def get_ensayos(uuid_controlador: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 100) -> List[Ensayo]:
    """
    Recupera todos los ensayos de la base de datos, con paginación y filtrado por controlador.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM ensayos WHERE 1=1"
        params = []
        if uuid_controlador:
            query += " AND uuid_controlador = ?"
            params.append(str(uuid_controlador))
        
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, skip])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [Ensayo(**row) for row in rows]

def get_ensayo(uuid_ensayo: uuid.UUID) -> Optional[Ensayo]:
    """
    Recupera un ensayo específico por su UUID.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ensayos WHERE uuid_ensayo = ?",
            (str(uuid_ensayo),),
        )
        row = cursor.fetchone()
        return Ensayo(**row) if row else None

def delete_ensayo(uuid_ensayo: uuid.UUID) -> bool:
    """
    Elimina un ensayo por su UUID.
    Retorna True si se eliminó un registro, False en caso contrario.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Debido a ON DELETE CASCADE en la DB, las lecturas asociadas a este ensayo se eliminarán automáticamente.
        cursor.execute(
            "DELETE FROM ensayos WHERE uuid_ensayo = ?",
            (str(uuid_ensayo),),
        )
        conn.commit()
        return cursor.rowcount > 0
