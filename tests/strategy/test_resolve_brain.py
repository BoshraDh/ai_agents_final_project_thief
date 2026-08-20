"""Tests for the `[strategy]` config-driven brain factory."""

from __future__ import annotations

from bb_ai_12_thief.strategy.resolve_brain import resolve_brain
from bb_ai_12_thief.strategy.thief_brain import ThiefBrain


def test_resolve_brain_defaults_to_thief_brain_when_unset():
    brain = resolve_brain({})
    assert isinstance(brain, ThiefBrain)


def test_resolve_brain_loads_the_configured_class_path():
    private_config = {
        "strategy": {"thief_class": "bb_ai_12_thief.strategy.thief_brain:ThiefBrain"}
    }
    brain = resolve_brain(private_config)
    assert isinstance(brain, ThiefBrain)
