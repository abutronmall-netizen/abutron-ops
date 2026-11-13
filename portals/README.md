# ABUTRON APEX — Client, Admin and Operator Portal Source Snapshot

**Snapshot date:** 2026-11-13 (UTC)  
**Branch:** snapshot/abutron-three-portals-2026-11-13  
**Repository visibility at upload:** PRIVATE  
**Delivery type:** source-only archives of the three existing deployed portal surfaces. No production deployment performed.

## Archives

| Artifact | Contents | Files | SHA-256 (zip bytes) |
| --- | --- | ---: | --- |
| `client-portal-source-2026-11-13.zip` | V7 client web assets; client account scripts; signup web+backend; selected client API Python modules | 102 | `5de92d34a593f27c4895bd86825907fd0bf0409d5c9cdae25314ecd70476706b` |
| `admin-portal-source-2026-11-13.zip` | V7 admin web assets; account admin UI; admin/CRM/license API Python modules | 27 | `cb9dd74301b1421ee668cb7af6ffe552137f5ed73d943e7d6ce26447534d25c4` |
| `apex-portal-source-2026-11-13.zip` | APEX 1.1 operator dashboard FastAPI source and static UI files | 31 | `6aa225e6782e28dda0e9333b0835bf3fff1567e60a371a1968ae02adf734850d` |

Each ZIP contains `SOURCE_MANIFEST.json` with individual source paths and SHA-256 hashes. These are reviewed portal code snapshots, not whole-system backups.

## Original server source roots

- `/var/www/abutron-v7/client/`
- `/var/www/abutron-v7/admin/`
- `/var/www/apex-landing/account/`
- `/opt/apex-client-portal/`
- `/opt/apex-signup/`
- `/opt/apex/runtime/apex_ui/`

## Exclusions and security

Excluded runtime databases and customer records, broker credential vaults, secrets, private keys, MT5 terminal profiles, logs, caches, historical backups, generated Python bytecode, worker process state, operating-system configuration, and other non-portal execution infrastructure. No unencrypted customer database is shipped. This archive is not a complete operational clone of ABUTRON APEX.

## Observed server facts, 2026-11-13

- `apex-client-portal.service` and `apex-signup.service` were active.
- `/account/client/`, `/account/admin/` and `/apex/` exist as browser portal entry points.
- APEX `/api/apex11-engines` returned HTTP 200 but identified its dashboard telemetry as read-only, and **did not confirm broker order execution**.
- Current Admin backend includes read-only administrative endpoints. Do not interpret this repository as evidence of full CRM mutation features.
- Some execution systemd units were in failed state. The source snapshot neither fixes nor restarts those services.

## Recommended next step

Create a **dedicated private** `abutronmall-netizen/abutron-apex-platform` repository and migrate this snapshot there. Do not merge these archives into `abutron-ops/main` or deploy them directly. This private branch is an isolated staging destination because the older `abutron-apex` repository was observed **public** at upload time.

## Integrity checks

Unzip each artifact, inspect `SOURCE_MANIFEST.json`, and compare the per-file SHA-256 digests. Verify source revisions against the currently running host before release. Use a reproducible deployment build rather than copying this archive over a running portal.
