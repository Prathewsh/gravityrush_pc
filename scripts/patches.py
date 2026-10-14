"""Compile title/version-scoped Gravity Rush executable patches."""
import argparse
import json
import os
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
from game_profiles import GRAVITY2, identify, metadata

EBOOT_BASE = 0x400000
GAME_IDS = set(GRAVITY2.title_ids)
APP_VERSION = GRAVITY2.patch_version
BUILTIN_XML = Path(__file__).resolve().parent.parent / 'patches/GravityRush2.xml'
FPS_PRESETS = {'30': [], '60': ['60 FPS'], '90': ['60 FPS'], 'uncap': ['60 FPS']}


def game_app_version(game):
    try:
        return metadata(game).get('APP_VER')
    except (OSError, ValueError):
        return None


def eboot_segments(elf):
    phoff, = struct.unpack_from('<Q', elf, 0x20)
    phentsize, phnum = struct.unpack_from('<HH', elf, 0x36)
    if phentsize < 56 or phoff + phentsize * phnum > len(elf):
        raise ValueError('invalid ELF program headers')
    segments = []
    for i in range(phnum):
        kind, _, _, vaddr, _, _, memsz, _ = struct.unpack_from('<IIQQQQQQ', elf, phoff + i * phentsize)
        if kind == 1:
            segments.append((vaddr, vaddr + memsz))
    return segments


def external_patches(directory, app_version=APP_VERSION, exclude=BUILTIN_XML, title_ids=None):
    found = []
    wanted = GAME_IDS if title_ids is None else set(title_ids)
    for path in sorted(Path(directory).glob('*.xml')):
        if path.resolve() == Path(exclude).resolve():
            continue
        try:
            root = ET.parse(path).getroot()
        except ET.ParseError as error:
            print(f'Patches: {path.name}: {error}', file=sys.stderr)
            continue
        ids = {e.text.strip() for e in root.iter('ID') if e.text}
        if not ids & wanted:
            continue
        for meta in root.iter('Metadata'):
            if meta.get('AppVer') == app_version and meta.get('AppElf', 'eboot.bin') == 'eboot.bin':
                found.append((f'{path.name}/{meta.get("Name")}', path, meta))
    return found


def write_patches(path, writes):
    blob = struct.pack('<8sQQ', b'BBPATCH2', EBOOT_BASE, len(writes))
    for offset, data in writes:
        blob += struct.pack('<QQ', offset, len(data)) + data
    path.write_bytes(blob)


def encode(line):
    kind,value=line.get('Type'),line.get('Value')
    if kind=='bytes': return bytes.fromhex(value.replace(' ',''))
    if kind in ('bytes16','bytes32','bytes64'):
        return int(value,0).to_bytes(int(kind[5:])//8,'little')
    if kind=='float32': return struct.pack('<f',float(value))
    if kind=='float64': return struct.pack('<d',float(value))
    if kind=='utf8': return value.encode()+b'\0'
    if kind=='utf16': return value.encode('utf-16-le')+b'\0\0'
    raise ValueError(f'unsupported patch type {kind!r}')


def compile_patches(xml, names, app_version, segments):
    found={}
    for meta in ET.parse(xml).getroot().iter('Metadata'):
        if meta.get('Name') in names and meta.get('AppVer')==app_version and meta.get('AppElf','eboot.bin')=='eboot.bin':
            found[meta.get('Name')]=meta
    missing=[n for n in names if n not in found]
    if missing: raise ValueError(f'patches not found for app version {app_version}: {missing}')
    writes=[]
    for name in names:
        for line in found[name].iter('Line'):
            offset=int(line.get('Address'),0)-EBOOT_BASE
            data=encode(line)
            if not any(start<=offset and offset+len(data)<=end for start,end in segments):
                raise ValueError(f'{name}: address {line.get("Address")} is outside the eboot')
            writes.append((offset,data))
    return writes




def external_selection(found, config):
    """Selected external patches: patches.json {"enabled": [...], "disabled": [...]} overrides
    each file's isEnabled."""
    settings={}
    if config and Path(config).is_file():
        settings=json.loads(Path(config).read_text(encoding='utf-8'))
    enabled,disabled=set(settings.get('enabled',[])),set(settings.get('disabled',[]))
    return [(key,path,meta) for key,path,meta in found
            if key in enabled or (key not in disabled and meta.get('isEnabled','false').lower()=='true')]


def compile_external(selected, segments):
    """Writes of the selected external patches; a patch with unsupported lines is skipped whole."""
    writes=[]
    for key,_,meta in selected:
        try:
            ours=[]
            for line in meta.iter('Line'):
                offset=int(line.get('Address') or '',0)-EBOOT_BASE
                data=encode(line)
                if not any(start<=offset and offset+len(data)<=end for start,end in segments):
                    raise ValueError(f'address {line.get("Address")} is outside the eboot')
                ours.append((offset,data))
        except ValueError as error:
            print(f'Patches: skipped {key}: {error}',file=sys.stderr)
            continue
        writes+=ours
        print(f'Patches: external {key} ({len(ours)} writes)')
    return writes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game-dir', type=Path, default=Path(os.environ.get('BB_GAME_DIR', '../CUSA03694')))
    p.add_argument('--out', type=Path, default=BUILTIN_XML.parent.parent / 'out')
    p.add_argument('--fps', choices=FPS_PRESETS, default='60')
    p.add_argument('--extra', default='')
    p.add_argument('--patches-dir', type=Path)
    p.add_argument('--patches-config', type=Path)
    # Accepted for existing command-line integrations; settings never select executable offsets.
    p.add_argument('--settings', type=Path)
    p.add_argument('--render-res', default='')
    p.add_argument('--output-res', default='')
    p.add_argument('--print-scaled', action='store_true')
    p.add_argument('--print-preset-size', action='store_true')
    a = p.parse_args()
    if a.render_res:
        p.error('Gravity Rush has no verified render-resolution patch; remove BB_RENDER_RES')
    if a.print_scaled or a.print_preset_size:
        return
    a.out.mkdir(parents=True, exist_ok=True)
    target = a.out / 'patches.bin'
    write_patches(target, [])  # Never reuse a previous game's executable writes.
    try:
        values = metadata(a.game_dir)
    except (OSError, ValueError):
        print('Patches: missing game metadata; none applied')
        return
    profile = identify(values)
    version, title = values.get('APP_VER'), values.get('TITLE_ID')
    if profile is None or not version or not title:
        print('Patches: unsupported title/version metadata; none applied')
        return
    segments = eboot_segments((a.out / 'eboot.elf').read_bytes())
    names = []
    if profile == GRAVITY2 and version == APP_VERSION:
        names = FPS_PRESETS[a.fps] + [n.strip() for n in a.extra.split(';') if n.strip()]
    elif a.extra:
        p.error('No bundled patches exist for this game/version')
    writes = compile_patches(BUILTIN_XML, names, version, segments) if names else []
    if a.patches_dir:
        selected = external_selection(external_patches(a.patches_dir, version, title_ids={title}),
                                      a.patches_config)
        writes += compile_external(selected, segments)
    write_patches(target, writes)
    print(f'Patches: {profile.name} {version}: {len(writes)} writes; built-in {names or "none"}')


if __name__ == '__main__':
    main()
