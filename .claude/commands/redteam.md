---
description: Phase 3 — Adversarial audit. Attack the manifest before any file is touched.
argument-hint: <manifest or grafts to audit>
---

You are in **Phase 3: RED TEAM** (cross-red-team mode).

## Task

Attack the proposed plan before a single file is touched. As Claude Code, I attack against actual file content. Gemini attacks against architectural logic. Each catches what the other misses.

## Routing Check (run first)

Classify the work before executing:
- **File-access-required red-team** (compiler simulation against actual source, anchor verification, line-number drift, residency check, instruction-contradiction check that requires reading the current file state) → execute here. Claude Code's file access is the comparative advantage.
- **Architecture-only red-team** (vague-rule scrutiny, design philosophy challenge, "is this approach sound?" interrogation, alternative-architecture brainstorming with no file dependency) → route to Chat. Produce a paste-ready forensic dump in the standardized **Handoff format** (see below) and stop.
- **Prompt-design red-team** specifically → even if some file-access checks apply, the holistic LLM-behavior reasoning is Chat-shaped. Run only the file-access checks here (anchor verification, residency grep); route the rest to Chat with the full prompt file pasted.
- **Unclear** → ask the user: "Want me to red-team this here, or dump it for Chat?" Wait for the call.

**Handoff format (when routing to Chat).** When this Routing Check sends work to Chat, the LAST thing emitted to the terminal MUST be a single select-all-copy block in this exact shape:

> **=== HANDOFF TO CHAT ===**
>
> **File under review:** `<exact path>`
> **Problem statement:** [one line — what design is being challenged?]
> **Scout findings (key anchors):** [3-5 lines, with line numbers + brief excerpts]
> **Suspected weakness:** [the specific failure mode you want Chat to attack]
> **Question for Chat:** [what should Chat verdict / propose?]
>
> **=== END HANDOFF — open the file in VS Code, Ctrl+A, paste alongside this block ===**

Do NOT embed the full file content inline. Prompt files are 300-800 lines; embedding inflates terminal output and risks paraphrase drift. The user opens the named file in VS Code and copies it directly.

**Return contract — append this INSIDE the handoff block.** Identical to `design.md`'s, deliberately: the two handoff blocks mirror each other and a red-team handback is the leg that most often arrives as loose prose. Keep them in step when either changes.

> **=== RETURN IN THIS SHAPE ===**
> 1. What you investigated, and why
> 2. VERIFIED findings — each with the quoted text or `file:line` it rests on
> 3. CORRECTIONS to canon — name them, including to your own earlier reply
> 4. **LINES KILLED** — what you proposed and then abandoned, plus the evidence that killed it. *"Nothing was killed"* is a valid entry
> 5. What remains UNVERIFIED, and why
> 6. Exact changes required, file by file — **quote the anchor text; never cite a line number**
> 7. Hard stops / framings to avoid, discovered along the way
> 8. Open questions you did NOT rule
>
> One fenced block, versioned (`v1`, `v2`, …). To revise: **rewrite in place** while nothing has been applied; **once a block has been applied, issue a NEW block headed `SUPERSEDES v<N>`.** Never append a correction and rely on read order.
> **=== END RETURN CONTRACT ===**

**Section 4 is the load-bearing one for THIS phase.** Red team is run 2–5 chats wide precisely because independent models kill different things (CLAUDE.md Operating Loop step 4). Without LINES KILLED, each chat's discarded attacks are invisible, so the same dead ends resurface next round and I re-adjudicate them at step 5. It is also the natural inbound counterpart to the **Omission Audit**'s clause (b) — an explicit "intentionally not addressed — reason" entry — and the two should be kept in step. ⚠️ **A handback is ASSERTED until verified here, however certain it sounds.**

## Data Shuttle Requirement

The Conversational Agent (Gemini) cannot see my terminal output. The user MUST paste my verification output (grep results, file excerpts, variable checks) into Gemini's prompt for cross-red-team. Without this shuttle, Gemini's red team operates on assumed file state — silent breakage risk.

## Mandatory Checks

### The Crucible (Strategic Interrogation)
Is any rule vague? Does it force System Cosplay? Does it over-engineer? If a plan is logically flawed or hallucination-prone, propose a superior alternative or flag DROP_UPDATE. If the graft modifies a prompt, walk it through CLAUDE.md Principle 5 lenses (Cosplay / Breathing / Quota / Re-Anchor / Permission / Tension / Pink Elephants) and flag any violation by name.

### Compiler Simulation Gate (for all code grafts)
Trace execution against the actual source file — not a prose-level review. Verify simultaneously:
- **(a) Existence** — variable/function physically exists at specified location
- **(b) Timing — Populated State** — variable holds populated value BEFORE first consumption
- **(c) Timing — No Shadowing** — no step reads from a variable only written in a later step
- **(d) Scope** — variable accessible at point of use, not trapped in conditional/loop
- **(e) Type Parity** — consumer's expected type matches assigned type

> "The sequence looks right" is NOT a passing verdict. This gate fires on every code graft.

### Handoff Strategy Validation
Full Reconstruction valid only for short payloads (<150 lines). Larger files MUST use Targeted Edit. If the Architect proposed Full Reconstruction on a large file, OVERRIDE and prescribe Targeted Edit.

### Instruction Contradiction Check
Does any new rule break an existing rule in the source? Does any preserved example, worked-example block, demo, anti-pattern, or other illustrative content in the modified zone STILL DEMONSTRATE behavior the new rule forbids? Logic conflicts, parity crashes, variable mismatches, formatting drifts, AND rule-vs-example demonstrations all count. **LLMs weight concrete examples more heavily than abstract rules. When a graft changes a rule, the red-team must verify that every example in or near the modified zone still aligns with the new behavior — silent example-rule contradictions are the most common failure mode this gate catches.** (E.g., P4-A v1 left a RENOVATE example row after a rule forbidding RENOVATE rows; P3 prior surgery left I/O Parity Check + Integrity Checklist in `<example_workspace>` after removing the corresponding rules.)

### Omission Audit (Claude Code lead — file access required)
Cross-reference the GRAFTs against the upstream context the Architect was working from:
- Phase 1 forensic evidence dump
- Pre-existing target file (if refactor)
- Explicit user instructions in the trigger

For each item raised in upstream context, verify ONE of:
- (a) A GRAFT explicitly addresses it
- (b) The Architect logged an explicit "intentionally not addressed — reason" entry

Items meeting NEITHER are SILENT OMISSIONS. Flag each by name as a candidate new GRAFT. Empty omission list is a valid output ("Omission Audit: no silent omissions detected") — silence is failure here, not approval.

### Concept Residency Check (deletion AND rename grafts)
For each graft that DELETES content (paragraph, bullet, named term, rule, example block), identify every named concept or vocabulary token in the deletion zone. For each named concept, verify no surviving text in the file references it by name. If a surviving reference exists, EITHER (a) the deletion creates a dangling pointer — block the graft until the inbound reference is also resolved, OR (b) the surviving reference is in a different context that's truly self-contained. Default to (a) — flag for Architect review.

Practical workflow: list the named concepts being removed (e.g., 'PROTECT status,' 'P2 (The Draftsman)', 'Supremacy Clause'), then grep each for inbound references. Zero matches = safe deletion. Non-zero matches = review whether each remaining reference is self-contained or dangling.

This check is asymmetric: it fires on deletion AND rename grafts, not on pure insertion.

**Also check who POINTS AT the file, not just who names the concept.** A graft that substantially changes what a file CONTAINS — emptying it, condensing it, moving its substance somewhere else — silently invalidates any OTHER file that instructs a reader to go and read it. This evades every check above: the filename is unchanged so a name-grep finds nothing, and the pointer still resolves so nothing errors. It just quietly becomes a lie. Before clearing such a graft, grep `CLAUDE.md` and all of `.claude/commands/` for the target file's PATH or filename, then re-read each hit and confirm the instruction is still TRUE. Canonical incident: 2026-07-27, the lessons audit emptied `memory/feedback_workflow.md` into one-line pointers while `compass.md` still told every fresh session to read that file for "every dated cross-session lesson." The project's anti-drift skill was degraded by the very refactor meant to strengthen the protocol, and nobody noticed until the Chief Architect re-pasted his own prompts and forced a line-by-line diff.

**Renames are the dangerous case, and the scope is CROSS-FILE.** A graft that renames or removes a *named* mechanism can silently break a DIFFERENT prompt that references that name — single-file design/red-team handoffs hide the coupling completely. Before clearing any rename/remove graft, grep ALL of `Prompts/` **and** `run_phase*.py` for the mechanism's name plus any cross-reference label. Canonical incident: the 2026-06-24 P4 surgery replaced the "Multi-Value Mirror Prohibition," but `prompt3_formulator.txt:306` still stamped 3+ item cards' Extra with a directive naming "P4's Multi-Value Mirror Prohibition (Fix 4-A)" and the OLD behavior — contradicting the new P4 logic AND leaking an internal flag into student-facing Extra (P5 exports Extra verbatim). The handoff packet was P4-only, so it surfaced at output QA twelve days later, never during design. A name-grep across `Prompts/` at design time would have caught it instantly.

### Butterfly Effect
What does this break downstream? Map dependencies.

### Standalone Manifest Gate — GO / NO-GO (FINAL)
- ✅ **GO** — All grafts internally consistent, non-contradictory, safe to execute.
- 🚫 **NO-GO** — Output corrected, unabridged, standalone grafts. These are instructions for the Surgeon, not final code. Treat the Surgeon as a senior developer: plain English for complex logic; verbatim strings only when exact text is required.

## Output structure (lead with this)

Every Phase 3 output MUST lead with the following 4-section block before the VERDICT fence. This is mandatory.

🎯 **My Understanding:** Plain-English statement of what the Architect's manifest is trying to achieve.

🧩 **The Verdict (ELI15):** Plain-English summary of what passed, what failed, and what was modified. No graft-numbering jargon, no line-number references. One paragraph.

⚠️ **Assumptions & Ramifications:** What was assumed about ambiguous grafts, and what downstream effects the verdict implies for Surgeon execution or dependent files.

🚦 **Alignment Check:** Explicit prompt asking the user to confirm the verdict summary is correct before invoking /surgeon. NOT optional.

~~~
[VERDICT: CLEARED FOR SURGERY] or [VERDICT: REJECTED — BACK TO DESIGN]
[SURGERY PRESCRIPTION: 🟢 Full Reconstruction | 🔴 Targeted Surgical Diffs | scope justification]
~~~

## Mode Toggle

- 🟢 **Full Reconstruction** — default for fresh sessions or when ≥50% of grafts modified. Output ALL grafts, even unchanged.
- 🔴 **Standalone Grafts** — default for mid-session work where only 1-2 grafts changed. Output only modified grafts. Every graft output must be fully lossless and standalone.

> 🚫 If even one graft requires a change, you cannot declare CLEARED FOR SURGERY until you have output the corrected version. "Cleared" means 100% of the latest grafts you received are bulletproof.

## Task input

$ARGUMENTS
