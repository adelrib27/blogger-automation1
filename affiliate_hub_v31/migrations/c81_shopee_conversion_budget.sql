CREATE TABLE IF NOT EXISTS v31_shopee_conversion_attempts (
    day_utc TEXT NOT NULL,
    slot INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 3),
    campaign TEXT,
    product_key TEXT,
    CHECK ((campaign IS NULL) = (product_key IS NULL)),
    PRIMARY KEY (day_utc, slot),
    UNIQUE (day_utc, campaign, product_key)
);
