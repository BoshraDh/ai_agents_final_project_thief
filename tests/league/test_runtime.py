"""Tests for LeagueRuntime's negotiate/play loop, against a fake transport
(no real network) that mirrors a cooperative opponent's replies.
"""

from __future__ import annotations

import asyncio

from bb_ai_12_thief.crypto.step0 import Step0Declaration
from bb_ai_12_thief.domain.barriers import BarrierSet
from bb_ai_12_thief.domain.board import Board
from bb_ai_12_thief.domain.pheromones import PheromoneField
from bb_ai_12_thief.domain.protocol import GameOutcome, Position, Role
from bb_ai_12_thief.league.inbox import LeagueInbox
from bb_ai_12_thief.league.runtime import _CLOSING_TURN_TIMEOUT_SEC, LeagueRuntime
from bb_ai_12_thief.league.terms import terms_signature, to_wire_terms
from bb_ai_12_thief.llm.template_provider import TemplateProvider
from bb_ai_12_thief.strategy.thief_brain import ThiefBrain

_SHARED = {
    "board_and_agents": {
        "grid_size": 7, "cop_start": [0, 0], "thief_start": [3, 3],
        "axis_origin_corner": "top-left", "axis_start_index": 0,
    },
    "world": {"map_area": "New York", "hint_max_words": 15},
    "movement_and_barriers": {"max_barriers": 14, "max_moves": 35, "survival_threshold": 2},
    "pheromones": {
        "pheromone_center_intensity": 0.9, "pheromone_decay": 0.1, "pheromone_grid_size": 5,
    },
    "network_and_league": {"num_games": 6},
}


class _FakeTransport:
    """No-op sends; a cooperative opponent's replies are pre-seeded via `inbox`."""

    def __init__(self) -> None:
        self.sent_turns: list[dict] = []
        self.audits: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return None

    async def negotiate(self, message: dict) -> dict:
        return {"ok": True}

    async def send_turn(self, message: dict) -> dict:
        self.sent_turns.append(message)
        return {"ok": True}

    async def send_audit(self, payload: dict) -> dict:
        self.audits.append(payload)
        return {"ok": True}


def _runtime(inbox: LeagueInbox, transport: _FakeTransport, survival_threshold: int = 2):
    return LeagueRuntime(
        role=Role.THIEF,
        own_position=Position(row=3, col=3),
        opponent_start=Position(row=0, col=0),
        board=Board(size=7),
        barriers=BarrierSet(max_barriers=14),
        brain=ThiefBrain(),
        trash_talk=TemplateProvider(hint_max_words=15),
        own_scent=PheromoneField.from_config(_SHARED),
        survival_threshold=survival_threshold,
        shared_config=_SHARED,
        group_id="bb-ai-12",
        members=["id-1"],
        transport=transport,
        inbox=inbox,
        step0=Step0Declaration.create("bb-ai-12"),
        handshake_timeout_sec=1.0,
        turn_timeout_sec=1.0,
    )


def test_negotiate_returns_true_when_terms_and_signature_match():
    inbox = LeagueInbox()
    terms = to_wire_terms(_SHARED)
    nonce = "deadbeef"
    inbox.receive_negotiate(
        {"terms": terms, "nonce": nonce, "signature": terms_signature(terms, nonce)}
    )
    runtime = _runtime(inbox, _FakeTransport())
    assert asyncio.run(runtime.negotiate())


def test_negotiate_returns_false_when_terms_differ():
    inbox = LeagueInbox()
    inbox.receive_negotiate({"terms": {"wrong": 1}, "nonce": "x", "signature": "y"})
    runtime = _runtime(inbox, _FakeTransport())
    assert not asyncio.run(runtime.negotiate())


def test_play_stops_early_once_survival_threshold_is_reached():
    inbox = LeagueInbox()
    for step in range(1, 3):
        inbox.receive_turn({"step": step, "smell_grid": {}})
    transport = _FakeTransport()
    runtime = _runtime(inbox, transport, survival_threshold=2)
    outcome = asyncio.run(runtime.play(10))
    assert outcome == GameOutcome.SURVIVED
    assert runtime.final_turn == 2
    assert transport.audits[0]["result_claim"] == "survival"


def test_play_runs_to_the_turn_cap_when_nothing_terminal_happens():
    inbox = LeagueInbox()
    for step in range(1, 4):
        inbox.receive_turn({"step": step, "smell_grid": {}})
    transport = _FakeTransport()
    runtime = _runtime(inbox, transport, survival_threshold=100)
    outcome = asyncio.run(runtime.play(3))
    assert outcome == GameOutcome.ONGOING
    assert runtime.final_turn is None


def test_play_concludes_survived_locally_when_opponent_goes_silent_at_the_boundary():
    # Nothing is ever delivered to the inbox -- every wait_for_turn times out.
    inbox = LeagueInbox()
    transport = _FakeTransport()
    runtime = _runtime(inbox, transport, survival_threshold=1)
    outcome = asyncio.run(runtime.play(5))
    assert outcome == GameOutcome.SURVIVED
    assert runtime.final_turn == 1
    assert len(transport.sent_turns) == 1


def test_closing_turn_does_not_burn_the_full_turn_timeout(monkeypatch):
    """Regression test for a stall found live 2026-08-26 vs SMNGRP05.

    Once we have claimed the win the opponent has no further turn to send us,
    so the normal turn timeout was pure dead wait -- and it ran down *after*
    they had already opened their own 90s audit window. With turn_timeout_sec
    at 180 our submit_audit landed ~90s too late and they recorded it as never
    having arrived, even though their server had accepted it.
    """
    inbox = LeagueInbox()
    transport = _FakeTransport()
    runtime = _runtime(inbox, transport, survival_threshold=1)
    runtime.turn_timeout_sec = 999.0
    seen: list[float] = []

    def _spy(self, step, timeout_sec, *args, **kwargs):
        seen.append(timeout_sec)
        raise TimeoutError(f"turn {step}")

    monkeypatch.setattr(LeagueInbox, "wait_for_turn", _spy)
    outcome = asyncio.run(runtime.play(35))

    assert outcome == GameOutcome.SURVIVED
    assert seen == [_CLOSING_TURN_TIMEOUT_SEC]


def test_negotiate_plays_on_when_only_their_turn_arrived(capsys):
    # Their greeting for this sub-game was eaten by our previous sub-game's
    # process; their turn proves the handshake happened. Terms are unverifiable,
    # which is treated exactly like a mismatch -- warn, and play.
    inbox = LeagueInbox()
    inbox.receive_turn({"step": 1, "hint": "their opener"})
    runtime = _runtime(inbox, _FakeTransport())
    assert asyncio.run(runtime.negotiate(2)) is False
    assert "playing on, terms unverified" in capsys.readouterr().out


def test_negotiate_that_falls_back_to_a_turn_still_lets_us_send_ours():
    # The whole point: before the fix we never sent a single turn in sub-game 2.
    inbox = LeagueInbox()
    inbox.receive_turn({"step": 1, "hint": "their opener"})
    transport = _FakeTransport()
    runtime = _runtime(inbox, transport)
    asyncio.run(runtime.negotiate(2))
    asyncio.run(runtime.play(1))
    assert [t["step"] for t in transport.sent_turns] == [1]
