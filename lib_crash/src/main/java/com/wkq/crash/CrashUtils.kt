package com.wkq.crash

import java.util.UUID

/** Kotlin 与 Java 均可直接使用的统一入口，每次只调度一种故障。 */
object CrashUtils {
    /** 返回运行 ID 仅表示已调度，异常不会在这里捕获或吞掉。 */
    @JvmStatic
    @JvmOverloads
    fun trigger(
        type: CrashType,
        thread: CrashThread = CrashThread.MAIN,
        runId: String = UUID.randomUUID().toString()
    ): String = type.scenario.trigger(thread, runId)

    /** Native 入口；发生的是信号/C++ 终止，不是 Java 异常。 */
    @JvmStatic
    @JvmOverloads
    fun triggerNative(
        type: NativeCrashType,
        thread: CrashThread = CrashThread.MAIN,
        runId: String = UUID.randomUUID().toString()
    ): String = type.scenario.trigger(thread, runId)
}
