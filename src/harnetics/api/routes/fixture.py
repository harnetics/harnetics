"""
# [INPUT]: 依赖 FastAPI、engine.fixture_runner (list_scenarios/run_scenario/import_fixture_dir)
# [OUTPUT]: 对外提供 fixture_router: POST /api/fixture/import, GET /api/fixture/scenarios, POST /api/fixture/run
# [POS]: api/routes 的夹具域端点，供前端测试实验室面板调用；无 LLM 依赖，全链路本地执行
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from harnetics.engine.fixture_runner import (
    FixtureRunResult,
    FixtureScenario,
    import_fixture_dir,
    list_scenarios,
    run_scenario,
)

router = APIRouter(prefix="/api/fixture", tags=["fixture"])
logger = logging.getLogger("uvicorn.error")

# ---- 默认夹具目录（相对于服务器 cwd / 项目根）------
_DEFAULT_BASE = "fixtures/evaluator-test"


# ---- 请求体 -------------------------------------------------------------

class ImportRequest(BaseModel):
    path: str = _DEFAULT_BASE


class RunRequest(BaseModel):
    scenario_id: str
    base_dir: str = _DEFAULT_BASE


# ---- 辅助转换 -----------------------------------------------------------

def _scenario_to_dict(s: FixtureScenario) -> dict:
    return {
        "scenario_id": s.scenario_id,
        "evaluator": s.evaluator,
        "label": s.label,
        "expected_outcome": s.expected_outcome,
        "fixture_path": s.fixture_path,
    }


def _result_to_dict(r: FixtureRunResult) -> dict:
    return {
        "scenario_id": r.scenario_id,
        "draft_id": r.draft_id,
        "outcome": r.outcome,
        "expected_outcome": r.expected_outcome,
        "match": r.match,
        "eval_results": r.eval_results,
        "error": r.error,
    }


# ---- 端点 ---------------------------------------------------------------

@router.post("/import")
def fixture_import(req: ImportRequest) -> dict:
    """将指定路径下的夹具源文档批量导入图谱（幂等）。"""
    path = Path(req.path)
    if not path.is_dir():
        raise HTTPException(status_code=400, detail=f"路径不存在或不是目录: {req.path}")
    try:
        doc_ids = import_fixture_dir(path)
    except Exception as exc:
        logger.exception("fixture.import.failed path=%s", req.path)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "ok", "imported": len(doc_ids), "doc_ids": doc_ids}


@router.get("/scenarios")
def fixture_scenarios(base_dir: str = _DEFAULT_BASE) -> list[dict]:
    """返回 evaluator-test 下所有可运行 DRAFT 场景的元数据列表。"""
    scenarios = list_scenarios(base_dir)
    return [_scenario_to_dict(s) for s in scenarios]


@router.post("/run")
def fixture_run(req: RunRequest) -> dict:
    """运行单个场景：评估夹具草稿 → 写进化信号 → 返回结果。"""
    try:
        result = run_scenario(req.scenario_id, req.base_dir)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("fixture.run.failed scenario_id=%s", req.scenario_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return _result_to_dict(result)


@router.post("/run-all")
def fixture_run_all(base_dir: str = _DEFAULT_BASE) -> dict:
    """批量运行所有场景，返回聚合结果。"""
    scenarios = list_scenarios(base_dir)
    results: list[dict] = []
    passed = failed = 0
    for s in scenarios:
        try:
            r = run_scenario(s.scenario_id, base_dir)
            results.append(_result_to_dict(r))
            if r.match:
                passed += 1
            else:
                failed += 1
        except Exception as exc:
            results.append({
                "scenario_id": s.scenario_id,
                "error": str(exc),
                "outcome": "error",
                "expected_outcome": s.expected_outcome,
                "match": False,
                "eval_results": [],
                "draft_id": "",
            })
            failed += 1
    return {
        "total": len(scenarios),
        "passed": passed,
        "failed": failed,
        "results": results,
    }
