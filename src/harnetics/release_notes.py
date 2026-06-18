# [INPUT]: 依赖 Python stdlib re；处理 release 正文与安装包指引块
# [OUTPUT]: 对外提供 build_install_guide(version)、merge_install_guide(body, guide)
# [POS]: release notes 纯文本拼装辅助模块，被发布脚本与测试复用
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

import re

_INSTALL_GUIDE_BLOCK_RE = re.compile(
    r"\n*<!-- hermes-install-guide:start -->.*?<!-- hermes-install-guide:end -->\n*",
    re.S,
)


def build_install_guide(version: str) -> str:
    """Build the standard platform-selection guide for a release version."""
    return f"""<!-- hermes-install-guide:start -->
## 下载哪个安装包？

如果你是第一次下载安装包，请先看这里：

- **Windows 10 / 11（64 位）**：下载 `Harnetics_{version}_x64-setup.exe`
- **macOS Apple Silicon（M1 / M2 / M3 / M4）**：下载 `Harnetics_{version}_aarch64.dmg`
- **macOS Intel（老款 Intel 芯片 Mac）**：下载 `Harnetics_{version}_x64.dmg`
- **Linux**：当前 release **不提供** Linux 桌面安装包

### 不确定自己是哪种 Mac？

在 macOS 左上角点 ** → 关于本机**：

- 如果看到 **芯片：Apple M1 / M2 / M3 / M4**，请下载 `Harnetics_{version}_aarch64.dmg`
- 如果看到 **处理器：Intel**，请下载 `Harnetics_{version}_x64.dmg`

### 额外说明

- 当前 macOS 安装包尚未完成 Apple notarization；如果遇到系统拦截，需要按未签名应用方式手动放行
- 桌面安装包默认连接云端 OpenAI-compatible LLM / Embedding 服务；如需本地模型，请自行配置 Ollama
<!-- hermes-install-guide:end -->
""".strip()


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
