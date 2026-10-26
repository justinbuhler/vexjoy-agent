# SPEC: /d - session-pick router with Jev validation

Maintenance contract; ordinary routing follows `SKILL.md`.

## Purpose and scope

Preserve the complete user request and constraints while selecting a live
agent, skill, pipeline, and attachment stack. The session selects the route
using `/do` rules; Jev supplies attachment evidence and separately validates
the actual proposed intent before any dispatch or direct handling.

## Invariants

1. `scripts/pre-route.py` runs before Jev preparation and owns protected
   git/security skill and pipeline choices.
2. `jev-route.py` preparation returns evidence, project facts, and any forced
   route. It does not select an agent, skill, pipeline, or complexity.
3. The session reads the complete rules and request-filtered manifest, selects
   names and complexity, and provides a reason for general-purpose fallback.
4. `--finalize` validates membership, applies protected routes and skill-owner
   defaults, and computes attachments. Unresolved `problems` block execution.
5. Missing optional attachment evidence permits route preparation, never an
   invented successful intent check.
6. `build-dispatch.py` validates the complete handoff, plan, ordered phases,
   and conditional gates, then runs fresh actual-intent validation. Normal,
   protected, trivial, unavailable-evidence, injected, and resumed paths all
   require this check. Trivial uses `--router-finalize`.
7. Preserve unchanged `request_verbatim`, actual `intent`, and required
   verbatim `prior_context`. Missing, stale, baseline-only, unavailable, error,
   review, and essential-clarification receipts do not authorize execution.
8. `JEV_TRANSPORT=auto|vercel|direct` selects transport. Auto prefers direct
   when configured, then Vercel; explicit selection never switches. Credentials
   are never arguments, logs, or persisted artifacts.
9. Each fan-out worker has separate ownership, scoped task spec, builder call,
   and actual-intent validation. The validated builder prompt is consumed once.
10. Supported native hooks guard pending dispatch/completion. Other harnesses
    follow the builder contract explicitly; universal interception is not claimed.

## Dependencies and verification

Runtime: `jev-route.py`, `print-route-rules.py`, `pre-route.py`,
`routing-manifest.py`, `build-dispatch.py`, required-router gate, and shared
Jev transport. Dispatch telemetry remains `[do-route]`.

Use `EVAL.md` cases and focused prepare/finalize, transport, router-gate,
intent, and dispatch tests. Recheck protected overrides, invalid names,
unavailable evidence, prior-context preservation, and every intent-gate path.
Fresh final acceptance evidence remains required after the worker executes.

Jev is a judgment signal, not ground truth. Manifest-valid names can still be
wrong for the request, aligned intent can still yield incomplete implementation,
and historical percentages are not release evidence. Cite only reproducible
results present for the current corpus, manifest, and implementation.
