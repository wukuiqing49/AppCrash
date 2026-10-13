package com.wkq.crash

import org.junit.Assert.*
import org.junit.Test

class CrashScenariosTest {
    @Test
    fun eachScenarioProducesItsExpectedException() {
        val scenarios = listOf(
            RuntimeExceptionCrash to RuntimeException::class.java,
            NullPointerCrash to NullPointerException::class.java,
            ArrayIndexOutOfBoundsCrash to ArrayIndexOutOfBoundsException::class.java,
            ListIndexOutOfBoundsCrash to IndexOutOfBoundsException::class.java,
            StringIndexOutOfBoundsCrash to IndexOutOfBoundsException::class.java,
            ClassCastCrash to ClassCastException::class.java,
            ArithmeticCrash to ArithmeticException::class.java,
            NumberFormatCrash to NumberFormatException::class.java,
            IllegalArgumentCrash to IllegalArgumentException::class.java,
            IllegalStateCrash to IllegalStateException::class.java,
            UninitializedPropertyCrash to UninitializedPropertyAccessException::class.java
        )
        assertEquals(scenarios.size, scenarios.map { it.first.id }.toSet().size)
        scenarios.forEach { (scenario, expected) ->
            repeat(2) {
                val failure = try { scenario.causeCrash() } catch (error: Throwable) { error }
                assertTrue("${scenario.id}: ${failure.javaClass.name}", expected.isInstance(failure))
                assertTrue("Missing scenario stack frame", failure.stackTrace.any {
                    it.className == scenario.javaClass.name
                })
            }
        }
    }

    @Test
    fun blankRunIdIsRejectedBeforeScheduling() {
        for (thread in CrashThread.entries) {
            try {
                RuntimeExceptionCrash.trigger(thread, " ")
                fail("Blank ID accepted")
            } catch (error: IllegalArgumentException) {
                assertEquals("runId must not be blank", error.message)
            }
        }
    }
}
