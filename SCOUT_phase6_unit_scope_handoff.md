# SCOUT HANDOFF → CHAT (Architect): Phase 6 Unit Auditor over-injects out-of-unit DEBT

**From:** Claude Code (Scout). **To:** Chat / Gemini (Architect — no file access).
**This is a design-ideation request, not an implementation order.**

> ⚠️ **This brief is the reasoning. The FILES listed at the bottom are the territory — paste them WHOLE into Chat alongside this brief.** Do not work from my excerpts; read the complete files.

---

## 0. What we want back from you

We have a reproducible design bug in the Unit Auditor (Phase 6). Root cause is confirmed with file evidence below. **Brainstorm the architecture — don't rubber-stamp a fix we picked.** Return:

1. **2–4 candidate architectures** for scoping the audit to the unit, each described *concretely* (what data flows where, what Python does vs. what the LLM does, what gets matched against what). Not "map it to a graph" — show the mechanism.
2. **A trade-off table** scoring each on **token economy**, accuracy/robustness, maintainability, elegance.
3. **A recommendation** with reasoning.
4. **Explicit handling of the three temporal cases** (§5): a Ref B point whose true "home" is a **past** video, a **future** video, or **genuinely ambiguous**.
5. **How REF A is checked** — efficiently *and* thoroughly. Not a shallow title substring match; not an O(150 videos × N bullets) brute-force dump into the LLM every run. Find the elegant middle.
6. **Division of labor:** which file changes (`prompt6_unit_auditor.txt`, `run_phase6.py`, or both) and why.
7. **Conceptual grafts** in plain English (no code). Claude Code red-teams and executes.

**Design values to honor:** Subtraction > Addition (we're *restoring* a discarded input — the net can still be subtractive in rule-count). No System Cosplay (don't force the LLM to hand-run an O(N²) matching table it will hallucinate — ask whether Python should pre-compute). Elegance is explicitly wanted. **Output schema is frozen** — emitted entries must stay byte-compatible with prompt1's Blue Zone (`<entry zone="BLUE" type="DEBT">`, `<reason>` opens with `[`, `<provisional_front>`/`<provisional_back>` last two children). The `certainty="HIGH|LOW"` attribute already exists — title-derived inference is probabilistic, so you may want to exploit it.

---

## 1. The bug in one paragraph

Phase 6 ("The Unit Auditor") is a unit-END sweep: after every video in a *unit* has been carded, it compares the unit's cards against CompTIA exam objectives (Ref B) and emits one `DEBT` entry per missed exam fact, feeding the normal P2→P3→P4→P5 pipeline. It scopes the audit by "which Ref B **section IDs** appear in the cards' Tags." But a **unit is a video range** while a **Ref B section is an exam objective that spans many videos across many units** — so one narrow laptop card tagged `3.3` (cooling fan) or `1.2` (display connector) drags in the *entire* desktop-motherboard / monitor-technology objective, including material taught in **past** videos and **future** videos. The syllabus that would fix this (**REF A**, with per-unit video boundaries) exists in the same reference file but is **sliced off by `run_phase6.py` before the LLM ever sees it.** Result: 167 DEBT entries, output truncated mid-emit.

The unit under audit: **Unit 2 = videos 122–127** — a *laptop hardware* unit (Laptop Features / HW Tools / Core Hardware / CPU & Motherboard / Touring Your Laptop Display / Power Management).

**What we want instead of "audit every sub-bullet of every tagged section":**
```
DEBT = (Ref B points whose teaching HOME falls inside this unit's video window)
       MINUS (points already covered by this unit's cards)
```

---

## 2. Root cause — three reinforcing defects

1. **REF A is amputated before the LLM sees it.** `run_phase6.py` step 4 does `ref_b_idx = ref_full.find("**[REF B:")` then `reference_library = ref_full[ref_b_idx:]` — discarding all of REF A (the syllabus, with `UNIT_START`/`UNIT_END` markers) that sits above REF B in the same file. The auditor only ever receives REF B. (The manual copy-paste path has the identical amputation.)
2. **Scope keyed to the wrong axis.** `prompt6_unit_auditor.txt` line 6: *"You audit ONLY Ref B sections whose ID appears in the unit's card Tags column."* Section-ID granularity → one narrow card inherits a whole objective.
3. **Two mandates push toward maximal injection.** Line 24 *Anti-Laziness Gate*: "You MUST enumerate ALL sub-bullets … examining only one is a critical failure." Lines 21–23 *coverage gate*: "When uncertain, default to UNCOVERED — duplicate cards are preferable to missed exam facts." No counterweight for "this belongs to another unit."

---

## 3. The temporal proof (the key evidence to design around)

Cross-referencing the over-injected clusters against REF A's video titles shows their true "home" lessons sit *outside* unit 2 — both behind it and ahead of it. (These home assignments are **my title-derived inferences at partial certainty** — illustrative of the method, not authoritative; the uncertainty is exactly the design challenge.)

| Over-injected cluster (from the bad run) | Ref B § | Plausible "home" in REF A (by title) | vs. unit 2 (122–127) |
|---|---|---|---|
| IPS / TN / VA / OLED / Mini-LED / digitizer / inverter | 1.2 | 60 Monitor Technologies, 61 LCD Breakdown, 66 Troubleshooting Display | **PAST** |
| ATX/ITX / PCIe / BIOS/UEFI / TPM / HSM / CPU-arch / VRAM / NIC | 3.3 | 12–18 CPU, 24 BIOS & UEFI, 25 POST, 28 Form Factors, 30–31 Motherboard, 54 Expansion Cards | **PAST** |
| S.M.A.R.T. / mSATA / SSD form factors | 1.1 | 36 Intro to Mass Storage, 38 Solid State Drive, 45 Mass Storage Troubleshooting | **PAST** |
| USB-C / Lightning | 1.3 | 46–49 USB Standards / Thunder and Lightning | **PAST** |
| NFC / Bluetooth / stylus / SIM / eSIM | 1.3 | 128–135 Mobile Devices unit | **FUTURE** |
| Cellular / hotspot / MDM / sync / GPS troubleshooting | 1.4 | 129 Mobile Connections, 133–138 Mobile Devices unit | **FUTURE** |
| Batteries / biometrics / liquid damage | 1.1 | 133 Maintaining Mobile Devices, 136 Mobile Device Security | **FUTURE (ambiguous — see §4)** |

The auditor injected both **already-covered** (past) and **not-yet-covered** (future) content into a laptop unit. REF A pins every home down by title — and the auditor never got to see REF A.

**Classification:** reproducible design bug. The truncation / "max message" is only a *symptom* of being asked for 167 entries — re-running or raising max-tokens would just emit all 167 wrong entries intact. Don't treat the truncation as the problem.

---

## 4. The design problem to brainstorm

Introduce a **subtraction based on "home":** every Ref B sub-bullet has a *primary home* — the video whose title most plausibly teaches it. A unit owns a Ref B point **only if that point's home falls inside the unit's video window** (122–127). Points homed in past videos were another unit's job (already covered); points homed in future videos are a later unit's job (will be covered). Both are subtracted.

Three cases your design must handle:
- **PAST home (high confidence):** `[IPS Display :: Performance Characteristics]` → video 60. Exclude.
- **FUTURE home (high confidence):** `[eSIM :: Form Factor Definition]` → Mobile Devices unit (128–135). Exclude.
- **AMBIGUOUS home (the hard one):** `[Mobile Battery Health :: …]` — laptop batteries could be video 124 "Core Hardware"; *mobile* battery maintenance is video 133. Ref B labels say "Mobile," nudging future — but we can't be sure. **We derive home from video TITLES only — no transcripts — so every assignment is probabilistic.** Policy? (Inject at `certainty="LOW"` for human veto? Suppress? A confidence threshold? This trades against the "duplicates preferable to missed facts" ethos — name the trade-off and pick.)

**Crux question:** *How do we assign each candidate Ref B point a home (or home-confidence) from syllabus titles — efficiently and thoroughly — and turn that into a clean subtraction, without a brittle hand-matching pass and without blowing the token budget?*

**Seed directions (non-exhaustive — critique these AND generate better ones):**
- **Seed 1 — LLM inline, windowed input.** Feed the LLM REF A (~153 short title lines, cheap) + only the *tagged* Ref B sections; for each candidate sub-bullet it names the most-likely home video and keeps it only if in [122,127]. *Reliable, or a hallucination trap?*
- **Seed 2 — Python pre-computes a static `bullet → home_video` map** (offline, possibly LLM-assisted once, then frozen as data). Runtime Python filters Ref B to the unit window *before* the LLM runs; the LLM only does coverage-matching on an already-scoped shortlist. *Maintenance cost vs. runtime cheapness/robustness?*
- **Seed 3 — Neighbor heuristic off the unit's own card concepts.** The cards' fine-grained tag concepts (`ACPI_POWER_STATES`, `DISPLAY_ASSEMBLY`) are a better scope seed than the coarse section ID; audit only Ref B points semantically adjacent to what the unit actually carded. *Does it under-cover genuine total-omission gaps?*
- **Seed 4 — Explicit exclusion list via unit markers.** Hand the auditor the current unit's REF A slice (6 titles) plus a cumulative "ALREADY COVERED / COVERED LATER — DO NOT INJECT" list built from prior+future titles. *Cheaper/safer than per-bullet home-assignment?*

Combine, discard, or invent. We care most that the **principle** is right and the **token cost per run** is sane.

---

## 5. Card-inventory notes (the tag mess any design must survive)

Unit 2's 32 cards carry narrowly-laptop concepts but broad section IDs — and the tagging is inconsistent:
- Section-ID format varies: `::1.1::` vs `::Domain_1.1::`.
- Card 10 has an **empty** tag entirely (coverage still counts from its Back).
- Some tags carry trailing secondary domains (`::Domain_5.2`, `::Domain_5.5`) — secondary subjects, not the card's primary section.
- The collision that caused the blow-up: cards #19/#20 (display *connector/assembly*, video 126) tag `1.2`; cards #13/#14/#17 (cooling fan, ZIF socket, video 125) tag `3.3`. Two narrow cards each inherited a huge objective.

Unit 2's *real* footprint is small and coherent: laptop physical security & docking, tools, core hardware (RAM/storage/wireless/charging), laptop CPU/mobo (cooling fan/ZIF/soldered CPU), laptop display assembly, power connector + ACPI. Nothing like 167 facts.

---

## 6. The model knew — it was overruled by its own rules (monologue evidence)

Not laziness or hallucination — the execution trace shows the model flagging the absurdity ~5× and being forced onward:
- It correctly **excluded** secondary tags 5.2/5.5: *"…auditing massive troubleshooting domains against a unit that only touched them tangentially in single cards, which would generate an unreasonable flood of 'UNCOVERED' findings."* — it named the failure mode, but only had permission to skip *secondary* tags, not *primary* tagged sections.
- *"the unit covers the lecturer's specific talking points rather than the full reference objectives … almost entirely separate."*
- *"I'm wrestling with whether 168 entries is genuinely necessary or if I should push back … The scope rule is clear … I'll proceed with the full execution rather than second-guessing the system the user built."*

A good fix gives that correct instinct a *sanctioned, mechanical* basis (the syllabus) instead of forcing the model to override it.

---

## 7. PASTE THESE WHOLE FILES TO CHAT (do not let me hand you excerpts)

1. **`Prompts/prompt6_unit_auditor.txt`** — the auditor prompt to redesign. Key spots: **line 6** (Exhaustion scope rule), **lines 21–23** (injection-biased coverage gate), **line 24** (Anti-Laziness Gate), the SCHEMA MANDATE + OUTPUT FORMAT blocks.
2. **`Prompts/prompt1_harvester.txt`** — the schema parent. Phase 6's output must stay byte-compatible with prompt1's Blue Zone entries, and Phase 6 was carved out of prompt1 (2026-06-12). Chat needs the whole file to judge the schema contract and shared DNA.
3. **`run_phase6.py`** — the orchestrator. Key spot: **step 4**, `ref_full.find("**[REF B:")` slice that discards REF A. It already holds the unit-window integers (`unit_start_video`, `boundary_video`) and REF A's markers are parsed elsewhere (`run_master._check_unit_boundary`) — the raw materials for the fix are already in hand.
4. **`Prompts/reference_library_p1.xml`** — contains **BOTH** `**[REF A: COURSE SYLLABUS MAP]**` (the 153-video list; unit boundaries around lines 117–161; unit 2 = videos 122–127) **and** `**[REF B: MASTER KNOWLEDGE GRAPH]**` (the exam-objective graph the cards tag against). **This is the single most important file** — REF A is what the fix must feed the auditor.

*(Why whole files, not my excerpts: Chat designs best with full context, and curated excerpts risk omitting something load-bearing — I don't know what I don't know.)*
