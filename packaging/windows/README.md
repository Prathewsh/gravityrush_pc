# Gravity Rush on Windows

Experimental native runtime for the PS4 versions of Gravity Rush Remastered and
Gravity Rush 2. The runtime still needs a complete Windows build and gameplay
verification. Python test results alone do not establish playability.

## Build

Install MSYS2, open its **CLANG64** shell, and install the dependencies:

```bash
pacman -S --needed git \
  mingw-w64-clang-x86_64-{toolchain,cmake,ninja,pkgconf,python} \
  mingw-w64-clang-x86_64-{vulkan-headers,vulkan-loader,vulkan-memory-allocator,glslang} \
  mingw-w64-clang-x86_64-{sdl3,fmt,boost,robin-map,xxhash,ffmpeg,zydis} \
  mingw-w64-clang-x86_64-{spirv-tools,spirv-headers}
git submodule update --init --recursive
bash build.sh
```

The remaining submodules supply ImGui, LibAtrac9, magic_enum, miniz and xbyak.
The build no longer needs the removed co-op networking libraries or FSR/DLSS SDKs.

From a source checkout, use Python 3.10 or newer:

```bash
python launcher/bbport_launcher_win.py
# Or launch directly with a selected dump:
BB_GAME_DIR=F:/path/to/CUSA03694 python run.py
```

The launcher requires Tkinter. The game folder must contain `eboot.bin` and
`sce_sys/param.sfo`. Remastered receives no bundled executable patches;
Gravity Rush 2's FPS patch requires update 01.11. `BB_FPS=30` disables that patch.
The display title can identify regional Remastered dumps; CUSA01130 is also
recognized directly by title ID.

## Package

After a successful build, install a Windows Python 3.10+ distribution with Tkinter
(set `WINPYTHON` if it is not found automatically), then run:

```bash
bash packaging/windows/package.sh
```

The script creates `dist/bbport-windows.zip` with `Gravity Rush.exe`,
`Play Gravity Rush.exe`, the runtime and required DLLs. PyInstaller packages
Python and Tkinter; players do not need a separate Python installation.
No game files or system modules are distributed.

Launcher settings are stored in `gravity-launcher.json`, with logs in
`last_run.log`. Launching through the launcher separates saves and GPU caches
under `user/<TITLE_ID>/`. Existing saves are not automatically migrated.
Loose asset mods use `mods/<mod-name>/app0/<game-relative-path>`; original game
files are preserved. Executable and system-module replacements are rejected.

## Verification

```bash
python -m unittest discover -s tests
```

Some tests require built runtime binaries, a matching game dump, or a particular
host platform. A skipped test is not a successful runtime check. Full native
builds target Windows x86-64 or Linux x86-64; macOS is not a runtime target.
