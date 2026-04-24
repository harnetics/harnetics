# fixtures/format-test/
> L2 | 父级: fixtures/AGENTS.md

每种支持格式的最小化航天主题样本，用于测试各解析器的解析效果。

成员清单
FMT-MD-001.md: Markdown 格式样本 — 推进系统需求说明，含 YAML front-matter、多级标题、加粗、参数引用
FMT-YAML-001.yaml: YAML 格式样本 — 接口控制参数，含 sections/parameters 嵌套结构
FMT-CSV-001.csv: CSV 格式样本 — 接口参数矩阵，UTF-8，含中文列头
FMT-DOCX-001.docx: Word 格式样本 — 设计说明书，含多级标题、表格、正文段落
FMT-XLSX-001.xlsx: Excel 格式样本 — 参数矩阵 + 接口参数，含 2 个 Sheet
FMT-PDF-001.pdf: PDF 格式样本 — 地面热试车测试报告，2 页，可被 pypdf 文本提取

用法
```bash
# 测试单个格式解析
harnetics ingest fixtures/format-test/FMT-DOCX-001.docx

# 批量导入全部格式（验证全链路）
harnetics ingest fixtures/format-test/
```

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
