"""Thief's default brain: evade — maximize distance to the tracked police."""

from __future__ import annotations

from bb_ai_12_thief.strategy.heuristic_brain import HeuristicBrain


class ThiefBrain(HeuristicBrain):
    """Maximizes Manhattan distance to the tracked police position (flees)."""

    _sign = -1
