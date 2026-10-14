"""Gravity Rush 2 launch patch integration, using synthetic executable metadata."""
from paths import ROOT
import contextlib
import io
import os
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

import patches
from test_patches import elf_image


class GravityPatchTests(unittest.TestCase):
    def compile(self, title='CUSA03694', version='01.11', settings='', extra=()):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'sce_sys').mkdir()
            (root / 'sce_sys/param.sfo').write_bytes(b'fixture')
            # The compiler validates virtual ranges, without needing any game code.
            elf = bytearray(elf_image(b''))
            struct.pack_into('<Q', elf, 0x40 + 40, 0x2000000)
            (root / 'eboot.elf').write_bytes(elf)
            (root / 'settings.ini').write_text(settings)
            args = ['patches.py', '--out', str(root), '--game-dir', str(root),
                    '--settings', str(root / 'settings.ini'), *extra]
            with patch('sys.argv', args), patch('game_profiles.sfo', return_value={
                    'TITLE_ID': title, 'APP_VER': version}), patch.dict(os.environ, {}, clear=True), \
                    contextlib.redirect_stdout(io.StringIO()):
                patches.main()
            return (root / 'patches.bin').read_bytes()

    def test_fps_compiles_for_each_bundled_title(self):
        for title in patches.GAME_IDS:
            with self.subTest(title=title):
                blob = self.compile(title=title)
                magic, base, count = struct.unpack_from('<8sQQ', blob)
                self.assertEqual((magic, base), (b'BBPATCH2', patches.EBOOT_BASE))
                expected = patches.compile_patches(patches.BUILTIN_XML, ['60 FPS'], '01.11', [(0, 0x2000000)])
                self.assertEqual(count, len(expected))
                self.assertGreater(count, 0)
                self.assertEqual(blob[24:], b''.join(struct.pack('<QQ', off, len(data)) + data
                                                   for off, data in expected))

    def test_unrecognized_settings_do_not_select_patches(self):
        self.assertEqual(self.compile(), self.compile(settings=
            'effect_dof=0\nskip_intro=1\ndebug_menu=1\ncheat_no_death=1\nmodel_lod=-2\n'))

    def test_other_titles_versions_and_missing_metadata_get_no_writes(self):
        for title, version in [('CUSA99999', '01.11'), ('CUSA03694', '01.00'),
                               (None, '01.11'), ('CUSA03694', None)]:
            with self.subTest(title=title, version=version):
                self.assertEqual(self.compile(title, version), struct.pack('<8sQQ', b'BBPATCH2', 0x400000, 0))

    def test_30_fps_has_no_writes(self):
        self.assertEqual(len(self.compile(extra=('--fps', '30'))), 24)

    def test_remastered_never_receives_sequel_fps_patch(self):
        for fps in ('30', '60', '90', 'uncap'):
            with self.subTest(fps=fps):
                self.assertEqual(self.compile('CUSA01130', '01.11', extra=('--fps', fps)),
                                 struct.pack('<8sQQ', b'BBPATCH2', 0x400000, 0))

    def test_external_files_are_filtered_by_title_and_version(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = '<Patch><TitleID><ID>{}</ID></TitleID><Metadata Name="Test" AppVer="{}"/></Patch>'
            for name, title, version in [('good', 'CUSA03694', '01.11'),
                                         ('wrong_game', 'CUSA99999', '01.11'),
                                         ('old', 'CUSA03694', '01.09')]:
                (root / (name + '.xml')).write_text(template.format(title, version))
            self.assertEqual([key for key, _, _ in patches.external_patches(root)], ['good.xml/Test'])
            self.assertEqual(patches.external_patches(root, title_ids={'CUSA04943'}), [])

    def test_builtin_file_is_not_listed_as_external(self):
        self.assertEqual(patches.external_patches(ROOT / 'patches'), [])
