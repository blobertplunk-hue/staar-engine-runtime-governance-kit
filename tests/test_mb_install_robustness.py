"""Stage 4 robustness fixtures for MB_INSTALL v0 atomic_swap."""

import importlib.util
import os
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "mb_install_v0", ROOT / "tools" / "metablooms" / "mb_install_v0.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

atomic_swap = _mod.atomic_swap
AtomicSwapError = _mod.AtomicSwapError


def _write_file(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestAtomicSwapRobustness(unittest.TestCase):

    def test_atomic_swap_refuses_without_bootstrap_flag(self):
        with tempfile.TemporaryDirectory() as root:
            tmp_tree = os.path.join(root, "tmp")
            target_tree = os.path.join(root, "target")
            os.makedirs(tmp_tree)
            with self.assertRaises(NotImplementedError):
                atomic_swap(tmp_tree, target_tree, allowed_root=root)

    def test_atomic_swap_requires_target_and_allowed_root(self):
        with tempfile.TemporaryDirectory() as root:
            tmp_tree = os.path.join(root, "tmp")
            os.makedirs(tmp_tree)
            with self.assertRaises(AtomicSwapError):
                atomic_swap(tmp_tree, _bootstrap_flag=True)
            with self.assertRaises(AtomicSwapError):
                atomic_swap(tmp_tree, os.path.join(root, "target"), _bootstrap_flag=True)

    def test_atomic_swap_rejects_target_outside_allowed_root(self):
        with tempfile.TemporaryDirectory() as allowed_root, tempfile.TemporaryDirectory() as outside_root:
            tmp_tree = os.path.join(allowed_root, "tmp")
            os.makedirs(tmp_tree)
            outside_target = os.path.join(outside_root, "target")
            with self.assertRaises(AtomicSwapError):
                atomic_swap(
                    tmp_tree,
                    outside_target,
                    allowed_root=allowed_root,
                    _bootstrap_flag=True,
                )

    def test_atomic_swap_rejects_tmp_tree_outside_allowed_root(self):
        with tempfile.TemporaryDirectory() as allowed_root, tempfile.TemporaryDirectory() as outside_root:
            tmp_tree = os.path.join(outside_root, "tmp")
            os.makedirs(tmp_tree)
            target_tree = os.path.join(allowed_root, "target")
            with self.assertRaises(AtomicSwapError):
                atomic_swap(
                    tmp_tree,
                    target_tree,
                    allowed_root=allowed_root,
                    _bootstrap_flag=True,
                )

    def test_atomic_swap_replaces_throwaway_target(self):
        with tempfile.TemporaryDirectory() as root:
            tmp_tree = os.path.join(root, "tmp")
            target_tree = os.path.join(root, "target")
            _write_file(os.path.join(tmp_tree, "payload.txt"), "new")
            _write_file(os.path.join(target_tree, "payload.txt"), "old")

            atomic_swap(tmp_tree, target_tree, allowed_root=root, _bootstrap_flag=True)

            self.assertFalse(os.path.exists(tmp_tree))
            self.assertEqual(_read_file(os.path.join(target_tree, "payload.txt")), "new")
            self.assertFalse(os.path.exists(target_tree + ".mb_install_backup"))

    def test_atomic_swap_rolls_back_if_new_tree_replace_fails(self):
        with tempfile.TemporaryDirectory() as root:
            tmp_tree = os.path.join(root, "tmp")
            target_tree = os.path.join(root, "target")
            _write_file(os.path.join(tmp_tree, "payload.txt"), "new")
            _write_file(os.path.join(target_tree, "payload.txt"), "old")

            real_replace = _mod.os.replace
            calls = []

            def flaky_replace(src, dst):
                calls.append((src, dst))
                if len(calls) == 2:
                    raise OSError("simulated second replace failure")
                return real_replace(src, dst)

            with mock.patch.object(_mod.os, "replace", side_effect=flaky_replace):
                with self.assertRaises(OSError):
                    atomic_swap(tmp_tree, target_tree, allowed_root=root, _bootstrap_flag=True)

            self.assertEqual(_read_file(os.path.join(target_tree, "payload.txt")), "old")
            self.assertTrue(os.path.exists(tmp_tree))
            self.assertFalse(os.path.exists(target_tree + ".mb_install_backup"))

    def test_atomic_swap_refuses_existing_backup_path(self):
        with tempfile.TemporaryDirectory() as root:
            tmp_tree = os.path.join(root, "tmp")
            target_tree = os.path.join(root, "target")
            backup_tree = target_tree + ".mb_install_backup"
            _write_file(os.path.join(tmp_tree, "payload.txt"), "new")
            _write_file(os.path.join(target_tree, "payload.txt"), "old")
            _write_file(os.path.join(backup_tree, "payload.txt"), "backup")

            with self.assertRaises(AtomicSwapError):
                atomic_swap(tmp_tree, target_tree, allowed_root=root, _bootstrap_flag=True)


if __name__ == "__main__":
    unittest.main()
