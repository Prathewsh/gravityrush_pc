// SPDX-License-Identifier: GPL-2.0-or-later
#include "common/elf_info.h"
namespace Core {
class Emulator {
public:
    static void SetGame(const char* app0, const char* serial, const char* title, const char* version) {
        auto& info = Common::ElfInfo::Instance();
        info.game_serial = serial ? serial : "";
        info.title = title ? title : "";
        info.app_ver = version ? version : "";
        info.game_folder = app0 ? app0 : "";
        info.initialized = true;
    }
};
}
extern "C" void bbgpu_configure_game(const char* app0, const char* serial, const char* title,
                                     const char* version) {
    Core::Emulator::SetGame(app0, serial, title, version);
}
