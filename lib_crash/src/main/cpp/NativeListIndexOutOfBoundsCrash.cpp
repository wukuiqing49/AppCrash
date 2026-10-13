#include "scenarios.h"
#include <vector>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeListIndexOutOfBoundsCrash() {
    std::vector<int> values{1};
    (void) values.at(values.size());
    std::abort();
}
}
