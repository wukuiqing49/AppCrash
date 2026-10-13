package com.wkq.crash

object ArithmeticCrash : CrashScenario("integer-division-by-zero") {
    override fun causeCrash(): Nothing {
        val values = intArrayOf(1, 0)
        values[0] / values[1]
        error("Unexpected division success")
    }
}
