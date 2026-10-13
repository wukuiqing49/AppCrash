package com.wkq.crash

/** Native 场景共用线程调度，具体故障分别在 C++ 文件实现。 */
abstract class NativeCrashScenario internal constructor(
    id: String,
    internal val nativeCode: Int,
    val expectedSignal: String
) : CrashScenario(id) {
    final override fun prepare() = NativeBridge.ensureLoaded()

    final override fun causeCrash(): Nothing {
        NativeBridge.invoke(nativeCode)
        error("Native scenario returned without terminating: $id")
    }
}
