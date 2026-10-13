#include "scenarios.h"
#include <sys/mman.h>
#include <unistd.h>
#include <stdexcept>
#include <cstdlib>

namespace crash_scenarios {
[[noreturn]] __attribute__((noinline)) void NativeArrayIndexOutOfBoundsCrash() {
    // 一字节数组紧邻保护页，使越界写稳定落入不可访问页。
    const long size = sysconf(_SC_PAGESIZE);
    if (size <= 0) throw std::runtime_error("Cannot query page size");
    const auto page_size = static_cast<size_t>(size);
    void* mapping = mmap(nullptr, page_size * 2, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (mapping == MAP_FAILED) throw std::runtime_error("Guarded array mmap failed");
    auto* bytes = static_cast<unsigned char*>(mapping);
    if (mprotect(bytes + page_size, page_size, PROT_NONE) != 0) {
        munmap(mapping, page_size * 2);
        throw std::runtime_error("Guarded array mprotect failed");
    }
    volatile unsigned char* array = bytes + page_size - 1;
    array[0] = 0;
    array[1] = 1;
    std::abort();
}
}
