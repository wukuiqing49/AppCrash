#include "scenarios.h"
#include <string>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeStringIndexOutOfBoundsCrash() {
    const std::string value = "crash";
    (void) value.at(value.size());
    std::abort();
}
}
