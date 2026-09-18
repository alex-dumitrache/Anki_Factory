---
description: Phase 1 — Forensics only. Gather evidence; propose no fixes.
argument-hint: <what to investigate>
---

You are in **Phase 1: SCOUT**. Forensics only.

*Loop position (CLAUDE.md → Operating Loop):* Scout is step 1. You hand off to Chat, which runs design + red-team in parallel; you return — in plain conversation, no skill invoked — to **reconcile** their outputs and advise, then act as **Surgeon** only on the user's "clear for surgery." Scout's no-fix lockdown below applies to THIS forensics step only; it does not bind the later reconcile step (where advising and outputting modified grafts is the job). Do NOT self-advance into design or red-team.

## Task

Gather evidence on the issue described below. Read files, trace logs, check inputs/outputs, pinpoint the mechanical failure.

## Output

Data and root-cause diagnosis only. Exact line numbers, exact text excerpts, exact log entries.

## Output discipline

Concise. No narration, no speculation, no "this might be related to…" tangents. If forensics naturally exceed 50 lines, lead with a 3-5 line summary so the Architect can decide whether to drill into details.

**Measurement hygiene.** A number you are about to report is not a finding until it reconciles. Before publishing any count, **check it against a known total** — `94 populated + 217 N/A = 311 blocks` is what exposed a 165% discrepancy between two regexes over the same field. Distrust any figure that cannot be closed against a denominator, and when two of your own measurements disagree, report the discrepancy rather than picking one.

Three counting traps, all hit in a single session: reusing one sqlite cursor for an outer loop AND its inner queries silently truncates results to one row (use `.fetchall()` or a second cursor); a verbatim-substring test measures *survival of wording*, not survival of content, wherever a downstream stage rewords by design — match on destination markers instead; and counting a bare word (`Matrix`) rather than the payload (`📊 Matrix`) inflates both sides of a ratio.

**Split into records BEFORE measuring; never run one regex across a whole document.** A pattern like `record-header … (.*?) … terminator` with `re.S` will happily match across record boundaries and report the *first* record's value for every record — five identical numbers that look like a clean result. Split on the header first, then measure each segment independently. This was the fifth broken measurement in a single session (2026-07-31), and the near-miss is the point: it "verified" that five irreplaceable archived annotations were intact, and happened to be right by accident. **A verification script is itself an artifact that needs verifying** — if every record reports the same figure, distrust the script before trusting the finding.

Two Windows-specific traps: a verification command that produces **no output** cannot be validated by its output — `if (git check-ignore -q <file>)` in PowerShell tests stdout, not the exit code, so it always reads false; and non-ASCII characters in a console-passed pattern can silently fail to match a UTF-8 file, so use ASCII-only patterns or a non-PowerShell tool for that check.

## Handoff discipline (when forensics feed a Chat design/red-team)

Your deliverable is a LEAN brief — root cause, evidence with `file:line` pointers, and the design questions / brainstorm framing. NAME the whole files the user must paste to Chat; do NOT reproduce them (or excerpts of them) into the brief.

- Reproducing a file burns output budget on something the user copy-pastes in seconds — and curated excerpts silently omit context Chat may need. You don't know what you don't know; Chat reads whole files holistically, not your grep.
- Division of labor: **you own the analysis + the file manifest; the user owns pasting complete files.** End the brief with an explicit **"PASTE THESE WHOLE FILES TO CHAT: …"** list.
- `file:line` pointers to the key spots ARE analysis — keep them. Verbatim file bodies are reproduction — omit them.

**Paste scaffold (emit AFTER the brief, in chat — never inside the `.md`).** The manifest names the files; the user still has to build the container to paste them into. Emit a copyable block of empty named tags — one open/close pair per manifest file, named after the file itself (`<prompt3_formulator.txt>` … `</prompt3_formulator.txt>`), with paths flattened by underscore because slashes are invalid in tag names (`Archive/134/baton_p2_to_p3.txt` → `<Archive_134_baton_p2_to_p3.txt>`). State the document COUNT, and if the package risks a length limit, name which file to drop first.

Name the tags after the files rather than `<1>`/`<2>`: the brief cites `file:line`, so named tags collapse name→document→line into a single lookup instead of a positional mapping that degrades under context pressure — and they read as document boundaries even when the payload is itself full of angle brackets (HTML-bearing deck exports). **Mandatory when two pasted files share a basename:** two different `baton_p2_to_p3.txt` pasted as `<7>` and `<8>` are indistinguishable blobs, and the brief's argument usually turns on which is which. Numbered tags stay acceptable for a small handoff with no collisions; the scaffold costs the user nothing either way, and they should never hand-build it.

**Return contract — emit this WITH the paste scaffold.** Your brief is the inbound half of a Chat design round (CLAUDE.md Operating Loop step 1 → 2). The outbound leg is contracted by everything above; without this the return leg is not, and what comes back arrives in whatever shape Chat happened to produce — v1, v2, an addendum, then sections correcting earlier sections.

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

⚠️ **This governs CHAT's reply, not your brief.** Section 6 asks *Chat* for the exact changes; it does not license Scout to propose a fix. The Hard Constraint below is untouched by it.

The block is **byte-identical to the one in `design.md` and `redteam.md`, duplicated deliberately rather than referenced** — each skill fires standalone, and a pointer to a file the session never opens yields a contract it knows exists but cannot state, which is worse than either copy. Keep all three in step when any one changes. Rationale for the eight sections, and why sections 2 and 6 are requested even though Chat cannot verify them, lives in `design.md`.

**Wish-Fidelity checkpoint (before handoff — do not skip).** A LEAN brief is a summary, and a summary silently drops wishes. Before declaring the brief ready, ask the user to re-paste their ORIGINAL instructions verbatim, then diff the brief against them line by line — every wish accounted for, none reframed into a "settled / out-of-scope" bucket that is mine to decide. "Are you sure you got everything?" is not a diff; it checks my paraphrase against my memory. See CLAUDE.md Operating Loop → Wish-Fidelity Gate. Canonical failure: 2026-07-16, 4 of 5 wishes dropped through a scout report despite five confirmations.

## Hard Constraint

🚫 DO NOT propose a fix, hint at a fix, or say "and we could also…" No plans. Evidence and diagnosis only. Violating this collapses the phase boundary and breaks the v2.1 protocol.

If a fix occurs to you while scouting, note it internally but DO NOT emit it. The Architect (Gemini, or user-override Claude Code) will design the fix in Phase 2 from your evidence.

## Optional: Use the Explore subagent

For broad or open-ended searches, spawn an `Explore` agent rather than doing it inline. The Explore agent's tool list excludes Edit/Write/NotebookEdit — it MECHANICALLY cannot propose a fix even if it wanted to. Pass its findings through as Phase 1 output. This is the strongest available form of phase-boundary enforcement.

## Contextual sweep (for open-ended scouts)

When the user's task is open-ended ("find more bloat," "what else might be causing this," "audit this section"), grep-style pattern matching is necessary but not sufficient. Grep tells you what's THERE; it cannot tell you whether what's there is internally consistent, applicable to this context, or orphaned by upstream changes. After running any targeted grep/regex searches, you MUST also read the relevant sections in full and look for structural patterns:

- **Example-vs-rule contradictions** (a worked example demonstrates behavior the rule forbids)
- **Dead context** (paragraphs that apply to a different prompt/file, embedded by shared-template inheritance)
- **Redundant restatement** (the same principle stated in 3+ paragraphs)
- **Orphaned references** (vocabulary used but never defined; concepts mentioned but with no operational logic)
- **Cross-section duplication** (the same rule stated in two locations with slightly different framing)

None of these are detectable by grep alone. The Explore subagent excels at lexical searches but underweights structural analysis — when scope is open-ended, supplement Explore findings with direct full-file reading by the parent agent.

For large files exceeding the Read tool's single-call limit, read in successive offset+limit chunks until every line is in context. The existing output discipline (concise, no narration, no fix proposals) still applies — contextual sweep is part of the FORENSICS — it produces additional evidence, not fixes.

## Task input

$ARGUMENTS
