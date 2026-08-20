"""Tests for the Manhattan-distance heuristic and its role subclasses."""

from __future__ import annotations

from bb_ai_12_thief.domain.barriers import BarrierSet
from bb_ai_12_thief.domain.board import Board
from bb_ai_12_thief.domain.protocol import Direction, Position
from bb_ai_12_thief.strategy.heuristic_brain import HeuristicBrain, manhattan
from bb_ai_12_thief.strategy.thief_brain import ThiefBrain


def test_manhattan_distance():
    assert manhattan(Position(0, 0), Position(3, 4)) == 7


def test_thief_brain_moves_away_from_the_police():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    brain = ThiefBrain()
    move = brain.decide_move(board, barriers, Position(3, 3), Position(0, 0))
    assert move in (Direction.SOUTH, Direction.EAST)


def test_thief_brain_stays_at_the_farthest_reachable_corner():
    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    brain = ThiefBrain()
    move = brain.decide_move(board, barriers, Position(6, 6), Position(0, 0))
    assert move == Direction.STAY


def test_pursuer_sign_moves_toward_the_evader():
    class PursuerBrain(HeuristicBrain):
        _sign = 1

    board = Board(size=7)
    barriers = BarrierSet(max_barriers=14)
    brain = PursuerBrain()
    move = brain.decide_move(board, barriers, Position(0, 0), Position(3, 3))
    assert move in (Direction.SOUTH, Direction.EAST)
