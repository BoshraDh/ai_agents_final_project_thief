"""Tests for the league wire message builders."""

from __future__ import annotations

from bb_ai_12_thief.crypto.commit_reveal import CommitRevealLog
from bb_ai_12_thief.crypto.step0 import Step0Declaration
from bb_ai_12_thief.domain.pheromones import PheromoneField
from bb_ai_12_thief.domain.protocol import Position, Role
from bb_ai_12_thief.league.messages import build_audit, build_negotiate, build_turn

_SCENT_CONFIG = {"pheromones": {
    "pheromone_center_intensity": 0.9, "pheromone_decay": 0.1, "pheromone_grid_size": 5,
}}


def test_build_negotiate_nests_group_id_at_top_level_and_inside_identity():
    message = build_negotiate({"a": 1}, "nonce", "sig", "bb-ai-12", ["id-1", "id-2"])
    assert message["group_id"] == "bb-ai-12"
    assert message["identity"] == {"group_id": "bb-ai-12", "members": ["id-1", "id-2"]}


def test_build_turn_includes_required_fields_and_omits_unset_optionals():
    scent = PheromoneField.from_config(_SCENT_CONFIG)
    scent.step(Position(0, 0))
    message = build_turn(1, Role.THIEF, "hint text", scent, "deadbeef" * 8)
    assert message["step"] == 1
    assert message["sender"] == "thief"
    assert message["smell_grid"] == {"0,0": 0.9}
    assert "capture_claim" not in message
    assert "claim_response" not in message
    assert "win_claim" not in message


def test_build_turn_includes_win_claim_when_given():
    scent = PheromoneField.from_config(_SCENT_CONFIG)
    message = build_turn(
        1, Role.THIEF, "hint", scent, "commit", win_claim={"type": "survival"}
    )
    assert message["win_claim"] == {"type": "survival"}


def test_build_audit_puts_a_system_spec_record_first():
    log = CommitRevealLog()
    log.seal(1, {"move": "N"})
    step0 = Step0Declaration.create("bb-ai-12")
    envelope = build_audit(Role.THIEF, log, "survival", step0)
    assert envelope["sender"] == "thief"
    assert envelope["result_claim"] == "survival"
    assert envelope["records"][0]["payload"]["type"] == "system_spec"
    assert len(envelope["records"]) == 2
