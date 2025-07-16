# models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

# --- Modelos para Lecturas de Sensores ---

class LecturaSensorBase(BaseModel):
    """
    Modelo base para una lectura de sensor, define los campos comunes.
    """
    uuid_controlador: uuid.UUID
    # id_sensor debe ser un entero entre 1 y 4
    id_sensor: int = Field(..., ge=1, le=4, description="ID del sensor (1 a 4)")
    uuid_ensayo: uuid.UUID # Ahora el ensayo es parte de la lectura
    nombre_ensayo: str     # Y su nombre
    lectura_temperatura: float
    lectura_humedad: float

class LecturaSensorCreate(LecturaSensorBase):
    """
    Modelo para la creación de una nueva lectura de sensor (POST request).
    Hereda de LecturaSensorBase, no necesita campos adicionales para la creación
    ya que el timestamp se genera en el backend.
    """
    pass

class LecturaSensor(LecturaSensorBase):
    """
    Modelo completo para una lectura de sensor, incluyendo el timestamp.
    Se usa para las respuestas de la API (GET requests).
    """
    timestamp: datetime # El timestamp se añade cuando se recupera de la DB

    class Config:
        # Permite que Pydantic cree instancias del modelo a partir de atributos de objeto
        # (ej. de filas de SQLite que se comportan como diccionarios).
        from_attributes = True

# --- Modelos para Controladores ---

class ControladorBase(BaseModel):
    """
    Modelo base para un controlador.
    """
    nombre_controlador: str

class ControladorCreate(ControladorBase):
    """
    Modelo para la creación de un nuevo controlador (POST request).
    """
    pass

class Controlador(ControladorBase):
    """
    Modelo completo para un controlador, incluyendo su UUID y timestamp de registro.
    Se usa para las respuestas de la API.
    """
    uuid_controlador: uuid.UUID
    timestamp_registro: datetime

    class Config:
        from_attributes = True

# --- Nuevos Modelos para Ensayos ---

class EnsayoBase(BaseModel):
    """
    Modelo base para un ensayo.
    """
    nombre_ensayo: str
    uuid_controlador: uuid.UUID # Nuevo: Ensayo asociado a un controlador

class EnsayoCreate(EnsayoBase):
    """
    Modelo para la creación de un nuevo ensayo.
    """
    pass

class Ensayo(EnsayoBase):
    """
    Modelo completo para un ensayo, incluyendo su UUID y timestamp de registro.
    """
    uuid_ensayo: uuid.UUID
    timestamp_registro: datetime

    class Config:
        from_attributes = True
