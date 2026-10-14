Gravity Rush for Windows (experimental)
======================================

Targets the PS4 versions of Gravity Rush Remastered and Gravity Rush 2.
No game files are included. Supply your own decrypted dump containing eboot.bin
and matching sce_sys/param.sfo. Gameplay has not been verified on Windows.

Start Gravity Rush.exe, select your game folder, and press PLAY.
Play Gravity Rush.exe uses the last selected folder and FPS setting.
Launcher settings: gravity-launcher.json. Launch log: last_run.log.
The launcher keeps saves and GPU caches under user/<TITLE_ID>/.

The bundled FPS patch is for Gravity Rush 2 update 01.11 only. Remastered uses
its own timing and receives no bundled executable patches. Executable fingerprints
have not been verified; title/version checks cannot detect a modified executable.

This build uses native rendering and offline services. Temporal upscaling,
online multiplayer, direct camera hooks and game-specific effect controls have
been removed. Remove BB_RENDER_RES if it was set by an older configuration.

Requirements: 64-bit Windows 10/11, x86-64 CPU with AVX, BMI1, MOVBE and LZCNT,
and a Vulkan 1.3 graphics driver. macOS and PS Vita game dumps are unsupported.

Build instructions: packaging/windows/README.md in the source checkout.
