package com.wkq.crash

/** SIGABRT；具体行为参见 README 的 Native 场景表。 */
object NativeUninitializedPropertyCrash : NativeCrashScenario("native-uninitialized-property", 11, "SIGABRT")
