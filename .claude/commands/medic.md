---
description: Card triage & repair — read Anki lapses + in-card annotations, diagnose, apply fixes via AnkiConnect on approval.
argument-hint: [days | guid | --report]
---

You are running **`/medic`** — Anki card triage and repair.

Full rationale, evidence, and measured figures: **`SKILL_SPEC_anki_medic.md`** at repo root. Read it when a judgement call is unclear. Everything below is operational and must be followed as written.

**Two outputs, always:** (1) a numbered list of proposed changes, applied through AnkiConnect once approved — or a no-op verdict; (2) ticket entries appended to `MEDIC_TICKETS.md`. Output 2 is the point; output 1 is triage.

## Arguments

| Form | Meaning |
|---|---|
| *(none)* | last 7 days |
| `30` | widen window to 30 days |
| `<guid>` | one specific card |
| `--report` | **read-only. Diagnose and propose NO AnkiConnect writes** — not even for approval. Reads (`findCards`, `cardsInfo`) are still fine. The ledger is still written; it is a record, not a card change |

---

## 🚫 FATAL PRECONDITIONS — get these wrong and the run is worthless

**1. Copy BOTH database files.** Anki runs SQLite in WAL mode.

```
cp "$APPDATA/Anki2/User 1/collection.anki2"      <scratchpad>/coll.anki2
cp "$APPDATA/Anki2/User 1/collection.anki2-wal"  <scratchpad>/coll.anki2-wal
```
Open the **copy**. Copying the base file alone silently drops uncommitted writes — a full day of reviews and annotations. The live file is locked while Anki is open; never open it directly. **Never write to the collection via SQLite, ever** — no `UPDATE`, no `INSERT`, no exceptions. Card and note changes travel through **AnkiConnect only** (Step 7), which goes through Anki's own code — SQLite writes bypass it entirely.

**If `-wal` is absent, that is not a failure — verify why.** Check whether Anki is running (`Get-Process anki`). A clean shutdown checkpoints the WAL into the base file and deletes it, so **no `-wal` + Anki closed = the base copy is complete; proceed.** No `-wal` while Anki *is* running means you are reading the wrong profile directory — stop and find the right one.

**2a. `revlog.type` — know which kind of failure you are looking at.** The skill filters `type IN (0,1,2)` everywhere and never says why. Measured 2026-08-11 across the whole collection:

| type | meaning | `ease=1` count | weight |
|---|---|---|---|
| **0** | **learn** — card has not graduated yet | **9,514** | first-exposure noise, mostly. A single one means nothing |
| **1** | **review** — a genuine **LAPSE**: known, then forgotten | **4,286** | the real signal |
| **2** | **relearn** — failed again while recovering from a lapse | **1,562** | strong signal, the card is fighting back |
| 3 | filtered / cram | 20 | exclude |
| 4 | manual reschedule | — | not a review at all, exclude |

**62% of all Again presses are type 0.** Any rule that treats "an Again" as one thing will spend most of its attention on cards being seen for the first time. **Weight a type-1 lapse far above a type-0 stumble**, and never conclude a card is broken from learn-stage failures alone.

**2. NEVER query `cards.lapses`.** It increments only on review-stage failures. The worst card in this collection reads `lapses = 1` against 12 "Again" presses. **A `lapses > 0` filter reports a healthy deck.** Use `revlog.ease` with `type IN (0,1,2)`.

**3. Field map is positional.** `ord 0 Front · 1 Back · 2 Extra · 3 Inverse_Question · 4 Inverse_Answer · 5 Medic_Notes`. Read by index, never by field name.

**4a. NEVER reuse one sqlite cursor for an outer loop and its inner queries.** Iterating `cur.execute(...)` while issuing further queries on that same cursor silently truncates the outer loop, usually to one row — no error, just a wrong answer that looks like a finding. Use `.fetchall()` first, or a second cursor. **This has now bitten three separate sessions**, most recently run 3, which reported 1 card in a cluster that contains 32. It was caught only because the number contradicted a listing produced moments earlier.

**4b. Scope a term search to `Front` and `Back`, never to all six fields.** `flds LIKE '%SMTP%'` also matches notes that merely *mention* the term in a `⚠️ NOT:` line or a `Logic:` bullet, inflating both sides of a ratio. Verified: the all-fields scope produced SNMP 42% / SMTP 34%; the Front/Back scope reproduces run 1 at **SNMP 39% / SMTP 33%**, and the all-fields figures were the wrong ones.

**4. If two of your own measurements disagree, report the discrepancy — do not pick one.** Ad-hoc regexes over this project's dual-format artifacts have disagreed by 165%. Use one parser; when parsing pipeline batons use `\*{0,2}Field:\*{0,2}`.

---

## STEP 1 — Gather (five independent triggers)

| Trigger | Query |
|---|---|
| Failure | `revlog.ease = 1`, `type IN (0,1,2)`, within window |
| Struggle | `revlog.ease = 2` (Hard) |
| **Annotation** | §2's shape test finds annotation prose. **NO watermark, no date filter, no grade filter** — see below |
| Junk | `ease = 4` on a card's **first** review, **and the card is not a core fact** — see below |
| Watermark | last `/medic` run; read from the `medic::run::<date>-<HHMM>` tag. **Gates the three review triggers only, never the annotation trigger** |

The annotation trigger is not optional. The Chief Architect must never have to fail a card deliberately to flag it.

🚩 **`notes.mod` alone is a self-inflicted trigger — importing a patch bumps it on every note you touched.** Measured 2026-07-31: **15 of 16 notes would have re-fired on the next run purely because the previous run patched them**, every one with an empty annotation. The loop compounds — each run guarantees its own notes re-trigger, and the pile grows every time. **Require the annotation to exist, not merely the timestamp to have moved.** Do not fix this with a tag-exclusion list; the content test is simpler and cannot drift.

🚫 **The watermark must NOT gate the annotation trigger. An annotation that still exists is unprocessed, full stop.** The watermark advances when a *run finishes*, not when an *annotation is handled* — so an annotation that was read but never cleared becomes permanently invisible the moment the run that read it completes. **Verified failure, run 2 → run 3 (2026-07-31):** run 2 read four annotations, dispositioned every sentence into the ledger, and wrote skill amendments from them — but emitted no patch row, so the fields stayed live. The watermark advanced regardless, and `mod > watermark` then returned **zero of the four**. Run 3 found them only because its shape scan happened to ignore the watermark. **This is MEDIC-32's clock failing in the opposite direction and it fails silently** — the run reports "no annotations" and looks correct.

**Existence IS the unprocessed flag**, because Step 8 clears every annotation it processes. Scan the whole deck for annotation-shaped content on every run; a stale annotation costs one re-read, a missed one costs the Chief Architect's feedback entirely.

🚫 **"Annotation present" means §2's SHAPE test passes — never "a field is non-empty."** These two rules collide if you read them loosely: §2 says scan all six fields, so *"is any field populated"* is true for every card in the collection — **every card has a Front.** Dry-run 2026-07-31: the loose reading suppressed **1 of 16** self-inflicted triggers instead of 15, leaving the loop wide open. The test is **first-person prose or shouting caps** (`I answered…`, `should we…`, `THIS IS A VERY BAD…`) — the Chief Architect's voice. **Card content never counts, however long it is**, and a field whose only content is pipeline-marked (`⚠️ NOT:`, `📊 Matrix`, `Logic:`, …) never counts either.

🚩 **Annotations are a bonus signal, NOT the primary one. Find patterns on your own initiative.**

> *"I will not edit all cards that I fail, I still want cc to identify patterns and connect by its own initiative."*

Most failing cards will carry **no annotation at all**. The four non-annotation triggers are first-class and must be worked with equal effort: run the Class H cross-run analysis and the Class G acronym-collision scan on **every** invocation, whether or not a single note was annotated. **A run that only reports on annotated cards has failed**, even if every annotated card was handled perfectly.

## STEP 2 — Read annotations from BOTH fields

Annotations live in **`Medic_Notes` (ord 5)** and, historically, in **`Extra` (ord 2)** where Extra was empty.

🚫 **Scan ALL SIX fields, every run. The Chief Architect types wherever the cursor is.** Verified 2026-07-31: a note carried *"THIS IS A VERY BAD REVERSE, DONT EVEN THINK THIS NEEDS A REVERSE ANYWAY"* appended to the end of its **`Inverse_Question` (ord 3)** — a field a two-field scan never opens, on a card sitting at **13 Again out of 14 reviews, already suspended by hand**. The loudest signal in the collection was invisible to the skill.

**Detection is by shape, not by location.** In any field, first-person prose (`I answered…`, `I confused…`, `should we…`, `this is…`) or SHOUTING CAPS mid-field is the Chief Architect's, regardless of which field it sits in. Pipeline payloads are marker-led and third-person. When an annotation is found appended to a *content* field (`Front`, `Back`, `Inverse_Question`, `Inverse_Answer`), it is **also a rendering defect** — it is being displayed on the card during review — so clear it in the patch and say so.

**Separator:** pipeline content in `Extra` always carries a marker — `⚠️ NOT:`, `📊 Matrix`, `👁️`, `🪝 Hook:`, `Relates to:`, `Example:`, `Forensic:`. **Unmarked prose in `Extra` is the user's.**

### 🚫 Medic_Notes has TWO provenances and the default is INVERTED vs `Extra`

`Medic_Notes` was **renamed from `Image_Prompt`**, so the field is mostly full of legacy pipeline image prompts, not annotations. Measured 2026-07-30 against the marker list below: **13 user-authored vs 248 pipeline** — the annotations are the 5% minority. Of those 13, six are legacy `[TROUBLESHOOTING]` / `[TOOLS]` stamps, leaving **7 real annotations in `Medic_Notes`** plus 2 more in `Extra`.

**Reject as pipeline** any value carrying `Answer text:`, `[SCENE:`, `[MOOD:`, `[METAPHOR:`, `Style:`, `Setting (`, `Actor`, or `Image Caption`. Everything else is the user's.

⚠️ **Note the inversion.** In `Extra`, a marker means pipeline and unmarked prose is the user's. In `Medic_Notes` the *pipeline* payload is the bulky marked one and the user's is short unmarked prose. Diagnosing from a stray image prompt patches a card against a scene description of a shrimp boat.

### 🚫 2-0. Enumerate every annotation into `MEDIC_FEEDBACK_LEDGER.md` BEFORE reading it for meaning

**One row per sentence, and every row gets a disposition** — `IN` · `SPEC` · `TICKET` · `ANSWERED` · `N/A` · `❌ DROPPED`. Append a new dated section; never rewrite an existing one. Transcribe the sentence programmatically — **never retype it.**

This is not bookkeeping, it is the only check that works. Reading an annotation *for meaning* produces a list of rules, and every later verification then asks *"is the rule I derived present?"* — so anything dropped **while deriving** is invisible to that question no matter how many times it is asked. Nine consecutive verification passes over this skill all missed a request that was written in plain words, because none of them iterated over the Chief Architect's sentences.

**A run that ends with any row still blank, or any `❌ DROPPED` unrouted, is not finished.** Report the tally in the run summary.

⚠️ **Cite SECTION NAMES, never line numbers.** `medic.md` is a living file — it grew 19 KB → 33 KB in a single session, and every `:NNN` written into the ledger silently became wrong: 26 of 29 pointed at the wrong rule or a blank line **while still reading as verified**. A stale pointer inside a proof artifact is worse than a blank cell, because nothing about it looks broken. Write `§2f`, `Step 7a`, `Class B ruling` — anchors that survive an edit.

### 🚩 2a. An annotation is a SEQUENCE. The newest entry governs.

Annotations accrete across sessions inside one field, self-labelled `15:42pm:`, `edit 3`, `review at 17:00pm`, `16:23pm review`.

**Split on timestamp and `edit N` markers. Process oldest→newest. The final entry wins.** Earlier statements a later entry retracts are history, never findings.

> Worked example: one note reads *"pipeline outputs are a TOTAL MESS… refine pipeline"* and ends *"edit 3, nevermind, I just realized encoding =/= encryption… the answer was staring me in the face. in the NOT SECTION."* Blob-reading = pipeline defect. Sequence-reading = Class J. **Opposite verdicts from identical text.**

### 2b. Resolve which card (forward vs reverse) from the timestamp

One note serves both cards. Parse `HH:MM` tokens → find the nearest `revlog.id` for that note → read `cards.ord`. **Verified 4/4, max 10 min drift.** `ord 0` = forward, `ord 1` = reverse. No prefix convention needed. With no timestamp, attribute to the most recent review before `notes.mod` and mark it inferred.

### 2c. Separate the two payloads

| Payload | Destination |
|---|---|
| **Card diagnosis** — "I answered X instead of Y" | drives the repair |
| **Meta-feedback** — skill design, naming, pipeline questions | → `MEDIC_TICKETS.md` or surface for discussion; **never** a repair input |

Both appear in the same paragraph. Misreading meta-feedback as diagnosis patches a problem the card does not have.

### 2d. Exclude deliberate flag-fails from every statistic

When an annotation says the failure was deliberate — *"I had to fail this card so you can see it"*, *"I actually guessed right"* — mark the review `flag-fail`, **exclude it from all rate calculations**, keep the annotation as input. Report separately: `N of M Again presses were deliberate flags — excluded from rates.`

### 2e. A self-resolution or self-grade outranks `revlog.ease`

*"I count it as a success"*, *"nevermind, I realized…"*, *"I seem to learned the lesson in this case"* → **Class J. No patch.** The gap closed during the session; explaining it afterwards is bloat.

### 2f. Partially-correct answers are DOWN-weighted, not treated as failures

> *"I answered correctly wifi 4 but got the speed wrong… should we act on this types of reviews where I got the answer wrong? **dont lean towards it.**"*

Anki records one grade for a whole card, so a multi-value Back gives no per-value signal — a card can be 80% known and still read as a failure. **Do not treat partial knowledge as a defect.** Where an annotation shows most of the answer was retrieved, prefer **Class J** unless the miss is itself a cluster collision (Class A/B).

⚠️ Record it as a ticket candidate instead: a compound Back that masks partial knowledge is an **atomicity** problem in the card's construction, not something a repair tool fixes.

## STEP 3 — Classify

| Class | Signature |
|---|---|
| **A** Rival answer | a sibling's answer satisfies this cue on its merits |
| **B** 🚩 Priming bleed | answered a *different card's* answer, primed by reviewing it earlier |
| **C** Abstract-on-abstract | jargon answer explained with more jargon |
| **D** Bare atom | no annotation of any kind on the card |
| **E** Missing relational context | fact isolated from its sibling set |
| **F** Cue defect | front ambiguous, or its qualifier mislabels the fact class |
| **G** Near-identical acronyms | terms differing by transposition (SNMP/SMTP) |
| **H** Cross-run repeat offender | same concept fails every time it is taught |
| **I** Junk | buried with Easy on first review — **an Easy here is a suspend surrogate, not a grade.** Clean, do not repair |
| **J** No defect | cue misread, or self-resolved |

**Class B is the dominant class and it is RULED A BUG:**

> *"'Desirable friction' applies to retrieving the answer, not deciphering an ambiguous question."*

| Friction | Verdict |
|---|---|
| Retrieving the answer is hard | **Feature.** Leave it alone |
| Working out *which question is asked* is hard | **Bug.** Repair the cue |

An annotation describing front→back pairing memorisation (*"I should just learn through associating front 'role = …'"*) **confirms** Class B; it does not excuse it.

**Class H is measurement, not prediction.** Group a term's again-rate by import batch: consistent across batches = knowledge gap; variable = card construction. Never predict future confusion.

## STEP 4 — Select ONE tool

| Class | Tool |
|---|---|
| A | **⚠️ NOT-section update first** — name the rival explicitly. Escalate to ⚖️ Bridge card + **named axis** only if the NOT already names it |
| **B** | **✂️ Front constraint edit** — cue-side defect needs a cue-side fix. Add **⏱️ Forced adjacency** as a *second* tool only when the confusion is mutual — it is scheduling, so it does not count against the one-tool rule |
| C | 🧠 Analogy **+** 🧸 ELI5 *(the only class permitted two **content** tools)* |
| D | 🚀 Mnemonic / ⚡ Acronym / 🔢 Peg — most specific gate that fires (Peg > Acronym > Mnemonic) |
| E | 📊 Matrix recovery, escalating to 🩺 Explainer |
| F | ✂️ Front edit |
| G | 🚀 Phonetic separator |
| H | 💡 Killer Fact *(images moved out — see Step 5)* |
| I | 🏷️ **Tag `medic::junk::proposed` — that tag IS the execution path.** See below |
| J | **nothing** |

**✂️ Front edits have STANDING PERMISSION.** Do not stop to ask. Log every one (Step 6). Reversible from the before-value recorded in `MEDIC_ANNOTATION_ARCHIVE.md` (Step 7b rule 4).

🚫 **The one hard limit on that permission: ADD CONSTRAINT WITHOUT SPOILING THE ANSWER.**

> *"front edit if necessary to add constraints without spoiling."*

Standing permission removes the approval gate, **not this rule.** A front edit must narrow which sibling is being asked for while leaving the answer fully un-retrievable from the cue.

**Test before emitting any front edit:** could someone who does not know the answer now produce it from the front alone? If yes, the edit is a spoiler — **discard and redraft.** Adding the answer's own vocabulary, its distinguishing value, or a near-synonym of it to the cue is the failure mode. Sharpen the *category*, the *scope*, or the *axis of comparison* — never the answer.

*Example — Class B, `SSL/StartTLS (Mail-protocol role)?` vs siblings:* naming the axis (`…as opposed to end-to-end coverage`) discriminates legitimately; naming the ports or "encrypted versions of POP3/IMAP/SMTP" hands over the answer.

**✅ A `(NOT <rival>)` qualifier on the FRONT is explicitly permitted** — it is the cheapest legal front edit and it passes the spoiler test by construction: *excluding* a rival never reveals the answer.

> *"instead of or besides image, just editing the front with (NOT ...) might be enough to avoid confusion and my brain making those connections."*

Form: `📌 Cloud service models (Main members — **NOT** deployment models)?` Use the Chief Architect's **actual wrong answer** as the excluded rival, exactly as the ⚠️ NOT-section tool does. This is the cue-side counterpart of that tool and it directly addresses **T7** — discrimination that currently requires revealing the card to see. **Ban:** never stack more than one `(NOT …)` on a front; a cue carrying two exclusions has become a list, and the card should go to ➖ Merge instead.

### 4a. Scheduling constrains the vehicle

| Card state | Constraint |
|---|---|
| Just graded Good/Easy — next review weeks out | a Back/Extra edit is **invisible until then**. Prefer a **new card** (bridge or explainer) — it enters the new queue immediately |
| In learning/relearning | field edits land soon; cheapest tools apply |
| Failed repeatedly today | front edit justified — visible within the day |

### 🚩 4a-bis. Class I — why it exists, and how it actually gets executed

> *"sometimes I cannot suspend bad or very trivial cards, newly created dumb reverse cards for example, I just hit easy, **as ankiweb has no suspend function**, so I graduate and push them by hitting easy from the very first review… **that is why this skill needs to look at those as well to clean them.**"*

**Read the grade correctly.** AnkiWeb has no suspend button. A first-review Easy on a junk card is therefore **not** a signal of mastery — it is the Chief Architect burying an unsuspendable card 30+ days out with the only control available. Treating it as a confident pass inverts the meaning entirely. **Reverse cards are the usual offenders** — they leak past the P5 veto gate because the gate never shows them (T3).

**Suspension goes through AnkiConnect `suspend`, never a SQLite write to `cards.queue`.** The tag remains useful as a durable marker and as the fallback when the API is unreachable:

1. `addTags` every Class I note with `medic::junk::proposed` (or `::partial`) — fields otherwise untouched.
2. **Then propose the AnkiConnect `suspend` call** (Step 7a) covering exactly the `proposed` cards — card ids, count, and the search that produced them. On approval it executes; the Chief Architect does nothing by hand. **Fallback if Anki is closed or the probe fails:** the tag still works — *search `tag:medic::junk::proposed` in Anki desktop, select all, `Ctrl+J`*. Desktop has suspend; AnkiWeb does not, which is the asymmetry that creates this class in the first place. **`medic::junk::partial` is never bulk-suspended by either route** — name the junk `ord` and let the Chief Architect decide.
3. **Never suspend on your own authority** — but *executing* an approved `suspend` call is not own-authority, it is the Chief Architect's decision carried out. The gate is approval, not who types it. **Deleting is different and stays manual regardless**: `/medic` never deletes a note or card by any channel, approved or not, because deletion has no undo path through this workflow.

🚫 **`ease = 4` on a first review is AMBIGUOUS — it means "burying junk" OR "I already knew this." Check the content before proposing.** The Chief Architect's own words scope this class: *"bad or very trivial cards, **newly created dumb reverse cards** for example."* A card carrying a core exam fact answered confidently is the opposite of junk. **Verified false positive, run 3:** `Qm>3{4O>Gn` was tagged `junk::proposed` and left unsuspended because its content is *"SMTP (Default TCP Port)? → 25"* — a syllabus fact, not a dumb reverse.

**Before tagging, ask whether the card would be missed.** Junk looks like: a reverse whose question is a definition read backwards, a card whose answer is a restatement of its own front, a near-duplicate of a healthier sibling. **Not junk:** a port number, an expansion, a single canonical fact — however trivially it was answered. When it is genuinely unclear, tag `medic::junk::partial` and say why; that tag already means *needs a human decision*.

🚩 **Anki tags are NOTE-level; junk is CARD-level. Split the tag or you propose suspending healthy cards.** Measured 2026-07-31: 16 junk cards collapsed to 11 notes, and on **4 of them only one side was junk** — a single tag plus select-all would have suspended 4 healthy siblings. Therefore:

| Tag | Meaning | Action |
|---|---|---|
| `medic::junk::proposed` | **every** card of the note is junk | safe to bulk-select and suspend |
| `medic::junk::partial` | only some cards are junk — usually the reverse | **must be reviewed card-by-card**; name the junk `ord` in the run summary |

Never fold `partial` into `proposed` to make the summary tidier. The whole point of the tag is that it can be acted on without re-reading the diagnosis.

**A Class I finding that ships as prose in a chat log has not been delivered.** Without the tag the cards are unreachable the moment the session closes.

### 4b. Escalation
First patch = one tool. A second tool only on **repeat failure of an already-patched card**, logged. Third failure of a patched card = reclassify as **card-design failure** and open a ticket instead of patching again — **or propose ➖ Merge**, if the failure is a collision with one specific sibling rather than the card being hard on its own.

## STEP 5 — Compose, then check every ban

**Landing site: `Extra`.** It renders on **both** cards; `Back` renders on one. Never overwrite — append after `<br>`, patch content last. Skip if a same-class marker is already present.

⚠️ **One exception, because two rules collide here.** When the annotation itself is living in `Extra` (Step 2's second home) and the chosen tool also lands in `Extra`, "never overwrite" and Step 8's archive-then-clear point opposite ways. **Resolution: the annotation is not card content — replace it, provided it is already archived verbatim.** Preserve any *pipeline* payload in that field (`⚠️ NOT:`, `📊 Matrix`, `🪝 Hook:`, …) by appending around it; only the user's own prose may be displaced.

| Tool | Gate / ban |
|---|---|
| 🧠 Analogy | Organic / Kinetic / Arts only. **Required sensory detail.** BANNED: traffic · cars · highways · water pipes · office filing · **locks/keys** · factories · buildings · clocks/gears · bridges · conveyor belts · money · computer parts · office supplies |
| 🧸 ELI5 | must revolve around a **physical object a child can hold**. BANNED WORDS: *data · signal · protocol · interface · connection*. Substitute: data→mail, power→juice, signal→shouting, protocol→secret rules |
| 💡 Killer Fact | must contain History **or** Scale **or** Contrast. Forbidden openers: *"This is a…" · "It is used for…" · "Allows you to…"*. Must relate to the concept, not define a noun in the answer |
| 🚀 Mnemonic | Acronyms: `[Animal][Action][Object] → [Sound!] → [Outcome!]`. Concepts: `[Adjective][Animal][Action] → [Sound!] → [Outcome!]`. Canonical: *Dizzy Hippos Crashing Parties → SPLASH! → IPs FOR EVERYONE!* · **Assignment matrix — pick the system by content type:** procedural/sequential → **Link & Story** (cause-effect chains) · conceptual/abstract → **Visual Transformation** (symbolic, scale-distorted, hybrid creatures) · comparative/relational → **Phonetic** (sound-alike substitution) |
| ⚡ Acronym | **Gate: answer matches `^[A-Z0-9]{2,}$`** — `PCIe` fails (lowercase), `S/MIME` fails (slash), `A+` fails (symbol). **Format:** `⚡ [Absurd Animal Scene] → [Sound!] → [Outcome!]<br>(Spells out: [Full Acronym] – [Brief Definition])`. The scene encodes the letters; the parenthetical carries the real expansion — **both are required**, a scene without the expansion teaches nothing |
| 🔢 Peg | **gate: exact single numeric value.** Major System `0=s 1=t 2=n 3=m 4=r 5=l 6=sh 7=k 8=f 9=p`; seeds `22=nun · 25=nail · 80=fuzz · 143=dreamer · 161=tissue · 443=reamer · 993=papa` |
| 🖼️ ~~Image Prompt~~ | 🚫 **REMOVED 2026-08-11 — images are no longer a `/medic` tool.** They belong to a separate agent at `C:/Users/<you>/Desktop/image_prompts/`, which can actually *render* the picture; `/medic` could only ever emit prompt text the Chief Architect then had to turn into an image by hand. **Do not re-add this row, and do not write image prompts into any field.** If a card needs one, say so in the run summary and stop there. ⚠️ The forty-word rule that used to sit here was a lossy compression of a ~600-line protocol that now lives at `image_prompts/rules.txt` — restoring the summary would re-lose it |
| 📽️ Short | 🚫 **Not a `/medic` tool — it belongs to `/shorts`** (`.claude/commands/shorts.md`, built 2026-08-18). **Gate: the answer is a mechanism or force you cannot see, or must watch happen** — invisible physics, moving parts, a process over time. A name, a number or a list is *not* a short and stays with Mnemonic, Peg or the image agent. `/shorts` generates a 60-second NotebookLM video and writes the public link into `Extra` as a bare `📽️`. **`/medic` neither generates nor writes these.** If a failing card's answer is a mechanism, say so in the run summary and stop there. ⚠️ **Never run `/medic` and `/shorts` at the same time** — two agents writing one collection is silent corruption, not a merge conflict |
| ⚠️ **NOT-section update** | **Cheapest tool in the box, and the only one with direct evidence of working.** Seed the `⚠️ NOT:` line with **the user's actual wrong answer**, verbatim from the annotation — never a generic distractor. Proof: *"nevermind, I just realized encoding =/= encryption… the answer was staring me in the face. in the NOT SECTION."* If `Extra` already carries a `⚠️ NOT:` naming that rival, this tool is spent — escalate |
| 🩺 Explainer | **Structure, in this order** — it is copied from the exemplar the Chief Architect validated, not invented: (1) **one unifying analogy covering the whole cluster** (the canonical case: MIME = how the letter is packaged · S/MIME = the seal on it · SSL/TLS = the courier · StartTLS = switching to a secure vehicle mid-journey · Implicit TLS = secure from the start); (2) **per-term breakdown**, each term getting its own short block; (3) **a concrete before/after example** showing the mechanism, not a definition; (4) **explicit "X is NOT Y" contrasts** for every confusable pair in the cluster; (5) **chronological evolution** only where it explains why the terms differ. Expand acronyms **before** explaining them — half the answer is in the expansion. Appended to the failing card's `Extra` inside a 🔄 collapsible. **No separate deck** |
| 🔄 Collapsible | `<details><summary>🔄</summary><div align="center">…<table border="1">…</table></div></details>` · **≤5 columns, ≤6 rows** |
| ⏱️ **Forced adjacency** | **Scheduling, not text — the only tool that changes *when* rather than *what*.** Answers the complaint no content tool can: *"I cannot compare right now wording of card that I am thinking with."* **AnkiConnect only** — unreachable via the patch file. Gate: both cards exist and **a verified rival has been given as this card's answer at least once** — one direction is enough. Do NOT use to rescue a single hard card with no named rival; that is cramming. ⚠️ **Requiring the confusion to be bidirectional is too tight and was wrong** — run 3 correctly withheld the tool under that gate on both diagnosed pairs, including the cloud-models case that is the tool's own founding rationale (*"I cannot compare right now wording of card that I am thinking with public, hybrid"*). That complaint is inherently one-directional: the Chief Architect is holding one card and cannot see the other. **Two strengths, pick the weaker one that fits:** ① **Align** — `setDueDate` both cards to the same day so they meet in one session. 🚫 **ALIGN COMPRESSES INTERVALS. Say so in the approval box, every time.** Review *history* survives; the *interval* does not. Measured 2026-08-01 with `days:"0"`: **15d→2d · 4d→1d · 5d→1d.** An earlier version of this line claimed *"intervals and history survive"* — that was **wrong**, and the Chief Architect approved a schedule change under a description that did not match what happened. ⚠️ **A card in the learning queue is graduated to review by this call** (`queue 1 → 2`, observed on the same run) — a second undisclosed side effect. ⚠️ **Untested alternative worth trying before the next Align:** Anki's Set Due Date accepts a `!` suffix (`"0!"`) which is documented to control interval handling. **Do not assume which way it cuts — test it on one card and record the result here.** ② **Reset** — `forgetCards` on both, returning them to new so they **re-learn side by side from scratch**. Reset is correct when the pair is *maturity-mismatched* (one card mature, its rival new), because the mature card's long interval is what lets the confusion persist unseen. Reset destroys review history — propose it explicitly, never as a silent upgrade from Align |
| ➖ **Merge** | **Subtraction. Propose replacing two reliably-confused cards with ONE card that asks for the difference.** Preferred over discriminating between them when the pair has collided **3+ times** and both members are individually low-value. Emits a *proposal* — new card text plus the two guids to suspend — never an automatic delete. Constitution 1: the best fix removes a constraint |

**A ban failure regenerates that component. It never ships with a warning.**

### 🚩 5a. AIRLOCK — run on every field, no exceptions
`->` → `→` · `=>` → `⇒` · **strip every stray `>`** · no internal `<b>` inside a `</…>` wrapper.

A raw `>` terminates the card template's `innerHTML` parse and spills text. This is not cosmetic — **it has already silently destroyed content at scale.**

**The dominant live mechanism is `</` + non-letter, not a bare `>`.** `</🚀` is not a close tag: per the HTML spec, `</` followed by anything that is not an ASCII letter puts the parser into *bogus-comment* state, which swallows everything up to the next `>` — and that `>` is usually the one closing an internal `<b>`. The mnemonic's label and opening clause vanish; the remainder spills as bare text. **2,141 such wrappers exist across the `Basic+` deck; 358 notes carry a wrapper plus a trailing raw `>`.** Never emit `</` before a non-letter.

⚠️ Do not cite `Tiny Javelins>` as evidence — it is stored HTML-escaped as `&gt;` and renders as a harmless literal character. It was a false positive in the original ticket, disproven by raw-byte inspection on 2026-07-30.

⚠️ **Collapsibles require CSS that does not exist yet.** The `Basic+` stylesheet has one selector (`.card`); `details`, `summary`, `.extra-container` are unstyled. **Do not emit collapsibles until the CSS ships** — they render as 36px centred disclosure triangles.

🚩 **FALLBACK — do not deadlock on that.** 📊 Matrix recovery and 🩺 Explainer both name the collapsible as their container, so taken literally the prohibition leaves **Class E with no usable tool.** Until the CSS ships:

- Emit as **plain text with `<br>` separators and a leading `🔄 Refresher:` label** — no `<details>`, no `<table>`.
- **Cap it hard.** Uncollapsed content renders at 36px centred, so a full five-part Explainer is unreadable. Ship the unifying cluster analogy plus the "X is NOT Y" contrasts only; hold the per-term breakdown and the chronology.
- **Declare it:** `Class E degraded — CSS pending, emitted plain-text short form.` Never silently push the long form into a container that cannot hold it.

Once the CSS lands, delete this fallback and use the collapsible as specified.

## STEP 6 — Log, then render (Immutable Source Doctrine)

- **Phase A · Ghost Hunt** — all classification, gating and tool selection **before** any output.
- **Phase B · Commitment Log** — write decisions visibly, then **LOCK** them.
- **Phase C · Read-Only Render** — the proposal list transcribes the log, and the executed calls transcribe the proposal. FORBIDDEN: *sneak-ins* (patching an unlogged card), *audibles* (changing tool between log and proposal), *lazy skips* (logged card missing from the file).

**Then HALT.** Present diagnoses and stop. Never diagnose and emit in one unbroken run.

🚩 **HALT gates the AnkiConnect WRITES ONLY — never the tickets.** Append output 2 to `MEDIC_TICKETS.md` *before* halting. Tickets mutate no card and need no approval, and a ticket left "queued pending go" dies the moment the go never arrives — which is precisely the silence Step 8 exists to prevent.

## STEP 7 — Execute via AnkiConnect. There is no patch file.

**Every change ships through AnkiConnect** — field text, tags, scheduling, suspension. The manual `PATCH.txt` import was retired 2026-08-01: Anki already has to be open for scheduling, so a second channel that needs a human to click Import was pure friction.

| Need | Call |
|---|---|
| Field text | `updateNoteFields` — `{note:{id, fields:{Front:"…", Extra:"…"}}}` |
| Tags | `addTags` / `removeTags` — `{notes:[id], tags:"a b"}` |
| Due date | `setDueDate` — `{cards:[id], days:"0"}` |
| Suspend / restore | `suspend` / `unsuspend` — `{cards:[id]}` |
| Reset progress | `forgetCards` — `{cards:[id]}` |
| Batch | `multi` — one round trip, but **still log each call separately** |

**Never `deleteNotes`.** Deletion stays manual by any channel — it has no undo path through this workflow.

### 🚩 7a. PREFLIGHT — do this FIRST, before the snapshot

The Chief Architect reviews on **AnkiWeb**. If the desktop app is closed or unsynced, the snapshot is missing today's reviews and every diagnosis is built on stale data. **Order matters and is not negotiable:**

🚫 **PREFLIGHT RUNS TWICE — once before the snapshot, and again as the FIRST action after the go.** Hours can pass between diagnosis and approval, and Anki can be closed in between. **Verified failure 2026-08-01:** AnkiConnect answered `v6` during diagnosis, the Chief Architect replied `go`, and the connection was refused — the app had been closed meanwhile.

🚫 **PROBE BEFORE YOU BUILD. One cheap call comes before any script.** The same failure burned a 163-line execution script, a full run, and a Python stack trace to discover a fact that `Get-Process anki` answers instantly. **On `go`, the first thing that happens is the process check — not writing code.** *"All of this was wasted tokens just to say, well, Anki isn't open."*

1. **Is Anki running?** `Get-Process anki`. If not, **LAUNCH IT — do not ask.** Path: `C:/Program Files/Anki/anki.exe` (verified on disk — **forward slashes on purpose**, see below). **Standing permission granted 2026-08-01:** *"I wanted to take over the screen, I don't care… give permission to launch Anki straight away, as soon as I say go."* Announce it in one line and keep going; **never stop for approval**, and never make the Chief Architect discover a closed app from a stack trace.
2. **Wait for AnkiConnect.** Poll `{"action":"version"}` until it answers; the server binds several seconds after the window appears. If it never answers, stop and say so — do not fall back to a stale snapshot silently.
3. **`sync`.** `{"action":"sync"}` pulls AnkiWeb reviews down. **This is the step that is easy to forget and expensive to skip.** Say plainly in the summary whether it ran and what it pulled.
4. **THEN** take the snapshot (Precondition 1). Syncing after the snapshot makes the snapshot a lie.

⚠️ **`sync` is the one write allowed before approval** — it moves nothing of the Chief Architect's, it only reconciles what already exists. Everything else waits for the go.

🚫 **Write Windows paths with FORWARD SLASHES in this file, and in any script you generate.** `C:\Program Files\Anki\anki.exe` contains `\a`, which is a **bell character** in most string literals — and `\P`, `\A`, `\n`, `\t` are equally hazardous. This file has already been corrupted twice by it: the launch path silently became `Ankinki.exe`, an instruction no session could have followed. Windows accepts `/` everywhere, PowerShell included. **If you must use backslashes, use a raw string and verify the result by reading the line back — never trust that it wrote what you typed.**

### 7b. Execution rules

1. **Read freely. Write only after an explicit go.** `findCards`, `cardsInfo`, `notesInfo`, `notesModTime`, `areSuspended`, `apiReflect` need no gate. Every mutating call is numbered in the summary and executed only on approval.
2. **Approval can be partial.** *"go 1,3"* applies those items only. Never treat a partial go as a full one.
3. **Re-resolve immediately before every write.** You diagnosed from a snapshot; AnkiConnect talks to the live collection. Confirm the target through `notesModTime` / `cardsInfo` and **abort that one call, naming the card, if it moved.** There is no import step to make staleness visible any more, so this check is the only thing standing between a stale diagnosis and a wrong edit.
4. **Write the rollback BEFORE the write, not after.** The patch file used to be the undo path; it is gone. Append every touched field's **complete before-value** to `MEDIC_ANNOTATION_ARCHIVE.md` under the run heading first, then execute. A change you cannot reverse is a change you should not have made.
5. **Verify after.** Re-read each touched note and confirm it holds what you sent. Report anything that did not land.

🚫 **AnkiConnect speaks note/card IDs and does NOT know GUIDs** — verified 2026-07-31: `notesInfo` returns `cards · fields · mod · modelName · noteId · profile · tags`, no `guid`. Bridge through the snapshot (`SELECT id, guid FROM notes`; `notes.id` is stable and never regenerated), or address by tag via `findCards` and skip ids entirely.

⚠️ **`cardsInfo.due` is a DAY NUMBER for review cards** — `2113` means days since collection creation, never a timestamp. `setDueDate` takes a **relative day count as a string** (`"0"` = today). Either mistake reschedules to the wrong century without erroring.

**GUID safety:** 7 duplicate GUIDs exist collection-wide. **Abort on any target carrying one** rather than risk touching the wrong note.


## STEP 8 — Tag, archive, report

**Tags** (no external state file — it drifts): `medic::patched::YYYY-MM-DD` · `medic::tool::<tool>` · `medic::junk::proposed` · `medic::junk::partial` · `medic::cleared::YYYY-MM-DD` · `medic::run::YYYY-MM-DD-HHMM` (watermark).

⚠️ **The run tag carries a TIME, not just a date.** Two runs on one day would otherwise write the identical tag, making the watermark unable to tell them apart — and 2026-07-31 had three runs. The date-only form is legacy; read both, and take the maximum.

🚫 **`medic::tool::` is ONLY for repair tools.** Bookkeeping actions — clearing an annotation, tagging junk — made no repair, so scoring their post-patch again-rate is meaningless and it pollutes the one table meant to show which techniques actually work. Measured 2026-07-31: 5 notes carried `medic::tool::clear-only`, which the next run would have dutifully reported an again-rate for. **Use `medic::cleared::<date>` and `medic::junk::*` for bookkeeping; never `medic::tool::`.** Outcome measurement reads `medic::tool::` exclusively.

**Annotation lifecycle:** archive `Medic_Notes` verbatim to a log **first**, then clear it. The annotations are the QA evidence trail.

🚩 **Clear EVERY annotation you processed — including Class J.** A no-op card gets no repair row, so the reflex is to leave its annotation in place; that half-cleans the field and leaves the Chief Architect reading their own stale notes during review. *"Should we instruct skill to cleanup these comments I leave?"* — yes, all of them. Emit a clear-only row (all other fields unchanged) for any note whose annotation you read, whatever the verdict. This is not a sneak-in: the row is in the commitment log, its tool is `clear-only`, and the content is already archived.

⚠️ **Archive the RAW field, not a stripped rendering.** Pasted rich text (a Copilot explainer, a web excerpt) can be 90% markup — one live field measured 23,445 raw chars against 2,560 of text. Stripping before archiving discards the original irreversibly, and `MEDIC_ANNOTATION_ARCHIVE.md` is the only surviving copy once the field is cleared.

**Outcome measurement:** for every previously-patched card, re-read `revlog` and report post-patch again-rate **per tool**. This is how the toolkit learns which techniques work for this user. Without it the skill is only a patcher.

🚫 **Minimum n = 5 reviews per tool. Below that, report `insufficient data (n=N)` and NO percentage.** A patched card is typically rescheduled days or weeks out, so the first run after a patch sees one review or none — measured 2026-07-31, the first four patched cards had **4 post-patch reviews between them and every one passed**, which renders as *"front-edit 76% → 0%"* and reads as a perfect result. It is a coin landing heads once. **Never print a pre→post arrow below n=5**, never rank tools on it, and never let a single passing review retire a card from further attention. Carry the running total forward instead; the table is worth having in a month, not tonight.

⚠️ **Skip `medic::tool::clear-only`** — 5 notes carry it from the 2026-07-31 run, written before bookkeeping and repair were separated. It is legacy, it names no repair, and it has no rate worth reporting. Do not re-tag those notes to fix it; that would cost an import to correct a display artifact.

### 🚩 Answer "was it me or the card?" in plain words — every time, unasked

> *"are cards cues confusing or am I confusing 2 different concepts? Are the fronts bad or am I dont grasping the concept OR reading front cues properly? **If skill handles this well without me being verbose… good, if not skill needs refining.**"*

The class letter already encodes the answer — **Class A/B = the card's fault, Class J = neither, Class C/D/E = the concept needs more scaffolding.** But a letter is not an answer to a person. State it as one sentence per diagnosed card:

- *"Your answer was legitimate — the cue didn't exclude it. Card's fault."* (A/B/F)
- *"The cue was fine; the concepts hadn't separated yet."* (C/D/E)
- *"Nothing wrong — you resolved it yourself."* (J)

The Chief Architect must never have to ask this, and must never have to write the question into a card to get it answered.

### 🚩 The no-op verdict is a first-class, counted outcome

> *"we have to define and not bloat it"* · *"if it's noise, if it's a false positive, ignore it"*

Class J terminates with zero output, **logged and counted**: `3 of 11: no defect — cue misread. No patch emitted.`

A skill built to patch will find something to patch every time. That is Claude Code's Addition Bias, inherited by anything it authors. **Without a counted no-op the deck grows while the failures do not shrink.**

### Ticket output — append to `MEDIC_TICKETS.md`

Card failures, scouting results, forensic findings, upstream defects. **Never append to `prompt_telemetry_database.txt`** — different provenance, and that file's most-repeated entry is a verified false positive.

**Print ALL open tickets with age in days in every run summary.** A ticket must not go quiet — that is exactly how 590 telemetry issues sat unread for two months.

**🚫 Never route a ticket to the Design Council.** Accumulate, age, surface. Routing is a separate Chief-Architect action into a fresh session.

**🚫 Upstream pipeline defects are RECORDED, NOT WORKED.** Scope is card repair.

---

## THE SUMMARY — this is the deliverable. Everything above it is plumbing.

🚫 **DO NOT narrate the run.** No step-by-step, no "now I'll check…", no reasoning shown as it happens, no script output pasted in. The Chief Architect reads this at the end of a study day, often tired. **A technical journal is a failure of the run even when every diagnosis in it is correct.**

> *"reading the whole technical journal log… it's hard to decipher… I just want a section at the end saying what happened, what I need to know, and what I need to approve."*

Report conclusions and the evidence for them. Three blocks, always in this order — **done · decide · know**. Anything that fits none of the three does not go in the summary at all; it goes in a ticket.

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  /medic · <date>          <N> reviewed · <N> failed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ ALREADY DONE — nothing needed from you
   synced AnkiWeb → pulled <N> reviews
   <N> cards diagnosed · <N> no defect · <N> tickets filed
   annotations archived and cleared: <N>

❓ NEEDS YOUR GO — <N> changes
   ┌ 1 ─ FRONT EDIT · <front excerpt>
   │  why    you answered "<their answer>" — <rival> owns that
   │  before <exact text>
   │  after  <exact text>
   └  fault: the card's, not yours

   ┌ 2 ─ SUSPEND · <N> cards
   │  why    buried with Easy on first review, never studied
   │  cards  <list>
   └  reversible with unsuspend

   ┌ 3 ─ RESCHEDULE · <card> + <card>
   │  why    you confuse these two and never see them together
   │  action both due today  (setDueDate "0")
   └  keeps review history

   ▸ reply  go  ·  go 1,3  ·  no

⚠️ WORTH KNOWING — no action
   <one line each, max 4 lines. Anything longer is a ticket.>
```

**Rules for the ❓ block, because this is the part that gets approved:**

- **Show the exact before and after text**, never a description of the change. *"tightened the cue"* is not reviewable; the two strings are.
- 🚫 **Disclose SIDE EFFECTS in the box, not in the report afterwards.** State every state change the call makes, including the ones nobody asked for. Canonical failure 2026-08-01: an Align was approved as *"keeps review history"* and it also **compressed three intervals (15d→2d, 4d→1d, 5d→1d) and graduated a learning card to review.** All of it was true, reversible and honestly reported — *after* execution. **An approval given without the side effects is not informed consent, and disclosing them later does not repair it.** If a call's full effect is not known, say that in the box and let the Chief Architect decide whether to run it.
- **One numbered item per change**, so a partial go (`go 1,3`) is unambiguous.
- **Every item carries a one-line `why` in plain language** — the Chief Architect's own wrong answer where there is one.
- **Say whose fault it was** on every diagnosis: the card's (Class A/B/F), the concept's (C/D/E), or nobody's (J). Never make them ask.
- **Say how to undo it.** Every item, one clause.
- **If the list is empty, say so in one line and stop.** A run with nothing to approve is a good outcome, not an embarrassment.

**Rules for ⚠️ WORTH KNOWING:** four lines maximum. It is for things that change what the Chief Architect *believes*, not things they might find interesting — a card at 100% failure, a measurement that contradicts an earlier one, a tool that could not run. Everything else is a ticket, and tickets are listed by number and age only.

⚠️ **GUIDs break markdown tables.** Anki GUIDs are base91 and routinely contain `|`, `#`, `>` and backticks — `D#3g|gsjxO` is live in this collection. A raw guid in a table cell splits the row. The boxed layout above avoids this; prefer a card's front text over its guid in anything the Chief Architect reads.

### After the go

Execute, then report in **three lines**: what landed, what was skipped and why, what changed on screen. Re-read every touched note to confirm. If anything failed, say which and leave the rest applied — never silently roll back a successful change because a later one failed.


## Task input

$ARGUMENTS
