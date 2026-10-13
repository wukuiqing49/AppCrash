#include "scenarios.h"
#include <string>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeNumberFormatCrash() {
    (void) std::stoi("not-a-number");
    std::abort();
}
}
