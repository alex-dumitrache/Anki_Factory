# MEDIC TICKETS — open ledger

Single ledger for card failures, scouting results, forensic findings, and upstream pipeline defects.
**Routing is deferred by Chief-Architect ruling (2026-07-30).** Nothing here goes to the Design Council until explicitly routed into a fresh session.

Every `/medic` run must print all OPEN tickets with age in days. A ticket cannot go quiet.
Closed tickets move to `CHANGELOG.md` — the tracked record of the surgery that fixed them.

---

## T1 · Cue collision inside concept clusters — OPEN

**Severity:** highest. **Opened:** 2026-07-30. **Class:** pipeline (P3 front construction).

Four cards share the stem `⚙️ S/MIME (…)?`, discriminated only by a trailing parenthetical. `⚙️ MIME (Effect on attachments)?` and `⚙️ S/MIME (Security actions on attachments)?` are near-identical in shape.

**Evidence:** the 9-card email-crypto cluster carries **71 lifetime Again presses**. On 2026-07-29, **8 of 11 Again presses (73%)** came from this one cluster. Timestamped mechanism: 17:02 `Aside from encrypting…` graded Good → 17:57 `SSL/StartTLS` failed with the earlier card's Inverse_Answer. 55-minute bleed.

**Ruled a BUG** (2026-07-30): *"'Desirable friction' applies to retrieving the answer, not deciphering an ambiguous question."*

**Fix direction:** P3 must guarantee cue uniqueness within a cluster. Not yet designed.

---

## T2 · Wrong qualifier class on the front — OPEN

**Opened:** 2026-07-30. **Class:** pipeline (P3).

`📌 SSL/StartTLS (Mail-protocol role)?` answers with an identity — *"Encrypted versions of POP3/IMAP/SMTP, using alternate non-default ports"* — not a role. Chief Architect: *"the word 'role' throws me off. role implies to me an action."*

**Verified not drift:** byte-identical in `polished_yaml.txt` (P3), `final_anki_cards.txt` (P4), and the live collection. P3 wrote it this way. Source `Raw_Fact` was a spec/identity fact.

Tied for worst card in the collection at **12 Again**.

---

## T3 · Reverse cards are invisible in the P5 veto gate — OPEN

**Opened:** 2026-07-30. **Class:** pipeline (`run_phase5.py` veto UI).

Chief Architect: *"reverses are not even shown in veto gate"* — so junk reverses ship unreviewed, and with no suspend function on AnkiWeb they get buried with Easy on first sight.

**Evidence:** **250 cards were graded Easy on their very first review** (6.9% of all reviewed cards). **49 are reverse cards.**

---

## T4 · The `Notes` field is a routing sink — OPEN

**Opened:** 2026-07-28. **Class:** pipeline (P2→P3 handoff).

`prompt2_draftsman.txt` writes a `📊 Matrix` into `Notes` for nearly every block. `prompt3_formulator.txt`'s BIFURCATED DATA ROUTING (`:346–370`) does not list `Notes` as a source; the only rule that reads it (`:385`) is scoped to the DEBT ATOMICITY OVERRIDE (`:377`) for `Contrast_Metric` + `Source_Type=DEBT` blocks.

**Evidence:** **228 matrices generated across 22 runs, 35 delivered — 15%.** Measured format-agnostically and payload-exact.

**Council round completed** (5 architects, 2026-07-29). Reconciled verdict: Python siphon reading the P2 baton, joined on the existing `Meta` concept field (**91.4% exact match across 25 runs**), injected at `run_phase5.py:735` immediately before the Origin strip — post-veto, so a rejected owner re-homes to a surviving sibling. **Not executed. Awaiting Chief-Architect clearance.**

Also open in the same file: `prompt3_formulator.txt:100` (matrices MUST go on Back, FORBIDDEN in Extra) directly contradicts `:385` (matrices route to Extra). All 35 delivered matrices are in Extra — i.e. in violation of `:100`.

---

## T5 · The pipeline emits a custom syntax that HTML destroys before the handler runs — OPEN, ✅ PREMISE CONFIRMED

> ✅ **SETTLED 2026-08-01 by direct observation.** The Chief Architect opened `nid:1770642186100` (Standard Ports: SNMP) and reported all four blocks **completely hidden — *including in the Anki editor***. That last detail is decisive: the editor renders the field as HTML too, so the loss happens at **parse time, before any JavaScript runs**. `</⚙️` is a closing tag whose name begins with a non-letter, which puts the browser into **bogus-comment state** and discards everything up to the next `>`.
>
> **The diagnosis is now sharper than either earlier version.** This is *not* "malformed markup" carelessly emitted, and it is *not* a designed feature working as intended. The template **does** contain an inline-toggle engine (`renderContent()` converts `</TAG content>` into a checkbox) — but **it has never fired even once**, because the browser destroys its input before the JS reads `innerHTML`. The feature was designed; the delimiter choice was fatal. **`</X` is never valid HTML when `X` is not an ASCII letter — there is no configuration in which this syntax could have worked.**
>
> ✅ **NO DATA IS LOST.** All four blocks are intact in `notes.flds`, verified byte-for-byte. This is a rendering defect, fully recoverable, not a deletion.
>
> **This reverses the "PREMISE DISPUTED" banner of a few hours earlier** — which was itself right to exist, since the previous diagnosis had been made from raw bytes with the template never opened.

**Opened:** 2026-07-30. **REWRITTEN 2026-07-30** against raw-byte evidence from `/medic` run 1. **Class:** pipeline (all prompts), generation side. **Severity:** high — silent content loss, not cosmetic.

### 🚩 What the original entry got wrong

It cited the SDRAM note (`DCXH>@FAe5`) carrying `Tiny Javelins>` as live evidence of a raw `>` breaking the parse. **That exemplar is a FALSE POSITIVE.** Raw bytes from the collection:

```
...</tbody></table></div><br><br>Tiny Javelins&gt;<br><br><br><br>
```

The character is stored **HTML-escaped as `&gt;`**. It renders as a literal `>` — visible junk, nothing more. There is no wrapper on that note, nothing is swallowed, and the card's Refresher table renders correctly.

**And the stated mechanism is wrong in general:** a bare `>` in text content does not terminate HTML parsing. Only `<` opens a tag. Stripping stray `>` treats a symptom.

### The real mechanism

`</` followed by a **non-ASCII-alpha** character puts the HTML parser into **bogus comment state**, which consumes everything up to the next `>` and discards it. The pipeline emits exactly that shape. Raw bytes, `q}A$}rAxk%` (Standard Ports: SNMP), field 2:

```
</⚙️ Association — IDENTIFY standard port • 📝 Port 161/162: SNMP (Simple Network Management Protocol)>
</🚀 Major System: 161=Tissue, 162=Kitchen. Story: The Network Manager sneezes into a <b>Tissue</b> (161/Poll) and runs to the <b>Kitchen</b> (162/Trap) when an alarm goes off.>
</🧸 SNMP is the hall monitor 👮. He checks his list (161) and blows his whistle (162) if there's trouble.>
</🎓 "SNMP - 161/162">
```

- ⚙️ Association — consumed whole → **invisible**.
- 🚀 Mnemonic — the bogus comment terminates early at the `>` of the internal `<b>`, so the opening half is **invisible** and the remainder spills as bare text ending in a stray `>`. **This is the "Tiny Javelins>" symptom — and the wrapper is its cause, not the `>`.**
- 🧸 ELI5 and 🎓 — consumed whole → **invisible**.

The AIRLOCK sub-rule that actually matters is therefore **"no internal `<b>` inside a `</…>` wrapper"**, and the deeper fix is to stop emitting `</` wrappers at all.

### Measured scale — Basic+ deck, 2026-07-30

| Measure | Count |
|---|---|
| Malformed `</…>` wrappers | **2,141** |
| Notes carrying a wrapper **plus** a following raw `>` | **358** |
| Fields carrying a genuinely raw, unescaped `>` | 169 |

Wrapper tokens observed: `</⚙️` · `</🚀` · `</🧸` · `</🎓` · `</Foreground:`.

The 169 raw-`>` fields are mostly unconverted `->` arrows (`UEFI -> Unified Extensible`, `GPT -> GUID Partition Table`) — a separate and genuinely cosmetic AIRLOCK miss.

**Fix direction:** emit these blocks as plain text (drop the `</` and the trailing `>`) or as a real element. Not designed. `<2>` §6.1.C's `->`→`→` / strip-stray-`>` rules are necessary but not sufficient.

⚠️ **`medic.md` STEP 5a carries the same false exemplar** — *"A raw `>` terminates the card template's `innerHTML` parse... There is a live example in the collection (`Tiny Javelins>`)."* Flagged, **not edited**: skill edits are a Surgeon-phase action needing Chief-Architect approval.

**Remediation of the 358 notes already in the collection is T11, not this ticket.**

---

## T6 · `Logic:` bullets are not landing — OPEN

**Opened:** 2026-07-30. **Class:** pipeline (P3 Line-2 content). **Severity:** low-confidence, needs more evidence.

Chief Architect on the worst card in the collection: *"the logic point does not help me either."*

Single datapoint. Recorded so it can accumulate rather than be rediscovered.

---

## T7 · Discrimination is reveal-side only — OPEN

**Opened:** 2026-07-30. **Class:** pipeline (P3 routing philosophy).

`⚠️ NOT:` and `📊 Matrix` land in `Extra`, which renders **after** the answer. Chief Architect: *"I should not have to reveal a card to see matrix and NOT to learn. Cue, front of cards should be unique, point to a single answer, non ambiguous."*

**T1, T2 and T7 are one root cause wearing three faces:** the cue does not carry enough signal to identify which sibling is being asked for.

---

## T8 · `Delta_Logic` conservation — OPEN, UNRESOLVED

**Opened:** 2026-07-29. **Class:** pipeline (P3 Line-2 contention). **Status:** classification (c) — unclear.

`Delta:` reaches a forward card 63 times from 94 populated `Delta_Logic` fields (67%), and reaches a **reverse card zero times across all 22 runs**. Block→card attrition is only 7.7%, so attrition does not explain the gap. 100% of `Delta_Logic` blocks also carry a `Reasoning_Anchor`, and `prompt3_formulator.txt:194` defines Line 2 as a **single** bullet with `Logic:` ranked above `Delta:` at `:347`.

⚠️ **Two of my own measurements disagreed (94 vs 250 blocks) and I could not reconcile them.** The CASE A hypothesis (DEBT/SUGGESTION three-bullet stacking) was **disconfirmed** — INTENT survives at 37% vs DEBT at 22%. **Parked by ruling. Do not act on the numbers in this ticket without re-deriving them on one canonical parser.**

---

## T9 · Telemetry database hygiene — OPEN

**Opened:** 2026-07-29. **Class:** tooling (`harvest_telemetry`).

`prompt_telemetry_database.txt` holds **590 model-authored issue reports** spanning 2026-05-14 → 07-27, **unread for two months**. It contains 71 duplicate lines and leaked raw payload (`<final_logic_package>`, `[[LOGIC_BLOCK]]`).

🚩 **Its most-repeated entry is a FALSE POSITIVE.** The P3 Tags "purge periods" complaint appears 19 times across 13 videos — but `git log -S` dates the `PRESERVE periods` fix to commit `6d30435` (2026-06-19), **10 of the 13 flagged runs postdate it**, and every checkable run has periods intact. The model reported stripping periods it never stripped.

**Lesson for all future tickets: a telemetry self-report is not evidence of an output defect. Verify the output.**

**Fix direction:** dedupe at harvest, print a top-N recurring digest at pipeline end.

---

## T10 · Root-directory clutter, and why moving anything is not safe yet — OPEN

**Opened:** 2026-07-30. **Class:** project architecture. **Severity:** hygiene, not correctness. **Do not work now.**

**The state:** **104 files in the project root** — 54 `.txt`, 15 `.py`, 14 `.md`, 6 `.bak*`, 15 other. Chief Architect: *"If they all sat in a folder I would not mind, but now everything is linked… I dont want to move anything, as everything is interlinked. not sure what is safe."*

**That caution is correct, and here is the measured blast radius.** Root paths are hard-coded as bare filenames in at least four places, and a move breaks all of them silently:

| Coupling | Detail |
|---|---|
| **Orchestrators** | `run_phase5.py` performs **16** bare-name file operations, `run_phase1.py` **9**, `run_phase4.py` 2, `run_phase3.py` 1. These read and write the pipeline's ~20 working artifacts (`baton_*`, `forensic_*`, `polished_yaml.txt`, `ANKI_IMPORT_READY.txt`, …) by name, relative to CWD |
| **Constitution & docs** | `CLAUDE.md` §IV names nine skill files, `CHANGELOG.md`, `memory/`, `Prompts/`, `config.py`, `run_master.py`, `run_phase*.py`; `medic.md` references `SKILL_SPEC_anki_medic.md` and `MEDIC_TICKETS.md` by bare name; the spec references `MEDIC_TICKETS.md` and `CHANGELOG.md`; tickets cite prompts as `file:line` |
| **Hook** | `.claude/settings.local.json` `cat`s `.claude/preflight_check.txt` on every `UserPromptSubmit`. A missing payload looks identical to a turn where nothing was injected — **no visible symptom** |
| **`.gitignore`** | *(symptom, not cause)* Line 2 is `*`, so every tracked root file exists only via a literal whitelist entry. A subfolder move silently untracks. Real, but the smallest of the four |

### 🚩 The actual problem: root is not a folder, it is the project's addressing scheme

Chief Architect, correcting an earlier framing of this ticket: *"the problem with messy files and folders, no structure is now we are committed to it — if you open any file, it will probably link to root directory. It's not even about git… it has little to do with gitignore and more to do with python scripts, constitution files, references."*

**That is the correct reading.** Every artifact in this project — orchestrator I/O, Constitution clauses, skill cross-references, ticket citations — resolves against the root as an implicit namespace. Nothing declares a base path; the flat layout *is* the path.

**The consequence, and the real reason to defer:** introducing structure is not a file move, it is **renaming the namespace every one of those references depends on.** There is no incremental version. You cannot relocate `polished_yaml.txt` without `run_phase5.py`, cannot relocate a skill without `CLAUDE.md` §IV, cannot relocate the spec without `medic.md`. **A partial migration leaves the project in a state where some references resolve and some silently do not** — and the failures are silent in three of the four coupling classes above.

That is what "we are committed to it" means, and it is a design fact rather than untidiness. The 104-file root is the *visible symptom*; the invisible one is that root-relative addressing is load-bearing in code, in the Constitution, and in every cross-document reference simultaneously.

**Scope of the real fix**, per Chief Architect: *"I should rewrite claude.md, surgeon, commit, hook, etc… probably claude md, compass hook and surgeon and commit skills are enough about root file cleanliness mandate."* A root-cleanliness mandate is not one edit — it needs a coherent design covering:

1. Which root files are **durable** (tracked source, docs) vs **per-run working artifacts** (regenerated every pipeline run, ~20 of them) vs **legacy** (6 `.bak*` files, already documented as deletable in `CLAUDE.md` §IV).
2. Whether working artifacts move to a `work/` or `run/` subfolder — which requires touching `run_phase1/3/4/5.py` and re-verifying **28 bare-name file operations**.
3. `.gitignore` restructuring so a subfolder move does not silently untrack. The current `*`-plus-whitelist pattern actively fights directory structure.
4. Whether a cleanliness rule belongs in `CLAUDE.md` §IV, in `compass.md`, in `surgeon.md`/`commit.md` as a per-phase check, or in the preflight hook. **Routing decision, not yet made.**

**Companion item, cheap and independent:** nothing currently instructs a future session that a *deleted-but-committed* document lives in git history. A session reading T4 and looking for `SCOUT_lapse_forensics_handoff.md` would find it absent with no reason to check `git log --diff-filter=D --name-only`. **Proposed `CLAUDE.md` §IV line drafted 2026-07-30, not written — awaiting approval.** This one can ship without T10.

**Recommendation:** route T10 to the Design Council when the pipeline work resumes, not before. It touches five orchestrators, `.gitignore`, `CLAUDE.md`, and up to four skills — exactly the kind of cross-cutting refactor that needs parallel red-teaming rather than a single pass. Constitution 2 is satisfied by the named, twice-realised failure pattern (silent untracking), so this is not elegance-driven.

---

## T11 · 538 notes carry content invisible at render — remediation, not prevention — OPEN, ✅ PREMISE CONFIRMED

> ✅ **CONFIRMED 2026-08-01 on a live card** — see T5. The content is invisible on the card *and* in the editor, so it has never been seen. **Count corrected: 538 notes** carry the `</TAG …>` syntax in `Extra` (`</🧸` 537 · `</🚀` 520 · `</🎓` 392 · `</⚙️` 357), not the 358 originally estimated — that figure counted only notes with a wrapper *plus* a trailing raw `>`.
>
> ✅ **Nothing needs recovering from backup.** Every block is intact in `notes.flds`; only rendering fails. Remediation is a **delimiter change**, not a content rescue, which makes it far cheaper and fully reversible.
>
> ⚠️ **Try the template-only fix FIRST — it may make this ticket unnecessary.** See T25. If `{{Extra}}` is moved inside `<script type="text/template">` and read with `.textContent`, the browser never parses the field as HTML, the existing engine receives its input intact, and **all 538 notes are fixed with zero data changes, legacy included.** Only if that fails is a 538-note migration warranted.

**Opened:** 2026-07-30 (`/medic` run 1). **Class:** collection data. **Severity:** high.

T5 stops the pipeline **generating** malformed `</emoji …>` wrappers. This ticket covers the notes that **already have them** — a data migration, not a prompt fix, and a different owner.

**Scope:** 2,141 wrappers across **358 notes**. Every 🚀 mnemonic, 🧸 ELI5, ⚙️ Association and 🎓 line inside a wrapper has **never been displayed to the Chief Architect**, on any review, ever.

### Full defect census — measured 2026-07-31 by running AIRLOCK over the whole deck

6,130 populated `Basic+` fields scanned; **688 flagged**. Counts are *fields*, not notes or occurrences, so they sit between the per-note figure (358) and the per-occurrence figure (2,141):

| Defect | Fields | Destroys content? |
|---|---|---|
| Malformed `</` + non-letter wrapper | **538** | **Yes** — swallows to the next `>` |
| Stray unescaped `>` | **187** | **Yes** — terminates the `innerHTML` parse |
| `->` not converted to `→` | 176 | No — cosmetic only |
| `=>` not converted to `⇒` | 3 | No — cosmetic |

**Remediate the first two; the arrows are not worth an import on their own** — fold them in only if a migration is already touching the note. **AIRLOCK itself was validated in the same pass:** its wrapper and stray-`>` detection matched an independently computed ground truth exactly (538/538, 187/187), it correctly ignored the escaped `&gt;` false-positive case, and it passed all 120 fields emitted by both 2026-07-31 patches. The detector is trustworthy; the backlog is what needs work.

### 🚩 This is a SECOND, independent invisibility mechanism

The `data-simple="1"` flag already fixed (which hid `Extra` on 1,310 notes) was mechanism one. Turning that flag off revealed the *field* — it did **not** reveal content sitting inside a bogus-comment wrapper. The two stack. A note can pass the `data-simple` fix and still show nothing.

### Consequence for `/medic` itself — this one bites the skill

**A card can look tool-saturated in the database and be bare on screen.** Step 5's *"skip if a same-class marker is already present"* reads the database, so it will skip a card whose marker has never rendered.

Run 1 hit this live: `q}A$}rAxk%` (Standard Ports: SNMP, 25/59 = 42% again, the worst Class G card in the collection) already carries a 🚀 mnemonic, a 🧸 ELI5 and an ⚙️ Association — **all three swallowed**. Adding a fourth tool on top of three the user has never seen would be Addition Bias, so the phonetic separator was **withheld**. Until T11 is remediated, `/medic` cannot tell "already treated" from "treated but invisible."

**Recommendation:** remediate before the next `/medic` run acts on any card whose Extra contains `</`. Re-measure SNMP afterwards — its 39% again-rate may partly be a rendering artifact rather than a knowledge gap.

---

## T12 · Class G — SNMP/SMTP is the collection's worst acronym collision — OPEN

**Opened:** 2026-07-30 (`/medic` run 1). **Class:** card construction / learner-confusability. **Source:** Chief-Architect hypothesis, independently confirmed by measurement.

Chief Architect, unprompted, in a `Medic_Notes` annotation on `D#3g|gsjxO`:

> *"can you pattern match before I even realize why i fail? for example, user seems to fail at SNMP and SMTP, maybe user thinks theyre the same thing. DONT LAUGH, but for a long time I actually did, when I first started learning ports (they look the same, I skimmed during reviews and did not register with me the difference in spelling)"*

**The hypothesis is correct.** Measured lifetime, `type IN (0,1,2)`:

| Term | Again / reviews | Rate |
|---|---|---|
| **SNMP** | 67 / 173 | **39%** |
| **SMTP** | 49 / 176 | 28% |
| Basic+ baseline | 4141 / 17457 | 23.7% |
| Collection baseline | 15302 / 78537 | 19.5% |

Worst cards: `q}A$}rAxk%` ord0 **25/59 (42%)**, ord1 **18/38 (47%)**. Both tagged `leech`.

Across an 18-pair confusability sweep (same length, same first and last letter, ≤2 substitutions) **SNMP/SMTP shows the largest deviation from baseline of any pair in the collection**. Runners-up are benign: IMEI/IMSI both sit at 21%, PDU/PSU at 20/18%.

⚠️ **A naive anagram or 1-edit scan MISSES this pair.** `SNMP`→`SMTP` is a transposition-plus-substitution (2 positions differ), so it fails both an anagram test and a Levenshtein-1 test. The first scan in run 1 missed it for exactly that reason. Any future confusability scan must use the *same-length + same-first-and-last-letter + ≤2 substitutions* heuristic.

**Not patched in run 1** — blocked on T11 (the target card's three existing mnemonics are invisible). Tool when unblocked: 🚀 Phonetic separator. Candidate encoding, held for a future run: SNMP ≈ **SNooP** (watches the **N**etwork) vs SMTP ≈ **STaMP** (sends the **M**ail) — the sound-alike carries the discriminating middle letter.

---

## T13 · Class H — RADIUS_TACACS is the worst MATURE cluster in the collection — OPEN

**Opened:** 2026-07-30 (`/medic` run 1). **Class:** unclassified — measurement only. **Status:** deliberately undiagnosed.

Own-initiative cross-run scan. **78 Again / 191 reviews = 41%**, 9 cards, import batch 2026-04-10 (~3.5 months of review history). Against a 23.7% Basic+ baseline this is the highest-volume mature offender in the deck, and it appears in **no existing ticket**.

Per-card:

| Card | ord0 | ord1 |
|---|---|---|
| `RADIUS (Expansion)?` → Remote Authentication Dial-In User Service | **24/42 (57%)** | — |
| `TACACS (Expansion)?` → Terminal Access Controller Access-Control System | **13/34 (38%)** | — |
| RADIUS vs TACACS+ — deployment use | 9/20 | — |
| Centralized AAA protocol → RADIUS | 9/26 | 4/12 |
| RADIUS vs TACACS+ — transport | 6/16 | — |
| Enterprise AAA for privileged admin → TACACS+ | 6/16 | 3/13 |
| RADIUS vs TACACS+ — AAA phase handling | 4/12 | — |

🚫 **NOT diagnosed, and that is deliberate.** Step 3 says *"Class H is measurement, not prediction"* and supplies one discriminator: group the again-rate **by import batch** — consistent across batches = knowledge gap, variable = card construction. **This cluster exists in a single batch, so the discriminator cannot be run.** Guessing which it is would be prediction. For contrast, `POE_SYSTEM` spans two batches (36% / 29% ≈ consistent → knowledge gap) and *is* diagnosable.

**Fix direction:** none proposed. The two `(Expansion)?` cards carrying the worst rates suggests raw acronym-expansion recall rather than cue collision, but that is a hypothesis, not a finding. Needs a second import batch, or an explicit Chief-Architect ruling to treat single-batch clusters as knowledge gaps by default.

---

## T14 · Compound Backs mask partial knowledge — atomicity, not repairability — OPEN

**Opened:** 2026-07-30 (`/medic` run 1). **Class:** pipeline (P3 card construction). **Severity:** low-confidence, accumulating.

Raised by `medic.md` §2f, which routes this to a ticket rather than a repair tool.

**Datapoint 1** — `z~<Y?FaJp<`, `📌🆖 802.11n (Max Speed / Frequency Bands / Wi-Fi Name)?` → `~600 Mbps | Dual-band (2.4 GHz & 5 GHz) | Wi-Fi 4`. Three values behind one grade. Chief Architect:

> *"I answered correctly wifi 4 but got the speed wrong, 480mbps, was thinking of usb speeds :)). anyway, should we act on this types of reviews where I got the answer wrong? **dont lean towards it.**"*

Two of three values retrieved; Anki records a single Again. The card reads as a failure while the knowledge is ~67% present. **Correctly handled as Class J — no patch.** Recorded here because the *construction* is the issue: a compound Back gives no per-value signal, so neither Anki nor `/medic` can see which third is missing.

**Do not act on one datapoint.** Logged so it accumulates rather than being rediscovered each run — the same discipline as T6. If a second and third compound-Back card produce the same pattern, the finding is that P3 should split multi-value Backs into atoms, and the ticket becomes actionable.

⚠️ Explicitly **not** a licence to atomise the deck. The Chief Architect's *"dont lean towards it"* governs: partial knowledge is not a defect, and treating it as one would inflate the patch rate against real failures.

---

## T15 · Deck-wide collision hunter — a specialised API call, NOT another prompt tweak — OPEN

**Raised** 2026-07-30 (annotation on `m;;#)IS.jH`, ledger rows 151–158). **Chief-Architect ruling attached.**

> *"one suggestion I will throw in there for the ticket is to add an api call, sort of prompt 7 with only job to hunt and fix issues like this, look at WHOLE deck and see if two or more cards point to more answers or if confusing, etc. …**no more prompt tweaking, because we did that and still nothing. a specialized API call would be more efficient imo.**"*

**The defect that raised it, verified 2026-07-31.** `m;;#)IS.jH` reverse: *"CLI-only remote management protocol for Layer 2 and Layer 3 network infrastructure hardware (Protocol name)?"* → **Telnet**. SSH is also CLI-only and also manages L2/L3 hardware; the real discriminator (Telnet is unencrypted) appears nowhere in the cue. The **forward is fine** — it names Telnet, so no rival is possible. Reverse 3/11 again vs forward 2/9. The Chief Architect's own hedge — *"maybe I am wrong and reverse card is correct"* — was half right, and the half that was right is the half that matters: **the defect is reverse-only**, which is also why the P5 veto gate never caught it (T3).

**Why this is not a `/medic` job.** `/medic` is reactive — it sees a card only after a failure or an annotation. A cue that admits two answers is defective **before anyone reviews it**, and finding it requires reading the whole deck at once, not one card at a time. Different trigger, different scope, different tool.

**Scope when it is built.** Whole-deck sweep for fronts that admit more than one answer within their own tag cluster. Cross-check candidate rivals by asking whether the rival's Back satisfies the cue on its merits — the Class A test, applied deck-wide instead of per-failure.

**⚠️ Routing.** Prompt design is Chat-shaped work (CLAUDE.md §II) and the ruling above forbids more prompt tweaking regardless. This ticket is a **design brief for a new API call**, not an edit to `prompt5_exporter.txt`. Do not route it into a prompt revision.

**Blocked on:** nothing technical. Needs a Chief-Architect decision on whether it runs as a P7 stage or an on-demand sweep.

---

## T16 · `Basic+` stylesheet blocks three tools — ✅ CLOSED 2026-08-01

> ✅ **Closed.** An additive CSS block was pasted into the note type's Styling box and confirmed rendering on a live card (IPv4 Octet). `.card` untouched, so nothing existing changed appearance. ⚠️ **It styles collapsibles; it does not create them** — see T25, where the deck turns out to split into 538 notes the CSS reaches and 825 it cannot.

**Raised** 2026-07-30, still unwritten as of 2026-07-31. The `Basic+` stylesheet is **761 chars with a single selector (`.card`)**. `details`, `summary`, `table` and `.extra-container` are entirely unstyled, so uncollapsed content renders at 36px centred.

**What it blocks, right now:**

| Tool | State |
|---|---|
| 🔄 Collapsible | unusable |
| 📊 Matrix recovery | degraded to plain-text short form |
| 🩺 Explainer | degraded — the 5-part structure is unreadable uncollapsed |

**Class E therefore has no full-strength tool**, and runs must emit `Class E degraded — CSS pending`. The Chief Architect asked for exactly this capability by name: *"look at formatting of this table, its perfect for comparisons like this where it gets confusing and putting them site by side is ideal"* (ledger row 118).

**Fix:** a CSS block pasted into the note type's styling — `details`/`summary` affordances, `table` borders and padding, left-aligned `.extra-container`. Not a code change; a paste into Anki's card-template editor. **Nothing else in the ledger is blocked on so little work.**

---

## T17 · `rH8ZgpH>:E` reverse — delete candidate, not a repair candidate — OPEN

**Chief-Architect verdict, typed into the card's own `Inverse_Question` field:**

> *"THIS IS A VERY BAD REVERSE, DONT EVEN THINK THIS NEEDS A REVERSE ANYWAY."*

**State, verified 2026-07-31:** ord1 at **13 Again / 14 reviews (93%)**, `queue = -1` (already hand-suspended), interval 0. The forward (`Cloud service models (Main members)?` → IaaS/PaaS/SaaS) is healthy at 2/7.

**Why it is not a `/medic` repair.** No tool applies. The cue — *"the umbrella category for the tiers that split stack management between provider and customer"* — asks the Chief Architect to name a category label they have no reason to hold as a retrievable fact. Patching it would be repairing a card that should not exist, which is Addition Bias with extra steps.

**Also note where the verdict was written.** It sat in `Inverse_Question`, a field `/medic` did not scan until 2026-07-31 (MEDIC-21) — and because that field renders, the complaint was being displayed on the card during review.

**Decision needed:** delete the reverse, or leave it suspended. Leaving it suspended is free; deleting removes it from future veto-gate and collision sweeps.

---

## T18 · `/medic` now has an addon dependency — AnkiConnect — OPEN

🚩 **SEVERITY RAISED 2026-08-01 — this is no longer a *second* channel, it is the ONLY one.** The manual patch file was retired, so **every** change now routes through AnkiConnect (addon `2055492159`, `127.0.0.1:8765`): field text (`updateNoteFields`), tags (`addTags`), plus the original 🗑️ suspend, ⏱️ Align (`setDueDate`) and ⏱️ Reset (`forgetCards`). The run also **launches Anki and calls `sync`** before snapshotting. If the addon is unavailable, `/medic` can no longer change anything at all — where previously it could still emit a file.

**The dependency is soft but silent.** If Anki is closed, the addon is disabled, or the port changes, those tools stop working — and the failure mode is a skipped proposal, not an error. The skill mandates a probe and a tag-based fallback, but **the fallback only exists for suspend**; adjacency and reset have no non-API route, because the import format has no card-state column.

**Watch for:** an Anki update disabling the addon (it pins point versions), or a run that silently reports "none proposed" when it should have proposed scheduling changes. **Mitigation if it ever bites:** the tag handoff generalises — `medic::adjacent::<date>` plus a manual `Ctrl+Shift+D` reproduces Align by hand.

---

## T19 · SNMP/SMTP again-rates did not reconcile — ✅ RESOLVED 2026-07-31 (run 3)

> ✅ **Resolved against my own figures.** Run 3 re-measured on one documented scope — term present in **`Front` or `Back` only** — and got **SNMP 39% · SMTP 33%**, reproducing run 1 and refuting the 42% / 34% logged earlier that day. The bad method was `flds LIKE '%SMTP%'` across all six fields, which counts notes that merely *mention* the term in a `⚠️ NOT:` line or a `Logic:` bullet. **The Front/Back scope is now a fatal precondition in `medic.md` (4b).** T12's claim survives on the corrected numbers. Original discrepancy retained below.

Precondition 4 requires reporting a disagreement rather than picking a side. Two measurements of the same quantity, two days apart:

| Term | 2026-07-30 (run 1) | 2026-07-31 (this session) |
|---|---|---|
| SNMP | 67 again / 173 reviews = **39%** | 81 / 190 = **42%** |
| SMTP | 49 / 176 = **28%** | 81 / 236 = **34%** |
| Basic+ baseline | 4141 / 17457 = 23.7% | 4146 / 17502 = 23% |

**The baseline moved by 45 reviews — plausible for two days. SMTP moved by 60, and gained 32 Again presses.** That cannot be two days of reviews on a deck averaging ~60 reviews/day total. The two scans almost certainly scoped differently — run 1 counted per-card within a card list, this one matched `flds LIKE '%SMTP%'` across all six fields, which also catches notes that merely *mention* the term in a NOT-section or Logic line. **The direction of the finding survives** (both scans put SNMP well above baseline and above SMTP, which is T12's claim); the magnitudes do not.

**Do not quote either figure as fact.** Before T12 is acted on, re-measure once with a single documented scope — cards whose **Front or Back** carries the term, not any field — and record the method alongside the number. Fifth measurement discrepancy of the 2026-07-30/31 sessions; see `scout.md` measurement hygiene.

### ✅ RESOLVED 2026-07-31 (`/medic` run 3) — ready to close

Re-measured exactly as this ticket instructed, on one documented scope.

**Method, stated so it can be reproduced or refuted:** notetype `Basic+` only; for each *card*, the term is matched against **that card's own side** — `Front`+`Back` for `ord 0`, `Inverse_Question`+`Inverse_Answer` for `ord 1` — over HTML-stripped text; `revlog` restricted to `type IN (0,1,2)`; one parser shared with every other figure in this run.

| Term | Again / reviews | Rate |
|---|---|---|
| **SNMP** | 64 / 166 | **39%** |
| **SMTP** | 57 / 171 | **33%** |
| Basic+ baseline | 4146 / 17502 | 23.7% |

**This reproduces run 1 (39% / 28%) and refutes the 2026-07-31 figures (42% / 34%).** The diagnosis in the ticket was right: `flds LIKE '%SMTP%'` matched notes that merely *mention* SMTP in a NOT-section or Logic line — including the whole email cluster — inflating both numerator and denominator. **Use 39% / 33%.** T12's claim stands on the corrected numbers: SNMP sits **15 points above baseline**, SMTP 9 points above.

---

## T20 · `n;KV9(m.}?` — 29 Again out of 29 reviews. The worst card in the collection, and it is in no ticket — OPEN

**Opened:** 2026-07-31 (`/medic` run 3, own-initiative Class H scan). **Class:** card construction. **Severity:** high.

Found by the mandated cross-run sweep, not by any annotation. **`SERVER_PORT_LISTENING` is the worst cluster in the deck at 35/57 = 61%** — and one card supplies 29 of those 35.

| | |
|---|---|
| Front | *"📌🚪 A TCP SYN arrives at a web server's port 80, but no service process is bound to that port. What does the server return?"* |
| Back | **TCP RST** |
| Record | **29 Again / 29 reviews = 100%.** Ease histogram `{1: 29, 2: 0, 3: 0, 4: 0}` |
| Life | first review 2026-04-30, last 2026-05-06, then `queue = -1` — hand-suspended |

**Never answered correctly. Not once, in 29 attempts, across seven days.** The Chief Architect then suspended it by hand — the same vote recorded in T17, cast with the only control AnkiWeb offers.

**Why no patch.** A card at 100% for 29 straight reviews is not a cue defect a `⚠️ NOT:` line repairs; nothing in the toolkit moves a number like that, and the card is suspended so no repair could even be seen. Step 4b's escalation rule applies by analogy: repeated failure of the same card is a **card-design failure**, and the ruling belongs to the Chief Architect, not to a repair tool. Patching it would be Addition Bias.

**The other three cards in the cluster are healthy** (4/15, 2/9, 0/4), which is the useful part of the finding: the cluster is not a knowledge gap, it is one broken card dragging a 61% rate.

**Decision needed:** delete, rewrite from the source transcript, or leave suspended. Same shape as T17 — and the two should probably be decided together.

---

## T21 · Class G — three new confusable pairs above baseline — OPEN

**Opened:** 2026-07-31 (`/medic` run 3, mandated Class G sweep). **Class:** learner-confusability.

Swept with the T12-mandated heuristic (*same length + same first and last letter + ≤2 substitutions*), scoped to **Front+Back of the card's own side** — 136 terms with ≥25 reviews, 22 candidate pairs. Baseline 23.7%.

| Pair | Rates | Note |
|---|---|---|
| **WSXGA / WUXGA** | **36% / 36%** (22/61 each) | Identical rates on identical review counts. Display-resolution acronyms differing by one letter |
| **LDAP / LLDP** | 32% / 35% | Transposition-shaped, both above baseline |
| **ACPI / AHCI** | 32% / 27% | Both above baseline |
| SNMP / SMTP | 39% / 33% | **already T12** — reconfirmed, see T19 below |

⚠️ **Two apparent pairs are ARTEFACTS, do not chase them.** `SDN/SYN` and `SAN/SYN` show 100% on the `SYN` side purely because `SYN` appears almost entirely on **T20's single broken card** (29/29). That is one defective card, not an acronym collision. RAID/RFID (24%/25%) is inside noise of the 23.7% baseline.

**Not patched.** T12's phonetic separator is still blocked on T11, and the same reasoning applies here — adding a mnemonic to a card whose existing mnemonics may be invisible is untestable. Recorded to accumulate.

---

## T22 · The annotation watermark UNDER-triggers — ✅ FIXED 2026-07-31 (MEDIC-39)

> ✅ **Fixed by subtraction: the annotation trigger now has no date filter at all.** The watermark gates only the three review triggers. **Existence is the unprocessed flag** — Step 8 clears every annotation it processes, so anything still present is by definition unhandled. A stale annotation costs one re-read; a missed one costs the Chief Architect's feedback entirely. Diagnosis below stands as the record of how it was found.

**Opened:** 2026-07-31 (`/medic` run 3). **Class:** skill logic (`medic.md` Step 1). **Severity:** high — silent, and it already fired.

**MEDIC-32 fixed over-triggering** (importing a patch bumps `notes.mod`, so every run re-fired its own notes). **This is the same clock failing in the opposite direction, and nothing guards it.**

The Step 1 annotation trigger requires `notes.mod` newer than the watermark. The watermark advances to **run completion**. So any annotation that a run *reads but does not clear* is stamped older than the watermark the moment that run finishes — and **no future run can ever see it again**.

**It already happened.** Run 2 (2026-07-31 00:23) read four annotations across three notes, dispositioned all of them in `MEDIC_FEEDBACK_LEDGER.md` rows 125–159, wrote skill edits and tickets from them — and **emitted no patch row**, so the fields stayed live. Run 3's `mod > watermark` query returned **zero of them**. They were recovered only because the collection-wide shape scan runs independently of the watermark.

Ledger row 125 reads, in the Chief Architect's words, *"for the next `/medic` run"* — an explicit handoff that the trigger design guaranteed would be missed.

**Fix direction (not executed — skill edits are a Surgeon-phase action):** the durable signal is *"an annotation exists and carries no `medic::cleared::` tag newer than it"*, not *"the timestamp moved"*. That is content-based in the same spirit as MEDIC-32's fix, and it cannot drift. **A run must not advance the watermark past an annotation it did not clear.**

---

## T23 · `medic::run::<date>` cannot distinguish two runs on one day — ✅ FIXED 2026-07-31 (MEDIC-44)

> ✅ **Fixed.** The run tag now carries a time — `medic::run::YYYY-MM-DD-HHMM`. Date-only tags are read as legacy and the maximum is taken. Compounding with T22 is moot now that the watermark no longer gates annotations at all.

**Opened:** 2026-07-31. **Class:** skill logic. **Severity:** low, but it corrupts the watermark's meaning.

Run 2 and run 3 both fall on 2026-07-31, so both write the identical tag `medic::run::2026-07-31`. The watermark is therefore **not a per-run marker but a per-day one**, and a same-day second run cannot compute a correct floor from it. Compounding with T22, a run can silently inherit the previous run's window.

Cheap fix: append a sequence or time (`medic::run::2026-07-31b` / `::2026-07-31T1204`). Recorded, not executed.

---

## T24 · Junk carry-forward — one `proposed` note never suspended, four `partial` notes never resolved — OPEN

**Opened:** 2026-07-31 (`/medic` run 3). **Class:** workflow follow-through.

Live state of the 11 notes tagged by run 2, verified against the collection this run:

| Tag | Cards suspended | Cards still live |
|---|---|---|
| `medic::junk::proposed` | 10 | **2** |
| `medic::junk::partial` | 0 | 8 |

- **`Qm>3{4O>Gn` is tagged `medic::junk::proposed` and both its cards are still live** — every other `proposed` note was suspended. Either the approved `suspend` call missed it or it was deliberately spared. ⚠️ Worth a second look before acting: its content is *"📌 SMTP (Default TCP Port)? → Port 25"* and the reverse *"📌 Port 25 (Assigned protocol)? → SMTP"*, which reads as a core exam fact rather than junk. **Not re-proposed for suspension by this run** — a `proposed` tag whose card looks legitimate is exactly the case that needs a human, not a bulk action.
- **The four `partial` notes** (`QvRJkif@e6`, `BU[oB7jhr!`, `kKo/V%8vR0`, `r:PGT.t]ZD`, 8 cards) are correctly unsuspended — `partial` is never bulk-suspended by design. But the skill requires the junk `ord` to be **named in the run summary** so the Chief Architect can decide card-by-card, and that decision has not been recorded anywhere. They will sit here until it is.

---

## 🚩 T5 / T11 / T25 — MAJOR CORRECTION 2026-08-01: `</emoji …>` is DELIBERATE SYNTAX, not malformed markup

**The `Basic+` card template already contains a collapsible engine.** Reading it for the first time on 2026-08-01 (it had never been read — only the stylesheet had):

```js
// Inline collapsibles
s = s.replace(/<\/([^\s>]+)\s+([^>]+)>/g, function(_, tag, content){
  return '<label class="inline-toggle"><input type="checkbox" class="toggle-input" />'
    + '<span class="toggle-summary">' + tag + '</span>'
    + '<span class="toggle-inner">' + content.trim() + '</span></label>'; });
```

`</🚀 Major System: …>` is **the pipeline's intended micro-syntax for an inline toggle**, converted at render time into a checkbox. Used on **538 notes** — `</🧸` 537 · `</🚀` 520 · `</🎓` 392 · `</⚙️` 357. T5 called this "AIRLOCK not enforced upstream" and T11 called it "swallowed content"; **both were diagnosing a designed feature as a defect.**

**Every class the engine emits is unstyled.** Verified against the note type config: `.inline-toggle` · `.toggle-input` · `.toggle-summary` · `.toggle-inner` · `.card-details` · `.card-summary` · `.card-details-inner` · `.foreground-hidden` · `.extra-field` · `.qa-container` · `.answer-field` — **all eleven, no CSS.** The stylesheet was 672 chars containing only `.card`. So the toggle renders as a raw checkbox with its body **not hidden**, because nothing sets `display:none` on `.toggle-inner`.

**The `<<collapsible:Title>>` block form is emitted by 0 notes** — a dead path in the template.

❓ **UNRESOLVED PREMISE — needs the Chief Architect's eyes, one card.** Two possibilities, and they demand different fixes:
- **(A)** The browser parses `</🚀` as a bogus comment *before* the JS reads `innerHTML`, so the content never reaches the engine → genuinely invisible, T11 stands in substance.
- **(B)** It survives to the JS, gets converted, and renders **fully expanded plus a stray checkbox** because `.toggle-inner` has no `display:none` → nothing is lost, it just looks like noise.

**Open `q}A$}rAxk%` (Standard Ports: SNMP) and report what appears where the 🚀 mnemonic should be.** A checkbox and visible text ⇒ (B), CSS alone fixes it. Nothing at all ⇒ (A), the parse must be fixed too. **Do not act on T5 or T11 until this is settled.**

**Reinvention catch:** T25 originally proposed writing template JavaScript to wrap `Extra` elements. That JS already existed. `CLAUDE.md` §II — *"am I COPYING the baseline, or REINVENTING it?"* — caught only because the template was finally read instead of assumed.

---

## T25 · Collapse every `Extra`/`Back` element by default — TWO populations, TWO fixes — OPEN

**Raised** 2026-08-01, after T16's stylesheet shipped and the Chief Architect saw a working collapsible for the first time.

> *"I think we should collapse everything in extra. For one reason, I want to focus on the answer, and then reveal stuff gradually… sometimes it's just a wall of text, I don't know where my eyes should jump, especially when I'm quick reviewing… the answer is PKI, and my eyes are trying to look for the answer, but instead I'm met with all the explainers."*

### The deck splits cleanly in two, and each half needs a different fix

Measured 2026-08-01 across 1,363 notes with a non-empty `Extra` — the two sets are **disjoint**:

| Population | Count | What it needs |
|---|---|---|
| `Extra` uses the template's `</TAG …>` inline syntax | **538** | **CSS only.** The engine already converts these to checkbox toggles; all 11 of its classes were simply unstyled |
| `Extra` is **plain text** (`⚠️ NOT: …`, `Logic: …`) | **825** | **New template JS.** No element exists to style — one must be created at render time |

⚠️ **Both are required. Neither alone is sufficient**, and each of my first two answers claimed exactly one of them was the whole story:

- **First answer — "template JS, not CSS":** wrong for the 538, whose engine already existed. Reinvention Bias (`CLAUDE.md` §II) — the template had never been read, only the stylesheet.
- **Second answer — "no JavaScript, style the engine you already have":** **wrong for the 825, which is 60% of the deck.** Caught by the Chief Architect pasting a card that did not collapse: `o]YYXi,E)(`, whose `Extra` is the plain string `⚠️ NOT: Treating them as identical mechanisms…`. Verified — no `</TAG>` syntax in either `Extra` or `Back`.

**The lesson for whoever finishes this: measure the population before choosing the instrument.** Both wrong answers came from generalising a real finding across a deck that is not homogeneous.

### It spans `Back`, not just `Extra`

The same card's `Logic:` line lives in the **`Back`** field. Any solution keyed only on `Extra` leaves half the wall of text standing. Both templates (`Forward` and `Card 2`) run the same `renderContent()` and both need the change.

### Marker census (block-leading, in `Extra`)

| Marker | Blocks | | Marker | Blocks |
|---|---|---|---|---|
| 💡 | 661 | | 📘 | 73 |
| 🧠 | 661 | | `Analogy:` | 24 |
| 🔍 | 493 | | 👁️ | 20 |
| ⚠️ | 429 | | 🪝 | 14 |
| 🌄 | 167 | | `Example:` | 11 |
| 🔄 | 155 | | 📊 | 10 |
| `Logic:` | 75 | | `Delta:` · `Forensic:` | 6 · 7 |

⚠️ **📊 Matrix is not its own block.** It is appended *inside* the `⚠️ NOT:` block, which is why Matrix stayed visible while Refresher collapsed. A wrapper keyed on `<br><br>` boundaries will miss it — Matrix needs an **inline** split. Still unsolved. **2,648 blocks carry no marker at all**; most are continuation lines that belong with the block above them, which is why the proposed JS appends unmarked segments to the preceding `<details>` rather than leaving them loose.

### Status

**Drafted and handed to the Chief Architect 2026-08-01**, not yet confirmed on a live card: a marker-split block inserted into `renderContent()` immediately above `return s.replace(/(<br>\s*)+$/, '');` in **both** back templates, guarded by `if (!/<\/[^A-Za-z\/][^>]*>/.test(s))` so the 538 `</TAG>` notes are skipped and nothing double-wraps. Everything before the first marker stays visible — **the answer never hides**, which was the whole point of the request.

**Close this ticket only when:** a plain-text card (`o]YYXi,E)(`) shows collapsed `Logic` and `⚠️ NOT` toggles, a `</TAG>` card (`q}A$}rAxk%`) still renders correctly, and the 📊 Matrix inline case is either solved or explicitly deferred to its own ticket.

**Depends on the T5/T11 premise question above** — if `</🚀` never survives the HTML parse, the 538 population needs a parse fix before any of this matters.

---

## T26 · Cards test acronyms the Chief Architect has never been taught — OPEN

**Raised** 2026-08-01, on a freshly imported batch. **Class:** pipeline (front construction) + card repair. **Severity:** high — it makes cards unanswerable for a reason that has nothing to do with the fact being tested.

> *"It's asking me all these acronyms, this versus that, but I don't know what they all mean… I know what bring your own device means, it's kind of logical. But CYOD, COPE — until I learn them, I need a helping thing… Assume I don't know, even if it's not on the objectives list. This is jargon for me, so I have to Google it."*

Observed on `🔤 CYOD (Selection method)?`, `MDM (Main job)?`, and `Mobile deployment models (Named types)?` → *"BYOD, CYOD, and COPE."* The card asks for a property of a thing whose **name** is still opaque, so the failure is vocabulary, not knowledge.

### 🚫 The exception that defines the rule

**Acronym-expansion cards get NO help, ever.** `TOTP (Expansion)?` exists precisely to test the expansion — glossing it destroys the card. *"That's the whole point of getting tested on the acronym. So, no helping there."* Any implementation must detect and skip these; the `🏷️` marker and the `(Expansion)?` qualifier both identify them.

### Mechanism — settled 2026-08-01, inline gloss

`<details>`/`<summary>` are **block** elements and force a line break, which mangles a cue. The gloss must be **inline**, so it uses the `<label>`+`<span>` pattern already proven in this collection:

```html
🔤 <label class="acro"><input type="checkbox" class="ax"><span class="an">CYOD</span><span class="av"> (Choose Your Own Device)</span></label> (Selection method)?
```

⚠️ **No `id` attribute — deliberately.** An earlier draft used `id="acro-cyod"` with `for=`, which breaks the moment the same acronym is glossed on more than one card: **duplicate IDs in a document make the label→input binding undefined**, and this ticket now mandates glossing *every* card carrying the acronym. Wrapping the input inside the `<label>` binds them implicitly, so no id exists to collide. The input, `.an` and `.av` stay siblings, which is what the `~` selector needs.

Collapsed it reads `🔤 CYOD (Selection method)?` on one line, with the acronym dotted-underlined; expanded, the gloss appears in place. **This works only because the Front template is bare `{{Front}}` with no JavaScript**, so raw HTML in the field renders directly — the `</TAG …>` syntax and its engine are irrelevant here. CSS classes `.acro .an .av .ax` added to the `Basic+` stylesheet the same day.

### 🎯 What this ticket is actually for — read this before the rules

**The goal is to remove JARGON as a barrier to answering.** Nothing more, nothing less. A card should fail because the Chief Architect doesn't know the *fact*, never because they don't know what the *letters* stand for.

> *"Any acronym that is jargon for me. So we need to clarify jargon."*

🚫 **The CompTIA objectives list is IRRELEVANT to this decision.** Whether a term is examinable has no bearing on whether it is opaque to the reader. *"It doesn't matter if it's on the CompTIA objectives list."*

🚫 **"The lecture explained it" is not a defence.** Exposure is not retention. *"Maybe the lecture explained it in the video. But that happened two days ago and I forgot what COPE means."* A gloss costs one click and nothing else; assuming prior knowledge costs a failed card and a Google search.

### 🚩 Scope: EVERY card gets the gloss. Once per card, not once per deck.

> *"I want every single card that has that acronym explained."*

**Gloss the acronym on every front where it appears** — a card met in isolation cannot borrow a gloss from a sibling weeks away.

**Two different rules. Conflating them stalled two separate `/medic` runs — state them separately, always:**

| Situation | Rule |
|---|---|
| **The SAME acronym twice in one front** | Gloss the **first occurrence only.** *"What happens during **MDM** enrollment that gives the MDM server control…"* → one gloss; the second `MDM` stays plain text |
| **DIFFERENT acronyms in one front** | Gloss **every one of them.** *"BYOD (When to specify instead of **CYOD** or **COPE**)?"* → each chosen acronym gets its own independent gloss |

> *"What do we do when we have two acronyms in the same [front]? We have to expand and explain **both**."*

📌 **Extended 08 Aug 2026 from fronts to backs.** Both rules above still hold verbatim; they now apply across a whole card side rather than the front alone. **The authoritative version is the four-case table in "The universal sweep" below** — read that one, not this one, when implementing.

⚠️ **This section has now been rewritten twice for the same underlying reason.** Version 1 said *"one gloss per front, first occurrence only"* — ambiguous between per-card and per-deck. Version 2 said *"within a single front, gloss only the first occurrence"* — ambiguous between *first repeat of one acronym* and *first acronym in the front*. **Both were correct in intent; both stopped a `/medic` run mid-task.** A rule with two readings is not caught, it is *interpreted*. **A table of explicit cases beats a sentence that is merely accurate.**

### 🚩 Ask before patching. Not every acronym needs help.

**[SUPERSEDED 08 Aug 2026 — see "The universal sweep" below. Kept because it is why the live cards look curated.]** The pipeline no longer curates: *"Do a universal sweep. Do not waste time trying to curate or guess what I already know. If the clickable expansion is there and I already know it, it doesn't bother me."* The paragraph below still describes the **9 notes glossed by `/medic` on 2026-08-01**, which is why `BYOD` sits bare on one front while `CYOD` and `COPE` beside it are glossed.

> *"First, ask me before you patch anything — ask me which acronyms I need help with."*

BYOD is self-evident to this learner; CYOD and COPE are not. **The list is a Chief-Architect decision, never inferred.** A `/medic` run proposes the candidates and waits.

🚫 **TWO questions per acronym, not one. They are independent and both answers matter:**

> *"I need to be asked. **Would you like to be tested on this?** Number one. Number two. **Would you like to have it explained?**"*

| # | Question | If yes |
|---|---|---|
| **1** | *Do you want to be **tested** on this expansion?* | **[SUPERSEDED 08 Aug 2026 — answered NO, globally.]** Standalone acronym cards are being removed from P2 altogether: *"I am completely getting rid of standalone acronym flashcards in Prompt 2… Because I will no longer be tested explicitly on what acronyms mean, there is no 'answer' to spoil."* Question 1 no longer gets asked per-acronym |
| **2** | *Do you want it **explained** on the fronts that use it?* | Apply the inline gloss per the scope table above. **Now answered YES, universally, by the pipeline** — see below |

**Both can be yes.** They are not alternatives: a card that tests the expansion lives in its own right, while the gloss removes the vocabulary barrier from every *other* card that merely uses the term. **Both can be no** — then the acronym is left alone entirely.

⚠️ **Ask question 1 even when no expansion card exists** — especially then. Measured 2026-08-01: **not one of MDM, BYOD, COPE, CYOD or MAM is expanded anywhere in the collection.** So there is nothing to protect and nothing being taught; the deck tests properties of five terms it never defines. That absence is the finding, and it is question 1's whole point.

### Two jobs, two owners

| Job | Owner | State |
|---|---|---|
| Find the acronyms in the recent import, propose the list, apply approved glosses via AnkiConnect | **`/medic`** | ran once, 2026-08-01, 9 notes |
| Stop the pipeline generating cue-opaque acronym cards in the first place | **upstream ticket — this one** | ✅ **shipped 2026-08-08** as a P5 post-processor (below); the P2 half is deferred |

**Superseded upstream direction (08 Aug 2026):** the original note said P3 should gloss on first use in a front. It landed in **P5 instead**, after the export stream is assembled — P3 works in YAML, which is upstream of both the reverse-card merge and the TTS pass, and glossing there would have been read aloud. Relates to **T15** (deck-wide collision hunter) — both are "the cue is unusable for a reason the answer cannot fix." T15 still needs a Chief-Architect decision session; this one no longer does.

### The universal sweep — ruled and shipped 2026-08-08

**Three rulings, all Chief-Architect, all direct quotes.**

**1. The premise changed: acronym expansions stop being tested at all.**

> *"I am completely getting rid of standalone acronym flashcards in Prompt 2 (not in this session, I'll sit with the idea before I make prompt 2 changes). Because I will no longer be tested explicitly on what acronyms mean, there is no 'answer' to spoil. The clickable expansions are meant to be passive study aids."*

⏳ **The P2 change is DEFERRED by explicit decision — nothing in P2 was touched.** This matters more than it reads: until it lands, P2 still emits `Cognitive_Goal: Acronym` exile blocks, so `(Expansion)?` cards can still reach the export. **The expansion-card guard in the shipped code is therefore live logic, not defensive decoration**, and must not be removed as dead code before P2 actually stops. 55 such cards already exist in the collection.

**2. Universal, not curated.**

> *"Do a universal sweep. Do not waste time trying to curate or guess what I already know. If the clickable expansion is there and I already know it, it doesn't bother me."*

The cost argument that motivated all of this: the 2026-08-08 run planned **32 blocks, 7 of them acronym exiles** (SSID, SAML, SSO, PAM, MFA, IAM, DLP). To stay under the payload split the acronyms were cut by hand — P3 received 25 blocks and the finished deck has **zero** expansion cards. A gloss costs one API call at the very end and no payload weight at all.

**3. Fronts and backs, forward and reverse; first occurrence per card side.**

> *"The expansions must be applied to every occurrence on both the Fronts and the Backs of the cards."*
>
> *"…if we have 10 separate cards with for example MDM, they all get expansions because there is no way to predict which card I am studying and I need them all to have the clickable expansion. The deduplication is meant in isolation per card to prevent a single card from having multiple clickable expansions on same acronym."*

🚩 **The scope rule, as a table of explicit cases. This ticket has already stalled two `/medic` runs on a rule that was merely accurate — do not compress this back into a sentence.**

| Situation | Rule |
|---|---|
| **Same acronym twice in one field** | gloss the **first only** |
| **Same acronym in the Front and again in the Back of the same card** | gloss the **first only** — Front and Back are one card side, seen in one review |
| **Different acronyms anywhere on one card side** | gloss **every one of them**, independently |
| **Same acronym on the forward card and on the reverse card** | gloss **both** — they are two cards met weeks apart, and neither can borrow the other's gloss |
| **Same acronym across ten different notes** | gloss **all ten**. There is no deck-level dedup, ever |

### What shipped — `run_phase5.py:948`, hybrid regex → API → Python stitch

**Slot:** immediately after the TTS block, immediately before the header assembly and the `ANKI_IMPORT_READY.txt` write.

⚠️ **The position is load-bearing and was verified, not assumed.** `clean_text()` (`tts_reader.py:254`) strips HTML tags but **keeps their inner text**, so a gloss injected any earlier is spoken aloud on every card — and on a front carrying two glosses the audio is unusable. Anything upstream of P5 Pass 3 is also upstream of the reverse merge and the pipe assembly.

⚠️ **Single-quoted HTML attributes are mandatory here.** The export is a double-quoted pipe rectangle and `prompt5_exporter.txt:244` says so outright — *"You MUST use single quotes for the HTML attributes to prevent breaking the double-quoted CSV rectangle."* The `/medic` glosses use double quotes and are correct **for their channel**: AnkiConnect is JSON and never sees the CSV. Copying that string verbatim into the export corrupts the row. The markup is otherwise byte-identical to the proven pattern.

| Stage | Mechanism |
|---|---|
| **Hunt** | `\b[A-Z][A-Z0-9]{2,}\b` over fields 2/3/4/5/6 with HTML tags and `[sound:]` tokens masked out |
| **Define** | **one** `config.call_llm` call returning `{"MDM": "Mobile Device Management", "NOT": ""}`; empty string = "not an acronym" |
| **Stitch** | Python, first-occurrence-per-side, `re.sub` with a callable so replacement text is never re-scanned |

**No stop-list, deliberately** (Constitution §III-1). The regex is only a cheap candidate net; the model is the semantic filter. Measured on the previous run's export, the noise it must reject is 3 words — `NOT`, `LOW`, `ONE` — all of which the model answers with `""`.

**Failure is non-blocking:** two attempts, then the deck ships unglossed with a warning. An acronym gloss must never be able to cost a run.

🚩 **The `try/except` around `config.call_llm` is load-bearing — do not remove it as redundant with the retry loop.** The retry only handles a *bad answer*; a **raised** exception (network down, provider error) is a different path, and this block runs **before** the export write, so an escaping exception discards the whole deck *after* the veto gate has already been worked by hand. The Casting Director makes the identical call bare at `:1486` and that is **not** a precedent — it runs after the file is on disk, where the blast radius is a missing persona. Caught in verification 2026-08-08: 6 of 7 failure paths passed and the raise path killed the run.

**Verified before the graft landed,** by running the exact block against the 16 real rows of the last export plus two synthetic rows: 8 fields preserved on every row, zero raw double-quotes introduced, one API call, `🏷️ TOTP (Expansion)?` skipped whole, `MDM` inside `href='…?q=MDM+console'` left untouched, second same-side occurrence left plain.

### `Extra` is in scope — ruled 2026-08-08

> *"Yes, please add the `Extra` field to the scope so it gets the clickable expansions too, since it visually renders on the back of the card."*

`Extra` **does** render on the answer side of both cards — verified from the `Basic+` templates, where `Forward.Back` and `Card 2.Back` each contain `{{Extra}}`. It mattered: on the last shipped deck **5 of 11 candidates lived only in `Extra`** (`TOTP`, `MFA`, `EDR`, plus two noise words), in strings like *"⚠️ NOT: Built-in MDM security"* and *"adjacent to 6.3 EDR function"*.

🚩 **`Extra` is swept with the FORWARD side only — `_ACRO_SCOPES = ((2, 3, 4), (5, 6))`. Do not add field 4 to the reverse scope, however symmetric that looks.**

This ticket's first draft of the change said field 4 *"must appear in **both** scopes, because it is rendered on both cards."* **That is wrong and it corrupts cards.** `Extra` renders twice but *is one string*: once the forward pass has wrapped an acronym, the acronym text sits exposed between `<span class='an'>` and its closing tag, where the tag-mask does not reach — so a second pass over the same field wraps it again and nests a `<label>` inside the first. **Measured on the 16 real rows of the last export: 3 rows corrupted with `((2,3,4),(5,6,4))`, 0 with `((2,3,4),(5,6))`.** The error was invisible on re-reading and took ten seconds to find by execution — the 2026-07-31 lesson (*"a behavioural fix is not verified by re-reading it"*) fired exactly as written.

⚠️ **Two known, accepted cosmetic consequences.** Neither is worth engineering around, and the ruling *"if the clickable expansion is there and I already know it, it doesn't bother me"* covers both:

1. **Double expansion when opened.** Some `Extra` strings already carry the expansion in prose — `⚠️ NOT: MAM (Mobile Application Management) — covers apps…` now renders the expansion twice when the gloss is opened. **Collapsed it is byte-for-byte what it always looked like.** Suppressing it would need a brittle "is the expansion already in the next parenthetical" regex, which Constitution §III-1 puts last.
2. **One narrow gap.** An acronym appearing on the forward Front *and* in `Extra` but in **neither** reverse field is glossed on the forward card only; the reverse card shows it bare in `Extra`. Unavoidable while `Extra` is a single shared string, and it fails in the mild direction — a missing gloss, never a duplicate or broken markup.

---

## T27 · The deck teaches what a thing *is*, never where the learner would *meet* it — OPEN

**Raised** 2026-08-05, off a live SAML / SSO / JIT transcript from the **newer second-lecturer** videos CompTIA added after Mike Myers recorded the originals. **Class:** pipeline (P1 harvest · P2 routing · P3 Line-2 contest). **Severity:** medium — no card is *wrong*; the deck is uniformly ungrounded. **Priority:** secondary project, per the Chief Architect.

> *"The lecture, and I need to modify prompt1, prompt2, or prompt3 … these concepts are being, they're such dry concepts. There's no anchoring. There's no, nothing telling us what, what are these? Give us an example. A real world example."*
>
> *"For example, DNS caching. When you explain, as a dry fact, DNS caching — but when you relate it to a real world user encountered event, where you see, for example, in the corner of the browser."*
>
> *"Is this a dry fact? Do we have enough context? Do we have a cohesive story? Do we have examples of where the systems are implemented? Because the lecture, the student is only learning dry facts."*

### 🎯 What this ticket is for

**A card should also be able to answer "where would I run into this?"** — not only "what is it." The complaint is not about accuracy and not about the Logic bullet's *presence*; it is that the deck never lands the concept in an event the learner has personally witnessed.

**Named target shape, 2026-08-05 — three things, not one:**

> *"As long as the pipeline is doing something about it, we create, like, **vivid examples** and **pain points** and, **what is this about?** … I don't want to memorize dry facts. That's all."*

⚠️ **Read that as three distinct outputs, because the pipeline treats them as three different mechanisms and two of them already exist:**

| Wanted | Nearest existing mechanism | State |
|---|---|---|
| **Vivid examples** — where you'd meet it | **`/shorts` trigger three** (added 2026-08-19) | a 60-second short showing the concept in a situation the learner has witnessed. This row read "none" until `/shorts` existed |
| **Pain points** — what problem it solves | `PainPoint_Model` + Template 13 (`Mission`) | **exists and is forbidden standalone** — 1 block in 358 |
| **"What is this about?"** — the orienting frame | `Foundational_Bridge` | **exists and is demoted without exception** |

**Two of the three asks are unblocking machinery that is already built, not building new machinery.** Any design that answers only the first ask has answered one third of this ticket.

### The premise, checked — substantially true, and one part of it is not

The Chief Architect's own workaround is the strongest evidence: the last trigger they spoke into the SAML lecture was **`"Create a flashcard about concrete examples … there's no examples here. It's just dry facts."`** They are hand-triggering the grounding card, per video, because nothing generates it.

⚠️ **But the transcript is not example-free, and the ticket must not claim it is.** The lecturer opens with a concrete pain scenario — *"when I go online at work, I have to log into four or five different applications and databases … it's easier just to use the same one for everything"* — and offers one relational anchor, *"the principle of least privilege taken to the next level."* What is genuinely absent is **named products, screen-level observations, and worked walkthroughs**. So the defect is not "the lecture gave us nothing to work with"; it is **the pipeline discards the little grounding that arrives and manufactures none of its own.** A fix aimed at the wrong half of that will miss.

### Measured — 27 runs, 363 cards, 358 P2 blocks

| Signal | Count | Share |
|---|---|---|
| Cards carrying `Analogy:` on the Back | **8** | 2.2% |
| …of which are *actual* analogies (rest are lecturer-provenance notes) | **3** | 0.8% |
| Extra fields carrying `Example:` | **17** | 4.7% |
| `Syntax_Example` populated in the P2 baton | **18 / 358** | 5% |
| `PainPoint_Model` blocks | **1 / 358** | 0.3% |
| `Foundational_Bridge` blocks | **2 / 358** | 0.6% |
| **Paradigm Exemption fires — the only authorised standalone-grounding path** | **0** | **never, in 27 runs** |

⚠️ **`Example:` is a SYNTAX channel, not an exemplification channel.** `prompt2_draftsman.txt:493` defines its only source as `Syntax_Example: [Code syntax for practical execution]`. Every one of the 17 delivered is a command, a URL, a UI path or a product list (`powercfg -h off`, `ftp://192.168.1.1`, `Devices > Enrollment restrictions`, `iCloud, OneDrive, Google Drive, Dropbox`). **Do not read the 4.7% as 4.7% of cards being grounded** — the true rate of "here is where you meet this" is the 0.8% above.

### Root cause: three grounding mandates exist, and every path to the card is closed

The pipeline is **not missing** the intent. It already carries three separate instructions to ground abstraction in reality. All three are attached to block types that cannot reach a card.

| # | Mandate | Where | Why it never lands |
|---|---|---|---|
| 1 | **User Anchor → `Analogy:`** — *"preserves the lecturer's specific analogy or scenario"* | `prompt2_draftsman.txt:409` → `prompt3_formulator.txt:347` | **Purely extractive** — populated only from `<lecturer_anchor>`/`<lecturer_description>`. Silent lecturer ⇒ `N/A` (**201 of 358 blocks**). And when it *is* populated, Back Line 2 holds **one** bullet and `Logic:` outranks `Analogy:` in the prefix order |
| 2 | **The Troubleshooting Heuristic** — *"MUST frame the concept as a real-world Helpdesk symptom … This grounds abstract theory in practical IT reality"* | `prompt2_draftsman.txt:380` | Scoped to `PainPoint_Model`, which the **Scaffolding Demotion Mandate** (`:285`) declares *"STRICTLY FORBIDDEN"* as a standalone block. The **Paradigm Exemption** (`:287`) is its only escape and has fired **zero** times |
| 3 | **The Temporal Boundary Lock** — *"go deeper into the Problem Space … the administrative cost of updating 50 individual router configurations by hand"* | `prompt2_draftsman.txt:402` | Scoped to `PainPoint_Model` / `Mission` / `Foundational_Bridge` — the same demoted set. `Foundational_Bridge` is demoted **without exception** (`:299`) |

**P1 is extractive at the source too.** The **Metaphor & Slang Hunt** (`prompt1_harvester.txt:364`) mandates *"a minimum of TWO functional descriptions, analogies, or non-standard slang **used by the lecturer**."* Against a lecturer who uses none, that quota has nothing to find — and the pipeline's own telemetry already reports it misfiring: *"the mandatory two-metaphor BRIDGE quota produces near-guaranteed downstream duplication"* (`prompt_telemetry_database.txt` L147, video 118).

**And the executing model reported the Line-2 leak independently, twice** (`prompt_telemetry_database.txt` L352, L395, video 124): *"`User_Anchor` → `Analogy:` routing is stated once in the Bifurcated Data Routing section but never cross-referenced in the Seven Sins list, so a dropped `User_Anchor` has no named Sin to file it under."*

### 🚫 What is already settled — do not re-open these

| Prior finding | Standing | How T27 differs |
|---|---|---|
| **`User_Anchor` 4% delivery — "Not a leak"** (Negative findings, below) | **Correct, unchanged.** Line 2 holds one bullet; `Logic:` outranks `Analogy:`; 128 of 131 blocks were structurally unable to reach it | That ruling answered *"is this a bug?"* — **no**. T27 asks *"should a dedicated channel exist at all?"* The ruling is T27's **evidence**, not its target. Do not re-file it as a leak |
| **"Pipeline is sycophantic to the transcript" — No** (Negative findings, below) | **Correct, unchanged.** STEP 1.5E fired on run 133 and shipped real-world content from a transcript with zero currency mentions | The pipeline *can* originate non-transcript content. So the gap is not "it only ever parrots the lecturer" — it is that **no sweep is pointed at exemplification.** 1.5D bridges *mechanism*; 1.5E bridges *currency*; nothing bridges *instantiation* |

### Second datapoint for T6

**T6** (*"`Logic:` bullets are not landing"*) was filed 2026-07-30 as a single datapoint — *"the logic point does not help me either"* — and marked **low-confidence, needs more evidence**. This is that evidence, and it also explains the first: the `Logic:` bullet restates the mechanism in different words rather than placing it in an event the learner has seen. **T6 and T27 are the same complaint at two altitudes.** Whoever works either should read both.

### 🚩 Open questions — NOT ruled, NOT designed

None of the below has a Chief-Architect decision. **Do not implement past this line.**

| # | Question | Why it is load-bearing |
|---|---|---|
| 1 | **Which prompt owns it?** | P1 = a new harvest sweep (a sibling to 1.5C/D/E). P2 = lift the demotion so a grounding block can stand alone. P3 = let Line 2 carry two bullets so `Analogy:` stops losing to `Logic:`. **The subtractive option is P3** — the channel already exists and is merely outranked; per Constitution §III-1 that outranks adding a fourth sweep to P1, and it should be priced before any new sweep is designed |
| 2 | **Always, or only when the lecture is dry?** | The Chief Architect framed it as *"where the lecture is just bad"* — implying detection. A detector is a new judgment surface; firing unconditionally is simpler but bloats good lectures. **Not decided** |
| 3 | **One grounding card per video, or per concept?** | Their own trigger asked for *"a **unified** example of what these concepts ultimately boil down to"* — singular, spanning SAML+SSO+JIT. That is **not** the same shape as one example per concept, and the two produce very different decks |
| 4 | **Does a grounding card get tested, or just read?** | An "example" card risks being unanswerable-by-design — the failure mode T20 and T26 both describe. If it is not retrievable it may belong in `Extra`, not on a Back |
| 5 | **Hallucination budget** | Manufactured examples are model-authored general IT knowledge — the same trust tier as 1.5D/1.5E, both of which carry **mandatory `certainty="LOW"`**. Any new path almost certainly inherits that, and with it the veto gate. Confirm rather than assume |

### Two jobs, two owners

| Job | Owner |
|---|---|
| Design the mechanism — prompt work, whole-file, holistic | **Chat (Gemini / Claude.ai)** per `CLAUDE.md` §II prompt-design routing. Hand over `prompt1_harvester.txt`, `prompt2_draftsman.txt`, `prompt3_formulator.txt` **whole**, with this ticket |
| Anchor verification, residency grep, compiler simulation, execution | **Claude Code** |
| Repair the ~363 already-shipped ungrounded cards | **Not this ticket.** Remediation vs prevention, same split as T11 — open a separate one only if the Chief Architect wants it |

---

## T28 · The card template silently deletes content from 120 notes on every render — OPEN

**Found 2026-08-12** while simulating an unrelated write against the live collection. **Class:** card template (`Basic+`, both back templates). **Severity:** high — silent, active, and losing content today with no agent involved.

### Measured, not inferred

| | |
|---|---|
| `Basic+` notes with a non-empty `Extra` | **1,402** |
| **notes that LOSE text at render time** | **120 (8%)** |
| characters discarded per full pass | **2,846** |
| of those, notes containing a `<table>` | 19 |

Examples: `LINBbhsFm:` loses 49 chars · `wNkH%E)lIc` loses 107 · `G/eD=8--Ty` loses 69.

### The mechanism

`renderContent()`'s marker-splitter cuts `Extra` on `<br>` and reassembles it. **A pre-existing `<details>` block whose body contains an internal `<br>` gets cut in half** — which is every `🔄 Refresher` table the pipeline emits, because the table markup carries `<br>`s.

The opening half hits the `/^<(label|details)\b/` passthrough branch and is pushed intact. The tail lands in the final `else` branch, which does:

```js
out[out.length-1] = out[out.length-1].replace('</div></details>', '<br>' + p + '</div></details>');
```

**But a pipeline-generated `<details>` has the shape `<details><summary>🔄</summary>Refresher…<div align="center"><table>…` — it contains no literal `</div></details>`.** The `.replace()` matches nothing, returns the string unchanged, and the tail is discarded. No error, no warning. Only blocks the splitter *builds itself* end in that exact string, so the append only ever works on its own output.

### Why it went unseen

The loss is invisible three ways: the source field is intact in the database, the *first* half of every affected block still renders, and the missing part is usually the bottom of a table. **This is the third silent-render defect in this collection** — after `data-simple="1"` hiding `Extra` on 1,310 notes, and `</🚀` bogus-comment parsing on 538. Same shape every time: the data is fine, the renderer eats it, and nothing reports a failure.

### Fix direction — not designed, and do not improvise it

The append branch must not depend on a magic string. Candidates: append before the **last** `</details>` found by index rather than by literal match; or make the passthrough branch consume following non-marker segments explicitly; or stop splitting inside an already-open block by tracking depth. **Whichever is chosen, re-run the simulation over all 1,402 fields and require zero character loss before shipping** — the harness that found this is trivial to rebuild and is the only honest acceptance test.

⚠️ **Not urgent to the point of panic:** nothing is being deleted from the database and every fix is applied at render time, so a corrected template restores all 120 notes at once. But it is losing content on every review today.

**Found by:** simulating the template's own JS in Python over real `Extra` values, while checking whether a *different* markup was safe. Reading the template did not reveal it; running it did.

---

## Negative findings — do not re-litigate

| Finding | Verdict |
|---|---|
| Extreme-lapse outliers | Legacy 2021–22 personal cards. Pipeline-era mean 0.54 lapses/card vs 0.66 collection. ⚠️ Test biased toward old cards by the `lapses`-column problem |
| Reverse cards underperform | **No.** Forward 26.6% vs reverse 25.1%. ⚠️ Confound: only 34% of notes get a reverse, threshold-selected |
| `User_Anchor` 4% delivery | **Not a leak.** Line 2 holds one bullet; `Logic:` outranks `Analogy:`. 128 of 131 blocks were structurally unable to reach it |
| Pipeline is "sycophantic to the transcript" | **No.** `prompt1_harvester.txt:226` STEP 1.5E REALITY CHECK SWEEP fired on run 133 and shipped `CDMA/GSM split (Current real-world status)? → Largely obsolete today` from a transcript with zero currency mentions |
| Pipe characters break the deck import | **No.** 82 rows across 4 runs, every matrix row parses to exactly 8 fields, including one with 5 literal pipes. Quote-wrapping handles it |
| Phase 6's 8→0 DEBT drop | Human veto (`run_phase6.py:82–210`), not a leak. ⚠️ But `:167`'s LOW-certainty bulk prompt defaults to `ENTER = reject ALL` |

---

## Method warnings for whoever works these

1. **Copy `collection.anki2` AND `collection.anki2-wal` together.** Anki runs WAL mode; copying the base file alone silently drops a day of writes. This cost two false "your data isn't there" reports.
2. **Never query `cards.lapses`.** It only increments on review-stage failures. The worst card reads `lapses=1` against 12 Again presses. Use `revlog.ease=1` with `type IN (0,1,2)`.
3. **The P2 baton has two serialization formats** (`**Field:**` and `Field:`); run 135 mixes both in one file. Use `\*{0,2}Field:\*{0,2}`. Five ad-hoc regexes disagreed by up to 165% this session.
4. **Ripgrep is blind to `Archive/`** — root `.gitignore` line 2 is `*` and rg honours it, returning a silent false negative. Use a non-git-aware tool.
5. **Count `📊 Matrix` payloads, not the bare word "Matrix."**
6. **`Medic_Notes` provenance: the skill's stated 14/247 split is now 13/248.** `medic.md` Step 2 cites *"14 user-authored vs 247 pipeline"*. That figure was derived with a looser marker list. Re-measured 2026-07-30 with the skill's own published list (`Answer text:` · `[SCENE:` · `[MOOD` · `[METAPHOR:` · `Style:` · `Setting (` · `Actor` · `Image Caption`), the split is **13 / 248** — `uYw]B57)WG` is an image prompt that the looser filter missed and `Image Caption` correctly catches. The published list is the better one; only the headline number is stale. **Reconciliation:** of those 13, six are legacy category stamps (`[TROUBLESHOOTING]` ×4, `[TOOLS]` ×2), leaving **7 genuine annotations in `Medic_Notes` + 2 in `Extra` = 9**, which is exactly the set run 1 processed.
7. **A confusability scan must use *same length + same first and last letter + ≤2 substitutions*.** Anagram and Levenshtein-1 tests both miss `SNMP`/`SMTP` (two positions differ). See T12.
8. **Never put a raw Anki GUID in a markdown table.** GUIDs are base91 and routinely contain `|`, `#`, `>` and backticks — `D#3g|gsjxO` is live in this collection. Backticks do **not** protect a pipe inside a GFM table cell; the row splits and the summary mangles. Use the indented run-summary template, or escape the pipe as `\|`.

---

## T29 · Ordered sequences get an enumeration card and no memory hook — OPEN

**Raised** 2026-08-19 by the Chief Architect, who also demonstrated the mechanism working
on themselves mid-sentence. **Class:** pipeline (P1 detect · P2 flag) + image agent (mint)
+ `/medic` (retro-fit). **Severity:** medium-high — it affects every ordered list in the
syllabus, and the syllabus is full of them.

> *"Imagine this. There's seven steps. It's complicated. But PEMDAS is not complicated…
> Parentheses, exponent, multiplication, division, addition, subtraction. Very easy if you
> know the acronym. And I'm thinking, okay, the same with CompTIA troubleshooting where
> it's like five steps."*

> *"So it starts with P. P-E-D… D stands for — well, I don't know what D stands for, but I
> know it's the third step. And I have to figure out what D stands for. I have to recall
> what the D stands for. … Oh, I remember, **developing**. See. That's the system working."*

**That second quote is the evidence, not the anecdote.** They recovered a step they could
not recall directly, from its position in a letter string. The experiment ran itself.

### Why this is NOT already covered

| Existing machinery | What it does | Why it does not cover this |
|---|---|---|
| `prompt1_harvester.txt:176` Step 1.5C | captures "a multi-step protocol handshake, state transition, or process flow… the sequence itself is testable" | produces the **enumeration** card — the thing that is hard to memorise. No hook. |
| `prompt2_draftsman.txt:211` Acronym Historian Gate | expands an acronym that already exists (`DHCP` → Dynamic Host Configuration Protocol) | **opposite direction.** This ticket needs an acronym *minted from* a sequence's initials. |
| image agent 🚀 mnemonic | acronym → vivid scene (`DHCP` → "Dizzy Hippos Crashing Parties") | scoped to a **label**, not to an ordered set. |

### 🚩 The image agent's Layer 1 / Layer 2 rule does NOT veto this — read carefully

`image_prompts/rules.txt` warns: *"A mnemonic that delivers only Layer 1 is hollow… Most
acronym mnemonics fail here, and they fail invisibly, because the letters come back and it
feels like it worked."* `HOLLOW: "Silly Nervous Monkeys Panic" for SNMP — letters
recovered, function absent.`

**That rule governs ACRONYM cards, where the tested content is what the thing DOES.** A
sequence card asks *"what is step three?"* — **the tested content is the POSITION.** For
sequences, Layer 1 *is* Layer 2, and the hollow-mnemonic failure does not apply.

⚠️ **Do not let a future session cite the Layer 1/2 rule to close this ticket.** The two
cases are genuinely different and the distinction is the whole basis for the ticket.

### Two limits that must be designed around, not discovered later

1. **A hook only reconstructs a term already met.** `D` → "developing" worked because the
   Chief Architect had seen the word. For a novel term `D` is a blank. **The hook card sits
   ALONGSIDE the enumeration card, never instead of it.**
2. **Most real sequences will not pronounce.** The seven-step laser imaging process is
   Processing · Charging · Exposing · Developing · Transferring · Fusing · Cleaning →
   **`PCEDTFC`**, which is not a word. PEMDAS works precisely because it says something.
   **Mandating "mint an acronym" produces garbage strings**, and `rules.txt` already warns
   against *"a mnemonic that is worse than none because it is memorable in the wrong
   direction."*
   ✅ **The fallback is an ACROSTIC** — the "Please Excuse My Dear Aunt Sally" form, a
   sentence whose word-initials carry the order. Terminology, since it was asked: PEMDAS is
   an **acronym mnemonic**; the Aunt Sally sentence is an **acrostic**.

### Proposed split of work — three of four are existing machinery

| Job | Owner | Change required |
|---|---|---|
| detect an ordered set of >3 items | **P1** | none — `:176` already does it |
| flag that card as needing a sequence hook | **P2** | one marker on an existing card type |
| mint the acronym **or acrostic**, and the image | **image agent** | extend the Layer 1/2 gate to the sequence case |
| retro-fit sequences already in the deck | **`/medic`** | new toolbox row; ~2,400 cards will never be re-processed by the pipeline |

🚫 **The P1/P2 wording is NOT drafted here.** `CLAUDE.md` routes prompt design to Chat —
Claude Code scouts and verifies, Chat drafts the graft. The section anchors and the
constraints above are the scout output; hand them to Chat with the whole prompt file.

### Open questions for the Chief Architect

1. **Threshold:** they said *"more than three elements."* Is 4 the floor, or does an ordered
   3 (e.g. a 3-step handshake) also qualify?
2. **Does the hook get its own card, or ride on the enumeration card's Extra?** A separate
   card enters the queue immediately (`/medic` §4a reasoning); an Extra edit is invisible
   until the card is next due.
3. **Unordered lists too?** The request named *"steps, sequence, lists, anything with more
   than three elements"* — but a hook for an UNORDERED set (e.g. the four CMYK toners) is a
   different job from a hook for an ORDER, and CMYK is already its own acronym.

⚠️ **There is an Anki note on this that has NOT been read.** The Chief Architect: *"I put
this in an Anki note recently, if you look."* Anki was closed at the time of writing and
`Medic_Notes` could not be searched. **Read it before designing — their written version may
carry constraints this transcription does not.**
