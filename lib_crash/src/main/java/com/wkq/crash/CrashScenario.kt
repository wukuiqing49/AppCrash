package com.wkq.crash

import android.os.Handler
import android.os.Looper
import android.util.Log
import java.util.UUID

/** 每次调用只触发一个故障；不接管宿主异常处理器。 */
abstract class CrashScenario internal constructor(val id: String) {
    internal abstract fun causeCrash(): Nothing
    internal open fun prepare() = Unit

    /**
     * 返回运行 ID 仅表示已调度，不代表故障或采集验证通过。
     * 主线程入口始终入队，给调用者留下记录运行 ID 的机会。
     */
    @JvmOverloads
    fun trigger(
        thread: CrashThread = CrashThread.MAIN,
        runId: String = UUID.randomUUID().toString()
    ): String {
        require(runId.isNotBlank()) { "runId must not be blank" }
        // 加载等准备失败直接交给调用者，不伪装成已经调度的测试故障。
        prepare()
        val action = Runnable {
            Log.e("lib_crash", "scenario=$id runId=$runId thread=${Thread.currentThread().name}")
            try {
                causeCrash()
            } catch (failure: Throwable) {
                // 保留真实异常类型与堆栈，并在报告中关联测试 ID。
                failure.addSuppressed(CrashRunMarker(id, runId))
                throw failure
            }
        }
        when (thread) {
            CrashThread.MAIN -> check(Handler(Looper.getMainLooper()).post(action)) {
                "Main looper rejected crash scheduling"
            }
            CrashThread.BACKGROUND -> Thread(action, "lib_crash-$id").start()
        }
        return runId
    }
}

internal class CrashRunMarker(id: String, runId: String) :
    RuntimeException("lib_crash scenario=$id runId=$runId")
