# 巡检工作流功能实现说明


1	英语 English	en	美国、英国、加拿大、澳大利亚、印度、全球
2	西班牙语 Spanish	es	西班牙、墨西哥、拉美
3	中文简体 Chinese Simplified	zh-CN	中国、新加坡、海外华人
4	葡萄牙语 Portuguese (Brazil)	pt-BR	巴西、葡萄牙
5	德语 German	de	德国、奥地利、瑞士
6	法语 French	fr	法国、加拿大、非洲部分国家
7	日语 Japanese	ja	日本
8	韩语 Korean	ko	韩国
9	意大利语 Italian	it	意大利
10	荷兰语 Dutch	nl	荷兰、比利时
11	阿拉伯语 Arabic	ar	沙特、阿联酋、埃及、中东
12	印地语 Hindi	hi	印度
13	印尼语 Indonesian	id	印度尼西亚
14	土耳其语 Turkish	tr	土耳其
15	泰语 Thai	th	泰国
16	越南语 Vietnamese	vi	越南
17	俄语 Russian	ru	俄罗斯、部分东欧
18	波兰语 Polish	pl	波兰
19	瑞典语 Swedish	sv	瑞典
20	丹麦语 Danish	da	丹麦
21	芬兰语 Finnish	fi	芬兰
22	挪威语 Norwegian	no	挪威
23  繁体中文 zh-TW      香港/台湾/澳门


## 1. 目标

新增“巡检工作流”入口。用户只需创建一次工作流，后续直接点击执行；计划周期可选，用于展示待执行状态。每次执行复用当前巡检、照片、签名、PDF、Excel、Word、上传的完整结果流程。

不替换现有项目验收功能，也不新建一套报告结果模型。

## 2. 用户流程

```text
新建工作流
  -> 配置名称、检查模板、频率、默认地点和默认执行时间
  -> 保存

工作流列表
  -> 显示待执行 / 已执行 / 已逾期状态
  -> 点击“执行巡检”

自动创建本次现有巡检记录
  -> 自动生成名称和执行时间
  -> 进入现有巡检填写页
  -> 拍照、填写结果、签名
  -> 使用现有逻辑生成 PDF
  -> 回到工作流历史记录
```

## 3. 工作流配置

新建或编辑工作流时支持：

| 字段 | 说明 |
| --- | --- |
| 工作流名称 | 例如“消防设施周巡检” |
| 检查模板 | 复用现有内置或自定义巡检模板 |
| 计划周期 | 可不设置；设置后可选每日、每周，用于待执行状态计算 |
| 默认执行时间 | 仅设置计划周期后显示，用于待执行状态计算 |
| 默认地点 | 创建本次巡检记录时自动带入 |
| 默认签名档案 | 保存时读取当前选中的签名档案，创建记录时自动生成签名快照 |
| PDF/Excel/Word 模板 | 保存时读取当前默认模板，创建记录时自动带入 |
| 默认服务器与自动上传 | 数据字段已预留，首版暂不提供页面配置 |
| 启用状态 | 停用后不允许新执行，但保留历史 |

计划周期第一版只用于显示“今天是否待执行”，不自动创建记录、不推送通知；未设置周期的工作流始终可手动执行。

## 4. 执行规则

点击“执行巡检”时：

1. 判断该工作流是否已有未完成的执行记录。
2. 有未完成记录时，进入并继续该记录，不重复创建。
3. 没有未完成记录时，创建一条新的现有 `InspectionRecord`。
4. 自动生成名称：

```text
{工作流名称} - {yyyy-MM-dd} - {当天序号}
例如：消防设施周巡检 - 2026-07-22 - 001
```

5. 创建记录时带入工作流的模板、地点、签名、报告模板、服务器配置。
6. 现有检查项会按模板复制到本次记录，因此后续修改模板不会影响历史巡检。
7. 用户完成当前巡检、签名、导出 PDF 后，将该记录标记为本工作流的一次完成执行。

## 5. 数据设计

在现有 `core_report` 的 Room 数据库中新增两张表，不修改现有 `InspectionRecord` 的结果结构。

```text
InspectionWorkflow
- id
- name
- templateId
- templateName
- frequencyType: DAILY / WEEKLY
- weeklyDays
- defaultExecuteTime
- defaultLocation
- signatureProfileId
- pdfTemplateId
- excelTemplateId
- wordTemplateId
- serverProfileId
- autoUploadEnabled
- enabled
- createdAt
- updatedAt

InspectionWorkflowRun
- id
- workflowId
- inspectionRecordId
- runName
- plannedAt
- startedAt
- completedAt
- runNo
- status: IN_PROGRESS / COMPLETED / CANCELLED
- createdAt
```

`InspectionWorkflowRun.inspectionRecordId` 直接关联现有 `InspectionRecord`。照片、检查项、签名、导出文件继续使用现有表与逻辑。

## 6. 页面设计

- 工作流列表：卡片显示模板、地点、执行状态和“执行巡检”按钮。
- 工作流编辑页：配置名称、模板、频率、默认时间、地点和启用状态。
- 工作流详情页：展示工作流配置、执行历史、继续未完成巡检、查看本次报告。
- 执行页：直接跳转现有 `ProjectInspectionActivity`，不重写检查、照片、签名和提交页面。

## 7. 复用与改动

直接复用：巡检模板、检查结果、照片、签名、PDF/Excel/Word、报告详情、分享、上传、重试、备份。

需要新增：工作流数据库表、Dao/Repository、工作流列表/编辑/详情页面、执行入口、频率状态计算、历史记录关联、Room 迁移与测试。

## 8. 验收标准

- 可创建每日和每周工作流。
- 同一工作流可重复执行，历史记录互不覆盖。
- 每次执行自动创建新的现有巡检记录。
- 本次记录自动带入名称、时间、模板、签名和报告配置。
- 完成后可使用现有流程签名并生成 PDF。
- 修改或停用工作流不影响已完成巡检和已生成报告。
- 工作流历史可打开对应现有巡检详情和报告详情。
