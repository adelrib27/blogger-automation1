-- C71 UNIVERSAL SAFE: D1 SQLite metadata, NO blogue/pet-specific rows.
-- Apply only to a NEW, explicit V31 D1 database after review, backup,
-- named environment, migration approval and read-after-write test.
-- NOT applied to a live DB by this PR.

CREATE TABLE IF NOT EXISTS v31_ready_leases (
  site_key TEXT NOT NULL,
  campaign TEXT NOT NULL,
  lease_name TEXT NOT NULL,
  owner_nonce TEXT NOT NULL,
  acquired_epoch INTEGER NOT NULL,
  expires_epoch INTEGER NOT NULL,
  PRIMARY KEY (site_key,campaign,lease_name),
  CHECK (expires_epoch > acquired_epoch)
);

CREATE TABLE IF NOT EXISTS v31_ready_jobs (
  site_key TEXT NOT NULL,
  campaign TEXT NOT NULL,
  fingerprint TEXT NOT NULL,
  product_key TEXT NOT NULL,
  html_sha256 TEXT NOT NULL,
  evidence_sha256 TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('READY','USED')),
  created_epoch INTEGER NOT NULL,
  used_epoch INTEGER,
  PRIMARY KEY(site_key,campaign,fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_v31_ready_jobs_tenant_status
  ON v31_ready_jobs(site_key,campaign,status);

CREATE TABLE IF NOT EXISTS v31_verified_evidence (
  site_key TEXT NOT NULL,
  campaign TEXT NOT NULL,
  product_key TEXT NOT NULL,
  product_title TEXT NOT NULL,
  verified_epoch INTEGER NOT NULL,
  expires_epoch INTEGER NOT NULL,
  evidence_sha256 TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  PRIMARY KEY(site_key,campaign,product_key),
  CHECK(expires_epoch > verified_epoch)
);

CREATE TABLE IF NOT EXISTS v31_search_budget (
  site_key TEXT NOT NULL,
  campaign TEXT NOT NULL,
  day_utc TEXT NOT NULL,
  kind TEXT NOT NULL CHECK(kind IN ('SEARCH','HTTP')),
  used INTEGER NOT NULL DEFAULT 0,
  max_allowed INTEGER NOT NULL,
  blocked_until_epoch INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(site_key,campaign,day_utc,kind),
  CHECK(used >= 0 AND max_allowed >= 1)
);
