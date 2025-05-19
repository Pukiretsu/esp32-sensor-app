//! Simplistic model layer
//! (with mock-store layer)

use crate::{Error, Result};
use chrono::{NaiveDate, NaiveTime};
use serde::{Deserialize, Serialize};
use std::sync::{Arc, Mutex};

// region: --- Dht11Record Types

#[derive(Clone, Debug, Serialize)]
pub struct Dht11Record {
    pub id: u64,
    pub record_session: String,
    pub dht11_number: i32,
    pub temperature: f32,
    pub humidity: f32,
    pub date: Option<NaiveDate>,
    pub time: Option<NaiveTime>,
}

#[derive(Deserialize)]
pub struct Dht11RecordPending {
    pub record_session: String,
    pub dht11_number: i32,
    pub temperature: f32,
    pub humidity: f32,
    pub date: Option<NaiveDate>,
    pub time: Option<NaiveTime>,
}

// endregion: --- Dht11Record Types

// region: --- Model Controller
#[derive(Clone)]
pub struct ModelController {
    dht11record_store: Arc<Mutex<Vec<Option<Dht11Record>>>>,
}

// Constructor
impl ModelController {
    pub async fn new() -> Result<Self> {
        Ok(Self {
            dht11record_store: Arc::default(),
        })
    }
}

// CRUD Implementation
impl ModelController {
    // FIXME: Implement CREATE operation with SQLx
    pub async fn create_dht11_record(
        &self,
        dht11_record_pending: Dht11RecordPending,
    ) -> Result<Dht11Record> {
        let mut store = self.dht11record_store.lock().unwrap();
        let id = store.len() as u64;
        let dht11record = Dht11Record {
            id,
            record_session: dht11_record_pending.record_session,
            dht11_number: dht11_record_pending.dht11_number,
            temperature: dht11_record_pending.temperature,
            humidity: dht11_record_pending.humidity,
            date: dht11_record_pending.date,
            time: dht11_record_pending.time,
        };
        store.push(Some(dht11record.clone()));
        Ok(dht11record)
    }

    // FIXME: Implement READ operation with SQLx
    pub async fn list_dht11_records(&self) -> Result<Vec<Dht11Record>> {
        let store = self.dht11record_store.lock().unwrap();

        let records = store.iter().filter_map(|t| t.clone()).collect();

        Ok(records)
    }

    // FIXME: Implement DELETE operation with SQLx
    pub async fn delete_dht11_records(&self, id: u64) -> Result<Dht11Record> {
        let mut store = self.dht11record_store.lock().unwrap();

        let dht11_record = store.get_mut(id as usize).and_then(|t| t.take());

        dht11_record.ok_or(Error::Dht11RecordDeleteFailIdNotFound { id })
    }
}

// regioe: --- Model Contdattime
