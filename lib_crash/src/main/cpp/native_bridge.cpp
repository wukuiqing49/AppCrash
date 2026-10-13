#include <jni.h>
#include <android/log.h>
#include "scenarios.h"

namespace {
// noexcept 让未处理的 C++ 异常在原生边界终止，不越过 JNI 边界。
void invoke(JNIEnv* env, jobject, jint code) noexcept {
    __android_log_print(ANDROID_LOG_ERROR, "lib_crash", "native-entry code=%d", code);
    switch (code) {
        case 1: crash_scenarios::NativeRuntimeExceptionCrash();
        case 2: crash_scenarios::NativeNullPointerCrash();
        case 3: crash_scenarios::NativeArrayIndexOutOfBoundsCrash();
        case 4: crash_scenarios::NativeListIndexOutOfBoundsCrash();
        case 5: crash_scenarios::NativeStringIndexOutOfBoundsCrash();
        case 6: crash_scenarios::NativeClassCastCrash();
        case 7: crash_scenarios::NativeArithmeticCrash();
        case 8: crash_scenarios::NativeNumberFormatCrash();
        case 9: crash_scenarios::NativeIllegalArgumentCrash();
        case 10: crash_scenarios::NativeIllegalStateCrash();
        case 11: crash_scenarios::NativeUninitializedPropertyCrash();
        case 12: crash_scenarios::NativeAbortCrash();
        case 13: crash_scenarios::NativeSegmentationCrash();
        default:
            if (jclass exception = env->FindClass("java/lang/IllegalArgumentException")) {
                env->ThrowNew(exception, "Unknown native crash code");
                env->DeleteLocalRef(exception);
            }
    }
}

jint protocol_version(JNIEnv*, jobject) { return 1; }
}

extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) return JNI_ERR;
    jclass bridge = env->FindClass("com/wkq/crash/NativeBridge");
    if (bridge == nullptr) return JNI_ERR;
    const JNINativeMethod methods[] = {
        {const_cast<char*>("invoke"), const_cast<char*>("(I)V"), reinterpret_cast<void*>(invoke)},
        {const_cast<char*>("protocolVersion"), const_cast<char*>("()I"), reinterpret_cast<void*>(protocol_version)}
    };
    const jint status = env->RegisterNatives(bridge, methods, 2);
    env->DeleteLocalRef(bridge);
    return status == JNI_OK ? JNI_VERSION_1_6 : JNI_ERR;
}
