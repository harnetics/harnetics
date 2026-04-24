# [INPUT]: 依赖 python-docx 库与 models.document.Section
# [OUTPUT]: 对外提供 parse_docx(file_path, doc_id) -> list[Section]
# [POS]: parsers 包的 Word 文档解析器，按 Heading 样式切分章节
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from pathlib import Path

from harnetics.models.document import Section

# ================================================================
# Word (.docx) 解析器
# ================================================================

def parse_docx(file_path: str, doc_id: str) -> list[Section]:
    """将 .docx 文件按 Word Heading 样式切分为 Section 列表。

    策略：
    - 段落 style.name 以 "Heading" 开头时，开启新 Section
    - 其余段落追加到当前 Section 的 content
    - 若文档无任何内容，返回含单个空 Section 的列表
    """
    from docx import Document  # lazy import，避免启动时硬依赖

    doc = Document(str(Path(file_path)))
    sections: list[Section] = []
    current_heading: str = "(preamble)"
    current_level: int = 0
    current_parts: list[str] = []

    def _flush(order: int) -> None:
        content = "\n".join(p for p in current_parts if p.strip())
        sections.append(
            Section(
                section_id=f"{doc_id}-sec-{order}",
                doc_id=doc_id,
                heading=current_heading,
                content=content,
                level=current_level,
                order_index=order,
            )
        )

    for para in doc.paragraphs:
        text = para.text.strip()
        style_name: str = para.style.name if para.style else ""

        if style_name.startswith("Heading"):
            # ---- 保存上一节 ----
            if current_parts or current_heading != "(preamble)":
                _flush(len(sections))
            # ---- 推断层级（"Heading 1" → level=1）----
            try:
                level = int(style_name.split()[-1])
            except (ValueError, IndexError):
                level = 1
            current_heading = text or f"(untitled heading {len(sections)})"
            current_level = level
            current_parts = []
        else:
            if text:
                current_parts.append(text)

    # ---- 最后一节 ----
    _flush(len(sections))

    if not sections:
        return [
            Section(
                section_id=f"{doc_id}-sec-0",
                doc_id=doc_id,
                heading="(empty document)",
                content="",
                level=0,
                order_index=0,
            )
        ]

    return sections
