use crate::model::{Dht11Record, Dht11RecordPending, ModelController};
use crate::Result;
use axum::extract::Path;
use axum::routing::{delete, post};
use axum::Router;
use axum::{extract::State, Json};

pub fn routes(mc: ModelController) -> Router {
    Router::new()
        .route("/sensor", post(create_dht11_record).get(list_dht11_records))
        .route("/sensor/:id", delete(delete_dht11_records))
        .with_state(mc)
}

// region: --- REST Handlers

async fn create_dht11_record(
    State(mc): State<ModelController>,
    Json(dht11_record_pending): Json<Dht11RecordPending>,
) -> Result<Json<Dht11Record>> {
    println!("->> {:<12} - Create Record of DHT11", "HANDLER");

    let dht11_record = mc.create_dht11_record(dht11_record_pending).await?;
    Ok(Json(dht11_record))
}

async fn list_dht11_records(State(mc): State<ModelController>) -> Result<Json<Vec<Dht11Record>>> {
    println!("->> {:<12} - list_dht11_records", "HANDLER");
    let dht11_records = mc.list_dht11_records().await?;
    Ok(Json(dht11_records))
}

async fn delete_dht11_records(
    State(mc): State<ModelController>,
    Path(id): Path<u64>,
) -> Result<Json<Dht11Record>> {
    println!("->> {:<12} - delete_dht11_records", "HANDLER");
    let dht11_record = mc.delete_dht11_records(id).await?;
    Ok(Json(dht11_record))
}

// endregion: --- REST Handlers
