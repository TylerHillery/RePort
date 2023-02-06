CREATE TABLE IF NOT EXISTS holdings(
    user_id         TEXT,
    account         TEXT,
    symbol          TEXT,
    security_name   TEXT,
    shares          REAL,
    target_weight   REAL,
    price           INT,
    cost            INT,

) STRICT;