package com.wkq.crash

object NullPointerCrash : CrashScenario("null-pointer") {
    override fun causeCrash(): Nothing {
        val value: String? = null
        return value!!.length.let { error("Unexpected null access success") }
    }
}
