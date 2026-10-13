# 故障测试依赖真实错误操作：禁止优化场景方法，避免折叠、内联或改写故障点。
# 仍允许移除未使用场景和混淆名称，不保留原始包名、类名及方法名。
-keep,allowshrinking,allowobfuscation class com.wkq.crash.* extends com.wkq.crash.CrashScenario {
    *** causeCrash*(...);
}

# JNI_OnLoad 通过精确类名和方法签名注册，必须保留这个最小链接边界。
# 不能用 allowobfuscation，否则 release 下 RegisterNatives 会失败。
-keep,allowoptimization class com.wkq.crash.NativeBridge {
    native <methods>;
}
