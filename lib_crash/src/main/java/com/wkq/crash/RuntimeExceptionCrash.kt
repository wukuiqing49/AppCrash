package com.wkq.crash

object RuntimeExceptionCrash : CrashScenario("runtime-exception") {
    override fun causeCrash(): Nothing {
        throw RuntimeException("Intentional lib_crash runtime exception")
    }
}
