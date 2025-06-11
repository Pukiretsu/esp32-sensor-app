#![allow(unused)]

use anyhow::Result;
use serde_json::json;

#[tokio::test]
async fn quick_dev() -> Result<()> {
    let hc = httpc_test::new_client("http://localhost:8080")?;

    //hc.do_get("/hello2/nigga").await?.print().await?;
    let req_login = hc.do_post(
        "/api/login",
        json!({
            "username": "esplogger",
            "passwd": "jzsoNdIqMQGo6Tq"
        }),
    );

    //req_login.await?.print().await?;

    let req_create_dht11_record = hc.do_post(
        "/api/sensor",
        json!({
            "record_session": "Test_Session",
            "dht11_number": 2,
            "temperature": 52.1,
            "humidity": 80.1,
            "date": "2025-05-06",
            "time": "04:30:24.355574",
        }),
    );

    req_create_dht11_record.await?.print().await?;

    hc.do_get("/api/sensor").await?.print().await?;
    //hc.do_get("/hello2/Niggerman").await?.print().await?;
    //hc.do_get("/src/main.rs").await?.print().await?;

    Ok(())
}
