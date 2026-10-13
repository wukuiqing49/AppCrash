# lib_crash 测试计划

## 环境与入口

- JDK 17、Gradle 9.1.0、AGP 8.13.2、Kotlin 2.1.21、compileSdk 36、minSdk 24、NDK 27.0.12077973、CMake 3.22.1。
- 模块为 lib_crash 与用户授权的 demo 单页测试 App；临时 R8 夹具提供额外隔离设备测试包，不加入模块图。库命名空间 com.wkq.crash。
- 命令：`./gradlew.bat :lib_crash:assembleDebug :lib_crash:testDebugUnitTest`。
- 首次实现测试全部场景；共享 CrashScenario 修改后所有场景均需回归。
- 源码：`lib_crash/src/main/java/com/wkq/crash/`，每个场景一个独立文件；JVM 用例位于 `lib_crash/src/test/java/com/wkq/crash/CrashScenariosTest.kt`。

## 功能用例与影响关系

| ID | 场景类 | JVM 预期异常 |
| --- | --- | --- |
| runtime-exception | RuntimeExceptionCrash | RuntimeException |
| null-pointer | NullPointerCrash | NullPointerException |
| array-index-out-of-bounds | ArrayIndexOutOfBoundsCrash | ArrayIndexOutOfBoundsException |
| list-index-out-of-bounds | ListIndexOutOfBoundsCrash | IndexOutOfBoundsException 或子类 |
| string-index-out-of-bounds | StringIndexOutOfBoundsCrash | IndexOutOfBoundsException 或子类 |
| class-cast | ClassCastCrash | ClassCastException |
| integer-division-by-zero | ArithmeticCrash | ArithmeticException |
| number-format | NumberFormatCrash | NumberFormatException |
| illegal-argument | IllegalArgumentCrash | IllegalArgumentException |
| illegal-state | IllegalStateCrash | IllegalStateException |
| uninitialized-lateinit-property | UninitializedPropertyCrash | UninitializedPropertyAccessException |
| blank-run-id | CrashScenario.trigger | 两种线程配置均在调度前拒绝空白 ID |

上述 11 个故障各在 JVM 直接执行两次，断言类型与场景堆栈，并检查 ID 唯一；不在 JVM runner 中调度致命线程。

## 设备与集成用例

- `unified-type-mapping`：CrashType 与全部 11 个独立场景一一对应，ID 唯一；修改枚举、工具类或场景列表时回归。
- `unified-blank-run-id`：CrashUtils 对每种类型、两种线程拒绝空白 ID，不调度致命故障。
- `unified-java-overloads`：验证 Java 静态入口及 1/2/3 参数重载。
- 上述 JVM 用例位于 `lib_crash/src/test/java/com/wkq/crash/CrashUtilsTest.kt`；统一入口真实线程行为仍属于设备用例。
- `native-types`、`native-blank-id`、`native-java-overloads`：NativeCrashTypesTest 验证 11 个原场景都有 native 类型，13 个协议码唯一、信号映射完整、空白 ID 在加载 so 前被拒绝，以及 Java 静态重载。

- 每个故障增加 `<ID>-main`、`<ID>-background` 两个设备用例，操作前持久化运行 ID；断言线程、堆栈与进程行为。共享依赖 CrashScenario、宿主异常处理器与 Android Looper。
- `<ID>-capture`：核对宿主采集记录及关联 ID，采集 SDK 未指定时未执行。
- `release-obfuscation`：执行 `python scripts/verify_r8.py`，临时宿主使用 implementation 引用库，检查 11 个 Java 场景仍在 DEX，原始场景名称和源码文件名改写，AAR 正确携带 consumer rules。仅 NativeBridge 允许保留原名以便 JNI 注册。加 `--device-apk` 构建启用 R8、debug 签名的 verification 变体并引用 release 库；不是生产签名包。
- `native-artifacts`：`python scripts/verify_native_artifacts.py` 检查 release AAR 的 arm64-v8a/armeabi-v7a/x86_64 so、ELF 16 KB 对齐、APK 未压缩 so 的 ZIP 16 KB 对齐，且动态导出只有 JNI_OnLoad。
- `native-<TYPE>-main/background`：`python scripts/verify_native_device.py --serial <明确选择的测试设备>`；13 类型各两线程，明确 case 编号、日志 runId、线程、预期信号及退出，单次只触发一个。名称与机制见 README Native 表，源码为各 `lib_crash/src/main/cpp/Native*Crash.cpp`，上游依赖为 NativeBridge、CMake 配置、CrashScenario、R8 规则。跨机读取测试报告后重新确认设备，不能复用设备通过结论。
- 用户已确认 release 保留库，业务宿主仍需按自己的规则验收最终 APK/AAB 与 Native 采集 SDK。设备脚本只安装事先不存在的随机夹具包，执行后仅清理该包，不清日志和用户数据。
- 前置：专用或明确指定的测试宿主，每次只执行一个故障，由外部工具获取证据并重启再测下一项。不清除用户数据、不接管宿主处理器。
- 当前 Native 已在 Android 16 x86_64、4 KB 页面模拟器验证。ARM 真机、16 KB 页面设备、业务宿主及其采集 SDK/正式产物暂未验证；Java/Kotlin 场景现阶段为 JVM 直接异常验证。

## 验收脚本回归

- `python -m unittest discover -s scripts -p test_native_verifiers.py`：检查有效 APK、so 全部/部分缺失、内容被替换、重复 ZIP 条目、压缩及未对齐；检查正确异常、通用 abort、错误异常类型/诊断、错误 runId/线程/编号，以及直接信号场景混入 C++ 异常。
- `native-artifacts` 还须核对 APK 的三个 ABI 与 AAR 字节一致；R8 夹具状态必须已通过。
- `native-device` 对八类 C++ 异常核对类型和诊断信息；其余五类直接信号场景不宣称完成符号化堆栈验证。历史日志重放与设备重新执行分别记录。

## JitPack 发布验证

- `:lib_crash:testDebugUnitTest :lib_crash:publishReleasePublicationToMavenLocal`：检查 JitPack 所需本地发布，不使用 Actions 或 Token。
- 发布坐标 `com.github.wukuiqing49:AppCrash:<标签>`；本地默认版本为 libCrash，JitPack 使用 VERSION 环境变量。
- 验证 POM/AAR/Gradle metadata、三个 ABI、consumer rules。标签推送后请求 JitPack 构建，再执行匿名 Gradle 远程依赖解析，不由本地发布推断云端成功。

## 功能边界

demo 只实现用户授权的崩溃测试页面，不开发其他产品 UI、采集或上报服务。ANR、OOM 与栈溢出不在本期范围。
最新结果：`doc/testing/TEST_REPORT.md`；逐项基线：`doc/testing/TEST_BASELINE.json`。

## 测试页面与设备验收

- `:demo:assembleDebug :demo:assembleRelease :lib_crash:testDebugUnitTest`：检查 XML/ViewBinding、测试 App 的 manifest/API 36、release R8 与库 JVM 回归。
- `demo-startup-mode-thread-cancel`：启动不崩溃；模式/线程可切换；取消确认后进程继续运行，且没有写入本次故障记录。
- `demo-java-<TYPE>-main/background`：11 种异常 × 2 线程；调试 Intent 仅预选控件，外部脚本实际点击触发与确认，核对异常类型、场景 causeCrash 堆栈、运行 ID、线程和退出。
- `demo-native-<TYPE>-main/background`：13 种 Native × 2 线程；核对编号、类型/诊断信息（C++ 异常场景）、信号和退出。
- 每项核对进程故障后持久化的运行 ID 与场景 ID；最后重新启动页面，验证上次触发记录可见。
- `python scripts/verify_demo_device.py --serial <selected-device>`：构建并安装本次随机包名，拒绝覆盖现有包，完成后仅卸载此包；不接触其他设备，不清日志或用户数据。证据在 build/demo-device/<run>/，关键证据另行归档。
- 默认中文页面；主布局由唯一 root 处理系统栏 Insets，通过滚动适应内容。小屏幕、字体放大和横屏按实际设备截图验收，不由编译通过推断。
- `--ui-only`：不触发崩溃，实际选择下拉场景、编辑运行 ID、打开/关闭键盘，横屏下滚动到触发按钮并取消确认；截图检查系统栏裁剪与图标对比度。
