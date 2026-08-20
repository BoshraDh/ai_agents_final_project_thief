"""Factory: resolve which brain instance to use from `[strategy]` config.

Stage 3 ships a single option (`ThiefBrain`, the Manhattan-distance
heuristic) — `resolve_brain` exists now so a later custom `thief_class`
override in `config/game.toml` never needs to touch the runtime layer.
"""

from __future__ import annotations

import importlib
from typing import Any

from bb_ai_12_thief.strategy.base import BrainBase
from bb_ai_12_thief.strategy.thief_brain import ThiefBrain


def resolve_brain(private_config: dict[str, Any]) -> BrainBase:
    """Reads `[strategy]` from `config/game.toml`; defaults to `ThiefBrain`."""
    strategy_cfg = private_config.get("strategy", {})
    class_path = strategy_cfg.get("thief_class")
    if not class_path:
        return ThiefBrain()
    return _load_custom_brain(class_path)


def _load_custom_brain(class_path: str) -> BrainBase:
    module_name, _, class_name = class_path.partition(":")
    module = importlib.import_module(module_name)
    brain_cls = getattr(module, class_name)
    return brain_cls()
