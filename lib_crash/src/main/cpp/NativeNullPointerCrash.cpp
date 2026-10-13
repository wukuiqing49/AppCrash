#include "scenarios.h"
#include <cstdint>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeNullPointerCrash() {
    // volatile 地址避免编译期直接折叠空指针操作；实际非法写入。
    volatile std::uintptr_t address = 0;
    *reinterpret_cast<volatile int*>(address) = 1;
    std::abort();
}
}
