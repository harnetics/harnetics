# [INPUT]: 依赖 Python stdlib re；处理 release 正文与安装包指引块
# [OUTPUT]: 对外提供 merge_install_guide(body, guide)
# [POS]: release notes 纯文本拼装辅助模块，被发布脚本与测试复用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import re

_INSTALL_GUIDE_BLOCK_RE = re.compile(
    r"\n*<!-- hermes-install-guide:start -->.*?<!-- hermes-install-guide:end -->\n*",
    re.S,
)


def merge_install_guide(body: str, guide: str) -> str:
    """Append or replace the install-guide block in a release body."""
    normalized_body = body.rstrip()
    normalized_guide = guide.strip()
    if _INSTALL_GUIDE_BLOCK_RE.search(normalized_body):
        merged = _INSTALL_GUIDE_BLOCK_RE.sub(
            "\n\n" + normalized_guide + "\n",
            normalized_body,
        )
    else:
        merged = normalized_body + "\n\n" + normalized_guide + "\n"
    return merged.strip() + "\n"
