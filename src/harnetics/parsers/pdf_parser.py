# [INPUT]: 依赖 pypdf 库与 models.document.Section
# [OUTPUT]: 对外提供 parse_pdf(file_path, doc_id) -> list[Section]
# [POS]: parsers 包的 PDF 解析器，按页切分章节（文字型 PDF）
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from pathlib import Path

from harnetics.models.document import Section

# ================================================================
# PDF 解析器
# ================================================================

def parse_pdf(file_path: str, doc_id: str) -> list[Section]:
    """将 .pdf 文件按页切分为 Section 列表。

    策略：
    - 每页生成一个 Section（heading="Page {n}"，content=提取的文字）
    - 无文字内容的页跳过
    - 若整个 PDF 无可提取文字，返回含单个占位 Section 的列表，提示无文字内容
    """
    from pypdf import PdfReader  # lazy import

    reader = PdfReader(str(Path(file_path)))
    sections: list[Section] = []

    for page_num, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = text.strip()
        if not text:
            continue
        sections.append(
            Section(
                section_id=f"{doc_id}-sec-{len(sections)}",
                doc_id=doc_id,
                heading=f"Page {page_num}",
                content=text,
                level=1,
                order_index=len(sections),
            )
        )

    if not sections:
        return [
            Section(
                section_id=f"{doc_id}-sec-0",
                doc_id=doc_id,
                heading="(no text content)",
                content="This PDF contains no extractable text. It may be a scanned document.",
                level=0,
                order_index=0,
            )
        ]

    return sections
