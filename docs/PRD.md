# PRD — bb-ai-12 Thief Peer

## Purpose
A fully decentralized, peer-to-peer AI agent that plays the "thief" role in the
Police-Thief pursuit game defined by `police_thief_p2p.pdf` v3.0.0, against an
independently-developed "police" agent (sibling repo: `bb-ai-12-police`), with no central
server, no shared memory, and no referee.

## Functional requirements

- **FR-1 Board & movement**: play on a `grid_size x grid_size` grid (book minimum 7x7),
  4-orthogonal + STAY movement, no diagonals, no illegal off-board or barrier-blocked moves.
- **FR-2 Barriers (read-only for this side)**: the thief never places barriers but must
  respect them as blocked cells when planning moves, and may reason about likely barrier
  locations when choosing an escape route (stage 3+).
- **FR-3 Capture**: the thief loses a sub-game if the police lands on its true cell and
  issues an honest `capture_claim`; the thief must answer honestly when asked — a lie is
  caught by the crypto audit (stage 6) and forfeits.
- **FR-4 Survival cap**: the thief wins the sub-game by surviving `survival_threshold` steps
  uncaught.
- **FR-5 Scoring**: fixed point table (Appendix ו) — capture: cop 20 / thief 5; survival:
  cop 5 / thief 10; tie: 2/2; technical_loss: 0/0. Never hardcoded outside `domain/scoring.py`.
- **FR-6 Communication**: each peer is simultaneously an MCP server and client (FastMCP),
  P2P, no shared server (stage 2).
- **FR-7 Strategy**: the move decision is always a pure algorithm — never delegated to an
  LLM. Default ships as a Manhattan-distance + Bayesian-belief heuristic requiring zero LLM
  tokens (stage 3-4).
- **FR-8 Language/scent**: free-text hints capped at `hint_max_words`, may lie (deception is
  a legitimate thief tactic to smear the police's belief map); pheromone scent-trail belief
  modeling (stage 4).
- **FR-9 Integrity**: every move sealed via SHA-256 commit-reveal with a fresh nonce; a
  mutual post-game audit re-verifies every step (stage 6).
- **FR-10 Reporting**: four standardized JSON artifacts per game
  (`declaration_/config_/log_/result_<game_id>...json`), auto-emailed via Gmail API to the
  grader address, rate-limited by a Gatekeeper (stage 7).
- **FR-11 Config split**: shared, signed terms live in `config/game.json` (byte-identical to
  the police repo's copy); private, local-only settings live in `config/game.toml`.

## Non-functional requirements
- **NFR-1**: every Python source file ≤ 150 lines of code.
- **NFR-2**: ≥ 85% test coverage (`pytest --cov`).
- **NFR-3**: zero Ruff violations (`ruff check .`).
- **NFR-4**: no hardcoded game-rule numbers outside `config/game.json` and
  `domain/scoring.py` (which mirrors the book's fixed table verbatim, by design).
- **NFR-5**: no secrets committed (`credentials.json`, `token.json`, `.env` all gitignored).
- **NFR-6**: `uv`-managed dependencies only (no bare `pip`/`venv`).
- **NFR-7**: semantic versioning starting at `1.0.0`.
- **NFR-8**: works fully with zero LLM calls (template trash-talk provider, 0 tokens) —
  the game must be completable and gradeable with no API keys configured.

## Out of scope for this repo
- The police's own strategy logic and barrier-placement decisions (lives entirely in the
  sibling `bb-ai-12-police` repo).
- Any shared runtime process between the two repos — they only ever talk over the network.

## Status
All 7 book-mandated build stages complete: FR-1 through FR-9 implemented and tested (FR-3's
crypto audit and FR-9 itself cover local sealing/auditing, not yet the wire-level exchange
between peers — see `docs/PRD_security_crypto.md`), FR-10 (the four JSON artifacts build and
write correctly; Gmail sending is built and unit-tested but no real email has been sent —
see `docs/PRD_reporting_shell.md`), FR-11 (loading + a pre-game config-agreement check, no
full handshake yet). See `docs/PRD_base_logic.md` / `docs/PRD_mcp_infra.md` /
`docs/PRD_strategy.md` / `docs/PRD_language_scent.md` / `docs/PRD_cloud_tunnel.md` /
`docs/PRD_security_crypto.md` / `docs/PRD_reporting_shell.md` for stage-specific detail and
`docs/TODO.md` for what's next (deferred integration work, not a new stage).
