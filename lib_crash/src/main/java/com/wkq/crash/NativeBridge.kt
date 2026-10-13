package com.wkq.crash

/** 仅此 JNI 链接边界保留名称；首次显式调用 Native 场景时加载。 */
internal object NativeBridge {
    init { System.loadLibrary("crash_native") }

    fun ensureLoaded() {
        check(protocolVersion() == 1) { "Incompatible libcrash_native.so" }
    }

    external fun invoke(code: Int)
    private external fun protocolVersion(): Int
}
