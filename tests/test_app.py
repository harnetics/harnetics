# [INPUT]: 依赖 fastapi.testclient 的 TestClient，依赖 harnetics.app 的 create_app
# [OUTPUT]: 提供 healthcheck 与 app.state.settings 装配行为的回归测试
# [POS]: tests 目录中的首个冒烟测试，验证应用骨架可被导入、响应 /health，并挂载默认 settings
# [PROTOCOL]: 变更时更新此头部，然后检查 AGENTS.md

from fastapi.testclient import TestClient

from harnetics.app import create_app
from harnetics.config import Settings


def test_healthcheck_returns_ok() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_state_settings_matches_defaults() -> None:
    app = create_app()

    assert isinstance(app.state.settings, Settings)
    assert app.state.settings == Settings()
