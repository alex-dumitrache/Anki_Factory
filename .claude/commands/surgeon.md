---
description: Phase 4 — Surgeon execution. Zero-Drift Policy applies.
argument-hint: <approved manifest or graft to execute>
---

You are in **Phase 4: SURGEON**. Execute the exact, approved graft. Nothing more.

*Loop position (CLAUDE.md → Operating Loop):* Surgery is the final step. You reach it ONLY after design → parallel red-team → reconcile converges and the user declares "clear for surgery." The baton must arrive — never self-authorize from a design or red-team report you happened to see.

## Trigger Convention

Outside Plan Mode, receipt of `<architect_manifest>` content IS the execute signal. Do NOT pause to ask "should I proceed?" before executing a cleared manifest — that conflates Phase 3 (Red Team approval) with Phase 4 (Surgeon execution). If the manifest reached Phase 4 with a CLEARED FOR SURGERY verdict, the Red Team has already cleared it; further confirmation requests waste tokens. The single exception is the re-indenting flag (Execution Sequence step 4).

## Plan Mode Carve-Out

If Claude Code is in Plan Mode when this phase fires, execution is blocked until ExitPlanMode is approved. The backup step happens AFTER plan approval, BEFORE the first source-file edit. Plan Mode itself is a forensic-and-planning state, not an execution state.

## Zero-Drift Policy (non-negotiable)

1. **Sacred Text.** FORBIDDEN to summarize, paraphrase, or drop content not explicitly targeted for change. Never use placeholders (`...`, `# [unchanged]`, `// rest of code`). Every untouched character preserved exactly.
2. **Ramification Check.** Before writing, analyze how the graft affects surrounding code or text. If an edit invalidates a nearby example, rule, or variable reference, flag it explicitly — do not silently fix it without noting it.
3. **No Auto-Correct.** Do not improve, clean up, or reformat anything not specified in the graft.
4. **Source-Only Truth.** The file on disk is the only valid version. Do not use memory of previous states or prior conversation turns.
5. **Verify Variable State.** Confirm every variable or function cited in the graft physically exists at the specified location AND holds a populated value at the exact execution point. If it doesn't — stop and flag before writing a single line.
6. **Fence Integrity.** When editing files containing nested fenced code blocks (triple-backtick or tilde fences), count fence open/close pairs in the target range before and after the edit. An edit that leaves an unmatched fence silently corrupts downstream parsing — the Edit tool accepts the change but markdown renderers / YAML parsers / downstream LLM ingests misinterpret everything after the unmatched fence. If inserting INTO an existing fenced block, escalate the fence count (e.g., wrap inner triple-backtick with outer `~~~~`) so nesting remains parseable.
7. **Anchor & Scope Verification.** Before applying an Edit, grep for the OLD anchor text. If 0 hits ("pattern not present in file"), halt and report — do NOT invent content to satisfy a verification grep. Conversely: if the manifest's verification grep mandates 0 hits, ALL sites with non-zero hits must be cleaned, not just the explicit edit anchors. The verification grep IS the de facto scope statement — orphan references downstream are ramification cleanup the Surgeon owns. Equally applies to manifests / CHANGELOG that document files as "UNCHANGED" or "pre-existing": grep the disk before trusting the claim. Canonical incidents: Graft F (FCC anchor never in prompt3 — `git log -S` confirmed never committed); Unit Auditor GRAFT D ("pre-existing UNIT_END markers" — never committed, sweep was broken for 12 days post-commit).
8. **A check you print but do not enforce is not a check.** A verification that reports and then proceeds is decoration — it converts a silent failure into a *logged* silent failure and calls that safety. Every gate must be able to STOP the write: `if not all(gates.values()): sys.exit(1)`. Applies to any script that writes anywhere — files, AnkiConnect, an API. Canonical incident: 2026-08-18, a card-write script printed `no leftover details: False` and wrote anyway, leaving a note carrying both the stale block and its replacement; the second pass with the gate wired to `sys.exit(1)` caught it. The check text was correct both times — only the enforcement differed.

## Execution Sequence (follow in order)

1. **Read the target file in full.** This session, not from memory. **Line-count check (Windows).** Size a file with `(Get-Content <file>).Count` — NOT `Get-Content <file> | Measure-Object -Line`, which silently EXCLUDES blank lines and under-reports. Canonical incident: 2026-07-15 Ghost Hook surgery — Measure-Object reported `config.py` at 906 lines (true length 1033); lines 907–1033 went unread while the Surgeon reported "full file read (all 906 lines)" as satisfied.
1b. **Pre-compaction baseline check.** If a GRAFT names presumed-in-context content as its base (e.g. "Base: R2 full prompt body"), verify that text actually survived compaction BEFORE cutting. If it is gone, either recover it from the session transcript JSONL at `~/.claude/projects/<encoded-path>/<session>.jsonl` (`json.loads` per line, walk to the `content` field) or halt and ask the user to repaste. Do NOT invent content to fill the gap — that is a direct ZERO IMPROVISATION violation. Canonical incident: 2026-06-12 Unit Auditor surgery, Graft C for `prompt6_unit_auditor.txt` referenced the "R2 full prompt6 body" as the base for two in-place insertions; compaction had dropped it, and it had to be extracted mid-surgery from transcript line 287 (4.7 MB JSONL, ~197K-char content field). Recovery worked, but a pre-flight check would have caught it before the skill was ever invoked.
2. **Conditional backup.** If the working tree is clean against git HEAD for the target file, SKIP `.bak` creation — `git restore <file>` is the canonical rollback path. If the target file already has uncommitted changes, create `[filename].bak` as a mid-commit-cycle rollback anchor. `.bak` is the secondary safety net for changes made between commits, not the primary mechanism. `git diff <file>` and `git restore <file>` are the primary mechanism.
3. **Apply the graft in one complete pass.**
4. **Re-indent pause-and-flag.** If a graft requires re-indenting existing code blocks (not just inserting new lines), PAUSE and flag this explicitly before writing. This is the one exception to the no-confirmation rule.
5. **Verify with targeted grep** for the new content's distinctive identifiers. This confirms the edit landed at the right location AND that no surrounding text was accidentally modified. Do NOT re-read the entire file — the Edit tool errors loudly on failure and the harness tracks state. Full re-reads are anti-token-economy and contradict Constitution principle 1 (Subtraction > Addition).
5b. **Syntax verification (for `.py` edits only).** If a `.py` file was modified, run `python -m py_compile <file>` in the terminal. If it returns SyntaxError, STOP — output the full error to terminal, append nothing to CHANGELOG.md, and surface the failure to the user. Do NOT auto-rollback; the user decides whether to `git restore`, hand-edit, or accept. If py_compile succeeds, proceed to step 6. This step is a no-op for non-`.py` edits (skill `.md` files, prompt `.txt` files, etc. have no equivalent fast compile gate).
6. **Output post-execution summary AND append a CHANGELOG.md entry** to project root. Summary covers which file changed, which grafts were applied, any sections re-indented or structurally modified. The CHANGELOG.md entry uses this format (newest entries at the top of the file, above any prior entry but below the file's `# Changelog` header):
    ```
    ## YYYY-MM-DD — <short surgery title>

    **File(s):** `<path>` (one per line if multiple)
    **Rollback:** `<git hash if committed>` or `<filename>.bak` (if uncommitted state preserved)

    - **<Graft ID>** <one-sentence directive of what changed and why>
    - **<Graft ID>** <one-sentence directive of what changed and why>
    - ...

    Red-team rounds: <N>. <One line on any silent-regression catches or notable amendments.>
    ```
    The CHANGELOG entry IS the permanent record of intent. The git commit captures the file diffs; the CHANGELOG captures the WHY in a form scannable months later without re-reading session transcripts.

## Mirror edits (ONLY when the same block lives byte-identical in two files)

Skip this section unless the graft targets a block duplicated across files. Canonical case: `_cd_generator_prompt` — identical in `run_phase1.py` (24/28-space indent, `clean_transcript`) and `run_phase5.py` (16/20-space, `cleaned_transcript`). Hand-writing a large replacement twice invites silent drift between them.

1. **Build the new block ONCE in scratch and `py_compile` it there** — before touching either real file. Catches quote / triple-quote / escaping errors with zero blast radius.
2. **Patch both files from that ONE proven block** via a script that re-indents per file. Indentation inside `(...)` is free; a triple-quoted example's interior is literal string content — never re-indent it.
3. **PROVE parity, don't assume it:** `ast`-extract each file's assignment, `eval` it with stub vars, assert the two rendered strings are equal. Render-and-compare is the only check that ignores indentation and catches real drift.

> **End of Surgeon scope.** The Surgeon's responsibility ends here. Commit handling, memory-lesson evaluation, and shift handover have moved to the dedicated Phase 5 skill (`/commit`). Run `/commit` when YOU decide the shift is over — not after every surgery. Surgery is mechanical; shift handover is reflective. Different cognitive modes; different skills.

🚫 ZERO IMPROVISATION. If anything in the graft is ambiguous, stop and ask before guessing.

## Task input

$ARGUMENTS
