# Chat Handoff — Reconcile P3's "Multi-Value Spec-List Signal" with the post-surgery P4 (Archetype split)

> **Purpose:** forensic packet for the DESIGN chat. Your job (Chat): design the P3 graft.
> **Attach to the design chat alongside this file:** `Prompts/prompt3_formulator.txt` (FULL) **and** `Prompts/prompt4_reverse.txt` (FULL, post-surgery — so you can match P3 to P4's new logic).
> **Status:** SURGERY EXECUTED 2026-06-26 — GRAFT 1 (delete the Multi-Value Spec-List Signal) applied to `prompt3_formulator.txt` Template 6 (clean tree, no `.bak`, not yet committed). Red-team skipped by Architect decision (pure verified deletion). Companion to the 2026-06-24 P4 surgery; commit the two together. See CHANGELOG.md.
> Produced by Claude Code (scout). Claude Code does not design/red-team prompt text; it will reconcile your grafts and operate.

---

## 1. One-paragraph problem

The 2026-06-24 P4 surgery replaced the **"Multi-Value Mirror Prohibition"** with a **two-archetype branch** (`prompt4_reverse.txt:99–129`): P4 now self-inspects a 3+ item Forward Back and routes **Archetype A (fingerprint list) → clean swap** vs **Archetype B (property/example list) → consequence pivot**. But `prompt3_formulator.txt:306` still stamps every 3+ item Spec card's `Extra` with a directive hard-coding the **old** rule — and explicitly names the deleted mechanism. That stamp is now (a) **contradictory** for Archetype A, (b) **redundant** (P4 self-detects; nothing consumes the flag), and (c) **leaking** into the student-facing card.

## 2. The exact P3 rule (verbatim)

`prompt3_formulator.txt:306`, inside **Template 6 — SPEC / OPTIMIZATION (Group C: Boundaries Domain)**, right after the Front/Back format (lines 303–305):

> * **Multi-Value Spec-List Signal (Mandatory):** If the Back Line 1 of this card will contain three or more comma-separated values (a value list rather than a single atomic metric), you MUST append the following flag to the card's Extra field: `⚠️ SPEC-LIST: P4 must use consequence-based framing for Rev_Front — standard Spec Flip is FORBIDDEN (3+ item list triggers Mirror Glitch).` This signal persists through the pipeline as a trigger for P4's Multi-Value Mirror Prohibition (Fix 4-A). If the Extra field already has content, append this flag after a `<br>` separator. If Extra would otherwise be N/A, set Extra to this flag alone.

## 3. Findings (file-verified)

**(A) CONTRADICTION — the blocking one.** The stamped directive says *"consequence-based framing… standard Spec Flip is FORBIDDEN"* and points to *"P4's Multi-Value Mirror Prohibition (Fix 4-A)"* — a mechanism GRAFT 1 **deleted**. For an **Archetype-A fingerprint card**, P4's new rule says *"clean swap; consequence-pivot FORBIDDEN,"* while the Extra says the opposite. P4 receives contradictory, card-specific orders; the imperative Extra ("P4 **must**…") can easily win → **re-creates the umbrella-card bug** for exactly the cards GRAFT 1 targets.

**(B) REDUNDANCY — P4 self-detects; nothing consumes the flag.**
- P4 (post-surgery) keys on the raw list ("three or more comma-separated items" in Forward Back L1), NOT on the flag. `rg "SPEC-LIST" prompt4_reverse.txt` → **zero**.
- `rg "SPEC-LIST" prompt5_exporter.txt` → **zero**. `rg "SPEC-LIST|Multi-Value|Fix 4-A" run_phase*.py config.py run_master.py` → **zero**.
- Only producer/consumer of the string in the entire repo is `prompt3_formulator.txt` itself. The flag is **vestigial** — it triggers nothing; it only injects (now-wrong) text.

**(C) LEAK — the directive reaches the student-facing card.** P3 appends the flag to `Extra`; P5 exports `Extra` verbatim (no stripping). Confirmed in `ANKI_IMPORT_READY.txt:14` (06-23 run): the literal string *"⚠️ SPEC-LIST: P4 must use consequence-based framing for Rev_Front — standard Spec Flip is FORBIDDEN (3+ item list triggers Mirror Glitch)"* appears in a real flashcard's Extra column. Also present in the current run's pre-export final cards (`unit_sweep_final_anki_cards_with_reverse.txt:26` ID3, `:87` ID9). Internal pipeline jargon should never land in an exported field.

**(D) RECURRENCE — the bug is a documented pattern now, not a one-off.** `ANKI_IMPORT_READY.txt:14` (06-23, pre-surgery): card **"Cloud Ownership Models (Main members)?" → "Private, Public, Hybrid, Community"** (a 4-item canonical-member fingerprint, Archetype A) got the convoluted pivot reverse **"Cloud access arrangements, each defined by who may use and access the infrastructure (exam classification)? → Cloud Ownership Models."** This is the *second* documented instance of the umbrella-card failure (first: IaaS/PaaS/SaaS, V119). Re-processed today, this card would hit the P3↔P4 contradiction in (A). *(Date caveat: this card predates the P4 surgery; cited as evidence of the failure class + the leak, both structurally still live.)*

## 4. Design space (framed — Chat decides; evidence favors deletion)

- **Option A — DELETE the signal (Subtraction).** Remove the `Multi-Value Spec-List Signal` from `prompt3_formulator.txt:306` entirely. P4 self-detects 3+ item lists and self-routes Archetype A/B (GRAFT 1); the flag triggers nothing (Finding B) and now mis-instructs P4 (A) and pollutes Extra (C). Cleanest; aligns with Constitution "Subtraction > Addition." **Evidence points here.**
- **Option B — NEUTRALIZE/RETARGET.** Keep a minimal, non-prescriptive marker (e.g., a flag that merely notes "3+ item list" without prejudging consequence-vs-swap, and placed somewhere P5 does NOT export). Only justified if a downstream consumer needs the hint — none currently does.
- **Option C — UPGRADE (move classification upstream).** Have P3 run the fingerprint-vs-property test and stamp the archetype for P4 to execute. Duplicates P4's logic, deepens coupling — likely over-engineering given P4 already self-routes.

## 5. Open design questions for Chat

1. Delete vs neutralize vs upgrade (§4)? Given P4 self-detects and nothing consumes the flag, is there ANY reason to keep an upstream signal?
2. If keeping any flag (B/C): it must NOT live in an exported field. Where should it go so it doesn't leak to the student (Finding C)? (Separate question: should P5 gain an Extra-sanitizer as defense-in-depth, or is fixing the source sufficient?)
3. Template 6 is the only emitter today. Do any other P3 templates produce 3+ item Backs that would need the same treatment, or is Spec/Template-6 the complete surface?
4. Adjacent (not this graft): the recurrence (D) is the 2nd documented North-Star-#2 escape — does it now meet the **GRAFT 3** adoption gate the P4 red team set (≥2 documented escapes)? Flag for a separate decision.

## 6. Scope notes

- **P4** already surgered (Archetype split) — do NOT redesign it; design P3 to MATCH it.
- **P5 / run_phase*.py** — no code changes implied by the P3 reconciliation itself (orchestrators are flag-agnostic). The optional Extra-sanitizer (Q2) would be a P5-prompt change, separate decision.
- **status=N/A** (old OQ) remains out of scope/unverified.
