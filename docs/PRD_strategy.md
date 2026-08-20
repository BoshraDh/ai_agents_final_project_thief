# PRD — Stage 3: Blind Strategy

## Goal
A real, pure-algorithm move-decision brain — Manhattan-distance evasion — replaces the
hardcoded STAY from stage 2 for this peer's own outbound moves. "Blind" per the book's own
staging: no scent trail, no free-text hints, no deception yet (stage 4); no crypto-verified
truthfulness yet (stage 6).

## Delivered
| Module | Responsibility | Book reference |
|---|---|---|
| `domain/belief.py` | `BeliefState` — exact position tracker, replayed from public start positions + honestly-relayed moves | ch.4 (belief concept, simplified pre-deception) |
| `strategy/base.py` | `BrainBase` — abstract `decide_move(board, barriers, own_pos, opp_pos) -> Direction` contract | ch.6.5 (LLM-never-decides rule) |
| `strategy/heuristic_brain.py` | `HeuristicBrain` + `manhattan()` — shared Manhattan-distance search over `domain.rules.legal_moves`; `_sign` sets pursue (+1) vs evade (-1) | ch.6 |
| `strategy/thief_brain.py` | `ThiefBrain(HeuristicBrain)`, `_sign = -1` — flees the tracked police | ch.6 |
| `strategy/resolve_brain.py` | `resolve_brain(private_config)` — factory reading `[strategy].thief_class` from `config/game.toml`, defaulting to `ThiefBrain` | Appendix ב (config split) |
| `runtime/peer_runtime.py` | `_decide_move` now calls the resolved brain via `BeliefState`; `run_turn_loop` updates belief on both the move sent and the move received | ch.7 |
| `cli.py` | `peer` subcommand now builds `Board`/`BarrierSet`/`BeliefState`/brain from config instead of hardcoding STAY | — |

## Design decision: the stage-2/3 boundary on the wire protocol
`mcp/server.py`'s `receive_move` tool is **unchanged from stage 2** — it still always replies
STAY. Stage 3's real brain only drives this peer's own *outbound* move selection in
`PeerRuntime.run_turn_loop`. Making the inbound stub reply with a real move too requires a
synchronized turn-taking / negotiation protocol (who moves first, how a shared turn counter is
agreed) that the architecture already slates for `peer/turn_handler.py` + `peer/handshake.py` +
`domain/negotiation.py` — deliberately not built ad hoc here. Building it now, without
re-consulting the book's exact negotiation-protocol text, risks inventing a shape that
contradicts the binding spec. It is tracked as an explicit open item (`docs/TODO.md`), not
silently skipped.

## Acceptance criteria (all met)
- [x] `BeliefState.from_config` seeds both agents' positions from `config/game.json`'s public
      `cop_start`/`thief_start`; `apply_own_move`/`apply_opponent_move` update independently.
- [x] `ThiefBrain` always returns a *legal* move (sourced from `domain.rules.legal_moves`, so
      barrier/bounds checks are reused, not reimplemented) that maximizes Manhattan distance
      to the tracked police; returns STAY only when already at the farthest reachable cell.
- [x] `resolve_brain` defaults to `ThiefBrain` when `[strategy]` is absent/empty, and loads a
      `module:ClassName` override when configured — `config/game.toml`'s `[strategy]` section
      is now uncommented and points at the real class.
- [x] **Manually verified with real strategy on both sides**: ran `bb-ai-12-thief peer --turns 4`
      and `bb-ai-12-police peer --turns 4` concurrently. This repo's outbound moves were real
      evasion decisions (`S, S, S, E` — moving away from the tracked, stub-frozen police
      position at (0,0)), not hardcoded STAY, confirming the brain is genuinely driving
      outbound play. The same benign stage-2 teardown race (documented in
      `docs/PRD_mcp_infra.md`) recurred once this side's shorter-running script exited first —
      expected, not a new defect.
- [x] `uv run pytest -q --cov=src` passes at 94% coverage (46 tests); `uv run ruff check .` is
      clean.

## Explicitly deferred to later stages
- Inbound `receive_move` replying with a real move (needs the synchronized turn-taking
  protocol above).
- Reasoning about likely barrier locations when planning an escape route — the brain
  currently only ever chooses a movement direction against the empty `BarrierSet` this peer
  starts with; the wire protocol doesn't yet carry the police's barrier placements to this
  side. Arrives together with barrier-placement decisions in a later stage once the message
  schema is extended.
- Pheromones/scent, free-text hints, deception, template/LLM trash-talk — stage 4.
- Cloud tunneling — stage 5.
- Commit-reveal sealing, nonces, Step-0 declaration, real negotiation handshake — stage 6.
- Gmail reporting, GUI, replay viewer — stage 7.
