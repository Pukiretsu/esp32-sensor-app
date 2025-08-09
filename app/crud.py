# crud.py
import sqlite3
from typing import List, Optional
from datetime import datetime
import uuid
import pytz

from database import get_db_connection
from models import (
    LecturaSensorCreate, LecturaSensor,
    ControladorCreate, Controlador, EstadoControlador,
    EnsayoCreate, Ensayo, EstadoEnsayo,
    UserCreate, User, UserInDB,
    ControladorUpdateName, ControladorUpdateEnsayo
)

# Define la zona horaria de Colombia
COLOMBIA_TIMEZONE = pytz.timezone('America/Bogota')

def get_colombia_timestamp():
    return datetime.now(COLOMBIA_TIMEZONE).isoformat()

## Funciones para Lecturas de Sensores

def create_lectura_sensor(lectura: LecturaSensorCreate, uuid_ensayo_asignado: uuid.UUID) -> LecturaSensor:
    """
    Crea una nueva lectura de sensor, asignando el ensayo determinado por el backend.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        uuid_l = uuid.uuid4()
        timestamp = get_colombia_timestamp()
        
        try:
            cursor.execute(
                """
                INSERT INTO lecturas_sensor (uuid_lectura, uuid_controlador, uuid_ensayo, id_sensor, timestamp, lectura_temperatura, lectura_humedad, lectura_bateria)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid_l),
                    str(lectura.uuid_controlador),
                    str(uuid_ensayo_asignado),
                    lectura.id_sensor,
                    timestamp,
                    lectura.lectura_temperatura,
                    lectura.lectura_humedad,
                    lectura.lectura_bateria,
                ),
            )
            conn.commit()
            return LecturaSensor(
                uuid_lectura=uuid_l,
                uuid_controlador=lectura.uuid_controlador,
                uuid_ensayo=uuid_ensayo_asignado,
                id_sensor=lectura.id_sensor,
                timestamp=datetime.fromisoformat(timestamp),
                lectura_temperatura=lectura.lectura_temperatura,
                lectura_humedad=lectura.lectura_humedad,
                lectura_bateria=lectura.lectura_bateria,
            )
        except sqlite3.Error as e:
            print(f"Error al crear lectura de sensor: {e}")
            raise

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
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT * FROM lecturas_sensor WHERE 1=1"
        params = []
        if uuid_controlador:
            query += " AND uuid_controlador = ?"
            params.append(str(uuid_controlador))
        if id_sensor:
            query += " AND id_sensor = ?"
            params.append(id_sensor)
        if uuid_ensayo:
            query += " AND uuid_ensayo = ?"
            params.append(str(uuid_ensayo))
        query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
        params.extend([limit, skip])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [LecturaSensor(**row) for row in rows]

def get_latest_lectura_sensor() -> Optional[LecturaSensor]:
    """
    Obtiene la última lectura de sensor registrada en la base de datos.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM lecturas_sensor ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        return LecturaSensor(**row) if row else None

## Funciones para Controladores

def create_controlador(controlador: ControladorCreate) -> tuple[Controlador, Ensayo]:
    """
    Crea un nuevo controlador y le asigna un ensayo genérico único.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        uuid_c = uuid.uuid4()
        timestamp_registro = get_colombia_timestamp()

        # 1. Crear un ensayo genérico único para este nuevo controlador
        uuid_ensayo_generico = uuid.uuid4()
        nombre_ensayo_generico = f"Ensayo Genérico para {controlador.nombre_controlador}"
        
        try:
            # Crea el ensayo genérico con el uuid_controlador NULL por ahora
            cursor.execute(
                """
                INSERT INTO ensayos (uuid_ensayo, nombre_ensayo, uuid_controlador, timestamp_registro, estado)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(uuid_ensayo_generico),
                    nombre_ensayo_generico,
                    None, # Inicialmente NULL
                    timestamp_registro,
                    EstadoEnsayo.default.value,
                ),
            )
            
            # Crea el controlador, referenciando el ensayo genérico
            cursor.execute(
                """
                INSERT INTO controladores (uuid_controlador, uuid_ensayo_generico, uuid_ensayo_activo, nombre_controlador, timestamp_registro, estado, bateria)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid_c),
                    str(uuid_ensayo_generico),
                    str(uuid_ensayo_generico), # Por defecto, el ensayo activo es el genérico
                    controlador.nombre_controlador,
                    timestamp_registro,
                    EstadoControlador.activo.value, # Se asigna como 'Activo' al crearse
                    controlador.bateria,
                ),
            )

            # 3. Actualizar el ensayo genérico con el UUID del controlador
            cursor.execute(
                """
                UPDATE ensayos
                SET uuid_controlador = ?
                WHERE uuid_ensayo = ?
                """,
                (str(uuid_c), str(uuid_ensayo_generico)),
            )

            conn.commit()

            # Recuperar y retornar los objetos completos
            created_controlador = get_controlador(uuid_c)
            updated_ensayo_generico = get_ensayo(uuid_ensayo_generico)

            return created_controlador, updated_ensayo_generico
        
        except sqlite3.Error as e:
            conn.rollback() # Revertir si algo falla
            print(f"Error al crear controlador o su ensayo genérico: {e}")
            raise

def get_controladores(skip: int = 0, limit: int = 100) -> List[Controlador]:
    """
    Recupera controladores de la base de datos.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM controladores LIMIT ? OFFSET ?", (limit, skip))
        rows = cursor.fetchall()
        return [Controlador(**{**row, 'estado': EstadoControlador(row['estado'])}) for row in rows]

def get_controlador(uuid_controlador: uuid.UUID) -> Optional[Controlador]:
    """
    Recupera un controlador específico por su UUID.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM controladores WHERE uuid_controlador = ?",
            (str(uuid_controlador),),
        )
        row = cursor.fetchone()
        if row:
            return Controlador(**{**row, 'estado': EstadoControlador(row['estado'])})
        return None

def update_controlador_name(uuid_controlador: uuid.UUID, new_name: str) -> Optional[Controlador]:
    """
    Actualiza el nombre de un controlador existente.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE controladores
            SET nombre_controlador = ?
            WHERE uuid_controlador = ?
            """,
            (new_name, str(uuid_controlador)),
        )
        conn.commit()
        if cursor.rowcount > 0:
            return get_controlador(uuid_controlador)
        return None

def update_controlador_ensayo(uuid_controlador: uuid.UUID, uuid_ensayo_activo: uuid.UUID) -> tuple[Optional[Controlador], Optional[Ensayo]]:
    """
    Actualiza el ensayo activo de un controlador y los estados correspondientes.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # 1. Obtener el controlador y el ensayo nuevo
        controlador = get_controlador(uuid_controlador)
        ensayo_nuevo = get_ensayo(uuid_ensayo_activo)

        if not controlador or not ensayo_nuevo:
            return None, None

        # 2. Actualizar el estado del ensayo anterior (si no es el ensayo genérico)
        uuid_ensayo_anterior = controlador.uuid_ensayo_activo
        if uuid_ensayo_anterior and uuid_ensayo_anterior != controlador.uuid_ensayo_generico:
            cursor.execute(
                """
                UPDATE ensayos
                SET estado = ?
                WHERE uuid_ensayo = ?
                """,
                (EstadoEnsayo.parado.value, str(uuid_ensayo_anterior)),
            )

        # 3. Actualizar el estado del controlador
        cursor.execute(
            """
            UPDATE controladores
            SET uuid_ensayo_activo = ?, estado = ?
            WHERE uuid_controlador = ?
            """,
            (str(uuid_ensayo_activo), EstadoControlador.en_ensayo.value, str(uuid_controlador)),
        )

        # 4. Actualizar el estado del nuevo ensayo activo
        cursor.execute(
            """
            UPDATE ensayos
            SET estado = ?
            WHERE uuid_ensayo = ?
            """,
            (EstadoEnsayo.corriendo.value, str(uuid_ensayo_activo)),
        )

        conn.commit()

        # Recuperar y retornar los objetos actualizados
        updated_controlador = get_controlador(uuid_controlador)
        updated_ensayo = get_ensayo(uuid_ensayo_activo)

        return updated_controlador, updated_ensayo


def delete_controlador(uuid_controlador: uuid.UUID) -> Optional[Controlador]:
    """
    Elimina un controlador. No permite eliminar si el ensayo genérico del controlador
    tiene lecturas asociadas.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Obtener el controlador antes de intentar eliminarlo
        controlador_to_delete = get_controlador(uuid_controlador)
        if not controlador_to_delete:
            return None
        
        try:
            # Primero, eliminar el ensayo genérico asociado para evitar el error de integridad
            # Esto funcionará si no hay lecturas asociadas al ensayo genérico
            cursor.execute(
                "DELETE FROM ensayos WHERE uuid_ensayo = ?",
                (str(controlador_to_delete.uuid_ensayo_generico),),
            )
            
            # Si el ensayo genérico se elimina, ahora podemos eliminar el controlador
            cursor.execute(
                "DELETE FROM controladores WHERE uuid_controlador = ?",
                (str(uuid_controlador),),
            )
            
            conn.commit()
            
            if cursor.rowcount > 0:
                # Retornar el objeto que se eliminó
                return controlador_to_delete
            else:
                return None
        except sqlite3.IntegrityError as e:
            # Esto ocurrirá si se intenta eliminar el ensayo genérico que tiene lecturas
            print(f"Error de integridad al eliminar controlador: {e}")
            conn.rollback()
            return None
        except sqlite3.Error as e:
            print(f"Error al eliminar controlador: {e}")
            conn.rollback()
            raise


## Funciones para Ensayos

def create_ensayo(ensayo: EnsayoCreate) -> Ensayo:
    """
    Inserta un nuevo ensayo en la base de datos.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        uuid_e = uuid.uuid4()
        timestamp_registro = get_colombia_timestamp()
        cursor.execute(
            """
            INSERT INTO ensayos (uuid_ensayo, nombre_ensayo, uuid_controlador, timestamp_registro, estado)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                str(uuid_e),
                ensayo.nombre_ensayo,
                str(ensayo.uuid_controlador) if ensayo.uuid_controlador else None,
                timestamp_registro,
                ensayo.estado.value,
            ),
        )
        conn.commit()
        return Ensayo(
            uuid_ensayo=uuid_e,
            nombre_ensayo=ensayo.nombre_ensayo,
            uuid_controlador=ensayo.uuid_controlador,
            timestamp_registro=datetime.fromisoformat(timestamp_registro),
            estado=ensayo.estado,
        )

def get_ensayos(uuid_controlador: Optional[uuid.UUID] = None, skip: int = 0, limit: int = 100) -> List[Ensayo]:
    """
    Recupera ensayos de la base de datos, con paginación y filtrado.
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
        return [Ensayo(**{**row, 'estado': EstadoEnsayo(row['estado'])}) for row in rows]

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
        if row:
            return Ensayo(**{**row, 'estado': EstadoEnsayo(row['estado'])})
        return None

def update_ensayo(uuid_ensayo: uuid.UUID, ensayo: EnsayoCreate) -> Optional[Ensayo]:
    """
    Actualiza un ensayo existente.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE ensayos
            SET nombre_ensayo = ?, uuid_controlador = ?, estado = ?
            WHERE uuid_ensayo = ?
            """,
            (
                ensayo.nombre_ensayo,
                str(ensayo.uuid_controlador) if ensayo.uuid_controlador else None,
                ensayo.estado.value,
                str(uuid_ensayo)
            ),
        )
        conn.commit()
        if cursor.rowcount > 0:
            return get_ensayo(uuid_ensayo)
        return None

def delete_ensayo(uuid_ensayo: uuid.UUID) -> bool:
    """
    Elimina un ensayo. No se permite eliminar si es un ensayo genérico de algún controlador.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verificar si este ensayo es el ensayo genérico de algún controlador
        cursor.execute(
            "SELECT COUNT(*) FROM controladores WHERE uuid_ensayo_generico = ?",
            (str(uuid_ensayo),)
        )
        if cursor.fetchone()[0] > 0:
            # Si es un ensayo genérico de algún controlador, no se permite eliminar
            return False

        try:
            cursor.execute(
                "DELETE FROM ensayos WHERE uuid_ensayo = ?",
                (str(uuid_ensayo),),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.IntegrityError as e:
            # Esto podría ocurrir si hay lecturas aún referenciando este ensayo
            print(f"Error de integridad al eliminar ensayo: {e}")
            return False
        except sqlite3.Error as e:
            print(f"Error al eliminar ensayo: {e}")
            raise

def get_controller_generic_ensayo(uuid_controlador: uuid.UUID) -> Optional[Ensayo]:
    """
    Recupera el ensayo genérico asignado a un controlador específico.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT E.* FROM ensayos E
            JOIN controladores C ON E.uuid_ensayo = C.uuid_ensayo_generico
            WHERE C.uuid_controlador = ?
            """,
            (str(uuid_controlador),),
        )
        row = cursor.fetchone()
        if row:
            return Ensayo(**{**row, 'estado': EstadoEnsayo(row['estado'])})
        return None

def get_running_ensayo_for_controlador(uuid_controlador: uuid.UUID) -> Optional[Ensayo]:
    """
    Recupera el ensayo que se encuentra en estado 'Corriendo' para un controlador específico.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM ensayos WHERE uuid_controlador = ? AND estado = ?",
            (str(uuid_controlador), EstadoEnsayo.corriendo.value),
        )
        row = cursor.fetchone()
        if row:
            return Ensayo(**{**row, 'estado': EstadoEnsayo(row['estado'])})
        return None

## Funciones para Usuarios

def create_user(user: UserCreate, hashed_password: str) -> User:
    """
    Crea un nuevo usuario en la base de datos.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        uuid_u = uuid.uuid4()
        try:
            cursor.execute(
                """
                INSERT INTO users (uuid_usuario, nombre_usuario, correo, hashed_password)
                VALUES (?, ?, ?, ?)
                """,
                (str(uuid_u), user.nombre_usuario, user.correo, hashed_password),
            )
            conn.commit()
            return User(uuid_usuario=uuid_u, nombre_usuario=user.nombre_usuario, correo=user.correo)
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.nombre_usuario" in str(e):
                raise ValueError("El nombre de usuario ya existe.")
            if "UNIQUE constraint failed: users.correo" in str(e):
                raise ValueError("El correo electrónico ya está registrado.")
            raise e

def get_user_by_username(nombre_usuario: str) -> Optional[UserInDB]:
    """
    Recupera un usuario por su nombre de usuario.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE nombre_usuario = ?",
            (nombre_usuario,),
        )
        row = cursor.fetchone()
        if row:
            return UserInDB(**row)
        return None

def get_user_by_uuid(uuid_usuario: uuid.UUID) -> Optional[UserInDB]:
    """
    Recupera un usuario por su UUID.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE uuid_usuario = ?",
            (str(uuid_usuario),),
        )
        row = cursor.fetchone()
        if row:
            return UserInDB(**row)
        return None

def get_user_by_email(correo: str) -> Optional[UserInDB]:
    """
    Recupera un usuario por su correo electrónico.
    """
    with get_db_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE correo = ?",
            (correo,),
        )
        row = cursor.fetchone()
        if row:
            return UserInDB(**row)
        return None
