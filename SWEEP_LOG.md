# SWEEP_LOG.md — a human-readable record of what past sweeps found

⚠️ **`/sweep` does NOT read this file.** It reads the session transcript directly
(`~/.claude/skills/sweep/SKILL.md` §0). This log exists so a person can skim what
past sweeps fixed without re-reading a chat. Nothing depends on it.

A sweep covers an **arc** — the mini-project under discussion — and **re-sweeps the
same arc on every invocation until a pass comes back CLEAN.** It is a broom, not a
one-shot audit. The earlier framing at the top of this file — *"a segment: everything
between the previous sweep and now"* — was superseded 2026-08-18 and is wrong: a
turn-count or last-invocation boundary says nothing about whether the work is clean.

**Every entry states DIRTY or CLEAN**, because that is the signal that decides what
the next sweep covers. Scope is one conversation — never other sessions or projects.

**Newest at top. Append only** — past entries are marked, not rewritten.

---

## 2026-08-19 ~00:30 · session `b4ebdbda` · the shorts arc, pass 3 · **DIRTY** (3 misses)

**Covered:** the same arc again — 32 user turns from *"stuck on printers"* (transcript
line 3284) to now, which now includes the sweep-skill rewrite itself. Re-swept because
pass 2 came back DIRTY.

**Re-verified from pass 2 — all 4 fixes still stand:** `/shorts` invocation arguments ·
the new-card fallback · `Logic` in §5b · the 📽️ row in `medic.md`. Ten separate arc
decisions were re-probed against `shorts.md` (share link, daily limit, 12/day ceiling,
link HTML, no-tags, overview fences, the "don't say 1 minute" rule, batch analysis,
the "due now" ban, the Agains filter) — **all ten present.**

**3 misses, all fixed:**
- `SWEEP_LOG.md` — **this file still described the SEGMENT model the broom rewrite
  replaced**, and claimed *"Read by `/sweep` §0 before every sweep"* when the skill
  reads the transcript and mentions this file once, as an optional write. Half-fixed
  last pass: the ⚠️ warning was corrected while the title and definition above it
  still stated the opposite.
- `SWEEP_LOG.md` — **no entry recorded DIRTY or CLEAN**, which is the one signal the
  new auto-detection asks for. Field added to the format and applied retroactively.
- `NOTEBOOK_REGISTRY.md` — **an unverified share setting was stated as fact.**
  `75cf466b…` was set to "Anyone with a link" but never opened logged-out; it sat in
  the same column as the proven notebook. The Chief Architect's founding requirement
  for this feature was that people without Google accounts can watch.

**Open at close:** `75cf466b…` still unverified logged-out (now flagged in the
registry, no longer only in this log) · card `1786875801512` eligible for the existing
Relative Voltage video, not linked · `account1`'s printer notebook UUID not
captured · `/shorts` never run as a skill · the untested whole-card prompt variant ·
`CHANGELOG.md` 1,534 lines · 27 loose root files · Codex's four approved images
unrendered.

---

## 2026-08-18 ~14:40 · session `b4ebdbda` · the shorts arc, pass 2 · **DIRTY** (4 misses)

*(Status label added retroactively 2026-08-19 — this entry predates the DIRTY/CLEAN field.)*

**Covered:** 28 user turns — from *"I'm currently stuck on printers"* (transcript
line 3284) to now — **read from disk, not pasted.** Confirms the Chief Architect
never needs to paste a conversation back.

**4 major misses, all fixed:**
- `shorts.md` §2 — **no invocation arguments at all.** Turn 1 asked for scope
  (*"all cards created… yesterday, for example, or whatever"*) and the skill had
  one hardcoded filter. Added an argument table copied from `/medic`'s proven shape.
- `shorts.md` §2 — **the `if no reviews, take new cards` fallback was missing.**
  The skill would have reported "nothing to do."
- `shorts.md` §5b — **`Logic` was never used.** Turn 1 asked for *"the logic, the
  not, the delta, everything."* Added as third fallback; the full-paste variant is
  flagged as never tested rather than silently dropped.
- `medic.md` — **zero mentions of `/shorts`.** `/medic` triages failing cards and
  assigns tools, and the newest tool was invisible to it. Added a 📽️ signpost row
  mirroring the 🖼️ one.

**Corrected in this file and the skill:** the cross-session ledger premise. Sweep
is one chat; the transcript is the boundary source; this log is optional.

---

## 2026-08-18 ~14:10 · session `b4ebdbda` · the sweep-skill arc · **DIRTY** (3 misses)

*(Status label added retroactively 2026-08-19.)*

**Covered:** 1 user turn (the segmented-sweep request), plus my own work in it.
Transcript lag meant the near end came from context, not the `.jsonl`.

**Fixed:**
- `shorts.md` §1z — **the never-run-in-parallel rule was missing entirely.** Three
  agents now write this Anki collection (`/medic`, the Codex image agent,
  `/shorts`) and the newest one did not carry the rule. Recovered from the image
  agent's brief, where it had been living alone.
- `shorts.md` §6a — PLUS-account ordering. The observation that `account2` may
  have a ceiling above 6 was in `NOTEBOOK_REGISTRY.md` but not where the limit
  logic lives.
- `~/.claude/skills/sweep/SKILL.md` — added §0 SEGMENTS (ledger-first boundary,
  three-step lookup, cross-session warning), §7 WRITE AUTHORITY + this ledger, an
  explicit universality statement, and the transcript-lag caveat.

**Open at close:** `CHANGELOG.md` oversized (1,492 lines) · 27 loose files at
project root · `check.sh` still cannot detect a rule deleted from *inside* a file
· `/shorts` never run as a skill · card `1786875801512` unlinked · new notebook
never tested logged-out · Codex's four approved images unrendered.

---

## 2026-08-18 ~12:20 · session `b4ebdbda` · session start → 12:20 · **DIRTY** (4 misses)

*(Status label added retroactively 2026-08-19.)*

*(Logged retroactively — this sweep ran before the ledger existed.)*

**Covered:** all 140 user turns, read from the transcript.

**Fixed:**
- `check.sh` — its skill loop hardcoded **eight** files and omitted `shorts`, so
  "workflow skill files tracked in git: ok" was checking 8 of 9. Added, plus a
  self-audit loop that now flags any `commands/*.md` missing from the list.
- Three stale "eight skill files" counts: `MEDIC_TICKETS.md:177`,
  `~/.claude/PROJECTS.md:87`, `image_prompts/OPERATING_BRIEF.md:54` (also 26→28
  tickets).
- `shorts.md` §9a — recorded that `NOTEBOOK_PRODUCER_BRIEF.txt` is deliberately
  untracked, with `Archive/139/` as the evidence, so it does not get "fixed."

**Found and routed earlier the same session:** `/sweep` answered as
non-existent when it had lived at `~/.claude/skills/sweep/` for ten days →
global `CLAUDE.md` rule 15 · TLDRs back-referencing instead of carrying → global
rule 14 standalone section · deletion-is-reinvention → global rule 4 · a printed
check that does not abort → `surgeon.md` Zero-Drift item 8.
