use postgres::Error as PostgresError;
use postgres::{Client, NoTls};
use std::env;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use chrono::{NaiveDate, NaiveTime};

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

// Create the database's URL.

//const DB_URL: &str = "postgres://admin:HATmik211@db:5432/sensor_log_db";
const DB_URL: &str = env!("DATABASE_URL");

// Constants for HTTP responses

const OK_RESPONSE: &str = "HTTP/1.1 200 OK\r\n\
                           Access-Control-Allow-Origin: *\r\n\
                           Content-Type: application/json\r\n\r\n";

const OK_RESPONSE_CORS: &str = "HTTP/1.1 200 OK\r\n\
                       Access-Control-Allow-Origin: *\r\n\
                       Access-Control-Allow-Methods: GET, OPTIONS\r\n\
                       Access-Control-Allow-Headers: Content-Type\r\n\r\n";

const NOT_FOUND: &str = "HTTP/1.1 404 NOT FOUND\r\n\r\n";
const INTERNAL_SERVER_ERROR: &str = "HTTP/1.1 500 INTERNAL SERVER ERROR\r\n\r\n";
const UNAUTHORIZED_ERROR: &str = "HTTP/1.1 401 Unauthorized\r\nWWW-Authenticate: Basic realm=\"Restricted Area\"\r\n\r\n";
const BAD_REQUEST: &str = "HTTP/1.1 400 Bad Request\r\n\r\n";
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
    let mut buffer = [0; 1024];
    let mut request = String::new();

    match stream.read(&mut buffer) {
        Ok(size) => {
            request.push_str(String::from_utf8_lossy(&buffer[..size]).as_ref());

            // handle all CRUD requests
            let (status_line, content) = match &*request {
                
                // handle dht_11 related requests
                r if r.starts_with("POST /sensor") => handle_post_sensor_request(r),
                r if r.starts_with("GET /sensor/") => handle_get_sensor_request(r),
                r if r.starts_with("GET /sensor") => handle_get_all_sensor_request(),
                r if r.starts_with("PUT /sensor/") => handle_put_sensor_request(r),
                r if r.starts_with("DELETE /sensor/") => handle_delete_sensor_request(r),
                
                // handle log related requests
                r if r.starts_with("POST /log") => handle_post_log_request(r),
                r if r.starts_with("GET /log/") => handle_get_log_request(r),
                r if r.starts_with("GET /log") => handle_get_all_log_request(),
                r if r.starts_with("PUT /log/") => handle_put_log_request(r),
                r if r.starts_with("DELETE /log/") => handle_delete_log_request(r),
                
                // handle web requests and be CORS compliant
                r if r.starts_with("OPTIONS") => (OK_RESPONSE_CORS.to_string(), "".to_string()),
                
                _ => (NOT_FOUND.to_string(), "404 Not Found".to_string()),
            };

            stream
                .write_all(format!("{}{}", status_line, content).as_bytes())
                .unwrap();
        }
        Err(e) => {
            println!("Error: {}", e);
        }
    }
}

// ------------ Controllers --------------------

//POST 
//handle_post_request function template
/* 
fn handle_post_request(request: &str) -> (String, String) {
    match (
        get_sensor_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(Sensor), Ok(mut client)) => {
            client
                .execute(
                    "INSERT INTO Sensors (titulo, contenido, estado) VALUES ($1, $2, $3)",
                    &[&Sensor.titulo, &Sensor.contenido, &Sensor.estado],
                )
                .unwrap();

            (
                OK_RESPONSE.to_string(),
                "Tarea creada con exito".to_string(),
            )
        }
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}*/

fn handle_post_sensor_request(request: &str) -> (String, String) {
    match (
        get_sensor_request_body(&request),
        Client::connect(DB_URL,NoTls),
    ) {
        (Ok(dht11), Ok(mut client)) => {
            client
                .execute(
                    "INSERT INTO dht11_data (tipo, temperatura, humedad) VALUES ($1, $2, $3)",
                    &[&dht11.tipo, &dht11.temperatura, &dht11.humedad],
                )
                .unwrap();

            (
                OK_RESPONSE.to_string(),
                "Entrada del sensor creada con exito".to_string(),
            )
        }
        (Err(_dht11_entry), Ok(_client)) => (BAD_REQUEST.to_string(), "Verifica la estructura de la petición".to_string()),
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error no se creo la entrada del sensor".to_string()),
    }
}

fn handle_post_log_request(request: &str) -> (String, String) {
    match (
        get_log_request_body(&request),
        Client::connect(DB_URL,NoTls),
    ) {
        (Ok(log_entry), Ok(mut client)) => {
            client
                .execute(
                    "INSERT INTO log (tag, evento) VALUES ($1, $2)",
                    &[&log_entry.tag, &log_entry.evento],
                )
                .unwrap();

            (
                OK_RESPONSE.to_string(),
                "Entrada del sensor creada con exito".to_string(),
            )
        },

        (Err(_log_entry), Ok(_client)) => (BAD_REQUEST.to_string(), "Verifica la estructura de la petición".to_string()),

        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error no se creo la entrada del sensor".to_string()),
    }
}

// handle_get_request function
/* 
fn handle_get_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            match client.query_one("SELECT id, titulo, contenido, estado, TO_CHAR(fecha,'DD/MM/YYYY') as fecha FROM Sensors WHERE id = $1", &[&id]) {
                Ok(row) => {
                    let sensor = Sensor {
                        id: row.get(0),
                        tipo: row.get(1),
                        temperatura: row.get(2),
                        humedad: row.get(3),
                        fecha: row.get(4),
                    };

                    (
                        OK_RESPONSE.to_string(),
                        serde_json::to_string(&Sensor).unwrap(),
                    )
                }
                _ => (NOT_FOUND.to_string(), "Tarea no encontrada".to_string()),
            }
        }
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}
*/

fn handle_get_sensor_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            // si no funciona implementando crono voler la fecha un <string> y en el query poner
            // TO_CHAR(fecha, 'DD/MM/YYYY') as fecha
            match client.query_one("SELECT id, tipo, temperatura, humedad, fecha, hora FROM dht11_data WHERE id = $1", &[&id]) {
                Ok(row) => {
                    let dht11 = Sensor {
                        id: row.get(0),
                        tipo: row.get(1),
                        temperatura: row.get(2),
                        humedad: row.get(3),
                        fecha: row.get(4),
                        hora: row.get(5),
                    };

                    (
                        OK_RESPONSE.to_string(),
                        serde_json::to_string(&dht11).unwrap(),
                    )
                }
                _ => (NOT_FOUND.to_string(), "Entrada no encontrada".to_string()),
            }
        },
        
        (Err(_id), Ok(_client)) => (BAD_REQUEST.to_string(), "Verifica la estructura de la petición".to_string()),
        
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}

fn handle_get_log_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            match client.query_one("SELECT id, tag, evento, fecha, hora FROM log WHERE id = $1", &[&id]) {
                Ok(row) => {
                    let log_entry = Log {
                        id: row.get(0),
                        tag: row.get(1),
                        evento: row.get(2),
                        fecha: row.get(3),
                        hora: row.get(4),
                    };

                    (
                        OK_RESPONSE.to_string(),
                        serde_json::to_string(&log_entry).unwrap(),
                    )
                }
                _ => (NOT_FOUND.to_string(), "Log no encontrado".to_string()),
            }
        }
        (Err(_id), Ok(_client)) => (BAD_REQUEST.to_string(), "Verifica la estructura de la petición".to_string()),
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}

// handle_get_all_request function
/*
fn handle_get_all_request(request: &str) -> (String, String) {
    match Client::connect(DB_URL, NoTls) {
        Ok(mut client) => {
            let mut Sensors = Vec::new();

            for row in client.query("SELECT id, titulo, contenido, estado, TO_CHAR(fecha,'DD/MM/YYYY') as fecha FROM Sensors", &[]).unwrap() {
                Sensors.push(Sensor {
                    id: row.get(0),
                    titulo: row.get(1),
                    contenido: row.get(2),
                    estado: row.get(3),
                    fecha: row.get(4),
                });
            }

            (
                OK_RESPONSE.to_string(),
                serde_json::to_string(&Sensors).unwrap(),
            )
        }
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}
*/

fn handle_get_all_sensor_request() -> (String, String) {
    match Client::connect(DB_URL, NoTls) {
        Ok(mut client) => {
            let mut dht11s = Vec::new();

            for row in client.query("SELECT id, tipo, temperatura, humedad, fecha, hora FROM dht11_data", &[]).unwrap() {
                dht11s.push(Sensor {
                    id: row.get(0),
                    tipo: row.get(1),
                    temperatura: row.get(2),
                    humedad: row.get(3),
                    fecha: row.get(4),
                    hora: row.get(5),
                });
            }

            (
                OK_RESPONSE.to_string(),
                serde_json::to_string(&dht11s).unwrap(),
            )
        }
        
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}

fn handle_get_all_log_request() -> (String, String) {
    match Client::connect(DB_URL, NoTls) {
        Ok(mut client) => {
            let mut dht11s = Vec::new();

            for row in client.query("SELECT id, tag, evento, fecha, hora FROM log", &[]).unwrap() {
                dht11s.push(Log {
                    id: row.get(0),
                    tag: row.get(1),
                    evento: row.get(2),
                    fecha: row.get(3),
                    hora: row.get(4),
                });
            }

            (
                OK_RESPONSE.to_string(),
                serde_json::to_string(&dht11s).unwrap(),
            )
        }
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}

// handle_put_request function
/*
fn handle_put_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        get_Sensor_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(Sensor), Ok(mut client)) => {
            client
                .execute(
                    "UPDATE Sensors SET titulo = $1, contenido = $2, estado = $3 WHERE id = $4",
                    &[&Sensor.titulo, &Sensor.contenido, &Sensor.estado, &id],
                )
                .unwrap();

            (
                OK_RESPONSE.to_string(),
                "tarea actualizada con exito".to_string(),
            )
        }
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}
*/

fn handle_put_sensor_request(request: &str) -> (String, String) {
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

            (
                OK_RESPONSE.to_string(),
                "Entrada actualizada con exito".to_string(),
            )
        }
        (Err(_id), Err(_dht11),Ok(_client)) => (BAD_REQUEST.to_string(), "Verifica la estructura de la petición".to_string()),
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}

fn handle_put_log_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        get_log_request_body(&request),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(log_entry), Ok(mut client)) => {
            client
            .execute(
                "UPDATE log SET tag = $1, evento = $2, fecha = $3, hora = $4 WHERE id = $5",
                &[&log_entry.tag, &log_entry.evento, &log_entry.fecha, &log_entry.hora, &id],
            )
            .unwrap();
        
        (
            OK_RESPONSE.to_string(),
            "Entrada actualizada con exito".to_string(),
        )
    }
    (Err(_id), Err(_log),Ok(_client)) => (BAD_REQUEST.to_string(), "Verifica la estructura de la petición".to_string()),
        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}

// handle_delete_request function
/* 
fn handle_delete_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            let rows_affected = client
                .execute("DELETE FROM Sensors WHERE id = $1", &[&id])
                .unwrap();

            if rows_affected == 0 {
                return (NOT_FOUND.to_string(), "Sensor not found".to_string());
            }

            (
                OK_RESPONSE.to_string(),
                "tarea eliminada con exito".to_string(),
            )
        }

        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}
*/

fn handle_delete_sensor_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            let rows_affected = client
                .execute("DELETE FROM dht11_data WHERE id = $1", &[&id])
                .unwrap();

            if rows_affected == 0 {
                return (NOT_FOUND.to_string(), "Entry no se encontró".to_string());
            }

            (
                OK_RESPONSE.to_string(),
                "Entrada eliminada con exito".to_string(),
            )
        }

        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
    }
}

fn handle_delete_log_request(request: &str) -> (String, String) {
    match (
        get_id(&request).parse::<i32>(),
        Client::connect(DB_URL, NoTls),
    ) {
        (Ok(id), Ok(mut client)) => {
            let rows_affected = client
                .execute("DELETE FROM log WHERE id = $1", &[&id])
                .unwrap();

            if rows_affected == 0 {
                return (NOT_FOUND.to_string(), "Entry no se encontró".to_string());
            }

            (
                OK_RESPONSE.to_string(),
                "Entrada eliminada con exito".to_string(),
            )
        }

        _ => (INTERNAL_SERVER_ERROR.to_string(), "Error".to_string()),
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

fn get_log_request_body(request: &str) -> Result<Log, serde_json::Error> {
    serde_json::from_str(request.split("\r\n\r\n").last().unwrap_or_default())
}
