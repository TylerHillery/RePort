CREATE TABLE IF NOT EXISTS cash(
    user_id         TEXT,
    account_name    TEXT,
    cash            INT,  -- in pennies
    created_at      TEXT, -- YYYY-MM-DD HH:MM:SS.SSS
    updated_at      TEXT  -- YYYY-MM-DD HH:MM:SS.SSS

)