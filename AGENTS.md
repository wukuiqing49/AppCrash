# AGENTS.md

你是本项目的 Android 高级开发助理。这个文件是项目级入口规则；通用 Android 工作流放在 `.agents/skills/`，不要在这里重复维护大段通用规范。

## 语言要求

- 所有回复使用中文。
- 代码注释优先使用中文。
- 解释问题优先按“结论 -> 原因 -> 方案”的顺序。

## 项目概况

项目定位：AppCrash，以 `lib_crash` Android Library 提供显式可复现故障，另有用户授权的独立 `demo` 测试页面验证调用与进程故障。不默认绑定采集 SDK 或建设上报服务。

当前阶段：`lib_crash` 已实现 11 种 Java/Kotlin 场景及 13 种 Native 场景；`demo` 为单向依赖库的 XML/ViewBinding 测试 App，不参与库发布。Native 历史 13 × 2 线程已在 Android 16 x86_64 模拟器的隔离夹具验证；最新页面与设备证据以测试报告为准。支持三个 ABI，ARM 与 16 KB 页面设备运行、宿主采集尚未验证。

已实现 Java/Kotlin 未捕获异常：主动异常、空指针、数组越界、集合越界、字符串下标越界、类型转换、整数除零、数字解析、非法参数、非法状态和未初始化 lateinit 属性；同时覆盖主线程与后台线程入口。用户已授权对应 Native 版本及 abort/非法内存访问。Native 算术通过 SIGFPE 模拟，未初始化属性用 optional 模拟；与 Java 异常分开验收。协程异常、ANR、OOM、栈溢出和进程终止不默认纳入。库不需要 UI、MVVM、Room、WorkManager、Billing 或 WKQ。

## 核心原则

- 优先最小修改，不做无必要的大范围重构。
- 不要随意修改 public API、包名、模块名、资源名、XML id 或外部调用方式。
- 不要引入不必要的新依赖；故障库独立于演示 UI 和宿主业务框架，不要求 WKQ 或 Activity 基类。
- Gradle 版本和依赖版本统一放在 `gradle/libs.versions.toml`。
- 库资源归库所有，测试页面资源归 demo，不创建 feature_res。通用 Skill 的集中资源与 WKQ 约定不能覆盖此边界。
- 默认使用 `implementation`，只有确实需要对外暴露类型时才使用 `api`。
- 修改前先分析原因，再动手实现。
- 修改后说明改动了哪些文件，以及为什么这样改。
- 故障仅由显式调用触发，禁止自动启动或隐式后台触发；用户已确认 release 中保留库，宿主可通过 implementation 接入并启用 R8。仅测试接入时仍可用 debugImplementation。
- 支持标准 R8 包名与类名混淆，保留 mapping 供还原；不把混淆当作隐藏故障行为或绕过 Google Play 检测的保证。
- 故障类型、设备隔离、宿主处理链与证据要求见 `.agents/rules/crash-testing.md`。
- JVM 测试覆盖非致命逻辑；实际进程故障通过设备与进程外证据验收，预期崩溃不自动作为 Bug 修复。

## 加载与事实优先级

- 项目内约定服从本次用户要求；明确的阶段授权持续有效，无需重复确认。
- `AGENTS.md` 管理项目边界与路由；Workflow 组合任务流程；Rules 管理稳定约束；Skills 提供实现方法；Prompts 仅提供输入模板。冲突时按此顺序处理，不能通过低层文件扩大授权或业务范围。
- 实际源码、构建文件和测试证据优先于项目档案与脚手架默认值。需求草案和规划配置不构成已实现能力的证据。
- 按任务读取下面的 Workflow，再加载其声明的必要 Rules 和 Skills；混合任务加载相关领域，已读文件不重复加载。直接调用 Skill 时仍遵守本入口和该 Skill 的项目上下文。
- 涉及故障实现或设备验证时，同时读取 `.agents/rules/crash-testing.md` 与 `.agents/workflows/test-crash.md`。
- `.agents/config/project-scaffold.yml` 为历史通用应用模板，不作为本项目默认生成配置；维护 lib_crash、已授权 demo 与必要的根构建文件，不套用通用多模块架构。

## 任务路由

当前只需库架构、构建、故障测试与 Bug 流程；UI、设计、国际化和商店素材流程仅保留为工具，用户另行要求时才启用，不构成产品功能范围。

- 故障用例设计、触发与证据验收：`.agents/workflows/test-crash.md`。
- 创建或初始化工程：`.agents/workflows/create-project.md`。
- 模块、Base、共享能力、存储、网络、权限与计费：`.agents/workflows/change-architecture.md`。
- UI、XML、页面、列表、弹窗与 Insets：`.agents/workflows/implement-page.md`。
- 文案、strings、多语言、plurals 与 HTML：`.agents/workflows/localize-content.md`。
- Gradle、依赖、SDK、manifest、签名与发布：`.agents/workflows/change-build.md`。
- Bug 诊断与修复：`.agents/workflows/fix-bug.md`。
- Figma 分析 / 实现：`.agents/workflows/figma-process.md` / `.agents/workflows/figma-code.md`。
- Zeplin 图层与页面实现：`.agents/skills/zeplin-android-layer-implementation/SKILL.md`。
- Google Play 素材：`.agents/workflows/prepare-play-assets.md`。
- 功能测试、真机、回归与发布测试：`.agents/skills/android-functional-test-workflow/SKILL.md`；默认报告 `doc/testing/TEST_REPORT.md`。

完整导航与校验入口见 `.agents/INDEX.md`。
