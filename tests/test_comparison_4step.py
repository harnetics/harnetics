# [INPUT]: 依赖 harnetics.engine.comparison_4step 与 models.document.Section
# [OUTPUT]: 提供四步比对引擎单元契约测试，锁定 Step1/Step3 输出预算与异常 fallback 行为
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


class Step3RecordingLLM:
    def __init__(self) -> None:
        self.max_tokens: list[int | None] = []

    def generate_draft(self, system_prompt: str, context: str, user_request: str, *, max_tokens: int | None = None) -> str:
        self.max_tokens.append(max_tokens)
        return '[{"requirement_id":"R001","chapter":"6.1","requirement_heading":"6.1 范围","requirement_content":"审查范围","status":"covered","detail":"已覆盖","requirement_ref":"6.1","response_ref":"FSAR 6.1"}]'


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


def test_step3_uses_configured_output_budget(monkeypatch) -> None:
    monkeypatch.setenv("HARNETICS_COMPARISON_STEP3_MAX_TOKENS", "12345")
    llm = Step3RecordingLLM()
    engine = Comparison4StepEngine(llm=llm)  # type: ignore[arg-type]

    findings = engine._evaluate_one_batch(
        [{"id": "R001", "heading": "6.1 范围", "content": "审查范围", "section_ref": "6.1"}],
        {0: [{"heading": "FSAR 6.1", "text": "包含审查范围。"}]},
    )

    assert llm.max_tokens == [12345]
    assert findings[0]["status"] == "covered"


def test_step4_missing_model_summary_uses_computed_fallback(monkeypatch) -> None:
    monkeypatch.setenv("HARNETICS_COMPARISON_STEP4_MAX_TOKENS", "4096")
    engine = Comparison4StepEngine(llm=RecordingLLM())  # type: ignore[arg-type]
    engine._step1_scan_requirements = lambda _: [  # type: ignore[method-assign]
        {"id": "R001", "heading": "要求1", "content": "内容1", "section_ref": "6.1"},
        {"id": "R002", "heading": "要求2", "content": "内容2", "section_ref": "6.2"},
    ]
    engine._step2_match_one = lambda _req, _sections: []  # type: ignore[method-assign]
    engine._step3_evaluate_batched = lambda _reqs, _matches, _sections: iter([[  # type: ignore[method-assign]
        {"requirement_id": "R001", "chapter": "6.1", "requirement_heading": "要求1", "status": "covered"},
        {"requirement_id": "R002", "chapter": "6.2", "requirement_heading": "要求2", "status": "missing"},
    ]])
    engine._step4_global_review = lambda _findings: {"compliance_rate": 0.5, "corrections": []}  # type: ignore[method-assign]

    events = list(engine.analyze_4step_streaming(
        "CMP-TEST",
        [Section(section_id="R1", doc_id="REQ", heading="6.1", content="内容1")],
        [Section(section_id="S1", doc_id="RESP", heading="6.1", content="应答")],
        "req.pdf",
        "resp.pdf",
    ))
    completed = events[-1]

    assert completed["summary"] == "自动计算：共审查2项，已覆盖1项，部分覆盖0项，未覆盖1项，待明确0项。"
    assert "未生成全局结论" not in completed["analysis_md"]
