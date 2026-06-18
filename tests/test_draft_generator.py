from harnetics.engine.draft_generator import _build_system_prompt
from harnetics.llm.prompts import DRAFT_SYSTEM_PROMPT


def test_build_system_prompt_returns_base_prompt_without_evolution() -> None:
    assert _build_system_prompt() == DRAFT_SYSTEM_PROMPT
