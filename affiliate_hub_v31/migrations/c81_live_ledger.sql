-- Provision only after the owner approves the operational LIVE policy.
CREATE TABLE IF NOT EXISTS v31_autonomous_live_attempts (
    site_key TEXT NOT NULL,
    campaign TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    post_id TEXT NOT NULL,
    policy_sha256 TEXT NOT NULL,
    created_epoch INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('CLAIMED','PUBLISHED','FAILED')),
    PRIMARY KEY (site_key, campaign, fingerprint),
    UNIQUE (site_key, campaign, post_id)
);
CREATE INDEX IF NOT EXISTS v31_live_attempts_recent
    ON v31_autonomous_live_attempts (site_key, campaign, created_epoch);
