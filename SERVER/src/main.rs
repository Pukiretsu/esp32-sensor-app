#![allow(unused)]

use crate::{ctx::Ctx};

pub use self::error::{Error, Result};

use axum::{
    extract::{Path, Query}, http::{Method, Uri}, middleware, response::{Html, IntoResponse, Response}, routing::{get, get_service}, Json, Router
};
use model::ModelController;
use serde::Deserialize;
use serde_json::json;
use uuid::Uuid;
use std::{net::SocketAddr, time::Duration};
use tower_cookies::CookieManagerLayer;
use tower_http::services::ServeDir;
use sqlx::{migrate::Migrator, pool, postgres::PgPoolOptions, PgPool};
use dotenv::dotenv;


mod ctx;
mod error;
mod model;
mod web;

static MIGRATOR: Migrator = sqlx::migrate!("./migrations");

pub async fn run_migrations(pool: &PgPool) -> Result<(), sqlx::Error> {
    MIGRATOR.run(pool).await
}

#[tokio::main]
async fn main() -> Result<()> {
    // init database connection
    dotenv().ok();
    let db_connection_str = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgres//postgres:passwd@localhost".to_string());

    println!("  ->> Connecting to: {db_connection_str}");
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .acquire_timeout(Duration::from_secs(60))
        .connect(&db_connection_str)
        .await
        .expect("->> couldn't connect to database.\n");

    static MIGRATOR: Migrator = sqlx::migrate!();

    // Init ModelController.
    let mc = ModelController::new().await?;

    let routes_apis = web::routes_dht11_records::routes(mc.clone())
        .route_layer(middleware::from_fn(web::mw_auth::mw_require_auth));

    let routes_all = Router::new()
        .merge(web::routes_login::routes())
        .merge(routes_apis)
        .layer(middleware::map_response(main_response_mapper))
        .layer(middleware::from_fn_with_state(
            mc.clone(),
            web::mw_auth::mw_ctx_resolver,
        ))
        .layer(CookieManagerLayer::new())
        .fallback_service(routes_static());

    // region: -- Server
    let addr = SocketAddr::from(([0, 0, 0, 0], 8080));
    println!("->> LISTENING on {addr}\n");
    axum::Server::bind(&addr)
        .serve(routes_all.into_make_service())
        .await
        .unwrap();
    // endregion: -- server

    Ok(())
}

async fn main_response_mapper(
    ctx: Option<Ctx>,
    uri: Uri,
    req_method: Method,
    res: Response) -> Response {
    println!("->> {:<12} - main_response_mapper", "RES_MAPPER");
    
    let uuid =  Uuid::new_v4();
    // -- get eventual response error.
    let service_error = res.extensions().get::<Error>();
    let client_status_error = service_error.map(|se| se.clien_status_and_error());

    // -- If client error, build the new response.
    let error_response = client_status_error
    .as_ref()
    .map(|(status_code, client_error)| {
        let client_error_body = json!({
            "error": {
                "type" : client_error.as_ref(),
                "req_uuid": uuid.to_string(),
            }
        });

        println!("  ->> client_error_body: {client_error_body}");
        
        // Build the new response from the client error body
        (*status_code, Json(client_error_body)).into_response()
    });

    // -- Build and log the server log line
    let client_error = client_status_error.unzip().1;
    //log_request(uuid, req_method, uri, ctx, service_error, client_error).await;
    println!("  ->> server log line - {uuid} - Error: {service_error:?}");

    println!();
    error_response.unwrap_or(res)
}

fn routes_static() -> Router {
    Router::new().nest_service("/", get_service(ServeDir::new("./")))
}