CREATE TABLE IF NOT EXISTS holdings(
    user_id         TEXT,
    account_name    TEXT,
    ticker          TEXT,
    security_name   TEXT,
    shares          REAL,
    target_weight   REAL,
    cost            REAL,
    price           REAL, 
    created_at      TEXT, -- YYYY-MM-DD HH:MM:SS.SSS
    updated_at      TEXT  -- YYYY-MM-DD HH:MM:SS.SSS

)