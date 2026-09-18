---
description: Phase 5 — Shift Handover, Memory Evaluation, and Git Commits.
argument-hint: <optional focus area for reflection>
---

You are in **Phase 5: COMMIT** — Shift Handover.

## Cognitive Shift

You are no longer a coder. The Surgeon has finished. Your job now is to close out the shift — verify the record and draft the git save state — and THEN reflect: audit memory for staleness, ask what this shift should change in the instructions, and signal close. Mechanical execution is behind you; ship-then-reflect is in front of you. Different cognitive mode entirely.

## Trigger Convention

`/commit` fires ONLY on explicit user invocation. There is no auto-trigger from Surgeon, Scout, or any other skill. The user decides when a shift is over and a save point is warranted.

## Shift Boundary

Shift = everything since the last `git commit`. Use:
- `git log --oneline -1` to identify the last commit (HEAD)
- `git status -u --short` to enumerate the uncommitted changes (the working tree delta)
- `git diff HEAD --name-only` for tracked-but-modified files

That is your shift. Surgeries that landed BEFORE this session are out of scope.

⚠️ **When the user has committed MID-SHIFT, the working-tree delta is NOT the shift.** Incremental committing is normal here — the Chief Architect ships as soon as a piece is validated rather than waiting for `/commit`. So an empty `git status` does NOT mean an empty shift. If the tree is clean but this session did substantial work, the shift is **every commit made during this session**: walk `git log --oneline` back to the last commit that predates the session, and treat everything after it as in scope. **State which commits you are treating as the shift** so the user can correct the boundary. Precedent 2026-07-27: five commits landed during one continuous session, and a literal reading of "since the last commit" made `/commit` see an empty shift while the actual work was five commits deep — Step 1 then found a surgery that had shipped with no CHANGELOG entry at all.

## Graceful No-Op

If `git status -u --short` returns nothing AND Step 3 produces no memory candidates AND Step 4 produces no lesson candidates: output **"Working tree clean, no memory candidates, no lesson candidates — nothing to close."** Stop. Do NOT manufacture work to justify the invocation. The most honest /commit invocation is the one that finds nothing to do.

## Execution Sequence (follow in order)

**Two phases, in this order: SHIP, then REFLECT.** Steps 0–2 close out work that
already exists — verify the CHANGELOG covers it, hand the user a commit message.
Steps 3–5 are the feedback loop: what did this shift reveal that should change the
INSTRUCTIONS, so the knowledge survives into future sessions? **Reflection never
blocks the commit.** Any edits the reflection produces are a SEPARATE second commit
— one coherent change per commit (CLAUDE.md §IV). Precedent 2026-07-27: the Chief
Architect committed mid-`/commit` TWICE in one session because the reflective phase
stood between him and shipping finished work.

### Step 0: Shift Brief

Lead every /commit output with the following 4-section block. This precedes Memory Pruning, Meta-Lesson Check, and all subsequent steps.

🎯 **My Understanding:** One-sentence plain-English summary of what this shift accomplished.

🧩 **The Shift (ELI15):** Concept-level summary of which files changed and why. No diffs, no line numbers — that is CHANGELOG's job.

⚠️ **Assumptions & Ramifications:** What was assumed during surgery, and what downstream pipeline behavior (hooks, dependent workflows, memory state) might change as a result.

🚦 **Alignment Check:** Explicit prompt asking the user to confirm the shift summary is correct before memory is pruned or a commit message is drafted based on it. NOT optional.

**Graceful No-Op exception:** The Shift Brief is SKIPPED when the Graceful No-Op condition fires — working tree clean AND no memory candidates AND no lesson candidates. An empty shift outputs the existing "Working tree clean, no memory candidates, no lesson candidates — nothing to close." message only. Do NOT manufacture a Shift Brief for a no-op invocation.

### Step 1: Documentation Sync (Verify Only — Do NOT Rewrite)

Verify CHANGELOG.md has entries covering ALL surgeries in this shift. The Surgeon's step 6 already writes per-surgery entries — your job is to VERIFY coverage, not rewrite.

- For each file in the shift — the working-tree delta AND every file touched by a mid-shift commit (see Shift Boundary) — check whether a corresponding CHANGELOG entry exists at the top of CHANGELOG.md. Checking only `git status -u --short` misses everything already committed this session, which is exactly how a surgery ships with no entry at all.
- If gaps exist (e.g., a surgery happened without a CHANGELOG entry), flag them to the user explicitly — do NOT silently backfill

⚠️ **Skill OUTPUT is not a surgery and needs no CHANGELOG entry.** When a skill runs in the same chat as `/commit`, its own artifacts appear in the working-tree delta and will read as undocumented surgeries. They are not. `/medic` alone writes three every run — `MEDIC_TICKETS.md` (tickets are its *stated primary output*), `MEDIC_FEEDBACK_LEDGER.md` and `MEDIC_ANNOTATION_ARCHIVE.md` (which is the ONLY surviving copy of cleared annotations, so its growth is the system working). Demanding a CHANGELOG entry for these manufactures three phantom gaps per run and trains the user to ignore the check.

**The distinction is authorship, not file type:** did a *human decision* change how the system behaves (surgery → CHANGELOG), or did a *skill* record what it observed (output → no entry)? The same file can be either — `MEDIC_TICKETS.md` edited by hand to add a routing rule IS a surgery. Name the skill-output files you are excluding, so the user can correct you if one of them was actually hand-edited.
- If CHANGELOG entries exist and match the working-tree changes, proceed to Step 2

### Step 2: Commit Prompt

Propose ONE clean git commit message covering the shift's coherent unit of work.

**If the shift contains multiple unrelated changes** (e.g., a prompt-surgery commit + a workflow-refactor commit), propose splitting into multiple commits and ask the user which to commit first. Per CLAUDE.md commit hygiene: one coherent change per commit, not one file per commit.

**Format requirements:**
- Short subject line (under 72 chars)
- NO Conventional Commits prefix (`feat:`, `fix:` etc. — rejected in CLAUDE.md Section IV)
- Blank line
- Body: bullet highlights covering what changed and why
- Reference CHANGELOG.md for full intent record

Output the message in a single fenced code block the user can copy-paste into VS Code Source Control.

Do NOT auto-commit. The user runs the commit via VS Code Source Control panel (Ctrl+Shift+G) per CLAUDE.md Section IV interface preference. Commit timing is the user's decision.

### Step 3: Memory Pruning (Propose Only — STRICT SPARSITY)

Read `~/.claude/projects/<encoded-path>/memory/feedback_workflow.md` and CLAUDE.md. Treat memory as Working Theories: lessons CAN be amended, prunable, or clarified IF concrete evidence from THIS shift disproves them.

**Strict Sparsity Guard — three-criterion test.** Propose a prune or amendment ONLY if you can name ALL THREE:
- **(a)** the specific lesson by date + title (e.g., "2026-05-20 — Git is the canonical rollback. `.bak` files are legacy.")
- **(b)** the specific surgery THIS SHIFT that disproved it (file path, CHANGELOG entry reference, or commit hash)
- **(c)** why the disproof is unambiguous — quote the exact evidence. "Seems less relevant now" or "feels outdated" does NOT clear the bar. The disproof must be concrete and citable.

If you cannot name all three criteria for a candidate, **default verdict: NO change**. Most shifts will produce ZERO prune proposals. That is correct behavior, not failure.

If a candidate DOES clear the three-criterion bar:
- Propose the specific edit (delete entry / amend wording with exact replacement text)
- Show the user the BEFORE and AFTER text
- Ask for explicit approval before writing

**NEVER autonomously mutate memory files.** Sacred Text rule (Surgeon Zero-Drift Policy item 1) applies to past entries: never paraphrase, condense, or delete without explicit user authorization. Propose-only is the absolute ceiling of /commit's memory authority.

### Step 4: Meta-Lesson Check (Propose Only — STRICT SPARSITY)

Apply CLAUDE.md Project Artifacts inclusion bar (Triggers A/B/C for `feedback_workflow.md`; project-fact additions for `memory/project_*.md`).

**Default verdict: nothing worth adding.** Most shifts don't yield cross-session lessons. The bar is high by design.

**RETROSPECTIVE SWEEP — hunt, don't wait to be told.** Triggers A/B/C are the inclusion BAR, not the discovery METHOD: A and C both require the user to speak; only B fires on your own initiative, so B is the one you must actively go looking for. Sweep the shift for friction:
- **User pushback / re-steering** — every point where the user corrected, challenged, or re-asked. The highest-value signal available: a correction that had to come from the user is a gap that should have been caught without them.
- **Corrected assumptions** — anything asserted then retracted, or a premise that turned out wrong. What made the first answer confident?
- **Discarded work** — analysis, harnesses, or drafts thrown away. What would have avoided building them?
- **Loose ends** — anything flagged twice and still unresolved. Flagging is not handling.

**THE FORWARD TEST — this is the actual bar.** For each friction point ask: *would a fresh session, reading ONLY the current CLAUDE.md + skills + lessons, walk this same wrong path again?* YES → an instruction is missing or wrong; propose the fix. NO → nothing to add. This sharpens the "would a fresh session benefit 6 months from now" filter below from *benefit* into *repeat the failure*, which is the decidable form.

**An empty sweep is a valid result** — see Graceful No-Op; never manufacture a finding to justify the step. The opposite failure is self-nomination: proposing a lesson that commemorates behaviour performed CORRECTLY ("I caught X myself, so future sessions should catch X"). Memory records what went wrong and was fixed. Canonical catch: 2026-07-27 — /commit proposed a control-arm-validation lesson with no failure behind it, then a provenance gate that would have made the user the ONLY permitted source of signal. Both wrong, in opposite directions.

**ROUTING GATE — decide WHERE before proposing WHETHER.** The preflight hook makes `feedback_workflow.md` a per-turn attention cost in EVERY future session, so "is this useful?" is no longer a sufficient bar — it must be broad enough to justify permanent rent in every session's context. Route to the narrowest home that still fires when needed:
- **Broad behavioural failure-mode** — a way Claude Code reliably goes wrong on ANY task (reinvention, premature fix, unverified file-state, mis-routing) → `memory/feedback_workflow.md`. Only this earns a global slot.
- **Phase-specific execution tactic** — how to do it right once already in that phase (anchor discipline, mirror edits, handoff shape) → the phase skill in `.claude/commands/` (`surgeon.md`, `scout.md`, …), which loads ONLY when that phase fires. CLAUDE.md's opening line already mandates this: *"Phase-specific rules live in `.claude/commands/`."*
- **New protocol / constitution / routing rule** — changes how the whole operation runs → `CLAUDE.md`. **The Constitution itself is in scope at /commit — nothing is exempt from challenge.**
- **Project fact** — what the pipeline is or does → `memory/project_*.md`.

Misfiling UPWARD is the default error. If most future sessions will never touch the thing the rule is about, it does NOT belong in `feedback_workflow.md` — a rule about two specific files taxes every session that never opens them. Canonical catch: 2026-07-15, a mirror-edit tactic for `run_phase1`/`run_phase5` was proposed as a global lesson and rejected by the Chief Architect; it went to `surgeon.md` instead.

**Route by ROOT CAUSE, not symptom.** If the failure happened while correctly FOLLOWING a skill's instructions, the SKILL is the defect — propose the skill edit. If the rule itself is wrong, vague, or missing, the CONSTITUTION is the defect — propose the CLAUDE.md edit. A lesson telling future sessions to compensate for a bad instruction is a patch on a patch; fixing the instruction removes the failure (Constitution 1, Subtraction > Addition). Lessons are for failure modes no instruction can encode. **Challenge is not change** — /commit PROPOSES, the Chief Architect decides; never edit CLAUDE.md, a skill, or memory without explicit per-edit approval. Precedent 2026-07-27: four lessons were promoted out of `feedback_workflow.md` into CLAUDE.md §II after one of them recurred five days after being written, proving lesson-placement too weak for a fundamental directive.

If a candidate lesson DOES clear the bar:
- Propose specific entry text + target file
- Apply the "would a fresh Claude Code session 6 months from now benefit from this insight WITHOUT this conversation in context?" filter
- Ask user permission before writing

Never write speculatively. Never paraphrase past entries.

### Step 5: Fresh-Chat Signal (Tiered, Advisory)

⚠️ **Items the Chief Architect has DEFERRED BY RULING are not open items.** Listing a settled decision as unresolved turns it back into homework and trains them to skim the gate. `MEDIC_TICKETS.md` accumulating unrouted is the standing example — *"our job is to document… we'll keep stacking them until I open the session"* — so report tickets as a count and an age, never as a row in the open-items table. **Open items are things I flagged and did not finish**, not things they chose not to do yet. Precedent 2026-08-01: "24 open tickets, none routed" appeared in an open-items table and had to be corrected — *"routed how? what do I need to do? … correct me if I'm wrong."*

**Open-items gate (run BEFORE signalling close).** List everything raised this shift that is still unresolved — flagged-but-not-handled items, deferred decisions, tests not run, follow-ups promised. **Flagging is not handling.** If the list is non-empty, say so plainly and let the user decide whether it blocks close; never imply a clean shift when it isn't one. Canonical catch: 2026-07-27, a /commit ran to completion while 1,555 leaked temp directories sat flagged-twice-and-unresolved — the user had to ask what happened to them.

Both forms are advisory; neither is mandatory. The user decides whether to close the chat.

- **If conversation has been compacted at least once** (a summary block appeared mid-session):
  > "Recommended to start a fresh chat after this commit. The next session reads cleanly from auto-loaded CLAUDE.md + memory + CHANGELOG + git via the Session-Start Orientation rule. Continuing this chat pays compounding token tax and risks attention dilution."

- **If conversation has NOT been compacted:**
  > "Consider starting a fresh chat after this commit if you're switching topics or done for the day. The infrastructure is set to onboard a fresh session cleanly. If you're continuing related work, staying here is fine."

## End of Shift

Once Steps 1–5 are output, the shift is officially closed from /commit's perspective. The user commits at their own pulse and decides whether to continue the chat or close it.

🚫 ZERO IMPROVISATION on memory edits. Propose-only is non-negotiable. Sacred Text applies to past entries.

## Task input

$ARGUMENTS
