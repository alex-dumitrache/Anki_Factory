# ⚙️ Phase 0 — TELEMETRY (Feedback Harvest & Triage)

> Front-end to the workflow: turns accumulated prompt telemetry into a ranked, criteria-filtered set of candidate fixes ready for `/design → /redteam → /surgeon`. Run when `prompt_telemetry_database.txt` has accumulated several videos' worth of entries.

## Role (routing)

Claude Code = **Scout + Data Shuttle**. GATHER, ORGANIZE, and CROSS-VERIFY. The holistic **signal-vs-noise judgment is Chat-shaped** — hand the raw telemetry + full prompt files to Chat (Gemini / Claude.ai) for the independent triage. Your edge is frequency-counting and file-state verification, not holistic prompt reading. Do NOT make the final noise call yourself.

## Procedure

1. **Gather.** Read `prompt_telemetry_database.txt` (root = live accumulator; `Archive/<N>/` = per-video snapshots). Note entry count, video span, phase tags (`[date | Video N | Phase]`).
2. **Frequency-count (the objective signal test).** Cluster duplicate complaints; tally recurrence across *distinct videos*. Recurrence across ≥2 videos = reproducible = strong signal. Keep this count as your oracle for checking Chat's triage later.
3. **Hand off to Chat — keep it INDEPENDENT.** Give Chat raw telemetry + full prompt files with one narrow question: *"which clusters are signal worth fixing vs noise?"* Do NOT bundle already-decided grafts into that question — priming destroys the independent read. Grafts are a separate track.
4. **Different reviewers for different work.** Signal/noise → Chat (holistic). Resulting grafts → `/redteam` here (file-access checks). Never cross them.

## Two signal sources — cross-check them

- **Telemetry** = the model's EXPLICIT gut-check (what it chose to flag).
- **Monologue** = the model's IMPLICIT reasoning trace (what it actually struggled with, even silently).
They catch different failures. A finding that shows in the monologue but has **zero telemetry recurrence is low-confidence** — the model didn't even flag it; usually noise. Prefer findings that the monologue shows AND telemetry recurs. *Precedent: the "Mode-1 re-drafts a card 4×" finding had monologue support but zero telemetry → dropped.*

## The valid-fix bar (KEEP vs DROP)

A cluster is **SIGNAL** only if ALL three hold:
- **(a) Reproducible** — recurs across ≥2 videos, OR names a flat contradiction (rule vs rule, or a rule vs its own example).
- **(b) Caused real damage** — wrong output, silent drop, or a forced guess. Not a momentary pause, not a hedge.
- **(c) Worth it** — passes the token metric below.

**DROP / ABSORB** (ABSORB = "real but leave it" is valid): one-off hedges ("a stricter reader could…"), theoretical gameability with no observed failure, rare input-gated edge cases, the model asking for a rule covering something it already handled, or any fix whose cost exceeds the friction removed.

## The real token metric (what "net-negative" actually means)

The bar is **NOT prompt line-count.** It is **net TOTAL tokens per run = prompt tokens + deliberation/spin tokens + emitted-output tokens.**

- **Removing a CONTRADICTION is the biggest win.** The model burns deliberation re-litigating it *every run*. A short clarifying line that KILLS a contradiction is net-NEGATIVE on total tokens even though it grows the prompt slightly — it ends recurring spin. **Clearing confusion justifies a small addition.**
- **Cutting OUTPUT bloat** (ledger rows, attestations the model must emit) is the second-biggest win and the real truncation lever — distinguish it from mere prompt-length trimming.
- **Spaghetti is the trap.** A brittle, multi-step mechanical recipe added for an edge case is net-POSITIVE on prompt tokens, ADDS new execution overhead, AND is fragile — the worst trade. The advisor's instinct (and the model's own Addition Bias) is to "add a clarifying rule" for everything. Resist. For any proposed addition ask: *does it eliminate more recurring spin/output-waste than the reading cost it adds, every run?* A contradiction-killer: yes. An edge-case recipe: almost never.
- **Net target:** fewer contradictions, less output to emit, zero new brittle recipes.

## Fix-type hierarchy (prefer the earliest that works)

1. **DELETE** the contradicting clause / wrong example. (Best — net-negative, kills spin.)
2. **CLARIFY BY SUBTRACTION** — remove the ambiguity at its source.
3. **SEMANTIC / LLM-native heuristic** over a brittle mechanical checklist.
4. **MERGE** into an existing rule (no new section).
5. **ADD a new rule — LAST RESORT.** Allowed only as a SHORT confusion-clearing clause that ends recurring spin; never a multi-step recipe. Justify the token cost in one line.

> **Truncation is not a prompt bug.** It is LLM runtime behavior — classify before fixing. A reproducible contradiction is fixable; raw output-length exhaustion is re-run / fewer cards per pass / the continuation protocol, NOT a graft.

**But when the WORKSPACE itself is the budget problem, compression IS the fix — and it is the cheap one.** Exception-only reporting on workspace sections + verbatim-content carve-outs reclaims ~1500–2000 tokens per run. Cap interpretive PROSE only; never cap the verbatim content downstream consumers depend on (Python regex matches, Phase 2 `Raw_Fact` derivation, structural prefixes) — the cap hard-stops at the prose and the carve-outs are unconditional preserves. **Anti-pattern:** trimming workspace MANDATES to fix truncation — that breaks evaluation. What you want is compressed REPORTING with full EVALUATION intact. Canonical: the 2026-06-01 RUTHLESS WORKSPACE COMPRESSION block in `prompt1_harvester.txt` (HOME Gate / Truth Check / Step 3C / Tutor Bridge made exception-only, `<reason>` capped at 2 sentences with carve-outs for verbatim lecturer quotes and Ref B); verified on Video 116 — workspace fit the budget, M2 provisionals all generated, Pass 2 EARNED ESCAPE.

## Load-bearing verification (Claude Code's job)

- **No-file reviewers hallucinate file state.** Every anchor Chat quotes, every "prompt X *also* has Y" claim, every cross-prompt ripple MUST be verified against the actual files before it becomes a graft. *Precedent: a red-team round invented a non-existent P3 `Source_Type` enum, mis-located the "Scaffolding Demotion Mandate," and inverted a verbatim/paraphrase fact — all caught only by reading the files.*
- **Cross-prompt ripple.** Pipeline is P1→P2→P3→P4→P5 (+P6). A fix to one prompt's OUTPUT can break a downstream prompt's INPUT contract or a `run_phase*.py` parser. Trace every output-format change (Meta, Tags, ledger lines, enums) to its consumers — including the Python — before shipping.
- **Reconcile the plan against the full manifest.** In multi-pass surgery, check the per-prompt pass list against the complete approved graft set before declaring done. *Precedent: G19 was dropped from a pass plan via summary-list drift, caught only at the end-of-campaign tally.*

## Know when to stop reviewing

Parallel red-teams exist to surface the real DISAGREEMENTS (the splits). Once a split is **factual** (about file state — "does prompt X contain Y?"), settle it by READING THE FILE, not another round — more rounds on factual questions breed hallucinations, not truth. Stop when the cheap contradiction-deletes are agreed and the remaining splits are either factual (you resolve) or pure phrasing (bikeshed → Chief Architect decides). Convergence Mandate: agreement after one substantive challenge round is acceptable.

## Behavior changes get a regression test

Any graft that changes *which cards are produced / kept / killed* (not merely wording) is validated on a real run before being trusted — review cannot substitute. Flag it ⚠️ and ship it last.

## Telemetry file lifecycle

- The file is **DATA**. Never store methodology or lessons inside it (they'd be lost on reset and would contaminate the Chat handoff).
- The pre-surgery baseline is already frozen in the latest `Archive/<N>/` snapshot — so resetting the root loses nothing.
- **After fixes ship (committed) and ≥1 run confirms the friction is gone: archive the root DB (snapshot — never hard-delete), then reset it.** Resetting clears already-fixed entries so the NEXT triage cycle isn't re-litigating solved issues. The commit is the before/after boundary; recurrence of a patched cluster in new telemetry = the fix didn't take.

## Hand-off

Route surviving candidates to `/design` (express as grafts) → `/redteam` → `/surgeon`. Triage produces the manifest; the existing phases execute it.
