"""Read real SFO fixtures and verify title-specific launcher state."""
from paths import ROOT
import importlib.util
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from game_profiles import GRAVITY2, REMASTERED, effective_fps, inspect_game

spec = importlib.util.spec_from_file_location('gravity_launcher', ROOT / 'launcher/bbport_launcher_win.py')
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


def make_game(root, serial, title, version='01.11'):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'eboot.bin').write_bytes(b'fixture')
    keys, data, entries = bytearray(), bytearray(), bytearray()
    for key, value in [('TITLE_ID', serial), ('TITLE', title), ('APP_VER', version)]:
        encoded = value.encode('utf-8') + b'\0'
        entries += struct.pack('<HHIII', len(keys), 0x204, len(encoded), len(encoded), len(data))
        keys += key.encode() + b'\0'
        data += encoded
    header = struct.pack('<4sIIII', b'\0PSF', 0x101, 20 + len(entries),
                         20 + len(entries) + len(keys), 3)
    (root / 'sce_sys').mkdir(exist_ok=True)
    (root / 'sce_sys/param.sfo').write_bytes(header + entries + keys + data)
    return root


class GameProfileTests(unittest.TestCase):
    def test_only_sequel_update_can_enable_patched_timing(self):
        self.assertEqual(effective_fps(GRAVITY2, {'APP_VER': '01.11'}, '90'), '90')
        self.assertEqual(effective_fps(GRAVITY2, {'APP_VER': '01.00'}, 'uncap'), '30')
        self.assertEqual(effective_fps(REMASTERED, {'APP_VER': '01.11'}, 'uncap'), '30')
        with self.assertRaises(ValueError):
            effective_fps(GRAVITY2, {'APP_VER': '01.11'}, 'invalid')

    def test_remastered_region_title_fallback_and_sequel_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for serial, title, expected in [('CUSA01130', 'Localized title', REMASTERED),
                    ('CUSA01113', 'Gravity Rush™ Remastered', REMASTERED),
                    ('CUSA03694', 'Gravity Rush 2', GRAVITY2)]:
                self.assertEqual(inspect_game(make_game(root / serial, serial, title))[0], expected)

    def test_other_games_invalid_serials_and_missing_eboot_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for serial, title in [('CUSA99999', 'Other game'), ('../../other', 'Gravity Rush Remastered'),
                                  ('', 'Gravity Rush Remastered')]:
                game = make_game(root, serial, title)
                with self.assertRaises(ValueError):
                    inspect_game(game)
            game = make_game(root, 'CUSA03694', 'Gravity Rush 2')
            (game / 'eboot.bin').unlink()
            with self.assertRaisesRegex(ValueError, 'eboot.bin'):
                inspect_game(game)

    def test_switching_games_isolates_saves_caches_and_timing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = make_game(root / 'first', 'CUSA01130', 'Gravity Rush Remastered')
            second = make_game(root / 'second', 'CUSA03694', 'Gravity Rush 2')
            with patch.object(launcher, 'DATA_DIR', root / 'data'), patch.dict(os.environ,
                    {'BB_GPU_USER_DIR': 'previous-game-cache'}, clear=True):
                env1, _ = launcher.launch_environment(first, 'uncap')
                env2, _ = launcher.launch_environment(second, 'uncap')
            self.assertNotEqual(env1['BB_USER_DIR'], env2['BB_USER_DIR'])
            self.assertEqual(env1['BB_GPU_USER_DIR'], env1['BB_USER_DIR'])
            self.assertEqual(env2['BB_GPU_USER_DIR'], env2['BB_USER_DIR'])
            self.assertEqual(env1['BB_FPS'], '30')  # Patch disabled; game timing unchanged.
            self.assertEqual(env2['BB_FPS'], 'uncap')
