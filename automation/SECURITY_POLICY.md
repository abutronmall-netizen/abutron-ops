# ABUTRON public source and worker-inventory security policy

GitHub currently reports **all connected abutronmall-netizen repositories as public**, including abutron-ops. Historical README statements that a repo is private do not prove its visibility.

## Permitted content

- Sanitized, read-only worker inventory with snapshot-scoped IDs, masked unit/source names, current state, schedules, source/unit SHA256, public hardening flags.
- Architecture diagrams, dependency mapping, dry-run runbooks, synthetic tests.
- Independently reviewed and sanitized source files with behavior-compatible secret/identity resolution.

## Content prohibited in a public repository

- Actual MT5 login/account data, complete account owner maps, connection profile identifiers, private email, phone or customer data.
- API keys, activation/HMAC secrets, passwords, private keys, tokens, environment-file values, signed native receipt content.
- Raw systemd ExecStart arguments or Environment content, internal authenticated URLs or private server addresses.
- Broker native cashflows, historical positions, full ledgers, M5/HCC data, SQLite account databases, private customer receipts or evidence archives.
- Unreviewed EA binaries and binary backup/recovery archives.

## Export requirements

The generator emits a selected safe field list; it does **not** copy raw unit text or the full executable source. Source labels must have 32-character profile IDs and 5+ digit account identifiers masked. A public output scan checks for identity tokens and validates summary/unit counts. Human review remains mandatory: hashes, filenames and error strings may also reveal sensitive details.

No program should automatically publish raw server files to GitHub, change LIVE activation, modify risk settings, promote a model or restart any unit as part of inventory or documentation tasks.

## Private source completion

Keep original scripts in encrypted offsite custody until a truly private version-controlled repository is available. Source restoration needs exact hash, source bytes, dependencies, secrets injection, systemd unit and timer, rollback and independent tests. SHA256 alone is not a recoverable code backup.
