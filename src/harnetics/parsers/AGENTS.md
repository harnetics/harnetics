# harnetics/parsers/
> L2 | 父级: src/harnetics/AGENTS.md

文档解析器包 — 负责将各种格式文件解析为 Section 列表，供 DocumentIndexer 入库。

## 成员清单

- `markdown_parser.py`: Markdown 标题解析器，按 `#` 标题切分 Section，被 indexer._ingest_markdown() 调用
- `yaml_parser.py`: YAML 文档解析器，提取 frontmatter metadata 与内容块
- `icd_parser.py`: ICD YAML 专用解析器，提取接口控制文档参数列表
- `docx_parser.py`: Word (.docx) 解析器，按 Heading 样式切分 Section，依赖 python-docx
- `xlsx_parser.py`: Excel (.xlsx) 解析器与 CSV 解析器；xlsx 按 Sheet 名切分，csv 按文件名单节，依赖 openpyxl
- `pdf_parser.py`: PDF 解析器，按页切分 Section，依赖 pypdf；仅支持文字型 PDF

[PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
