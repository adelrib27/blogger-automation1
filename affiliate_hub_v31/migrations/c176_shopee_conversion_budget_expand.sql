CREATE TABLE v31_shopee_conversion_attempts_c176_new (
    day_utc TEXT NOT NULL,
    slot INTEGER NOT NULL CHECK (slot BETWEEN 1 AND 20),
    campaign TEXT,
    product_key TEXT,
    CHECK ((campaign IS NULL) = (product_key IS NULL)),
    PRIMARY KEY (day_utc, slot),
    UNIQUE (day_utc, campaign, product_key)
);

INSERT INTO v31_shopee_conversion_attempts_c176_new (day_utc, slot, campaign, product_key)
SELECT day_utc, slot, campaign, product_key FROM v31_shopee_conversion_attempts;
DROP TABLE v31_shopee_conversion_attempts;
ALTER TABLE v31_shopee_conversion_attempts_c176_new RENAME TO v31_shopee_conversion_attempts;
