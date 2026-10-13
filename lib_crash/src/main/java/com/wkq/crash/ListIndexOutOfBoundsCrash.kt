package com.wkq.crash

object ListIndexOutOfBoundsCrash : CrashScenario("list-index-out-of-bounds") {
    override fun causeCrash(): Nothing {
        val values = arrayListOf("one")
        values[values.size]
        error("Unexpected list access success")
    }
}
