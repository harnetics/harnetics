# [INPUT]: 依赖 harnetics.engine.comparison_4step 与 models.document.Section
# [OUTPUT]: 提供四步比对引擎单元契约测试，锁定 Step1 稳定性、Step3 输出预算与异常 fallback 行为
# [POS]: tests 的比对审查回归测试，保护客户端文档比对功能不被 provider 大输出限制拖死
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from harnetics.engine.comparison_4step import Comparison4StepEngine, _STEP1_REQUIREMENT_CACHE
from harnetics.models.document import Section


class RecordingLLM:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def generate_draft(
        self,
        system_prompt: str,
        context: str,
        user_request: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.calls.append({
            "system_prompt": system_prompt,
            "context": context,
            "user_request": user_request,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })
        raise TimeoutError("provider timed out")


class EmptyLLM:
    def generate_draft(
        self,
        system_prompt: str,
        context: str,
        user_request: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.3,
    ) -> str:
        return "[]"


class ShouldNotCallLLM:
    def __init__(self) -> None:
        self.calls = 0

    def generate_draft(
        self,
        system_prompt: str,
        context: str,
        user_request: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.calls += 1
        return "[]"


class StableLLM:
    def __init__(self) -> None:
        self.calls = 0

    def generate_draft(
        self,
        system_prompt: str,
        context: str,
        user_request: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.3,
    ) -> str:
        self.calls += 1
        return '[{"id":"R001","heading":"稳定要求","content":"稳定内容","section_ref":"6.1"}]'


class Step3RecordingLLM:
    def __init__(self) -> None:
        self.max_tokens: list[int | None] = []

    def generate_draft(
        self,
        system_prompt: str,
        context: str,
        user_request: str,
        *,
        max_tokens: int | None = None,
        temperature: float = 0.3,
    ) -> str:
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


def test_step1_fallback_extracts_numbered_review_items_instead_of_pdf_pages() -> None:
    engine = Comparison4StepEngine(llm=EmptyLLM())  # type: ignore[arg-type]
    sections = [
        Section(section_id="P1", doc_id="REQ", heading="Page 1", content="标准审查大纲 第6章 专设安全设施"),
        Section(
            section_id="P2",
            doc_id="REQ",
            heading="Page 2",
            content="目 录\n6.1.1 专设安全设施的材料 ...... 1\n6.1.2 保护涂层系统 ...... 10",
        ),
        Section(
            section_id="P3",
            doc_id="REQ",
            heading="Page 3",
            content=(
                "1\n6.1.1 专设安全设施的材料\n审查责任\n主审——负责材料审查\nI．审查范围\n"
                "具体的审查范围如下：\n1. 材料和制造。审查用于专设安全设施建造的材料和制造工艺。\n"
                "2. 专设安全设施流体的成分和相容性。必须控制安全壳和堆芯喷淋冷却剂。"
            ),
        ),
        Section(
            section_id="P4",
            doc_id="REQ",
            heading="Page 4",
            content=(
                "II．验收准则\n1. 材料应符合适用规范并保存鉴定记录。\n"
                "2. 流体成分应满足系统功能要求。"
            ),
        ),
    ]

    requirements = engine._step1_scan_requirements(sections)

    assert [req["section_ref"] for req in requirements] == [
        "6.1.1.1",
        "6.1.1.2",
        "6.1.1.3",
        "6.1.1.4",
    ]
    assert all(not req["heading"].startswith("Page") for req in requirements)


def test_step1_caches_llm_requirements_for_same_requirement_file() -> None:
    _STEP1_REQUIREMENT_CACHE.clear()
    llm = StableLLM()
    engine = Comparison4StepEngine(llm=llm)  # type: ignore[arg-type]
    sections = [Section(section_id="S1", doc_id="REQ", heading="6.1", content="稳定审查内容")]

    first = engine._step1_scan_requirements(sections)
    second = engine._step1_scan_requirements(sections)

    assert first == second
    assert llm.calls == 1


def test_step1_uses_bounded_deterministic_fallback_without_llm_result() -> None:
    llm = ShouldNotCallLLM()
    engine = Comparison4StepEngine(llm=llm)  # type: ignore[arg-type]
    sections = [
        Section(
            section_id="P3",
            doc_id="REQ",
            heading="Page 3",
            content=(
                "6.2.1 安全壳功能设计\nI．审查范围\n"
                "1. 安全壳结构应满足设计压力和温度要求。\n"
                "2. 安全壳隔离功能应满足单一故障准则。"
            ),
        )
    ]

    requirements = engine._step1_scan_requirements(sections)

    assert [req["section_ref"] for req in requirements] == ["6.2.1.1", "6.2.1.2"]
    assert llm.calls == 1


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
