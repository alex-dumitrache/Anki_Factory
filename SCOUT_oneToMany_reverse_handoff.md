# Chat Handoff — Abolish the "One-to-Many / Guess-What-I'm-Thinking" REVERSE card (Prompt 4 & Prompt 5)

> **Purpose:** forensic packet for the DESIGN chat. Your job (Chat): design the graft(s). This file is self-contained — every claim is file-verified against the LIVE main-folder prompts (not Archive snapshots).
> **Attach to the design chat alongside this file:** `Prompts/prompt4_reverse.txt` (FULL) and `Prompts/prompt5_exporter.txt` (FULL). Both are in scope because *which gate to fix* is the open design question.
> **Optional context:** `SCOUT_reverse_threshold_handoff.md` (adjacent June-24 work on a DIFFERENT reverse sin — do not collide with it).
> Produced by Claude Code (scout phase). Claude Code does not design or red-team prompt text; it will reconcile your grafts, run red-team file-access checks, and operate the Surgeon.

---

## 0. The Sin, in one sentence

A reverse card whose **cue (Rev_Front) is a generic property that many entities share**, paired with a generic identify-the-entity anchor ("Which laptop part?", "Name it"), so the answer is not retrievable by knowledge — the student must **guess which specific entity the author had in mind**. This is the inverse of a spoiler: not too *revealing*, too *under-determined*.

The Architect's position: these are **inevitable** — you cannot force the generator to keep bolting on constraints until every reverse is unique. Some reverses simply should not exist. The pipeline needs a way to **detect and delete** an under-determined reverse (drop to N/A) rather than ship it or endlessly renovate it.

---

## 1. The failure card (real output, video 126 — live)

Forward (accepted as good by the Architect):
- **Front:** "Laptop charging circuit repair (Real obstacle)?"
- **Back:** "Physical access"

Reverse (the card the Architect rejects as a guess-what-I'm-thinking Sin):
- **Rev_Front:** "Physical access, not technical skill, is what makes this repair a hassle (Which laptop part)?"
- **Rev_Back:** "Laptop charging circuit"

**Why it is a Sin:** "hard to physically access" is true of many laptop parts (CPU, display assembly, motherboard, keyboard, battery in sealed units…). The card is answerable only by recalling *this lecture's* framing. Its own batch proves the collision:
- The sibling CPU card's NOT-field literally reads: *"Don't confuse this with the CPU upgrade question — charging circuit repairs are doable, just inconvenient to reach."*
- The sibling display card ("whole-unit swap when it cracks → Laptop display") is also an access/serviceability property.

Three cards in one batch keyed off overlapping "serviceability" properties; only one owns the generic "physical access" cue by author fiat.

## 2. Goal

Give the pipeline a **uniqueness gate for reverse cards**: when a Rev_Front cue does not point to exactly one answer (enough context / nuance / constraint that the answer is forced), **delete the reverse** (Rev_Front = Rev_Back = "N/A") rather than ship it. A one-directional card is explicitly legal (P5 `:74` "Respect N/A Reverse Fields"). Not every card earns a reverse.

*(The Architect floated a cheap external API pass that flips each reverse to forward and tests whether the cue forces a unique answer. That is a Phase-2 design option, noted here as intent, NOT designed in this scout packet.)*

## 3. Pipeline trace (origin → final) — where the Sin passes each gate untouched

| Stage | Evidence (LIVE, video 126) | What happened |
|---|---|---|
| P4 Mode 1 (draft) | Rev born with consequence-based framing "Physical access… (Which laptop part)?" | Generated the under-determined cue. |
| **P4 Mode 2 Tier 1** | `forensic_raw_p4_pass2.txt:11` | Row: `\| 3 \| 2 (PROCEED — Spec) \| PASS \| PASS (2w "Physical access" below 3w quota) \| PROTECT ← \| PROTECT \|`. Routed **PROTECT** → BULLDOZE permanently blocked. |
| **P4 Mode 2 Tier 2** | `prompt4_reverse.txt:259` | "Sins 1 and 2a are **resolved in Tier 1 — omit here**." Sin 1 never re-evaluated. |
| **P5 Sentinel (Mode 1)** | `prompt5_exporter.txt:56-105` | No metric matches an under-determined cue; Contextual Self-Sufficiency Safe Harbor exempts "(Which laptop part)?". No flag. |
| **P5 Surgeon (Mode 2)** | `ANKI_IMPORT_READY.txt` | Cosmetic only (bold + image link). Semantics unchanged → shipped. |

## 4. ROOT CAUSE A — P4 owns a 1-to-many check that is never actually run

P4 **does** have the concept. `prompt4_reverse.txt:158-160`:

```
1. Sin 1: The Asymmetry & Collision Violation: Did Mode 1 reverse a tag that belongs
   in Zone 1 (Redaction)? Or did Mode 1 create a 1-to-many guess?
   * The Flaw: Mode 1 reversed a `Diagnosis` block, OR Mode 1 asked "288 pins
     (Assigned component)?" without specifying the generation. Both create invalid
     1-to-many guessing games.
   * The Fix: BULLDOZE TO N/A. (Exception: RENOVATE a Spec Collision ONLY if an
     exam-critical discriminator natively exists to save it).
```

Three compounding defects make this rule inert:

**(A1) The only worked example is a NUMERIC spec ("288 pins").** The auditor is primed to hunt numeric/port collisions. A *semantic-property* collision ("physical access → which part") does not match the pattern. There is no semantic-collision exemplar anywhere in the Sin catalog.

**(A2) Sin 1's collision-half has NO evaluation slot in either tier.**
- Tier 1 mandate `:221`: *"evaluate only: Sin 1 (Zone routing), Sin 2a, Sin 2b, and Fix 4-D."* — Sin 1 is **redefined as "Zone routing"** (did Mode 1 reverse a Zone-1 tag?). The 1-to-many half is dropped.
- Tier 1 table columns `:227`: `ID | Zone | Sin 2a | Sin 2b | 4-D | Verdict` — **no collision column exists.**
- Tier 2 per-card ledger `:259`: *"Sins 1 and 2a are resolved in Tier 1 — omit here. Evaluate sins 2b through 7."* — Tier 2 explicitly **skips Sin 1**, trusting Tier 1.

Net: Tier 2 believes Tier 1 resolved Sin 1; Tier 1 only ever resolved the Zone-routing half. **The 1-to-many collision check falls through the crack between the two tiers and is computed nowhere.**

**(A3) PROTECT makes the card BULLDOZE-immune even if Sin 1 fired.** The card earned PROTECT (Fix 4-D Consequence-Format Exemption) at `forensic_raw_p4_pass2.txt:11`. Verdict code `:235`: *"PROTECT … proceeds to Tier 2 RENOVATE-only; BULLDOZE permanently blocked for all sins."* Reinforced at `:263`. **The consequence-based framing that PROTECT rewards is the exact mechanism that generates the generic under-determined cue** — the shield protects the disease.

## 5. ROOT CAUSE B — P5's Sentinel is structurally blind to under-determination

Full metric catalog read (`prompt5_exporter.txt:56-105`). Every cue-quality metric hunts the **opposite** defect — a cue that is *too revealing*:
- **Spoiler Leak — Semantic** (`:58`, `:82`): Front describes the Back's mechanism/definition → too easy.
- **Subject Anchoring** (`:60`, `:102`): Front names the Subject → recognition not recall.
- **Tautology / Mirror Glitch** (`:57`, `:83-84`): Rev echoes/duplicates the forward answer.

The one-to-many card is too **hard/ambiguous**, so none of these fire.

The single ambiguity metric — **Contextual Self-Sufficiency Sweep** (`:101`) — asks whether the Front *"could belong to two or more unrelated technology clusters"* (cross-**domain** ambiguity). Its **Safe Harbor** explicitly passes any Front whose anchor *"names a specific technology cluster"* — **"(Which laptop part)?" names the cluster, so it is exempted.** It never asks the within-domain question: *given the correct domain, does this cue force one answer or many?*

**There is no P5 metric for within-domain cue under-determination.** The Architect's hunch that "P5 hunts for the Sentinel [and should catch this]" is not borne out.

## 6. Current gate map (where reverses are filtered, and where the hole is)

| Gate | Location | What it catches | This Sin? |
|---|---|---|---|
| Zone 1 ABORT | P4 `:63-66` (per prior scout) | ~15 directional tags never reversed | ✗ (charging card is Zone 2 Spec) |
| Sin 1 (Zone-routing half) | P4 `:221` Tier 1 | Reversed a Zone-1 tag | ✗ (routed Zone 2 PROCEED) |
| Sin 1 (collision half) | P4 `:158-159` prose only | 1-to-many guess | **✗ evaluated in neither tier** |
| Sin 2a/2b, 3, 4, 5, 6, 7 | P4 Tier 1/2 | echoes, mirrors, spoilers, bloat, dupes | ✗ (opposite defects) |
| PROTECT | P4 `:235` | — | **shields it (BULLDOZE-immune)** |
| Sentinel cue metrics | P5 `:57-104` | too-revealing cues | ✗ (opposite defect) |
| Contextual Self-Sufficiency | P5 `:101` | cross-domain ambiguity | ✗ (Safe Harbor exempts cluster anchor) |

**The hole:** no gate asks "does this reverse cue point to exactly one answer?" The nearest hooks are (a) P4 Sin 1's dormant collision clause and (b) P5's Contextual Self-Sufficiency Sweep, which is scoped to the wrong axis (cross-domain, not within-domain uniqueness).

## 7. The discriminator (good reverse vs. Sin) — for design calibration

A generic identify-the-entity anchor ("Which X?", "Name it") is **necessary but not sufficient** for the Sin. The test is on the BODY:
- **GOOD (self-identifying fingerprint):** the cue property is possessed by exactly one entity. "FTP mode silently dropped by stateful routers because the data channel arrives as an unrequested inbound packet (Name)?" → **FTP Active Mode.** Only one mode fits.
- **SIN (under-determined property):** the cue property is shared by many entities in the domain. "Physical access is what makes this repair a hassle (Which laptop part)?" → charging circuit — but CPU/display/motherboard also fit.

The uniqueness/blind-answer test (mask the forward, does the cue alone force exactly one answer?) is the semantic judgment **the pipeline never performs** on reverse cues.

## 8. Scope notes (verified)

- **Reproducible prompt-logic gap (type a), not runtime.** The hole is structural in the live prompts; same input → same miss.
- **Distinct from the June-24 reverse-threshold work.** `SCOUT_reverse_threshold_handoff.md` targeted North Star #2 (Front *embeds the definition* → too EASY, recognition). This Sin is the inverse (Front is a *generic property* → too HARD, guess). The earlier grafts do not touch it; a fix here must not re-open that one.
- **N/A reverses are already first-class.** P5 `:74` "Respect N/A Reverse Fields" — deleting a reverse to N/A is an existing, supported outcome, not a new mechanism.

## 9. PREVALENCE (Archive: 17 runs + live, every `ANKI_IMPORT_READY.txt`)

Extractor: `scratchpad/extract_reverses.py`; raw: `scratchpad/reverses_out.txt`.

- **232 cards total; 160 carry a reverse** (Rev_Front & Rev_Back both present).
- **51 / 160 (32%)** use a generic "which/what/name" identify-the-entity anchor.
- **Most of the 51 are legitimate unique fingerprints** (FTP active/passive by NAT behavior, IMAP folder-sync, certificate revocation, bounded 2-way hypervisor Type 1/2). The generic *structure* is common; genuine under-determination is **sparse**.

**Genuinely under-determined instances found (the actual Sin):**

Clear:
- `[126/live] "Physical access, not technical skill, is what makes this repair a hassle (Which laptop part)?" → Laptop charging circuit` (the reported card).
- `[115] "Bandwidth ceiling matched exactly to the actual command payload (Which IoT wireless protocol)?" → Zigbee` (Z-Wave / BLE are also low-bandwidth IoT).

Borderline (weak / negative / generic cue, plausibly one-to-many):
- `[112] "Internet appliances that overlap on performance improvement, access control, and security enforcement… (Name the pair)?" → Proxy Server; Load Balancer` (generic property + multi-answer + "name the pair" is also multi-fact/ungradeable).
- `[122] "Which laptop expansion device can't deliver desktop-grade screen output or integrated power through a single cable (Name)?" → Port Replicator` (negative framing; docking-station confusion).
- `[117] "The physical host resource that fills up first as you add VMs and sets the ceiling on concurrent VM count (Which resource)?" → RAM` (RAM vs CPU cores).
- `[126/live] "Board-mounted with no socket, unlike RAM or storage (Which laptop part)?" → Laptop CPU` (mild; the "unlike RAM or storage" contrast partly rescues it).

**Read on prevalence:** ~2 clear + ~4 borderline out of 160 reverses. The Sin is **real but not epidemic** — it slips through individually, one card at a time. A fix should be a targeted uniqueness gate, not a heavy rewrite of the reverse engine. (Anti-Addition-Bias note for the Architect: do not over-fit to a rare failure.)

## 10. Open design questions for Chat (resolve in design; NOT pre-answered here)

1. **Which gate?** Revive P4 Sin 1's collision half (give it a Tier-1/Tier-2 evaluation slot), add a new P5 Sentinel metric, add an external uniqueness API pass, or a combination? Trace evidence supports any of the three internal locations plus the external option.
2. **PROTECT interaction.** If the fix lives in P4, how does it pierce PROTECT immunity (`:235`, `:263`) without reintroducing the Mirror-Glitch that PROTECT exists to prevent? Should "under-determined cue" be a BULLDOZE trigger that PROTECT cannot shield (a carve-out), given PROTECT's framing is what *creates* the Sin?
3. **Detection mechanism.** Is the uniqueness test doable as an in-prompt "blind re-identification" self-check (mask forward, does the cue force one answer?), or does it genuinely need the external flip-to-forward API pass the Architect proposed (LLM self-assessment of ambiguity is unreliable)?
4. **Delete vs. rescue threshold.** Sin 1 currently allows RENOVATE "ONLY if an exam-critical discriminator natively exists" (`:160`). Keep that escape hatch, or make under-determination a hard delete-to-N/A? The Architect's stance leans delete: stop forcing uniqueness by piling on constraints.
5. **Placement timing.** After P4 Mode 2 (generator-adjacent, kills it before export) or after the Sentinel (final safety net)? Both gates are evidenced as viable; pick per false-positive tolerance and token cost.
6. **False-positive guard.** 32% of reverses use the generic anchor but most are legitimate fingerprints. Any gate MUST pass the fingerprint cases (§7 GOOD example) and fire only on genuine under-determination (§7 SIN example). What is the operational discriminator the LLM/API applies?

---

*Scout artifacts: `SCOUT_oneToMany_reverse_handoff.md` (this file), `scratchpad/extract_reverses.py`, `scratchpad/reverses_out.txt`. All prompt-state claims verified against live `Prompts/prompt4_reverse.txt` and `Prompts/prompt5_exporter.txt` this session.*
