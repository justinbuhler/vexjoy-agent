# `/d` prepare/finalize contract

Implementation lives in `scripts/jev-route.py` and `jev_transport.py`.
Preparation collects Jev attachment evidence; the session model selects names
and complexity using the complete `print-route-rules.py` output and
request-filtered routing manifest. Jev does not choose the primary route.

## Preparation

The default command accepts `--request-file`. The deterministic
`pre-route.py` guard runs first and supplies any protected skill/pipeline.
The receipt contains `available`, `jev_called`, `source`, `forced`,
`stack`, `project`, `signals`, `signal_scores`, `domain_scores`,
`error`, `latency_ms`, and `usage`. It does not contain a selected
agent, skill, pipeline, or complexity.

`JEV_TRANSPORT=auto|vercel|direct`; Vercel uses `AI_GATEWAY_API_KEY`,
direct uses `TYPESAFE_API_KEY`. Auto prefers direct when configured, then
Vercel; explicit selection never switches. Missing or unusable evidence leaves
an explicit error. Selection can continue without optional evidence, but
unavailable intent validation never authorizes execution.

## Selection and finalization

For Simple+, the session reads all routing rules and manifest candidates,
then records agent, additional agents, skill, pipeline, complexity, confidence,
reasoning, and any required general-purpose fallback reason. Preserve the
protected force route. Trivial proceeds to builder `--router-finalize`
without selecting a worker.

Run `jev-route.py --finalize --result-file <receipt> --decision-file <pick>`.
The script validates names against the live manifest, applies protected
skill/pipeline overrides, supplies skill-owner defaults, and computes `attach`.
The result contains selected names, source metadata, `attach`, signals, domain
scores, and `problems`. Correct invalid names and rerun; unresolved problems
or absent route fields block dependent execution.

Use the returned attachment order, including protected stack entries and agent
domain floors, plus required shared rigor. Union the validated additional
agents with signal-selected research ownership. Each worker needs its own
scoped handoff and builder check.

## Required actual-intent validation

Preparation and finalization permit route preparation only. Both routers pass
the actual task spec to the builder under `required-router-protocol.md`.
The builder validates phase/gate evidence and invokes Jev on the proposed intent
and route. Baseline or cached receipts cannot satisfy this requirement.
Unavailable, error, review, and essential clarification block worker dispatch
and direct finalization. Manifest validity does not prove intent alignment;
aligned intent does not prove completion.

## Verification and boundaries

Use `scripts/tests/test_jev_route_finalize.py` for membership, defaults,
protected overrides, and attachments. Changes to rules, manifest descriptions,
questions, or stack policy require the routing cases in `../EVAL.md`.
Request and project evidence leave the machine through the configured Jev
transport; existing private-domain filtering and local-only boundaries remain
binding. Credentials never belong in arguments, logs, or persisted receipts.

## Implementation map

- `scripts/jev-route.py`: preparation and finalization receipts
- `scripts/print-route-rules.py`: complete session selection rules
- `scripts/pre-route.py`, `routing-manifest.py`: protected guards and membership
- `scripts/jev_transport.py`, `jev_vercel.py`, `jev_gateway/jev_vercel_gateway.mjs`: transport
- `scripts/build-dispatch.py`: required actual-intent gate and dispatch
- `hooks/jev-route-injector-userprompt.py`: optional preparation precompute
