package com.wkq.crash

object ArrayIndexOutOfBoundsCrash : CrashScenario("array-index-out-of-bounds") {
    override fun causeCrash(): Nothing {
        val values = intArrayOf(1)
        values[values.size]
        error("Unexpected array access success")
    }
}
