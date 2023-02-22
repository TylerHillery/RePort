CREATE TABLE IF NOT EXISTS holdings(
    account_name    VARCHAR,
    ticker          VARCHAR,
    security_name   VARCHAR,
    shares          DOUBLE,
    target_weight   DOUBLE,
    cost            DOUBLE,
    price           DOUBLE
)