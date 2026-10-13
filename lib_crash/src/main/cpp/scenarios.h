#pragma once

namespace crash_scenarios {
[[noreturn]] void NativeRuntimeExceptionCrash();
[[noreturn]] void NativeNullPointerCrash();
[[noreturn]] void NativeArrayIndexOutOfBoundsCrash();
[[noreturn]] void NativeListIndexOutOfBoundsCrash();
[[noreturn]] void NativeStringIndexOutOfBoundsCrash();
[[noreturn]] void NativeClassCastCrash();
[[noreturn]] void NativeArithmeticCrash();
[[noreturn]] void NativeNumberFormatCrash();
[[noreturn]] void NativeIllegalArgumentCrash();
[[noreturn]] void NativeIllegalStateCrash();
[[noreturn]] void NativeUninitializedPropertyCrash();
[[noreturn]] void NativeAbortCrash();
[[noreturn]] void NativeSegmentationCrash();
}
