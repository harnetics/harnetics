# [INPUT]: 依赖 ImportService、Repository 与 RetrievalPlanner
# [OUTPUT]: 提供候选来源与模板排序的回归测试
# [POS]: tests 目录中的检索规划测试，锁定 Task 5 的候选选择行为
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from harnetics.importer import ImportService
from harnetics.repository import Repository
from harnetics.retrieval import RetrievalPlanner


def test_retrieval_planner_returns_template_and_ranked_sources(
    temp_db_path,
    fixture_root,
) -> None:
    repo = Repository(temp_db_path)
    importer = ImportService(repo)
    importer.import_file(fixture_root / "fixtures" / "requirements" / "DOC-SYS-001.md")
    importer.import_file(fixture_root / "fixtures" / "design" / "DOC-DES-001.md")
    importer.import_file(fixture_root / "fixtures" / "templates" / "DOC-TPL-001.md")

    planner = RetrievalPlanner(repo)
    plan = planner.plan(
        topic="TQ-12 地面试车测试大纲",
        department="动力系统部",
        target_doc_type="TestPlan",
        target_system_level="Subsystem",
    )

    assert plan.template.name == "地面试验测试大纲编写模板"
    assert [document.doc_id for document in plan.documents[:2]] == ["DOC-DES-001", "DOC-SYS-001"]
