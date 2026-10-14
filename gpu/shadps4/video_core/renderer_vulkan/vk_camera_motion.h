// SPDX-License-Identifier: GPL-2.0-or-later
// No camera-buffer layout has been validated for the Gravity Rush games.
#pragma once
#include <array>
#include "common/types.h"
#include "video_core/texture_cache/image.h"
namespace VideoCore { class TextureCache; }
namespace Vulkan {
class Instance; class Scheduler; class Runtime; class ObjectMotion;
class CameraMotion {
public:
    CameraMotion(const Instance&, Scheduler&, VideoCore::TextureCache&, Runtime&) {}
    bool Enabled() const { return false; }
    bool Ready() const { return false; }
    void SetObjectMotion(ObjectMotion*) {}
    void InvalidateHistory() {}
    void SetJitter(std::array<float, 2>) {}
    VideoCore::ImageId Depth() const { return {}; }
    void OnGBufferPass(VideoCore::ImageId) {}
    void OnDisplayPass(VideoCore::ImageId) {}
};
}
