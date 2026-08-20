"""Tests for the turn-loop (stage 6: real brain + hint + sealed moves), no real networking."""

from __future__ import annotations

from bb_ai_12_thief.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_thief.domain.barriers import BarrierSet
from bb_ai_12_thief.domain.belief import BeliefState
from bb_ai_12_thief.domain.board import Board
from bb_ai_12_thief.domain.pheromones import PheromoneField
from bb_ai_12_thief.domain.protocol import Direction, Position
from bb_ai_12_thief.llm.template_provider import TemplateProvider
from bb_ai_12_thief.runtime.peer_runtime import PeerRuntime
from bb_ai_12_thief.strategy.thief_brain import ThiefBrain

_PHEROMONE_CONFIG = {
    "pheromones": {
        "pheromone_center_intensity": 0.9,
        "pheromone_decay": 0.10,
        "pheromone_grid_size": 5,
    }
}


def _runtime() -> PeerRuntime:
    return PeerRuntime(
        host="127.0.0.1",
        port=9999,
        opponent_url="http://unused",
        board=Board(size=7),
        barriers=BarrierSet(max_barriers=14),
        belief=BeliefState(own_position=Position(3, 3), opponent_position=Position(0, 0)),
        brain=ThiefBrain(),
        trash_talk=TemplateProvider(hint_max_words=15),
        opponent_scent=PheromoneField.from_config(_PHEROMONE_CONFIG),
        commit_log=CommitRevealLog(),
    )


def test_decide_move_uses_the_brain_to_evade_the_tracked_opponent():
    assert _runtime()._decide_move() == Direction.SOUTH


def test_run_turn_loop_sends_the_requested_number_of_moves_with_hints(monkeypatch):
    runtime = _runtime()
    sent = []

    def fake_send_move(direction: str, turn: int, hint: str = "") -> dict[str, str | int]:
        sent.append((direction, turn, hint))
        return {"direction": "STAY", "turn": turn, "hint": "..."}

    monkeypatch.setattr(runtime.transport, "send_move", fake_send_move)
    runtime.run_turn_loop(3)
    assert [t for _, t, _ in sent] == [1, 2, 3]
    assert all(hint for _, _, hint in sent)
    assert runtime.belief.opponent_position == Position(0, 0)
    assert runtime.opponent_scent.intensity_at(Position(0, 0)) > 0


def test_run_turn_loop_seals_every_move_and_passes_audit(monkeypatch):
    runtime = _runtime()
    monkeypatch.setattr(
        runtime.transport,
        "send_move",
        lambda direction, turn, hint="": {"direction": "STAY", "turn": turn, "hint": "..."},
    )
    runtime.run_turn_loop(3)
    assert runtime.commit_log.audit()
    assert runtime.commit_log.tampered_turns() == []
