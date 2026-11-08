"""Disposable GitHub-hosted CI tests for strict root bootstrap operations.

Never test these root mutations on ABUTRON's actual self-hosted production runner.
"""
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ops import root_install_source_ops_v1 as installer


@unittest.skipUnless(os.geteuid() == 0, "hosted disposable CI root test")
class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="abutron-root-installer-")
        self.root = Path(self.tmp.name)
        self.parent = self.root / "approval-parent"
        self.parent.mkdir(mode=0o700)
        self.store = self.root / "inactive"
        self.approval = self.parent / "source-approval"
        self.bins = (self.root / "stage", self.root / "rollback")
        self.sudoers = self.root / "sudoers.conf"

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def runner(arg: tuple[str, ...]):
        if "/usr/sbin/visudo" == arg[0]:
            return subprocess.CompletedProcess(arg, 0, "", "")
        if arg[:4] == (
            "/usr/sbin/runuser", "-u", "abutrongha", "--"
        ) and arg[4:7] == ("/usr/bin/sudo", "-n", "-l"):
            return subprocess.CompletedProcess(arg, 0, "", "")
        return subprocess.CompletedProcess(arg, 1, "", "")

    def execute(self, run):
        with patch.object(installer, "BINARIES", self.bins), \
             patch.object(installer, "SUDOERS", self.sudoers), \
             patch.object(installer, "STORE", self.store), \
             patch.object(installer, "APPROVAL_PARENT", self.parent), \
             patch.object(installer, "APPROVAL", self.approval), \
             patch.object(installer, "_secure_source",
                          return_value=b"#!/usr/bin/python3 -I\n# readonly test\n"), \
             patch.object(installer.pwd, "getpwnam", return_value=object()), \
             patch.object(installer, "_run", side_effect=lambda *a: run(a)), \
             patch("sys.argv", ["trusted-root-installer"]):
            return installer.install()


    def test_reviewed_source_blob_and_approval_directory_are_pinned(self):
        from hashlib import sha1
        from ops import approved_source_stage_v1 as stage
        source = Path(stage.__file__).read_bytes()
        git_blob = sha1(
            ("blob " + str(len(source)) + "\0").encode() + source
        ).hexdigest()
        self.assertEqual(installer.EXPECTED_GIT_BLOB, git_blob)
        self.assertEqual(stage.INBOX, installer.APPROVAL)
        self.assertEqual(installer.APPROVAL_PARENT, Path("/var/lib"))
        self.assertEqual(
            stage.INBOX, Path("/var/lib/abutron-apex11-source-approval-v1")
        )
        self.assertNotIn("/var/lib/abutron-gh-runner", str(stage.INBOX))

    def test_installs_only_two_exact_commands_and_no_argument_sudo(self):
        out = io.StringIO()
        with redirect_stdout(out):
            self.execute(self.runner)
        for p in self.bins:
            self.assertEqual(p.read_bytes(),
                             b"#!/usr/bin/python3 -I\n# readonly test\n")
            self.assertEqual(p.stat().st_mode & 0o777, 0o750)
        self.assertEqual(self.sudoers.stat().st_mode & 0o777, 0o440)
        policy = self.sudoers.read_text()
        self.assertIn(' "' + '", ', policy)
        self.assertNotIn("NOPASSWD: ALL", policy)
        self.assertNotIn("sudo -n bash", policy)
        self.assertIn("EXACT_NO_ARGUMENT_SUDO_GRANTS=2", out.getvalue())
        self.assertTrue(self.store.is_dir())
        self.assertTrue(self.approval.is_dir())

    def test_invalid_visudo_rolls_back_new_commands(self):
        def failing(arg):
            if arg[0] == "/usr/sbin/visudo":
                return subprocess.CompletedProcess(arg, 1, "", "")
            return self.runner(arg)

        with self.assertRaises(installer.Blocked):
            self.execute(failing)
        for p in (*self.bins, self.sudoers):
            self.assertFalse(p.exists(), str(p))

    def test_no_general_root_shell_even_with_existing_policy(self):
        def unsafe(arg):
            # A preexisting general sudo permission must block installation.
            if arg[-1] == "/usr/bin/bash":
                return subprocess.CompletedProcess(arg, 0, "", "")
            return self.runner(arg)

        with self.assertRaises(installer.Blocked):
            self.execute(unsafe)
        self.assertFalse(self.sudoers.exists())


if __name__ == "__main__":
    unittest.main()
