"""Root integration tests run ONLY on disposable GitHub-hosted CI runners.

All files live inside a TemporaryDirectory. Absolutely no /opt, MT5, actual
Restic repo, sudoers, production staging or trading access is exercised.
"""
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import unittest
from datetime import datetime, timezone
from hashlib import sha256

from ops import approved_source_stage_v1 as s
from ops.tests.test_approved_source_stage_v1 import approved, AT

FILE = "apex11/abutron_replacement/native_v4_off_fence.py"
DATA = b"# fixture only: no code is imported from staged bundle\n"


@unittest.skipUnless(os.geteuid() == 0, "root integration in isolated hosted CI")
class RootIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="abutron-offline-stage-")
        self.p = Path(self.tmp.name)
        self.old = s.INBOX, s.STORE
        root = self.p / "root"
        root.mkdir(mode=0o700)
        s.INBOX = root / "approval"
        s.STORE = root / "inactive-store"
        s.INBOX.mkdir(mode=0o700)
        s.STORE.mkdir(mode=0o700)
        self.bundle = s.INBOX / "source.tar.gz"
        self.manifest = s.INBOX / "manifest.json"
        self._write_tar()
        self._write_manifest()

    def tearDown(self):
        s.INBOX, s.STORE = self.old
        self.tmp.cleanup()

    def _write_tar(self, name=FILE, kind=tarfile.REGTYPE):
        with tarfile.open(self.bundle, "w:gz") as f:
            info = tarfile.TarInfo(name)
            info.type = kind
            info.size = len(DATA) if kind == tarfile.REGTYPE else 0
            if kind == tarfile.SYMTYPE:
                info.linkname = "/etc/passwd"
            f.addfile(info, io.BytesIO(DATA) if kind == tarfile.REGTYPE else None)
        self.bundle.chmod(0o600)

    def _write_manifest(self, **changes):
        p = approved(AT)
        p["archive_sha256"] = sha256(self.bundle.read_bytes()).hexdigest()
        p.update(changes)
        self.manifest.write_text(json.dumps(p), encoding="utf-8")
        self.manifest.chmod(0o600)

    def test_stage_and_rollback_touch_only_isolated_root_store(self):
        s._prepare_store()
        msg = s._stage(AT)
        self.assertIn("INACTIVE_SOURCE_STAGED", msg)
        release = s.STORE / "releases" / s.SOURCE_COMMIT
        self.assertEqual((release / FILE).read_bytes(), DATA)
        state = json.loads((s.STORE / "state.json").read_text())
        self.assertEqual(state["current"], s.SOURCE_COMMIT)
        self.assertIsNone(state["previous"])
        with self.assertRaises(s.Blocked):
            s._stage(AT)
        self.assertEqual(s._rollback(), "INACTIVE_SOURCE_ROLLBACK_POINTER_ONLY")
        self.assertIsNone(json.loads(
            (s.STORE / "state.json").read_text())["current"])
        self.assertTrue((release / FILE).exists())
        with self.assertRaises(s.Blocked):
            s._rollback()

    def test_missing_restore_evidence_blocks_before_staging(self):
        self._write_manifest(isolated_restore_drill="NOT_TESTED")
        s._prepare_store()
        with self.assertRaises(s.Blocked):
            s._stage(AT)
        self.assertFalse((s.STORE / "releases" / s.SOURCE_COMMIT).exists())

    def test_changed_archive_denied(self):
        self.bundle.write_bytes(b"not the approved archive")
        s._prepare_store()
        with self.assertRaises(s.Blocked):
            s._stage(AT)
        self.assertFalse((s.STORE / "releases" / s.SOURCE_COMMIT).exists())

    def test_link_in_signed_archive_denied(self):
        self._write_tar(kind=tarfile.SYMTYPE)
        self._write_manifest()
        s._prepare_store()
        with self.assertRaises(s.Blocked):
            s._stage(AT)
        self.assertFalse((s.STORE / "releases" / s.SOURCE_COMMIT).exists())

    def test_traversal_in_signed_archive_denied(self):
        self._write_tar(name="apex11/abutron_replacement/../../../etc/cron.d/evil")
        self._write_manifest()
        s._prepare_store()
        with self.assertRaises(s.Blocked):
            s._stage(AT)
        self.assertFalse((s.STORE / "releases" / s.SOURCE_COMMIT).exists())

    def test_root_approval_directory_must_not_be_writable_by_runner(self):
        s.INBOX.chmod(0o770)
        s._prepare_store()
        with self.assertRaises(s.Blocked):
            s._stage(AT)
        self.assertFalse((s.STORE / "releases" / s.SOURCE_COMMIT).exists())

if __name__ == "__main__":
    unittest.main()
