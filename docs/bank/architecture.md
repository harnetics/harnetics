<!--
[INPUT]: 依赖商业航天访谈结论、领域问题建模与 v3 架构判断
[OUTPUT]: 对外提供 Harnetics v3 的问题来源、两维对齐模型与产品方向叙事
[POS]: design-docs/ 的核心领域叙事文档，为 PRD 与架构判断提供背景
[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
-->

# Harnetics/Aerospace MVP v3 — 跨部门文档对齐系统

> **设计准则最高约束：一切设计必须来自设计系统的颜色和组件 (shadcn/ui + Tailwind)。所有界面排印、交互和反馈需基于定义好的 Design System 执行。**

> v3 基于一家商业航天初创公司（1 名技术负责人 + 3 名一线员工）的实地访谈重写。v2 沿 V 模型设计了四个模块（需求→报告→异常→运维），架构精巧但脱离了一线真实痛点。v3 只解决一个问题：**跨部门、跨层级的文档对齐**。

---

## 1. 从一线来的判断

### 1.1 数据

和一家商业火箭公司的技术负责人、3 名来自不同部门的一线工程师做了半天访谈。核心发现：

- 每天 **40–60%** 的工作时间花在文档编写和评审上（四人独立确认）
- 文档工作中最耗时的不是"写"，而是"对齐"——一份文档需要引用和追溯多个部门、多个层级的其他文档
- 目前的对齐方式：邮件问、开会对、手动查，信息散落在不同人的电脑和系统里

### 1.2 核心痛点

> 一个部门提出特定需求时，往往需要多部门/多层级的文档对齐。

展开来说：

**动力系统部**的工程师要写一份"某型发动机地面试车测试大纲"。这份文档需要对齐：

- 系统工程部的总体需求文档中关于该发动机性能指标的条目
- 总体设计部的火箭总体方案中的动力分系统接口要求
- 全局 ICD 中的推力/质量/接口定义
- 试验与验证部的测试标准模板
- 质量与可靠性部的 FMEA 相关条目

在没有 AI 的世界里，这个工程师要花 2–3 天找文档、读文档、手动对齐引用，然后才能开始真正写初稿。写完后还要送多部门评审，评审的核心也是"你有没有对齐到我这边的最新版本"。

**这就是对齐税**。每份文档都要交，每次交得多少取决于涉及几个部门、几个层级。

### 1.3 v2 哪里偏了

v2 沿着 V 模型的四个阶段（需求→测试→异常→运维）各做了一个模块，每个模块 7–12 条 Evaluator，总共 36 条。架构上没毛病，但回到这四个人面前——他们的日常工作不是"跑 V 模型流水线"，而是"在一张巨大的文档网络中找到和自己相关的节点，对齐后写出新文档"。

v3 的判断：先别管 V 模型的哪个阶段，**把文档对齐这一件事做到位**。哪种文档先做？哪类对齐先通？由具体场景驱动，不由架构设计预设。

### 1.4 LW 的洞察

我的战略伙伴 LW（前航天软件工程师，现互联网开发测试）给了一句精准的判断：

> **重心在于数据怎么流转。在这个产品里，数据就是文档。**

Agent 不是替代工程师，是做**润滑剂**——降低文档在部门之间流转时的摩擦力。

---

## 2. 两维对齐模型

工程师每天在两个维度上做文档对齐。

§1.3.5 同时给出了与 v3 两维模型直接对应的定义：

> **The interrelationships of system elements at a given architecture level of decomposition can be referred to as the horizontal view of the system.** The horizontal view also includes requirements; integration, verification, or validation activities and results; various other related artifacts; and external elements. **How the horizontal elements, activities, results, and artifacts are derived from or lead to higher-level systems and lower-level system element can be referred to as the vertical view of the system.**

这段原文为 v3 的两维对齐模型提供了直接的理论基础：横向视图 = v3 的工程流程维度，纵向视图 = v3 的系统层级维度。

### 2.1 纵向维度：系统层级

商业火箭公司的系统层级结构（从访谈整理确认）：

```
任务层（商业发射任务）
   ↓
系统层（火箭总体）
   ↓
分系统层（动力 / GNC / 结构 / 回收）
   ↓
单机层（发动机 / 飞控 / 传感器）
   ↓
零部件层（材料 / 工艺）
```

INCOSE v5 §1.3.5 对此有精确表述：**系统层级结构通过划分（Partitioning）产生——抑制元素之间交互的细节，只看每个元素与整体的关系，把系统分成一组完整且互不重叠的子集。** 每一层的下属元素不超过 7±2 个（Miller 1956 认知负荷约束）。最终产物称为产品分解结构（Product Breakdown Structure, PBS）。

纵向对齐的含义：**上一层的需求约束下一层的设计，下一层的验证结果汇报给上一层。** 文档要在这个链条上上下追溯。

### 2.2 横向维度：工程流程

```
需求 → 设计 → 集成 → 测试 → 运营
```

对应 INCOSE v5 §2.3.5 的技术过程组：利益相关方需求定义 → 需求分析 → 架构设计 → 实现 → 集成 → 验证 → 确认 → 运行 → 维护 → 处置。

横向对齐的含义：**同一层级内，不同工程阶段之间的文档要前后衔接。** 测试大纲要追溯到设计文档的接口定义，验证报告要追溯到需求条目。

### 2.3 组织维度：部门结构

系统层级 × 工程流程 = 具体的组织部门。从访谈获得的部门列表（12 个）：

| 部门                | 覆盖层级         | 主要工程阶段 |
| ------------------- | ---------------- | ------------ |
| 系统工程部          | 任务层–系统层   | 需求         |
| 总体设计部          | 系统层           | 设计         |
| 动力系统部          | 分系统层         | 设计–测试   |
| GNC 与航电部        | 分系统层         | 设计–测试   |
| 结构与机构部        | 分系统层         | 设计–测试   |
| 回收与再利用技术部  | 分系统层         | 设计–测试   |
| 总装与集成（AIT）部 | 系统层–分系统层 | 集成         |
| 发射与运营部        | 任务层–系统层   | 运营         |
| 试验与验证部        | 全层级           | 测试         |
| 质量与可靠性部      | 全层级           | 全流程       |
| 供应链与制造部      | 单机层–零部件层 | 集成         |
| 前沿技术预研部      | 分系统层–单机层 | 设计         |

**每个部门既是文档的生产者，也是其他部门文档的消费者。** 文档对齐的复杂度来自这张 12×5（部门×阶段）的矩阵，再乘以纵向 5 层。

### 2.4 为什么对齐这么难

这不是信息化程度低的问题，是结构性的问题。

**INCOSE v5 §3.2.3 的追溯框架**定义了三个维度的追溯需求：

| 追溯维度 | 含义                     | 在文档对齐中的体现                       |
| -------- | ------------------------ | ---------------------------------------- |
| 垂直追溯 | 需求层级的上下分解与回溯 | 任务需求→系统需求→分系统指标→单机规格 |
| 横向追溯 | 同层级跨学科的对应关系   | 动力部设计→AIT 集成方案→试验部测试用例 |
| 数字线程 | 版本演化和配置变更传播   | ICD v2.3 → 哪些下游文档还引用着 v2.1？  |

一线工程师每天做的事，就是在这三个维度上手动追溯。他们没有使用"追溯"这个词，但描述的行为就是——"找到上游最新版的要求，确认下游文档已经更新"。

---

## 3. 文档图谱

### 3.1 ICD 是脊柱

**接口控制文档（Interface Control Document, ICD）** 是整个文档网络的中心节点。从访谈确认：ICD 由技术负责人敲定，定义了分系统之间的接口——机械、电气、软件、热控的参数和约束。

INCOSE v5 §3.2.4（接口管理）的定义：**接口管理确保系统元素与外部实体之间以及系统元素彼此之间的交互得到识别、定义和管理。** 原文特别强调："Failing to identify all interface boundaries and interactions is a significant risk...especially during system integration, verification, and validation." ICD 被置于配置管理之下（put under configuration control）。

§3.2.4 还提到了两个对 v3 有价值的方法：

- **N² 图（N-squared diagram）**：一种用于系统性识别所有分系统之间接口交互的矩阵方法。v3 的文档图谱在逻辑上等价于一张动态的 N² 图——每个部门是矩阵的行/列，每条边是矩阵单元格中的接口
- **数据中心实践（Data-centric practice）**：原文指出这种实践"enables effective impact and change analysis...helping ensure consistency of interface requirements and definitions across the architecture"。这正是 v3 变更影响分析器（§4.2）的设计理念

ICD 为什么是脊柱：

- 它连接所有分系统部门（每个部门都依赖 ICD 知道自己的边界）
- 它是纵向追溯的枢纽（系统级 ICD → 分系统接口 → 单机规格）
- 它的版本变更影响最广（ICD 改了，所有引用它的文档都要检查）

### 3.2 两类文档

从访谈整理出的文档分类，可以映射到 INCOSE v5 §2.3.4.5 的配置项分类：

**全局文档**（由技术负责人或系统工程部管控）：

| 文档类型       | INCOSE 对应                                     | 管控者         |
| -------------- | ----------------------------------------------- | -------------- |
| 全局 ICD       | Technical Description / Interface Specification | 技术负责人     |
| 系统级需求文档 | Stakeholder Requirements + System Requirements  | 系统工程部     |
| 火箭总体方案   | System Architecture Description                 | 总体设计部     |
| 总体测试计划   | Verification Plan                               | 试验与验证部   |
| 质量管理计划   | Product Assurance Plan                          | 质量与可靠性部 |

**部门文档**（由各分系统/职能部门管控）：

| 文档类型       | INCOSE 对应              | 示例               |
| -------------- | ------------------------ | ------------------ |
| 分系统设计文档 | Design Description       | 动力系统详细设计   |
| 测试大纲/规程  | Test Procedure           | 发动机地面试车大纲 |
| 试验报告       | Test/Verification Report | 结构静力试验报告   |
| 分析报告       | Analysis Report          | GNC 仿真分析报告   |
| 状态报告       | Status Report            | 集成进度周报       |

### 3.3 文档之间的关系

文档不是孤立的，它们通过几种关系型的边互相连接：

```
traces_to     — 需求到设计/测试的追溯（纵向）
references    — 引用另一份文档的特定条目（横向）
derived_from  — 下级文档从上级文档分解而来（纵向）
constrained_by — 被 ICD 或标准约束
supersedes    — 新版本替代旧版本（数字线程）
impacts       — 变更影响标记
```

这些关系构成一张**文档图谱**——整个公司所有文档的有向图。手动维护这张图是不可能的。目前的现状是每个人脑子里有一张局部的图，对齐的过程就是"打电话问人"。

### 3.4 文档图谱的数据模型

```yaml
DocumentNode:
  doc_id: string              # 唯一标识
  title: string
  doc_type: enum              # ICD | Requirement | Design | TestPlan | TestReport | Analysis | Status
  department: string          # 所属部门
  system_level: enum          # Mission | System | Subsystem | Unit | Component
  engineering_phase: enum     # Requirement | Design | Integration | Test | Operation
  version: string             # 版本号
  status: enum                # Draft | UnderReview | Approved | Superseded
  content_hash: string        # 内容校验
  last_updated: datetime
  sections: list[Section]     # 结构化章节

Section:
  section_id: string
  heading: string
  content: string             # 文本内容（已解析）
  level: int                  # 章节层级
  tags: list[string]          # 语义标签

DocumentEdge:
  source_doc_id: string
  source_section_id: string | null
  target_doc_id: string
  target_section_id: string | null
  relation: enum              # traces_to | references | derived_from | constrained_by | supersedes | impacts
  confidence: float           # AI 识别的边给置信度，人工确认的为 1.0
  created_by: string          # "human" | "ai_ingest" | "ai_alignment"
  created_at: datetime
```

---

## 4. 产品能力定义

v3 MVP 只提供两个核心能力，不多不少。

### 4.1 能力一：文档对齐草稿生成

**输入**：工程师描述一个文档需求——部门、文档类型、主题/上下文。

**过程**：

1. 从文档图谱中识别与该需求相关的上游文档（纵向追溯）
2. 识别与该需求相关的平级文档（横向追溯）
3. 检查 ICD 中的接口约束
4. 生成草稿，每个段落/条目附带来源引用
5. 标记有冲突或版本不一致的地方

**输出**：一份带引注的文档草稿——工程师可以直接审核修改，而不是从零开始写。

**用 INCOSE 的话来说**（§2.3.5.2–5.3）：这个能力覆盖了需求分析中"将利益相关方需求转化为技术需求"的初始步骤，以及架构设计中"分配需求到系统元素"的辅助步骤。但它不做决策——它生成草稿，工程师决策。

### 4.2 能力二：变更影响分析

**输入**：一份文档被修改（版本更新）。

**过程**：

1. 比对新旧版本差异
2. 在文档图谱中查找所有引用或依赖该文档的下游节点
3. 评估影响范围和严重程度
4. 生成受影响文档清单 + 需要更新的具体条目

**输出**：变更影响报告——哪些部门的哪些文档的哪些条目需要检查。

**用 INCOSE 的话来说**（§2.3.4.5 配置管理）：这是配置管理中"变更管理"活动的自动化辅助——识别变更、分析影响、跟踪状态。目前这些靠邮件和会议，延迟高、遗漏多。

### 4.3 这两个能力的关系

能力一是**主动写**——帮工程师生成对齐好的草稿。
能力二是**被动防**——当文档链上的某个节点变了，自动告诉下游。

两者共享同一个底层：文档图谱 + 引注追溯。

---

## 5. 系统架构

### 5.1 四层结构

```
┌────────────────────────────────────────────────────┐
│  人类治理层                                        │
│  审核队列 · 引用确认 · 文档发布审批               │
└────────────────┬───────────────────────────────────┘
                 │
┌────────────────┴───────────────────────────────────┐
│  对齐引擎层                                        │
│  图谱查询 · 草稿生成 · 变更影响分析 · Evaluator   │
└────────────────┬───────────────────────────────────┘
                 │
┌────────────────┴───────────────────────────────────┐
│  文档图谱层                                        │
│  文档索引 · 关系存储 · 版本追踪 · 向量检索        │
└────────────────┬───────────────────────────────────┘
                 │
┌────────────────┴───────────────────────────────────┐
│  文档接入层                                        │
│  解析器 · 格式转换 · 监听器 · ICD 解析            │
└────────────────────────────────────────────────────┘
```

### 5.2 文档接入层

负责把各种格式的文档变成统一的结构化数据。

**解析器**（按优先级排列）：

| 格式                        | 解析策略                 | MVP 优先级 |
| --------------------------- | ------------------------ | ---------- |
| Markdown / 纯文本           | 直接结构化解析           | P0         |
| JSON / YAML（结构化文档）   | Schema 解析              | P0         |
| Word（.docx）               | python-docx 提取         | P1         |
| PDF                         | pdfplumber/PyMuPDF 提取  | P1         |
| Excel（需求表、ICD 参数表） | openpyxl 提取            | P1         |
| CAD / 模型（STEP/IGES）     | 元数据提取（不解析几何） | P2         |

**ICD 解析器**（专项）：ICD 通常以表格形式定义接口参数，解析逻辑比一般文档更结构化——参数名、类型、单位、范围、所属分系统。

**文档监听器**：监控文档目录的变更（文件新增/修改/删除），触发重新索引。MVP 用文件系统 watch，后续可对接文档管理系统 API。

### 5.3 文档图谱层

文档图谱是整个系统的核心资产。

**存储**：

```
SQLite (MVP) / PostgreSQL (规模化)
├── documents       — 文档元数据
├── sections        — 章节内容（分段存储）
├── edges           — 文档间关系
├── embeddings      — 语义向量索引（本地向量数据库）
└── versions        — 文档版本历史
```

**索引建立过程**：

1. **文档入库**：解析器将文档拆为 DocumentNode + Section 列表
2. **语义嵌入**：每个 Section 生成向量嵌入（用于语义检索）
3. **关系抽取**：
   - **规则识别**（高置信度）：正则匹配文档编号引用（如"见 ICD-2024-001 §3.2"）
   - **语义识别**（中置信度）：LLM 辅助分析 Section 之间的追溯关系
   - **人工确认**：对 AI 识别的关系进行确认，确认后置信度升至 1.0
4. **ICD 枢纽绑定**：将 ICD 中的每个接口参数与引用它的部门文档关联

**图谱查询 API**：

```python
class DocumentGraph:
    def get_upstream(self, doc_id: str, depth: int = 2) -> list[DocumentNode]:
        """获取该文档的上游依赖（纵向向上追溯）"""

    def get_downstream(self, doc_id: str, depth: int = 2) -> list[DocumentNode]:
        """获取依赖该文档的下游文档（用于变更影响分析）"""

    def get_related(self, doc_id: str, relation: str = None) -> list[DocumentEdge]:
        """获取横向关联的文档"""

    def get_icd_constraints(self, department: str, subsystem: str = None) -> list[Section]:
        """获取 ICD 中与指定部门/分系统相关的约束条目"""

    def get_by_scope(self, department: str = None, level: str = None, phase: str = None) -> list[DocumentNode]:
        """按组织维度筛选文档"""

    def find_stale_references(self, doc_id: str) -> list[StaleReference]:
        """检查该文档引用的其他文档是否已有新版本"""
```

### 5.4 对齐引擎层

#### 草稿生成器

```python
class AlignmentDraftGenerator:
    def generate(self, request: DraftRequest) -> AlignedDraft:
        """
        1. 解析 request：部门、文档类型、主题描述
        2. 查文档图谱：
           - get_icd_constraints(department) → ICD 约束
           - get_by_scope(level, phase) → 同层级相关文档
           - get_upstream(parent_doc) → 上级文档的要求
        3. 组装 context：把检索到的相关章节拼为 LLM 上下文
        4. 生成草稿：LLM 生成结构化文档，要求每个段落标注引用来源
        5. 验证引注：Evaluator 检查每条引用是否真实存在
        6. 返回 AlignedDraft（草稿 + 引注 + 冲突标记）
        """
```

**关键约束**：

- 草稿中每个技术指标必须追溯到具体的源文档章节（不能凭空生成数字）
- 如果检索到的上游文档之间有冲突（同一参数不同值），必须标记冲突而不是猜一个
- 草稿不做设计决策——它只是把分散的信息对齐到一个地方，决策权在工程师

#### 变更影响分析器

```python
class ChangeImpactAnalyzer:
    def analyze(self, doc_id: str, old_version: str, new_version: str) -> ImpactReport:
        """
        1. diff 新旧版本：识别变更的 sections
        2. 对每个变更 section：
           - get_downstream(doc_id) → 受影响的下游文档
           - 定位下游文档中引用该 section 的具体条目
        3. 评估影响级别：
           - Critical：ICD 接口参数变更 → 所有引用方
           - Major：需求文档变更 → 对应的设计/测试文档
           - Minor：格式/描述性文字变更
        4. 生成 ImpactReport：受影响文档列表 + 具体条目 + 建议动作
        """
```

### 5.5 人类治理层

**审核队列**：所有 AI 生成的草稿进入审核队列，工程师审核后才能标记为正式草稿。这和 v2 一致——INCOSE v5 §2.3.4.4（决策管理）要求所有关键决策有记录可追溯。

**引用确认**：AI 识别的文档间关系（置信度 < 1.0 的边）需要人工确认。确认后成为图谱的可信数据。

**审批流程**：文档发布仍然走各部门现有的审批流程。我们不替代审批，我们加速审批之前的准备工作。

---

## 6. INCOSE v5 在 v3 中的角色

v2 用 INCOSE v5 做了每个模块的 Evaluator 规范（36 条检查项）。v3 用 INCOSE v5 做**文档图谱的骨架和对齐引擎的规则来源**。

### 6.1 需求追溯（§2.3.5.2–5.3 + §3.2.3）

INCOSE v5 定义了需求的 49 个属性。v3 不是每条都检查（那是 v2 的做法），而是抽取和文档对齐直接相关的属性作为图谱节点的元数据。

文档对齐需要用到的需求属性：

| 属性                | 用途                           |
| ------------------- | ------------------------------ |
| unique_id           | 图谱节点标识                   |
| parent_id           | 纵向追溯的边                   |
| source_ref          | 来源追溯的边                   |
| verification_method | 确定关联的测试文档类型         |
| allocated_to        | 确定负责部门                   |
| criticality         | 变更影响的严重程度判定         |
| status              | 过滤有效文档（不追溯已废弃的） |

### 6.2 接口管理（§3.2.4）

INCOSE 把接口管理分为五个步骤：识别→定义→控制→合规检查→责任指派。v3 的 ICD 枢纽模型直接映射：

| INCOSE 步骤 | v3 实现                                         |
| ----------- | ----------------------------------------------- |
| 识别        | ICD 解析器提取所有接口参数                      |
| 定义        | 存储为结构化的 ICDParameter 节点                |
| 控制        | 版本监听 + 变更影响分析                         |
| 合规检查    | Evaluator 检查下游文档引用的 ICD 版本是否为最新 |
| 责任指派    | 每个接口参数标注 owner_department               |

### 6.3 配置管理（§2.3.4.5）

INCOSE v5 原文对配置管理的定位：

> **CM establishes and maintains consistency, integrity, traceability, and control of a product's configuration. CM provides enduring truth, trust and traceability across the full life cycle.** Configuration management must account for horizontal and vertical integration.

"enduring truth, trust and traceability"——这九个字精确概括了 v3 文档图谱要做的事：为工程师提供一个可信赖的、可追溯的、跨部门/跨层级的文档一致性基础设施。

配置管理的五个活动在 v3 中的对应：

| CM 活动        | v3 实现                              |
| -------------- | ------------------------------------ |
| 配置识别       | 文档入库时分配 doc_id + version      |
| 变更管理       | 变更影响分析器                       |
| 配置状态统计   | 文档图谱查询：多少文档引用了过期版本 |
| 配置验证与审计 | Evaluator 检查引用链完整性           |
| 供应链管理     | N/A（MVP 不涉及）                    |

### 6.4 追溯性（§3.2.3）

INCOSE v5 §3.2.3 对追溯性的定义：

> **Bidirectional traceability is facilitated by SE tools which support establishment of two-way links.** CM identification enables "connect the dots" — identity, location, relationships, pedigree, origin.

v3 的文档图谱天然支持双向追溯——每条 DocumentEdge 都可以正向和反向查询（get_upstream / get_downstream）。

原文还区分了三种追溯：
- **垂直追溯（Vertical traceability）**：parent/child across architecture levels (Level n → n+1 → n+2)
- **横向追溯（Horizontal traceability）**：peer relationships across same level AND across life cycle stages
- **数字线程（Digital thread）**：connecting digital models, digital twins, physical assets via unique configuration IDs

v2 的 Citation Chain 三维追溯模型在 v3 中简化为**文档图谱的边**。不再需要独立的 CitationChain 数据结构——边本身就是追溯记录。

| 追溯维度 | v3 图谱中的边类型                  |
| -------- | ---------------------------------- |
| 垂直追溯 | `derived_from`, `traces_to`    |
| 横向追溯 | `references`, `constrained_by` |
| 数字线程 | `supersedes`, `impacts`        |

### 6.5 知识管理（§2.3.3.6）

v3 MVP 场景中有一项能力——引用"本部门历史的类似测试大纲"。这直接对应 INCOSE v5 §2.3.3.6 知识管理流程：

> The purpose of the Knowledge Management process is to **create the capability and assets that enable the organization to exploit opportunities to re-apply existing knowledge.**

原文区分了两类知识：
- **显性知识（Explicit knowledge）**：记录在文档、流程、标准中——v3 文档图谱直接索引和管理的对象
- **隐性知识（Tacit knowledge）**：存在于个人经验中——v3 通过语义检索相似的历史文档来间接「外化」这部分知识

知识管理的关键活动与 v3 的映射：

| KM 活动                     | v3 实现                                    |
| --------------------------- | ----------------------------------------- |
| 建立知识分类体系（Taxonomy） | 文档图谱的 doc_type + system_level + engineering_phase 分类 |
| 捕获领域工程信息             | 文档入库 + 语义嵌入                         |
| 识别可复用资产               | 语义检索历史相似文档                         |
| 评估知识资产的适用性         | 版本状态过滤（Approved vs Superseded）       |
| 维护架构模式与参考架构       | ICD 枢纽 + 文档模板系统                     |

特别值得注意的是，INCOSE 原文对产品线复用提出了严肃警告："the prior solution was intended for a different use, environment, or performance level." 这对 v3 的设计约束是：历史文档可以作为**参考**用于草稿生成，但不能直接**复制**——必须用 Evaluator 验证与当前项目上下文的一致性。

### 6.6 信息管理（§2.3.4.6）

v3 的文档图谱层本质上是一个信息管理系统。INCOSE v5 §2.3.4.6 的原文定义：

> The purpose of the Information Management process is to **generate, obtain, confirm, transform, retain, retrieve, disseminate, and dispose of information** to designated stakeholders.

原文强调两个关键关联：
1. **信息管理必须与配置管理紧密关联**（"Information management must be associated very closely with configuration management to ensure the integrity, initial release and change control"）——v3 的文档图谱层同时承担了信息索引（IM）和版本追踪（CM）
2. **知识管理以信息管理为基础**（"information management is key for knowledge management"）——v3 的 §6.5 知识管理能力依赖 §6.6 信息管理基础设施

信息管理的核心活动与 v3 的对应：

| IM 活动             | v3 实现                                       |
| ------------------- | -------------------------------------------- |
| 建立系统数据字典     | 文档图谱的元数据 schema（DocumentNode 模型）   |
| 定义信息访问权限     | Phase 3 的权限体系                             |
| 信息检索与分发       | 图谱查询 API + 语义检索                        |
| 信息归档             | 版本历史表（versions）                         |
| 处置无效信息         | Superseded 状态标记                            |

---

## 7. Evaluator 设计

v3 的 Evaluator 不是按 V 模型模块组织（v2 的 E1.x–E4.x），而是按**文档对齐的质量维度**组织。

### 7.1 引注完整性（5 项）

| #    | 检查项                     | 方法                                       | 级别 |
| ---- | -------------------------- | ------------------------------------------ | ---- |
| EA.1 | 每个技术指标都有来源引用   | 段落扫描：数字/公式/参数必须有 source_ref  | 阻断 |
| EA.2 | 引用的文档/章节真实存在    | 在图谱中查找 target_doc + target_section   | 阻断 |
| EA.3 | 引用的文档版本为最新有效版 | 比对 version 与图谱中 status != Superseded | 告警 |
| EA.4 | 无循环引用                 | 图谱环检测                                 | 阻断 |
| EA.5 | 引注覆盖率                 | 技术性段落中有引注的比例 ≥ 80%            | 告警 |

### 7.2 ICD 一致性（3 项）

| #    | 检查项                              | 方法                                 | 级别 |
| ---- | ----------------------------------- | ------------------------------------ | ---- |
| EB.1 | 文档中涉及的接口参数与 ICD 定义一致 | 参数名/值/单位比对                   | 阻断 |
| EB.2 | ICD 版本引用正确                    | 文档声明的 ICD 版本 = 图谱中的最新版 | 告警 |
| EB.3 | 无 ICD 未定义的私有接口             | 文档中的接口参数在 ICD 中有对应条目  | 告警 |

### 7.3 跨部门一致性（3 项）

| #    | 检查项                           | 方法                             | 级别 |
| ---- | -------------------------------- | -------------------------------- | ---- |
| EC.1 | 同一参数在不同部门文档中的值一致 | 图谱横向查询 + 数值比对          | 阻断 |
| EC.2 | 上级需求全覆盖                   | 父文档的每条需求在子文档中有追溯 | 告警 |
| EC.3 | 层级分配无遗漏                   | 系统需求→分系统的分配关系完整   | 告警 |

### 7.4 AI 质量（3 项）

| #    | 检查项               | 方法                                     | 级别 |
| ---- | -------------------- | ---------------------------------------- | ---- |
| ED.1 | 无凭空捏造的技术指标 | 每个数字/参数可追溯到源文档              | 阻断 |
| ED.2 | 无错误归因           | LLM 交叉验证：引用的章节是否支持相应论述 | 阻断 |
| ED.3 | 冲突明确标记         | 检测到的上游冲突是否在草稿中标记而非隐藏 | 阻断 |

**共 14 项 Evaluator，10 项阻断 / 4 项告警。** 比 v2 的 36 项大幅精简，因为 v3 只做文档对齐，不做整个 V 模型链路。

---

## 8. 数据模型

### 8.1 Draft 请求

```yaml
DraftRequest:
  requester_department: string       # 发起部门
  doc_type: enum                     # 需要生成的文档类型
  system_level: enum                 # 涉及的系统层级
  subject: string                    # 主题描述（自然语言）
  parent_doc_id: string | null       # 上级文档（如有）
  related_doc_ids: list[string]      # 已知相关文档（可选）
  template_id: string | null         # 文档模板（可选）
  constraints: list[string]          # 附加约束（如"须符合GJB xxx"）
```

### 8.2 对齐草稿

```yaml
AlignedDraft:
  draft_id: string
  request: DraftRequest
  sections: list[DraftSection]
  source_documents: list[DocumentRef]   # 生成过程中引用的所有源文档
  conflicts: list[Conflict]             # 检测到的上游冲突
  eval_results: list[EvaluationResult]  # Evaluator 检查结果
  generated_by: string                  # LLM 标识
  generated_at: datetime

DraftSection:
  heading: string
  content: string
  citations: list[Citation]             # 该段落的引用列表
  confidence: float                     # 生成置信度

Citation:
  source_doc_id: string
  source_section_id: string
  source_text_snippet: string           # 被引用的原文片段
  relation: string                      # 引用关系说明

Conflict:
  parameter: string                     # 冲突的参数
  doc_a: DocumentRef                    # 源 A
  value_a: string
  doc_b: DocumentRef                    # 源 B
  value_b: string
  resolution: string | null             # 解决建议（如有）
```

### 8.3 变更影响报告

```yaml
ImpactReport:
  trigger_doc_id: string                # 触发变更的文档
  old_version: string
  new_version: string
  changed_sections: list[SectionDiff]
  impacted_documents: list[ImpactedDoc]
  summary: string

SectionDiff:
  section_id: string
  change_type: enum                     # Added | Modified | Deleted
  old_content: string | null
  new_content: string | null

ImpactedDoc:
  doc_id: string
  department: string
  impact_level: enum                    # Critical | Major | Minor
  affected_sections: list[string]       # 受影响的章节 ID
  suggested_action: string              # 建议动作
  current_reference_version: string     # 当前引用的版本
```

### 8.4 ICD 参数

```yaml
ICDParameter:
  param_id: string                      # 参数唯一标识
  name: string                          # 参数名（如 "推力"）
  interface_type: enum                  # Mechanical | Electrical | Software | Thermal | Data
  subsystem_a: string                   # 接口一端
  subsystem_b: string                   # 接口另一端
  value: string                         # 参数值（含单位）
  unit: string
  range: string | null                  # 允许范围
  owner_department: string              # 管控部门
  version: string
  last_updated: datetime
```

---

## 9. MVP 范围

### 9.1 第一个场景

MVP 只做一个部门的一种文档。根据访谈反馈，选择**动力系统部的测试大纲**作为切入点（理由：频率高、跨部门依赖明确、格式相对标准）。

具体而言：

**用户**：动力系统部工程师
**任务**：编写"某型发动机地面试车测试大纲"
**需要对齐的文档**：

1. 系统工程部的系统级需求文档（需求条目）
2. ICD（发动机接口参数）
3. 试验与验证部的测试标准模板（格式要求）
4. 本部门历史的类似测试大纲（经验参考）

**AI 做的事**：

1. 检索上述 4 类文档的相关章节
2. 生成测试大纲草稿（按模板格式）
3. 每个测试项追溯到需求条目和 ICD 参数
4. 标记需求覆盖缺口（有需求无对应测试项）
5. 标记 ICD 版本不一致（如有）

**AI 不做的事**：

- 不做测试方案设计（方法选择是工程师的专业判断）
- 不做通过/失败判定
- 不做测试数据分析

### 9.2 MVP 数据准备

| 数据               | 来源         | 格式            | 数量    |
| ------------------ | ------------ | --------------- | ------- |
| 系统级需求文档     | 系统工程部   | Markdown / Word | 1 份    |
| 全局 ICD           | 技术负责人   | Excel / YAML    | 1 份    |
| 测试标准模板       | 试验与验证部 | Word / Markdown | 1 份    |
| 历史测试大纲       | 动力系统部   | Word / PDF      | 3–5 份 |
| 动力分系统设计文档 | 动力系统部   | Word            | 1 份    |

总共约 10 份文档，足以验证核心链路。

### 9.3 MVP 验收标准

| 标准       | 指标                                        | 目标               |
| ---------- | ------------------------------------------- | ------------------ |
| 草稿可用性 | 工程师一次审核通过率（需修改 < 30%）        | > 50%              |
| 引注完整性 | EA.1–EA.5 全部实现并通过                   | 100%               |
| ICD 一致性 | EB.1–EB.3 全部实现并通过                   | 100%               |
| 时间节省   | 从"开始写"到"可提交评审"的时间              | 从 2–3 天降到半天 |
| 变更检测   | 修改 ICD 中一个参数，系统能识别受影响的文档 | 召回率 > 80%       |

### 9.4 MVP 不包含

| 不做                         | 原因                                 |
| ---------------------------- | ------------------------------------ |
| V 模型全链路（v2 的 M1–M4） | 解决了对齐问题后再考虑流程自动化     |
| 多项目/多火箭型号            | 先在一个项目上跑通                   |
| 实时遥测解析                 | 测试大纲是发射前文档，不涉及实时数据 |
| 自动审批                     | 审批流程不变，只加速准备阶段         |
| Web 管理界面                 | MVP 用 CLI + 本地文件，验证核心能力  |
| DOORS/PDM 集成               | 先用文件系统做文档源，跑通后再对接   |

---

## 10. 技术选型

| 组件     | 选择                                         | 理由                                                         |
| -------- | -------------------------------------------- | ------------------------------------------------------------ |
| 主语言   | Python 3.11+                                 | 快速迭代 + 文档解析生态（python-docx, pdfplumber, openpyxl） |
| 图存储   | SQLite + 关系表模拟图查询                    | MVP 足够，不引入图数据库的运维成本                           |
| 向量索引 | chromadb（本地嵌入）                         | 纯本地、零运维                                               |
| 嵌入模型 | sentence-transformers（本地）                | 航天数据不可上传                                             |
| LLM      | litellm（统一接口）                          | 支持本地模型和私有 API 按需切换                              |
| 文档解析 | python-docx + pdfplumber + openpyxl + PyYAML | 覆盖 MVP 需要的格式                                          |
| CLI      | typer                                        | 轻量 Python CLI                                              |
| 测试     | pytest                                       | 标准                                                         |

### 关于 Rust

v2 用 Rust 做 Kernel/Trace/Policy 层。v3 MVP 全部用 Python——因为 v3 的核心价值在文档理解和对齐，不在运行时性能。Rust 留到文档量级上来后（数千份文档、秒级查询要求）再引入。

---

## 11. 项目结构

```
harnetics/
├── pyproject.toml
├── README.md
│
├── harnetics/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py          # DocumentNode, Section, DocumentEdge
│   │   ├── icd.py               # ICDParameter
│   │   ├── draft.py             # DraftRequest, AlignedDraft, Citation, Conflict
│   │   └── impact.py            # ImpactReport, ImpactedDoc, SectionDiff
│   │
│   ├── parsers/
│   │   ├── __init__.py
│   │   ├── markdown_parser.py
│   │   ├── docx_parser.py
│   │   ├── excel_parser.py
│   │   ├── yaml_parser.py
│   │   └── icd_parser.py        # ICD 专用解析器
│   │
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── store.py             # SQLite 存储
│   │   ├── indexer.py           # 文档入库 + 关系抽取
│   │   ├── query.py             # DocumentGraph 查询 API
│   │   └── embeddings.py        # 向量嵌入 + 语义检索
│   │
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── draft_generator.py   # 草稿生成器
│   │   ├── impact_analyzer.py   # 变更影响分析器
│   │   └── conflict_detector.py # 冲突检测
│   │
│   ├── evaluators/
│   │   ├── __init__.py
│   │   ├── base.py              # Evaluator 基类 + EvaluatorBus
│   │   ├── citation.py          # EA.1–EA.5 引注完整性
│   │   ├── icd.py               # EB.1–EB.3 ICD 一致性
│   │   ├── consistency.py       # EC.1–EC.3 跨部门一致性
│   │   └── ai_quality.py        # ED.1–ED.3 AI 质量
│   │
│   ├── llm/
│   │   ├── __init__.py
│   │   └── client.py            # LLM 调用封装（litellm）
│   │
│   └── cli/
│       ├── __init__.py
│       └── main.py              # CLI 入口
│
├── tests/
│   ├── conftest.py
│   ├── test_models/
│   ├── test_parsers/
│   ├── test_graph/
│   ├── test_engine/
│   └── test_evaluators/
│
├── fixtures/                    # demo 文档（匿名化的样例数据）
│   ├── requirements/
│   │   └── system_requirements.md
│   ├── icd/
│   │   └── global_icd.yaml
│   ├── templates/
│   │   └── test_plan_template.md
│   ├── design/
│   │   └── propulsion_design.md
│   └── historical/
│       ├── test_plan_001.md
│       └── test_plan_002.md
│
└── docs/
    ├── architecture.md
    └── quickstart.md
```

---

## 12. CLI 设计

```bash
# 初始化文档库（首次使用）
harnetics init --doc-root ./documents

# 导入文档
harnetics ingest ./documents/requirements/system_req_v3.docx
harnetics ingest ./documents/icd/global_icd.xlsx
harnetics ingest ./documents/ --recursive  # 批量导入

# 查看文档图谱
harnetics graph show                       # 所有文档和关系概览
harnetics graph show --department 动力系统部  # 按部门筛选
harnetics graph upstream DOC-001           # 上游追溯
harnetics graph downstream DOC-001         # 下游追溯

# 生成对齐草稿
harnetics draft \
    --department 动力系统部 \
    --type test_plan \
    --subject "某型发动机地面试车测试大纲" \
    --parent-doc DOC-001 \
    --output ./output/draft.md

# 变更影响分析
harnetics impact DOC-003 --old-version v2.1 --new-version v2.3

# 检查文档一致性
harnetics check ./output/draft.md           # 对一份文档运行全部 Evaluator
harnetics check --all                       # 检查整个文档库的引用一致性

# 查看系统状态
harnetics status                             # 文档数、关系数、过期引用数
```

---

## 13. 路线图

### Phase 0：单场景验证（0–2 月）

- 支持 Markdown + YAML 格式文档入库
- 文档图谱基础存储 + 查询
- ICD 参数提取（YAML 格式）
- 草稿生成器（动力部测试大纲场景）
- EA.1–EA.5 + EB.1 Evaluator
- CLI 基础命令（ingest / draft / check）
- 用 fixture 数据跑通完整链路

**验收**：对 fixture 中的动力部场景，生成的测试大纲草稿通过 Evaluator 检查，且每个测试项有来源引用。

### Phase 1：格式扩展 + 变更分析（2–4 月）

- 支持 Word / Excel / PDF 格式
- ICD 从 Excel 表格提取
- 变更影响分析器
- EB.2–EB.3 + EC.1–EC.3 Evaluator
- 文档监听器（文件变更触发重索引）
- AI 关系抽取（LLM 辅助识别文档间追溯关系）

**验收**：修改 ICD 中一个参数，系统在 1 分钟内给出受影响文档列表。至少 2 个额外部门场景可运行。

### Phase 2：多部门 + WebUI（4–8 月）

- 扩展到 4+ 部门的文档覆盖
- 简易 Web 界面（FastAPI + 单页面）
- ED.1–ED.3 Evaluator（AI 质量检查）
- 文档审核队列（Web）
- 关系图可视化
- 向量语义检索优化（大文档库场景）

**验收**：跨 4 个部门的一次完整对齐流程可在 Web 上完成，对齐时间从天级降到小时级。

### Phase 3：集成 + 规模化（8–12 月）

- 对接 DOORS / PDM 等现有系统
- Rust 高性能查询引擎（千级文档场景）
- 多项目/多型号支持
- 权限体系
- 标准合规检查（GJB / ECSS 评估器）
- API 开放（供内部系统集成）

---

## 14. 这个项目不做什么

| 不做                      | 原因                                                |
| ------------------------- | --------------------------------------------------- |
| 替代 DOORS / MATLAB / STK | 这些是成熟的领域工具，我们连接它们                  |
| 自动做工程决策            | 选材、方案比较、设计权衡是工程师的专业判断          |
| 文档管理系统              | 我们不存储"正式版本"，我们索引和对齐它们            |
| 自动审批                  | 审批流程是组织治理行为，我们加速审批前的准备        |
| 航天数据上云              | 数据安全红线不可触碰                                |
| "一键生成"完整文档        | 不存在——每份文档的决策依据不同，AI 只做对齐和初稿 |

---

## 15. v2 → v3 的关键变化

| 维度           | v2                 | v3                              |
| -------------- | ------------------ | ------------------------------- |
| 核心问题       | V 模型全链路自动化 | 跨部门文档对齐                  |
| 模块数         | 4（M1–M4）        | 2 个能力（草稿生成 + 变更分析） |
| Evaluator 数   | 36 项              | 14 项                           |
| 技术栈         | Rust + Python      | Python（MVP），Rust 按需引入    |
| 切入场景       | 测试报告生成（M2） | 测试大纲草稿对齐                |
| 数据基础       | 遥测二进制流       | 各部门文档                      |
| ICD 的角色     | 逆向校验工具       | 文档网络的脊柱节点              |
| Citation Chain | 独立数据结构       | 图谱的边                        |
| 来源           | 架构推演           | 一线访谈                        |

---

## 16. 核心指标

| 指标           | 定义                                   | 目标                  |
| -------------- | -------------------------------------- | --------------------- |
| 对齐时间       | 从"开始写文档"到"可提交评审"           | 从 2–3 天降到半天    |
| 引注追溯率     | AI 草稿中可追溯到源文档的技术指标比例  | 100%                  |
| 变更影响召回率 | 文档变更时，受影响下游文档的识别召回率 | > 80%                 |
| 版本一致率     | 文档引用的 ICD/需求版本为最新的比例    | 目标 100%，基线先摸底 |
| 工程师接受度   | 草稿需要修改的比例 < 30% 的文档占比    | > 50%                 |

---

## 附录 A：INCOSE v5 引用映射

| INCOSE v5 章节               | v3 中的对应                             |
| ---------------------------- | --------------------------------------- |
| §1.3.5 系统内的层级结构     | 两维对齐模型 — 横向/纵向视图（§2.1）  |
| §2.3.3.6 知识管理           | 历史文档复用 + 语义检索（§6.5）        |
| §2.3.4.5 配置管理           | 版本追踪 + 变更影响分析（§4.2, §6.3） |
| §2.3.4.6 信息管理           | 文档图谱层基础设施（§5.3, §6.6）      |
| §2.3.4.4 决策管理           | 人类治理层（§5.5）                     |
| §2.3.5.2 利益相关方需求定义 | 需求追溯属性提取（§6.1）               |
| §2.3.5.3 系统需求定义       | 需求追溯属性提取（§6.1）               |
| §3.2.3 追溯性               | 文档图谱双向追溯边模型（§6.4）         |
| §3.2.4 接口管理             | ICD 枢纽 + N² 图等价模型（§3.1, §6.2）|

## 附录 B：术语表

| 术语      | 定义                                                          |
| --------- | ------------------------------------------------------------- |
| 文档对齐  | 确保一份文档的内容与其引用/依赖的其他文档一致、完整、版本正确 |
| 文档图谱  | 公司所有文档及其相互关系构成的有向图                          |
| ICD       | 接口控制文档，定义分系统之间接口参数和约束的基准文档          |
| 对齐税    | 工程师在文档编写中为跨部门/跨层级对齐所付出的额外时间成本     |
| 引注      | AI 生成内容对源文档具体位置的引用标记                         |
| 上游文档  | 在追溯链中层级更高或产出更早的文档                            |
| 下游文档  | 依赖或引用上游文档的文档                                      |
| Evaluator | 对 AI 生成内容进行形式化检查的自动化评估器                    |
| Gate      | 流程中的质量关卡，通过才能进入下一步                          |
| 置信度    | AI 识别的文档间关系的可信程度，人工确认后为 1.0               |
