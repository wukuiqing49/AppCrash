package com.wkq.crash

object StringIndexOutOfBoundsCrash : CrashScenario("string-index-out-of-bounds") {
    override fun causeCrash(): Nothing {
        val value = "crash"
        value[value.length]
        error("Unexpected string access success")
    }
}
