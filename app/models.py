# models.py
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
import uuid
from enum import Enum

# --- Enums para estados ---

class EstadoControlador(str, Enum):
    """
    Estados posibles para un controlador.
    """
    inactivo = "Inactivo"      # Se coloca solo cuando se lleva varios dias sin recibir peticiones del controlador
    activo = "Activo"          # Se encuentra activo con el ensayo default tomando datos
    en_ensayo = "En ensayo"    # Actualmente tiene un ensayo corriendo diferente al default

class EstadoEnsayo(str, Enum):
    """
    Estados posibles para un ensayo.
    """
    default = "Default"        # Se asigna unicamente al ensayo por defecto de un controlador
    parado = "Parado"          # Se manda una señal para el ensayo confirmando el estado de parada, se asigna por defecto al controlador dueño de este ensayo el ensayo generico
    corriendo = "Corriendo"    # Se quita del ensayo activo del controlador dueño el ensayo por defecto y se asigna el estado con la etiqueta corriendo
    finalizado = "Finalizado"  # No permite tomar más datos una vez se coloca este estado

# --- Modelos para Controladores ---

class ControladorBase(BaseModel):
    """
    Modelo base para un controlador.
    """
    nombre_controlador: str = Field(..., description="Nombre para identificar el controlador")
    estado: EstadoControlador = Field(EstadoControlador.inactivo, description="Estado actual del controlador")
    bateria: Optional[float] = Field(None, description="Voltaje de la batería del último valor reportado")
    uuid_ensayo_activo: Optional[uuid.UUID] = Field(None, description="Llave foránea de un ensayo activo")

class ControladorCreate(ControladorBase):
    """
    Modelo para la creación de un nuevo controlador (POST request).
    """
    pass

class ControladorUpdateName(BaseModel):
    """
    Modelo para actualizar el nombre de un controlador.
    """
    nombre_controlador: str

class ControladorUpdateEnsayo(BaseModel):
    """
    Modelo para actualizar el ensayo activo de un controlador.
    """
    uuid_ensayo_activo: uuid.UUID

class Controlador(ControladorBase):
    """
    Modelo completo para un controlador, incluyendo sus UUIDs y timestamp de registro.
    Se usa para las respuestas de la API.
    """
    uuid_controlador: uuid.UUID = Field(..., description="Llave primaria única por cada controlador")
    uuid_ensayo_generico: uuid.UUID = Field(..., description="Llave foránea de un ensayo genérico asignado")
    timestamp_registro: datetime = Field(..., description="Fecha y hora de creación formateada en ISO8601 para el huso horario de Colombia UTC-5")

    model_config = ConfigDict(from_attributes=True)

# --- Modelos para Ensayos ---

class EnsayoBase(BaseModel):
    """
    Modelo base para un ensayo.
    """
    nombre_ensayo: str = Field(..., description="Nombre para identificar el ensayo")
    uuid_controlador: Optional[uuid.UUID] = Field(None, description="Llave foránea del controlador al que pertenece este ensayo")
    estado: EstadoEnsayo = Field(EstadoEnsayo.parado, description="Estado actual del ensayo")

class EnsayoCreate(EnsayoBase):
    """
    Modelo para la creación de un nuevo ensayo.
    """
    pass

class Ensayo(EnsayoBase):
    """
    Modelo completo para un ensayo, incluyendo su UUID y timestamp de registro.
    """
    uuid_ensayo: uuid.UUID = Field(..., description="Llave primaria única por cada ensayo")
    timestamp_registro: datetime = Field(..., description="Fecha de creación formateada en ISO8601 huso horario de Colombia UTC-5")

    model_config = ConfigDict(from_attributes=True)

# --- Modelos para Lecturas de Sensores ---

class LecturaSensorBase(BaseModel):
    """
    Modelo base para una lectura de sensor.
    """
    uuid_controlador: uuid.UUID = Field(..., description="Llave foránea del controlador desde el cual se realizó la lectura")
    id_sensor: int = Field(..., ge=1, le=4, description="Número del 1-4 para identificar el sensor")
    lectura_temperatura: float = Field(..., description="Lectura de temperatura en °C")
    lectura_humedad: float = Field(..., description="Porcentaje de humedad relativa del aire")
    lectura_bateria: Optional[float] = Field(None, description="Voltaje de batería reportado")

class LecturaSensorCreate(LecturaSensorBase):
    """
    Modelo para la creación de una nueva lectura de sensor (POST request).
    """
    pass

class LecturaSensor(LecturaSensorBase):
    """
    Modelo completo para una lectura de sensor, incluyendo su UUID y timestamp.
    """
    uuid_lectura: uuid.UUID = Field(..., description="Llave primaria única para identificar la lectura")
    uuid_ensayo: Optional[uuid.UUID] = Field(None, description="Llave foránea del ensayo asociado a esta lectura")
    timestamp: datetime = Field(..., description="Fecha y hora de la medición en formato ISO8601 huso horario de Colombia UTC-5")

    model_config = ConfigDict(from_attributes=True)

# --- Modelos para Usuarios (Autenticación) ---

class UserBase(BaseModel):
    """
    Modelo base para un usuario.
    """
    nombre_usuario: str
    correo: str

class UserCreate(UserBase):
    """
    Modelo para la creación de un nuevo usuario.
    """
    password: str

class User(UserBase):
    """
    Modelo completo para un usuario, incluyendo su UUID.
    """
    uuid_usuario: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class UserInDB(User):
    """
    Modelo para un usuario como se almacena en la base de datos (incluye el hash de la contraseña).
    """
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)
