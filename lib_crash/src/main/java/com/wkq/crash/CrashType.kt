package com.wkq.crash

/** 统一入口支持的故障类型，与独立场景一一对应。 */
enum class CrashType(internal val scenario: CrashScenario) {
    RUNTIME_EXCEPTION(RuntimeExceptionCrash),
    NULL_POINTER(NullPointerCrash),
    ARRAY_INDEX_OUT_OF_BOUNDS(ArrayIndexOutOfBoundsCrash),
    LIST_INDEX_OUT_OF_BOUNDS(ListIndexOutOfBoundsCrash),
    STRING_INDEX_OUT_OF_BOUNDS(StringIndexOutOfBoundsCrash),
    CLASS_CAST(ClassCastCrash),
    INTEGER_DIVISION_BY_ZERO(ArithmeticCrash),
    NUMBER_FORMAT(NumberFormatCrash),
    ILLEGAL_ARGUMENT(IllegalArgumentCrash),
    ILLEGAL_STATE(IllegalStateCrash),
    UNINITIALIZED_PROPERTY(UninitializedPropertyCrash);

    val id: String get() = scenario.id
}
