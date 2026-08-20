"""Zero-token default trash-talk provider — canned sentence bank only.

Ships as the default so a full game is completable and gradeable with no
API keys configured (NFR-8). `ollama`/`claude_api`/`claude_cli` providers
(later stages) implement the same `TrashTalkProvider` contract with a real
LLM call, but never choose the move either. FR-8 allows the thief's hints
to lie — that's deferred until the audit/crypto layer (stage 6) exists to
make a caught lie costly; this stage's lines are flavor text, not yet
tied to (true or false) position claims.
"""

from __future__ import annotations

from bb_ai_12_thief.llm.provider_base import TrashTalkProvider

_THIEF_LINES = [
    "You'll never catch me.",
    "I was never even here.",
    "Slower than my grandmother, officer.",
    "Try looking the other way.",
]


class TemplateProvider(TrashTalkProvider):
    """Cycles a fixed, thief-flavored sentence bank — zero LLM tokens."""

    def _generate(self, turn: int) -> str:
        return _THIEF_LINES[turn % len(_THIEF_LINES)]
