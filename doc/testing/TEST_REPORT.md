# lib_crash 测试报告

## 本轮：改用 JitPack（2026-10-13）

- 按用户指定改用 JitPack；删除旧公共 Maven 文件目录，发布坐标改为 `com.github.wukuiqing49:AppCrash:1.0.0`，源码包名不变。新增 jitpack.yml 指定 JDK 17，仅测试并发布 lib_crash，不发布 demo，不使用 GitHub Actions 或下载 Token。
- `:lib_crash:testDebugUnitTest :lib_crash:publishReleasePublicationToMavenLocal` 本地成功，JVM 测试复用通过输出；新坐标的 AAR/POM/Gradle metadata 已生成。前两次因本机虚拟内存不足未启动 JVM，关闭本项目专用模拟器并以单进程 512 MB 堆重试后成功，没有终止其他项目构建进程。
- 通用 App 构建检查器仍要求不存在的 app 模块，返回 2 错误及 1 提示；本项目为 lib_crash + demo，不适用该固定 App 路径检查。实际 Gradle 发布成功，不据此声称该通用门禁通过。
- 云端构建及匿名下载结果待标签推送后验证；下方 raw Maven 下载方案为历史配置，当前已停用。本轮不修改故障实现，不重复设备崩溃测试。

## 历史：测试页面与无 Token 发布（2026-10-13）

新增独立 `demo` 测试 App，支持 Java/Kotlin 与 Native 场景、主线程/后台线程、运行 ID、确认/取消及崩溃后查看上次记录；不进入库 AAR。新增 `scripts/verify_demo_device.py` 执行实际页面点击、故障判定与随机测试包清理。按最新要求删除发布 Action，移除 GitHub Packages 凭据，仅保留 Gradle maven-publish，将产物生成到仓库根目录 `maven/`。

| 检查 | 状态 | 结果与证据 |
| --- | --- | --- |
| Demo Debug/Release 构建 | 本次通过 | `:demo:assembleDebug :demo:assembleRelease`，最终 Insets 修正后再次构建成功；release 启用 R8，为 unsigned APK |
| JVM 与脚本回归 | 本次通过 | `:lib_crash:testDebugUnitTest` 8 项通过；Python Native 验收脚本 9 项通过 |
| 页面触发真实崩溃 | 本次通过 | Android API 36、x86_64、4096 字节页面模拟器 emulator-5590；11 Java/Kotlin × 2 线程 + 13 Native × 2 线程，共 48 项通过；核对异常/信号、运行 ID、线程与进程退出。[完整结果及逐项日志](evidence/demo-2026-10-13/crash/result.json) |
| 页面交互与重启记录 | 本次通过 | 全量测试覆盖确认、取消与崩溃后记录；最终 Insets 修正后执行 3 项无崩溃 UI 回归，覆盖场景选择、运行 ID 输入/键盘及横屏滚动。[最终 UI 结果及截图](evidence/demo-2026-10-13/ui/result.json) |
| R8 与 Native 打包 | 本次通过 | release mapping 中故障类改名，JNI NativeBridge 保留；重建 AAR 后核对 demo release APK 的三个 ABI so 与 AAR 一致、未压缩及 16 KB ZIP 对齐 |
| 项目约定 | 本次通过 | Agent 结构、架构、UI 与 i18n 检查通过；demo 资源归属与库边界已更新 |
| Gradle 公共目录发布 | 本次通过 | `:lib_crash:publishReleasePublicationToPublicMavenRepository` 成功，生成 1.0.0 的 AAR、POM、Gradle metadata 和校验文件；配置中无认证凭据，已删除发布 workflow |
| 独立消费者解析 | 本次通过 | 临时 Gradle 工程从本地 `maven/` 按坐标解析 `com.wkq:lib-crash:1.0.0` AAR 及 Kotlin stdlib/annotations 传递依赖；`verifyResolution` 成功 |
| 公开远端下载 | 未执行 | 尚未推送生成目录；公共 raw URL 下载须在公共仓库推送后验证，本地解析成功不等于远端可用 |

48 项故障测试发生在最后一轮系统栏/滚动裁切修正前，之后仅修正页面显示并复跑 UI 检查，没有修改故障逻辑。测试夹具安装前确认随机包不存在，结束均卸载成功；未操作连接的真机或其他应用数据。专用模拟器首次启动的 SystemUI 无响应已恢复后再完成测试。

尚未验证 ARM、实际 16 KB 页面设备、真实采集 SDK、放大字体及更多屏幕尺寸。构建仍有 SDK XML 工具版本及 Gradle 弃用提示，不影响本次构建成功。源码未提交，未建立可靠源码指纹，不推进通过基线。下方 GitHub Packages/Actions 记录为历史方案，当前已停用。

## 历史：公共库发布配置修正（2026-10-13）

- 修改 `.github/workflows/publish.yml`，移除私有仓库环境变量与强制检查；版本标签校验、测试流程和发布权限保持有效。
- README 与测试计划改为公共库接入说明；明确 GitHub Maven/Gradle 公共包仍要求 Token，Actions artifact 不作为私有存储。
- 本次通过：工作流 YAML 结构、发布触发及 packages 写权限检查，确认不存在私有仓库门禁；README 结构和文档差异检查。
- 未执行：远端可见性变更、GitHub 云端发布及下载。本轮仅改工作流门禁和文档，不重复库构建及设备测试；沿用下方历史构建证据，不推进基线。

## 历史：GitHub Packages 自动发布配置


新增 `.github/workflows/publish.yml`，修改 lib_crash/build.gradle、gradle/libs.versions.toml、.gitignore 和 README；故障实现及公开调用 API 未修改。

| 检查 | 状态 | 结果 |
| --- | --- | --- |
| 本地 Maven 发布与 JVM | 本次通过 | `:lib_crash:testDebugUnitTest :lib_crash:publishReleasePublicationToMavenLocal`，指定本仓库 build/publication-check 作为本地 Maven 目录；构建退出码 0，8 项 JVM 测试通过 |
| 发布产物 | 本次通过 | 核对 com.wkq:lib-crash:1.0.0 的 POM/AAR/Gradle metadata；三个 ABI、consumer rules 完整 |
| 标签版本覆盖 | 本次通过 | `:lib_crash:generatePomFileForReleasePublication -PpublishVersion=1.0.1`，生成 POM 版本确认为 1.0.1 |
| R8 与 Native 产物 | 本次通过 | `python scripts/verify_r8.py`、`python scripts/verify_native_artifacts.py`，11 场景混淆保留、APK/AAR so 一致、三 ABI 对齐及导出检查通过 |
| 验收脚本回归 | 本次通过 | 9 项 Python 测试通过 |
| 工作流静态检查 | 本次通过 | YAML 可解析，标签和手动输入配置、packages 写权限已核对；未执行 Linux runner |
| 通用 App 构建门禁 | 排除 | 检查器要求 app/build.gradle 与 app manifest，输出 2 错误和 1 提示；本项目唯一模块为 Android Library，此 App 模板门禁不适用 |
| GitHub 云端发布 | 未执行 | 未推送配置/标签，未上传远端包；须在私有仓库 Actions 上验证权限和实际发布结果 |
| 设备故障与采集 SDK | 未执行 | 本轮修改发布配置，不改变故障实现；ARM、16 KB 页面设备与实际采集 SDK 仍无验证证据 |

本次通过检查组 6，排除 1，未执行 2。初次本地命令因 PowerShell 解析未加引号的 -D 参数失败，修正引用后通过。源码未提交，未推进基线。自动发布只在检查成功后执行，并归档 Native 符号和验收产物 30 天；不把本地发布成功视为 GitHub 发布成功。

## 历史：验收脚本优化


修改范围：scripts/verify_native_artifacts.py、scripts/verify_native_device.py、新增 scripts/test_native_verifiers.py，以及 README/测试计划。库源码、public API 与故障机制未修改。

| 检查 | 状态 | 结果 |
| --- | --- | --- |
| 验收脚本回归 | 本次通过 | `python -m unittest discover -s scripts -p test_native_verifiers.py`，9 项通过；覆盖缺失/重复/替换 so、压缩与对齐、错误异常与运行关联 |
| 真实 AAR/APK 产物 | 本次通过 | `python scripts/verify_native_artifacts.py`，三个 ABI 的 APK so 均与 AAR 一致，ELF/ZIP 16 KB 对齐、未压缩，导出只有 JNI_OnLoad |
| 历史 Native 日志重放 | 本次通过 | 保存的 26 份脱敏日志均满足新判定；八类 C++ 异常同时核对类型及诊断信息。这是日志重放，不是设备复跑 |
| Native 设备重新执行 | 受阻 | `python scripts/verify_native_device.py --serial emulator-5582`，执行前模拟器离线，退出码 1；未安装夹具或触发故障，未改用连接的真机 |
| JVM、库构建、R8 构建 | 历史通过未复测 | 本轮仅修改 Python 验收与文档，沿用下方历史证据 |

本次通过检查组 3，受阻 1。直接信号场景仍未核对符号化 Native 堆栈；ARM/16 KB 页面设备及宿主采集仍未验证。JNI 注册名称、C++ RTTI 字符串可能保留原始名称，剥离调试符号和限制动态导出不能保证全部名称消失。未建立可靠源码指纹，不推进基线。

## 历史：Native 实现与验证

- 日期：2026-10-13，Asia/Singapore；运行 ID：lib-crash-native-13。
- 模式：增量。新增 13 个独立 Native 实现、JNI 链接、CMake/ABI 配置与统一入口；共享调度新增加载准备步骤，因此回归所有 JVM 测试，并在 R8 后的隔离夹具中执行全部 Native 场景的两个线程版本。
- 环境：Windows、JDK 17.0.12、Gradle 9.1.0、AGP 8.13.2、Kotlin 2.1.21、compileSdk 36、NDK 27.0.12077973、CMake 3.22.1。设备为 Android 16/API 36 x86_64 模拟器，实际页面大小 4096 字节。
- 代码包含本轮未提交改动；未建立可靠源码指纹，不推进通过基线。

| 检查 | 状态 | 命令/证据 | 实际结果 |
| --- | --- | --- | --- |
| Debug/Release AAR | 本次通过 | `./gradlew.bat :lib_crash:assembleDebug :lib_crash:testDebugUnitTest :lib_crash:assembleRelease` | 退出码 0，33 秒；三个 ABI 均构建 |
| JVM 全量回归 | 本次通过 | 补充新测试后执行 `./gradlew.bat :lib_crash:testDebugUnitTest`；`lib_crash/build/test-results/testDebugUnitTest/TEST-*.xml` | 8 项实测通过，0 失败；覆盖 Java 场景、统一入口与 Native 元数据/空白 ID/Java 重载，2 秒 |
| R8 构建与 DEX/JNI | 本次通过 | `python scripts/verify_r8.py --device-apk`；`build/r8-verification/result.json`、`mapping.txt`、`verification-device.apk` | 11 个 Java 场景改名并保留；JNI NativeBridge 是唯一保留原始类名的库链接边界。设备夹具启用 R8，引用 release 库，使用 debug 签名 verification 变体 |
| so ABI、导出与 16 KB 对齐 | 本次通过 | `python scripts/verify_native_artifacts.py`；[产物检查证据](evidence/native-2026-10-13/native-artifacts.json) | arm64-v8a/armeabi-v7a/x86_64 全通过；ELF LOAD 及 APK 未压缩 so 均按 16 KB 对齐，动态导出只有 JNI_OnLoad |
| Native 主线程及后台线程 | 本次通过 | `python scripts/verify_native_device.py --serial emulator-5582`；[26 项结果及 APK SHA-256](evidence/native-2026-10-13/device-results.json) | 13 × 2 全通过，每次核对 runId、线程、Native 编号、预期信号与进程退出；每项耗时及脱敏日志路径见结果 |
| Java/Kotlin 的设备进程行为 | 未执行 | 本轮设备验证针对新增 Native 路径 | Java/Kotlin 异常已做 JVM 回归，不把 Native 设备结果当成 Java 设备结果 |
| 宿主崩溃采集 | 未执行 | 需要指定宿主与采集 SDK | 尚无集成证据 |
| 业务宿主 APK/AAB 混淆 | 未执行 | 需要真实业务宿主 release 产物 | 临时夹具证据不能代替真实业务产物 |
| ARM 与 16 KB 页面设备运行 | 未执行 | 需要对应测试设备 | 三 ABI 编译及静态对齐不等于 ARM 或 16 KB 运行通过 |

检查组本次通过 5、失败 0、未执行 4；其中 JVM 用例 8 项、Native 设备用例 26 项均通过。所有 Gradle 命令使用本次进程级 JAVA_TOOL_OPTIONS=-Xshare:off，未改变项目 JVM 配置。仍有 SDK XML 工具版本和 Gradle 弃用提示，没有构建失败。

Agent 结构、架构与构建门禁通过。构建门禁的 3 项提示涉及没有业务 app、versionCode 和网络安全配置，属于应用模板检查。根工程仍仅有 lib_crash。临时宿主源码已自动清理，随机测试包在安装前确认不存在，完成后卸载成功；未操作已连接真机、清空日志或修改其他应用数据。

Native 算术用例显式模拟 SIGFPE；未初始化属性使用 optional.value 模拟，不声称存在 C++ lateinit。原生空指针/保护页写产生 SIGSEGV，未处理 C++ 异常产生 SIGABRT；日志还核实了 std::runtime_error、out_of_range、bad_cast、invalid_argument、logic_error、bad_optional_access 的实际类型。NativeBridge 为 JNI 稳定名称例外，mapping/native symbols 可还原场景与源码信息。
