#include "scenarios.h"
#include <sys/mman.h>
#include <unistd.h>
#include <stdexcept>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeSegmentationCrash() {
    const long size = sysconf(_SC_PAGESIZE);
    if (size <= 0) throw std::runtime_error("Cannot query page size");
    void* mapping = mmap(nullptr, static_cast<size_t>(size), PROT_NONE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mapping == MAP_FAILED) throw std::runtime_error("Protected page mmap failed");
    *static_cast<volatile unsigned char*>(mapping) = 1;
    std::abort();
}
}
