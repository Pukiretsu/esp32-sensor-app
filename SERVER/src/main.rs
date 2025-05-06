use chrono::{NaiveDate, NaiveTime};
use postgres::Error as PostgresError;
use postgres::{Client, NoTls};
use std::env;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};

#[macro_use]
extern crate serde_derive;

// Creación del modelo, con el ID, titulo y contenido
#[derive(Serialize, Deserialize)]
struct Sensor {
    id: Option<i32>,
    tipo: i32,
    temperatura: f32,
    humedad: f32,
    fecha: Option<NaiveDate>,
    hora: Option<NaiveTime>,
}

#[derive(Serialize, Deserialize)]
struct Log {
    id: Option<i32>,
    tag: String,
    evento: String,
    fecha: Option<NaiveDate>,
    hora: Option<NaiveTime>,
}

#[derive(Serialize, Deserialize)]
struct Status {
    id: Option<i32>,
    stat: String,
    battery: i32,
}

// Create the database's URL.

//const DB_URL: &str = "postgres://admin:HATmik211@db:5432/sensor_log_db";
const DB_URL: &str = env!("DATABASE_URL");

// functions for building HTTP responses

/// Respuesta 200 OK estándar con JSON y CORS
fn build_ok_response(body: &str) -> String {
    format!(
        "HTTP/1.1 200 OK\r\n\
         Access-Control-Allow-Origin: *\r\n\
         Content-Type: application/json\r\n\
         Content-Length: {}\r\n\
         \r\n\
         {}",
        body.len(),
        body
    )
}

/// Respuesta para peticiones OPTIONS (CORS preflight)
fn build_cors_ok_response() -> String {
    format!(
        "HTTP/1.1 200 OK\r\n\
         Access-Control-Allow-Origin: *\r\n\
         Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS\r\n\
         Access-Control-Allow-Headers: Content-Type\r\n\
         Content-Length: 0\r\n\
         \r\n"
    )
}

/// Respuesta 404 Not Found
fn build_not_found_response(body: &str) -> String {
    format!(
        "HTTP/1.1 404 Not Found\r\n\
         Content-Type: text/plain\r\n\
         Content-Length: {}\r\n\
         \r\n\
         {}",
        body.len(),
        body
    )
}

/// Respuesta 500 Internal Server Error
fn build_internal_error_response(message: &str) -> String {
    format!(
        "HTTP/1.1 500 Internal Server Error\r\n\
         Content-Type: text/plain\r\n\
         Content-Length: {}\r\n\
         \r\n\
         {}",
        message.len(),
        message
    )
}

/* /// Respuesta 401 Unauthorized con cabecera WWW-Authenticate
fn build_unauthorized_response() -> String {
    let body = "401 Unauthorized";
    format!(
        "HTTP/1.1 401 Unauthorized\r\n\
         WWW-Authenticate: Basic realm=\"Restricted Area\"\r\n\
         Content-Length: {}\r\n\
         \r\n\
         {}",
        body.len(),
        body
    )
} */

/// Respuesta 400 Bad Request
fn build_bad_request_response(message: &str) -> String {
    format!(
        "HTTP/1.1 400 Bad Request\r\n\
         Content-Type: text/plain\r\n\
         Content-Length: {}\r\n\
         \r\n\
         {}",
        message.len(),
        message
    )
}

/* const OK_RESPONSE: &str = "HTTP/1.1 200 OK\r\n\
                           Access-Control-Allow-Origin: *\r\n\
                           Content-Type: application/json\r\n\r\n";

const OK_RESPONSE_CORS: &str = "HTTP/1.1 200 OK\r\n\
                       Access-Control-Allow-Origin: *\r\n\
                       Access-Control-Allow-Methods: GET, OPTIONS\r\n\
                       Access-Control-Allow-Headers: Content-Type\r\n\r\n";

const NOT_FOUND: &str = "HTTP/1.1 404 NOT FOUND\r\n\r\n";

const INTERNAL_SERVER_ERROR: &str = "HTTP/1.1 500 INTERNAL SERVER ERROR\r\n\r\n";

const UNAUTHORIZED_ERROR: &str =
    "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Restricted Area\"\r\n\r\n";

    const BAD_REQUEST: &str = "HTTP/1.1 400 Bad Request\r\n\r\n"; */
// Main function

fn main() {
    // set database
    if let Err(e) = set_database() {
        println!("Error: {}", e);
        return;
    }

    // Start the server and print the port
    let listener = TcpListener::bind(format!("0.0.0.0:8080")).unwrap();
    println!("El server se inicio en el puerto 8080");

    // handle the client
    for stream in listener.incoming() {
        match stream {
            Ok(stream) => {
                handle_client(stream);
            }
            Err(e) => {
                println!("Error: {}", e)
            }
        }
    }
}

// handle_client function

fn handle_client(mut stream: TcpStream) {
    let mut buffer = [0; 4096];
    let mut request = String::new();

    match stream.read(&mut buffer) {
        Ok(size) if size > 0 => {
            request.push_str(String::from_utf8_lossy(&buffer[..size]).as_ref());
            println!("Petición recibida:\n{}", request);

            let response = route_request(&request);

            if let Err(e) = stream.write_all(response.as_bytes()) {
                eprintln!("Error al enviar la respuesta: {}", e);
            }
        }
        Ok(_) => {
            eprintln!("Cliente cerró la conexión sin enviar datos.");
        }
        Err(e) => {
            eprintln!("Error al leer del stream: {}", e);
        }
    }
}

fn route_request(request: &str) -> String {
    match request {
        // Sensor routes
        r if r.starts_with("POST /sensor") => handle_post_sensor_request(r),
        r if r.starts_with("GET /sensor/") => handle_get_sensor_request(r),
        r if r.starts_with("GET /sensor") => handle_get_all_sensor_request(),
        r if r.starts_with("PUT /sensor/") => handle_put_sensor_request(r),
        r if r.starts_with("DELETE /sensor/") => handle_delete_sensor_request(r),

        // Log routes
        r if r.starts_with("POST /log") => handle_post_log_request(r),
        r if r.starts_with("GET /log/") => handle_get_log_request(r),
        r if r.starts_with("GET /log") => handle_get_all_log_request(),
        r if r.starts_with("PUT /log/") => handle_put_log_request(r),
        r if r.starts_with("DELETE /log/") => handle_delete_log_request(r),

        // Status routes
        r if r.starts_with("POST /status") => handle_post_status_request(r),
        r if r.starts_with("GET /status/") => handle_get_status_request(r),
        r if r.starts_with("PUT /status/") => handle_put_status_request(r),
        r if r.starts_with("DELETE /status/") => handle_delete_status_request(r),

        // CORS preflight
        r if r.starts_with("OPTIONS") => build_cors_ok_response(),

        // Default 404
        _ => build_not_found_response("404 Endpoint not found"),
    }
}

// ------------ Controllers -----------------------------------------------------------------------------------------------------------------------------

//handle_post_request functions -----------------------------------------------------------------------------------------------------------------

fn handle_post_sensor_request(request: &str) -> String {
    match (
        get_sensor_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(dht11), Ok(mut client)) => {
            client
                .execute(
                    "INSERT INTO dht11_data (tipo, temperatura, humedad) VALUES ($1, $2, $3)",
                    &[&dht11.tipo, &dht11.temperatura, &dht11.humedad],
                )
                .unwrap();

            build_ok_response("Entrada del sensor creada con exito")
        }
        (Err(_dht11_entry), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error no se creo la entrada del sensor"),
    }
}

fn handle_post_sensors_request(request: &str) -> String {
    match (
        get_sensor_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(dht11), Ok(mut client)) => {
            client
                .execute(
                    "INSERT INTO dht11_data (tipo, temperatura, humedad) VALUES ($1, $2, $3)",
                    &[&dht11.tipo, &dht11.temperatura, &dht11.humedad],
                )
                .unwrap();

            build_ok_response("Entrada del sensor creada con exito")
        }
        (Err(_dht11_entry), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error no se creo la entrada del sensor"),
    }
}

fn handle_post_log_request(request: &str) -> String {
    match (
        get_log_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(log_entry), Ok(mut client)) => {
            client
                .execute(
                    "INSERT INTO log (tag, evento) VALUES ($1, $2)",
                    &[&log_entry.tag, &log_entry.evento],
                )
                .unwrap();

            build_ok_response("Entrada del sensor creada con exito")
        }

        (Err(_log_entry), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error no se creo la entrada del sensor"),
    }
}

fn handle_post_status_request(request: &str) -> String {
    match (
        get_status_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(stat_entry), Ok(mut client)) => {
            client
                .execute(
                    "INSERT INTO status (stat, battery) VALUES ($1, $2)",
                    &[&stat_entry.stat, &stat_entry.battery],
                )
                .unwrap();

            build_ok_response("Entrada del sensor creada con exito")
        }

        (Err(_log_entry), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error no se creo la entrada del sensor"),
    }
}

// handle_get_request function -----------------------------------------------------------------------------------------------------------------

fn handle_get_sensor_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            // si no funciona implementando crono voler la fecha un <string> y en el query poner
            // TO_CHAR(fecha, 'DD/MM/YYYY') as fecha
            match client.query_one(
                "SELECT id, tipo, temperatura, humedad, fecha, hora FROM dht11_data WHERE id = $1",
                &[&id],
            ) {
                Ok(row) => {
                    let dht11 = Sensor {
                        id: row.get(0),
                        tipo: row.get(1),
                        temperatura: row.get(2),
                        humedad: row.get(3),
                        fecha: row.get(4),
                        hora: row.get(5),
                    };

                    build_ok_response(&serde_json::to_string(&dht11).unwrap())
                }
                _ => build_not_found_response("Entrada no encontrada"),
            }
        }

        (Err(_id), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error"),
    }
}

fn handle_get_log_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            match client.query_one(
                "SELECT id, tag, evento, fecha, hora FROM log WHERE id = $1",
                &[&id],
            ) {
                Ok(row) => {
                    let log_entry = Log {
                        id: row.get(0),
                        tag: row.get(1),
                        evento: row.get(2),
                        fecha: row.get(3),
                        hora: row.get(4),
                    };

                    build_ok_response(&serde_json::to_string(&log_entry).unwrap())
                }
                _ => build_not_found_response("Log no encontrado"),
            }
        }
        (Err(_id), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error"),
    }
}

fn handle_get_status_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            match client.query_one("SELECT id, stat, battery FROM status WHERE id = $1", &[&id]) {
                Ok(row) => {
                    let status_entry = Status {
                        id: row.get(0),
                        stat: row.get(1),
                        battery: row.get(2),
                    };

                    build_ok_response(&serde_json::to_string(&status_entry).unwrap())
                }
                _ => build_not_found_response("Status no encontrado"),
            }
        }
        (Err(_id), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error"),
    }
}

// handle_get_all_request function -----------------------------------------------------------------------------------------------------------------

fn handle_get_all_sensor_request() -> String {
    match Client::connect(DB_URL, NoTls) {
        Ok(mut client) => {
            let mut dht11s = Vec::new();

            for row in client
                .query(
                    "SELECT id, tipo, temperatura, humedad, fecha, hora FROM dht11_data",
                    &[],
                )
                .unwrap()
            {
                dht11s.push(Sensor {
                    id: row.get(0),
                    tipo: row.get(1),
                    temperatura: row.get(2),
                    humedad: row.get(3),
                    fecha: row.get(4),
                    hora: row.get(5),
                });
            }

            build_ok_response(&serde_json::to_string(&dht11s).unwrap())
        }

        _ => build_internal_error_response("Error"),
    }
}

fn handle_get_all_log_request() -> String {
    match Client::connect(DB_URL, NoTls) {
        Ok(mut client) => {
            let mut dht11s = Vec::new();

            for row in client
                .query("SELECT id, tag, evento, fecha, hora FROM log", &[])
                .unwrap()
            {
                dht11s.push(Log {
                    id: row.get(0),
                    tag: row.get(1),
                    evento: row.get(2),
                    fecha: row.get(3),
                    hora: row.get(4),
                });
            }

            build_ok_response(&serde_json::to_string(&dht11s).unwrap())
        }
        _ => build_internal_error_response("Error"),
    }
}

// handle_put_request function -----------------------------------------------------------------------------------------------------------------

fn handle_put_sensor_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        get_sensor_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(dht11), Ok(mut client)) => {
            client
                .execute(
                    "UPDATE dht11_data SET tipo = $1, temperatura = $2, humedad = $3, fecha = $4, hora = $5 WHERE id = $6",
                    &[&dht11.tipo, &dht11.temperatura, &dht11.humedad, &dht11.fecha, &dht11.hora, &id],
                )
                .unwrap();

            build_ok_response("Entrada actualizada con exito")
        }
        (Err(_id), Err(_dht11), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error"),
    }
}

fn handle_put_log_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        get_log_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(log_entry), Ok(mut client)) => {
            client
                .execute(
                    "UPDATE log SET tag = $1, evento = $2, fecha = $3, hora = $4 WHERE id = $5",
                    &[
                        &log_entry.tag,
                        &log_entry.evento,
                        &log_entry.fecha,
                        &log_entry.hora,
                        &id,
                    ],
                )
                .unwrap();

            build_ok_response("Entrada actualizada con exito")
        }
        (Err(_id), Err(_log), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error"),
    }
}

fn handle_put_status_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        get_status_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(status_entry), Ok(mut client)) => {
            client
                .execute(
                    "UPDATE status SET stat = $1, battery = $2 WHERE id = $3",
                    &[&status_entry.stat, &status_entry.battery, &id],
                )
                .unwrap();

            build_ok_response("Entrada actualizada con exito")
        }
        (Err(_id), Err(_status), Ok(_client)) => {
            build_bad_request_response("Verifica la estructura de la petición")
        }

        _ => build_internal_error_response("Error"),
    }
}

// handle_delete_request function -----------------------------------------------------------------------------------------------------------------

fn handle_delete_sensor_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            let rows_affected = client
                .execute("DELETE FROM dht11_data WHERE id = $1", &[&id])
                .unwrap();

            if rows_affected == 0 {
                return build_not_found_response("Entry no se encontró");
            }

            build_ok_response("Entrada eliminada con exito")
        }

        _ => build_internal_error_response("Error"),
    }
}

fn handle_delete_log_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            let rows_affected = client
                .execute("DELETE FROM log WHERE id = $1", &[&id])
                .unwrap();

            if rows_affected == 0 {
                return build_not_found_response("Entry no se encontró");
            }

            build_ok_response("Entrada eliminada con exito")
        }

        _ => build_internal_error_response("Error"),
    }
}

fn handle_delete_status_request(request: &str) -> String {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            let rows_affected = client
                .execute("DELETE FROM status WHERE id = $1", &[&id])
                .unwrap();

            if rows_affected == 0 {
                return build_not_found_response("Entry no se encontró");
            }

            build_ok_response("Entrada eliminada con exito")
        }

        _ => build_internal_error_response("Error"),
    }
}

// set_database function

fn set_database() -> Result<(), PostgresError> {
    // Conect to database
    let mut client = Client::connect(DB_URL, NoTls)?;

    client.batch_execute(
        "CREATE TABLE IF NOT EXISTS dht11_data (
                id SERIAL PRIMARY KEY,
                tipo INTEGER     NOT NULL,
                temperatura REAL NOT NULL,
                humedad    REAL NOT NULL,
                fecha      DATE NOT NULL DEFAULT CURRENT_DATE,
                hora       TIME NOT NULL DEFAULT CURRENT_TIME
            );

            CREATE TABLE IF NOT EXISTS log (
                id     SERIAL      PRIMARY KEY,
                tag    VARCHAR(50) NOT NULL,
                evento VARCHAR(255) NOT NULL,   
                fecha  DATE        NOT NULL DEFAULT CURRENT_DATE,
                hora   TIME        NOT NULL DEFAULT CURRENT_TIME
            );
            
            CREATE TABLE IF NOT EXISTS status (
                id SERIAL PRIMARY KEY,
                stat VARCHAR(20) NOT NULL,
                battery INTEGER NOT NULL
            );",
    )?;

    Ok(())
}

// get_id function
fn get_id(request: &str) -> &str {
    request
        .split("/")
        .nth(2)
        .unwrap_or_default()
        .split_whitespace()
        .next()
        .unwrap_or_default()
}

// deserialize Sensor from request body with the id
fn get_sensor_request_body(request: &str) -> Result<Sensor, serde_json::Error> {
    serde_json::from_str(request.split("\r\n\r\n").last().unwrap_or_default())
}

fn get_sensor_vec_request_body(request: &str) -> Result<Vec<Sensor>, serde_json::Error> {
    serde_json::from_str(request.split("\r\n\r\n").last().unwrap_or_default())
}

fn get_log_request_body(request: &str) -> Result<Log, serde_json::Error> {
    serde_json::from_str(request.split("\r\n\r\n").last().unwrap_or_default())
}

fn get_log_vec_request_body(request: &str) -> Result<Vec<Log>, serde_json::Error> {
    serde_json::from_str(request.split("\r\n\r\n").last().unwrap_or_default())
}

fn get_status_request_body(request: &str) -> Result<Status, serde_json::Error> {
    serde_json::from_str(request.split("\r\n\r\n").last().unwrap_or_default())
}
