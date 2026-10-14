"""Title identification for the two supported PS4 games; no executable offsets here."""
from dataclasses import dataclass
from pathlib import Path
import re
from prepare import sfo


@dataclass(frozen=True)
class GameProfile:
    key: str
    name: str
    title_ids: frozenset
    patch_version: str | None = None


REMASTERED = GameProfile('remastered', 'Gravity Rush Remastered', frozenset({'CUSA01130'}))
GRAVITY2 = GameProfile('gravity2', 'Gravity Rush 2',
                       frozenset({'CUSA00547', 'CUSA03694', 'CUSA04934', 'CUSA04943'}), '01.11')
PROFILES = (REMASTERED, GRAVITY2)


def metadata(game):
    return sfo((Path(game) / 'sce_sys/param.sfo').read_bytes())


def identify(values):
    serial = values.get('TITLE_ID', '')
    if not isinstance(serial, str) or not re.fullmatch(r'CUSA[0-9]{5}', serial):
        return None
    for profile in PROFILES:
        if serial in profile.title_ids:
            return profile
    # Regional releases can use different serials; accept the game's own display title.
    title = re.sub(r'[^a-z0-9]+', ' ', str(values.get('TITLE', '')).casefold()).strip()
    if title in ('gravity rush remastered', 'gravity daze remastered'):
        return REMASTERED
    return None


def inspect_game(game):
    values = metadata(game)
    profile = identify(values)
    if profile is None:
        raise ValueError('Choose a PS4 Gravity Rush Remastered or Gravity Rush 2 dump '
                         f'(unrecognized title {values.get("TITLE_ID", "unknown")}).')
    if not (Path(game) / 'eboot.bin').is_file():
        raise ValueError('The game folder must contain eboot.bin.')
    return profile, values


def effective_fps(profile, values, requested='60'):
    if requested not in ('30', '60', '90', 'uncap'):
        raise ValueError(f'Unsupported FPS setting: {requested}')
    return requested if profile == GRAVITY2 and values.get('APP_VER') == GRAVITY2.patch_version else '30'


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game', type=Path)
    parser.add_argument('--fps', default='60')
    args = parser.parse_args()
    try:
        profile, values = inspect_game(args.game)
        print(effective_fps(profile, values, args.fps))
    except (OSError, ValueError) as error:
        parser.exit(1, f'Game selection: {error}\n')
