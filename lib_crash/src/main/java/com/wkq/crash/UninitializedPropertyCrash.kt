package com.wkq.crash

object UninitializedPropertyCrash : CrashScenario("uninitialized-lateinit-property") {
    override fun causeCrash(): Nothing {
        val holder = Holder()
        holder.value.length
        error("Unexpected property access success")
    }

    private class Holder { lateinit var value: String }
}
