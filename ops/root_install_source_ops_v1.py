#!/usr/bin/python3 -I
"""One-time, operator-executed root bootstrap for ABUTRON's fixed sudo operations.

Not invoked by GitHub Actions. Root operator must inspect and execute on the
real localhost through authenticated SSH. This only installs two fixed,
non-overwritable source-only helper files plus exact no-argument sudo entries;
it NEVER gives a runner general sudo, restarts services or enables trading.

Prerequisites: fresh offsite backup, source review, root-owned checkout and
explicit operator approval. Source staging still REQUIRES its independent
isolated-restore evidence manifest; installation alone does not certify it.
"""
from __future__ import annotations

from hashlib import sha1, sha256
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys
import tempfile

SOURCE = Path("/root/abutron-ops/ops/approved_source_stage_v1.py")
EXPECTED_GIT_BLOB = "ef89d40d3af2c5481405ea694483bf1b1b478fa4"
RUNNER_USER = "abutrongha"
BINARIES = (
    Path("/usr/local/sbin/abutron-gh-apex-source-stage-v1"),
    Path("/usr/local/sbin/abutron-gh-apex-source-rollback-v1"),
)
SUDOERS = Path("/etc/sudoers.d/abutron-gh-apex-source-ops-v1")
STORE = Path("/var/lib/abutron-apex11-inactive-source-v1")
APPROVAL_PARENT = Path("/var/lib/abutron-gh-runner")
APPROVAL = APPROVAL_PARENT / "abutron-apex11-source-approval-v1"
ALLOWED_INSTALL = {
    str(SOURCE),
    *(str(p) for p in BINARIES),
    str(SUDOERS),
}


class Blocked(RuntimeError):
    pass


def secure_root(path: Path, *, directory: bool) -> None:
    st = path.lstat()
    if st.st_uid != 0 or st.st_mode & 0o022 or stat.S_ISLNK(st.st_mode):
        raise Blocked("ROOT_OWNERSHIP_OR_MODE_UNTRUSTED")
    if directory:
        if not stat.S_ISDIR(st.st_mode):
            raise Blocked("ROOT_DIRECTORY_REQUIRED")
    elif not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
        raise Blocked("ROOT_REGULAR_FILE_REQUIRED")


def _secure_source() -> bytes:
    for path in (Path("/root"), Path("/root/abutron-ops"),
                 Path("/root/abutron-ops/ops")):
        secure_root(path, directory=True)
    secure_root(SOURCE, directory=False)
    fd = os.open(SOURCE, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode) or st.st_uid != 0 or st.st_size > 150000:
            raise Blocked("UNTRUSTED_PRIVILEGED_SOURCE")
        with os.fdopen(fd, "rb", closefd=False) as f:
            data = f.read(150001)
    finally:
        os.close(fd)
    digest = sha1(("blob " + str(len(data)) + "\0").encode() + data).hexdigest()
    if digest != EXPECTED_GIT_BLOB:
        raise Blocked("PRIVILEGED_SOURCE_BLOB_MISMATCH")
    if not data.startswith(b"#!/usr/bin/python3 -I\n"):
        raise Blocked("PRIVILEGED_INTERPRETER_NOT_ISOLATED")
    return data


def _make_root_dir(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        path.mkdir(mode=0o700)
    secure_root(path, directory=True)
    if path.stat().st_mode & 0o077:
        raise Blocked("ROOT_STORE_NOT_PRIVATE")


def _atomic_create(path: Path, content: bytes, mode: int) -> None:
    if path.exists() or path.is_symlink():
        raise Blocked("REFUSE_TO_REPLACE_EXISTING_ROOT_PROGRAM")
    fd, name = tempfile.mkstemp(prefix=".abutron-root-bootstrap-", dir=path.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as file:
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
        if path.exists() or path.is_symlink():
            raise Blocked("ROOT_PROGRAM_CONCURRENT_CHANGE")
        os.replace(name, path)
    finally:
        if os.path.lexists(name):
            os.unlink(name)


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, timeout=15,
                          check=False, env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin"})


def _assert_runner_denied(command: str) -> None:
    result = _run("/usr/sbin/runuser", "-u", RUNNER_USER,
                  "--", "/usr/bin/sudo", "-n", command)
    if result.returncode == 0:
        raise Blocked("UNRESTRICTED_RUNNER_SUDO_DETECTED")


def install() -> None:
    if os.geteuid() != 0 or len(sys.argv) != 1:
        raise Blocked("ONE_TIME_ROOT_NO_ARGUMENTS_ONLY")
    pwd.getpwnam(RUNNER_USER)
    os.umask(0o077)
    source = _secure_source()
    for path in (Path("/usr"), Path("/usr/local"), Path("/usr/local/sbin"),
                 Path("/etc"), Path("/etc/sudoers.d"),
                 Path("/var"), Path("/var/lib")):
        secure_root(path, directory=True)
    for path in (*BINARIES, SUDOERS):
        if path.exists() or path.is_symlink():
            raise Blocked("REFUSE_TO_REPLACE_ROOT_TARGET")
    # Do not modify the existing GitHub runner directory's permissions.
    # Fail rather than treating runner-writeable source approval as trusted.
    secure_root(APPROVAL_PARENT, directory=True)
    _assert_runner_denied("/usr/bin/id")
    _assert_runner_denied("/usr/bin/bash")

    created: list[Path] = []
    try:
        _make_root_dir(STORE)
        _make_root_dir(APPROVAL)
        for target in BINARIES:
            _atomic_create(target, source, 0o750)
            created.append(target)
            secure_root(target, directory=False)

        rule = (
            RUNNER_USER + " ALL=(root) NOPASSWD: "
            + str(BINARIES[0]) + ' "", '
            + str(BINARIES[1]) + ' ""\n'
        )
        _atomic_create(SUDOERS, rule.encode("ascii"), 0o440)
        created.append(SUDOERS)
        secure_root(SUDOERS, directory=False)

        for args in (("/usr/sbin/visudo", "-cf", str(SUDOERS)),
                     ("/usr/sbin/visudo", "-c")):
            if _run(*args).returncode != 0:
                raise Blocked("SUDOERS_INVALID")

        for target in BINARIES:
            result = _run("/usr/sbin/runuser", "-u", RUNNER_USER,
                          "--", "/usr/bin/sudo", "-n", "-l", str(target))
            if result.returncode != 0:
                raise Blocked("EXPECTED_FIXED_SUDO_NOT_GRANTED")

        _assert_runner_denied("/usr/bin/id")
        _assert_runner_denied("/usr/bin/bash")
        _assert_runner_denied("/usr/bin/sh")
    except Exception:
        # Never leave partially-authorized root programs on a failing install.
        for path in reversed(created):
            try:
                secure_root(path, directory=False)
                path.unlink()
            except OSError:
                print("MANUAL_OPERATOR_CLEANUP_REQUIRED")
        raise

    print("ABUTRON_RESTRICTED_ROOT_EXECUTABLES_INSTALLED")
    print("SOURCE_SHA256=" + sha256(source).hexdigest())
    print("EXACT_NO_ARGUMENT_SUDO_GRANTS=2")
    print("NO_GENERAL_ROOT_SHELL_GRANTED")
    print("INACTIVE_STAGE_REQUIRES_VALID_BACKUP_RESTORE_APPROVAL")


if __name__ == "__main__":
    try:
        install()
    except (Blocked, OSError, KeyError, ValueError, subprocess.TimeoutExpired):
        print("ABUTRON_ROOT_BOOTSTRAP_BLOCKED")
        raise SystemExit(78)
