"""MCP façade over the read-only transient Team Skills context service."""

from __future__ import annotations

import asyncio
import os
from collections import OrderedDict

from .consumer import ConsumerSource, default_consumer_source
from .context import TeamSkillsContextService, TransientContextSession
from .preferences import load_selector_preference
from .repository import TeamSkillsError
from .selector import resolve_selector_name, selector_for


def create_mcp_server(
    *,
    selector_name: str | None = None,
    source: ConsumerSource | None = None,
    offline: bool = False,
):
    """Create a stdio-capable MCP server without starting its transport."""

    try:
        from mcp.server import MCPServer
    except ImportError as error:  # pragma: no cover - packaging dependency guard
        raise TeamSkillsError(
            "MCP support is unavailable; install the application with its runtime dependencies"
        ) from error

    preference = (
        load_selector_preference()
        if selector_name is None and not os.environ.get("TEAM_SKILLS_SELECTOR")
        else None
    )
    resolved_selector = resolve_selector_name(selector_name, preference=preference)
    service = TeamSkillsContextService(selector_for(resolved_selector))
    source = default_consumer_source() if source is None else source
    sessions: OrderedDict[str, TransientContextSession] = OrderedDict()
    session_locks: dict[str, asyncio.Lock] = {}
    server = MCPServer("team-skills")

    def remember(session: TransientContextSession) -> None:
        sessions[session.context_id] = session
        session_locks.setdefault(session.context_id, asyncio.Lock())
        sessions.move_to_end(session.context_id)
        while len(sessions) > 32:
            expired, _session = sessions.popitem(last=False)
            session_locks.pop(expired, None)

    def existing(context_id: str) -> TransientContextSession:
        session = sessions.get(context_id)
        if session is None:
            raise TeamSkillsError(
                "transient context is unknown or expired; start a new Team Skills lookup"
            )
        sessions.move_to_end(context_id)
        return session

    @server.tool()
    async def team_skills_find(
        task: str,
        working_directory: str = ".",
        context_id: str | None = None,
    ) -> dict[str, object]:
        """Find validated team Skills for a task without writing into the working directory.

        Reuse context_id for a follow-up that adds, corrects, or replaces the earlier intent.
        """

        if context_id is not None:
            session = existing(context_id)
        else:
            session = await asyncio.to_thread(
                service.start,
                working_directory,
                source=source,
                offline=offline,
            )
        remember(session)
        async with session_locks[session.context_id]:
            result = await asyncio.to_thread(session.select, task)
        return result.to_data()

    @server.tool()
    async def team_skills_get(
        skill_id: str,
        working_directory: str = ".",
    ) -> dict[str, object]:
        """Open one exact Skill by ID after native admission and validation."""

        session = await asyncio.to_thread(
            service.start,
            working_directory,
            source=source,
            offline=offline,
        )
        remember(session)
        async with session_locks[session.context_id]:
            result = await asyncio.to_thread(session.select_exact, skill_id)
        return result.to_data()

    @server.tool()
    async def team_skills_read(
        context_id: str,
        skill_id: str,
        path: str = "SKILL.md",
    ) -> dict[str, object]:
        """Read one text file from a Skill selected in this in-memory context."""

        session = existing(context_id)
        async with session_locks[session.context_id]:
            content = session.read_selected_file(skill_id, path)
        return {
            "schema_version": 1,
            "context_id": context_id,
            "skill_id": skill_id,
            "path": path,
            "content": content,
            "writes": [],
        }

    return server


def run_mcp_server(
    *,
    selector_name: str | None = None,
    source: ConsumerSource | None = None,
    offline: bool = False,
) -> None:
    """Serve Team Skills over local stdio MCP."""

    create_mcp_server(
        selector_name=selector_name,
        source=source,
        offline=offline,
    ).run()
