# main.py
from fastapi import FastAPI, HTTPException, status, Query, Path, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import List, Optional
import uuid
from datetime import datetime, timedelta, timezone

import crud
from models import (
    LecturaSensorCreate, LecturaSensor,
    ControladorCreate, Controlador,
    EnsayoCreate, Ensayo,
    UserCreate, User, UserInDB,
    ControladorUpdateName, ControladorUpdateEnsayo
)

# Para JWT
from jose import JWTError, jwt
import bcrypt

# Inicializa la aplicación FastAPI
app = FastAPI(
    title="API de Sensores de Humedad y Temperatura",
    description="API CRUD para registrar lecturas de 4 sensores de humedad y temperatura en una base de datos SQLite, optimizada para un VPS económico, con autenticación JWT.",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Coloca los origenes permitidos
origins = [
    "http://localhost:53528",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://secador-solar-gia.online",
    "https://www.secador-solar-gia.online",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuración de Autenticación JWT ---
SECRET_KEY = "tu-super-secreto-jwt-que-deberias-cambiar-en-produccion"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si una contraseña en texto plano coincide con una contraseña hasheada usando bcrypt."""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def get_password_hash(password: str) -> str:
    """Hashea una contraseña en texto plano usando bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un token de acceso JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def authenticate_user(nombre_usuario: str, password: str) -> Optional[UserInDB]:
    """Autentica un usuario por nombre de usuario y contraseña."""
    user = crud.get_user_by_username(nombre_usuario)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Dependencia para obtener el usuario actual a partir del token JWT.
    Lanza HTTPException si el token es inválido o el usuario no existe.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        user_uuid: str = payload.get("user_uuid")
        if user_uuid is None:
            raise credentials_exception
        
        user = crud.get_user_by_uuid(uuid.UUID(user_uuid))
        if user is None:
            raise credentials_exception
        return User(uuid_usuario=user.uuid_usuario, nombre_usuario=user.nombre_usuario, correo=user.correo)
    except JWTError:
        raise credentials_exception

# --- Endpoints de Autenticación ---

@app.post(
    "/api/register",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario"
)
async def register_user(user_create: UserCreate):
    """
    Registra un nuevo usuario en el sistema.
    """
    db_user = crud.get_user_by_username(user_create.nombre_usuario)
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El nombre de usuario ya existe.")
    
    db_user_by_email = crud.get_user_by_email(user_create.correo)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El correo electrónico ya está registrado.")

    hashed_password = get_password_hash(user_create.password)
    try:
        user = crud.create_user(user_create, hashed_password)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@app.post(
    "/api/token",
    summary="Obtener un token de acceso JWT para la autenticación"
)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Autentica un usuario y retorna un token de acceso JWT.
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nombre de usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.nombre_usuario, "user_uuid": str(user.uuid_usuario)},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# --- Endpoints para Lecturas de Sensores ---

@app.post(
    "/api/sensor/",
    response_model=LecturaSensor,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva lectura de sensor"
)
async def create_new_lectura_sensor_api(lectura: LecturaSensorCreate):
    """
    Registra una nueva lectura de un sensor específico.
    El ensayo asociado se determina automáticamente: si el controlador tiene un ensayo
    'Corriendo', se usa ese; de lo contrario, se asigna al ensayo genérico del controlador.
    """
    controlador = crud.get_controlador(lectura.uuid_controlador)
    if not controlador:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador no encontrado")

    ensayo_uuid_to_use = controlador.uuid_ensayo_activo

    if not ensayo_uuid_to_use:
        generic_ensayo = crud.get_controller_generic_ensayo(controlador.uuid_controlador)
        if generic_ensayo:
            ensayo_uuid_to_use = generic_ensayo.uuid_ensayo
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No se pudo determinar el ensayo activo o genérico para el controlador.")

    return crud.create_lectura_sensor(lectura, ensayo_uuid_to_use)


@app.get(
    "/api/sensor/",
    response_model=List[LecturaSensor],
    summary="Obtener todas las lecturas de sensores o filtrar por controlador, sensor o ensayo"
)
async def read_lecturas_sensor_api(
    uuid_controlador: Optional[uuid.UUID] = Query(None, description="UUID del controlador para filtrar lecturas."),
    id_sensor: Optional[int] = Query(None, ge=1, le=4, description="ID del sensor (1-4) para filtrar lecturas."),
    uuid_ensayo: Optional[uuid.UUID] = Query(None, description="UUID del ensayo para filtrar lecturas."),
    skip: int = Query(0, ge=0, description="Número de registros a saltar (paginación)."),
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros a devolver (paginación).")
):
    """
    Obtiene una lista de lecturas de sensores.
    """
    return crud.get_lecturas_sensor(uuid_controlador, id_sensor, uuid_ensayo, skip, limit)

@app.get(
    "/api/sensor/latest",
    response_model=Optional[LecturaSensor],
    summary="Obtener la última lectura de sensor registrada"
)
async def read_latest_lectura_sensor_api():
    """
    Obtiene la lectura de sensor más reciente de la base de datos.
    """
    return crud.get_latest_lectura_sensor()

# --- Endpoints para Controladores ---

@app.post(
    "/api/controller",
    summary="Registrar un nuevo controlador y su ensayo genérico único",
    dependencies=[Depends(get_current_user)]
)
async def create_new_controlador_api(controlador: ControladorCreate):
    """
    Registra un nuevo controlador y le asigna un ensayo genérico único.
    """
    created_controlador, generic_ensayo = crud.create_controlador(controlador)
    return {"controlador": created_controlador, "ensayo_generico": generic_ensayo}


@app.get(
    "/api/controller",
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
    "/api/controller/{uuid_controlador}",
    response_model=Controlador,
    summary="Obtener un controlador específico por su UUID"
)
async def read_controlador_api(uuid_controlador: uuid.UUID):
    """
    Obtiene los detalles de un controlador específico.
    """
    db_controlador = crud.get_controlador(uuid_controlador)
    if db_controlador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador no encontrado")
    return db_controlador

@app.put(
    "/api/controller/name-update/{uuid_controlador}",
    response_model=Controlador,
    summary="Actualizar el nombre de un controlador existente por su UUID",
    dependencies=[Depends(get_current_user)]
)
async def update_existing_controlador_name_api(uuid_controlador: uuid.UUID, new_name: ControladorUpdateName):
    """
    Actualiza el nombre de un controlador existente.
    """
    db_controlador = crud.update_controlador_name(uuid_controlador, new_name.nombre_controlador)
    if db_controlador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador no encontrado")
    return db_controlador

@app.put(
    "/api/controller/update-test/{uuid_controlador}",
    summary="Actualizar el ensayo activo de un controlador y los estados correspondientes",
    dependencies=[Depends(get_current_user)]
)
async def update_controller_ensayo_api(uuid_controlador: uuid.UUID, ensayo_data: ControladorUpdateEnsayo):
    """
    Actualiza el ensayo activo de un controlador, actualizando los estados del controlador y del ensayo.
    """
    controlador_actualizado, ensayo_actualizado = crud.update_controlador_ensayo(uuid_controlador, ensayo_data.uuid_ensayo_activo)
    if not controlador_actualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador o ensayo no encontrado")
    
    return {"controlador_actualizado": controlador_actualizado, "ensayo_actualizado": ensayo_actualizado}

@app.delete(
    "/api/controller/{uuid_controlador}",
    summary="Eliminar un controlador existente por su UUID",
    dependencies=[Depends(get_current_user)]
)
async def delete_existing_controlador_api(uuid_controlador: uuid.UUID):
    """
    Elimina un controlador existente. No se puede eliminar si su ensayo genérico tiene lecturas asociadas.
    """
    deleted_controlador = crud.delete_controlador(uuid_controlador)
    if deleted_controlador is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Controlador no encontrado o no se puede eliminar (podría tener lecturas asociadas a su ensayo genérico).")
    
    return {"message": "Controlador eliminado exitosamente", "deleted_entry": deleted_controlador}

# --- Endpoints para Ensayos ---

@app.post(
    "/api/ensayos/",
    response_model=Ensayo,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo ensayo",
    dependencies=[Depends(get_current_user)]
)
async def create_new_ensayo_api(ensayo: EnsayoCreate):
    """
    Registra un nuevo ensayo.
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
    """
    return crud.get_ensayos(uuid_controlador, skip, limit)

@app.get(
    "/api/ensayos/{uuid_ensayo}",
    response_model=Ensayo,
    summary="Obtener un ensayo específico por su UUID"
)
async def read_ensayo_api(uuid_ensayo: uuid.UUID):
    """
    Obtiene los detalles de un ensayo específico.
    """
    db_ensayo = crud.get_ensayo(uuid_ensayo)
    if db_ensayo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ensayo no encontrado")
    return db_ensayo

@app.put(
    "/api/ensayos/{uuid_ensayo}",
    response_model=Ensayo,
    summary="Actualizar un ensayo existente por su UUID",
    dependencies=[Depends(get_current_user)]
)
async def update_existing_ensayo_api(uuid_ensayo: uuid.UUID, ensayo: EnsayoCreate):
    """
    Actualiza un ensayo existente.
    """
    db_ensayo = crud.update_ensayo(uuid_ensayo, ensayo)
    if db_ensayo is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ensayo no encontrado")
    return db_ensayo

@app.delete(
    "/api/ensayos/{uuid_ensayo}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar un ensayo existente por su UUID",
    dependencies=[Depends(get_current_user)]
)
async def delete_existing_ensayo_api(uuid_ensayo: uuid.UUID):
    """
    Elimina un ensayo existente. No se permite eliminar si es un ensayo genérico de algún controlador.
    """
    if not crud.delete_ensayo(uuid_ensayo):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ensayo no encontrado o no se puede eliminar (es un ensayo genérico de un controlador).")
    return {"message": "Ensayo eliminado exitosamente"}
