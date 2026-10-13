package com.wkq.crash

object IllegalStateCrash : CrashScenario("illegal-state") {
    override fun causeCrash(): Nothing {
        val initialized = false
        check(initialized) { "Intentional invalid state" }
        error("Unexpected state check success")
    }
}
