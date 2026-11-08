"""Offline-only contract tests: never invoke sudo, MT5, or source deployment."""
import io
import tarfile
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch

from ops import approved_source_stage_v1 as s


AT = datetime(2026, 11, 8, 10, 0, tzinfo=timezone.utc)


def approved(now=AT):
    return {
        "schema": "abutron.inactive.source.stage.approval.v1",
        "repo": s.SOURCE_REPO,
        "commit": s.SOURCE_COMMIT,
        "archive_sha256": "a" * 64,
        "approved_utc": now.isoformat().replace("+00:00", "Z"),
        "restic_snapshot": "abcd0123",
        "restic_remote_check": "PASS",
        "v7_db_readback": "PASS",
        "isolated_restore_drill": "PASS",
        "root_operator_review": "APPROVED",
    }


class ApprovalTests(unittest.TestCase):
    def test_exact_valid_approval(self):
        s.validate_approval(approved(), AT)

    def test_no_approval_without_independent_restore_drill(self):
        v = approved()
        v["isolated_restore_drill"] = "NOT_TESTED"
        with self.assertRaises(s.Blocked):
            s.validate_approval(v, AT)

    def test_no_cross_project_or_moving_branch(self):
        for key, value in [
            ("repo", "untrusted/repo"),
            ("commit", "main"),
            ("commit", "b" * 40),
            ("archive_sha256", "b" * 63),
            ("root_operator_review", "PENDING"),
            ("restic_remote_check", "NOT_VERIFIED"),
            ("v7_db_readback", "MISSING"),
            ("restic_snapshot", "invalid!"),
        ]:
            with self.subTest(key=key, value=value):
                v = approved()
                v[key] = value
                with self.assertRaises(s.Blocked):
                    s.validate_approval(v, AT)

    def test_freshness_and_exact_fields(self):
        for stamp in [
            AT - timedelta(hours=7),
            AT + timedelta(minutes=1),
        ]:
            v = approved(stamp)
            with self.assertRaises(s.Blocked):
                s.validate_approval(v, AT)
        v = approved()
        v["extra_command"] = "/bin/sh"
        with self.assertRaises(s.Blocked):
            s.validate_approval(v, AT)


class ArchiveTests(unittest.TestCase):
    def member(self, name, kind=tarfile.REGTYPE, size=42):
        m = tarfile.TarInfo(name=name)
        m.type = kind
        m.size = size
        return m

    def test_only_approved_regular_source_files(self):
        for name in [
            "apex11/abutron_replacement/native_v4_off_fence.py",
            "apex11/mql5/AbutronApexExistingDerivV4_6207.mq5",
            "apex11/tests/test_fp_history_window.py",
            "risk_guard/reservation_store.py",
        ]:
            self.assertEqual(s.validate_member(self.member(name)).as_posix(), name)

    def test_archive_traversal_and_unsafe_members_denied(self):
        for name in [
            "/etc/sudoers",
            "apex11/abutron_replacement/../../../etc/sudoers",
            "apex11/abutron_replacement/./bad.py",
            "apex11/abutron_replacement//double.py",
            "apex11/abutron_replacement/evil\\file.py",
            "apex11/abutron_replacement/bad name.py",
            "apex11/requirements.txt",
            ".github/workflows/privileged.yml",
            "etc/systemd/system/new.service",
            "opt/abutron/config",
        ]:
            with self.subTest(name=name):
                with self.assertRaises(s.Blocked):
                    s.validate_member(self.member(name))
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE,
                     tarfile.DIRTYPE, tarfile.CHRTYPE):
            with self.subTest(kind=kind):
                with self.assertRaises(s.Blocked):
                    s.validate_member(self.member(
                        "apex11/tests/untrusted.py", kind))
        with self.assertRaises(s.Blocked):
            s.validate_member(self.member(
                "risk_guard/massive.py", size=s.MAX_EXTRACTED + 1))


class EntrypointTests(unittest.TestCase):
    def test_unknown_execution_mode_denied(self):
        self.assertEqual(sorted(s.COMMANDS.values()), ["rollback", "stage"])
        self.assertEqual(len(s.COMMANDS), 2)
        with patch("sys.argv", ["python3"]), patch("os.geteuid", return_value=0):
            with self.assertRaises(s.Blocked):
                s.main()

    def test_root_and_zero_arguments_required(self):
        with patch("sys.argv", ["/usr/local/sbin/abutron-gh-apex-source-stage-v1",
                                "--unsafe"]), patch("os.geteuid", return_value=0):
            with self.assertRaises(s.Blocked):
                s.main()
        with patch("sys.argv", ["/usr/local/sbin/abutron-gh-apex-source-stage-v1"]), \
             patch("os.geteuid", return_value=1000):
            with self.assertRaises(s.Blocked):
                s.main()


if __name__ == "__main__":
    unittest.main()
