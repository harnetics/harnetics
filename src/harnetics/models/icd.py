# [INPUT]: 依赖 dataclasses
# [OUTPUT]: 对外提供 ICDParameter
# [POS]: models 包的接口控制子域，描述 ICD 参数条目
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ICDParameter:
    param_id: str
    doc_id: str
    name: str
    interface_type: str
    subsystem_a: str
    subsystem_b: str
    value: str
    unit: str
    range_: str = ""
    owner_department: str = ""
    version: str = ""
