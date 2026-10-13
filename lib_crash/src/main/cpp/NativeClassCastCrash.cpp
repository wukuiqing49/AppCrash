#include "scenarios.h"
#include <typeinfo>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeClassCastCrash() {
    struct Base { virtual ~Base() = default; };
    struct Derived : Base {};
    Base value;
    (void) dynamic_cast<Derived&>(value);
    std::abort();
}
}
