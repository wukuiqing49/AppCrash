#include "scenarios.h"
#include <optional>
#include <string>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeUninitializedPropertyCrash() {
    // C++ 没有 lateinit，用空 optional 的受检访问模拟未初始化属性。
    const std::optional<std::string> value;
    (void) value.value();
    std::abort();
}
}
