package com.wkq.crash

object NumberFormatCrash : CrashScenario("number-format") {
    override fun causeCrash(): Nothing {
        "not-a-number".toInt()
        error("Unexpected parsing success")
    }
}
