package com.wkq.crash

/** SIGFPE；具体行为参见 README 的 Native 场景表。 */
object NativeArithmeticCrash : NativeCrashScenario("native-integer-division-by-zero", 7, "SIGFPE")
