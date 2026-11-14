# Checkpoint — V31 selector R53, 13/11/2026 (America/Recife)

**Status: ROOT CAUSE HYPOTHESIS REPRODUCED OFFLINE, PATCH PREPARED, NOT YET APPLIED ON WINDOWS; REAL E2E STILL FAILED/NOT VALIDATED.**

## User's actual PowerShell evidence
- `failure_controls.json` timestamp 2026-11-13 19:05:38: 40 visible controls, 2 listboxes, 2 options, **0** “Novo blog”, 0 title inputs.
- `visible_controls.json` timestamp 2026-11-13 20:31:08: 40 controls, 2 options, 0 “Novo blog”.
- `preflight_controls.json` timestamp 2026-11-13 19:07:18: 75 controls, 2 listboxes, 37 options, **1** “Novo blog”, 0 title inputs.
- Immutable checkpoint `logs/provisioning/v31/lab-v31-e2e-20261113-r53.json`: `PROVISION_V31_PARTIAL_STOP`, `error_type=SafeAutomationError`, `created=false`, blog ID missing, `steps=[]`, settings/theme not started. A created=false checkpoint is not proof that no Blogger save happened; never retry exact R53.
- Blogger API list did not show R53 and Chrome/CDP audit passed, but neither proves that R53 has not been created in another visibility scope.
- Exact Windows baseline from authenticated MCP: `browser_provision.py=eee759adc7c79b1e914aab34687140fd021556c83a7636d84cc44469ad8e90c1`; `provision_new_blog_v31.py=ca124cb7409252ef0c319a44e694721b2d7e2be799bea8b08251e8c85bb95d56`.

## Code defect and scoped fix
The current `open_blog_switcher` *always* toggles a listbox, doesn't test existing “Novo blog” visibility, and on a Playwright click exception may issue a second DOM click. This can close an already-open menu or leave an ambiguous UI. This defect is **confirmed in code**; it remains a **hypothesis** as to the exact dynamic sequence of the 19:05 failure.

Prepared patch `browser_provision_selector_v31.patch` (only `browser_provision.py`) to:
1. Reuse already visible “Novo blog” without toggling.
2. Inspect `aria-expanded`, refuse to toggle an already-expanded menu closed.
3. Wait in a bounded loop for options to hydrate, and fail closed when missing.
4. Never issue a second click after ambiguous Playwright errors.

No slug, checkpoint, Blogger API, SEO, theme, Cloudflare, credentials, publication or authorization changes.

## Regressions and rollback
- Added `test_v31_selector_guard_lab.py`: baseline failed **7/10** cases (6 failures, 1 error); candidate passed **10/10**.
- Candidate plus 15 previous core/tests = **25/25 offline PASS** in isolated container; dependencies used current available files and selected historical snapshots, **NOT a real Chrome test**.
- Windows installer simulated under a temporary root: exact single-file backup/apply/hash/rollback PASS; second rollback blocked. The scratch test replaced the local_service hash only to account for an older snapshot; **no such bypass exists in the delivered installer**.
- Candidate `browser_provision.py` SHA256: `9c679f8f5b4f16390696ab2fd0eb9314006895617317ee586477a370e9b2216a`.
- Delivered ZIP: `BLOGGER_V31_SELECTOR_GUARD_LAB_SAFE_2026-11-13.zip`; SHA256 `92d43b48d97220639e37f6566090a02a551d3f7c1497b5dc5810211694cca999`. Manifest and archive integrity cross-checked; contains scripts for 25 Windows offline tests, exact source-hash preconditions, backup/rollback and the previously validated V2 controlled Python process restart gate. Installer only touches `browser_provision.py` and never writes Blogger.
- **The ZIP is NOT yet installed on Windows**; live MCP `source_manifest_v31` still confirms baseline SHA `eee759...`, Runner health OK, `v31_public_e2e_validated=false`.

## Next only available action
The authenticated MCP inspection tool is intentionally READ_ONLY. User must run the checksum-verified ZIP installer once on their Windows (safe scoped edit), share `RESULTADO`, `BACKUP`, `OFFLINE_TESTS`, `EXIT_CODE`. Afterward independently check hashes/health/audit, then **do not reuse R53**. A fresh exact LAB slug may be provisioned only once after preflight and reconciliation. Report partial stops as failures; no blanket main merge or public production edits.
