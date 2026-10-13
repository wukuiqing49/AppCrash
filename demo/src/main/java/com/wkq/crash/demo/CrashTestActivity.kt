package com.wkq.crash.demo

import android.app.Activity
import android.app.AlertDialog
import android.content.pm.ActivityInfo
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.WindowInsets
import android.view.WindowInsetsController
import android.widget.AdapterView
import android.widget.ArrayAdapter
import com.wkq.crash.CrashThread
import com.wkq.crash.CrashType
import com.wkq.crash.CrashUtils
import com.wkq.crash.NativeCrashType
import com.wkq.crash.demo.databinding.ActivityCrashTestBinding
import java.text.DateFormat
import java.util.Date
import java.util.UUID

class CrashTestActivity : Activity() {
    private lateinit var binding: ActivityCrashTestBinding
    private val preferences by lazy { getSharedPreferences("crash_test", MODE_PRIVATE) }
    private val nativeMode get() = binding.modeGroup.checkedRadioButtonId == R.id.mode_native
    private val thread get() = if (binding.threadGroup.checkedRadioButtonId == R.id.thread_main)
        CrashThread.MAIN else CrashThread.BACKGROUND
    private val index get() = binding.scenario.selectedItemPosition.coerceAtLeast(0)
    private val scenarioId get() = if (nativeMode) NativeCrashType.entries[index].id else CrashType.entries[index].id
    private val expected get() = if (nativeMode) NativeCrashType.entries[index].expectedSignal else JAVA_EXCEPTIONS[index]

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (BuildConfig.DEBUG && intent.getStringExtra("orientation") == "landscape") {
            requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        }
        binding = ActivityCrashTestBinding.inflate(layoutInflater)
        setContentView(binding.root)
        applyInsets()
        binding.modeGroup.setOnCheckedChangeListener { _, _ -> populateScenarios(0) }
        binding.scenario.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(parent: AdapterView<*>?, view: View?, position: Int, id: Long) = updateDetails()
            override fun onNothingSelected(parent: AdapterView<*>?) = Unit
        }
        val restoredNative = savedInstanceState?.getBoolean("native") ?: preferences.getBoolean("native", false)
        binding.modeGroup.check(if (restoredNative) R.id.mode_native else R.id.mode_java)
        populateScenarios(savedInstanceState?.getInt("index") ?: preferences.getInt("index", 0))
        val restoredBackground = savedInstanceState?.getBoolean("background") ?: preferences.getBoolean("background", false)
        binding.threadGroup.check(if (restoredBackground) R.id.thread_background else R.id.thread_main)
        // 调试自动化只能预选控件，必须实际点击并确认才会触发。
        if (BuildConfig.DEBUG && savedInstanceState == null) {
            intent.getStringExtra("mode")?.let { binding.modeGroup.check(if (it == "native") R.id.mode_native else R.id.mode_java) }
            intent.getStringExtra("scenario")?.let { name ->
                val names = if (nativeMode) NativeCrashType.entries.map { it.name } else CrashType.entries.map { it.name }
                val selected = names.indexOf(name)
                if (selected >= 0) binding.scenario.setSelection(selected)
            }
            intent.getStringExtra("thread")?.let { binding.threadGroup.check(if (it == "BACKGROUND") R.id.thread_background else R.id.thread_main) }
            intent.getStringExtra("runId")?.let { binding.runId.setText(it) }
        }
        showLastRun()
        binding.trigger.setOnClickListener {
            val selectedNative = nativeMode
            val selectedIndex = index
            val selectedThread = thread
            AlertDialog.Builder(this)
                .setTitle(R.string.confirm_title)
                .setMessage(getString(R.string.confirm_message, binding.scenario.selectedItem.toString(), threadLabel(selectedThread)))
                .setNegativeButton(R.string.cancel, null)
                .setPositiveButton(R.string.confirm_trigger) { _, _ -> trigger(selectedNative, selectedIndex, selectedThread) }
                .show()
        }
    }

    private fun populateScenarios(selected: Int) {
        val count = if (nativeMode) NativeCrashType.entries.size else CrashType.entries.size
        val names = resources.getStringArray(R.array.scenario_names).take(count)
        binding.scenario.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, names)
        binding.scenario.setSelection(selected.coerceIn(0, count - 1))
        updateDetails()
    }

    private fun updateDetails() {
        binding.scenarioDetails.text = getString(R.string.scenario_details, scenarioId, expected)
    }

    private fun trigger(native: Boolean, selected: Int, selectedThread: CrashThread) {
        val runId = binding.runId.text.toString().trim().ifBlank { "demo-" + UUID.randomUUID() }
        val id = if (native) NativeCrashType.entries[selected].id else CrashType.entries[selected].id
        val saved = preferences.edit().putBoolean("native", native).putInt("index", selected)
            .putBoolean("background", selectedThread == CrashThread.BACKGROUND)
            .putString("scenarioId", id).putString("runId", runId).putLong("time", System.currentTimeMillis()).commit()
        if (!saved) {
            showError(getString(R.string.save_failed))
            return
        }
        showLastRun()
        binding.trigger.isEnabled = false
        try {
            if (native) CrashUtils.triggerNative(NativeCrashType.entries[selected], selectedThread, runId)
            else CrashUtils.trigger(CrashType.entries[selected], selectedThread, runId)
        } catch (failure: Exception) {
            // 只处理同步准备失败；已调度故障由库在对应线程触发。
            binding.trigger.isEnabled = true
            showError(failure.message ?: getString(R.string.unknown_error))
        }
    }

    private fun showLastRun() {
        val runId = preferences.getString("runId", null) ?: return
        binding.lastRun.text = getString(R.string.last_run_details,
            preferences.getString("scenarioId", ""),
            getString(if (preferences.getBoolean("native", false)) R.string.mode_native else R.string.mode_java),
            threadLabel(if (preferences.getBoolean("background", false)) CrashThread.BACKGROUND else CrashThread.MAIN),
            runId, DateFormat.getDateTimeInstance().format(Date(preferences.getLong("time", 0))))
    }

    private fun threadLabel(value: CrashThread) = getString(if (value == CrashThread.MAIN) R.string.thread_main else R.string.thread_background)

    private fun showError(message: String) {
        AlertDialog.Builder(this).setTitle(R.string.prepare_failed).setMessage(message)
            .setPositiveButton(android.R.string.ok, null).show()
    }

    override fun onSaveInstanceState(outState: Bundle) {
        outState.putBoolean("native", nativeMode)
        outState.putInt("index", index)
        outState.putBoolean("background", thread == CrashThread.BACKGROUND)
        super.onSaveInstanceState(outState)
    }

    @Suppress("DEPRECATION")
    override fun onWindowFocusChanged(hasFocus: Boolean) {
        super.onWindowFocusChanged(hasFocus)
        if (!hasFocus) return
        if (Build.VERSION.SDK_INT >= 30) {
            val appearance = WindowInsetsController.APPEARANCE_LIGHT_STATUS_BARS or WindowInsetsController.APPEARANCE_LIGHT_NAVIGATION_BARS
            window.insetsController?.setSystemBarsAppearance(appearance, appearance)
        } else {
            window.decorView.systemUiVisibility = window.decorView.systemUiVisibility or View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
            if (Build.VERSION.SDK_INT >= 26) window.decorView.systemUiVisibility = window.decorView.systemUiVisibility or View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR
        }
    }

    @Suppress("DEPRECATION")
    private fun applyInsets() {
        if (Build.VERSION.SDK_INT >= 30) window.setDecorFitsSystemWindows(false)
        else window.decorView.systemUiVisibility = View.SYSTEM_UI_FLAG_LAYOUT_STABLE or View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN or View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION or View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
        binding.root.setOnApplyWindowInsetsListener { view, insets ->
            if (Build.VERSION.SDK_INT >= 30) {
                val bars = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout() or WindowInsets.Type.ime())
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom)
            } else view.setPadding(insets.systemWindowInsetLeft, insets.systemWindowInsetTop, insets.systemWindowInsetRight, insets.systemWindowInsetBottom)
            insets
        }
        binding.root.requestApplyInsets()
    }

    companion object {
        private val JAVA_EXCEPTIONS = listOf("RuntimeException", "NullPointerException", "ArrayIndexOutOfBoundsException",
            "IndexOutOfBoundsException", "IndexOutOfBoundsException", "ClassCastException", "ArithmeticException",
            "NumberFormatException", "IllegalArgumentException", "IllegalStateException", "UninitializedPropertyAccessException")
    }
}
