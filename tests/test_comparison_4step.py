# [INPUT]: 依赖 harnetics.engine.comparison_4step 与 models.document.Section
# [OUTPUT]: 提供四步比对引擎单元契约测试，锁定 Step1 输出预算与异常 fallback 行为
# [POS]: tests 的比对审查回归测试，保护客户端文档比对功能不被 provider 大输出限制拖死
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from harnetics.engine.comparison_4step import Comparison4StepEngine
from harnetics.models.document import Section


class RecordingLLM:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate_draft(self, system_prompt: str, context: str, user_request: str, *, max_tokens: int | None = None) -> str:
        self.calls.append({
            "system_prompt": system_prompt,
            "context": context,
            "user_request": user_request,
            "max_tokens": max_tokens,
        })
        raise TimeoutError("provider timed out")


def test_step1_uses_configured_output_budget_and_falls_back_on_timeout(monkeypatch) -> None:
    monkeypatch.setenv("HARNETICS_COMPARISON_STEP1_MAX_TOKENS", "4096")
    llm = RecordingLLM()
    engine = Comparison4StepEngine(llm=llm)  # type: ignore[arg-type]
    sections = [
        Section(section_id="S1", doc_id="REQ", heading="6.1 范围", content="审查专设安全设施范围。"),
        Section(section_id="S2", doc_id="REQ", heading="6.2 要求", content="审查功能、边界和验收准则。"),
    ]

    requirements = engine._step1_scan_requirements(sections)

    assert llm.calls[0]["max_tokens"] == 4096
    assert [req["id"] for req in requirements] == ["R001", "R002"]
