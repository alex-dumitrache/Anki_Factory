# /shorts — one-minute video mnemonics for cards you cannot picture

> **Job:** turn failing Anki cards into 60-second NotebookLM Shorts, and write the
> public video link into each card. **Nothing else.** Card text, scheduling,
> suspension and tags belong to `/medic`; images, pegs and mnemonics belong to the
> image agent at `Desktop/image_prompts/`.

**Built 2026-08-18** from a full end-to-end walk of the real flow. Every rule below
was earned by something breaking. Do not trim it without reading §0.

---

## §0. Why this file is long

The trimming instinct is wrong here, and that is not a guess — it was tested.

A "lean" version of the prompt template was written by deleting four lines that
looked like filler. The result was a generic overview of the whole topic instead of
the one point asked for. **The deleted lines were the fences.** See §5.

Same shape as `CLAUDE.md` §II Reinvention Bias: the rewrite drops load-bearing lines
you did not know were load-bearing. **Change ONE thing at a time and generate a real
video to check it.**

---

## §1. FATAL PRECONDITIONS — read every time

**1z. NEVER RUN WHILE `/medic` OR THE IMAGE AGENT IS RUNNING — and detect it
MECHANICALLY, do not ask.** Three agents write to this one Anki collection —
`/medic`, the Codex image agent at `Desktop/image_prompts/`, and this skill. **Two
agents writing one collection is silent corruption, not a merge conflict** — no
reconciliation step, no warning, no error.

🚫 **Do NOT stop and ask the Chief Architect whether anything else is running.**
Standing ruling, 2026-08-19: *"shorts skill means judge which cards AND EXECUTE in one
breath, no babysitting."* The question was also the weaker check — a human "yes, clear"
is a snapshot that says nothing about an agent starting thirty seconds later.

**Use `/medic`'s proven guard instead** (`medic.md` Step 7 rule 3): snapshot
`notesModTime` for every target note at diagnosis, re-read it immediately before each
write, and **abort that single write, naming the note, if `mod` moved.** It catches a
concurrent writer that a human confirmation cannot, and it costs one call.

⚠️ **Abort the one write, not the run.** A moved note means that note is contested;
the other fifteen are not. Report which were skipped and why (§10).

### 1z-i. "One breath" bans ASKING, not REPORTING — and permits a planned split

Two clarifications from the Chief Architect, 2026-08-19, that a literal reading of the
rule above would get wrong in opposite directions.

**A report is not a question.** *"I want no decision from me, I don't want the friction
and ideally you would figure out what cards and what concepts are hard."* Showing the
selection is **transparency, not an approval gate** — print what was chosen, what was
refused and why (§10), then keep going. 🚫 **Never end a report on "shall I proceed?"**
Their concern about pre-empting a concept that turns out to be easy is answered by
*seeing* the list, not by being asked to sign it off.

**A two-step run is allowed when the analysis is genuinely hard — if THEY split it.**
*"You are allowed to do it in 2 steps, first analyse which cards, then after that we
will actually create them, as this is a hard analysis initially."* Note the licence is
theirs to grant. **The default remains one breath**, and the split is a per-run
instruction, never a habit to drift back into. 🚫 **Do not invent a split** because a
batch feels large; that is the babysitting the rule exists to kill.

### 1z-ii. Discovering the ceiling is a legitimate run mode

*"Consider the ceiling… but let's break the limit. Plan for more so you can actually
see limits."* When asked to probe, **plan MORE shorts than the cap allows on purpose**
and let §6a's count check trip. Hitting the limit is then **the measurement, not a
failure** — record which account stopped, after how many, and the exact message.
⚠️ Say up front that the tail of the plan is expected to be refused, so a partial run
does not read as breakage.

**1y. USE THE BROWSER THAT HAS THE GOOGLE SESSIONS.** This work runs in the real
Chrome (`claude-in-chrome`), never the in-app preview browser — the in-app browser has
no Google session and lands on `accounts.google.com/signin`. 🚫 **A sign-in wall is not
an obstacle to solve. Never type a credential.** Switch surface instead (§11).

✅ **The logged-out browser is an ASSET, not a dead end.** It is the only honest test of
whether a share link works for someone without a Google account — which is the entire
point of this feature. Open the **artifact** URL in it and confirm a `<video>` element
renders with no permission wall. Proven 2026-08-19 for both notebooks.
⚠️ **Test the ARTIFACT url, never the NOTEBOOK url** — notebook URLs demand sign-in
even when sharing is correctly set, so testing one reports a false failure.

**1a. `authuser=N` IS NOT A STABLE ACCOUNT IDENTIFIER.** The index renumbers when an
account is added or removed. Measured 2026-08-18: `authuser=2` was one account at
16:00 and a different one at 17:30, after a third account signed in.

🚫 **Never trust the index. Verify identity on the page before every generation:**

```js
document.querySelector('[aria-label*="Google Account"]').getAttribute('aria-label')
// → "Google Account: KotyAle327  \n(account2@example.com)"
```

If the email is not the one the registry expects, **STOP.** Do not generate. Videos
made on the wrong account are not an error you will see — they just end up somewhere
else, under a different sharing state.

**1b. THE DOM IS THE TRUTH. SCREENSHOTS LIE.** Twice a screenshot appeared to show a
preset chip selected; `aria-pressed` was `false` both times, because the "checkmark"
is a hidden icon that is always in the markup. **Read state via JS, not from pixels.**

⚠️ **And read it in a SEPARATE call from the click.** Angular commits `aria-pressed`
asynchronously, so a state read in the same call that clicked is a race against the
framework, not a measurement. Measured 2026-08-19: a click on Custom topic read back
`aria-pressed="false"` in the same call and `"true"` moments later in the next one.
**Clicking and verifying in one call will report failures that did not happen — and
would eventually report a success that did not either.**

**1c. THE DIALOG RE-LAYS-OUT AT LEAST TWICE.** Selecting "Short" removes the
visual-style row (~70px shift). The three preset chips sometimes do not render at all
(~24px shift). **Never click by coordinate in this dialog.** Locate by text or
placeholder and click through the DOM.

**1d. A CHECK YOU PRINT BUT DO NOT ENFORCE IS NOT A CHECK.** A write script printed
`no leftover details: False` and wrote anyway, leaving a card with two video blocks.
**Every gate aborts.** `if not all(gates.values()): sys.exit(1)`. No exceptions.

**1e. `cat file | clip.exe` CORRUPTS UTF-8.** It turned the page emoji into `≡ƒôä` and
every em-dash into `ΓÇö`, inflating a 50,089-character file to 50,610 garbage
characters. **Use `Get-Content -Raw -Encoding UTF8 <file> | Set-Clipboard`.** The
console printing `??` is display only — **the character count is the honest test.**

**1f. THE ARTIFACT ID IS STALE UNTIL YOU RELOAD.** Angular recycles the tile and keeps
the *previous* artifact's ID in its `jslog`. **Reload the notebook page, then
harvest.** After reload the still-generating tile carries its own real ID. Proven:
`4e72c66c` read mid-render equalled `4e72c66c` final.

---

## §2. WHICH CARDS — selection

### Invocation — the scope of the run

**Same argument grammar as `/medic`, deliberately.** One skill's invocation should
not surprise someone who knows the other.

| Form | Meaning |
|---|---|
| *(none)* | the default candidate set below — failing, never graduated, first seen in the last 3 days |
| `7` / `30` | widen the first-seen window to N days |
| `new` | **skip the failure filter** — take unseen cards (`cards.queue = 0`) in due order |
| `<deck name>` | restrict to one deck |
| `<guid>` | one specific card |

*(Chief Architect, 2026-08-18: "I want to tell the skill to create me shorts, and
link shorts, for all decks — not all decks, all cards created last… yesterday, for
example, or whatever." The run is scoped by argument, never assumed.)*

### The default candidate set

**Filter on review history, never on due-ness.**

🚫 **"Due now" is a clock artifact.** The same deck yields 13 cards or 20 depending on
what minute you run — learning steps are 20 minutes, so cards drift in and out of
"due" continuously. A skill built on it gives different answers to the same question
an hour apart and you cannot tell which run was right.

**Candidate = a live `Basic+` card that:**

- has **at least one `revlog.ease = 1`** (an Again), and
- has **never graduated** — no `revlog.type = 1` anywhere in its history, and
- was **first seen in the last 3 days**.

```
per card:  revs       = SELECT id, ease, type FROM revlog WHERE cid=? ORDER BY id
           again      = count(ease = 1)
           graduated  = any(type = 1)
           first_seen = revs[0].id
```

**Exclusions, all mandatory:** `cards.queue = -1` (suspended) · note already contains
the film emoji · note tagged `medic::junk::*`.

🚫 **Never query `cards.lapses`** — it only increments on review-stage failures, so it
reads 0 for exactly these cards. Use `revlog`.

### 🚩 This filter sees ONE of two problem populations. Know which you were asked for.

**Never-graduated** = still being learned, failing on the way up. **Lapsed** = knew it,
then forgot — `revlog.type = 1` with `ease = 1`, which `medic.md` §2a calls *"the real
signal."* The default set above is **never-graduated only, by design**: a first-time
struggle is where a visual usually unlocks the concept.

**Measured 2026-08-19 — unlinked, unsuspended `Basic+` notes:**

| window | never graduated | lapsed |
|---|---|---|
| 3 days | 10 | 0 |
| 7 days | 11 | 3 |
| 30 days | 13 | **97** |
| 90 days | 13 | **260** |
| all time | 31 | **670** |

⚠️ **The lapsed pool is roughly twenty times larger.** So *"do all my problem cards"*
and *"run `/shorts 30`"* are not the same request — the default filter would show 13
notes against a real backlog of hundreds. **Ask which population, or say plainly which
one you ran**, and remember the daily cap is ~6 per account: 670 notes is months of
generations, so a lapsed run needs the §3 value test and §4 dedup doing real work, not
a queue drained top to bottom.

🚩 **`getReviewsOfCards` takes INT card ids. Given strings it returns `[]` for every
card — silently, with no error.** Measured 2026-08-19 on the first real run of this
skill: the query reported *"0 of 2407 Basic+ cards have any review history"*, which is
a clean, plausible-looking empty set and would have sent the run straight to §2's
new-card fallback for the wrong reason. The same call with ints returned 2,181 cards
with history and 20 candidates. **Pass `cards=[int, int, …]`, never `[str, …]`.**

⚠️ **A zero that agrees with your filter is the one to distrust.** The tell was not in
the query — it was that `medic.md` §2a records 9,514 measured learn-stage Agains in
this collection, so "no card has ever been reviewed" was arithmetically impossible.
**Cross-check any empty result against a number already written down** — here,
`findCards note:Basic+ is:review` → 2093, which needs no revlog call at all.

### 🚩 Judging difficulty WITHOUT review history — the `new` population

*"Not sure if it's a good idea to make cards prematurely for new cards. What if the
concept will be easy for me?"* — Chief Architect, 2026-08-19. A valid worry: a new card
has **no Agains, no lapses, no evidence of anything.** Every other population in this
file is selected by measured failure; this one cannot be.

**So the skill must predict difficulty from the card's own text.** That is the job it
was asked to do — *"ideally you would figure out what cards and what concepts are hard
and benefit from visuals"* — and it is a judgement, not a query.

**A new card is a candidate only if BOTH hold:**

1. **§3's shape test passes** — the answer is a mechanism or force, not a name, number
   or list. Unchanged, and still the first gate.
2. **The mechanism is one you could not arrive at by reasoning from the words.** The
   card describes something *counter-intuitive, invisible, spatial, or simultaneous* —
   opposite charges attracting across a gap, four things happening at once, a part
   moving against another part. If a competent reader could infer the answer from the
   Front alone, a video teaches them nothing they were going to miss.

🚫 **Being merely unfamiliar is NOT difficulty.** An unknown term is a vocabulary
problem and belongs to the image agent's mnemonics. Difficulty here means *the
mechanism resists imagination*, which is the same property §3 selects for — applied
predictively instead of retrospectively.

⚠️ **Be stricter with new cards than with failing ones, and say so in the report.** A
failing card has already proven it needs help; a new card is a bet. Mark every new-card
short as **pre-emptive** in the run report so a later review can ask whether the bet
paid — that is the only way this population ever gets calibrated.

📊 **Measured 2026-08-19: this population yields almost nothing, and that is the correct
result.** Of the first 70 unlinked new notes in due order, **4 passed the shape test**,
and all four were already covered by an existing short or belonged to the image agent.
The Chief Architect's worry — *"what if the concept will be easy for me?"* — is answered
by the arithmetic: the shape test alone refuses 66 of 70 without needing to predict
anything about difficulty. **Do not force a quota out of new cards.** If the honest
answer is "nothing here", say so and spend the generations on the lapsed pool.

### 🚩 "Most fragile" — ranking the lapsed pool

The lapsed population is ~670 notes (§2 table) against a cap of ~18/day, so **selection
is the whole job.** *"Do the most fragile out of the 670"* — Chief Architect,
2026-08-19. Fragile ≠ merely lapsed once. Rank on measured evidence, strongest first:

| Signal | Read from | Why it means fragile |
|---|---|---|
| **repeat lapses** | count of `type=1, ease=1` | learned and forgotten **more than once** — the single strongest signal |
| **relearn failures** | count of `type=2, ease=1` | failed again *while recovering*; `medic.md` §2a: "the card is fighting back" |
| **short surviving interval** | `lastIvl` at the lapse | forgot it despite a **recent** review — decay is fast, not just eventual |
| **again-rate** | Agains ÷ total reviews | separates a card that fails often from one that failed once long ago |
| recency of last lapse | newest `type=1, ease=1` | tiebreak only — an old lapse on a now-stable card is not fragile |

🚫 **Do not rank on lapse COUNT alone.** A card reviewed sixty times with three lapses
is healthier than one reviewed four times with three lapses, and count alone puts them
in the wrong order. Use rate and repetition together.

### 🚩 VALUE TEST FIRST, THEN RANK. Never rank first.

**Fragility and video-suitability are close to ANTI-correlated, and this is the single
most important thing measured on 2026-08-19.** Ranking 670 lapsed notes by fragility
and reading the top 34 produced: a geography deck, port numbers, DDR5 pin count, SXGA
resolution, Mini-ITX dimensions, and the acronyms TACACS, ACL, VGA and NIC. **Two
entries in the top 34 were video-shaped.**

That is not a flaw in the ranking — it is what fragility *is*. **Arbitrary facts are
what people forget; mechanisms are what they remember once they have seen them.** The
most-forgotten cards are therefore mostly peg and mnemonic territory, owned by the
image agent, not by this skill.

**So the order is: apply §3's shape test to the whole pool, THEN rank the survivors by
fragility.** Ranking first wastes the analysis on cards that were never candidates, and
worse, it *looks* productive — a tidy list of the most-failed cards that this skill must
refuse almost entirely. Measured the same day: **670 lapsed → 92 survive the shape test
→ the strongest dozen are worth generating.**

⚠️ **A high-fragility card that fails the value test is not a near-miss.** It is a card
the image agent should be told about. Report it as routed, not as rejected.

### Fallback — when the filter returns nothing

**Do not report "nothing to do."** Fall back to **new cards** — `cards.queue = 0`, in
due order, still subject to §3's value test. *(Chief Architect, 2026-08-18: "and if no
reviews, take new cards.")*

⚠️ **Say which set was used, in the run report.** A run over new cards is doing a
different job from a run over failures — pre-empting a struggle rather than answering
one — and the report must not blur the two.

---

## §3. WHICH OF THOSE DESERVE A VIDEO — the value test

> **A short earns its place when the answer is a process or force you cannot see, or
> must watch happen.**
> **A short is wasted when the answer is a name, a number, or a list.**

### Why this beats the lecture it came from

Confirmed by the Chief Architect 2026-08-19, after the first real run:

> *"I now have permanently burned into my retinas how fuser assembly looks and works.
> Better than lecture, NotebookLM deep dive. Because it's something I actually SEE.
> And I see it as it's linked to card so I see it just at the right time with Anki
> reviews."*

**Two separate claims, and the second is the architectural one.**

1. **Seeing beats hearing** for a mechanism — which is what §3's test above already
   selects for.
2. **Delivery timing is half the value.** The video arrives *at the moment the card is
   failed*, inside the review, with no decision to go and watch anything. A lecture
   and a deep dive both put the burden of "remember to go look this up" on the person.

🚫 **This is why the link lives ON the card and why there is no video library, no
playlist and no shorts deck.** §8 defends that on findability grounds — *the link IS
the index* — but the real reason is pedagogical: **a video you have to navigate to has
already lost the property that makes it work.** Any future proposal to collect these
somewhere central is a downgrade wearing the clothes of an improvement.

| The answer is… | Tool | Owner |
|---|---|---|
| a number | 🔢 peg / Major System | image agent |
| a name or acronym | 🚀 mnemonic | image agent |
| a **static** thing — a shape, a layout, a part you could photograph or draw once | 🖼️ image / diagram | image agent |
| **something that HAPPENS — over time, or across a distance** | **📽️ short** | **this skill** |

### 🚩 "Visual" does NOT mean "hardware". Correct this on sight.

> *"Don't necessarily code into the skill that it has to be hardware. It has to be
> visual. No. Because we can visualize the journey of a packet, starting from your
> computer, DNSing, querying the DNS, going to the top level domain. Their journey has
> to go there. We can make it visual — if it benefits from that."*
> — Chief Architect, 2026-08-19

**The test is whether it can be SHOWN HAPPENING, not whether you could touch it.** A
DNS resolution, a TCP handshake, a packet traversing NAT, a certificate chain being
walked, a VLAN keeping two flows apart, a RAID rebuild reconstructing a lost disk —
every one of these is a journey through space and time, and every one is a legitimate
short. **Protocols and abstractions animate as well as gears do**, sometimes better,
because the diagram in a textbook is already the standard way they are taught.

🚫 **Do not read the printer examples in this file as a statement about the domain.**
They are simply what the first runs happened to cover. If a rule here says *"the inside
of a printer"*, it means *"the layer the learner cannot see"* — which for software is
just as real and just as hidden.

### 🚩 TRIGGER TWO — the card presupposes a concept the learner does not hold

**Everything above asks: is the ANSWER mechanism-shaped? That is not the only way a
card fails.** A card can have a perfectly ordinary name-shaped answer and still be
unlearnable, because **a term in the QUESTION means nothing to the reader.**

The canonical case, raised 2026-08-19 — note `1786875801511`:

> Front: **Modern Laser Printers (Real-world corona-wire replacement)?**
> Back: **A primary charge roller (PCR) built into the toner cartridge.**

> *"I don't know what a corona wire is. What it does. I'm connecting two unknown
> concepts with this flashcard. And of course I'm going to fail it, because I'm going
> to have to go and do research on what a corona wire is. The card doesn't explain it."*

**Read the card and confirm it: neither field ever says what a corona wire DOES.** The
Logic line explains only that the exam still expects the old term. The card is a
mapping between two nouns, one of which the learner has never been shown. **No amount
of re-reading fixes that**, which is exactly why it fails repeatedly.

**This is a DIFFERENT trigger from the shape test and must be checked separately.**
§3's table would refuse this card — the answer is a name — and refusing it is the wrong
call, because the card's problem was never its answer.

**How to detect it:** for each card, list the nouns in the Front and Back. **Does the
card itself, anywhere in any field, say what each one IS or DOES?** If a load-bearing
term is only ever named, never explained, the card carries a prerequisite gap.

**How to fix it — cheapest first:**

| Fix | When | Owner |
|---|---|---|
| **inline gloss** (`<label class='acro'>` pattern, `MEDIC_TICKETS.md` T26) | the gap is a term whose *expansion* resolves it | **`/medic`** |
| **🖼️ image / diagram** | the gap is *what it looks like or where it sits* | image agent |
| **📽️ refresher short** on the PREREQUISITE (not on this card's answer) | the gap is *what it does and why* | **this skill** |

🚫 **The refresher short is about the prerequisite concept, not about this card.** For
the card above, the right video answers *"what does the charging step do, and why does
the drum need a uniform charge before the laser writes on it"* — a question this card
never asks. Generating a short about "what replaced the corona wire" would explain the
answer the learner already has and skip the one they are missing.

⚠️ **T26's exclusion still binds: a card that EXISTS to test a term gets no help.**
*"Acronym-expansion cards get NO help, ever… that's the whole point of getting tested on
the acronym."* Note `1786875801511`'s **inverse** direction asks for the legacy term and
answers *"Corona Wire"* — glossing it there destroys the card. **The forward direction
is not testing what a corona wire is**, so it may be helped. Check direction before
touching anything.

✅ **T26 already settled the principle in 2026-08-01, for acronyms:** *"'The lecture
explained it' is not a defence. Exposure is not retention… A gloss costs one click and
nothing else; assuming prior knowledge costs a failed card and a Google search."* This
trigger is that same finding applied to **concepts** rather than abbreviations. It is an
extension of proven infrastructure, not a new mechanism.

### 🚩 TRIGGER THREE — the card states a dry fact and never grounds it

**`MEDIC_TICKETS.md` T27, raised 2026-08-05:** *"The deck teaches what a thing IS, never
where the learner would MEET it."* In the Chief Architect's words:

> *"These concepts are so dry. There's no anchoring. Nothing telling us what are these?
> Give us an example. A real world example… For example, DNS caching. When you explain
> it as a dry fact — but when you relate it to a real world user encountered event,
> where you see, for example, in the corner of the browser."*

T27 names three wanted outputs and records the first as having **no mechanism at all**:
*vivid examples — where you'd meet it: none, 0.8% delivery, no sweep is pointed at
instantiation.* **A sixty-second short IS that missing mechanism.** Showing a concept
happening in a situation the learner has personally witnessed is the one thing this tool
does better than any card edit.

⚠️ **The Chief Architect raised DNS as the example for T27 on 2026-08-05 and again,
independently, on 2026-08-19.** The same concept, the same complaint, two weeks apart.
Treat a repeated example as a specification, not an anecdote.

**Trigger three fires when:** the card is correct, its answer is not confusable, and the
learner still cannot say where this would appear in their own life. **The short answers
"where would I run into this?"**, not "what is it" — the card already did that.

---

### 🚫 WHAT A SHORT CANNOT FIX — check this BEFORE generating anything

**The dominant failure mode in this collection is NOT comprehension, and a video is
powerless against it.** From the 124 annotated sentences in `MEDIC_FEEDBACK_LEDGER.md`,
written at review time:

| Their words | Class | Real cause | Owner |
|---|---|---|---|
| *"I answered answer from different card again"* · *"I was thinking of the answer… FOR A DIFFERENT CARD THAT I REVIEWED before this one"* · *"Cue, front of cards should be unique, point to a single answer"* | **B — cue collision / priming bleed** | two cards share a cue | `/medic` + **T1 · T2 · T15** |
| *"SNMP and SMTP, maybe user thinks theyre the same thing… they look the same, I skimmed and did not register the difference in spelling"* | **G — acronym collision** | two strings look alike | 🚀 mnemonic, image agent · **T12** |
| compound Backs hiding partial knowledge | atomicity | one card asks two things | **T14**, pipeline |

### ⚠️ These axes are INDEPENDENT. Do not collapse them into one.

> *"It depends. If card is bad AND novel concept I am more likely to fail. They are
> independent of each other, or should be considered as such."*
> — Chief Architect, 2026-08-19, correcting the first draft of this section

**Cue quality and concept comprehension are two separate variables**, and a card sits
somewhere on both:

| | **cue is unique** | **cue collides with a sibling** |
|---|---|---|
| **concept understood** | card is fine — it failed for some other reason | **`/medic` only.** A short explains what they already know |
| **concept NOT held** | **short only** — triggers one, two or three | **BOTH, and this is the worst card in the deck.** It fails for two independent reasons and fixing either one alone leaves it failing |

🚫 **The bottom-right cell is why "skip every cue-collision card" is wrong.** An earlier
draft of this section said exactly that. It would have refused the cards that need this
tool *most* — the ones where a confusable cue sits on top of a concept never understood,
which is precisely the combination the Chief Architect named. **A collision flag is not a
disqualification.** Generate the short, and report that the card also needs `/medic`.

✅ **What a collision flag DOES mean: a short alone will not close the card.** Say so in
the report so a card that keeps failing after a video is not read as the video failing.

⚠️ **And beware the sampling bias that produced the wrong draft.** Cue collisions
dominate the *annotations* because they are surprising enough to write about —
*"I answered the answer from a different card again"* is a noticeable event. A concept
quietly never understood produces no annotation at all; it just fails. **Annotation
frequency is not failure frequency**, and reasoning from the ledger's most-repeated
complaint to "the dominant failure mode" was an inference the data does not support.

✅ **The one class that IS ours, in their words:** *"it's all fragments I'm reviewing bit
by bit and I don't have the full picture."* (Class E, 2026-07-29.) **That sentence is
this skill's charter.** The corona-wire complaint of 2026-08-19 is the same sentence
said again about a different card.

### Detecting triggers two and three mechanically — and the two traps

**Measured 2026-08-19 across 1,015 failing/lapsed unlinked notes:** T1 175 · T2 44 ·
T3 42 · T1+T2 34 · T1+T3 22 · T2+T3 8 · all three 6. **331 flagged, 684 not.** Those
proportions are the sanity check — a detector that flags most of the deck is broken.

🚫 **Trap one — a term index built from short Backs matches generic nouns.** The first
T2 detector indexed every card whose Back is 1-4 words as "the card that defines this
term", then flagged any candidate whose Front contained one. Because some card's answer
is literally *Device*, *Network* or *Client*, it reported *"presupposes: device,
network, physical"* on almost everything. **Require a real term:** two or more words, or
an all-caps acronym, and a stoplist of the generic nouns this deck uses as answers.

✅ **And add the condition that makes T2 meaningful: is the PREREQUISITE card itself
unlearned?** A card presupposing a concept the learner has already mastered is fine.
The signal is a *chain* — this card depends on another card that is new or also failing.

🚫 **Trap two — "has no example anywhere" is not a T3 detector.** It matched 930 of
1,028 notes, because almost no card in this deck carries a scenario. A filter that
selects nine tenths of the pool has measured the deck's house style, not a defect.
**Sharpen it to the shape T27 actually names:** the Front is an *identity or definition
probe* — `(What it does)`, `(Main job)`, `(Primary function)`, `(Identity)`, `What is X`
— **and** no situation appears anywhere in the note. That lands on 42.

⚠️ **Both traps produced confident, plausible, well-formatted output.** Neither threw.
The tell was the count: a trigger that fires on ninety percent of a deck is describing
the deck.

### 🚩 The most fragile cards keep landing on missing transcripts

**Observed twice in two days.** 2026-08-18: RAID 5/6 parity — the two most fragile
mechanism cards in the collection, no lecture. 2026-08-19: the routing table card
(5 lapses, 3 relearn failures, the highest-scoring card in the whole shortlist) — no
lecture. Guest SSID/VLAN and AAA/RADIUS the same day.

**This is not a coincidence to note in passing — it is a standing instruction.** When a
top-ranked card is blocked on source, **say which lecture is missing, by topic, in the
run report.** The Chief Architect can obtain a transcript; they cannot act on a card
that silently vanished from a shortlist. **A blocked card is a request, not a skip.**

**Worked examples from the real batch:**

- ✅ `…513` why toner sticks to exposed areas — invisible electrostatics
- ✅ `…514` roller and separation pad working against each other — moving parts
- ✅ `…526` four colours accumulating on a belt — spatial process
- ❌ `…522` "Cleaning blade" — one word
- ❌ `…510` −400V to −600V — **a number**, belongs to the peg system
- ❌ `…524` CMYK — a list, belongs to a mnemonic

---

## §4. BATCH ANALYSIS — deduplicate before generating

**Output is `short → [cards]`, never `card → short`.** One video routinely answers
several cards, and the daily cap makes that the difference between 6 cards covered
and 12–15.

**Proven case:** *"How Laser Printers Use Relative Voltage"* states toner −300V,
unexposed −400V, exposed −150V. That fully answers **both** `…513` (why toner sticks
where it does) and `…512` (what the charge drops to at the struck spot). One
generation, two cards.

**Before generating, group candidates by the mechanism their answer describes.** If
two cards would produce the same sixty seconds, generate once and link both.

⚠️ **This is NOT "one explainer per topic"** — that was considered and rejected. This
is: do not spend two of six generations saying the same thing twice.

---

## §5. THE PROMPT — template, never improvised

🚫 **Do not write a bespoke prompt per card.** Freelanced instructions are what broke
the first attempt. The card already contains the three pieces that matter; slot them
in and get out of the way. **A fixed template also makes failure diagnosable:** same
template every time, so a bad short means a bad card, not a mystery.

### 5a. The fence mirrors the card's own scope

**Read the Back field: does it name ONE fact, or a SEQUENCE?** That is a lookup, not a
judgement call.

**NARROW card** — Back names one mechanism, value or relationship:

```
Explain ONLY this one point, in 60 seconds, for someone who has never seen
the inside of a {DOMAIN}. Show the physical mechanism, not a summary.
QUESTION I MUST BE ABLE TO ANSWER: {FRONT}
THE ANSWER: {BACK}
Make the WHY visible: {the mechanism, spelled out}
Emphasise {secondary detail}                  <- optional; IS honoured
Do not cover the other {TOPIC} steps.
```

**BROAD card** — Back names a chain of stages:

```
Cover the complete {PROCESS} end to end, in order, in 60 seconds, for someone
who has never seen the inside of a {DOMAIN}. Show the physical mechanism.
QUESTION I MUST BE ABLE TO ANSWER: {FRONT}
THE ANSWER: {BACK}
Do not go deeper into any single step than the others.
```

**ABSTRACT / SYSTEMS card** — the subject is a protocol, a flow or a boundary rather
than a physical assembly. Same fences, phrasing that does not assume a chassis:

```
Explain ONLY this one point, in 60 seconds, to someone who has never seen how
{SYSTEM} actually works under the hood. FOLLOW THE PATH — show where it starts,
each hop it makes, and what changes at each hop. Not a definition, not a summary.
QUESTION I MUST BE ABLE TO ANSWER: {FRONT}
THE ANSWER: {BACK}
Make the WHY visible: {what moves, what blocks it, what it becomes}
Do not cover the other {TOPIC} concepts.
```

#### The analogy pattern — validated by the Chief Architect's own paste

**For a cluster of abstractions that differ by LAYER rather than by function, map the
whole cluster onto one concrete physical scene.** This is not a stylistic suggestion:
they pasted this into a card themselves as the model of a good explanation
(`MEDIC_FEEDBACK_LEDGER.md` row 15, 2026-07-29), and `medic.md`'s 5-part explainer
structure was copied from it.

> *"These terms get confusing because they all deal with security for email, but they
> operate at different layers. **Think of sending a letter:** MIME = how the letter is
> packaged. S/MIME = putting a signature/seal on it so people know it's really from you.
> SSL/TLS = the secure courier transporting it. STARTTLS = asking the courier to switch
> to a secure vehicle after the journey has started. Implicit TLS = using a secure
> vehicle from the very beginning."*

**One scene, every member of the cluster placed inside it, differences visible as
positions in that scene.** Add to the abstract template when the card sits in such a
cluster:

```
Use ONE concrete real-world analogy and place every term inside it, so the
differences are visible as different parts of the same scene. Name the analogy
before using it, and do not switch analogies part-way.
```

⚠️ **This is the answer to "how do you make software visual."** A protocol has no
appearance, but a courier, a sealed envelope and a switched vehicle do — and the layer
distinction that the flat text hides becomes a position you can point at.

🚫 **Do not force an abstract topic through the hardware wording.** *"Never seen the
inside of a DNS"* is nonsense and produces a definition instead of a journey. **"Follow
the path" is the abstract equivalent of "show the physical mechanism"** — it is what
stops the model reciting a glossary entry.

**All three are fences.** The narrow one fences out breadth; the broad one fences out
depth; the abstract one fences out *definition mode*. **A summary is not a failure when the card itself is a summary** — it is the
correct output for a card like *"How does a laser printer create a permanent image on
paper?"*, and that exact video is now attached to that exact card.

### 5b. Which line becomes "do not confuse it with"

`⚠️ NOT` first · `Delta` if there is no NOT · `Logic` if there is neither · omit the
line if the card carries none of the three. They are not interchangeable: NOT kills a
rival answer, Delta separates two cards, Logic explains why the answer follows —
weakest as a discriminator, which is why it is last.

⚠️ **One line only — and one idea was never tested.** The Chief Architect's opening
proposal was to paste the *whole* card: *"with the logic, with the not, with the delta,
with everything… the more information, the better"* (2026-08-18). That was said before
the fence mechanics were understood, and **it has never been run against the template.**
Do not adopt it silently and do not dismiss it — it is a clean one-variable experiment
that someone should actually perform.

### 5c. What NOT to delete

These read like filler and are not:

- *"Explain ONLY this one point"* — scoping
- *"not a summary"* — **explicitly bans overview mode**
- *"Do not cover the other {TOPIC} steps"* — the hard fence
- *"Make the WHY visible: …"* — directs what to show

**NotebookLM's default behaviour is to summarise its sources.** Unfenced, it reverts
to that. It does not stay focused "instinctively" — it must be told twice, in
different words.

---

## §6. GENERATING — the UI walk

**Per short, in order:**

1. **Verify account identity** (§1a). Wrong email → STOP.
2. Navigate to the notebook for this topic on this account (§9 registry).
3. Click the **Video Overview** tile's chevron in the Studio panel.
4. Click **Short** — locate by text, not coordinate (§1c).
5. Focus the custom-topic box **through the DOM**:
   `[...document.querySelectorAll('textarea')].find(t => t.placeholder === 'Describe your own').focus()`
   🚫 Clicking it by coordinate lands on a preset chip after the layout shift, and the
   typed text vanishes silently.
6. Type the prompt. **Verify `textarea.value.length` before continuing.**
7. Confirm no preset chip is selected — all `aria-pressed === "false"`.
8. Click **Generate**, located by its text.
9. **Confirm a new "Generating…" tile appeared.** If the count did not increase,
   something blocked it — **STOP, screenshot, report what is on screen.**

### 6a. Daily limit

Roughly 6 videos per account per day, then, verbatim as of 2026-08-19: *"You have
reached your daily Video Overview limits, come back later. Or upgrade."*
⚠️ Note **"limits"**, plural — this file recorded it singular for a day. Another reason
step 9's count check, not the string, is the detector.

🚫 **Do not match that string.** Step 9's count check catches the limit, a network
failure, a changed dialog, a new consent screen and anything Google invents next,
**without knowing what any of them say.** When it trips, record the exact message in
the run report so the specifics can be encoded later.

On limit: move to the next account in the registry (§9). Three accounts is roughly
18 per day.

🚩 **A notebook whose sharing is UNVERIFIED outranks the quota heuristic below.**
Generating into a notebook that strangers cannot open produces links that are dead on
arrival, and the daily cap only matters when the run is actually near it — a 3-short
run has no quota problem to solve. **Prefer a notebook proven shareable; if you must
use an unproven one, verify it logged-out (§1y) in the same run.**

⚠️ **Try a PLUS account first.** `account2@example.com` carries a **PLUS** badge
(observed 2026-08-18) and its ceiling may be higher than 6. Order the registry so
the highest-allowance account is worked first — the limit is the binding
constraint on a run, so spending the cheapest allowance last wastes the most.

---

## §7. HARVESTING THE LINK — no waiting

**Reload the notebook page** (§1f), then read every artifact tile:

```js
const nb = location.pathname.split('/')[2];
[...document.querySelectorAll('artifact-library-item')].map(e => {
  const ids = new Set();
  e.querySelectorAll('[jslog]').forEach(x => {
    const m = (x.getAttribute('jslog') || '').match(/0:([A-Za-z0-9+/=]{20,})/);
    if (!m) return;
    try {
      (atob(m[1]).match(/[0-9a-f-]{36}/g) || []).forEach(u => { if (u !== nb) ids.add(u); });
    } catch (err) {}
  });
  return `https://notebook.google.com/notebook/${nb}/artifact/${[...ids][0]}`;
});
```

**The ID exists from the moment you press Generate.** The videos light up on their own
as each render finishes. **Never wait for rendering.**

🚩 **HARVEST AFTER EACH `Generate`, NOT ONCE AT THE END.** *"Fire all N, reload once,
harvest all N"* was the original instruction and it is **wrong for N > 1**: a tile that
is still generating renders as the literal string *"Generating Short Video Overview…
This may take a while"* — **no title, no timestamp, no prompt echo, and no attribute
that distinguishes it from the other two.** Measured 2026-08-19 on the first real run:
three shorts fired back to back produced three identical tiles and three IDs with no
way to tell which ID belonged to which prompt. **The mapping is unrecoverable** — the
only remaining options were to wait for titles or to guess, and guessing writes the
wrong video onto a card.

✅ **The fix is on the artifact page, and it needs no extra reloads.** Open
`…/artifact/<id>` and click **"View prompt and 1 source"** — it renders the exact
custom prompt that produced that video, verbatim, **while it is still generating.**
Batch-firing is therefore safe: fire all N, harvest all N ids, then confirm each id by
reading its own prompt back. Proven 2026-08-19 — three ids fired blind were each
identified with certainty in one page load apiece, before any had a title.

```js
[...document.querySelectorAll('button,[role="button"],a,span,div')]
  .filter(e => /View prompt/i.test(e.innerText||'') && (e.innerText||'').length < 60)
  .sort((a,b)=>a.innerText.length-b.innerText.length)[0].click();
// then read: body.innerText.match(/QUESTION I MUST BE ABLE TO ANSWER:[^]{0,150}/)
```

⚠️ **Confirm every id this way before writing. Never infer from tile order.** Order does
appear to be newest-first, and on this run that inference would have been correct —
which is exactly why it is dangerous. A wrong link is silent: the card opens a video
about the wrong mechanism and nothing errors.

*(An earlier draft of this section, written mid-run, mandated a reload after every
`Generate` as the workaround. Superseded within the same run — the prompt-echo control
is deterministic, cheaper, and works retroactively on ids already fired.)*

**The `?utm_*` tail is unnecessary** — the bare URL works publicly.

---

## §8. WRITING TO ANKI

**Format — exactly this, and it goes at the START of `Extra`:**

```html
<a href='{URL}' style='text-decoration:none;'>📽️</a><br>{existing Extra}
```

🚩 **PREPEND. Appending is destructive-by-rendering.** A bare `<a>` segment matches
neither the card template's marker branch nor its `<details>`/`<label>` passthrough,
so it falls to the `else` branch and gets folded **inside the previous collapsible** —
invisible until you open the NOT box. Prepended, it lands in `lead` and renders as a
bare clickable emoji, which is what the Chief Architect asked for.

### A card may carry MORE THAN ONE video. The gates must allow it.

> *"You can tag more than one video. If it's talking about corona wire, maybe I can
> have a refresher on the corona wire."* — Chief Architect, 2026-08-19

**Two distinct roles, and a card may hold both:**

| Role | Answers | Added by |
|---|---|---|
| **answer short** | the mechanism this card is *about* | §3 trigger one |
| **refresher short** | a prerequisite concept the card *presupposes* | §3 trigger two |

**Order: answer short first, refresher second**, so the card's own mechanism is the
first thing reachable. Two 📽️ side by side is the intended appearance.

⚠️ **Cap it at two.** A card needing three prerequisites explained is not a linking
problem — it is a badly scoped card, and it belongs to `/medic`. Report it, do not
paper over it with a row of links.

**Gates before every write — all must pass or abort (§1d):**

- **this artifact id is not already in the note** (prevents a duplicate link; replaces
  the old "note does not already contain the film emoji", which forbade the second
  video outright and would have blocked the refresher role above)
- **film-emoji count after == count before + 1** — exactly one added, none destroyed
- **fewer than two 📽️ present before the write**
- result starts with `<a href='`
- previous `Extra` still present in full
- no `</` followed by a non-letter

**Write the previous `Extra` to `VIDEO_ROLLBACK.md` BEFORE the write.** There is no
undo through AnkiConnect.

**Then `{"action":"sync"}`** — reviews happen on AnkiWeb, so an unsynced link does not
exist.

**One short serving several cards → the same link in each.** 🚫 **No tags.** The link
*is* the index: find every card using a short by searching `Extra:*<artifact-id>*`.

---

## §9. ACCOUNTS AND NOTEBOOKS

**`NOTEBOOK_REGISTRY.md` in the project root maps topic → account → notebook. Keyed on
EMAIL, never on `authuser` index** (§1a).

The `authuser` index is still how you *navigate* — append `?authuser=N` to the URL, no
clicking, no credentials — but you must **verify the email once you land.**

### 🚩 9-00. LOOK FOR AN EXISTING NOTEBOOK BEFORE BUILDING ONE. THERE ARE 99.

**Measured 2026-08-19, and it invalidated a whole plan.** `account1@example.com` —
the Chief Architect's main account — holds **99 topic-specific NotebookLM notebooks**,
one per lecture, built over months: *"Instructor: Guide to Email Protocols"*, *"DNS
Architecture and Email Security"*, *"Networking Fundamentals: Proxy Servers and Load
Balancers"*, *"Virtualization Fundamentals: VMs, Hypervisors and Storage"*, *"FTP Active
Mode and Port Triggering Dynamics"*, *"Remote Access Fundamentals: Telnet, SSH and
PuTTY"*, *"the instructor on VLANs, Managed Switches and SDN"*.

🚫 **A run had already created a notebook from an archived transcript and pasted 30 KB
of source into it before this was checked.** That is `CLAUDE.md` §II Reinvention Bias in
its purest form: the proven artifact existed and was never looked for.

**ALWAYS, before §9a:** open `https://notebook.google.com/?authuser=0`, enumerate, and
match by title.

```js
[...document.querySelectorAll('project-button,[class*="notebook-card"]')].map(e => ({
  t: (e.innerText||'').replace(/\s+/g,' ').replace(/more_vert/g,'').trim(),
  id: ((e.querySelector('a[href*="/notebook/"]')||{getAttribute:()=>''})
        .getAttribute('href')||'').match(/notebook\/([0-9a-f-]{36})/)?.[1]
}));
```

⚠️ **Grab the FULL 36-character UUID.** An 8-character prefix is not a notebook id and
navigating to a padded one silently loads nothing.

⚠️ **These notebooks are `Restricted` by default** — only one of the 99 was public. An
existing notebook still needs §9a step 6 before any link from it works for other people.

**Archive transcripts remain the fallback**, for a topic no notebook covers.

### 🚩 9-01. CHECK THE ACCOUNT'S QUOTA BEFORE BUILDING ANYTHING ON IT

**The daily-limit banner renders in the Studio panel on page load — you do NOT have to
attempt a generation to read it.**

```js
/daily Video Overview limit/i.test(document.body.innerText)   // true = spent
```

🚫 **Building a notebook on a spent account wastes the most expensive step in the
workflow.** Measured 2026-08-19: a notebook was created, two 30 KB sources pasted, and
sharing configured on `account2` — and only then did `Generate` reveal the account had
no quota left. **Check every candidate account first, then decide where to build.**

⚠️ **A cap does not reset on your calendar day.** `account3` was spent on 08-18 and
had reset by 08-19; `account2` generated 3 shorts late on 08-18 and was still refusing
the next afternoon. **Read the banner; never infer remaining quota from a count you
kept yourself.**

### 🚩 9-0. SOURCE MATERIAL IS THE REAL CEILING, NOT THE DAILY CAP

**NotebookLM generates from its sources.** A notebook holding the laser-printer lecture
cannot make a video about RAID parity — it will produce something confidently wrong, or
nothing. **Before planning any batch, check that a transcript covering that topic
exists.** The daily cap is the constraint people expect; source coverage is the one that
actually stops a run.

✅ **`Archive/<N>/NOTEBOOK_PRODUCER_BRIEF.txt` is a 29-transcript LIBRARY, not just a
per-run backup.** Every pipeline run froze its lecture there. Grep it to find the source
for a topic before concluding the topic is unbuildable:

```bash
grep -ril "hypervisor" Archive/*/NOTEBOOK_PRODUCER_BRIEF.txt
```

**Coverage measured 2026-08-19** (>=5 mentions): VM/hypervisor → runs 116-119 · ports
and NAT → 110, 116, 118 · wireless/SSID → 126, 129, 1242 · proxy → 112 · email and MIME
→ 111, 134 · printers → 139.

🚫 **No transcript found = §11, hand back.** Do not improvise a source, do not let
NotebookLM answer from general knowledge, and do not quietly drop the card from the
report. **Name the topic and say a lecture is missing** — that is actionable, and
"skipped" is not. Confirmed gaps that day: **RAID parity** (which holds the two most
fragile mechanism cards in the whole collection), RFID, fiber/ONT, and certificates.

### 9a. Creating a notebook when an account has none for the topic

Proven 2026-08-18. Steps:

1. `https://notebook.google.com/?authuser=N` → **Create new notebook**. Created
   immediately with a UUID.
2. **Add sources → "Copied text"**. 🚫 **Not "Upload file"** — that opens a native OS
   dialog browser automation cannot reliably drive.
3. Load the source into the clipboard **with correct encoding** (§1e) from
   `NOTEBOOK_PRODUCER_BRIEF.txt`, focus the `Paste text here` box, press `ctrl+v`.

   ⚠️ **`NOTEBOOK_PRODUCER_BRIEF.txt` is deliberately NOT tracked in git — do not
   "fix" this.** It is the current topic's transcript and is replaced wholesale each
   topic; every run freezes a copy into `Archive/<N>/NOTEBOOK_PRODUCER_BRIEF.txt`, so
   the history already exists there (verified 2026-08-18, `Archive/139/`). Chief
   Architect's ruling, same date. Tracking it would add a 50 KB churning blob to the
   repo for a file that is already archived per run.
4. **Verify before inserting:** emoji intact, em-dashes intact, no `≡ƒ` or `ΓÇ`.
5. Click **Insert**. The notebook auto-titles itself from the content.
6. 🚩 **Share → Notebook Access → "Anyone with a link" → Save.** A new notebook
   defaults to **Restricted**, and **every video link in it is dead for other people
   until this is changed.** There is also a "Public" option — do not use it; "Anyone
   with a link" is what is proven and is less exposed.
7. Record the new notebook in `NOTEBOOK_REGISTRY.md` against the account's email.

⚠️ **Artifact sharing inherits from the notebook.** The share dialog states it:
*"Only those who can view the notebook can view the shared Video Overview."* Sharing
is set **once per notebook**, not once per video.

---

## §10. REPORTING

**Report per short, plainly:** which cards it covers, what it explains, where it
landed. No narration of process, no script output.

**Always state the denominator:** *"20 candidates, 9 eligible, 5 shorts covering 8
cards."* A batch without its denominator hides the selection.

**Say why you skipped** — one clause each. A silent skip is indistinguishable from an
arbitrary one.

---

## §11. NOT BUILT — hand back, do not improvise

- **Replacing a short that turned out bad.** It means editing the `Extra` of every card
  linking to it. Report it; do not guess.
- **Any topic with no `NOTEBOOK_PRODUCER_BRIEF.txt`.** The brief is the source; without
  it there is nothing to build a notebook from.
- **Anything requiring a password.** Never. Hand back.
