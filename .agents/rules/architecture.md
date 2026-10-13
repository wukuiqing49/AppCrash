# Android 架构规则

## 模块边界

- AppCrash 模块为 lib_crash 与用户授权的 demo 测试 App；依赖方向只能为 demo -> lib_crash，测试页面与资源不进入库产物。不创建 core、feature 或共享资源模块。临时构建夹具不注册到项目模块图。下列应用模板约定不适用于本项目。
- 库不依赖宿主 App、UI、feature_res 或 WKQ，资源归库所有；用户已要求 release 保留库，宿主可通过 implementation 接入并完成 R8 验证。只有明确选择 debug-only 接入时才验收正式包排除。

- `core/` 和 `feature/` 是目录容器，不直接注册为 Gradle module。
- 实际模块使用 `:core:<module>` 和 `:feature:<module>`。
- `app` 只负责应用壳、全局初始化和顶层导航，不承载大量业务页面。
- `core` 子模块不得依赖 `app` 或功能 feature 模块；根据本项目资源集中约定，允许 implementation 依赖仅承载资源与生成 ViewBinding 的 `feature_res`。
- feature 模块不得形成循环依赖；`feature_res` 不依赖功能模块。
- 跨功能逻辑放职责匹配的 core 子模块；跨功能资源放共享资源模块。
- 功能专属 UI、状态和编排留在对应 feature 模块。

## 复用优先级

lib_crash 优先 Kotlin/Java 与 Android 平台能力，不为故障触发引入 WKQ、UI、网络、数据库或计费框架。以下应用框架优先级不适用于库。

1. 目标项目已有共享模块、基础封装和公共组件。
2. AndroidCoreBase、AndroidCoreUtils、AndroidCoreRouters、AndroidCoreNetwork、XPopup。
3. AndroidX 或已有第三方依赖。
4. 确认前三层不能满足后，才新增本地通用能力或依赖。

## WKQ 能力

- 以下仅在演示 App 明确采用 WKQ 时适用，故障库不要求继承基类或初始化框架。

- Activity、Fragment、ViewModel、Adapter 按项目约定继承 AndroidCoreBase 对应基类。
- AndroidCoreUtils 的 Kotlin `object` 和扩展函数通过组合或直接调用使用，不要求业务类继承。
- AndroidCoreUtils 只由 app 壳的 `Application` 统一初始化一次。
- 包装模块向下游暴露 WKQ 类型时使用 `api`；完全隔离第三方类型时使用 `implementation`。
- 接入或更新 WKQ 依赖前查询对应 GitHub 仓库最新 tag，并检查与当前构建基线的兼容性。

## 通用能力归属

- 网络、数据库、上传下载、图片、位置、计费、权限、文件、路由、存储和弹窗能力不得在功能模块重复实现。
- 网络安全 XML 和 FileProvider 的 Manifest 声明属于 app 壳平台配置；XML 文件统一放在 `feature_res`，由 app 引用。
- 模块归属不明确时，先检查 `settings.gradle`、相关模块构建文件和相邻代码。
