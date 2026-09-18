import config
import time
import os
import re
import sys
from tts_reader import speaker, build_speech_p2, clean_text

UNIT_SWEEP_MODE = os.environ.get("PIPELINE_UNIT_SWEEP", "").upper() == "TRUE"
_P = "unit_sweep_" if UNIT_SWEEP_MODE else ""

def normalize(text):
    """Fuzzy Logic: Strips extra words, parens, and spaces for matching."""
    # Removes anything inside parentheses and condenses the string
    text = re.sub(r'\(.*?\)', '', text) 
    return "".join(text.split()).lower().strip()

def print_centered_vertical(front_text, back_text=None, progress_str=""):
    """Centers text vertically and horizontally in the terminal, pushing prompt to the bottom."""
    try:
        terminal_lines = os.get_terminal_size().lines
    except Exception:
        terminal_lines = 24
    
    lines_list = []
    if progress_str:
        lines_list.append(progress_str.center(60))
        lines_list.append("")
        
    lines_list.extend([line.center(60) for line in front_text.split('\n')])
    
    if back_text:
        lines_list.append("")
        lines_list.extend([line.center(60) for line in back_text.split('\n')])
        
    content_height = len(lines_list)
    
    # Calculate padding to center content vertically while leaving 2 lines for input at the bottom
    top_padding = max(0, (terminal_lines - content_height - 2) // 2)
    bottom_padding = max(0, terminal_lines - content_height - top_padding - 2)
    
    # Print with exact padding
    print("\n" * top_padding, end="")
    for line in lines_list:
        print(line)
    print("\n" * bottom_padding, end="")

def normalize_concept(s):
    s = re.sub(r'\*+', '', s)
    s = ' '.join(s.split())
    s = s.lower()
    s = s.strip()
    return s

def merge_surgical_patch(base_payload, raw_llm_output):
    """Merges a surgical patch (Pass 2+ output) into the siphoned Pass 1 logic payload."""
    # Step 1 — Extract patch content
    fi_m = re.search(r'<final_logic_package>(.*?)</final_logic_package>', raw_llm_output, re.DOTALL)
    if fi_m:
        patch_text = fi_m.group(1).strip().replace("### 📦 ENRICHED LOGIC PAYLOAD", "").strip()
    else:
        patch_text = raw_llm_output

    # Step 2 — Empty patch guard
    if '[[LOGIC_BLOCK]]' not in patch_text and '<topology_override>' not in patch_text:
        print(' [P2 MERGE: ZERO PATCHES — BASE RETURNED UNCHANGED]')
        return base_payload

    # Step 3 — Parse base_payload into ordered dict
    base_parts = re.split(r'(?m)^\[\[LOGIC_BLOCK\]\]\s*$', base_payload)
    header = base_parts[0].strip() if base_parts[0].strip() else ""
    base_dict = {}
    for segment in base_parts[1:]:
        if not segment.strip():
            continue
        concept_m = re.search(r'(?m)^\*{0,2}Target_Concept:\*{0,2}\s+(.*?)\r?\n', segment)
        if not concept_m:
            continue
        key = normalize_concept(concept_m.group(1).strip())
        _base_key = key
        _key_ctr = 2
        while key in base_dict:
            key = f"{_base_key}__{_key_ctr}"
            _key_ctr += 1
        base_dict[key] = segment

    # Step 4 — Apply patch entries
    patch_parts = re.split(r'(?m)^\[\[LOGIC_BLOCK\]\]\s*$', patch_text)
    modified = 0
    injected = 0
    for segment in patch_parts:
        if not segment.strip():
            continue
        concept_m = re.search(r'(?m)^\*{0,2}Target_Concept:\*{0,2}\s+(.*?)\r?\n', segment)
        if not concept_m:
            continue
        key = normalize_concept(concept_m.group(1).strip())
        if key in base_dict:
            base_dict[key] = segment
            print(f' [P2 MODIFY] {key}')
            modified += 1
        else:
            base_dict[key] = segment
            print(f' [P2 INJECT] {key}')
            injected += 1

    # Step 5 — Apply topology override (if present)
    topo_m = re.search(r'<topology_override>(.*?)</topology_override>', raw_llm_output, re.DOTALL)
    if topo_m:
        topo_keys = [normalize_concept(line.strip()) for line in topo_m.group(1).splitlines() if line.strip()]
        if all(k in base_dict for k in topo_keys):
            ordered_items = [(k, base_dict[k]) for k in topo_keys]
            remaining = [(k, v) for k, v in base_dict.items() if k not in topo_keys]
            base_dict = dict(ordered_items + remaining)
        else:
            for k in topo_keys:
                if k not in base_dict:
                    print(f' [P2 TOPOLOGY WARNING: {k} not found — reorder aborted]')
                    break

    # Step 6 — Reconstruct payload
    blocks_content = "\n[[LOGIC_BLOCK]]\n".join(base_dict.values())
    if header:
        result = header + "\n[[LOGIC_BLOCK]]\n" + blocks_content
    else:
        result = "[[LOGIC_BLOCK]]\n" + blocks_content

    # Step 7 — Log summary
    print(f' [P2 MERGE COMPLETE] [{modified}] modified, [{injected}] injected. Final block count: [{len(base_dict)}]')

    return result

def run_phase2():
    print(" [!] PHASE 2 SPECIALIST: RECURSIVE BULLDOZER (v8.0 - VETO STATION)")
    print("-" * 50)

    # 1. READ INPUTS
    if not os.path.exists(_P + "baton_p1_to_p2.xml"):
        print(f" [X] Error: '{_P}baton_p1_to_p2.xml' missing! Run upstream phase first.")
        sys.exit(1)

    with open(_P + "baton_p1_to_p2.xml", "r", encoding="utf-8") as f:
        baton_xml = f.read()

    if not os.path.exists("Prompts/prompt2_draftsman.txt"):
        print(" [X] Error: 'Prompts/prompt2_draftsman.txt' missing from folder!")
        sys.exit(1)

    with open("Prompts/prompt2_draftsman.txt", "r", encoding="utf-8") as f:
        p2_text = f.read()

    # Inject reference library (decoupled to save Claude Code session tokens)
    _ref_lib_path = "Prompts/reference_library_p2.xml"
    if not os.path.exists(_ref_lib_path):
        print(f" [X] Error: '{_ref_lib_path}' missing -- cannot inject reference library.")
        sys.exit(1)
    with open(_ref_lib_path, "r", encoding="utf-8") as f:
        _reference_library = f.read()
    p2_text = p2_text.replace("{{REFERENCE_LIBRARY}}", _reference_library)

    # Define the exact placeholder from Prompt 2
    target_placeholder = "[👉PASTE FULL DATA PACKAGE FROM PROMPT 1 HERE👈]"

    # 2. EXTRACT "SAFE LIST" FROM P1 XML (XML SOVEREIGNTY)
    safe_concepts = set()
    matches = re.findall(r"<concept>(.*?)</concept>", baton_xml, re.DOTALL)
    for m in matches:
        safe_concepts.add(normalize(m))

    # Extract GREEN concepts for zone-aware summary reporting
    green_concepts = set()
    green_entry_matches = re.findall(
        r'<entry\s+zone=["\']GREEN["\'][^>]*>.*?<concept>(.*?)</concept>',
        baton_xml, re.DOTALL
    )
    for m in green_entry_matches:
        green_concepts.add(normalize(m))

    # ==========================================
    # 3. ITERATIVE REFINEMENT LOOP (2 PASSES)
    # ==========================================
    current_payload = ""
    base_payload = ""
    total_passes = 2
    audit_placeholder = "[👉LEAVE EMPTY FOR MODE1. PASTE FAILED XML OUTPUT HERE FOR MODE2👈]"

    for pass_num in range(1, total_passes + 1):
        if pass_num == 1:
            print(f" [>] PASS 1: Generating Initial Logic Blocks (Mode 1)...")
            prompt = p2_text.replace(target_placeholder, baton_xml).replace(audit_placeholder, "")
        else:
            print(f" [>] PASS {pass_num}: Cognitive Interrogation (Mode 2 - Pass {pass_num-1})...")
            # Ingest static Baton for truth, cycle previous payload to Audit Target
            prompt = p2_text.replace(target_placeholder, baton_xml).replace(audit_placeholder, current_payload)
            # Ensure Mode 2 Trigger is appended
            prompt += "\n\n(DRAFTSMAN)"

        current_payload = config.call_llm(prompt, context_header=f"PHASE 2 | PASS {pass_num}", phase="P2", pass_num=pass_num)

        if not current_payload:
            print(f" [X] Fatal Error in Pass {pass_num}. Aborting.")
            sys.exit(1)

        if pass_num == 1:
            # Forensic Logs
            with open(_P + f"forensic_raw_p2_pass{pass_num}.txt", "w", encoding="utf-8") as f:
                f.write(f"### FORENSIC LOG: PASS {pass_num} | MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + current_payload)
            p2_siphon_matches = re.findall(
                r"<final_logic_package>(.*?)</final_logic_package>",
                current_payload, re.DOTALL)
            if p2_siphon_matches:
                base_payload = (
                    "\n".join(p2_siphon_matches)
                    .strip()
                    .replace("### 📦 ENRICHED LOGIC PAYLOAD", "")
                    .strip()
                )
            else:
                base_payload = current_payload
            print(f" [P2 BASE SIPHON: {len(base_payload)} chars extracted]")
        else:
            raw_pass_output = current_payload
            with open(_P + f"forensic_raw_p2_pass{pass_num}.txt", "w", encoding="utf-8") as f:
                f.write(f"### FORENSIC LOG: PASS {pass_num} | MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + raw_pass_output)
            current_payload = merge_surgical_patch(base_payload, raw_pass_output)
            with open(_P + "forensic_merged_p2.txt", "w", encoding="utf-8") as f:
                f.write(f"### MERGED STATE: POST-PASS {pass_num} | MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + current_payload)

    # ==========================================
    # 4. INTERACTIVE VETO STATION
    # ==========================================
    # THE EXPLICIT PACKAGE SIPHON (v7.2 Standard - Armor Plated)
    # Target ALL <final_logic_package> tags to isolate the blocks from the Audit Log
    package_matches = re.findall(r"<final_logic_package>(.*?)</final_logic_package>", current_payload, re.DOTALL)
    
    if package_matches:
        # Join all captured stream zones together into one massive data block
        clean_payload = "\n".join(package_matches).strip()
        # Clean up internal headers if present to isolate raw blocks
        clean_payload = clean_payload.replace("### 📦 ENRICHED LOGIC PAYLOAD", "").strip()
    else:
        print(" [!] WARNING: <final_logic_package> tag not found. Falling back to fuzzy capture.")
        clean_payload = current_payload.replace("### 📦 ENRICHED LOGIC PAYLOAD", "").strip()
        clean_payload = re.sub(r"<red_team_audit>.*?</red_team_audit>", "", clean_payload, flags=re.DOTALL)
        clean_payload = re.sub(r"<drafting_board>.*?</drafting_board>", "", clean_payload, flags=re.DOTALL)

    blocks = clean_payload.split("[[LOGIC_BLOCK]]")

    if not blocks[1:]:
        print(" [X] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print(" [X] FATAL: [[LOGIC_BLOCK]] tag not found in payload.")
        print(" [X] The LLM output did not contain the expected split")
        print(" [X] marker. No blocks were extracted. Pipeline halted.")
        print(" [X] Fallback: check forensic_raw_p2_pass2.txt for raw")
        print(" [X] output and verify [[LOGIC_BLOCK]] is present.")
        print(" [X] !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        sys.exit(1)

    acronym_blocks = []
    injected_blocks = []
    auto_passed_blocks = []
    
    for block_idx, block_content in enumerate(blocks[1:], 1):
        concept_match = re.search(r"\*{0,2}Target[_ ]Concept:\*{0,2}\s+(.*?)\r?\n", block_content)
        goal_match = re.search(r"\*{0,2}Cognitive_Goal:\*{0,2}\s+(.*?)\r?\n", block_content)
        fact_match = re.search(r"\*{0,2}Raw_Fact:\*{0,2}\s+(.*?)\r?\n", block_content)

        if not concept_match:
            print(f" [!] WARNING: Block {block_idx} has no parseable Target_Concept field — skipping. Preview: {block_content[:60]!r}")
            continue
            
        current_concept = concept_match.group(1).strip()
        norm_concept = normalize(current_concept)
        goal = goal_match.group(1).strip() if goal_match else ""
        fact = fact_match.group(1).strip() if fact_match else ""

        if "Acronym" in goal:
            acronym_blocks.append({'concept': current_concept, 'fact': fact, 'content': block_content})
            continue
        
        is_original = False
        for safe in safe_concepts:
            if norm_concept == safe or (len(norm_concept) > 3 and norm_concept in safe) or (len(safe) >= 3 and safe in norm_concept):
                is_original = True
                break
        
        if is_original:
            auto_passed_blocks.append(block_content)
        else:
            injected_blocks.append((current_concept, block_content))

    goal_labels = {
        "PainPoint_Model": "Scaffolding: Pain Point",
        "Foundational_Bridge": "Scaffolding: Bridge",
        "Translation": "Scaffolding: Translator",
        "Rosetta_Identity": "Scaffolding: Rosetta",
    }

    approved_injected = []
    denied_count = 0
    accept_all = False

    if (injected_blocks or acronym_blocks) and config.veto_gate_needs_notification(2):
        config.send_ntfy(
            title="🧱 P2 Veto Gate Ready",
            message=f"{len(injected_blocks)} scaffolding + {len(acronym_blocks)} acronym block(s) awaiting curation. Switch to your terminal.",
        )

    if injected_blocks:
        try:
            config.clear_screen()
        except Exception:
            pass

        _use_anki = False

        print("=" * 60)
        print(f" {len(injected_blocks)} scaffolding block(s) for review.".center(60))
        print("=" * 60)
        print(" 📦 SCAFFOLDING BLOCKS — Type numbers to REJECT".center(60))
        print(" Default: KEEP ALL. ENTER accepts everything.".center(60))
        print("=" * 60)

        for i, (concept, content) in enumerate(injected_blocks, 1):
            goal_match = re.search(
                r"\*{0,2}Cognitive_Goal:\*{0,2}\s+(.*?)\r?\n",
                content)
            goal_txt = (goal_match.group(1).strip()
                        if goal_match else "UNKNOWN")
            goal_label = goal_labels.get(goal_txt, goal_txt)
            # 1. Try Provisional_Front; fallback to Raw_Fact
            preview_match = re.search(
                r"\*{0,2}Provisional_Front:\*{0,2}\s*(.*?)(?:\r?\n|$)",
                content)
            if (preview_match
                    and preview_match.group(1).strip()
                    and preview_match.group(1).strip() != "N/A"):
                preview_txt = "Front: " + preview_match.group(1).strip()
            else:
                fact_match = re.search(
                    r"\*{0,2}Raw_Fact:\*{0,2}\s*(.*?)(?:\r?\n\*{0,2}[A-Z]|$)",
                    content, re.DOTALL)
                fact_txt = fact_match.group(1).strip() if fact_match else ""
                preview_txt = (
                    "Fact: " + fact_txt
                    if fact_txt else "No preview available"
                )

            # 2. Robustly extract Reasoning_Anchor (bold or plain)
            reasoning_match = re.search(
                r"\*{0,2}Reasoning_Anchor:\*{0,2}\s*(.*?)"
                r"(?:\r?\n\*{0,2}[A-Z]|$)",
                content, re.DOTALL)
            reasoning_txt = (
                reasoning_match.group(1).strip() if reasoning_match else "")

            # 3. Print the display row
            print(f"  [{i:2d}] {goal_label} — {concept}")
            print(f"       └─ {preview_txt}")
            if reasoning_txt and reasoning_txt != "N/A":
                print(f"       └─ Logic: {reasoning_txt}")

        print("\n" + "=" * 60)
        raw = input(
            " [?] Reject numbers (e.g. 2,5), 'A' for Anki mode, "
            "or ENTER to keep all >> ").strip()

        if raw.strip().lower() == 'a':
            _use_anki = True
        else:
            try:
                reject_set = set(
                    int(x.strip()) for x in raw.split(',')
                    if x.strip().isdigit()
                )
            except ValueError:
                reject_set = set()

            for i, (concept, content) in enumerate(injected_blocks, 1):
                if i not in reject_set:
                    approved_injected.append(content)
                else:
                    denied_count += 1

        if _use_anki:
            for index, (concept, content) in enumerate(injected_blocks, 1):
                # Short-circuit: if accept_all is True, bulk-approve and continue
                if accept_all:
                    approved_injected.append(content)
                    continue

                goal_match = re.search(r"\*\*Cognitive_Goal:\*\* (.*?)\r?\n", content)
                goal_txt = goal_match.group(1).strip() if goal_match else "UNKNOWN"
                goal_label = goal_labels.get(goal_txt, goal_txt)

                preview_match = re.search(r"\*{0,2}Provisional_Front:\*{0,2}\s*(.*?)(?:\r?\n|$)", content)
                preview_txt = preview_match.group(1).strip() if preview_match and preview_match.group(1).strip() else concept[:60] + " (no preview)"

                progress_str = f"[{'█' * index}{'░' * (len(injected_blocks) - index)}] {index}/{len(injected_blocks)}"

                # STATE 1: Preview
                reason_match = re.search(r"\*\*Reasoning_Anchor:\*\*\s*(.*?)(?=\r?\n\*\*|\Z)", content, re.DOTALL)
                reason_txt = reason_match.group(1).strip() if reason_match else "N/A"
                prov_back_match = re.search(
                    r"\*{0,2}Provisional_Back:\*{0,2}\s*(.*?)(?=\r?\n\*{0,2}[A-Z]|\Z)",
                    content, re.DOTALL)
                prov_back = prov_back_match.group(1).strip() if prov_back_match else ""
                speech_str_s1 = build_speech_p2(goal_label, concept, preview_txt)
                speaker.play(speech_str_s1)
                # Prefetch Stage 2 audio matching Stage 2 display: BOTH prov_back AND reason when both exist
                if prov_back and reason_txt:
                    speaker.prefetch(clean_text(prov_back + ". " + reason_txt))
                elif prov_back:
                    speaker.prefetch(clean_text(prov_back))
                elif reason_txt:
                    speaker.prefetch(clean_text(reason_txt))
                for _la in range(index, index + 3):
                    if _la < len(injected_blocks):
                        _nc, _ncontent = injected_blocks[_la]
                        _ng_match = re.search(r"\*{0,2}Cognitive_Goal:\*{0,2}\s+(.*?)\r?\n", _ncontent)
                        _ng_txt = _ng_match.group(1).strip() if _ng_match else "UNKNOWN"
                        _ng_label = goal_labels.get(_ng_txt, _ng_txt)
                        _np_match = re.search(r"\*{0,2}Provisional_Front:\*{0,2}\s*(.*?)(?:\r?\n|$)", _ncontent)
                        _np_txt = (_np_match.group(1).strip()
                                   if _np_match and _np_match.group(1).strip() else _nc[:60])
                        _nr_match = re.search(r"\*\*Reasoning_Anchor:\*\*\s*(.*?)(?=\r?\n\*\*|\Z)", _ncontent, re.DOTALL)
                        _nr_txt = _nr_match.group(1).strip() if _nr_match else "N/A"
                        speaker.prefetch(build_speech_p2(_ng_label, _nc, _np_txt))
                        speaker.prefetch(clean_text(_nr_txt))
                config.clear_screen()
                print_centered_vertical(goal_label + "\n\n" + preview_txt, progress_str=progress_str)

                while True:
                    choice = input(" [?] (ENTER: Reveal | R: Reject Blindly | A: Accept All | P: Replay) >> ").strip().lower()
                    if choice == 'p':
                        speaker.stop(); speaker.play(speech_str_s1); continue
                    speaker.stop()
                    break

                if choice == "r":
                    denied_count += 1
                    continue
                elif choice == "a":
                    approved_injected.append(content)
                    accept_all = True
                    continue

                # STATE 2: Full Reveal
                rationale_section = ("\n\n▶ " + prov_back + "\n\nRATIONALE: " + reason_txt) if prov_back else ("\n\nRATIONALE: " + reason_txt)
                state2_display = goal_label + "\n\n" + preview_txt + "\n\nCONCEPT: " + concept + rationale_section

                # State 2 reveal — read BOTH provisional_back AND reason when both displayed
                if prov_back and reason_txt:
                    speech_str_s2 = clean_text(prov_back + ". " + reason_txt)
                elif prov_back:
                    speech_str_s2 = clean_text(prov_back)
                else:
                    speech_str_s2 = clean_text(reason_txt) if reason_txt else ""
                speaker.play(speech_str_s2)
                config.clear_screen()
                print_centered_vertical(state2_display, progress_str=progress_str)

                while True:
                    choice2 = input(" [?] (ENTER: Keep & Next | R: Reject | A: Accept All Remaining | P: Replay) >> ").strip().lower()
                    if choice2 == 'p':
                        speaker.stop(); speaker.play(speech_str_s2); continue
                    speaker.stop()
                    break

                if choice2 == "":
                    approved_injected.append(content)
                elif choice2 == "r":
                    denied_count += 1
                elif choice2 == "a":
                    approved_injected.append(content)
                    accept_all = True

    approved_acronyms = []
    rejected_acronym_count = 0

    if acronym_blocks:
        config.clear_screen()
        print("="*60)
        print(" [ PHASE A: ACRONYM BULK VETO ] ".center(60, "#"))
        print("="*60)
        for i, acr in enumerate(acronym_blocks, 1):
            print(f"  [{i}] {acr['concept']} -> {acr['fact']}")
        print("\n" + "="*60)
        raw_input_str = input("\n [?] Enter comma-separated numbers to KEEP (ENTER = skip all) >> ").strip()
        try:
            keep_indices = set(int(x.strip()) for x in raw_input_str.split(",") if x.strip().isdigit())
        except ValueError:
            keep_indices = set()
        for i, acr in enumerate(acronym_blocks, 1):
            if i in keep_indices:
                approved_acronyms.append(acr['content'])
        rejected_acronym_count = len(acronym_blocks) - len(approved_acronyms)

    # 6. FINAL ASSEMBLY AND SAVE (Chronological Preservation)
    final_payload_list = []
    for block_content in blocks[1:]:
        # If this specific text blob was in auto-passed OR approved-injected OR approved-acronyms, keep it here in order
        if block_content in auto_passed_blocks or block_content in approved_injected or block_content in approved_acronyms:
            final_payload_list.append(block_content)

    context_match = re.search(r"<context>.*?</context>", baton_xml, re.DOTALL)
    context_xml = context_match.group(0) if context_match else ""
    
    clean_logic_payload = context_xml + "\n\n### 📦 LOGIC PAYLOAD\n\n[[LOGIC_BLOCK]]" + "[[LOGIC_BLOCK]]".join(final_payload_list)

    # SANITIZATION: Purge EOF markers and Anki-breaking backticks
    clean_logic_payload = re.sub(r"\[EOF.*?\]", "", clean_logic_payload, flags=re.IGNORECASE)
    clean_logic_payload = clean_logic_payload.replace("```", "").replace("`", "").strip()

    config.clear_screen()
    print("="*60)
    print(" [!] CURATION SUMMARY ".center(60, "#"))
    print("="*60)
    green_auto = sum(1 for b in auto_passed_blocks
                     if any(normalize(m) in green_concepts
                            for m in re.findall(
                                r'\*\*Target_Concept:\*\*\s*(.*?)\r?\n',
                                b)))
    non_green_auto = len(auto_passed_blocks) - green_auto
    print(f" [+] Auto-Approved (🟩 GREEN)   : {green_auto}")
    print(f" [+] Auto-Approved (🟦 BLUE)    : {non_green_auto}")
    print(f" [+] Scaffolding Blocks Kept   : {len(approved_injected)}")
    print(f" [-] Scaffolding Blocks Rejected: {denied_count}")
    print(f" [+] Acronyms Kept             : {len(approved_acronyms)}")
    print(f" [-] Acronyms Skipped          : {rejected_acronym_count}")
    print("-" * 60)
    print(f" [*] Final Payload Block Count : {len(final_payload_list)}")
    print("="*60)

    # Provisional_Front and Provisional_Back lines pass through to baton_p2_to_p3.txt unchanged. Phase 3 M6 Framing-Constraint Protocol consumes them during drafting; Python enforcement of M7 (strip from YAML output) is handled by G5' in run_phase3.py.

    with open(_P + "baton_p2_to_p3.txt", "w", encoding="utf-8") as f:
        f.write(clean_logic_payload)
    
    # Pass 2 success already saved in loop forensic logs
    pass


if __name__ == "__main__":
    run_phase2()