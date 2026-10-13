package com.wkq.crash

import org.junit.Assert.*
import org.junit.Test

class NativeCrashTypesTest {
    @Test
    fun allManagedCasesHaveNativeCounterpartsAndSignals() {
        val expected = mapOf(
            "RUNTIME_EXCEPTION" to "SIGABRT", "NULL_POINTER" to "SIGSEGV",
            "ARRAY_INDEX_OUT_OF_BOUNDS" to "SIGSEGV", "LIST_INDEX_OUT_OF_BOUNDS" to "SIGABRT",
            "STRING_INDEX_OUT_OF_BOUNDS" to "SIGABRT", "CLASS_CAST" to "SIGABRT",
            "INTEGER_DIVISION_BY_ZERO" to "SIGFPE", "NUMBER_FORMAT" to "SIGABRT",
            "ILLEGAL_ARGUMENT" to "SIGABRT", "ILLEGAL_STATE" to "SIGABRT",
            "UNINITIALIZED_PROPERTY" to "SIGABRT", "ABORT" to "SIGABRT",
            "SEGMENTATION_FAULT" to "SIGSEGV"
        )
        assertTrue(NativeCrashType.entries.map { it.name }.containsAll(CrashType.entries.map { it.name }))
        assertEquals(expected, NativeCrashType.entries.associate { it.name to it.expectedSignal })
        assertEquals(13, NativeCrashType.entries.map { it.id }.toSet().size)
        assertEquals((1..13).toSet(), NativeCrashType.entries.map { it.scenario.nativeCode }.toSet())
    }

    @Test
    fun blankIdsFailWithoutLoadingSoOrSchedulingNativeFaults() {
        NativeCrashType.entries.forEach { type ->
            CrashThread.entries.forEach { thread ->
                try {
                    CrashUtils.triggerNative(type, thread, " ")
                    fail("Accepted blank ID for $type/$thread")
                } catch (error: IllegalArgumentException) {
                    assertEquals("runId must not be blank", error.message)
                }
            }
        }
    }

    @Test
    fun nativeEntryHasJavaStaticOverloads() {
        val methods = CrashUtils::class.java.methods.filter { it.name == "triggerNative" }
        assertEquals(setOf(1, 2, 3), methods.map { it.parameterCount }.toSet())
        methods.forEach { assertTrue(java.lang.reflect.Modifier.isStatic(it.modifiers)) }
    }
}
