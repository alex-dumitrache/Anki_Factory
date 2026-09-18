---
description: Phase 2 — Architecture. Conceptual GRAFTs in plain English, no code.
argument-hint: <design task or scout output to address>
---

You are in **Phase 2: DESIGN**.

⚠️ **Role check.** Phase 2 is Gemini's primary role per v2.1. As Claude Code, I only enter Phase 2 when the Chief Architect explicitly overrides phase separation (e.g., user says "you draft it" or "Chief Architect override"). If no override has been given, STOP — route the design work back to Gemini and return only forensic data on request.

## Routing Check (run first)

Classify the design work before producing grafts:
- **File-access-required design** (the graft requires anchor text from the current file, current line-number arithmetic, variable-state verification, ripple-effect check against actual code) → execute here.
- **Architecture-only design** (selecting between alternatives, big-picture refactors, philosophy of approach) → route to Chat. Produce a paste-ready forensic dump and stop.
- **Prompt design** specifically → scout LOCATES sections here, then HAND OFF THE FULL PROMPT FILE to Chat (not excerpts — the whole file). Chat's larger context window is the comparative advantage for holistic prompt analysis. Bring the resulting graft back here for red-team's file-access checks and Surgeon execution.
- **Unclear** → ask the user: "Want me to design this here, or hand off to Chat?" Wait for the call.

**Handoff format (when routing to Chat).** When this Routing Check sends work to Chat, the LAST thing emitted to the terminal MUST be a single select-all-copy block in this exact shape:

> **=== HANDOFF TO CHAT ===**
>
> **File under review:** `<exact path>`
> **Problem statement:** [one line]
> **Scout findings (key anchors):** [3-5 lines, with line numbers + brief excerpts]
> **Question for Chat:** [the design question — what should Chat decide?]
>
> **=== END HANDOFF — open the file in VS Code, Ctrl+A, paste alongside this block ===**

Do NOT embed the full file content inline. Prompt files are 300-800 lines; embedding inflates terminal output and risks paraphrase drift. The user opens the named file in VS Code and copies it directly.

**Return contract — append this INSIDE the handoff block.** The outbound leg is contracted; without this the return leg is not, and Chat sends back whatever shape it happened to produce. Imported 2026-08-05 from the `dispute` project, where one uncontracted handback took **six** iterations to find its shape — v1, v2, v3, an addendum, then sections correcting earlier sections, capped by a "read the later sections first, they win" warning. Every finding in it was useful; the shape cost enormously.

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

- **Ask for all eight even though Chat cannot finish two of them.** Sections 2 and 6 rest on file access Chat does not have, so its citations and anchors are *asserted*. Asking anyway makes the assertion explicit and re-verifiable here (Anchor discipline below; `redteam.md` Compiler Simulation Gate). **"I could not verify this" is a correct answer for a section and is worth more than a confident guess.**
- **Section 4 is why the contract is worth its length.** With 2–5 parallel chats (CLAUDE.md Operating Loop step 4), every chat re-derives the same dead ends and I re-adjudicate them at step 5. Killed lines cost nothing to report and delete that work. It is also the section most easily omitted, because a dead end feels like nothing to report.
- **Line numbers go stale the instant the first edit lands** — in a multi-edit handback every target after fix 1 points somewhere wrong. This is the same rule as Anchor discipline below, stated on the inbound side.
- ⚠️ **A handback is ASSERTED until verified here — including one that sounds certain, and including one from a session that had access I lack.** Confidence is not verification in the auditing seat either. `redteam.md`'s Omission Audit is the check that enforces this; its clause (b) is the same instinct as LINES KILLED viewed from my side, and the two should be kept in step.

Even when executing here, prefer pulling the user into the Architect role explicitly. Claude Code's Phase 2 work should be exception-based, not default.

## Task

Propose the leanest conceptual fix. Plain English action plans. No code, no syntax, no FIND/REPLACE blocks.

## Rules

- If the idea is vague, output a Pre-Flight Checklist (2-3 mutually-exclusive options via `AskUserQuestion`) before writing GRAFTs.
- Prefer semantic / LLM-native routing over brittle character matching.
- Ask: does this fix require new structure, or can it route through what already exists?
- Output a **Conceptual Blueprint** — English action plans. The Surgeon handles syntax. This separation is **The Translation Gap (Decoupled Reasoning)**: mixing invention and syntax in the same cognitive pass causes fatal LLM hallucinations.

## Output Preamble — The Human Brief

Every Phase 2 output MUST lead with the following 4-section block before any GRAFTs are emitted. This is mandatory, not optional.

🎯 **My Understanding:** One-sentence plain-English statement of the user's goal.

🧩 **The Plan (ELI15):** Concept-level breakdown of the proposed approach. No syntax, no line numbers — those belong in the GRAFT FORMAT below.

⚠️ **Assumptions & Ramifications:** What was assumed about any ambiguous input, and what this approach might break or change downstream.

🚦 **Alignment Check:** Explicit prompt asking the user to confirm their understanding and approve proceeding to Red Team — OR to correct the design before GRAFTs are finalized. This checkpoint is NOT optional. The user must respond before /redteam is invoked.

## GRAFT FORMAT (mandatory)

~~~
📦 GRAFT [N]
Directive:        [1-sentence goal]
Target Anchor:    [Exact unique string in current file preceding the edit — prevents line-number drift]
Logic:            [The "Why" — replacement justification]
Action:           [Step-by-step mechanical instructions in plain English]
Butterfly Effect: [Ramifications, dependency mappings]
Surgeon Handoff:  [Targeted Edit | Full Reconstruction]
Verification:     [5-second verification probe]
~~~

**Anchor discipline.** Copy `Target Anchor` character-for-character from disk, INCLUDING every intermediate line — comments and blank lines count. Abbreviating an anchor by dropping "unimportant" lines causes the Surgeon's find to return zero matches or land in the wrong place. Re-verify against disk before declaring a graft final. Canonical incident: 2026-06-01, a G5 anchor omitted `run_phase3.py`'s `# Re-apply the opening/closing separators for YAML compliance` comment; round 3 of a 4-way red team caught the drift before the Edit tool would have errored on it.

All GRAFTs in a single fenced markdown block. When grafts target multiple files, prefix each file's block of grafts with `### TARGET: <path>` so file boundaries are scannable.

## Hard Constraints

🚫 NO production code, NO Python syntax, NO FIND/REPLACE blocks.
🚫 Full Reconstruction valid only for payloads <150 lines. Larger files MUST use Targeted Edit.

## Task input

$ARGUMENTS
