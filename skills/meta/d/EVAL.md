# EVAL: /d — session-pick router with Jev validation

Regression cases. Load only when evaluating or redesigning this skill. Full
corpus run: `python3 scripts/jev-eval.py --out-dir <new-dir>` against
`scripts/routing-ab-corpus.json` (269 cases); `--out-dir` is required and
must be a fresh directory — never overwrite a completed run. Each case runs
`jev-route.py` prepare, a `claude -p` session pick (`scripts/d_route_model.py`),
and `jev-route.py --finalize`. Pass `--workload-dir NAME=PATH` for corpus cases
that record a workload, so both arms of a comparison see the same repo facts.
Results land under `scripts/routing-ab-results/` per
`docs/router-ab-runbook.md`. The manual set below is the fast sanity check; it
does not replace the full corpus run.

Compare arms with two runs each. A rerun with unchanged code changes the pick
on about 11% of rows, so count a row as changed only when both runs of the arm
agree.

## Idiom-guard sanity set (manual: send each request to `/d`, or run `jev-eval.py --limit`)

| # | Request | Expected | Mechanism under test |
|---|---|---|---|
| 1 | "push my changes" | pr-workflow, `source: "pre-route-force"`; session picks the agent | pre-route guard preserves the protected skill |
| 2 | "Push back on this architecture before we commit to it" | NOT pr-workflow | idiom guard (pushback/commit) |
| 3 | "Commit these changes and push to origin" | pr-workflow, force-route | genuine git intent |
| 4 | "Fish for compliments from the design team before shipping" | NOT a forced deploy route | idiom guard (fish=search) |
| 5 | "Configure my fish shell prompt to show git branch" | deploy | genuine Fish shell intent |
| 6 | "Make it public that we're hosting a charity stream next week" | NOT a forced deploy route | idiom guard (make public != deploy) |
| 7 | "Compare static site generators for a docs site" | NOT a forced deploy route | work-on-a-site guard |
| 8 | "Deploy my landing page to Vercel" | deploy | genuine deploy intent + companion word |
| 9 | "help me plan a birthday party" | sensible agent/skill selected by the session and validated by `--finalize` | complete rules and manifest selection |
| 10 | (simulate) both Jev keys unset | unavailable attachment evidence; route selection continues, actual-intent gate remains pending | no false aligned receipt |
| 11 | Multi-agent request | selected agents remain manifest-valid after `--finalize` | fan-out membership validation |
| 12 | "thanks" / "hi" / "say hello" / "what is 2+2" | session selects Trivial; builder `--router-finalize` validates actual intent before direct handling | no trivial intent-gate bypass |

Cases 6–8 distinguish public announcements, site research, and deployment.
Recheck them against the current guard; a historical failing deployment guard
is not evidence that the current case passes. Record actual current results.

## Routing call boundaries and transport checks
- Prepare collects attachment evidence and the protected guard; the session
  selects names and complexity. Finalize validates membership and computes the
  attachment stack without selecting a route through Jev. Every executable
  route makes a separate fresh actual-intent check through the builder.
- Test normal, force, trivial, fallback, and injected routes: none may answer
  or dispatch using baseline/cached/self-reported alignment.
- Missing or malformed answers, unavailable transport, review, and essential
  clarification fail closed. Corrected current intent must be rechecked.
- Reject missing phase evidence, empty task fields, absent Simple+ plans, and
  inapplicable claims that contradict creation/code/workflow conditions.
- Exercise `--router-finalize` and native session pending gates, including
  attempts to omit `router` or use manual Agent/Task dispatch.
- A 429, 503, 529, or timeout from Vercel retries at most twice and persists a
  safe receipt; other gateway errors trigger classification fallback only. Intent validation
  remains blocked until a fresh aligned response.
- `auto` prefers direct Jev, explicit transport selection never switches, and
  `direct` sends the same state and questions to the Jev API.

## Known failure modes
- The pick names a skill or agent not in the live manifest (renamed/deleted
  component) -> `--finalize` drops it and lists it in `problems`. Covered by
  `scripts/tests/test_jev_route_finalize.py`.
- Jev call exceeds timeout -> evidence stays empty and routing continues.
  Covered by the Vercel bridge retry receipt + `--timeout` flag.
- Missing Gateway bridge/HTTP-client dependency -> must not crash. Covered:
  `jev-route.py` uses the isolated Vercel bridge; the bridge package is
  installed by `install.sh`; missing attachment evidence does not bypass the
  builder's required actual-intent check.
- Confidently-wrong classification on `paraphrase-security`/
  `false-positive-guard` — actual-intent checking adds a runtime judgment but is not ground truth.
  Keep per-bucket `SAFETY_BUCKETS` evaluation; do not infer correctness from
  one aligned request.

## Full-corpus evidence

Do not cite a run unless its verdict exists in the repository and was produced
from the current corpus, manifest, and implementation. The previously cited
2026-09-16 v1/v2 verdict paths are absent, so their historical percentages are
not part of this maintenance contract. Generate a fresh output directory with
the command above when comparative routing evidence is needed. The corpus
remains a regression tool for route quality.
