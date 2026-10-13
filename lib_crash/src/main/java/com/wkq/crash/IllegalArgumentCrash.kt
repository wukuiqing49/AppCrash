package com.wkq.crash

object IllegalArgumentCrash : CrashScenario("illegal-argument") {
    override fun causeCrash(): Nothing {
        val input = -1
        require(input >= 0) { "Intentional invalid argument: $input" }
        error("Unexpected argument check success")
    }
}
