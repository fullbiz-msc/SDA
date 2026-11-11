import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('sda_install', ROOT / 'install.py')
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallTests(unittest.TestCase):
    def test_both_agents_install_complete_independent_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            for agent, directory in (('codex', '.agents'), ('claude', '.claude')):
                destination = installer.install(agent, home=tmp)
                self.assertEqual(destination, Path(tmp) / directory / 'skills/sda')
                installer.verify_package(destination)
                source = ROOT / agent / 'sda'
                files = [p for p in source.rglob('*') if p.is_file()]
                for path in files:
                    self.assertEqual(path.read_bytes(), (destination / path.relative_to(source)).read_bytes())

    def test_existing_skill_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'sda'
            destination.mkdir()
            marker = destination / 'SKILL.md'
            marker.write_text('User custom skill')
            with self.assertRaises(FileExistsError):
                installer.install('codex', destination)
            self.assertEqual(marker.read_text(), 'User custom skill')
            self.assertEqual(list(destination.iterdir()), [marker])

    def test_mismatched_standard_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = installer.install('codex', Path(tmp) / 'sda')
            (destination / 'references/ARCHITECTURE_STANDARDS.md').write_text('Modified')
            with self.assertRaises(ValueError):
                installer.verify_package(destination)

    def test_symlink_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / 'sda'
            destination.symlink_to(Path(tmp) / 'missing', target_is_directory=True)
            with self.assertRaises(FileExistsError):
                installer.install('claude', destination)
            self.assertTrue(destination.is_symlink())


if __name__ == '__main__':
    unittest.main()
