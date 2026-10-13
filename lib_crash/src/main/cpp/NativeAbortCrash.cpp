#include "scenarios.h"
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeAbortCrash() {
    std::abort();
}
}
