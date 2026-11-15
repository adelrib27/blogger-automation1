# Blogger Automation V31 — LAB E2E provision guards (2026-11-13)

**Status: PATCHED_AND_TESTED_OFFLINE / NOT_DEPLOYED_TO_WINDOWS / NO_BLOGGER_E2E.**
Dedicated branch, not merged to main. The user's request is to reach REAL end-to-end, never infer completion from mocks.

## State verified before development
- Runner health: `0.9-v31-r52-candidate`, `ok=true`, Chrome CDP audit `AUDIT_OK`, `new_blog_available=true`.
- MCP/Cloudflare V10 connected, source_manifest and read_source direct reads OK.
- Exact live hashes: `browser_provision.py=fb3d492e337db19172625a41ad0631441d82916f7f9f8fe3f47fd2a482437c01`, `provision_new_blog_v31.py=5c3b533ed35315799e595d64a48e4bb3f6aa73a0bd6ff522e214b046cbf049df`.
- Baseline package source matches live hashes with original line endings (browser CRLF; provision unchanged).
- E2E provision health flag `v31_public_e2e_validated=false`.

## Confirmed code defects and minimal fixes
1. `browser_provision.select_page` picked first URL whose host contained 'blogger.com', including `blogger.com.attacker.example` and inactive tabs. Reuse already installed `select_active_blogger_page` helper (strict host, visible preference, original fallback).
2. Provisioner requires exact originally requested slug, but `resilient_create.execute_create_resilient` default permitted up to TEN fallback slugs before provision checkpoint persisted Blog ID. Fix only provisioner via `max_address_attempts=1` and exact URL comparison before theme target validation. Keep shared resilient creator behavior unchanged for unrelated consumers.

## Executed evidence
- Before fixes: existing 10 tests OK; new 5-test contract suite had **3 failures** (visible tab, lookalike host, unexpected 10 slug attempts).
- After fixes: **15/15 offline tests PASS**, including original 10.
- Isolated installer simulation: baseline hashes validated, 15 offline tests, atomic apply, rollback and repeated rollback rejected.
- Patch candidates packaged as `BLOGGER_V31_E2E_GUARDS_WINDOWS_LAB_SAFE_2026-11-13.zip` (artifact in original ChatGPT conversation), SHA-256 `d2d7c202e2bbea77c4138e87303b5226e6b12e5fe145bf68b3f20d3817c6e5ae`.
- Candidate SHA-256: `browser_provision.py=eee759adc7c79b1e914aab34687140fd021556c83a7636d84cc44469ad8e90c1`, `provision_new_blog_v31.py=ca124cb7409252ef0c319a44e694721b2d7e2be799bea8b08251e8c85bb95d56`.
- No user Windows patch from THIS package yet, no creation, publication, theme, settings, or Blogger writes. No claim of real E2E.

## Next gated actions
1. Have user run one checksum-verified installer on their Windows. Installer runs 15 tests **before any source change**, backs up originals, updates exactly two files and reuses previously validated PID/auth/restart gate, auto-rolls back on failure; prints backup path.
2. Read live source manifest and compare candidate hashes; repeat readonly Chrome/preflight.
3. Create a unique authorized LAB blog **once** with `provision_new_blog_v31`; do not retry when checkpoint may indicate uncertain creation. Verify Blog ID, public URL, SEO, theme and checkpoint independently.
4. Distinguish *core provisioning* from 6 pages still `NOT_PUBLISHED` and Shopee/store workflows. Report scope and unresolved gaps, not artificial E2E success.

No secrets or Blogger writes in this branch. Rollback V9 gateway and original Windows source backups remain available. Do not merge without controlled LIVE tests.
