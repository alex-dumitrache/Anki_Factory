# Chat Handoff — Raise the threshold for REVERSE-card creation (Prompt 4)

> **Purpose:** forensic packet for the DESIGN chat. Your job (Chat): design the graft(s).
> **Attach to the design chat alongside this file:** `Prompts/prompt4_reverse.txt` (FULL file).
> Prompt 5 is NOT needed — it is exonerated (cosmetic only, see §8).
> Produced by Claude Code (scout phase). Claude Code does not design or red-team prompt text; it will reconcile your grafts and operate.

---

## 1. The failure card (real output, video 119)

Forward (accepted as good by the architect):
- **Front:** "Cloud service models (Main members)?"
- **Back:** "IaaS, PaaS, SaaS."

Reverse (the card the architect rejects as useless / convoluted / "semantic gymnastics"):
- **Rev_Front:** "The umbrella category for the tiers that split stack management between provider and customer (Term)?"
- **Rev_Back:** "Cloud service models."

Architect's proposed BETTER reverse (the genuine inverse):
- **Q:** "IaaS, PaaS, SaaS — what are they?"  →  **A:** "Cloud service models."

## 2. Goal

Raise the threshold for *creating* reverse cards so the pipeline holds back from manufacturing low-value "definitional-recognition" reverses like the one above — **without killing the reverse rule wholesale.** Genuine bidirectional cards must still be produced.

## 3. Pipeline trace (origin → final)

| Stage | Evidence (Archive/119) | What happened |
|---|---|---|
| P2 baton | `baton_p2_to_p3.txt:165` | Only a *cluster* about IaaS/PaaS/SaaS exists. No "Main members?" card. |
| Forward born | final card `Origin` field | "Main members?" forward was auto-injected by a *"Paranoia 3 Enumeration Audit — autonomous bundle injection."* `Meta: Spec … status=N/A`. |
| **P4 Mode 1** (draft) | `forensic_raw_p4_pass1.txt:65–66` | Generated the umbrella → "Cloud service models" reverse. |
| **P4 Mode 2** (Sovereign Auditor) | `forensic_raw_p4_pass2.txt:128–144` | Passed all 7 Sins. Anti-echo: "0w match (Fwd Back is bare list 'IaaS, PaaS, SaaS') → PASS"; "'Cloud service models' (exempt, Spec-Flip extraction) → PASS". |
| **P5** (Exporter) | `forensic_raw_p5.txt:29` | Cosmetic only: bolding + DuckDuckGo image link. Semantics unchanged. |

Mode 1 / Mode 2 = the two Operational Modes in `prompt4_reverse.txt:43` (Mode 1 generates, Mode 2 is the Sovereign Auditor / Sin checks).

## 4. ROOT CAUSE — the exact rule that manufactured it

Card `Meta = Spec` → **Zone 2** (`prompt4_reverse.txt:82`) → **Spec Flip Protocol** (`:90`). Forward Back L1 = "IaaS, PaaS, SaaS" = 3 comma-separated items, so the **Multi-Value Mirror Prohibition** (`:99–116`) fired. Verbatim target zone:

```
:99  * Multi-Value Mirror Prohibition: Before constructing Rev_Front via the Spec Flip,
       inspect Forward Back Line 1. If it contains three or more comma-separated items
       (a value list, not a single atomic value or port number), the standard format
       "[Value/Port] (Assigned [Concept])?" is FORBIDDEN — placing a multi-item list
       verbatim in Rev_Front triggers a guaranteed Sin 2 Mirror Glitch.
:100   Mandatory pivot: construct Rev_Front as a consequence-based query describing the
       operational situation that requires all items collectively, without naming any item.
:101   Format: "Which [protocol/system] requires all [N] of: [category description]?"
:102   Rev_Back is the PARENT CONCEPT NAME from Forward Front — NOT the value list. ...
:106   To identify the parent concept: it is the subject noun/acronym before the first parenthetical.
:108   Example — Mechanism list (Forward Back = "Confidentiality, Integrity, Authentication"):
:109     FORBIDDEN Rev_Front: "Confidentiality, integrity, and authentication (Pillars of which protocol)?"
:110     CORRECT   Rev_Front: "Which web protocol requires server identity proof, tamper detection, ...?"
:111     CORRECT   Rev_Back:  "HTTPS"
:113   Example — Category list (Forward Back = "Expired, Revoked, Self-Signed"):
:114     FORBIDDEN Rev_Front: "Expired, revoked, and self-signed (Categories for which browser event)?"
:115     CORRECT   Rev_Front: "Three distinct certificate failure states each trigger which browser ...?"
:116     CORRECT   Rev_Back:  "Certificate Warning (...)"
```

**The architect's preferred reverse is literally this rule's FORBIDDEN example pattern.** The rule bans the member-list as the cue and *mandates* the convoluted "consequence-based query → parent term," which is exactly the rejected umbrella card.

## 5. The internal contradiction (key design tension)

The card the Multi-Value Mirror Prohibition manufactures **fails Prompt 4's OWN North Star** (`:11`, `:15`):

> North Star FAIL **#2 — Embedded Operational Definition:** "The Front contains the operational definition of the Back, in enough detail that answering becomes vocabulary matching."

"The umbrella category for the tiers that split stack management between provider and customer" **is** the operational definition of "Cloud service models." Answering = vocabulary matching = recognition, which the North Star forbids (`:11`: "not recognize it from a definitional description").

So `prompt4_reverse.txt` contains a rule (`:99–116`) that produces cards its own constitution (`:11–24`) says must BULLDOZE. The Mode 2 audit missed it because the **7 Sins are lexical echo/duplicate checks** (the Rev_Front shares 0 words with the Forward Back, so anti-echo passed) — there is no non-lexical "is this a definitional-recognition card?" check in Mode 2.

## 6. Current threshold map (where the gate is and where the hole is)

Reverses are gated in 3 places today:
- **Zone 1 ABORT** (`:63–66`) — ~15 directional tags never reversed.
- **Zone 1B Exemption** (`:71`) — contrast cards abort if members already have standalone cards.
- **Zone 2** (`:82`, Identity/Spec/Mechanism/Command/Shortcut) — **NO Mode-1 eligibility gate. Every such card is force-reversed.** Only filter = Mode 2 Sins + North Star.

**The hole:** Zone 2 has no "should this be reversed at all / am I about to fabricate a definitional cue?" gate, and the Mode 2 filter is lexical, so a structurally-clean-but-pedagogically-hollow reverse ships.

## 7. Diagnosis — good vs. bad reverse (the discriminator)

Why the umbrella card is bad:
1. **Not a reverse — a new card.** True reverse swaps Q↔A. Forward = `[category] → [members]`; genuine inverse = `[members] → [category]`. The umbrella card keeps the category as the answer and *invents a fresh definitional question*, so the `members → category` direction is never tested.
2. **Cue is a definition → decoding, not retrieval** (North Star #2 failure, §5).
3. **Re-tests a handed term.** "Cloud service models" was the forward's *subject*; the reverse adds no new path to the hard content (the member names).
4. **Forced convolution.** The rule banned the clean list-cue, so the model manufactured obfuscated prose. That is the "gymnastics."

Why the architect's version is good: `IaaS, PaaS, SaaS → Cloud service models` uses the card's real content as the cue, tests the true inverse direction, needs no fabricated definition, forces recall not recognition. **General principle:** a good reverse swaps real atoms from the card and the cue forces retrieval; a reverse that requires *inventing* a definitional cue is a North Star #2 failure in disguise.

## 8. Scope notes (verified)

- **Reproducible, not runtime.** Live `Prompts/prompt4_reverse.txt` is **identical** to the 119 snapshot (both 318 lines; rule at `:99` byte-for-byte). Any "category → 3+ members" Spec card gets this treatment. Systemic.
- **P5 exonerated.** `forensic_raw_p5.txt:29` Rev_Front/Rev_Back == P4 Mode 2 output, modulo bold + image link. P5 is not a contributor.
- **Note the archetype split** the current rule does NOT make: (A) "category name → its member instances" (IaaS/PaaS/SaaS), where the member-list is a legitimate non-spoiling cue for the category; vs (B) "concept → its component properties" (HTTPS → C/I/A), where the rule's consequence-pivot was designed. The rule treats both identically.

## 9. Open design questions for Chat (resolve in design; not pre-answered here)

1. Is the fix to the Multi-Value Mirror Prohibition itself (it over-bans the legitimate list-cue), to add a Zone 2 eligibility gate, or both?
2. Should the rule fork on the §8 archetype split (A category→members vs B concept→components)?
3. How should any fix reconcile with North Star #2 — i.e., should it permit the clean `members → category` swap while still blocking genuine mirror glitches?
4. Does Mode 2 need a non-lexical check (definitional-recognition / North Star #2) since the lexical Sins missed this?
5. (Secondary, UNVERIFIED) Should `status=N/A` forwards be reverse-eligible at all? P4's own Pass-1 telemetry flags it reversed a `status=N/A` forward because "Mode 1 has no rule" on it. What `status=N/A` means in this pipeline is **not yet confirmed** — verify before relying on it.

---

## SCOUT ADDENDUM (2026-06-24) — Clone-bug history maps to Sin 2a, NOT the anti-echo GRAFT 2 targets

Architect supplied the original rationale for the anti-echo bans: a past failure (Gemini/DeepSeek) where the reverse CLONED the forward — same answer on both sides. Classic case: Fwd "What port is SSH? -> 22"; buggy reverse "Which port does SSH use? -> 22" (Rev_Back == Forward_Back; question reworded, direction NOT flipped). Genuine reverse = "Port 22 (Service)? -> SSH".

**File-verified mapping (live `prompt4_reverse.txt`):**
- **Sin 2a — Identity Glitch** (`:148-150`; Tier-1 `:207`): fires when `Rev_Back == Forward_Back`. THIS is the clone-bug catcher. Load-bearing, justified by the history, **must be PRESERVED untouched** by GRAFT 1/2.
- **Sin 2b — Mirror Check / Forward-Back Cross-Check** (`:150` MANDATORY QUOTA; `:201`): fires when `Rev_Front` shares >=3 consecutive words with Forward_Back. THIS is the over-broad ban that penalizes the fingerprint clean-swap (Rev_Front = the list). GRAFT 2's target.

**The discriminator: which SIDE the forward-answer lands on.**
- Forward-answer reused as Rev_FRONT (cue) = legitimate flip -> Sin 2b over-penalizes it (GRAFT 2 fixes).
- Forward-answer reused as Rev_BACK (answer) = clone bug -> Sin 2a correctly bans it (KEEP).
- GRAFT 1+2 touch only the Rev_Front side; the clone-bug ban (Rev_Back) is never weakened. Relaxing for fingerprints does NOT reintroduce the clone bug.

**Two nuances for red-team:**
1. The umbrella card is born in **Mode 1** (`:99` Multi-Value Mirror Prohibition), before Mode 2 runs. GRAFT 1 (Mode 1) is the real fix; GRAFT 2 (Mode 2) only prevents the new clean swap from being bulldozed.
2. Sin 2b **already** exempts "technical proper nouns / exam-standard identifiers" (`:150`, `:201`). IaaS/PaaS/SaaS plausibly qualify -> Sin 2b may NOT fire on that specific swap even today. RED-TEAM must check: (a) does the proper-noun exemption already cover proper-noun fingerprint lists (making GRAFT 2 partly redundant there, but still needed for COMMON-noun lists like OSI layer names)? (b) GRAFT 2's carve-out must be scoped to **Sin 2b ONLY** — it must not touch Sin 2a (Identity Glitch), or the clone bug returns.
