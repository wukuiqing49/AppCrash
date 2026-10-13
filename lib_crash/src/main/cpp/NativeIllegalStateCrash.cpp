#include "scenarios.h"
#include <stdexcept>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeIllegalStateCrash() {
    const bool initialized = false;
    if (!initialized) throw std::logic_error("Intentional invalid state");
    std::abort();
}
}
