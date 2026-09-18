import config
import os
import re
import sys

from tts_reader import speaker, build_speech_p5, clean_text


def _extract_card_rows(start_video, boundary_video):
    """Walk Archive/{N}/ANKI_IMPORT_READY.txt for N in [start, boundary].
    Skip header lines (blank, starts with '#'). Warn on rows with <8 cols.
    Returns a list of (one_based_card_number, front, back, tags) tuples."""
    rows = []
    counter = 0
    project_root = os.path.dirname(os.path.abspath(__file__))
    for n in range(start_video, boundary_video + 1):
        path = os.path.join(project_root, "Archive", str(n), "ANKI_IMPORT_READY.txt")
        if not os.path.exists(path):
            print(f" [~] PHASE 6: Archive/{n}/ANKI_IMPORT_READY.txt missing — skipped.")
            continue
        with open(path, "r", encoding="utf-8") as f:
            for raw in f.readlines():
                line = raw.rstrip("\r\n")
                if not line.strip():
                    continue
                if line.startswith("#"):
                    continue
                parts = line.split("|")
                if len(parts) < 8:
                    print(f" [!] PHASE 6: video {n}: row with only {len(parts)} columns — skipped: {line[:60]}...")
                    continue
                counter += 1
                front = parts[2].strip()
                back = parts[3].strip()
                tags = parts[7].strip()
                rows.append((counter, front, back, tags))
    return rows


def _build_inventory_block(rows):
    """Format extracted rows as the body that lands inside <unit_card_inventory>."""
    lines = []
    for n, front, back, tags in rows:
        lines.append(f"[{n}] | {front} | {back} | {tags}")
    return "\n".join(lines)


def _extract_final_inventory(raw_response):
    """Pull <final_inventory>...</final_inventory> from the LLM response.
    Falls back to the whole response if the tag is missing (caller will
    decide whether to abort)."""
    m = re.search(r"<final_inventory>.*?</final_inventory>", raw_response, re.DOTALL)
    if m:
        return m.group(0).strip()
    return raw_response.strip()


def print_centered_vertical(front_text, back_text=None, progress_str=""):
    """Centers text vertically/horizontally in the terminal, pushing the prompt to the bottom.
    Copied from run_phase5.py so the Veto-6 study UX is identical to the P1/P5 veto gates."""
    try:
        terminal_lines = os.get_terminal_size().lines
    except Exception:
        terminal_lines = 24
    lines_list = []
    if progress_str:
        lines_list.append(progress_str.center(60))
        lines_list.append("")
    lines_list.extend([line.center(60) for line in front_text.split("\n")])
    if back_text:
        lines_list.append("")
        lines_list.extend([line.center(60) for line in back_text.split("\n")])
    content_height = len(lines_list)
    top_padding = max(0, (terminal_lines - content_height - 2) // 2)
    bottom_padding = max(0, terminal_lines - content_height - top_padding - 2)
    print("\n" * top_padding, end="")
    for line in lines_list:
        print(line)
    print("\n" * bottom_padding, end="")


def veto_gate_6(final_inventory_xml):
    """VETO-6: interactive cull before the P2 baton, using the SAME Anki-style reveal + TTS
    flow proven in run_phase1/run_phase5 - the question is shown AND spoken, ENTER reveals the
    answer (also spoken), then Keep/Reject. HIGH-certainty entries are reviewed one at a time;
    LOW-certainty entries are bulk-handled (reject-all default). Returns <final_inventory> with
    only approved entries. Runs on whatever raw_response call_llm returned - run_master phase
    selection and config.call_llm are untouched."""
    ctx_m = re.search(r"<context>.*?</context>", final_inventory_xml, re.DOTALL)
    context_xml = ctx_m.group(0) if ctx_m else ""
    entries = re.findall(r"<entry\b.*?</entry>", final_inventory_xml, re.DOTALL)
    if not entries:
        print(" [~] VETO-6: no <entry> blocks found - passing through unchanged.")
        return final_inventory_xml

    def _tag(e, tag, default=""):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", e, re.DOTALL)
        return m.group(1).strip() if m else default

    def _cert(e):
        m = re.search(r'certainty="([^"]*)"', e)
        return m.group(1).upper() if m else "HIGH"

    high = [e for e in entries if _cert(e) != "LOW"]
    low = [e for e in entries if _cert(e) == "LOW"]
    approved = []

    # ---- HIGH: one at a time, Anki reveal + TTS (mirrors run_phase5 State 1 -> State 2) ----
    accept_all = False
    for idx, e in enumerate(high):
        if accept_all:
            approved.append(e)
            continue
        front_text = _tag(e, "provisional_front", "(no front)")
        back_text = _tag(e, "provisional_back", "(no back)")
        progress_str = f"[HIGH {idx + 1}/{len(high)}] {_tag(e, 'concept')}"
        speech_str_s1 = build_speech_p5(front_text)
        speaker.play(speech_str_s1)
        speaker.prefetch(clean_text(back_text))
        for _d in range(1, 4):
            if idx + _d < len(high):
                _nf = _tag(high[idx + _d], "provisional_front")
                _nb = _tag(high[idx + _d], "provisional_back")
                speaker.prefetch(build_speech_p5(_nf))
                if _nb:
                    speaker.prefetch(clean_text(_nb))
        config.clear_screen()
        print_centered_vertical(front_text, progress_str=progress_str)
        while True:
            choice = input(" [?] (ENTER: Reveal | R: Reject | A: Accept All | P: Replay | B: Keep-rest) >> ").strip().lower()
            if choice == "p":
                speaker.stop(); speaker.play(speech_str_s1); continue
            speaker.stop(); break
        if choice == "r":
            continue
        elif choice == "a":
            approved.append(e); accept_all = True; continue
        elif choice == "b":
            approved.extend(high[idx:]); break
        # State 2: reveal + speak the answer
        speech_str_s2 = clean_text(back_text)
        speaker.play(speech_str_s2)
        config.clear_screen()
        print_centered_vertical(front_text, back_text=back_text, progress_str=progress_str)
        while True:
            choice2 = input(" [?] (ENTER: Keep | R: Reject | A: Accept All | P: Replay) >> ").strip().lower()
            if choice2 == "p":
                speaker.stop(); speaker.play(speech_str_s2); continue
            speaker.stop(); break
        if choice2 == "r":
            continue
        elif choice2 == "a":
            approved.append(e); accept_all = True
        else:
            approved.append(e)

    # ---- LOW: bulk list, reject-all by default ----
    if low:
        config.clear_screen()
        print("=" * 60)
        print(f" VETO-6  |  LOW-certainty bulk ({len(low)})".center(60))
        print("=" * 60)
        for j, e in enumerate(low, 1):
            print(f"  [{j:2d}] {_tag(e, 'concept')}")
            print(f"       Q: {_tag(e, 'provisional_front')}")
            print(f"       A: {_tag(e, 'provisional_back', '(no back)')}")
        print("=" * 60)
        raw = input("\n [?] ENTER = reject ALL | K = keep all | keep #s (e.g. 3,7) | I = review individually >> ").strip()
        rl = raw.lower()
        if rl == "k":
            approved.extend(low)
        elif rl == "i":
            for j, e in enumerate(low):
                front_text = _tag(e, "provisional_front", "(no front)")
                back_text = _tag(e, "provisional_back", "(no back)")
                progress_str = f"[LOW {j + 1}/{len(low)}] {_tag(e, 'concept')}"
                speech_str_s1 = build_speech_p5(front_text)
                speaker.play(speech_str_s1)
                speaker.prefetch(clean_text(back_text))
                config.clear_screen()
                print_centered_vertical(front_text, progress_str=progress_str)
                while True:
                    c = input(" [?] (ENTER: Reveal | R: Reject | P: Replay) >> ").strip().lower()
                    if c == "p":
                        speaker.stop(); speaker.play(speech_str_s1); continue
                    speaker.stop(); break
                if c == "r":
                    continue
                speech_str_s2 = clean_text(back_text)
                speaker.play(speech_str_s2)
                config.clear_screen()
                print_centered_vertical(front_text, back_text=back_text, progress_str=progress_str)
                while True:
                    c2 = input(" [?] (ENTER: Keep | R: Reject | P: Replay) >> ").strip().lower()
                    if c2 == "p":
                        speaker.stop(); speaker.play(speech_str_s2); continue
                    speaker.stop(); break
                if c2 != "r":
                    approved.append(e)
        else:
            keep_nums = set(int(x.strip()) for x in raw.split(",") if x.strip().isdigit())
            for j, e in enumerate(low, 1):
                if j in keep_nums:
                    approved.append(e)

    config.clear_screen()
    print("=" * 60)
    print(f" [+] VETO-6 complete: {len(approved)} of {len(entries)} kept for the P2 baton.")
    print("=" * 60)
    body = "\n\n".join(approved)
    return f"<final_inventory>\n{context_xml}\n\n{body}\n</final_inventory>"


def run_phase6():
    print(" [!] PHASE 6 SPECIALIST: THE UNIT AUDITOR")
    print("-" * 50)

    # 1. READ ENV VARS
    start_env = os.environ.get("PIPELINE_UNIT_START_VIDEO")
    bnd_env = os.environ.get("PIPELINE_UNIT_BOUNDARY_VIDEO")
    if not start_env or not bnd_env:
        print(" [X] PHASE 6: PIPELINE_UNIT_START_VIDEO / PIPELINE_UNIT_BOUNDARY_VIDEO not set.")
        print(" [X] run_phase6.py expects to be launched from run_master.py's unit sweep hook.")
        sys.exit(1)
    try:
        unit_start_video = int(start_env)
        boundary_video = int(bnd_env)
    except ValueError:
        print(f" [X] PHASE 6: env vars are not integers (start={start_env!r}, boundary={bnd_env!r}).")
        sys.exit(1)

    print(f" [+] Unit window: videos {unit_start_video} through {boundary_video}")

    # 2. PROMPT
    prompt_path = os.path.join("Prompts", "prompt6_unit_auditor.txt")
    if not os.path.exists(prompt_path):
        print(f" [X] PHASE 6: {prompt_path} missing.")
        sys.exit(1)
    with open(prompt_path, "r", encoding="utf-8") as f:
        p6_text = f.read()

    # 3. CARD INVENTORY
    rows = _extract_card_rows(unit_start_video, boundary_video)
    if not rows:
        print(f" [X] PHASE 6: No card rows extracted for videos {unit_start_video}–{boundary_video}.")
        print(" [X] Verify Archive/{N}/ANKI_IMPORT_READY.txt files exist and contain card data.")
        sys.exit(1)
    print(f" [+] Card inventory: {len(rows)} cards across the unit.")
    inventory_block = _build_inventory_block(rows)

    # 4. REFERENCE LIBRARY (Ref A + Ref B, full file)
    ref_path = os.path.join("Prompts", "reference_library_p1.xml")
    if not os.path.exists(ref_path):
        print(f" [X] PHASE 6: {ref_path} missing.")
        sys.exit(1)
    with open(ref_path, "r", encoding="utf-8") as f:
        ref_full = f.read()
    if "**[REF A:" not in ref_full:
        print(" [X] PHASE 6: Ref A section not found in reference_library_p1.xml (expected '**[REF A:' marker).")
        sys.exit(1)
    if "**[REF B:" not in ref_full:
        print(" [X] PHASE 6: Ref B section not found in reference_library_p1.xml (expected '**[REF B:' marker).")
        sys.exit(1)
    reference_library = ref_full

    # 5. ASSEMBLE PROMPT
    prompt = (p6_text
              .replace("[👉PASTE UNIT CARD INVENTORY HERE👈]", inventory_block)
              .replace("{{REFERENCE_LIBRARY}}", reference_library)
              .replace("[👉BOUNDARY VIDEO👈]", str(boundary_video))
              .replace("[👉START VIDEO👈]", str(unit_start_video)))

    # 6. SINGLE LLM CALL
    print(" [>] Calling Unit Auditor LLM (single pass, no chunking)...")
    raw_response = config.call_llm(
        prompt,
        context_header="PHASE 6 | PASS 1",
        phase="P6",
        pass_num=1,
    )
    if not raw_response:
        print(" [X] PHASE 6: Unit Auditor returned empty response. Aborting.")
        sys.exit(1)

    # 7. WRITE FORENSIC LOG + BATON
    with open("unit_sweep_forensic_raw_p6_pass1.txt", "w", encoding="utf-8") as f:
        f.write(f"### FORENSIC LOG: P6 PASS 1 | MODEL: {config.LAST_ACTIVE_MODEL}\n"
                + "=" * 60 + "\n" + raw_response)

    final_inventory = _extract_final_inventory(raw_response)

    # VETO-6: interactive cull before the baton (HIGH one-by-one, LOW bulk).
    final_inventory = veto_gate_6(final_inventory)

    # SANITIZE + BATON STRIP (match run_phase1's baton): purge EOF/backticks and
    # strip provisional tags - P6 entries are all BLUE/DEBT, so provisionals are
    # veto-display scaffolding only and are not carried through to P2.
    final_inventory = re.sub(r"\[EOF.*?\]", "", final_inventory, flags=re.IGNORECASE)
    final_inventory = final_inventory.replace("```", "").replace("`", "").strip()
    final_inventory = re.sub(r"<provisional_front>.*?</provisional_front>", "", final_inventory, flags=re.DOTALL)
    final_inventory = re.sub(r"<provisional_back>.*?</provisional_back>", "", final_inventory, flags=re.DOTALL)

    with open("unit_sweep_baton_p1_to_p2.xml", "w", encoding="utf-8") as f:
        f.write(final_inventory)

    # 8. SUMMARY
    entry_count = len(re.findall(r"<entry\b", final_inventory))
    config.clear_screen()
    print("=" * 60)
    print(" [!] PHASE 6 COMPLETE: UNIT AUDIT EMITTED ".center(60, "#"))
    print("=" * 60)
    print(f" [+] Unit window         : {unit_start_video}–{boundary_video}")
    print(f" [+] Cards audited        : {len(rows)}")
    print(f" [+] DEBT entries emitted : {entry_count}")
    print(f" [+] Baton                : unit_sweep_baton_p1_to_p2.xml")
    print(f" [+] Forensic log         : unit_sweep_forensic_raw_p6_pass1.txt")
    print("=" * 60)


if __name__ == "__main__":
    run_phase6()
