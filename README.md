# <img src="launcher/gravity.ico" width="36" height="36" alt="Gravity Rush Icon" valign="middle"> Gravity Rush for Windows

**Experimental native runtime for Gravity Rush Remastered and Gravity Rush 2 on Windows 10 and 11.**
This is a focused fork of [Supermedo's](https://github.com/Supermedo) PC port project.

The runtime is designed to execute PS4 x86-64 code natively and translate graphics to Vulkan.
The Gravity Rush-only cleanup is complete, but the runtime remains experimental:
neither game's playability has been verified.
The launcher (`Gravity Rush.exe` / `bbport_launcher_win.py`) selects your game folder and starts
the preparation and runtime pipeline.

> **No game files are included.** You need your own decrypted PS4 dump of either game:
> Gravity Rush Remastered (regional CUSA01113/CUSA01130 releases) or Gravity Rush 2
> (CUSA00547, CUSA03694, CUSA04934, or CUSA04943). Gravity Rush 2 patches target update 01.11.
> Optional: `libSceNgs2.sprx` from `/system/common/lib/` of your console placed in `system_lib/` for audio.
> This project is not affiliated with Sony Interactive Entertainment or SIE Japan Studio.

## Implemented features

- **Small offline Tkinter launcher** for selecting either target game and starting it.
- **Separate saves and GPU caches** under `user/<TITLE_ID>/` when launched through the launcher.
- **Motion sensor & gyro support:** Native DualSense/DualShock 4 gyro with complementary filter orientation, or simulated tilt (`T`/`G` keys or left stick in sensor mode) and shake (`Y` or Cross/A).
- **Expanded memory mapping:** Fixed 0x700000000–0x800000000 system-reserved window handling for Gnm GPU rings and buffers.
- **Native Vulkan rendering** with controller and keyboard/mouse input.
- **Gravity Rush 2 01.11 FPS patch** included. Gravity Rush Remastered uses its own game timing.
- **Controller and keyboard & mouse support** with custom remapping and multi-controller detection.
- **Loose asset mods** in `mods/<mod-name>/app0/<game-relative-path>`, without changing original game files.

## Requirements

- Windows 10 (1903 or later) or Windows 11, 64-bit
- An Intel Core 4th generation (Haswell, 2013) or newer, or an AMD Ryzen (AVX, BMI1, MOVBE, LZCNT support required)
- A graphics card with Vulkan 1.3 and a current driver
- About 8 GB of free memory (RAM plus page file)

## Launching a build

1. Build and package the runtime using the [Windows instructions](packaging/windows/README.md),
   or unpack an available build of this fork.
2. (Optional for audio) Copy `libSceNgs2.sprx` from your PS4 console to `system_lib/`.
3. Start `Gravity Rush.exe` (or `python3 launcher/bbport_launcher_win.py`).
4. Choose a decrypted PS4 game folder containing `eboot.bin` and `sce_sys/param.sfo`.
5. Press **PLAY**. The log is saved to `last_run.log`. Controller input is automatic;
   keyboard/mouse bindings are stored in `input.ini`.

`Play Gravity Rush.exe` starts the last selected game with the saved settings.
The launcher stores its configuration in `gravity-launcher.json`. Existing saves from
older layouts are not automatically migrated. `BB_DATA_DIR` overrides the data directory.

## Current compatibility limits

The launcher recognizes Gravity Rush 2 by its listed title IDs. Remastered is recognized by
CUSA01130 or a regional dump's display title (`Gravity Rush Remastered` / `Gravity Daze Remastered`).
Gravity Rush 2 bundled executable patches are limited to update 01.11; other versions run
without those patches. `BB_FPS=30` disables the bundled FPS patch.
Gravity Rush Remastered is prepared without bundled executable patches.

The runtime uses native rendering and offline services. The inherited co-op stack,
temporal upscaler integration (FSR/DLSS/TAA), direct camera hooks, save-file hacks,
language-file rewrites, and legacy effect/cheat controls have been removed.
`BB_RENDER_RES` is unsupported; remove it from older configurations.

Title/version checks do not verify executable fingerprints. A matching clean dump is needed.
PS Vita dumps and macOS runtime execution are unsupported.

## Latest verification — 2026-10-15

- Python suite: **130 tests run — 79 passed, 51 skipped**.
- Three standalone C++ checks passed: command-buffer ownership, motion-history utilities,
  and UI-composition utilities. These do not verify in-game rendering.
- Shell syntax, settings C++ syntax, and Git whitespace checks passed.
- Full native build: **not verified**. CMake configuration stopped because Vulkan headers
  and libraries are missing from the macOS development environment.
- Windows gameplay: **not verified** for either game.

Run the Python checks with:

```bash
python3 -m unittest discover -s tests
```

Skipped checks require native binaries, game data, or a particular host platform.
The regression suite covers title recognition, FPS patch isolation, save/cache separation,
mod overlays, and launcher preparation; passing it does not establish playability.

## Building from source

See [Windows build and packaging instructions](packaging/windows/README.md).
The remaining dependencies provide PS4 execution, Vulkan rendering, audio, input and the
offline launcher. The former co-op stack, temporal upscaler integration and GTK launcher
dependencies have been removed. Historical source attribution is retained in generic
shared code; it does not enable support for other games.

## Issues

If you encounter crashes, graphical glitches, or input problems:

- Check existing issues before opening a new one.
- When opening a new issue, include your hardware specifications (CPU, GPU, driver version), Windows version, game Title ID/version, and any log output or error messages.

## Contributing

Contributions and pull requests are welcome:

- Fork the repository and create a branch for your fix or feature.
- Run regression tests (`python3 -m unittest discover -s tests`) before submitting.
- Keep pull requests focused and provide a clear description of changes.

## Testers welcome

Playtesters and compatibility reports are greatly appreciated:

- Test with your own decrypted dumps of Gravity Rush Remastered or Gravity Rush 2 (01.11).
- Report performance, graphical fidelity, audio status, and controller/gyro responsiveness across different hardware setups.
- Share logs and crash details to help narrow down compatibility edge cases.

## Credits

- Built on the native PC port base by [Supermedo](https://github.com/Supermedo) and [deadinside28](https://github.com/deadinside28).
- Insights and fixes adapted from [HayatoG/gr2_pc](https://github.com/HayatoG/gr2_pc) (system reservation, motion sensor, and geometry pipeline findings).
- Powered by the [shadPS4](https://github.com/shadps4-emu/shadPS4) renderer and translation layers.
- Thanks to the contributors and upstream projects including [SDL3](https://github.com/libsdl-org/SDL), [Dear ImGui](https://github.com/ocornut/imgui), and the PlayStation 4 homebrew/emulation community.

## License

GNU GPL v2 or later ([LICENSE](LICENSE)). Third-party components keep their own licenses.
