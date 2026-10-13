# Android Agent 能力索引

本文件只提供导航。运行时加载和冲突优先级以根目录 `AGENTS.md` 为准。

## 分层

| 层级 | 目录 | 职责 |
| --- | --- | --- |
| 入口 | `AGENTS.md` | 自动加载、项目事实、任务路由和全局红线 |
| 配置 | `.agents/config/` | 项目技术栈档案和脚手架固定参数 |
| 规则 | `.agents/rules/` | 稳定约束，说明必须/禁止什么 |
| 流程 | `.agents/workflows/` | 任务步骤，组合 Rules 和 Skills |
| 能力 | `.agents/skills/` | 领域实现方法、脚本、references 和 assets |
| 输入 | `.agents/prompts/` | 用户可填写的任务模板，不承载规则 |
| 任务数据 | `.ai-work/` | Figma、商店素材等输入、中间产物和结果 |

## 配置

- `config/project-profile.yml`：当前事实和生命周期；`pre-scaffold` 表示未初始化，规划放在 `planned`，不能当成已实现能力。
- `config/project-scaffold.yml`：历史通用应用模板，仅供工具自测或显式指定；AppCrash 为 lib_crash 与用户授权的 demo 测试 App，不使用此应用模板。
- `config/project-scaffold-roofquote.yml`：历史示例，仅供显式指定，不参与 AppCrash 默认生成。

## Rules

- `rules/android.md`：Android 通用修改边界、生命周期、性能、安全和兼容性。
- `rules/architecture.md`：模块边界、共享能力和 WKQ 复用。
- `rules/ui.md`：页面结构、滚动、文字、资源和 Insets。
- `rules/i18n.md`：strings、多语言、占位符、plurals 和 raw HTML。
- `rules/build.md`：Gradle、版本、依赖、签名、manifest、release 和 native。
- `rules/figma.md`：Figma 阶段门禁、图层映射、屏幕适配和验收。
- `rules/play-assets.md`：Google Play 素材保真、安全与合规。
- `rules/execution.md`：通用执行、Bug 修复、验证和输出。
- `rules/crash-testing.md`：故障分类、显式触发、设备隔离和进程外证据验收。

## Workflows

- `workflows/create-project.md`：创建或调整 Android 工程。
- `workflows/test-crash.md`：设计故障用例，分别验收故障触发与宿主采集。
- `workflows/change-architecture.md`：调整模块或共享能力。
- `workflows/implement-page.md`：实现或修改 Android 页面。
- `workflows/localize-content.md`：修改文案和多语言。
- `workflows/change-build.md`：修改构建与发布配置。
- `workflows/fix-bug.md`：诊断并修复 Android Bug。
- `workflows/figma-process.md`：Figma 分析阶段。
- `workflows/figma-code.md`：Figma 实现阶段。
- `workflows/prepare-play-assets.md`：准备 Google Play 商店素材。

## Skills

- `skills/android-functional-test-workflow/`：跨项目的改动影响分析、增量/发布回归与固定测试报告，默认输出 `doc/testing/TEST_REPORT.md`。
- `skills/android-project-scaffold-workflow/`：完整项目生成器、模板和生成测试。
- `skills/android-project-architecture-workflow/`：模块归属、共享能力分析和架构门禁。
- `skills/android-ui-workflow/`：XML UI 实现和 UI 静态门禁。
- `skills/android-i18n-workflow/`：国际化资源处理和 i18n 门禁。
- `skills/android-build-workflow/`：Gradle/发布修改和构建门禁。
- `skills/android-figma-workflow/`：Figma 拉取、规范化、映射、模板和验收门禁。
- `skills/plan-google-play-listing-assets/`：共享产品事实、Seed Keywords 和定位，统一策划 Feature Graphic、商店截图与 Preview Video，并导出独立 Prompt 文件。
- `skills/zeplin-android-layer-implementation/`：读取 Zeplin 图层、资源和设计 Token，并实现 Android XML + ViewBinding 页面。

## Prompts

- `prompts/create-project.md`
- `prompts/change-architecture.md`
- `prompts/implement-page.md`
- `prompts/localize-content.md`
- `prompts/change-build.md`
- `prompts/fix-bug.md`
- `prompts/figma-page.md`
- `prompts/prepare-play-assets.md`

## 验证

- `scripts/validate_agent_structure.py`：检查配置、Rules、Workflows、Prompts、Skills 和引用关系。
- `scripts/validate_play_assets.py`：检查 Google Play PNG/JPEG 素材的尺寸、比例和透明像素。
- `skills/plan-google-play-listing-assets/scripts/`：初始化素材工作区，导出独立 Prompt 文件，并校验关键词输入、Seed CSV、共享策略和三类素材 Brief。
- `scripts/validate_android_workflows.py`：先检查 Agent 结构，再聚合验证目标 Android 工程的 build、architecture、UI、i18n 和已有 Figma 产物。

未初始化阶段运行：

```powershell
python .agents/scripts/validate_agent_structure.py --project-root .
python .agents/scripts/validate_android_workflows.py --project-root . --config-only
```

结构检查默认 `--mode auto`，未初始化时只检查配置；存在 Gradle 文件或 lifecycle 为 initialized 时检查工程事实。`--mode project` 强制工程检查，`--mode config` 只检查配置。配置检查通过不代表 Android 构建或功能通过。

初始化后更新项目档案，再执行聚合门禁和实际 Gradle 构建/测试；聚合门禁在缺少 settings 时失败，避免空工程误报通过。

维护生命周期判断或脚手架配置时运行：

```powershell
python .agents/scripts/tests/test_validate_agent_structure.py -v
python .agents/skills/android-project-scaffold-workflow/scripts/test_render_project_scaffold.py -v
```
