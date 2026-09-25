from __future__ import annotations

import asyncio
import sys
import threading
import types

from adaptive_agents.team_skills.consumer import ConsumerSource
import adaptive_agents.team_skills.mcp_server as mcp_module


def test_mcp_runs_independent_context_starts_concurrently(monkeypatch) -> None:
    class FakeMCPServer:
        def __init__(self, _name: str) -> None:
            self.tools = {}

        def tool(self):
            def register(function):
                self.tools[function.__name__] = function
                return function

            return register

    barrier = threading.Barrier(2)
    created: list[str] = []

    class FakeResult:
        def __init__(self, skill_id: str) -> None:
            self.skill_id = skill_id

        def to_data(self) -> dict[str, object]:
            return {"skill_id": self.skill_id}

    class FakeSession:
        def __init__(self, context_id: str) -> None:
            self.context_id = context_id

        def select_exact(self, skill_id: str) -> FakeResult:
            return FakeResult(skill_id)

    class FakeService:
        def __init__(self, _selector) -> None:
            pass

        def start(self, working_directory, *, source, offline):
            barrier.wait(timeout=2)
            session = FakeSession(str(working_directory))
            created.append(session.context_id)
            return session

    fake_server_module = types.ModuleType("mcp.server")
    fake_server_module.MCPServer = FakeMCPServer
    fake_mcp_module = types.ModuleType("mcp")
    fake_mcp_module.server = fake_server_module
    monkeypatch.setitem(sys.modules, "mcp", fake_mcp_module)
    monkeypatch.setitem(sys.modules, "mcp.server", fake_server_module)
    monkeypatch.setattr(mcp_module, "TeamSkillsContextService", FakeService)
    monkeypatch.setattr(mcp_module, "selector_for", lambda _name: object())

    server = mcp_module.create_mcp_server(
        selector_name="codex",
        source=ConsumerSource("unused", "main", "."),
    )

    async def exercise() -> tuple[dict[str, object], dict[str, object]]:
        return await asyncio.gather(
            server.tools["team_skills_get"]("one", "context-one"),
            server.tools["team_skills_get"]("two", "context-two"),
        )

    first, second = asyncio.run(exercise())

    assert {first["skill_id"], second["skill_id"]} == {"one", "two"}
    assert set(created) == {"context-one", "context-two"}
