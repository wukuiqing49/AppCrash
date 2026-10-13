# 设计与验证崩溃测试用例

## 加载

- `AGENTS.md`
- `.agents/config/project-profile.yml`
- `.agents/rules/execution.md`
- `.agents/rules/android.md`
- `.agents/rules/crash-testing.md`
- 涉及模块或 API 时使用 `$android-project-architecture-workflow`。
- 涉及构建、native、R8 或正式包排除时使用 `$android-build-workflow`。
- 设备与报告使用 `$android-functional-test-workflow`，以崩溃规则补充验收。

## 流程

1. 检查真实工程与用例；无源码时明确未初始化，设计标为规划。
2. 明确用例 ID、类型、线程、设备范围、预期行为与采集集成范围，不默认扩展首期范围。
3. 只在 lib_crash 实现显式故障入口，验证逻辑置于进程外；使用现有或明确指定的测试宿主，不创建演示 UI，保留宿主异常处理链。
4. 实现任务授权内的用例与非致命逻辑测试，检查显式触发与测试变体隔离。
5. 设备执行前记录运行 ID 与环境并检查数据隔离，每次故障后从进程外取得证据。
6. 分别判断故障触发与宿主采集结果，无集成或访问权限的链路标为未验证。
7. 更新 `doc/testing/TEST_PLAN.md` 与 `doc/testing/TEST_REPORT.md`，仅实测通过项推进基线；仅修改 Agent 配置时不生成设备报告。
