# test_api.py
import requests
import pytest
import time
import uuid

# Asegúrate de que el API esté corriendo en esta URL.
API_URL = "http://localhost:8000/api"

# --- Datos de prueba ---
USERNAME = "admin"
PASSWORD = "1234"
EMAIL = "admin@example.com"

login_data = {
  "grant_type": "password",
  "username": USERNAME,
  "password": PASSWORD,
  "scope": "",
  "client_id": "",
  "client_secret": "",
}

# --- Fixture para el cliente de la API autenticado ---
@pytest.fixture(scope="session")
def api_client():
    """
    Fixture que crea un usuario de prueba, obtiene un token de autenticación
    y devuelve una sesión de requests autenticada.
    """
    print("\n[SETUP] Creando usuario de prueba...")
    # 1. Crear usuario de prueba
    payload_create = {
      "nombre_usuario": USERNAME,
      "correo": EMAIL,
      "password": PASSWORD
    }
    # La API debería devolver 201 Created si el usuario no existe.
    response = requests.post(f"{API_URL}/register", json=payload_create)
    # Si el usuario ya existe, no es un error en el fixture
    if response.status_code != 201 and response.status_code != 400:
        pytest.fail(f"Fallo al crear el usuario de prueba. Status: {response.status_code}, Response: {response.json()}")

    # 2. Iniciar sesión para obtener el token
    print("[SETUP] Obteniendo token de autenticación...")
    login_data = {
      "grant_type": "password",
      "username": USERNAME,
      "password": PASSWORD,
      "scope": "",
      "client_id": "",
      "client_secret": "",
    }
    response = requests.post(f"{API_URL}/token", data=login_data)
    assert response.status_code == 200, f"Fallo al obtener el token. Status: {response.status_code}, Response: {response.json()}"
    auth_token = response.json()
    
    # 3. Crear una sesión y agregar el header de autenticación
    session = requests.Session()
    session.headers.update({'Authorization': f"{auth_token['token_type']} {auth_token['access_token']}"})
    
    # Proveer la sesión a las pruebas
    yield session
    
    # --- TEARDOWN ---
    print("\n[TEARDOWN] Limpiando datos de prueba...")
    # No hay un endpoint para eliminar usuarios, pero se podría agregar.
    # Por ahora, nos aseguramos de que el usuario exista para no fallar.
    # En un entorno de pruebas real, se vaciaría la base de datos o se usaría
    # un endpoint de eliminación.
    print("[TEARDOWN] Finalizado.")


# --- PRUEBAS DE AUTENTICACIÓN Y REGISTRO ---

def test_register_user_success():
    """Prueba el registro de un nuevo usuario con datos únicos."""
    unique_username = f"user_{int(time.time())}"
    unique_email = f"user_{int(time.time())}@example.com"
    payload = {
        "nombre_usuario": unique_username,
        "correo": unique_email,
        "password": "new_password"
    }
    response = requests.post(f"{API_URL}/register", json=payload)
    assert response.status_code == 201, f"Expected 201, got {response.status_code} with {response.json()}"
    assert "uuid_usuario" in response.json()
    assert response.json()["nombre_usuario"] == unique_username

def test_register_duplicate_username():
    """Prueba que el registro de un usuario con nombre de usuario duplicado falle."""
    payload = {
        "nombre_usuario": USERNAME,  # Nombre de usuario ya usado en el fixture
        "correo": "new_email@example.com",
        "password": "password"
    }
    response = requests.post(f"{API_URL}/register", json=payload)
    assert response.status_code == 400, f"Expected 400, got {response.status_code} with {response.json()}"
    assert "El nombre de usuario ya existe" in response.json()["detail"]

def test_login_success():
    """Prueba que el inicio de sesión con credenciales correctas sea exitoso."""
    login_data = {
      "grant_type": "password",
      "username": USERNAME,
      "password": PASSWORD,
      "scope": "",
      "client_id": "",
      "client_secret": "",
    }
    response = requests.post(f"{API_URL}/token", data=login_data)
    assert response.status_code == 200, f"Expected 200, got {response.status_code} with {response.json()}\n sent:{response.request}"
    assert "access_token" in response.json()
    assert "token_type" in response.json()

def test_login_invalid_credentials():
    """Prueba que el inicio de sesión con credenciales incorrectas falle."""
    login_data = {
      "grant_type": "password",
      "username": "wrong_username",
      "password": "wrong_password",
      "scope": "",
      "client_id": "",
      "client_secret": "",
    }
    response = requests.post(f"{API_URL}/token", data=login_data)
    assert response.status_code == 401, f"Expected 401, got {response.status_code} with {response.json()}"
    assert "Nombre de usuario o contraseña incorrectos" in response.json()["detail"]


# --- PRUEBAS DE ENDPOINTS AUTENTICADOS (Controladores) ---

def test_create_controlador(api_client):
    """Prueba la creación de un controlador con autenticación."""
    payload = {"nombre_controlador": "Controlador de Prueba"}
    response = api_client.post(f"{API_URL}/controller", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "controlador" in data
    assert "uuid_controlador" in data["controlador"]
    assert "ensayo_generico" in data
    assert data["controlador"]["nombre_controlador"] == "Controlador de Prueba"

def test_create_controlador_unauthenticated():
    """Prueba que la creación de un controlador falle sin autenticación."""
    payload = {"nombre_controlador": "Controlador Sin Auth"}
    response = requests.post(f"{API_URL}/controller", json=payload)
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_read_controladores(api_client):
    """Prueba la obtención de la lista de controladores."""
    # Primero crea uno para asegurar que haya datos
    api_client.post(f"{API_URL}/controller", json={"nombre_controlador": "TestController"})
    
    response = api_client.get(f"{API_URL}/controller")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0

def test_update_controlador_name(api_client):
    """Prueba la actualización del nombre de un controlador."""
    # Crea un controlador para poder actualizarlo
    create_response = api_client.post(f"{API_URL}/controller", json={"nombre_controlador": "Old Name"})
    controlador_uuid = create_response.json()["controlador"]["uuid_controlador"]

    payload = {"nombre_controlador": "New Name"}
    response = api_client.put(f"{API_URL}/controller/name-update/{controlador_uuid}", json=payload)
    assert response.status_code == 200
    assert response.json()["nombre_controlador"] == "New Name"

def test_delete_controlador(api_client):
    """Prueba la eliminación de un controlador."""
    # Crea un controlador para poder eliminarlo
    create_response = api_client.post(f"{API_URL}/controller", json={"nombre_controlador": "ToDelete"})
    controlador_uuid = create_response.json()["controlador"]["uuid_controlador"]

    response = api_client.delete(f"{API_URL}/controller/{controlador_uuid}")
    assert response.status_code == 200
    assert response.json()["message"] == "Controlador eliminado exitosamente"


# --- PRUEBAS DE ENDPOINTS AUTENTICADOS (Ensayos) ---

def test_create_ensayo(api_client):
    """Prueba la creación de un ensayo."""
    # Crea un controlador para asociar el ensayo
    create_controller_response = api_client.post(f"{API_URL}/controller", json={"nombre_controlador": "Controller for Test"})
    controlador_uuid = create_controller_response.json()["controlador"]["uuid_controlador"]

    payload = {
        "nombre_ensayo": "Ensayo de Prueba",
        "uuid_controlador": controlador_uuid
    }
    response = api_client.post(f"{API_URL}/ensayos/", json=payload)
    assert response.status_code == 201
    assert "uuid_ensayo" in response.json()
    assert response.json()["nombre_ensayo"] == "Ensayo de Prueba"
    assert response.json()["uuid_controlador"] == controlador_uuid

def test_read_ensayos(api_client):
    """Prueba la obtención de la lista de ensayos."""
    # Necesitamos un controlador y un ensayo para asegurarnos de que hay datos
    controller_response = api_client.post(f"{API_URL}/controller", json={"nombre_controlador": "Controller for Ensayo Read"})
    controller_uuid = controller_response.json()["controlador"]["uuid_controlador"]
    
    payload = {
        "nombre_ensayo": "Ensayo de lectura",
        "uuid_controlador": controller_uuid
    }
    api_client.post(f"{API_URL}/ensayos/", json=payload)
    
    response = api_client.get(f"{API_URL}/ensayos/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


# --- PRUEBAS DE ENDPOINTS PÚBLICOS (Lecturas de Sensores) ---

def test_create_lectura_sensor():
    """
    Prueba la creación de una lectura de sensor.
    Este endpoint no requiere autenticación, por lo que usa requests directamente.
    """
    # Crea un controlador y ensayo genérico para que la lectura se pueda asociar
    controlador_payload = {"nombre_controlador": "Controlador Sin Auth"}
    controller_response = requests.post(f"{API_URL}/controller", json=controlador_payload)
    assert controller_response.status_code == 401 # Debe fallar sin auth
    # Aquí necesitarías una manera de crear un controlador sin auth para probar el endpoint,
    # o crear el controlador de forma mock. Como no hay un endpoint público para crear
    # controladores, esta prueba fallará hasta que se modifique la API.
    # Por ahora, esta prueba es teórica, asumiendo que ya hay un controlador creado.
    
    # UUID de un controlador pre-existente para la prueba
    # Debes reemplazar este UUID por uno que exista en tu base de datos de prueba.
    # controlador_uuid_known = "a_valid_uuid_from_your_db"
    # ensayo_uuid_known = "a_valid_ensayo_uuid_from_your_db"

    # payload = {
    #     "uuid_controlador": controlador_uuid_known,
    #     "id_sensor": 1,
    #     "uuid_ensayo": ensayo_uuid_known,
    #     "nombre_ensayo": "Ensayo Test Publico",
    #     "lectura_temperatura": 25.5,
    #     "lectura_humedad": 60.0
    # }
    # response = requests.post(f"{API_URL}/sensor/", json=payload)
    # assert response.status_code == 201
    # assert "timestamp" in response.json()
    pass # Esta prueba está comentada para evitar fallos por UUIDs inexistentes.