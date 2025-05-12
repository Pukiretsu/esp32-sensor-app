use crate::{web, Error, Result};
use axum::{body, routing::post, Json, Router};
use serde::Deserialize;
use serde_json::{json, Value};
use tower_cookies::{Cookie, Cookies};

pub fn routes() -> Router {
    Router::new().route("/api/login", post(api_login))
}

async fn api_login(cookies: Cookies, payload: Json<LoginPayload>) -> Result<Json<Value>> {
    println!("->> {:<12} - Api_login", "HANDLER");

    // TODO: implement real db/auth logic
    if payload.username != "demo1" || payload.passwd != "welcome" {
        return Err(Error::LoginFail);
    }

    // FIXME: Implement real auth-token gen/sign
    cookies.add(Cookie::new(web::AUTH_TOKEN, "user-1.exp.sign"));

    // Create the success body.
    let body = Json(json!({
        "result": {
            "success": true
        }
    }));

    Ok(body)
}

#[derive(Debug, Deserialize)]
struct LoginPayload {
    username: String,
    passwd: String,
}
