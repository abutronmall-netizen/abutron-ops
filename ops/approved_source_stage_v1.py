#!/usr/bin/python3
"""ABUTRON fixed, owner-bootstrapped INACTIVE source staging and rollback.

INSTALLATION IS NOT AUTOMATIC. Review on production with a real root operator.
Copy this exact file, owned root:root mode 0750, to the two command names in
COMMANDS below. Both invocations take ZERO arguments, ignore environment
inputs, and never write to /opt, MT5, CRM, systemd, or LIVE/DEMO controls.

Source bundle and backup attestation must be approved independently by a
root operator. Nothing in this program attests a real broker or enables orders.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from hashlib import sha256
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tarfile
import tempfile

SOURCE_COMMIT = "68f9815d39eeecbecbc5845e051e5ca2f9ae848c"
SOURCE_REPO = "abutronmall-netizen/abutron-apex"
INBOX = Path("/var/lib/abutron-gh-runner/abutron-apex11-source-approval-v1")
STORE = Path("/var/lib/abutron-apex11-inactive-source-v1")
COMMANDS = {
    "abutron-gh-apex-source-stage-v1": "stage",
    "abutron-gh-apex-source-rollback-v1": "rollback",
}
SOURCE_PREFIXES = (
    "apex11/abutron_replacement/",
    "apex11/mql5/",
    "apex11/tests/",
    "risk_guard/",
)
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
HEX_SNAPSHOT = re.compile(r"[a-f0-9]{8,64}\Z")
SAFE_REL = re.compile(r"[a-zA-Z0-9._/-]{1,230}\Z")
MAX_ARCHIVE = 40 * 1024 * 1024
MAX_EXTRACTED = 80 * 1024 * 1024
MAX_MEMBERS = 800


class Blocked(RuntimeError):
    pass


def check_root_owned(path: Path, *, directory: bool) -> os.stat_result:
    st = path.lstat()
    if path.is_symlink() or st.st_uid != 0 or (st.st_mode & 0o022):
        raise Blocked("UNTRUSTED_ROOT_OWNERSHIP_OR_MODE")
    if directory and not stat.S_ISDIR(st.st_mode):
        raise Blocked("EXPECTED_ROOT_DIRECTORY")
    if not directory and (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1):
        raise Blocked("EXPECTED_SINGLE_ROOT_REGULAR_FILE")
    return st


def read_root_json(path: Path) -> dict:
    st = check_root_owned(path, directory=False)
    if st.st_size > 8192:
        raise Blocked("OVERSIZED_ROOT_APPROVAL")
    # O_NOFOLLOW prevents a symlink swap between lstat and open.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as file:
        if os.fstat(file.fileno()).st_ino != st.st_ino:
            raise Blocked("APPROVAL_REPLACED")
        raw = file.read(8193)
    try:
        out = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise Blocked("INVALID_ROOT_APPROVAL") from exc
    if not isinstance(out, dict):
        raise Blocked("INVALID_ROOT_APPROVAL_SCHEMA")
    return out


def _timestamp(value: object, now: datetime) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise Blocked("APPROVAL_UTC_REQUIRED")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Blocked("APPROVAL_UTC_INVALID") from exc
    if not now - timedelta(hours=6) <= stamp <= now + timedelta(seconds=30):
        raise Blocked("APPROVAL_EXPIRED_OR_FUTURE")


def validate_approval(approval: dict, now: datetime) -> None:
    if set(approval) != {
        "schema", "repo", "commit", "archive_sha256",
        "approved_utc", "restic_snapshot", "restic_remote_check",
        "v7_db_readback", "isolated_restore_drill", "root_operator_review",
    }:
        raise Blocked("APPROVAL_FIELDS_NOT_EXACT")
    if (approval["schema"] != "abutron.inactive.source.stage.approval.v1"
        or approval["repo"] != SOURCE_REPO
        or approval["commit"] != SOURCE_COMMIT
        or not isinstance(approval["archive_sha256"], str)
        or HEX64.fullmatch(approval["archive_sha256"]) is None
        or not isinstance(approval["restic_snapshot"], str)
        or HEX_SNAPSHOT.fullmatch(approval["restic_snapshot"]) is None
        or approval["restic_remote_check"] != "PASS"
        or approval["v7_db_readback"] != "PASS"
        or approval["isolated_restore_drill"] != "PASS"
        or approval["root_operator_review"] != "APPROVED"):
        raise Blocked("APPROVAL_NOT_PROVEN_OR_NOT_CURRENT_SOURCE")
    _timestamp(approval["approved_utc"], now)


def validate_member(member: tarfile.TarInfo) -> PurePosixPath:
    raw = member.name
    if (not isinstance(raw, str)
        or SAFE_REL.fullmatch(raw) is None
        or raw.startswith("/")
        or "\\" in raw
        or any(p in ("", ".", "..") for p in raw.split("/"))
        or not raw.startswith(SOURCE_PREFIXES)
        or not member.isfile()
        or member.issym() or member.islnk()
        or member.size < 0 or member.size > MAX_EXTRACTED):
        raise Blocked("ARCHIVE_UNTRUSTED_MEMBER")
    return PurePosixPath(raw)


def _digest_file(path: Path) -> str:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    h = sha256()
    with os.fdopen(fd, "rb") as f:
        while buf := f.read(1024 * 1024):
            h.update(buf)
    return h.hexdigest()


def _write_json_atomic(path: Path, data: dict) -> None:
    blob = (json.dumps(data, sort_keys=True, separators=(",", ":")) + "\n").encode()
    fd, temp = tempfile.mkstemp(prefix=".state.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as f:
            f.write(blob)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.lexists(temp):
            os.unlink(temp)


def _store_state() -> dict:
    f = STORE / "state.json"
    if not f.exists():
        if f.is_symlink():
            raise Blocked("UNTRUSTED_INACTIVE_STATE_SYMLINK")
        return {"schema": "abutron.inactive.stage.state.v1",
                "current": None, "previous": None}
    state = read_root_json(f)
    if (set(state) != {"schema", "current", "previous"}
        or state["schema"] != "abutron.inactive.stage.state.v1"):
        raise Blocked("CORRUPT_INACTIVE_STATE")
    for key in ("current", "previous"):
        if state[key] is not None and (
            not isinstance(state[key], str)
            or HEX64.fullmatch(state[key]) is None):
            raise Blocked("CORRUPT_INACTIVE_STATE_RELEASE")
    return state


def _prepare_store() -> None:
    # Do not trust existing world-writable ancestors or symbolic directories.
    for parent in (STORE.parent, STORE):
        check_root_owned(parent, directory=True)
    releases = STORE / "releases"
    if not releases.exists():
        releases.mkdir(mode=0o700)
    check_root_owned(releases, directory=True)


def _stage(now: datetime) -> str:
    check_root_owned(INBOX.parent, directory=True)
    check_root_owned(INBOX, directory=True)
    approval = read_root_json(INBOX / "manifest.json")
    validate_approval(approval, now)
    archive = INBOX / "source.tar.gz"
    st = check_root_owned(archive, directory=False)
    if st.st_size <= 0 or st.st_size > MAX_ARCHIVE:
        raise Blocked("ARCHIVE_SIZE_INVALID")
    if _digest_file(archive) != approval["archive_sha256"]:
        raise Blocked("ARCHIVE_SHA256_MISMATCH")
    release = STORE / "releases" / SOURCE_COMMIT
    if release.exists() or release.is_symlink():
        raise Blocked("RELEASE_ALREADY_PRESENT_NO_OVERWRITE")
    tmp = Path(tempfile.mkdtemp(prefix=".unapproved.", dir=STORE / "releases"))
    try:
        os.chmod(tmp, 0o700)
        with tarfile.open(archive, "r:gz") as tar:
            members = tar.getmembers()
            if not 1 <= len(members) <= MAX_MEMBERS:
                raise Blocked("ARCHIVE_MEMBER_COUNT_INVALID")
            seen, extracted = set(), 0
            for member in members:
                rel = validate_member(member)
                if rel.as_posix() in seen:
                    raise Blocked("ARCHIVE_DUPLICATE_PATH")
                seen.add(rel.as_posix())
                extracted += member.size
                if extracted > MAX_EXTRACTED:
                    raise Blocked("ARCHIVE_DECOMPRESSED_BUDGET_EXCEEDED")
                target = tmp.joinpath(*rel.parts)
                target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                with tar.extractfile(member) as source:
                    if source is None:
                        raise Blocked("ARCHIVE_FILE_MISSING")
                    fd = os.open(target,
                                 os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                                 os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
                    with os.fdopen(fd, "wb") as sink:
                        shutil.copyfileobj(source, sink, length=128 * 1024)
                        sink.flush()
                        os.fsync(sink.fileno())
        os.replace(tmp, release)
    finally:
        if tmp.exists():
            shutil.rmtree(tmp)
    prior = _store_state()
    _write_json_atomic(STORE / "state.json", {
        "schema": "abutron.inactive.stage.state.v1",
        "current": SOURCE_COMMIT, "previous": prior["current"],
    })
    return "INACTIVE_SOURCE_STAGED_NO_ACTIVE_MT5_OR_SERVICE_CHANGE"


def _rollback() -> str:
    state = _store_state()
    if state["current"] is None:
        raise Blocked("NOTHING_TO_ROLLBACK")
    previous = state["previous"]
    check_root_owned(STORE / "releases" / state["current"], directory=True)
    if previous is not None:
        check_root_owned(STORE / "releases" / previous, directory=True)
    # Rollback only changes this INACTIVE staging metadata. Preserve both
    # releases for forensic inspection; never touch /opt or broker services.
    _write_json_atomic(STORE / "state.json", {
        "schema": "abutron.inactive.stage.state.v1",
        "current": previous, "previous": None,
    })
    return "INACTIVE_SOURCE_ROLLBACK_POINTER_ONLY"


def main() -> int:
    if len(sys.argv) != 1 or os.geteuid() != 0:
        raise Blocked("ROOT_ZERO_ARGUMENTS_REQUIRED")
    name = Path(sys.argv[0]).name
    if name not in COMMANDS:
        raise Blocked("UNAPPROVED_COMMAND_NAME")
    for p in (Path(sys.argv[0]), Path(sys.argv[0]).parent):
        check_root_owned(p, directory=p.is_dir())
    # Force a fixed umask independent of caller environment.
    os.umask(0o077)
    _prepare_store()
    lock = STORE / ".operation.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if COMMANDS[name] == "stage":
            message = _stage(datetime.now(timezone.utc))
        else:
            message = _rollback()
        print(message)
    finally:
        os.close(fd)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Blocked, OSError, tarfile.TarError, ValueError) as exc:
        # Do not emit sensitive path contents or exception traces in runner logs.
        print("ABUTRON_SOURCE_OPERATION_BLOCKED:" + type(exc).__name__)
        raise SystemExit(78)
