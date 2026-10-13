package com.wkq.crash

/** SIGABRT；具体行为参见 README 的 Native 场景表。 */
object NativeIllegalStateCrash : NativeCrashScenario("native-illegal-state", 10, "SIGABRT")
