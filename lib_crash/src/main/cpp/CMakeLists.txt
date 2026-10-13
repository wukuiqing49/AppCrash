cmake_minimum_required(VERSION 3.22)
project(crash_native LANGUAGES CXX)
add_library(crash_native SHARED
    native_bridge.cpp
    NativeRuntimeExceptionCrash.cpp
    NativeNullPointerCrash.cpp
    NativeArrayIndexOutOfBoundsCrash.cpp
    NativeListIndexOutOfBoundsCrash.cpp
    NativeStringIndexOutOfBoundsCrash.cpp
    NativeClassCastCrash.cpp
    NativeArithmeticCrash.cpp
    NativeNumberFormatCrash.cpp
    NativeIllegalArgumentCrash.cpp
    NativeIllegalStateCrash.cpp
    NativeUninitializedPropertyCrash.cpp
    NativeAbortCrash.cpp
    NativeSegmentationCrash.cpp
)
target_compile_features(crash_native PRIVATE cxx_std_17)
target_compile_options(crash_native PRIVATE
    -fexceptions -frtti -fvisibility=hidden -fvisibility-inlines-hidden
    -fno-omit-frame-pointer -fno-optimize-sibling-calls -Wall -Wextra -Werror
)
target_link_options(crash_native PRIVATE
    "-Wl,--version-script=${CMAKE_CURRENT_SOURCE_DIR}/native.exports"
    "-Wl,-z,max-page-size=16384"
)
set_target_properties(crash_native PROPERTIES
    LINK_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/native.exports"
)
target_link_libraries(crash_native PRIVATE log)
