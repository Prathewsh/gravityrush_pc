from paths import ROOT
import struct
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from patches import compile_patches, compile_external, external_patches, external_selection, encode


def elf_image(code):
    header = bytearray(0x1000)
    struct.pack_into('<Q', header, 0x20, 0x40)
    struct.pack_into('<HH', header, 0x36, 56, 1)
    struct.pack_into('<IIQQQQQQ', header, 0x40, 1, 5, 0x1000, 0, 0, len(code), 0x4000, 0x1000)
    return bytes(header) + bytes(code)


class PatchCompilerTests(unittest.TestCase):
    def test_bundled_patch_rejects_wrong_version_and_out_of_range(self):
        xml = ROOT / 'patches/GravityRush2.xml'
        for version, segments in [('01.00', [(0, 0x2000000)]), ('01.11', [(0, 16)])]:
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    compile_patches(xml, ['60 FPS'], version, segments)

    def test_external_selection_and_unsupported_patch_are_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'extra.xml').write_text('''<Patch><TitleID><ID>CUSA03694</ID></TitleID>
                <Metadata Name="On" AppVer="01.11" isEnabled="true"><PatchList>
                  <Line Type="bytes" Address="0x400100" Value="9090"/>
                </PatchList></Metadata>
                <Metadata Name="Bad" AppVer="01.11" isEnabled="true"><PatchList>
                  <Line Type="bytes" Address="0x400200" Value="90"/>
                  <Line Type="mask" Value="90 ??"/>
                </PatchList></Metadata></Patch>''')
            found = external_patches(root)
            self.assertEqual(compile_external(external_selection(found, None), [(0, 0x1000)]),
                             [(0x100, b'\x90\x90')])
            config = root / 'patches.json'
            config.write_text('{"disabled":["extra.xml/On", "extra.xml/Bad"]}')
            self.assertEqual(external_selection(found, config), [])

    def test_encodings(self):
        for kind, value, expected in [('bytes32', '0x12345678', b'\x78\x56\x34\x12'),
                                      ('utf8', 'Kat', b'Kat\0'), ('float32', '1', struct.pack('<f', 1))]:
            self.assertEqual(encode(ET.Element('Line', Type=kind, Value=value)), expected)
