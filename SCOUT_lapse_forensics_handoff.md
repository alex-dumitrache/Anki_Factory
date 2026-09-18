# SCOUT HANDOFF → CHAT (Architect): the `Notes` routing sink, the P3 Tags contradiction, and the lapse-feedback loop

**From:** Claude Code (Scout). **To:** Chat / Gemini (Architect — no file access).
**Date:** 2026-07-28. **This is a design-ideation request, not an implementation order.**

> ⚠️ **This brief is the reasoning. The FILES listed in §8 are the territory — paste them WHOLE into Chat alongside this brief.** Do not work from my excerpts; read the complete files.

> 📌 **Durability note:** this file sits at repo root, which `.gitignore` line 2 (`*`) excludes. It is **not tracked**. If it should survive disk loss, it needs a whitelist entry or its findings folded into `CHANGELOG.md`. Chief Architect's call.

---

## 0. What we want back from you

Two confirmed prompt-layer defects plus one architectural question. **Brainstorm — don't rubber-stamp.** Return:

1. **2–4 candidate architectures** for GRAFT A (recovering the `Notes` payload), each concrete: what data flows where, what Python does vs. what the LLM does. One option must be the **Python-side siphon at export** (no prompt change at all); at least one must be a **P3 routing change**. Score them.
2. **A verdict on GRAFT B** — the P3 Tags self-contradiction (§3). This one may be a two-line fix; say so if it is.
3. **Explicit handling of the three siphon hazards** in §2.4 (fuzzy join key, duplication against the 35 matrices that already land, 17-blocks→6-distinct-matrices repetition).
4. **A position on §5** — whether the pipeline should generate *disambiguation* cards for confusable pairs, given that the ⚖️ Compare archetype is empirically our best performer.
5. **🚩 A downstream-interception audit — the Chief Architect's central question.** Recovering the payload is only half the problem. *Does the infrastructure exist to carry it without dropping it again?* Specifically: if a matrix is reintroduced and made mandatory, how does **P3** route it, how does **P4** treat it when generating reverses, and how does **P5** handle it during BULLDOZE/MERGE/SHAVE? Every one of those stages can silently discard a field it has no rule for — which is exactly how we got here. Answer this per-stage, not in general.
6. **🚩 A token-budget verdict.** The Chief Architect's explicit constraint: *"the more we add through this pipeline, the more we run the risk of hitting token limits… that's why certain things are handled by the Python script."* Reintroducing 228 matrices into LLM-visible context is a real budget cost, and there is prior art in this project for output-budget truncation. **Say which stages must stay Python-side for this reason.** This is a strong argument for the export-time siphon over a prompt-side reintroduction — argue it either way, but argue it.
7. **A worth-it verdict.** *"If it's even worth it."* Do not assume recovery is correct. The counter-case: 15% of matrices already land, the deck's mature again-rate is 12.4%, and §5 shows the recovered content would not have prevented the flagship failure. Make the case for or against on evidence.
8. **Conceptual grafts** in plain English (no code). Claude Code red-teams and executes.

**Design values:** Subtraction > Addition. No System Cosplay. **Token economy is a hard constraint, not a preference.** **Output schema is frozen** — anything emitted must stay byte-compatible with existing baton formats.

---

## 1. Executive summary

The pipeline generates relational content correctly and then loses most of it at one handoff. Separately, a self-contradiction in P3 has been flagged by the model itself **19 times across 13 runs** and never fixed. A third finding — the user's Anki review database — turns out to be a usable ground-truth QA signal that nobody was reading.

| Finding | Evidence | Status |
|---|---|---|
| 193 of 228 comparison matrices lost in the `Notes` field (15% delivery) | measured across 22 archived runs, payload-exact | **confirmed** |
| P3 Tags "purge periods" rule contradicts its own reference example | 19 occurrences under 13 distinct video headers | **confirmed** |
| Contextual archetypes beat bare-recall archetypes | 522 notes / 5,369 reviews, holds under maturity control | **confirmed** |
| Run 134 TLS/SSL collapse is run-specific, not a knowledge gap | 17–22% in prior batches → 56–64% in run 134 | **confirmed** |
| Phase 6 Unit Auditor: 3 runs in 2 months, last output 100% vetoed | `unit_sweep_*` artifacts | **confirmed** |

---

## 2. GRAFT A — the `Notes` sink

### 2.1 The mechanism

P2 does genuine relational work. For nearly every block it builds a `📊 Matrix` comparing sibling concepts — exactly the side-by-side map the Chief Architect has been asking for. It writes that matrix into the `Notes:` field.

`Notes` has **no outbound route to any card field** except one narrow case. `prompt3_formulator.txt:346–370` (BIFURCATED DATA ROUTING) enumerates every source field P3 reads:

- **Zone A (Back):** `Reasoning_Anchor`→`Logic:`, `Delta_Logic`→`Delta:`, `User_Anchor`→`Analogy:`
- **Zone B (Extra):** `⚠️ NOT:`, `🪝 Hook:`, `Relates to:`, `Example:`, `Forensic:`, `👁️ Visual:`

`Notes` appears in neither list. The **only** rule that reads it is `prompt3_formulator.txt:385` — *"The `📊 Matrix:` listing all four values routes to Extra on every card"* — which sits under `:377`, the **DEBT ATOMICITY OVERRIDE**, scoped to `Contrast_Metric` blocks whose `Source_Type` is `DEBT`.

**Every matrix on a block with any other label has no path and is never evaluated.** Not rejected — never read. `prompt2_draftsman.txt:511` compounds it by defining `Notes` as *"TUTOR SCAFFOLDING … Not explicitly tested."*

Corroboration: P3's own forensic ledgers reason in detail about the S/MIME blocks (`forensic_raw_p3_pass1_chunk1.txt:13,14,16`) and **never once mention `Notes` or its contents.** No drop was weighed and rejected.

### 2.2 Scale (measured format-agnostically — see §2.3)

| | Count |
|---|---|
| `Notes` fields across 22 archived runs | 311 |
| carrying a `📊 Matrix` payload | **228** |
| matrices reaching finished decks | **35** |
| **delivery rate** | **15%** |

Survival is *intermittent*, not zero — runs 107, 109, 110, 111, 115, 116, 118, 119, 121, 124, 129, 131 landed some; runs 106, 112, 113, 117, 122, 133, 134, 135 landed none. Consistent with the DEBT/`Contrast_Metric` gating above.

**Other payloads in the same field die too:** Terminology Bridge 3→0, PDU alignment 3→0, Sibling Echo Matrix 7→0, ASCII Map 15→1. ⚠️ Those source counts are so low that this may be *conditional* behaviour rather than non-compliance — `prompt2_draftsman.txt:494` calls them "MANDATORY" but may mean "when applicable." **Unresolved; worth a reading of that section's full context.**

### 2.3 🚩 The baton format is not stable — any parser must handle both

Blocks serialize two ways, and the difference is markdown bold only:

```
run 134:   **Notes:** 📊 Matrix: MIME (binary→ASCII…) | S/MIME (adds cert-based sign/encrypt)
run 133:     Notes:   📊 Matrix: CDMA (No SIM card; carrier-side activation) | GSM (Uses SIM card)
```

**Run 135 mixes both styles inside a single file** (7 bold, 9 plain). A parser written against run 134 alone silently returns nothing for seven runs and half of another. *(This bit me during the scout — my first measurement reported "7 runs emit zero Notes," which was a regex artifact.)*

### 2.4 Hazards any siphon design must address

1. **The join key is fuzzy.** P2 blocks carry **no ID** — IDs are first minted at P3. The only join is `Target_Concept` (P2) ↔ the concept in `Meta:` (P3 `polished_yaml.txt`). But P3 *expands* names: P2's `S/MIME` becomes three P3 concepts (`S/MIME`, `S/MIME — Underlying Mechanism (Public Key Certificates)`, `S/MIME — Why It Encrypted Attachments Only`). Exact-string join fails; prefix matching works but isn't free.
2. **P3 remaps and merges.** Its own logs show `[ID15/16]` (merge) and `[ID18, orig block17]` under a *"Sequential Buffer Mandate forces highest ID regardless of source position."* Positional mapping is unsafe.
3. **Duplication is real.** 35 matrices already reach decks via the DEBT path. A blind siphon doubles them in exactly those runs.
4. **Repetition.** Run 134: 17 matrix-bearing blocks carry only **6 distinct matrices**. Attaching per-block puts the same map on many cards. Deduping means deciding which card owns the map — a design question.

---

## 3. GRAFT B — the P3 Tags self-contradiction (flagged 19×, never fixed)

`prompt_telemetry_database.txt` holds **590 model-authored issue reports** spanning 2026-05-14 → 2026-07-27, videos 110–135. **Nobody has read it.** The single most-repeated entry:

> **[P3]** *"The Tags 'purge periods' rule directly contradicts the reference example, which keeps periods intact (e.g., `Domain_3.0`) — I followed the explicit rule and stripped them, but **the conflict forced a guess**."*

Verified against the raw file: appears under video headers **116, 117×2, 118, 119, 122, 124×2, 126, 127, 129, 131×3, 133, 134, 135** — **13 distinct runs, 19 occurrences.**

**Why this is load-bearing beyond tidiness:** tags are the natural join key for any cross-run clustering (including GRAFT A's fallback and the lapse skill in §6). If period-stripping is a per-run coin-flip, tag-based joins are unreliable across runs.

**Telemetry health, incidentally:** issue volume is *not* declining — 14 (v110) → 90 (v131) → 26/27/29 (v133–135). By phase: P2 160, P3 136, P5 107, P4 100, P1 87. The file also contains 71 duplicate lines and leaked raw payload (`<final_logic_package>`, `[[LOGIC_BLOCK]]`).

---

## 4. The evidence base: the Anki collection as ground truth

Read-only analysis of `collection.anki2` (3,217 notes / 3,993 cards / 78,679 reviews).

**🚩 Methodological warning for anyone building on this:** the `cards.lapses` column **massively undercounts**. It only increments on *review*-stage failures. Run 134's worst cards show `lapses=0..1` while carrying 8–11 "Again" presses. **The correct signal is `revlog.ease = 1`.** A query filtering on `lapses > 0` reports a healthy deck.

### 4.1 Run 134 is a genuine outlier

Age-normalised (first 7 days after import), 16 batches since June:

| Import | Notes | Reviews | Again-rate |
|---|---|---|---|
| 2026-07-20 (run 133) | 22 | 150 | 36.0% |
| **2026-07-26 (run 134)** | 18 | 110 | **59.1%** |
| *mean excluding 134* | | | **30.6%** |

Run 134 = 0.56% of the collection and produced **62.5% of all "Again" presses that week.**

### 4.2 Archetype performance — controlled for card maturity

Emoji prefixes are assigned by `prompt5_exporter.txt` (verified verbatim: 📌 Spec, 🏷️ Acronym, 🔤 Define *(the DEFAULT/fallback)*, ⌨️ Command, 📋 Sequence, 🛠️ Tool, ⚖️ Compare, 🔍 Diagnose, 🚨 Risk).

| Archetype | All-study % | **Mature only %** | vs mature base | Mature n |
|---|---|---|---|---|
| 🏷️ Expansion (acronym) | 34.3% | **15.2%** | **+2.8** | 257 |
| 🔤 Define *(default bucket)* | 26.2% | 12.3% | −0.0 | 802 |
| 📌 Spec | 26.3% | 12.3% | −0.1 | 759 |
| ⚖️ **Compare** | 21.1% | **9.0%** | **−3.3** | 166 |
| 🔍 **Diagnose** | 13.9% | **8.3%** | **−4.1** | 181 |
| 📋 Sequence | 12.9% | 7.3% | −5.1 | 41 |

Baseline: 26.1% all-study → **12.4% mature-only.**

**The durable claim is the ORDERING, not the magnitudes.** Contextual/relational archetypes (Compare, Diagnose, Sequence) outperform; bare acronym expansion underperforms. ⚠️ An earlier uncontrolled version of this table put Expansion at **+8.2**; roughly two-thirds of that was card-age confound.

### 4.3 Repeat-offender discrimination

Same term across multiple batches separates *knowledge gap* from *card construction*:

| Term | Per-batch again-rate | Reading |
|---|---|---|
| SNMP | 43% · 42% | persistent knowledge gap |
| PoE | 38% · 30% | persistent knowledge gap |
| SSH | 8% · 35% · 12% | construction-dependent |
| **SSL** | 20% · 22% · **64%** | **run-134-specific** |
| **TLS** | 20% · 17% · **56%** | **run-134-specific** |
| SMTP | 30% · 33% · **17%** | improved in run 134 |

TLS/SSL were handled *better than baseline* twice before run 134. This is the strongest evidence that run 134's failure is construction, not comprehension — and note SMTP *improved* in the same batch, so "that batch was hard" doesn't explain it either.

---

## 5. Worked case: the P2PE ↔ Implicit TLS collision

The Chief Architect annotated a failing card live, in `Image_Prompt` (field 5 of `Basic+`): **"I answered before revealing 'Implicit TLS'"**.

The two cards, as they exist:

- **P2PE** — Back: *"Continuous device-to-server encryption, **zero unencrypted hops**"*; Reverse cue: *"**Not one single unprotected hop** exists between the phone and the mail server (Which coverage standard)?"*
- **Implicit TLS** — Back: *"Implicit TLS **encrypts instantly** on a dedicated port; StartTLS **delays encryption** until a mid-session upgrade"*

**The collision is structural.** "Zero unencrypted / not one unprotected moment" is *also* the defining property of Implicit TLS, because StartTLS is precisely the one with an unencrypted phase. The failure happened on the **reverse** card, whose cue is the ambiguous one.

**The missing axis, never stated on either card:** P2PE is **spatial** coverage (how many hops along the path); Implicit TLS is **temporal** (when in the session encryption begins). Both mean "no gaps."

### 🚩 The uncomfortable part

Run 134's two dropped matrices were:
- `Cleartext | SSL/StartTLS | Implicit-TLS vs StartTLS` — has Implicit TLS, **no P2PE**
- `SSL/StartTLS | P2PE` — has P2PE, **no Implicit TLS**

**Neither places P2PE and Implicit TLS in the same row.** Fixing GRAFT A would **not** have prevented this failure. The confusable pair was never analysed by the pipeline at all. That is a distinct gap from the routing bug, and it is the question in §0 item 4.

---

## 5b. 🚩 REQUIRED FRAMING — the loop is reactive BY DESIGN. Do not propose a Day-0 primer.

**This has already been proposed twice and rejected twice. Read this before designing anything.**

The Chief Architect's position, verbatim:

> *"I think the friction is good because it's making me seek answers, and I seek them in a very specific way, exactly where logic breaks for me, albeit days later."*
> *"We cannot predict the future to know what I will be confused by."*
> *"There's no way of knowing beforehand what's going to be easy and what I'm going to confront myself with."*

An up-front "Concept Primer" / pre-study explainer that anticipates confusion is **out of scope and already declined.** The reasoning is desirable difficulty: the retrieval failure is what makes the later explanation stick, and a predictive primer is a wall of text answering questions that haven't been asked yet.

**The chosen loop is: fail the card → annotate why, live → diagnose → patch.** Measurement, not prediction. Any design that front-loads explanation is a re-litigation of a settled decision.

⚠️ Corollary for GRAFT A: this is *also* why "just deliver every matrix to every card" is not automatically right. Bulk delivery is pre-emptive by nature. The §0 item 7 worth-it question exists because of this tension.

---

## 5c. Card ordering (finding recorded; NOT a design request)

Run 134's acronym-expansion card is **#18 of 18 — dead last.** The Chief Architect is asked *"S/MIME (Security actions on attachments)?"* at card 14 and told what S/MIME *stands for* at card 18. There is **no standalone MIME expansion card at all** — "Multipurpose" appears exactly once in the deck, buried inside the S/MIME expansion.

**End-placement is deliberate** (anti-spoiler) and the Chief Architect has confirmed it should stay. Recorded here only because it interacts with §4.2: 🏷️ Expansion is simultaneously the **worst-performing archetype** and the **last-encountered** card type, and every zero-annotation expansion card lapses across both run 133 and run 134 (CDMA 6, GSM 4, SIM 2, PRL 2, S/MIME 3). **Do not propose reordering.** The open question is whether expansion cards need scaffolding, not whether they need moving.

---

## 6. Context: the direction the Chief Architect has chosen

An end-of-pipeline **API call** was considered and **rejected**. The chosen vehicle is a **Claude Code skill**, run on demand, that reads the Anki collection, identifies failing cards, reads the user's live in-card annotation of *why* they failed, and patches at the right layer (edit a card, add a bridging ⚖️ card, or file an upstream pipeline defect).

**Autonomy constraint (stated explicitly):** *"Don't expect too much cooperation from me with this skill… you'll have to fetch the lapses, you'll have to fetch the GUID, and patch the required files based on the feedback I give you. The only thing I do is I summon the skill, and I accept the recommendations."* The skill reads the collection, identifies failures, reads the in-card annotation, decides the patch layer, and emits a ready-to-import file. The human contributes one command and one approval.

### 6.1 Patch layers available (all three are in scope)

1. **Edit the failing card** — front, back, or Extra.
2. **Edit the confusable *cluster*** — the sibling cards that collectively create the ambiguity, not just the one that failed.
3. **Add a new bridging card.** Empirically the best-supported option for confusable pairs: ⚖️ Compare is one of the two best-performing archetypes (9.0% mature vs 12.4% baseline, §4.2).

### 6.2 Enhancement techniques the Chief Architect wants available

Added context · ELI5 · mnemonics · analogies · killer facts · historical/news hooks · Rosetta-stone bridges · image prompts. **On demand for failing cards only** — the explicit contrast with the old protocol, which made them mandatory on every card and paid the token cost universally.

**What actually survives in the collection from that old protocol** (measured):

| Element | Notes carrying it | Date range |
|---|---|---|
| `Image_Prompt` (field 5) | **255** | 2025-12-31 → 2026-02-10 |
| Analogy | 67 | 2025-07-28 → **2026-07-26** (still live) |
| Mnemonic | 65 | 2025-07-28 → 2026-04-13 |
| ELI5 | 2 | 2025-07-28 → 2025-10-14 |
| Killer fact | 0 | — |

⚠️ The Chief Architect recalls ELI5 + killer fact + image prompt on *every* card. The collection only partly supports that — but a **fully-loaded old-protocol exemplar does exist** and is available: the `QHD (WQHD)` note in the native Anki export carries a killer fact, a memory hook, a Major-System mnemonic, an ELI5, a lecturer quote, a collapsible refresher table, search links, and a populated Image_Prompt. **That single note is the best available specification of the old format.**

### 6.2b 🚩 Independent validation of GRAFT A's value — read this before answering §0 item 7

The Chief Architect described, **unprompted and without reference to the `Notes` finding**, exactly the artifact the pipeline is discarding:

> *"When you review atomic facts… it's good to have them in isolation and this is why flashcards are great. But sometimes after you reveal the card, as a refresher and to compare yourself and to do a sort of mini encoding session — you see the table in the Extra field or somewhere on the reveal on the back of the card, you sort of correlate and refresh."*
> Examples given: USB speed generations; RAM pin-notch counts per DDR generation.

Three independent lines converge on the same artifact:

1. **P2 already builds it** — 228 `📊 Matrix` payloads, 193 discarded (§2.2).
2. **The old protocol already shipped it** — the `QHD` exemplar carries a collapsible `<details><summary>🔄</summary>` "Refresher: Display Standards" table listing HD/FHD/QHD/UHD side by side, on the reveal.
3. **The Chief Architect independently asks for it**, describing the reveal-side comparison table as a "mini encoding session."

⚠️ This is the strongest evidence *for* recovery, and it should be weighed against the counter-case in §0 item 7 — but note the shape it argues for: a **compact reveal-side refresher table**, not a bulk dump onto every card. It is also consistent with §5b, because a table you see *after* answering is not a pre-emptive primer.

### 6.2c Repeat-offender detection — validated by lived experience

The Chief Architect on RAID 5 vs RAID 6:

> *"I probably failed those two cards and confused them for **four months** until I realized… this is the part that an LLM could probably predict instead of me having to month after month fail at them. We could for example create a bridge card where it compares the two, or we can edit both cards."*

This is §4.3's cross-run repeat-offender analysis, arrived at independently. It is a **measurement** capability (which pairs keep failing together), not a prediction one — consistent with §5b. SNMP (43%/42% across two batches) is the same pattern still unresolved today.

### 6.2d Clustering of explainers — RULED, do not design

Earlier in the session the Chief Architect asked whether explainers should be split into categories/clusters. **Ruling: deferred deliberately, not to be designed up front.**

> *"No, not necessarily. This skill is probably gonna evolve over time. So we should deploy it first, and then we'll see how it goes — because we can theorize, and unless we do it… I'm gonna have to see in the moment."*

Ship, observe, evolve. Recorded so it is not re-raised as an open design question.

### 6.3 🚩 The Blueprint container — an OPEN question, never resolved

Stated repeatedly and still undecided. The Chief Architect's words:

> *"It has no limits. Anki has no limits. **I decide** if I graduate the whole blueprint… It's going to be there. If I ever want to go and look at it, it's going to be there. I'm going to hit again. **It's going to be a special type of note.**"*
> *"It would have to be a special folder, a special deck for it… I'm going to have to work the parameters in Anki when I create this special type of flashcard. **The graduation is a lot more extreme.** I see it once and that's it."*

So a recovered matrix / relational map is **not** necessarily an Extra-field bullet on an existing card. The stated intent is a **distinct note type, in its own deck, with deliberately extreme scheduling**, that the Chief Architect graduates manually.

⚠️ **Chat has already given two contradictory answers here** — first *"suppressed (suspended) so it doesn't show up in your daily reviews,"* then *"standalone cards added to the deck."* **These are incompatible: a suspended card can never be shown, so it can never be hit "Again," which is the explicit requirement.** Resolve it, don't repeat it.

This bears directly on GRAFT A: *where* recovered content lands changes what the graft must produce (an Extra-field string vs. a whole new note in a different notetype and deck). §0 item 1 cannot be answered without settling it.

### 6.4 Annotation lifecycle

Live annotation goes in `Image_Prompt` (field 5) — confirmed working in production: the Chief Architect wrote *"I answered before revealing 'Implicit TLS'"* into it on 2026-07-28 19:12. **The annotation must be cleared after the patch is applied** (*"clean our tracks"*) so field 5 does not accumulate stale failure notes. ⚠️ Two things unverified: whether a pipeline re-import overwrites field 5, and whether clearing should be automatic or approved per-card.

Immediate plan: **fix the 9 failing run-134 cards by hand first**, then encode the skill from what that teaches. Design constraints already stated by the Chief Architect:

- *"Define and not bloat it"* — **"no patch needed / user skimmed" must be a first-class, counted outcome.** A patch skill that always finds something to patch will bloat the deck. This is Claude Code's documented Addition Bias and any skill it authors inherits it.
- Annotation home is `Image_Prompt` (field 5, currently dead space — 255 notes populated, abandoned since 2026-02-10). ⚠️ **Unverified: whether a pipeline re-import overwrites field 5.** Must be checked before annotations accumulate.
- Not yet designed: logging *what patch was applied* and *whether it worked*. Without that, technique effectiveness is unmeasurable.

**Standing risk, with precedent:** 590 telemetry issues sat unread for two months. If the skill's upstream findings land somewhere nobody opens, it becomes the second telemetry database.

### 6.5 Delivery constraint — deployability over elegance

> *"These cards are priority. **I don't want to be in development hell forever.**"*

The 9 failing cards are being fixed **by hand, now**, independently of any graft this council designs. Card work does not wait on pipeline work. A proposal that requires a large refactor before producing any improvement is the wrong shape regardless of its elegance — this is Constitution 2 (Convergence Mandate) with a concrete deadline behind it.

Related selectivity constraint, stated separately: *"We don't want wall of text around every single fact, every logic, delta, etc."* — 15 of run 134's 18 cards are mechanical atoms (ports, FQDNs, credentials) that pass fine. Any bulk-delivery design must say what it does **not** touch.

### 6.6 Rosetta Stone — verified still resident

The Chief Architect asked whether the Rosetta-stone mechanism survives in the current pipeline (*"I don't know if it's still there. I don't know if it creates scaffolding blocks"*). **It does:** `prompt2_draftsman.txt` 6 refs, `prompt3_formulator.txt` 8, `prompt4_reverse.txt` 1, `prompt5_exporter.txt` 1. ⚠️ Notably **absent from `prompt1_harvester.txt`.** Residency confirmed by grep; *behaviour* not audited.

---

## 7. Findings that came back NEGATIVE (do not re-litigate)

- **Extreme-lapse outliers are legacy personal cards** (77/64/40 lapses = 2021–22 meditation and habit cards). Mean lapses/card: collection 0.66, pipeline-era 0.54 — pipeline cards lapse *less*. ⚠️ Test was biased toward old cards by the `lapses`-column problem; says nothing about recent card design.
- **Reverse cards are not a problem.** Forward 26.6% vs reverse 25.1% (−1.5 pts), neutral-to-better in every archetype. ⚠️ Confound: only 34% of notes get a reverse, threshold-selected.
- **The pipeline is not "sycophantic to the transcript."** Deprecation/currency rules exist (`prompt1_harvester.txt` 25 refs, P2 9, P3 5) including a named **STEP 1.5E REALITY CHECK SWEEP** (`prompt1_harvester.txt:226`). It fired correctly on run 133 — the transcript said nothing about 4G/5G/LTE and the deck still shipped `📌 CDMA/GSM split (Current real-world status)? → Largely obsolete today.` The S/MIME obsolescence loss was a *routing* failure, not a philosophy failure.
- **Phase 6's 8→0 DEBT drop was a human veto**, not a leak — `run_phase6.py:82–210` implements VETO-6. ⚠️ But `:167`'s LOW-certainty bulk prompt defaults to **`ENTER = reject ALL`**, and that run's telemetry had explicitly asked for human review of a LOW-certainty entry.

**Ruled OUT OF SCOPE by the Chief Architect for this round** (recorded so it is not silently dropped, and so nobody re-raises it): **NotebookLM.** It is a live and valued arm of the learning stack — `NOTEBOOK_PRODUCER_BRIEF.txt`, `NotebookLM_Prompt_BETA.txt`, `pairings.py` — and it was discussed repeatedly during this scout. It is excluded from *this* council round by explicit decision, not by oversight.

---

## 8. PASTE THESE WHOLE FILES TO CHAT

**The Chief Architect's instruction: give the council the WHOLE prompt chain, 2 through 5.** The downstream-interception audit (§0 item 5) cannot be answered from P2 and P3 alone — P4 and P5 are where a reintroduced field would next be at risk, and *"they might see things that we don't see."*

**Core set — paste all four:**
- `Prompts/prompt2_draftsman.txt` — writes `Notes`; `:494` and `:511` define its purpose
- `Prompts/prompt3_formulator.txt` — the routing mandate (`:346–370`, `:377`, `:385`) **and** the Tags contradiction of GRAFT B
- `Prompts/prompt4_reverse.txt` — reverse generation; must be checked for how it treats a reintroduced field
- `Prompts/prompt5_exporter.txt` — the exporter; also the source of the emoji/archetype rules in §4.2

**Orchestrator scripts — the council must see these, not just the prompts.** Every candidate architecture is executed by one of them, and a graft that a prompt can express but a script cannot carry is a dead graft. ⚠️ **Claude Code has read NONE of these except `run_phase6.py`.** Any statement in this brief about what a script does or could do is inference from filenames and greps, not from reading.

| Script | KB | Why the council needs it |
|---|---|---|
| `run_phase5.py` | 95 | Export stage — where a Python-side siphon would live. **The single most load-bearing unread file in this brief.** |
| `run_phase3.py` | 24 | Executes P3; any routing graft lands here |
| `run_phase2.py` | 25 | Executes P2; writes the `Notes` payload |
| `run_phase4.py` | 8 | Executes P4; reverse generation over a reintroduced field |
| `run_master.py` | 25 | Orchestration and baton hand-offs between stages |
| `config.py` | 46 | Configuration surface — never read; may already gate relevant behaviour |

**Supporting evidence:**
- `Archive/134/baton_p2_to_p3.txt` — a bold-style baton (worked example)
- `Archive/133/baton_p2_to_p3.txt` — a plain-style baton (the §2.3 format hazard)
- `Archive/134/ANKI_IMPORT_READY.txt` — the 18-card deck under analysis

### 8.1 Surfaces never examined during this scout

Named so the council knows the edges of the evidence, and so nobody assumes they were cleared:

`run_phase1.py` (77 KB — where the Tutor Bridge and Reality Check sweeps actually execute) · `config.py` (46 KB) · `reference_library_p1.xml` / `p2.xml` (108/109 KB — grepped only, never structurally read) · `PRE_FLIGHT_QUESTIONS.txt` · the separate **`Quiz` notetype** and `Z. CompTIA A+ Quiz` deck (71 notes — an entire second card system) · 792 suspended cards, reason unknown.

---

## 9. Method notes / trust calibration

Four measurement bugs were caught and corrected during this scout. Any number in this brief post-dates its correction, but the pattern is worth knowing:

1. A regex anchored on `^\*\*Notes:\*\*` reported "7 runs emit zero Notes" — they use plain `Notes:`.
2. A verbatim substring test claimed most P2 fields never reach the deck — P3 *rewords* by design; re-measured by destination marker.
3. Reusing one sqlite cursor for an outer loop and inner queries silently truncated results to 1 row (hit **twice**).
4. Counting the bare word `Matrix` instead of the `📊 Matrix` payload inflated both sides of the delivery ratio.

Ripgrep is blind to `Archive/` — root `.gitignore` line 2 is `*` and rg honours it. Archive searches must use a non-git-aware tool.
