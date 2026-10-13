#include "scenarios.h"
#include <stdexcept>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeRuntimeExceptionCrash() {
    throw std::runtime_error("Intentional native runtime exception");
}
}
