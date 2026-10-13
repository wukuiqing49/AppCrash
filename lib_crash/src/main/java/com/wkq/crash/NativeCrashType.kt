package com.wkq.crash

/** Native 类型与 Java/Kotlin 类型分开，避免混淆实际故障语义。 */
enum class NativeCrashType(internal val scenario: NativeCrashScenario) {
    RUNTIME_EXCEPTION(NativeRuntimeExceptionCrash),
    NULL_POINTER(NativeNullPointerCrash),
    ARRAY_INDEX_OUT_OF_BOUNDS(NativeArrayIndexOutOfBoundsCrash),
    LIST_INDEX_OUT_OF_BOUNDS(NativeListIndexOutOfBoundsCrash),
    STRING_INDEX_OUT_OF_BOUNDS(NativeStringIndexOutOfBoundsCrash),
    CLASS_CAST(NativeClassCastCrash),
    INTEGER_DIVISION_BY_ZERO(NativeArithmeticCrash),
    NUMBER_FORMAT(NativeNumberFormatCrash),
    ILLEGAL_ARGUMENT(NativeIllegalArgumentCrash),
    ILLEGAL_STATE(NativeIllegalStateCrash),
    UNINITIALIZED_PROPERTY(NativeUninitializedPropertyCrash),
    ABORT(NativeAbortCrash),
    SEGMENTATION_FAULT(NativeSegmentationCrash);

    val id: String get() = scenario.id
    val expectedSignal: String get() = scenario.expectedSignal
}
