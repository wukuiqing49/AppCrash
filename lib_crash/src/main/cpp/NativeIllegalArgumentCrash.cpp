#include "scenarios.h"
#include <stdexcept>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeIllegalArgumentCrash() {
    const int input = -1;
    if (input < 0) throw std::invalid_argument("Intentional negative argument");
    std::abort();
}
}
