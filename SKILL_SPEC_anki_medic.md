# SKILL SPEC — `/medic` (Card Triage & Repair)

**Status:** architectural specification, v2. **Not** an executable skill file.
**Author:** Claude Code. **Revised:** 2026-07-30. **Partially superseded 2026-07-31 — read the precedence rule below first.**

> 🚫 **PRECEDENCE — `medic.md` wins, always.** This document records *why* the skill is shaped as it is. It is not a second source of operational rules, and it is **not maintained in lockstep**: `medic.md` took ~22 amendments on 2026-07-31 and this file took none. Where the two disagree, **the skill is correct and this file is stale.** Consult this document for rationale, evidence and measured figures — never to settle what the skill should *do*.
>
> **Known stale as of 2026-07-31** (recorded rather than rewritten, since restating the skill here would create exactly the second source of truth this rule forbids — see `CHANGELOG.md` 2026-07-31 for each):
> - **§ AIRLOCK / T5 — factually wrong, corrected below at both sites.** `Tiny Javelins>` is stored HTML-escaped as `&gt;` and renders harmlessly; it was a false positive. The real mechanism is `</` + non-letter opening a bogus-comment parse.
> - **Annotation scan is no longer two fields.** All six are scanned, detection by *shape* not location — a verdict was found in `Inverse_Question`.
> - **🚫 THE PATCH FILE IS RETIRED (2026-08-01).** Every §7/§8 passage describing a `PATCH.txt` export, an import step, or a GUID-keyed 10-column layout is **dead**. All changes — field text, tags, scheduling, suspension — now execute through AnkiConnect after an explicit go, and the run opens Anki and syncs AnkiWeb first. Treat every "the user imports it" sentence below as historical.
> - **Absent entirely:** the AnkiConnect execution channel · ⏱️ Forced adjacency · ➖ Merge · `medic::junk::partial` · `(NOT <rival>)` front qualifiers · clearing annotations on Class J · the 13/248 provenance figure (was 14/247) · the Class E plain-text fallback.

**Sources:** legacy *Unified Flashcard Protocol* + *Ultimate Flashcard Protocol V68.1 Beta*; 8 in-card annotations from the 2026-07-29 review session; live collection forensics.

**Name:** `/medic` — not `/lapse`. The skill also triages **junk** cards that were never lapsed (buried with Easy), so a lapse-only name misdescribes half its job.

> 📌 **Durability:** repo root. Confirm it is not swept by `.gitignore` before relying on it.

---

## 0. What changed from v1

v1 was written before the 2026-07-29 review session. Eight annotated cards and a forensic pass invalidated or extended most of it.

| Change | Reason |
|---|---|
| **WAL copy is mandatory** | v1's method silently dropped a day of data — twice |
| Signal set widened well past `ease=1` | Hard presses, annotated-but-passed cards, junk buried with Easy |
| `Medic_Notes` is the annotation home | Renamed from `Image_Prompt`; Extra stays pipeline-owned |
| Timestamp→card resolution | Solves forward-vs-reverse with zero new fields |
| **Three new failure classes** | Priming bleed, near-identical acronyms, junk |
| Copilot-style explainer added to toolkit | Explicitly requested; v1 omitted it |
| Junk triage added | Suspend/delete is not repair — it's a separate function |
| Scheduling state feeds tool choice | A Back edit on a just-passed card is invisible for weeks |
| Upstream ticket output formalised | *"this QA is the missing link"* |

---

## 1. Scope

The legacy protocols are **deck-generation** engines. This skill runs the other direction: **existing card behaved badly → diagnose → repair, or condemn.**

**Two outputs, always:**
1. A **patch file** for Anki import (or a no-op verdict).
2. An **upstream ticket list** — pipeline defects that produced the bad card, so the next batch doesn't repeat it.

Output 2 is the point. Output 1 is triage.

---

## 2. Data acquisition

### 🚩 2.1 WAL — mandatory, non-negotiable

Anki runs SQLite in **WAL mode**. Copying only `collection.anki2` **silently discards every uncommitted write.**

```
copy BOTH:  collection.anki2  AND  collection.anki2-wal   → scratchpad
then open the copy (SQLite replays the WAL automatically)
```

**Verified failure:** 2026-07-29 — the base file's newest row was 07-28 19:20 while the 638 KB WAL held 63 reviews and 8 annotations from that day. The live file is locked while Anki is open, so direct read is not an option. **Copy both, or see stale data and report it as absent.**

### 2.2 The signal set — five independent triggers

| Trigger | Query | Why |
|---|---|---|
| **Failure** | `revlog.ease = 1`, `type IN (0,1,2)` | **Never `cards.lapses`** — see 2.3 |
| **Struggle** | `revlog.ease = 2` (Hard) | 897 rows collection-wide; +5.5% signal, free |
| **Annotation** | `notes.mod` newer than watermark | **Independent of grade.** You must never have to fail a card deliberately to flag it |
| **Junk** | `ease = 4` on a card's *first* review | 250 cards (6.9%), 49 of them reverses — buried, not mastered |
| **Watermark** | last `/medic` run timestamp | *"cards reviewed since last skill invocation"* |

### 🚩 2.3 The `lapses` column trap

`cards.lapses` only increments on *review*-stage failures. Measured: the worst card in the collection reads `lapses = 1` while carrying 12 "Again" presses. **A query on `lapses > 0` reports a healthy deck.** This one mistake neuters the skill.

### 2.4 Batch identity

Note IDs are epoch-ms creation stamps. One pipeline run is imported at a time, so **import time is the run boundary.** No run/video tag exists in the deck (tags carry topic hierarchy only).

### 2.5 Pipeline provenance

Join `polished_yaml.txt` `Meta:` segment-2 → `baton_p2_to_p3.txt` `Target_Concept`. **91.4% exact match across 25 runs.** Gives the skill the card's original `Raw_Fact`, `Delta_Logic`, and `Notes` — including the dropped `📊 Matrix`.

⚠️ **The baton exists in two serialization formats** (`**Field:**` and `Field:`); run 135 mixes both in one file. Every field pattern must be `\*{0,2}Field:\*{0,2}`. **One shared tested parser — five ad-hoc regexes disagreed by up to 165% this session.**

---

## 3. Reading the annotation

### 3.1 `Medic_Notes` — the single home

`Image_Prompt` is **renamed** to `Medic_Notes`. Verified field map:

```
ord 0 Front · 1 Back · 2 Extra · 3 Inverse_Question · 4 Inverse_Answer · 5 Medic_Notes
export:  1 guid · 2 notetype · 3 deck · 4–9 fields · 10 tags     → Medic_Notes = column 9
```

**Rename, never add.** Adding a 7th field pushes `tags` to column 11 and breaks every export header plus `run_phase5.py`. A rename changes nothing structural.

⚠️ 255 notes (Dec 2025–Feb 2026) carry legacy image prompts in that field. Harmless — recency filtering excludes them — but they will look like annotations in the browser.

**Division of fields, settled:**
| Field | Owner | Visible on |
|---|---|---|
| `Back` | pipeline | one card only |
| `Extra` | pipeline | **both cards** |
| `Medic_Notes` | **you** | neither (not rendered) |

### 🚩 3.1a Transition rule — annotations also live in `Extra`

*"also be aware some edits I made in extra field."* Confirmed: on 2026-07-29 two of eight annotations went into `Extra` (the cards where `Extra` was empty) and six into `Image_Prompt` (where it wasn't).

**The skill must read BOTH fields for annotations, indefinitely — not just `Medic_Notes`.** Distinguishing them is mechanical: pipeline content in `Extra` always carries a marker (`⚠️ NOT:`, `📊 Matrix`, `👁️`, `🪝 Hook:`, `Relates to:`, `Example:`, `Forensic:`). **Unmarked prose in `Extra` is yours.**

### 3.1b Appending to a non-empty `Extra`

*"how would you handle if existing text is already there? hmmm. we need to decide."*

**Rule:** never overwrite. Append after existing content with a `<br>` separator, patch content last. If the target already carries a marker of the same class (a `📊 Matrix` when recovering a matrix), **skip** — see the dedup guard in §8.4.

### 3.1c Two kinds of annotation — separate them

*"but this edit has little to do with the actual answer."*

Your notes carry **two distinct payloads** and the skill must not conflate them:

| Payload | Signal | Destination |
|---|---|---|
| **Card diagnosis** — "I answered X instead of Y" | Classifies the failure (§4) | Drives the patch |
| **Meta-feedback** — skill design, pipeline questions, naming | Not about this card at all | Routed to §9 tickets or surfaced for discussion — **never** treated as a repair input |

Both appear in the same field, often in the same paragraph. Misreading meta-feedback as a card diagnosis produces a patch for a problem the card doesn't have.

### 🚩 3.1d An annotation is a SEQUENCE, and a later entry can void an earlier one

**This is the highest-risk parsing rule in the spec.** Annotations accrete across multiple review sessions inside one field, self-labelled: `"15:42pm: new note"`, `"edit 3"`, `"review at 17:00pm"`, `"16:23pm review"`.

**Worked example — note `Pw=.L+EJUX` (MIME).** Read as one blob it says:

> *"pipeline outputs are a TOTAL MESS, unless Im not getting it. what do we need to do? refine pipeline…"*

Read as a sequence, the final entry is:

> *"**edit 3, nevermind, I just realized encoding =/= encryption, Im a dummy. I guess the answer was staring me in the face. in the NOT SECTION**"*

**Blob-reading classifies this as a pipeline defect. Sequence-reading classifies it as Class J plus a win for the existing NOT field.** Opposite verdicts from identical text.

**Rule:** split on timestamp and `edit N` markers, process oldest→newest, and **the newest entry governs.** Earlier complaints that a later entry retracts are logged as history, never as findings.

### 🚩 3.1e Deliberate flag-fails must be excluded from all statistics

Two of eight annotations state it outright:

> *"I had to fail this card so you can see it, so it gets flagged, but I could have hit good because I had the answer ready."*
> *"I did not actually fail this card because I did not know it. I actually guessed right, but I wanted to point you to an item in toolkit."*

**These are Again presses that carry no knowledge signal.** Left in, they corrupt the failure counts, the cluster analysis, and — worst — the §9 outcome measurement that judges which tools work.

**Rule:** when an annotation declares the failure deliberate, mark the review `flag-fail`, **exclude it from every rate calculation**, and keep the annotation as diagnostic input. Report separately: `2 of 11 Again presses were deliberate flags — excluded from rates.`

⚠️ **This is now obsolete by design.** §2.2's annotation trigger fires on `notes.mod` regardless of grade, so you never need to fail a card to flag it again. The rule exists to clean historical data.

### 3.1f The user's self-assessment overrides the raw grade

> *"I finally answered 'In-transit encryption methods'. omitted email, but **I count it as a success**"*
> *"I seem to learned the lesson in this case… so I should just read better"*

When an annotation contains an explicit self-resolution or self-grade, **it outranks `revlog.ease`.** A self-resolved card is **Class J — no patch.** You solved it during the session; adding an explanation afterwards is bloat for a gap that has already closed.

### 3.2 🚩 Forward vs reverse — solved by your timestamps

One note serves both cards, so one `Medic_Notes` field covers both. **Your manual timestamps resolve it.** Verified 4/4:

| You wrote | Nearest review | Card | Drift |
|---|---|---|---|
| "17:00" | 17:02:33 good | **ord=1 reverse** | 3 min |
| "17:52" | 17:57:05 AGAIN | ord=0 forward | 5 min |
| "16:23" | 16:24:57 AGAIN | ord=0 forward | 2 min |
| "15:42" | 15:52:08 AGAIN | ord=0 forward | 10 min |

**Algorithm:** parse `HH:MM` tokens from `Medic_Notes` → nearest `revlog.id` for that note → read `cards.ord`. **No second field, no prefix convention.**

**What to keep writing:** the timestamp and the ordinal (*"2nd review"*, *"edit 3"*). Those are load-bearing. The prose is diagnosis; the stamps are addressing.

**Fallback when no timestamp:** attribute to the most recent review before `notes.mod`, flagged as inferred.

---

## 4. Failure classification

| Class | Signature |
|---|---|
| **A · Rival answer** | A sibling's answer satisfies this cue on its own merits |
| **🚩 B · Priming bleed** | You answered a *different card's* answer, primed by reviewing it earlier in the session |
| **C · Abstract-on-abstract** | Jargon answer explained with more jargon |
| **D · Bare atom** | No annotation of any kind on the card |
| **E · Missing relational context** | Fact isolated from its sibling set |
| **F · Cue defect** | Front ambiguous, or its qualifier mislabels the fact class |
| **G · Near-identical acronyms** | Terms differing by transposition (SNMP/SMTP) |
| **H · Cross-run repeat offender** | Same concept fails every time it is taught |
| **I · JUNK** | Buried with Easy; should be suspended, not repaired |
| **J · NO DEFECT** | Cue misread. **First-class outcome — see §7** |

### 🚩 4.1 Class B is the dominant class, and it's new

**2026-07-29: 8 of 11 Again presses (73%) came from one 9-card cluster** carrying **71 lifetime Again presses**:

| Again | Front stem | Qualifier |
|---|---|---|
| 12 | `⚙️ S/MIME (…)?` | Underlying security mechanism |
| 9 | `⚙️ S/MIME (…)?` | Security actions on attachments |
| 4 | `⚙️ S/MIME (…)?` | Original scope limitation |
| 3 | `🏷️ S/MIME (…)?` | Expansion |
| 7 | `⚙️ MIME (…)?` | Effect on attachments |
| 12 | `📌 SSL/StartTLS (…)?` | Mail-protocol role |
| 8 | `⚙️ P2PE (…)?` | Coverage guarantee for email |
| 11 | `📌 Aside from encrypting…` | *none* |
| 5 | `⚖️ How do Implicit TLS…` | *none* |

**Four cards share the stem `S/MIME (…)?`, separated only by a parenthetical.** `MIME (Effect on attachments)?` and `S/MIME (Security actions on attachments)?` are near-identical in shape.

**Mechanism, timestamped:** 17:02 you graded `Aside from encrypting…` Good. 17:57 you failed `SSL/StartTLS` — annotation: *"I answered 'in transit email encryption techniques', thinking of the card I just hit good on a while ago."* That is the earlier card's Inverse_Answer. **Documented bleed, 55 minutes apart.**

Your own diagnosis, and it is correct: ***"Cue, front of cards should be unique, point to a single answer, non ambiguous."***

**Class B is a cue-side defect. It cannot be repaired by adding to the answer side.**

### 4.2 Class G is measurable

| Term | Notes | Reviews | Again | Rate |
|---|---|---|---|---|
| **SNMP** | 8 | 148 | 64 | **43.2%** |
| SSH | 8 | 141 | 44 | 31.2% |
| SMTP | 10 | 101 | 30 | 29.7% |
| *baseline* | | | | *26.1%* |

Your hunch — *"user seems to fail at SNMP and SMTP, maybe user thinks theyre the same thing"* — is confirmed. SNMP is **1.7× baseline** and the worst term measured. **The skill can surface this before you notice it.**

### 4.3 Class H is measurement, not prediction

Cross-run term analysis: consistent high rate across batches = knowledge gap; variable rate = card construction. TLS scored 20%/17% in earlier batches and 56% in run 134 — construction, not ignorance. **This runs after the fact and stays consistent with the standing rule that confusion cannot be predicted in advance.**

---

## 5. The toolkit

### 5.1 Content tools

**🧠 Analogy** — functional similarity, 1–2 emojis, **required sensory detail**.
Approved domains: Organic · Kinetic · Arts.
**BANNED:** traffic · cars · highways · water pipes · office filing · **locks/keys** · factories · buildings · clocks/gears · bridges · conveyor belts · money · computer parts · office supplies.

**🧸 ELI5** — kindergarten language, **must revolve around a physical object a child can hold**.
**Abstract Ban:** *data · signal · protocol · interface · connection*. Substitute: data→mail, power→juice, signal→shouting, protocol→secret rules.

**💡 Killer Fact** — One-Line Validator: must contain History **or** Scale **or** Contrast. Forbidden openers: *"This is a…" · "It is used for…" · "Allows you to…"* Scope Lock: must relate to the concept, not define a noun in the answer.

**🚀 Absurdist Mnemonic** — `[Animal][Action][Object] → [Sound!] → [Outcome!]`. Canonical: *Dizzy Hippos Crashing Parties → SPLASH! → IPs FOR EVERYONE!*
Assignment matrix: procedural→Link&Story · conceptual→Visual Transformation · comparative→Phonetic.

**⚡ Acronym Breakdown** — **gate: `^[A-Z0-9]{2,}$`.** `PCIe` fails, `S/MIME` fails.

**🔢 Number Peg / UVH** — **gate: exact single numeric value.**
Major System `0=s 1=t 2=n 3=m 4=r 5=l 6=sh 7=k 8=f 9=p`; seeds `22=nun · 25=nail · 80=fuzz · 143=dreamer · 161=tissue · 443=reamer · 993=papa`.
Category precedence: PINS → VOLTAGES → PORTS.

**🖼️ Image Prompt** — UVH Strict Assembly: **Location=Stage, Object=Actor, Concept=Action**, literal not metaphorical. Gates: Creativity ≥8/10 · **Blindfold Test** (erase the caption — does the image still hint at the answer?) · **NO SIGNS rule** (answer encoded in physical form, never on a label) · banned emotions (anything describable of a spreadsheet; requires bodily sensation).

**🩺 Copilot-Style Explainer** — *explicitly requested; v1 omitted it.*
For Class E/H where NOT and Matrix are insufficient. Structure from the pasted exemplar: one unifying analogy covering the whole cluster → per-term breakdown → concrete before/after example → explicit "X is not Y" contrasts → chronological evolution where relevant.

✅ **Container RULED 2026-07-30:** *"Append it to the card (in the Extra field). Do not create a separate deck for it."*
Delivered **appended to the failing card's `Extra`**, wrapped in the 🔄 collapsible so it stays collapsed by default and reveal-side. **No separate deck, no new notetype.** This also means it inherits `Extra`'s advantage — visible on both the forward and reverse card.

### 5.2 Structural tools

**⚠️ NOT-section update** — cheapest tool in the box, and proven: your MIME annotation ends *"nevermind, I just realized encoding =/= encryption… the answer was staring me in the face. in the NOT SECTION."* Seed the NOT with **your actual wrong answer**, not a generic distractor.

**✂️ Front constraint edit** — Class F/B only. Add discriminating signal to the cue **without spoiling the answer**. Highest blast radius in the toolkit; requires explicit approval per card.

**⚖️ Bridge card** — Class A/B. ⚖️ Compare sits at **9.0% mature vs 12.4% baseline**. Must name the **axis** (the P2PE/Implicit-TLS collision was spatial-vs-temporal and neither card named it).

**📊 Matrix recovery** — Class E. Retrieve the dropped `📊 Matrix` via §2.5. **Zero generation cost — the content already exists.**

**🔗 Micro-bridge** — inline `("Anchor Text")` for a term absent from the transcript. Priority 1 lecturer's phrasing, Priority 2 a 2–3 word visceral gloss.

**🔄 Collapsible refresher table** — ✅ **APPROVED for v1.** The proven container: the QHD exemplar's `<details><summary>🔄</summary>` block, and the SDRAM card's RAM-Generations table you pointed at — *"its perfect for comparisons like this where it gets confusing and putting them site by side is ideal."*

```html
<details><summary>🔄</summary><div align="center"><b>Refresher: [Title]</b><br>
<table border="1"><tbody><tr><th>…</th></tr><tr><td>…</td></tr></tbody></table>
</div></details>
```
Limits: **≤5 columns, ≤6 rows including header.** Collapsed by default — it does not compete with the answer, and it is reveal-side, so it does not front-load explanation. **This is the natural container for 📊 Matrix recovery** (§5.2) and for Class G acronym separation.

⚠️ AIRLOCK applies inside the wrapper: no internal `<b>` tags, no `->`, no stray `>`.

🚩 **HARD PREREQUISITE — the CSS does not exist yet.** Verified 2026-07-30: the entire `Basic+` stylesheet is **761 characters with one selector, `.card`**. There is **no** rule for `.extra-container`, `.extra-field`, `details`, `summary`, `.card-details`, `.inline-toggle`, or `.toggle-inner` — every one of those is generated by the template's JavaScript and rendered unstyled, inside a container set to `font-size: 36px; text-align: center` with flex centring.

**That is why simple mode was switched on** (simple mode replaces `.back` wholesale, so the machinery never runs). **Collapsibles will render as raw 36px centred disclosure triangles until the CSS lands.** Ship the CSS before the collapsible tool is enabled.

**🗑️ Junk triage** — **not a repair.** Class I: propose suspend or delete. 250 candidates exist (6.9% of reviewed cards, 49 reverses). Never auto-executed; always listed for approval.

---

## 6. Tool selection

**One primary tool.** Classification selects, gates filter, scheduling constrains.

| Class | Primary tool |
|---|---|
| A · Rival answer | ⚖️ Bridge card + named axis |
| **B · Priming bleed** | **✂️ Front constraint edit** — cue-side defect needs a cue-side fix |
| C · Abstract-on-abstract | 🧠 Analogy **+** 🧸 ELI5 *(only class permitted two)* |
| D · Bare atom | 🚀 / ⚡ / 🔢 — most specific gate that fires (Peg > Acronym > Mnemonic) |
| E · Missing context | 📊 Matrix recovery, escalating to 🩺 Explainer |
| F · Cue defect | ✂️ Front edit |
| G · Near-identical acronyms | 🚀 Phonetic separator |
| H · Repeat offender | 💡 Killer Fact or 🖼️ Image Prompt |
| I · Junk | 🗑️ Suspend/delete proposal |
| J · No defect | **nothing** |

### 🚩 6.1 Scheduling constrains the vehicle

*"chosen tool from toolkit will need to consider next time card will show. edit will most likely be on back so not visible straight away when I review it again weeks from now."*

| Card state | Constraint |
|---|---|
| Just graded Good/Easy — next review weeks out | A Back or Extra edit is **invisible until then.** Prefer a **new card** (bridge or explainer), which enters the new queue immediately |
| In learning / relearning — reappears soon | Field edits land quickly. Cheapest tools apply |
| Failed repeatedly today | Front edit is justified; you'll see it within the day |

### 6.2 Escalation
First patch = one tool. **Only on a repeat failure of an already-patched card** does a second tool get added, logged. Third failure of a patched card = reclassify as **card-design failure**, not an explanation gap, and route to §9.

---

## 7. 🚩 The no-op verdict

> *"If there's a problem with the card, we have to define and not bloat it."* · *"if it's noise, if it's a false positive, ignore it."*

**Class J terminates with zero output**, logged and counted: `3 of 11: no defect — cue misread. No patch emitted.`

Your SDRAM annotation is the archetype: *"I did not actually fail this card because I did not know it. I actually guessed right."*

**Why architectural, not polite:** a skill built to patch finds something to patch every time. That is Claude Code's documented Addition Bias, inherited by anything it authors. The maturity control this session is the warning — two-thirds of a headline finding evaporated under a proper control. **Without a counted no-op the deck grows while the failures don't shrink.**

---

## 8. Output

### 8.1 Landing sites

`Extra` renders on **both** cards; `Back` renders on one. That settles *"stitch to back — WHICH back?"* — **Extra reaches both for free.** The formatting complaint that caused `data-simple="1"` is a **template CSS problem, not a routing problem**; fix `.extra-container` before considering a P3 routing change.

### 8.2 Patch file — locked from a real Anki export

```
#separator:tab
#html:true
#guid column:1
#notetype column:2
#deck column:3
#tags column:10
```
Columns: `1 guid · 2 notetype · 3 deck · 4 Front · 5 Back · 6 Extra · 7 Inverse_Question · 8 Inverse_Answer · 9 Medic_Notes · 10 tags`

⚠️ **Native export layout — not `ANKI_IMPORT_READY.txt`**, which is pipe-separated, 8 columns, no GUID, and will not round-trip.

One file per run. **No SQLite writes, ever.**

### 8.3 GUID safety
7 duplicate GUIDs exist collection-wide. **Abort on any target carrying one** rather than risk merging the wrong note.

### 8.4 Ban enforcement — pre-emission, regenerate on failure

Domain ban · sensory requirement · abstract ban · concrete prop · lazy-fact detector · One-Line Validator · acronym gate · numeric gate · Blindfold test — **plus AIRLOCK on every field**: `->` → `→`, `=>` → `⇒`, strip stray `>`.

🚩 **AIRLOCK is load-bearing.** Your card template renders `Extra` by assigning `innerHTML` from a hidden div; a raw `>` terminates the parse and spills text. ⚠️ **CORRECTED 2026-07-31 — the SDRAM `Tiny Javelins` example is a FALSE POSITIVE:** it is stored HTML-escaped as `&gt;` and renders as a harmless literal character. The mechanism that *is* live is `</` followed by a non-letter (e.g. `</🚀`), which puts the parser into bogus-comment state and swallows everything to the next `>` — usually the `>` of an internal `<b>`. **2,141 such wrappers across the `Basic+` deck; 358 notes also carry a trailing raw `>`.** See `medic.md` §5a.

---

## 9. Upstream tickets — the missing link

> *"skill needs to draw lessons from cards and at the end review prompts if we can patch protocol to avoid having to patch bad cards in the first place. this QA is the missing link."*

Every run emits a ticket list. **Standing risk with precedent:** 590 model-authored issues sat unread in `prompt_telemetry_database.txt` for two months. **If tickets land somewhere nobody opens, this becomes the second telemetry database.** Tickets are printed in the run summary, not filed silently.

### Already collected

| # | Defect | Evidence |
|---|---|---|
| **T1** | **Cue collision within clusters.** 4 cards share the stem `S/MIME (…)?`; discrimination lives only in a parenthetical | 71 lifetime Again in one 9-card cluster; 73% of one day's failures |
| **T2** | **Wrong qualifier class.** `SSL/StartTLS (Mail-protocol role)?` answers with an identity, not a role | **Verified not drift** — byte-identical in P3, P4, and live |
| **T3** | **Reverses are invisible in the P5 veto gate**, so junk leaks and gets buried with Easy | 49 reverse cards first-graded Easy |
| **T4** | `Notes` sink — 228 matrices generated, 35 delivered (15%) | Format-agnostic, payload-exact, 22 runs |
| **T5** | **AIRLOCK not enforced upstream** | ⚠️ evidence corrected 2026-07-31 — `Tiny Javelins>` was a false positive (stored `&gt;`); the real defect is 2,141 malformed `</emoji` wrappers. See `MEDIC_TICKETS.md` T5, rewritten |
| **T6** | **`Logic:` bullets are not landing** — *"the logic point does not help me either"* | Annotation, note 1 |
| **T7** | **Discrimination is reveal-side only.** NOT and Matrix appear after the answer — *"I should not have to reveal a card to see matrix and NOT to learn"* | Annotation, note 2 |

**T1, T2, T7 are the same root cause: the cue does not carry enough signal to identify which sibling is being asked for.**

### ✅ 9.0 RULED — log everything, route nothing

Chief Architect ruling, 2026-07-30:

> **"Log all failures, scouting, and forensics cleanly in MEDIC_TICKETS.md. Do not route T1 (or any ticket) to the Design Council now. We will route them later… to a fresh chat session."**

**Scope is broader than pipeline defects.** `MEDIC_TICKETS.md` is the single ledger for **all** of it: card failures, scouting results, forensic findings, upstream defects. One file, one place to look.

**Routing is explicitly deferred.** The skill **never** initiates a council round. It accumulates, ages, and surfaces. Routing is a separate Chief-Architect action into a fresh session — which is also the right call for context economy: a fresh chat reading a clean ticket ledger beats one inheriting a long session's drift.

⚠️ **Standing scope note:** *"My focus right now is perfecting and deploying the /medic skill itself based on today's feedback, not fixing the upstream pipeline."* Upstream tickets are **recorded, not worked.** T1–T7 stay open in the ledger.

### 9.1 Where tickets live — `MEDIC_TICKETS.md`, not the telemetry log

**Separate file. Do not append to `prompt_telemetry_database.txt`.** Three reasons:

1. **Different provenance and trust level.** The telemetry log is machine-written — `harvest_telemetry` appends the LLM's own `<telemetry_log>` self-reports. Medic tickets are **human-observed, evidence-cited, output-verified.** This session proved the distinction matters: the telemetry log's most-repeated complaint (19×, 13 runs) was a **false positive** — the model reported stripping periods it never stripped. Mixing verified findings into an unverified stream degrades both.
2. **That file is already sick.** 590 unread entries, 71 duplicate lines, leaked raw payload. Appending inherits its failure mode.
3. **Different lifecycle.** Telemetry is append-only. Tickets have **state**.

**Ticket lifecycle — reuse existing infrastructure rather than inventing:**

| State | Home |
|---|---|
| **Open** | `MEDIC_TICKETS.md` — id, defect, evidence with `file:line`, affected card count |
| **Routed** | same file, marked with the council round it went to |
| **Closed** | **`CHANGELOG.md`** — the surgery that fixed it, in the existing tracked format |

🚩 **The anti-second-telemetry-database mechanism:** every `/medic` run prints **all open tickets** in its summary, with age in days. A ticket cannot go quiet — it reappears every invocation until closed. That is the one thing the telemetry log lacked, and the reason 590 issues sat unread for two months.

**Recommended companion:** the same digest treatment for the telemetry log itself — dedupe at harvest and print a top-N recurring digest at pipeline end. Different file, same principle: **don't ask a human to read a log; make the tool count and surface.**

---

## 10. State, dedup, lifecycle

**No external state file** — it drifts from the collection. **Use Anki's `tags`:** `medic::patched::YYYY-MM-DD`, `medic::tool::analogy`, `medic::junk::proposed`. Tags sync, travel with the note, and are queryable in the same read pass.

**Run watermark:** stored as a tag on a sentinel note or a scratch file — needed for *"cards reviewed since last skill invocation."*

**Annotation lifecycle:** after a patch ships, **archive `Medic_Notes` verbatim to a log, then clear it.** *"should we instruct skill to cleanup these comments I leave?"* — yes, but the annotations are the QA evidence trail; wiping without archiving destroys it.

---

## 11. Execution discipline

**Immutable Source Doctrine**, ported from `<2>` §1.5:
- **Phase A — Ghost Hunt:** all classification, gating, and tool selection before any output.
- **Phase B — Commitment Log:** decisions written visibly, then **locked**.
- **Phase C — Read-Only Render:** the patch file transcribes the log. Forbidden: *sneak-ins* (patching an unlogged card), *audibles* (changing tool between log and file), *lazy skips* (logged card missing from the file).

**Atomic stop:** the skill presents diagnoses and **halts**. It never diagnoses and emits in one unbroken run.

---

## 12. Deferred / excluded — overrule freely

| Item | Status |
|---|---|
| 🔍 Search links (DuckDuckGo / YouTube / TikTok) | Cheap, present in the QHD exemplar. Excluded to keep v1 narrow |
| Wave 1/2/3, Gatekeeper, Quiz engine, card-type matrix | Deck generation. No transcript in scope |
| Front ≤10 words / Back ≤7 words | Generation-time constraints — **except** where a Front edit *is* the repair |
| MIP Guillotine / Colon-Query rewriting | Would mass-rewrite existing reverses. High blast radius, no evidence of need |
| **Sibling burying** — *"cards need to be seen back to back"* | **Not a skill feature.** This is an Anki deck-preset toggle you control directly |

---

## 13. Decisions — settled and open

### Settled (2026-07-30)

| Decision | Ruling |
|---|---|
| **Front edits** — highest blast radius, fixes the dominant class | ✅ **Standing permission granted.** No per-card approval. Every front edit is still logged (§11 Phase B) and reversible via the patch file, but the skill does not stop to ask |
| **Collapsible refresher tables** | ✅ **In for v1** — see §5.2 |
| **Latency** — *"gotta wait until 1030pm"* | ✅ **Accepted for v1.** No bot, no automation. Same-day turnaround is not a requirement |
| **Annotation home** | ✅ `Image_Prompt` renamed to `Medic_Notes`; `Extra` stays pipeline-owned. ⚠️ **Superseded 2026-07-31: all SIX fields are scanned**, detection by shape not location — a verdict was found in `Inverse_Question` |
| **Skill name** | ✅ `/medic` |
| **Ticket storage** | ✅ `MEDIC_TICKETS.md`, closing into `CHANGELOG.md` (§9.1) |

### Still open

1. **T1 is a pipeline fix, not a card fix.** Route to the council now, or accumulate more evidence first?
2. **Explainer container** — its own deck, or appended to a failing card?
3. **`.extra-container` CSS** — worth fixing before any P3 routing change is considered?

### ✅ 13a. RULED — Cue bleed is a BUG

Chief Architect ruling, 2026-07-30, verbatim:

> **"Cue Bleed is a BUG, not a feature. 'Desirable friction' applies to retrieving the answer, not deciphering an ambiguous question. /medic must treat Class B (identical stems) as a defect and edit the Front of the card to make the discriminator sharp."**

**This is the spec's governing principle for Class B and it resolves the tension the annotations raised.** The distinction is precise and it is the line the skill enforces:

| Friction | Verdict |
|---|---|
| Retrieving the answer is hard | **Feature.** Desirable difficulty. Leave it alone |
| Working out *which question is being asked* is hard | **Bug.** Repair the cue |

**Operational consequence:** Class B is a defect. The front edit is the mandated tool, standing permission applies, and the skill does not ask whether the ambiguity might be productive. Where a card's stem is shared with siblings and the discriminator sits in a parenthetical, **sharpening the discriminator is the fix, not adding explanation to the answer side.**

Corollary: *"so I should just learn through associating flashcard front 'role = Encrypted versions of POP3/IMAP/SMTP'"* — memorising a front→back pairing instead of the concept is **evidence of the bug**, not evidence of learning. When an annotation describes that, it confirms Class B rather than excusing it.

### 13b. Two signals the skill structurally cannot see

Honest blind spots, not oversights:

- **Self-corrected near-misses.** *"I do sometimes confuse and want to say 802.11n is wifi 5, but I corrected myself before revealing."* No revlog trace, no annotation unless you write one. **Invisible.** The only capture route is you noting it.
- **Partially-correct answers.** *"I answered correctly wifi 4 but got the speed wrong."* Anki records one grade for the whole card; a multi-value Back has no per-value signal. Compound cards mask partial knowledge — which is itself an argument for atomicity, and a candidate ticket.

### 13c. Cross-domain bleed — a Class B variant

*"got the speed wrong, 480mbps, was thinking of usb speeds."* Class B as specced is **cluster-scoped** — siblings contaminating each other. This is **numeric bleed across unrelated domains** (USB 2.0's 480 Mbps → 802.11n's 600 Mbps). Same mechanism, no shared cluster, so cluster-based detection will miss it entirely. **Detection route: collide on the numeric value, not the topic.** Not built in v1.

---

## 14. Evidence base

All measured against the live collection (3,217 notes / 3,993 cards / 78,742 review rows) and the 22-run archive. Figures superseded during the session are void; these stand.

- **2026-07-29 session:** 63 reviews, 11 Again (**17.5%** — below your ~90% retention target), 8 notes annotated
- **Email-crypto cluster:** 9 cards, **71 lifetime Again**, 73% of that day's failures
- **Term rates:** SNMP 43.2% · SSH 31.2% · SMTP 29.7% · baseline 26.1%
- **Junk:** 250 cards first-graded Easy (6.9%), 49 reverses
- **Hard presses:** 897 vs 15,302 Again
- **Timestamp→card-ord resolution:** 4/4, max 10 min drift
- **Matrix leak:** 228 → 35 (15%)
- **Archetypes, mature reviews only:** Sequence 7.3% · Diagnose 8.3% · Compare 9.0% · *baseline 12.4%* · Spec 12.3% · Expansion 15.2%
- **Extra field:** 1,310 of 1,665 notes carried invisible content until the `data-simple` flip
- **`User_Anchor`:** 131 emitted, 5 delivered — **not a leak**, a designed single-slot precedence
