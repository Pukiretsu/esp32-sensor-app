# main.py
from fastapi import FastAPI, HTTPException, status, Query, Path, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from typing import List, Optional
import uuid
from datetime import datetime

import crud
from models import LecturaSensorCreate, LecturaSensor, ControladorCreate, Controlador, EnsayoCreate, Ensayo # Importa EnsayoCreate, Ensayo

# Inicializa la aplicación FastAPI
# Se han actualizado docs_url y redoc_url para que la documentación esté bajo /api/
app = FastAPI(
    title="API de Sensores de Humedad y Temperatura",
    description="API CRUD para registrar lecturas de 4 sensores de humedad y temperatura en una base de datos SQLite, optimizada para un VPS económico.",
    version="1.0.0",
    docs_url="/api/docs",    # Nueva URL para Swagger UI
    redoc_url="/api/redoc"   # Nueva URL para ReDoc
)

# Configura Jinja2 para las plantillas HTML
templates = Jinja2Templates(directory="templates")

# Monta el directorio 'static' para servir archivos CSS, JS, imágenes, etc.
# Los archivos en 'static' serán accesibles en la URL /static/
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- Rutas para servir las Vistas del Frontend ---

@app.get("/", response_class=HTMLResponse, summary="Servir la página de Inicio")
async def get_inicio_page(request: Request):
    """
    Ruta principal que renderiza el archivo `inicio.html`.
    """
    return templates.TemplateResponse("inicio.html", {"request": request})

@app.get("/datos", response_class=HTMLResponse, summary="Servir la página de Datos de Sensores")
async def get_datos_page(request: Request):
    """
    Ruta para la página de datos de sensores, que lista controladores y sus lecturas.
    """
    # Aquí podríamos cargar datos iniciales si fuera necesario, pero el JS se encargará.
    return templates.TemplateResponse("datos.html", {"request": request})

@app.get("/logs", response_class=HTMLResponse, summary="Servir la página de Logs (Por Implementar)")
async def get_logs_page(request: Request):
    """
    Ruta para la página de logs del sistema (actualmente un marcador de posición).
    """
    return templates.TemplateResponse("logs.html", {"request": request})

@app.get("/acerca", response_class=HTMLResponse, summary="Servir la página 'Acerca de'")
async def get_acerca_page(request: Request):
    """
    Ruta para la página 'Acerca de', con información del equipo y tecnologías.
    """
    return templates.TemplateResponse("acerca.html", {"request": request})


# --- Endpoints de la API (Todas inician con /api/) ---

# Dependencia para validar el formato del timestamp en las rutas
# Se mantiene para la documentación, pero la validación se hace en cada endpoint.
def validate_timestamp_path(timestamp: str = Path(..., description="Timestamp ISO 8601 en la zona horaria de Colombia.")) -> str:
    try:
        datetime.fromisoformat(timestamp)
        return timestamp
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de timestamp inválido. Debe ser ISO 8601 (ej. '2023-10-27T10:30:00.123456-05:00').")


@app.post(
    "/api/sensor/",
    response_model=LecturaSensor,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva lectura de sensor"
)
async def create_new_lectura_sensor(lectura: LecturaSensorCreate):
    """
    Registra una nueva lectura de un sensor específico.
    El `timestamp` se genera automáticamente en el backend en la zona horaria de Colombia.
    """
    return crud.create_lectura_sensor(lectura)

@app.get(
    "/api/sensor/",
    response_model=List[LecturaSensor],
    summary="Obtener todas las lecturas de sensores o filtrar por controlador, sensor o ensayo"
)
async def read_lecturas_sensor(
    uuid_controlador: Optional[uuid.UUID] = Query(None, description="UUID del controlador para filtrar lecturas."),
    id_sensor: Optional[int] = Query(None, ge=1, le=4, description="ID del sensor (1-4) para filtrar lecturas."),
    uuid_ensayo: Optional[uuid.UUID] = Query(None, description="UUID del ensayo para filtrar lecturas."),
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)."),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver (paginación).")
):
    """
    Obtiene una lista de lecturas de sensores.
    Permite filtrar por `uuid_controlador`, `id_sensor` y `uuid_ensayo`.
    """
    lecturas = crud.get_lecturas_sensor(uuid_controlador, id_sensor, uuid_ensayo, skip, limit)
    return lecturas

@app.get(
    "/api/sensor/latest",
    response_model=Optional[LecturaSensor],
    summary="Obtener la última lectura de sensor registrada"
)
async def read_latest_lectura_sensor():
    """
    Obtiene la lectura de sensor más reciente de la base de datos.
    Retorna None si no hay lecturas.
    """
    return crud.get_latest_lectura_sensor()

@app.get(
    "/api/sensor/{timestamp}/{uuid_controlador}/{id_sensor}",
    response_model=LecturaSensor,
    summary="Obtener una lectura de sensor específica por su clave primaria"
)
async def get_lectura_sensor_by_pk_api(
    timestamp: str = Path(..., description="Timestamp ISO 8601 en la zona horaria de Colombia."),
    uuid_controlador: uuid.UUID = Path(..., description="UUID único del controlador."),
    id_sensor: int = Path(..., ge=1, le=4, description="ID único del sensor (1 a 4).")
):
    """
    Obtiene una única lectura de sensor utilizando su `timestamp`, `uuid_controlador` e `id_sensor`.
    """
    # La validación del timestamp se realiza en la dependencia validate_timestamp_path
    db_lectura = crud.get_lectura_sensor_by_pk(timestamp, uuid_controlador, id_sensor)
    if db_lectura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lectura de sensor no encontrada")
    return db_lectura

@app.delete(
    "/api/sensor/{timestamp}/{uuid_controlador}/{id_sensor}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar una lectura de sensor específica por su clave primaria"
)
async def delete_existing_lectura_sensor_api(
    timestamp: str = Path(..., description="Timestamp ISO 8601 en la zona horaria de Colombia."),
    uuid_controlador: uuid.UUID = Path(..., description="UUID único del controlador."),
    id_sensor: int = Path(..., ge=1, le=4, description="ID único del sensor (1 a 4).")
):
    """
    Elimina una lectura de sensor específica utilizando su `timestamp`, `uuid_controlador` e `id_sensor`.
    """
    # La validación del timestamp se realiza en la dependencia validate_timestamp_path
    if not crud.delete_lectura_sensor(timestamp, uuid_controlador, id_sensor):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lectura de sensor no encontrada")
    return {"message": "Lectura eliminada exitosamente"}

# --- Endpoints para Controladores (Todas inician con /api/) ---

@app.post(
    "/api/controladores/",
    response_model=Controlador,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo controlador"
)
async def create_new_controlador_api(controlador: ControladorCreate):
    """
    Registra un nuevo controlador. Se generará un `uuid_controlador` único
    y el `timestamp_registro` se establecerá en la zona horaria de Colombia.
    """
    return crud.create_controlador(controlador)

@app.get(
    "/api/controladores/",
    response_model=List[Controlador],
    summary="Obtener todos los controladores registrados"
)
async def read_controladores_api(
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)."),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver (paginación).")
):
    """
    Obtiene una lista de todos los controladores registrados.
    """
    return crud.get_controladores(skip, limit)

@app.get(
    "/api/controladores/{uuid_controlador}",
    response_model=Controlador,
    summary="Obtener un controlador específico por su UUID"
)
async def read_controlador_api(uuid_controlador: uuid.UUID):
    """
    Obtiene los detalles de un controlador específico usando su `uuid_controlador`.
    """
    db_controlador = crud.get_controlador(uuid_controlador)
    if db_controlador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador no encontrado")
    return db_controlador

@app.put(
    "/api/controladores/{uuid_controlador}",
    response_model=Controlador,
    summary="Actualizar un controlador existente por su UUID"
)
async def update_existing_controlador_api(uuid_controlador: uuid.UUID, controlador: ControladorCreate):
    """
    Actualiza el nombre de un controlador existente utilizando su `uuid_controlador`.
    """
    db_controlador = crud.update_controlador(uuid_controlador, controlador)
    if db_controlador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador no encontrado")
    return db_controlador

@app.delete(
    "/api/controladores/{uuid_controlador}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un controlador existente por su UUID"
)
async def delete_existing_controlador_api(uuid_controlador: uuid.UUID):
    """
    Elimina un controlador existente utilizando su `uuid_controlador`.
    """
    if not crud.delete_controlador(uuid_controlador):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador no encontrado")
    return {"message": "Controlador eliminado exitosamente"}

# --- Nuevos Endpoints para Ensayos (Todas inician con /api/) ---

@app.post(
    "/api/ensayos/",
    response_model=Ensayo,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo ensayo"
)
async def create_new_ensayo_api(ensayo: EnsayoCreate):
    """
    Registra un nuevo ensayo. Se generará un `uuid_ensayo` único
    y el `timestamp_registro` se establecerá en la zona horaria de Colombia.
    """
    return crud.create_ensayo(ensayo)

@app.get(
    "/api/ensayos/",
    response_model=List[Ensayo],
    summary="Obtener todos los ensayos registrados (filtrar por controlador opcional)"
)
async def read_ensayos_api(
    uuid_controlador: Optional[uuid.UUID] = Query(None, description="UUID del controlador para filtrar ensayos."),
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)."),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver (paginación).")
):
    """
    Obtiene una lista de todos los ensayos registrados.
    Permite filtrar por `uuid_controlador`.
    """
    return crud.get_ensayos(uuid_controlador, skip, limit)

@app.get(
    "/api/ensayos/{uuid_ensayo}",
    response_model=Ensayo,
    summary="Obtener un ensayo específico por su UUID"
)
async def read_ensayo_api(uuid_ensayo: uuid.UUID):
    """
    Obtiene los detalles de un ensayo específico usando su `uuid_ensayo`.
    """
    db_ensayo = crud.get_ensayo(uuid_ensayo)
    if db_ensayo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ensayo no encontrado")
    return db_ensayo

@app.delete(
    "/api/ensayos/{uuid_ensayo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un ensayo existente por su UUID"
)
async def delete_existing_ensayo_api(uuid_ensayo: uuid.UUID):
    """
    Elimina un ensayo existente utilizando su `uuid_ensayo`.
    """
    if not crud.delete_ensayo(uuid_ensayo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ensayo no encontrado")
    return {"message": "Ensayo eliminado exitosamente"}
