CREATE TABLE dht11_records (
    id BIGSERIAL PRIMARY KEY,
    cid BIGINT NOT NULL,
    record_session TEXT NOT NULL,
    dht11_number INTEGER NOT NULL,
    temperature REAL NOT NULL,
    humidity REAL NOT NULL,
    date DATE,
    time TIME
);

CREATE TABLE request_log_lines (
    uuid UUID PRIMARY KEY,
    timestamp TIMESTAMP NOT NULL,

    user_id BIGINT,

    req_path TEXT NOT NULL,
    req_method TEXT NOT NULL,

    client_error_type TEXT,
    error_type TEXT,
    error_data JSONB
);