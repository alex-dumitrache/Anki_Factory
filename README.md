# Anki_Factory

A learning pipeline that turns course lectures into spaced-repetition flashcards, and then learns from the cards I fail.

---

## The story

I started Anki_Factory after realising making my own flashcards was a bottleneck in studying. Shared decks contained cards I already knew and missed my knowledge gaps, so I wanted a system built around what I didn't know.

My first step was simple: I fed an AI chat a lecture transcript and a signal for the knowledge gap I wanted to address, asking it to create flashcards. As the system grew, I found one prompt couldn't reliably handle every stage: models could hallucinate, take the path of least resistance, or satisfy the apparent request without serving the learning objective.

I evolved the prompt into specialised stages, each handling a different job, passing its output to the next stage, with its own checks and constraints.

The design is grounded in Barbara Oakley's Learning How to Learn and Piotr Woźniak's 20 rules of formulating knowledge. Cards are built to force recall rather than recognition, reverse cards are used only where knowledge works both ways, and different knowledge gets different templates. Words, pictures and sound reinforce each other, while Anki uses spaced repetition to schedule every card.

I initially ran the prompts by hand, then eventually designed the chain to run itself. That became the Python pipeline.

Later, I noticed that when I failed a card, I was learning something about the card itself. I realised my failures can be data, so I built /medic to read review history and failure notes, diagnose why cards failed, and choose how to repair them. A bad question might need rewriting, a missing distinction might need a comparison, and a weak cue might need strengthening. Numbers can use Major System hooks, while other concepts can use mnemonic, acronym or explainer techniques. The pipeline also generates NotebookLM video explainers and lecture-length audio deep dives.

The project grew from the original prompt into a pipeline with 76 commits, and I still run and develop it as my learning tool for whatever I take on next.

---

## What this repository is, and what it is not

This is the **public snapshot** of a private working repository. The private one carries 76 commits since March 2026 along with my own study material; this one carries the engine and its documentation, and nothing personal.

**What is here:** the six stage prompts, the Python that runs them, the nine workflow commands, the full dated `CHANGELOG.md`, the forensic briefs behind the bigger design decisions, the `/medic` specification and ticket log, and the integrity script.

**What is deliberately not here:**

| Left out | Why |
|---|---|
| My Anki collection, decks, review history and card annotations | personal study data |
| Lecture transcripts and anything generated from them | not mine to publish |
| The two reference libraries the prompts load | one is the course's own syllabus map, the other is the certification objectives restructured into a knowledge graph. Both are third-party material, so the placeholders stay empty here |
| API keys and my notification topic | read from the environment. `api_keys.py` has never been committed |

---

## How it works

A lecture transcript goes in, with the requests I speak while watching. Six stages, each one a prompt plus a Python orchestrator:

| Stage | What it does |
|---|---|
| **1. Harvester** (`run_phase1.py`) | separates my dictated requests from the lecturer's words, audits the lecture against the course map and the exam objectives, and presents everything at a review gate before anything is built |
| **2. Draftsman** (`run_phase2.py`) | turns approved entries into logic blocks: what each card will teach, and which concepts belong together |
| **3. Formulator** (`run_phase3.py`) | writes the cards, choosing a template by the kind of knowledge, then attacks its own output |
| **4. Reverse Engineer** (`run_phase4.py`) | decides which knowledge is safely reversible, and deletes a reverse card rather than rewrite one that cannot be answered honestly |
| **5. Sentinel / Exporter** (`run_phase5.py`) | final audit, acronym glosses, spoken audio, images, and a checksummed import file |
| **6. Unit Auditor** (`run_phase6.py`) | at the end of a course unit, checks the finished cards against the exam objectives for anything no single lecture covered |

`run_master.py` runs the chain: start, resume or re-run any stage, validate each stage's input, back up every run, and detect unit boundaries. Every hand-off between stages is a file on disk, so any stage can be replayed or audited. `config.py` routes each pass to a model suited to its job, with fallbacks and timeouts.

### The workflow commands

| Command | Role |
|---|---|
| `/scout` | evidence and root cause only; forbidden from proposing fixes |
| `/design` | the fix in plain English, no code |
| `/redteam` | adversarial review, with a go or no-go verdict |
| `/surgeon` | executes exactly the approved change, then verifies it |
| `/commit` | shift handover: what went wrong, and which rule would have prevented it |
| `/compass` | re-reads the project's rules mid-session to catch drift |
| `/telemetry` | triages the problems the prompts report about their own instructions |
| `/medic` | reads my review history and the notes I leave on failed cards, works out why a card failed, and proposes one repair |
| `/shorts` | turns a card that resists text into a one-minute explainer video |

---

## The design

### Learning science

Built on Barbara Oakley's *Learning How to Learn* and Piotr Woźniak's 20 rules of formulating knowledge. The prompts carry a "flashcard canon" that names the rules they enforce, including the minimum information principle and the rules against sets, enumerations and interference. In practice: cards force recall rather than recognition, a reverse card is made only where the knowledge runs both ways, each kind of knowledge gets its own template, and a hard card can be encoded as a memory hook, a mnemonic image or a short video.

### Working with the limits of language models

Every defence here exists because something went wrong first:

- a model reports "nothing found" when it did not look, so the prompts must show their counts even at zero
- long audits get cut off, so they evaluate everything and write down only what is wrong
- a worked example beats the rule written beside it, so the examples are fixed, not the prose
- naming a forbidden thing attracts it, so rules state the positive goal
- a model's report about its own work is not evidence: check the output

---

## How changes are made

Evidence first, then a design, then adversarial review, then exactly the approved edit, then a log entry with a way back. `CHANGELOG.md` records the intent of every change and its rollback path; `check.sh` is the integrity pass that runs at the start of a session.

---

## Authorship

I designed this system, directed every change, and tested and debugged it throughout. **The Python was written by AI coding assistants working to my design.**

---

## Status

Started in August 2025 as a single prompt, and still running and still developing. It was built for CompTIA A+, and it is designed around learning science rather than around one exam.

---

## What it needs

### The four things you must supply

**Everything else in the pipeline is generated.** This list is not from memory — it is every file the code opens for reading and never writes:

| You supply | Placeholder here | If it is missing |
|---|---|---|
| `raw_chat.txt` — the lecture, captured | `raw_chat.example.txt` | stage 1 stops: *"'raw_chat.txt' missing from folder!"* |
| `Prompts/reference_library_p1.xml` — course map + exam objectives | `Prompts/reference_library_p1.example.xml` | stage 1 and the stage 6 auditor stop |
| `Prompts/reference_library_p2.xml` | `Prompts/reference_library_p2.example.xml` | stage 2 stops |
| `api_keys.py` — your Gemini and Claude keys | `api_keys.example.py` | import fails |

The reference libraries are mine and are not published: one is the course's own syllabus map, the other the certification objectives restructured as a knowledge graph — both third-party material. **The placeholders show the exact structure the prompts expect.**

Every other file the stages read — the six prompts, `NotebookLM_Prompt_BETA.txt`, `pairings.py` — **is in this repository.** The batons between stages (`baton_p1_to_p2.xml`, `final_anki_cards.txt`, `ANKI_IMPORT_READY.txt`, the forensic logs, `Archive/`) are all created as the pipeline runs; you never make them yourself.

### Environment

| | |
|---|---|
| **Python packages** | `anthropic`, `google-genai`, `requests`, `numpy`, `Pillow`, `pyautogui`, `pyperclip`, `sounddevice`, `lameenc`, `kokoro-onnx`, `phonemizer` — see `requirements.txt` |
| **System** | Windows: the code uses `winsound` and `msvcrt`. `espeak-ng` for phonemisation |
| **Anki** | running, with the AnkiConnect add-on listening on `127.0.0.1:8765`. Stage 5 writes cards and images straight into the collection |
| **Model files** | the Kokoro TTS model and its voice pack, fetched on first use |

### The input format, and the workflow it was built around

I record the lecture through Whisper inside a ChatGPT session running in transcription-only mode, speaking my own flashcard requests into the same stream while I watch. `raw_chat.txt` is that conversation, pasted whole. **The parser was built around that habit, and it shows.**

Stage 1 expects:

- an opening setup block, beginning `You are operating in transcription-only mode` and ending `… continue responding with "Received."` — this whole block is deleted
- `You said:` / `ChatGPT said:` turn markers and standalone `Received.` lines — stripped
- my spoken requests inline, as lines beginning **`create a flashcard …`** or **`create flashcards …`** — these are lifted out as the card triggers, and everything else is treated as the lecturer's words

**`raw_chat.example.txt` is a complete worked example** — invented content, real format.

**If you capture lectures any other way, this is the part to rewrite.** It is a handful of regexes at the top of `run_phase1.py`; everything downstream only ever sees the cleaned transcript and the extracted triggers.

## What this is not

**This is a record of a working system, not a packaged install.** It grew on one machine over six months, and much of what it leans on I added as I needed it rather than as a documented list — editor extensions, audio tooling, Anki add-ons. The table above is what the code itself proves it needs; it is not a promise that a clean machine will run it.

**Do not expect to clone this and have it run.** It is published so the design, the prompts and the change history can be read.

## Running it, if you want to try

1. `pip install -r requirements.txt`, then install `espeak-ng`, and Anki with the AnkiConnect add-on.
2. Copy `api_keys.example.py` to `api_keys.py` and fill it in. `api_keys.py` is ignored by git and must never be committed.
3. Optional: set a `NTFY_TOPIC` environment variable for phone notifications when a stage needs you.
4. Copy the two `reference_library_p*.example.xml` files to `reference_library_p1.xml` and `reference_library_p2.xml`, and fill them in — stages 1 and 2 exit without them.
5. Copy `raw_chat.example.txt` to `raw_chat.txt` and replace it with a real transcript.
6. Start Anki, then `python run_master.py`.
