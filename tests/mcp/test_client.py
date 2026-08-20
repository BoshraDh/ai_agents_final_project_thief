"""Tests for the outbound MCP client, against an in-process FastMCP server.

`fastmcp.Client` accepts a `FastMCP` instance directly (in-memory transport,
no real socket) — used here so the round trip is verified without binding a
port, matching fastmcp's own recommended testing pattern.
"""

from __future__ import annotations

from bb_ai_12_thief.mcp.client import McpTransport
from bb_ai_12_thief.mcp.server import build_server
from bb_ai_12_thief.peer.turn_handler import TurnHandler


def test_send_commit_round_trips_in_process():
    handler = TurnHandler()
    mcp = build_server("test", handler)
    transport = McpTransport(mcp)
    reply = transport.send_commit("deadbeef", 1)
    assert reply == {"received": True, "turn": 1}
    assert handler.has_received_commit(1)


def test_send_reveal_returns_the_servers_own_prepared_reveal():
    handler = TurnHandler()
    handler.receive_commit(1, "deadbeef")
    handler.prepare_own_reveal(1, "S", "hi", "truth")
    mcp = build_server("test", handler)
    transport = McpTransport(mcp)
    reply = transport.send_reveal("N", "hello", "lie", 1)
    assert reply == {"move": "S", "hint": "hi", "intent": "truth", "turn": 1}
