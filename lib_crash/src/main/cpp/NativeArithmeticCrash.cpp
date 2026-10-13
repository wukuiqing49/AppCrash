#include "scenarios.h"
#include <csignal>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeArithmeticCrash() {
    // C++ 除零是未定义行为，不保证跨 ABI 产生信号；显式模拟算术信号。
    std::raise(SIGFPE);
    std::abort();
}
}
