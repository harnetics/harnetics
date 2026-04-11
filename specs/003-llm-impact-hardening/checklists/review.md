# Requirements Review Checklist: LLM Connectivity and Impact Localization Hardening

**Purpose**: 验证本特性的需求是否足够完整、清晰、可测，并能指导实现章节级影响定位与 LLM 配置稳健性修复
**Created**: 2026-04-11
**Feature**: [spec.md](../spec.md)

## Requirement Completeness

- [ ] CHK001 是否明确规定了草稿生成路由必须使用 `app.state.settings`，而不是依赖默认构造路径？ [Completeness, Spec §FR-001]
- [ ] CHK002 是否说明了裸 Ollama 模型名归一化的触发条件与适用边界？ [Completeness, Spec §FR-002]
- [ ] CHK003 是否覆盖了旧图谱边缺少 section id 时的兼容行为，而不是只描述理想的新边？ [Completeness, Spec §FR-007]

## Requirement Clarity

- [ ] CHK004 “可诊断错误上下文”是否被量化为至少包含模型、base URL 和异常类型，而非模糊表述？ [Clarity, Spec §FR-004]
- [ ] CHK005 “尽力推断 target_section_id” 是否给出了可识别的锚点类型示例，避免实现者自行猜测？ [Clarity, Spec §FR-006]
- [ ] CHK006 “章节级扫描引用关系”是否清楚区分了 `source_section_id` 与 `target_section_id` 的来源？ [Clarity, Spec §FR-005]

## Requirement Consistency

- [ ] CHK007 关于影响传播的要求，是否同时保证“章节定位失败不阻断 BFS”与“章节定位尽量精确”两者不冲突？ [Consistency, Spec §FR-007, Spec §FR-008]
- [ ] CHK008 成功标准是否与用户故事中的 P1 路径一致，避免只验证路由成功而不验证影响定位？ [Consistency, Spec §SC-001, Spec §SC-003]

## Acceptance Criteria Quality

- [ ] CHK009 是否为 Ollama 可用性检查定义了可客观验证的输入/输出，而不是只说“应可用”？ [Acceptance Criteria, Spec §User Story 1]
- [ ] CHK010 是否为影响分析章节定位定义了“至少一个下游文档返回非空 affected_sections”这样的可测门槛？ [Acceptance Criteria, Spec §SC-003]

## Scenario Coverage

- [ ] CHK011 是否同时覆盖了裸模型名、缺失模型、旧边缺少 section id、指定 changed sections 这四类关键场景？ [Coverage, Spec §Edge Cases]
- [ ] CHK012 对 YAML/ICD 文档章节粒度较粗这一限制，是否已有显式假设说明，不会让评审误以为本次必须做到参数级精确定位？ [Coverage, Spec §Assumptions]