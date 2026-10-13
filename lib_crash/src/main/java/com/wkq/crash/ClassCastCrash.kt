package com.wkq.crash

object ClassCastCrash : CrashScenario("class-cast") {
    override fun causeCrash(): Nothing {
        val value: Any = 42
        value as String
        error("Unexpected cast success")
    }
}
