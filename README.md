# lib_crash

Android 崩溃模拟库，库本身无 UI、自动初始化、采集 SDK 或网络依赖；仓库额外提供独立 demo 测试 App。

用于验证宿主 App 的故障触发、崩溃日志与采集报告。当前提供 11 种 Java/Kotlin 异常和 13 种 Native 故障，每种场景独立实现，支持主线程及后台线程。最低 Android API 24；Native 支持 armeabi-v7a、arm64-v8a、x86_64。

## 目录

- [接入](#接入)
- [方法与参数](#方法与参数)
- [调用](#调用)
- [独立场景](#独立场景)
- [Native / SO 版本](#native--so-版本)
- [宿主 R8 混淆](#宿主-r8-混淆)
- [JitPack 发布](#jitpack-发布)
- [配置入口](#配置入口)
- [构建与测试命令](#构建与测试命令)
- [常见问题](#常见问题)
- [测试页面](#测试页面)

## 接入

通过 JitPack 接入公共库，无需 Token 或 GitHub Actions，仓库配置见[JitPack 发布](#jitpack-发布)。宿主 app/build.gradle 添加：

```groovy
dependencies {
    implementation 'com.github.wukuiqing49:AppCrash:1.0.0'
}
```

版本号替换为已经成功发布的版本。宿主 minSdk 至少为 24；使用 AAR 时，宿主不需要安装 NDK/CMake 来重新编译本库。需要编译本库源码时才需要 Native 构建工具。

本地源码接入：宿主 settings.gradle 注册本库目录，例如本库仓库与宿主仓库同级：

```groovy
include ':lib_crash'
project(':lib_crash').projectDir = file('../AppCrash/lib_crash')
```

源码模块引用了 libs 版本目录，因此宿主必须提供本库所需的同名版本、插件及依赖 alias；推荐使用本仓库直接构建 AAR 或 Maven 发布，避免版本目录不一致。

只需 debug 时使用 debugImplementation；需要在 release 中保留时使用 implementation：

```groovy
implementation project(':lib_crash')
```

如果选择 debugImplementation，入口和 import 也须放在 src/debug。release 保留库时，按下方配置让宿主 R8 改写类名；故障仍只由显式调用触发。

## 宿主 R8 混淆

库 AAR 保留 API 名称以供编译，最终 APK/AAB 由宿主统一混淆。将本仓库 `gradle/crash-obfuscation.pro` 复制到宿主 app 模块，按当前 AGP 8.13.2 配置：

```groovy
android {
    buildTypes {
        release {
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'),
                    'proguard-rules.pro', 'crash-obfuscation.pro'
        }
    }
}
```

该文件的 `-repackageclasses` 是应用级全局配置，会改变所有允许重命名的类的包名，宿主应检查已有反射/JNI 的必要 keep 规则。库自带 consumer rules 限制故障方法的优化，允许场景名称混淆；仅 `com.wkq.crash.NativeBridge` 及其 native 方法为 JNI 注册保留稳定名称。不能承诺隐藏这个链接边界。库不向宿主注入全局重打包选项。避免宽泛的 `-keep class com.wkq.crash.** { *; }` 或 `-dontobfuscate`。

效果：未经还原的堆栈可能显示 `o.a.a(SourceFile:...)`，具体名称随构建变化。保留每版 `mapping.txt` 用于排查；上传映射后的崩溃后台可还原原始类名。日志标签、测试 ID 和异常消息字符串不属于类名混淆，仍保留。混淆不隐藏故障行为，也不代表通过商店审核。

可执行 `python scripts/verify_r8.py`，生成仅用于构建验证的临时宿主，检查 unsigned release APK、DEX 类定义和 mapping；不会安装或触发设备故障。结果写入 `build/r8-verification/`。该夹具不加入本项目模块图。

规则分层依据：[Android 库优化说明](https://developer.android.com/topic/performance/app-optimization/library-optimization)；堆栈还原见 [R8 Retrace](https://developer.android.com/tools/retrace)。

## 方法与参数

所有公开调用类型位于 `com.wkq.crash` 包。

| 方法/属性 | 说明 |
| --- | --- |
| CrashUtils.trigger(type, thread, runId): String | 触发 CrashType 指定的 Java/Kotlin 异常，返回本次运行 ID |
| CrashUtils.triggerNative(type, thread, runId): String | 触发 NativeCrashType 指定的 Native 故障，返回本次运行 ID |
| 独立场景.trigger(thread, runId): String | 直接调用某种场景，作用与统一入口相同 |
| CrashType.id / NativeCrashType.id | 稳定的场景 ID，用于标识故障种类 |
| NativeCrashType.expectedSignal | 该场景默认处理链下的预期信号，如 SIGABRT |

| 参数 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- |
| type | 统一入口必填 | 无 | Java/Kotlin 使用 CrashType；Native 使用 NativeCrashType |
| thread | 否 | CrashThread.MAIN | MAIN 通过主线程 Handler 入队；BACKGROUND 创建独立线程 |
| runId | 否 | 自动生成 UUID | 本次运行的关联标识，不能是空白字符串；建议由宿主生成并在调用前持久化 |

`runId` 可以是 `test-001`，但每次运行最好使用唯一值；场景 ID 表示“测什么”，运行 ID 表示“哪一次”。返回值只表示故障已经调度，不能当作故障发生或上报成功的结果。后台线程、以及从后台提交的主线程任务，都可能在调用返回前崩溃。

公开入口是 `trigger()`；`causeCrash()` 属于库内部实现，宿主无需调用。空白 runId、Native 加载/协议失败或调度失败可能同步抛给调用者，属于准备失败；已调度的致命故障不会通过正常方法返回值反馈。

## 调用

下面每个调用应分别执行；触发一次后重启宿主，再执行下一次。

```kotlin
import com.wkq.crash.CrashThread
import com.wkq.crash.CrashType
import com.wkq.crash.CrashUtils
import com.wkq.crash.NativeCrashType
import com.wkq.crash.NullPointerCrash

// 默认主线程，自动生成运行 ID。
CrashUtils.trigger(CrashType.ARRAY_INDEX_OUT_OF_BOUNDS)

// 指定线程和运行 ID；调用前由宿主保存运行 ID。
CrashUtils.trigger(CrashType.NULL_POINTER, CrashThread.BACKGROUND, "null-001")

// Named arguments 也可使用。
CrashUtils.triggerNative(NativeCrashType.ABORT, runId = "native-abort-001")

// 独立场景入口。
NullPointerCrash.trigger(CrashThread.MAIN, "null-main-001")
```

```java
import com.wkq.crash.CrashThread;
import com.wkq.crash.CrashType;
import com.wkq.crash.CrashUtils;
import com.wkq.crash.NativeCrashType;
import com.wkq.crash.NativeAbortCrash;
import com.wkq.crash.NullPointerCrash;

// 统一工具类为静态方法，支持 1/2/3 参数重载。
CrashUtils.trigger(CrashType.ARRAY_INDEX_OUT_OF_BOUNDS);
CrashUtils.trigger(CrashType.NULL_POINTER, CrashThread.BACKGROUND);
CrashUtils.triggerNative(NativeCrashType.ABORT, CrashThread.MAIN, "abort-001");

// Kotlin object 的独立入口通过 INSTANCE 调用。
NullPointerCrash.INSTANCE.trigger(CrashThread.MAIN, "null-001");
NativeAbortCrash.INSTANCE.trigger();
```

## 调度与证据

统一入口通过 CrashType 选择场景，默认在主线程触发，测试 ID 默认自动生成：

```kotlin
CrashUtils.trigger(CrashType.ARRAY_INDEX_OUT_OF_BOUNDS)
CrashUtils.trigger(CrashType.NULL_POINTER, CrashThread.BACKGROUND, "null-001")
```

Java 直接调用静态方法，不需要 INSTANCE：

```java
CrashUtils.trigger(CrashType.ARRAY_INDEX_OUT_OF_BOUNDS);
CrashUtils.trigger(CrashType.NULL_POINTER, CrashThread.BACKGROUND, "null-001");
```

CrashType.id 提供稳定场景 ID。以上示例分别运行，不能在同一次测试中连续触发多个故障。

每种场景是独立的 Kotlin object，支持两种触发线程：

```kotlin
ArrayIndexOutOfBoundsCrash.trigger(CrashThread.MAIN, "array-main-001")
NullPointerCrash.trigger(CrashThread.BACKGROUND, "null-background-001")
```

Java 使用 ArrayIndexOutOfBoundsCrash.INSTANCE.trigger(CrashThread.MAIN, "array-main-001")。

主线程故障通过 Handler 入队；后台故障通过独立 Thread 触发。返回运行 ID 只代表已调度，后台线程可能在调用返回前就崩溃。调用前由宿主持久化自定义运行 ID，便于进程外验证。

库不覆盖宿主异常处理器。是否退出与能否上传取决于宿主处理链；核对 logcat 的 lib_crash 标签、真实异常堆栈及 suppressed 中的运行 ID，再单独核对采集 SDK 的记录。部分 SDK 可能不保留 suppressed 信息，应同时保留日志关联。

## 独立场景

| CrashType | 独立实现类 | 实际操作 / 预期异常 |
| --- | --- | --- |
| RUNTIME_EXCEPTION | RuntimeExceptionCrash | 主动抛出 RuntimeException |
| NULL_POINTER | NullPointerCrash | 对 null 强制解引用，NullPointerException |
| ARRAY_INDEX_OUT_OF_BOUNDS | ArrayIndexOutOfBoundsCrash | 数组下标越界，ArrayIndexOutOfBoundsException |
| LIST_INDEX_OUT_OF_BOUNDS | ListIndexOutOfBoundsCrash | 集合下标越界，IndexOutOfBoundsException 或其子类 |
| STRING_INDEX_OUT_OF_BOUNDS | StringIndexOutOfBoundsCrash | 字符串下标越界，IndexOutOfBoundsException 或其子类 |
| CLASS_CAST | ClassCastCrash | 不合法的类型转换，ClassCastException |
| INTEGER_DIVISION_BY_ZERO | ArithmeticCrash | 运行时整数除零，ArithmeticException |
| NUMBER_FORMAT | NumberFormatCrash | 不合法的数字解析，NumberFormatException |
| ILLEGAL_ARGUMENT | IllegalArgumentCrash | 参数检查失败，IllegalArgumentException |
| ILLEGAL_STATE | IllegalStateCrash | 状态检查失败，IllegalStateException |
| UNINITIALIZED_PROPERTY | UninitializedPropertyCrash | 读取未初始化 lateinit，UninitializedPropertyAccessException |

每次只执行一个故障，重启测试宿主后再测试下一项。无采集 SDK 时只能验证故障触发，不能声称上报通过。ANR、OOM、栈溢出未实现。

## Native / SO 版本

原有 11 种 Java/Kotlin 场景保持独立，新增 13 种 Native 场景。每种都有独立 Kotlin 入口和 C++ 文件，统一打包成 `libcrash_native.so`，通过 JNI 显式调用。

```kotlin
// 以下示例分别执行；每次崩溃后重新启动宿主。
CrashUtils.triggerNative(NativeCrashType.ARRAY_INDEX_OUT_OF_BOUNDS)
CrashUtils.triggerNative(NativeCrashType.NULL_POINTER, CrashThread.BACKGROUND, "native-null-001")
NativeAbortCrash.trigger(CrashThread.MAIN)
```

Java 可直接调用 `CrashUtils.triggerNative(NativeCrashType.ABORT)`，或使用独立入口的 INSTANCE。

| NativeCrashType | 独立实现类（同名 .cpp） | 实际机制 | 默认处理下的信号 |
| --- | --- | --- | --- |
| RUNTIME_EXCEPTION | NativeRuntimeExceptionCrash | 未处理 std::runtime_error | SIGABRT |
| NULL_POINTER | NativeNullPointerCrash | 向空地址写入 | SIGSEGV |
| ARRAY_INDEX_OUT_OF_BOUNDS | NativeArrayIndexOutOfBoundsCrash | 一字节数组越界进入保护页 | SIGSEGV |
| LIST_INDEX_OUT_OF_BOUNDS | NativeListIndexOutOfBoundsCrash | vector.at 越界，未处理 std::out_of_range | SIGABRT |
| STRING_INDEX_OUT_OF_BOUNDS | NativeStringIndexOutOfBoundsCrash | string.at 越界，未处理 std::out_of_range | SIGABRT |
| CLASS_CAST | NativeClassCastCrash | 引用 dynamic_cast 失败，未处理 std::bad_cast | SIGABRT |
| INTEGER_DIVISION_BY_ZERO | NativeArithmeticCrash | 显式 raise(SIGFPE)，模拟算术故障 | SIGFPE |
| NUMBER_FORMAT | NativeNumberFormatCrash | stoi 解析失败，未处理 std::invalid_argument | SIGABRT |
| ILLEGAL_ARGUMENT | NativeIllegalArgumentCrash | 参数检查抛出 std::invalid_argument | SIGABRT |
| ILLEGAL_STATE | NativeIllegalStateCrash | 状态检查抛出 std::logic_error | SIGABRT |
| UNINITIALIZED_PROPERTY | NativeUninitializedPropertyCrash | 空 optional.value，未处理 std::bad_optional_access | SIGABRT |
| ABORT | NativeAbortCrash | 显式 abort() | SIGABRT |
| SEGMENTATION_FAULT | NativeSegmentationCrash | 写入 PROT_NONE 保护页 | SIGSEGV |

C++ 没有 Kotlin lateinit；这里用受检 optional 访问模拟。C++ 整数除零属于未定义行为，无法保证各 ABI 都产生信号，所以 Native 算术场景明确使用信号模拟，不宣称是真实除零。C++ 异常在 noexcept 的 JNI 调用边界触发终止，不跨 JNI 抛出，也不安装或覆盖宿主的信号/异常处理器。宿主自定义处理器可能改变最终退出行为。

首次显式触发 Native 时加载 so 并检查协议，加载失败同步抛给调用者，不冒充预期的 Native 崩溃。调用前由宿主持久化 runId；Native 信号不会走 Java suppressed 异常标记，需从 `lib_crash` 日志关联运行 ID、线程与 native-entry 编号，再核对 Native 采集记录。

支持 `armeabi-v7a`、`arm64-v8a`、`x86_64`，最低 API 24；不支持 32 位 x86。NDK/CMake 版本在版本目录统一配置。使用静态 libc++，不跨 so 传递 STL 对象；构建输出按 16 KB 对齐，保护页大小运行时查询。AAR 中 so 已剥离调试符号，只导出 JNI_OnLoad；未剥离符号留在本地 `lib_crash/build/intermediates/cxx/`，应随对应版本单独归档以便符号化。仅导出 JNI_OnLoad 不代表所有字符串不可见。

名称可见性边界：NativeBridge 的 JNI 注册名称必须保留；C++ RTTI 也可能包含类型及所在函数名称，例如 NativeClassCastCrash 内的局部多态类型。R8 不处理 so 中的这些字符串，不能保证原始名称全部消失。

Native 机制与调试参考：[JNI](https://developer.android.com/ndk/guides/jni-tips)、[16 KB 页面](https://developer.android.com/guide/practices/page-sizes)、[ndk-stack](https://developer.android.com/ndk/guides/ndk-stack)。

## JitPack 发布

使用 Gradle maven-publish 将 release AAR 安装到 Maven Local，由 JitPack 按 Git 标签构建并托管。仅 lib_crash 发布，demo 不发布。无需上传 AAR、配置 Token 或 GitHub Actions。`jitpack.yml` 指定 JDK 17、接受构建环境 SDK 许可证及库测试/发布命令，NDK/CMake/SDK 版本仍以版本目录为准。

本地验证发布（版本号来自 gradle/libs.versions.toml 的 libCrash）：

```powershell
.\gradlew.bat :lib_crash:testDebugUnitTest :lib_crash:publishReleasePublicationToMavenLocal
```

发布版本时提交源码并推送版本标签：

```powershell
git tag 1.0.0
git push origin main
git push origin 1.0.0
```

访问 [JitPack 项目页面](https://jitpack.io/#wukuiqing49/AppCrash)，选择标签并点击 Get it，或请求该版本依赖触发构建。必须等构建成功才能下载。AAR 包含三个 ABI 的 so 与 consumer rules；未剥离 Native 符号留在构建目录，需要自行按版本归档。

更新时修改 libCrash、提交并推送新的标签，例如 1.0.1；调用方同步更新依赖版本。JitPack 构建的版本使用其 VERSION 环境变量与标签一致。不要移动已发布标签。旧 GitHub raw Maven 目录已停用，当前坐标不再是 com.wkq:lib-crash。

宿主 settings.gradle 的 dependencyResolutionManagement.repositories 增加：

```groovy
maven {
    url = uri('https://jitpack.io')
    content { includeGroup('com.github.wukuiqing49') }
}
```

宿主模块引用 `implementation 'com.github.wukuiqing49:AppCrash:1.0.0'`。仓库必须为 Public，下载无需 credentials。源码包名仍是 com.wkq.crash，不受 Maven 坐标变化影响。

本机接入可使用 `:lib_crash:publishReleasePublicationToMavenLocal` 配合宿主的 mavenLocal()。发布流程依据 [JitPack Android 文档](https://docs.jitpack.io/android/)。

## 配置入口

| 文件 | 配置内容 |
| --- | --- |
| gradle/libs.versions.toml | 本地默认库版本 libCrash、AGP/Kotlin、compileSdk/minSdk、NDK/CMake、依赖版本 |
| lib_crash/build.gradle | JitPack Maven 坐标、release 发布变体、ABI 与 JNI 构建 |
| jitpack.yml | JitPack 的 JDK 与构建/发布命令，不是 GitHub Actions |
| lib_crash/consumer-rules.pro | AAR 自动传递给宿主的规则，包含 JNI 链接边界保留规则 |
| gradle/crash-obfuscation.pro | 宿主手动选择启用的全局重打包和源码文件名规则 |

## 构建与测试命令

```powershell
.\gradlew.bat :lib_crash:assembleDebug :lib_crash:testDebugUnitTest
python scripts/verify_r8.py --device-apk
python scripts/verify_native_artifacts.py
python -m unittest discover -s scripts -p test_native_verifiers.py
python scripts/verify_native_device.py --serial emulator-5582
```

设备命令必须替换为本次明确选择的测试设备序列号。`--device-apk` 构建使用 debug 签名的独立 verification 变体，启用 R8 并引用 release 库；不是正式签名的发布包。设备脚本逐个启动随机包名的临时宿主，核对日志信号与进程退出，并卸载本轮安装的包；不清空设备日志或覆盖已有包。结果在 `build/native-device/`，固定报告在 `doc/testing/TEST_REPORT.md`。

产物脚本确认 APK 包含全部三个 ABI 的 so，内容与已检查的 AAR 一致，且未压缩并按 16 KB 对齐。设备脚本对八类 C++ 异常额外核对异常类型及诊断信息，区分同为 SIGABRT 的错误；直接信号场景核对运行 ID、线程、编号、信号、退出及没有 C++ 异常终止信息，不等同于已验证符号化堆栈。

JVM 测试只执行非致命验证。Native 已在 Android 16 x86_64 模拟器验证 13 场景 × 2 线程；ARM 设备、16 KB 页面设备及实际采集 SDK 尚未验证。

## 常见问题

| 问题 | 说明与处理 |
| --- | --- |
| 依赖下载出现 404 | 检查仓库是否 Public、标签已推送、坐标大小写正确及 JitPack 构建状态 |
| 推送标签后没有新版本 | 在 JitPack 项目页请求该版本，查看 build.log；首次构建需要等待 |
| 重发同版本失败 | 不覆盖已发布版本；代码更新后创建新的版本标签 |
| Native 出现 UnsatisfiedLinkError | 检查宿主 ABI 过滤及最终 APK 的 lib 目录是否包含 libcrash_native.so；不支持 32 位 x86 |
| 为什么崩溃不是在调用它的 Activity 行号 | Java/Kotlin 错误操作位于独立场景实现中；Native 错误位于 so 中。触发页面是调用入口，不会替换真实故障位置 |
| 能否保证看不到原始类名 | 不能。R8 能改写允许混淆的名称，JNI 边界、RTTI、日志字符串及符号还原都有各自限制 |
| 触发了但没有收到采集报告 | 库只负责故障触发，需分别检查宿主 SDK 的初始化、异常/信号处理链及采集记录；方法返回不证明上报成功 |
| 是否需要申请 Android 权限 | 库没有业务权限要求；宿主采集 SDK 的网络等权限由宿主自行配置 |

最新验证范围和未验证项以 [测试报告](doc/testing/TEST_REPORT.md) 为准，测试设计见 [测试计划](doc/testing/TEST_PLAN.md)。

## 测试页面

`demo` 是独立 Android Application，单向依赖 `lib_crash`，不会进入发布的 AAR。页面提供 Java/Kotlin、Native/SO 模式、全部场景下拉选择、主线程/后台线程、可选运行 ID、触发确认和上次触发记录。默认语言为中文。

```powershell
.\gradlew.bat :demo:assembleDebug
adb -s <设备序列号> install demo/build/outputs/apk/debug/demo-debug.apk
adb -s <设备序列号> shell am start -n com.wkq.crash.demo/.CrashTestActivity
```

选择模式、场景与线程，点击“触发崩溃”并确认。每次仅触发一个故障；崩溃后手动重启 App，可查看调用前保存的场景和运行 ID。取消确认不会调度故障。上次触发记录不等同于故障采集成功，仍需核对日志或采集 SDK。

本地设备自动化：

```powershell
python scripts/verify_demo_device.py --serial <设备序列号>
python scripts/verify_demo_device.py --serial <设备序列号> --ui-only
```

脚本构建随机 applicationId 的隔离 Debug APK，通过真实 UI 点击触发和确认，验证 11 × 2 Java/Kotlin、13 × 2 Native 用例及记录持久化；完成后卸载该随机包。不会替换常规 demo 包、清空设备日志或删除其他 App 数据。截图、APK 与结果保存在 `build/demo-device/<运行目录>/`。调试 Intent 参数仅用于预选控件，不能自动触发故障。

`--ui-only` 不触发故障，仅检查模式/场景/线程选择、运行 ID 输入与键盘、确认取消及横屏滚动。页面根布局统一处理系统栏和键盘 Insets，滚动内容裁剪在该区域内。[页面截图](doc/testing/evidence/demo-2026-10-13/crash/page-java.png)

普通 Debug 包名为 `com.wkq.crash.demo`；`-PdemoApplicationId=<包名>` 仅供隔离设备测试。Release 开启 R8，默认生成未签名 APK用于构建验证，不配置正式发布签名。demo 不参与库 Maven 发布，设备测试由本地脚本显式执行。
