package com.wkq.crash

import org.junit.Assert.*
import org.junit.Test

class CrashUtilsTest {
    @Test
    fun typesMapToAllIndependentScenarios() {
        val expected = listOf(
            RuntimeExceptionCrash, NullPointerCrash, ArrayIndexOutOfBoundsCrash,
            ListIndexOutOfBoundsCrash, StringIndexOutOfBoundsCrash, ClassCastCrash,
            ArithmeticCrash, NumberFormatCrash, IllegalArgumentCrash, IllegalStateCrash,
            UninitializedPropertyCrash
        )
        assertEquals(expected.size, CrashType.entries.size)
        CrashType.entries.zip(expected).forEach { (type, scenario) ->
            assertSame(scenario, type.scenario)
            assertEquals(scenario.id, type.id)
        }
        assertEquals(expected.size, CrashType.entries.map { it.id }.toSet().size)
    }

    @Test
    fun unifiedEntryRejectsBlankIdForEveryTypeAndThread() {
        CrashType.entries.forEach { type ->
            CrashThread.entries.forEach { thread ->
                try {
                    CrashUtils.trigger(type, thread, " ")
                    fail("Blank ID accepted: $type/$thread")
                } catch (error: IllegalArgumentException) {
                    assertEquals("runId must not be blank", error.message)
                }
            }
        }
    }

    @Test
    fun javaStaticOverloadsAreAvailable() {
        val methods = CrashUtils::class.java.methods.filter { it.name == "trigger" }
        assertEquals(setOf(1, 2, 3), methods.map { it.parameterCount }.toSet())
        methods.forEach { assertTrue(java.lang.reflect.Modifier.isStatic(it.modifiers)) }
    }
}
