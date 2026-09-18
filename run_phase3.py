import config
import time
import os
import re
import sys

UNIT_SWEEP_MODE = os.environ.get("PIPELINE_UNIT_SWEEP", "").upper() == "TRUE"
_P = "unit_sweep_" if UNIT_SWEEP_MODE else ""

def normalize_concept(s):
    s = re.sub(r'\*+', '', s)
    s = ' '.join(s.split())
    s = s.lower()
    s = s.strip()
    return s

def merge_yaml_patch(base_yaml, patch_input):
    """Merges a surgical YAML patch into the base card set using single-pass sequential tokenizer."""

    # Step 1 — Parse base_yaml into ordered dict
    base_segments = re.split(r'(?m)^---(?:\s*\n)?', base_yaml)
    base_dict = {}
    for seg in base_segments:
        if not seg.strip():
            continue
        id_m = re.search(r'(?m)^ID:\s*(\d+)', seg)
        if id_m:
            base_dict[int(id_m.group(1))] = seg

    # Step 2 — Extract patch content and empty patch guard
    fi_m = re.search(r'<final_yaml_payload>(.*?)</final_yaml_payload>', patch_input, re.DOTALL)
    patch_content = fi_m.group(1).strip() if fi_m else patch_input

    has_id = bool(re.search(r'(?m)^ID:\s*\d+', patch_content))
    has_dsl = any(sig in patch_content for sig in ('[[KILL_CARD]]', '[[MERGE]]', '[[SPLIT]]'))
    if not has_id and not has_dsl:
        print(' [P3 MERGE: ZERO PATCHES — BASE RETURNED UNCHANGED]')
        return base_yaml

    # Step 3 — Sequential tokenizer (single-pass)
    segments = re.split(r'(?m)^---(?:\s*\n)?', patch_content)
    n_in = len(base_dict)
    modified = 0
    injected = 0
    killed = 0
    merged_count = 0
    split_count = 0
    new_id_mapping = {}  # "NEW_1" -> float_key from SPLIT operations

    i = 0
    while i < len(segments):
        seg = segments[i]
        if not seg.strip():
            i += 1
            continue

        # A. KILL check (handles both integer IDs and NEW_N references from SPLIT)
        kill_m = re.search(r'\[\[KILL_CARD\]\]\s*ID:\s*(\w+)', seg)
        if kill_m:
            kid_str = kill_m.group(1)
            if kid_str in new_id_mapping:
                target_key = new_id_mapping[kid_str]
                if target_key in base_dict:
                    del base_dict[target_key]
                    print(f' [P3 KILL] {kid_str} -> float key {target_key}')
                    killed += 1
                del new_id_mapping[kid_str]
            elif kid_str.startswith("NEW_"):
                print(f' [P3 KILL WARNING] Orphan {kid_str} reference, no SPLIT in scope. Skipped.')
            else:
                try:
                    kid = int(kid_str)
                    if kid in base_dict:
                        del base_dict[kid]
                        print(f' [P3 KILL] ID {kid}')
                        killed += 1
                except ValueError:
                    print(f' [P3 KILL WARNING] Invalid ID "{kid_str}". Skipped.')
            i += 1
            continue

        # B. MERGE check
        merge_m = re.search(
            r'\[\[MERGE\]\]\s*SOURCE_IDS:\s*([\d,\s]+)\s*(?:->|→)\s*TARGET_ID:\s*(\d+)',
            seg)
        if merge_m:
            source_ids = [int(x.strip()) for x in merge_m.group(1).split(',')]
            target_id = int(merge_m.group(2))
            j = i + 1
            while j < len(segments) and not segments[j].strip():
                j += 1
            if j < len(segments):
                base_dict[target_id] = segments[j]
                for sid in source_ids:
                    if sid != target_id and sid in base_dict:
                        del base_dict[sid]
                print(f' [P3 MERGE] SOURCE_IDS {source_ids} → TARGET_ID {target_id}')
                merged_count += 1
                i = j + 1
            else:
                i += 1
            continue

        # C. SPLIT check
        split_m = re.search(
            r'\[\[SPLIT\]\]\s*SOURCE_ID:\s*(\d+)\s*(?:->|→)\s*TARGET_IDS:\s*(\d+),\s*(NEW_\d+)',
            seg)
        if split_m:
            source_id = int(split_m.group(1))
            j = i + 1
            while j < len(segments) and not segments[j].strip():
                j += 1
            k = j + 1
            while k < len(segments) and not segments[k].strip():
                k += 1
            if j < len(segments) and k < len(segments):
                float_key = source_id + 0.1
                new_id_string = split_m.group(3)  # e.g. "NEW_1"
                base_dict[source_id] = segments[j]
                base_dict[float_key] = segments[k]
                # Guard: LLMs sometimes embed [[KILL_CARD]] inside the NEW_N block
                # instead of emitting it as a standalone segment. Detect and suppress.
                if '[[KILL_CARD]]' in segments[k]:
                    del base_dict[float_key]
                    print(f' [P3 KILL embedded] {new_id_string} -> float key {float_key} suppressed at SPLIT time')
                    killed += 1
                    split_count += 1
                else:
                    new_id_mapping[new_id_string] = float_key
                    print(f' [P3 SPLIT] SOURCE_ID {source_id} -> {source_id} + {new_id_string} (float key {float_key})')
                    split_count += 1
                i = k + 1
            else:
                i += 1
            continue

        # D. Implicit MODIFY / INJECT
        new_id_m = re.search(r'(?m)^ID:\s*(NEW_\d+)', seg)
        if new_id_m:
            print(f' [P3 WARNING: Orphan NEW_N segment encountered outside SPLIT context — skipped]')
            i += 1
            continue

        id_m = re.search(r'(?m)^ID:\s*(\d+)', seg)
        if id_m:
            card_id = int(id_m.group(1))
            if card_id in base_dict:
                base_dict[card_id] = seg
                print(f' [P3 MODIFY] ID {card_id}')
                modified += 1
            else:
                base_dict[card_id] = seg
                print(f' [P3 INJECT] ID {card_id}')
                injected += 1
        i += 1

    # Step 5 — Re-sort and re-sequence IDs
    sorted_items = sorted(base_dict.items(), key=lambda x: x[0])
    new_dict = {}
    for new_id, (old_key, block) in enumerate(sorted_items, 1):
        updated_block = re.sub(r'(?m)^(ID:\s*)\S+', f'ID: {new_id}', block, count=1)
        new_dict[new_id] = updated_block

    # Step 6 — Reconstruct
    n_out = len(new_dict)
    result = "\n---\n".join(b.strip('\n') for b in new_dict.values() if b.strip())

    # Step 7 — Log summary
    print(f' [P3 MERGE COMPLETE] [{modified}] modified, [{injected}] injected, [{killed}] killed, [{merged_count}] merged, [{split_count}] split. Input: [{n_in}] cards. Output: [{n_out}] cards.')

    return result

def run_phase3():
    print(" [!] PHASE 3 SPECIALIST: THE FORMULATOR (CARD FACTORY)")
    print("-" * 50)

    # 1. READ INPUTS
    if not os.path.exists(_P + "baton_p2_to_p3.txt"):
        print(f" [X] Error: '{_P}baton_p2_to_p3.txt' missing! Run upstream phase first.")
        sys.exit(1)

    with open(_P + "baton_p2_to_p3.txt", "r", encoding="utf-8") as f:
        baton_text = f.read()

    # Provisional_Front and Provisional_Back are intentionally present in baton_text — Phase 3 LLM consumes them per M6 Framing-Constraint Protocol Steps 1-4 before Step 5 strips them from YAML output. Python M7 enforcement is at the YAML output boundary below (G5').

    original_baton_text = baton_text

    raw_parts = baton_text.split("[[LOGIC_BLOCK]]")

    baton_preamble = raw_parts[0].strip()

    concept_blocks = []
    acronym_blocks = []
    _hier_re = re.compile(r'\*\*Hierarchy:\*\*\s*(.*)')

    for _raw_part in raw_parts[1:]:
        _part = _raw_part.strip()
        if not _part:
            continue
        _hier_m = _hier_re.search(_part)
        _hier_line = _hier_m.group(1).strip() if _hier_m else ""
        if "ACRONYM_EXILE" in _hier_line:
            acronym_blocks.append(_part)
        else:
            concept_blocks.append(_part)

    expected_concept_count = len(concept_blocks)
    expected_acronym_count = len(acronym_blocks)
    expected_total = expected_concept_count + expected_acronym_count

    print(f"✅ BATON PARSED: {expected_concept_count} concept blocks, {expected_acronym_count} acronym blocks, {expected_total} total.")

    if len(concept_blocks) <= config.P3_CHUNK_THRESHOLD:
        chunks = [concept_blocks + acronym_blocks]
        print("✅ DECK WITHIN THRESHOLD — single chunk, no split required.")
    else:
        midpoint = len(concept_blocks) // 2

        def extract_cluster(block_str):
            m = re.search(r'\*\*Cluster:\*\*\s*(.*)', block_str)
            return m.group(1).strip() if m else ""

        split_index = midpoint
        found_boundary = False
        fallback_reason = None

        while split_index < len(concept_blocks) - 1:
            cluster_current = extract_cluster(concept_blocks[split_index])
            cluster_next = extract_cluster(concept_blocks[split_index + 1])
            if cluster_current != cluster_next:
                found_boundary = True
                break
            if (split_index - midpoint) >= config.P3_MAX_WALK_DISTANCE:
                split_index = midpoint
                fallback_reason = "MAX_WALK"
                found_boundary = False
                break
            split_index += 1

        if not found_boundary and fallback_reason is None:
            split_index = midpoint
            fallback_reason = "NO_BOUNDARY_FOUND"
            print("⚠️ NO CLUSTER BOUNDARY FOUND — forcing cut at midpoint.")

        chunk1_blocks = concept_blocks[0 : split_index + 1]
        chunk2_blocks = concept_blocks[split_index + 1 :] + acronym_blocks

        chunks = [chunk1_blocks, chunk2_blocks]

        if found_boundary:
            c1_cluster = extract_cluster(chunk1_blocks[-1])
            c2_cluster = extract_cluster(chunk2_blocks[0])
            print(f"✅ SPLIT CONFIRMED")
            print(f" Chunk 1 ends on cluster: {c1_cluster}")
            print(f" Chunk 2 begins on cluster: {c2_cluster}")
            if c1_cluster and c2_cluster:
                assert c1_cluster != c2_cluster, (
                    "ERROR: Cluster walk produced identical boundary clusters. "
                    "Review walk logic."
                )
            else:
                print(
                    f"⚠️ WARNING: Could not parse cluster from boundary block "
                    f"(c1='{c1_cluster}', c2='{c2_cluster}'). "
                    f"Cluster assertion skipped — verify **Cluster:** field in "
                    f"blocks at split index {split_index} and {split_index + 1}."
                )
        else:
            print(
                f"⚠️ FALLBACK CUT APPLIED ({fallback_reason}) — chunks may share a cluster. "
                f"This is normal. Chunk 1: {len(chunk1_blocks)} blocks | Chunk 2: {len(chunk2_blocks)} blocks."
            )

    if not os.path.exists("Prompts/prompt3_formulator.txt"):
        print(" [X] Error: 'Prompts/prompt3_formulator.txt' missing from folder!")
        sys.exit(1)

    with open("Prompts/prompt3_formulator.txt", "r", encoding="utf-8") as f:
        p3_text = f.read()

    # ==========================================
    # 2. ITERATIVE REFINEMENT LOOP (2 PASSES)
    # ==========================================

    chunk_outputs = []
    total_chunks = len(chunks)

    # ── RESUME-FROM-CHECKPOINT ──────────────────────────────────
    resume_from_index = 0      # loop skips chunk_index < this value
    _ckpt_preloaded = {}       # {chunk_index: raw_card_text} loaded from disk

    if total_chunks > 1:
        print("━" * 40)
        print(f"⚠️  BATON TOO LARGE — splitting into {total_chunks} chunks.")
        for _ci, _cbl in enumerate(chunks):
            print(f"   Chunk {_ci + 1}: {len(_cbl)} blocks")
        print("━" * 40)

        def _extract_yaml_from_raw(raw_text):
            fi_m = re.findall(
                r"<final_yaml_payload>(.*?)</final_yaml_payload>", raw_text, re.DOTALL
            )
            if fi_m:
                out = "\n".join(fi_m)
            else:
                bt_m = re.findall(r"```(?:text|yaml)?\n(.*?)\n```", raw_text, re.DOTALL)
                out = "\n".join(bt_m) if bt_m else raw_text
            out = re.sub(r'(?m)^```\w*\s*$', '', out)
            out = re.sub(r'(?m)^```\s*$',    '', out)
            out = re.sub(r'(?m)^### 📦 YAML PAYLOAD\s*$', '', out)
            out = re.sub(r'(?m)^\[EOF.*?\]\s*$', '', out, flags=re.IGNORECASE)
            return out.strip()

        _start_input = input(
            f" [?] Start from which chunk? (1–{total_chunks}) >> "
        ).strip()
        try:
            _start_chunk = int(_start_input)
        except ValueError:
            _start_chunk = 1
        _start_chunk = max(1, min(_start_chunk, total_chunks))
        resume_from_index = _start_chunk - 1

        if resume_from_index > 0:
            print(f" [>] Loading chunks 1–{resume_from_index} from forensic logs...")
            for _load_n in range(1, resume_from_index + 1):
                _forensic_path = _P + f"forensic_raw_p3_pass1_chunk{_load_n}.txt"
                if not os.path.exists(_forensic_path):
                    print(f" [!] ERROR: {_forensic_path} not found. Cannot resume.")
                    print(" [!] Restarting from chunk 1.")
                    resume_from_index = 0
                    _ckpt_preloaded = {}
                    break
                with open(_forensic_path, "r", encoding="utf-8") as _cf:
                    _raw = _cf.read()
                _ckpt_preloaded[_load_n - 1] = _extract_yaml_from_raw(_raw)
                print(f"     Loaded chunk {_load_n} from {_forensic_path}.")
            else:
                print(f" [>] Resuming from chunk {_start_chunk}.")
        else:
            print(" [>] Starting from chunk 1.")
    # ── END RESUME SETUP ────────────────────────────────────────

    for chunk_index, chunk_block_list in enumerate(chunks):
        chunk_num = chunk_index + 1

        # ── CHECKPOINT SKIP ─────────────────────────────────────
        if chunk_index < resume_from_index:
            print(f" [>] Skipping chunk {chunk_num} (loaded from checkpoint).")
            chunk_outputs.append(_ckpt_preloaded[chunk_index])
            continue
        # ── END SKIP ─────────────────────────────────────────────

        chunk_payload = baton_preamble + "\n\n"
        for block in chunk_block_list:
            chunk_payload += "[[LOGIC_BLOCK]]\n\n" + block + "\n\n"
        chunk_payload = chunk_payload.strip()

        chunk_prompt = p3_text.replace(
            "[👉PASTE THE [[LOGIC_BLOCK]] STREAM FROM PROMPT 2 HERE👈]", chunk_payload
        ).replace(
            "[👉LEAVE EMPTY FOR MODE 1. PASTE DRAFTED CARDS HERE FOR MODE 2👈]", ""
        )

        print("━" * 40)
        print(f"PHASE 3 | PASS 1 | CHUNK {chunk_num} OF {total_chunks}")
        print(f"Blocks in this chunk: {len(chunk_block_list)}")

        raw_response = config.call_llm(
            chunk_prompt,
            context_header=f"PHASE 3 | PASS 1 | CHUNK {chunk_num}",
            phase="P3",
            pass_num=1
        )
        if not raw_response:
            print(f"\n [X] Fatal Error: Phase 3 | Pass 1 | Chunk {chunk_num} returned empty response. Aborting.")
            sys.exit(1)

        # 1. Extract from <final_yaml_payload> tags
        fi_matches = re.findall(
            r"<final_yaml_payload>(.*?)</final_yaml_payload>",
            raw_response, re.DOTALL
        )
        if fi_matches:
            raw_card_text = "\n".join(fi_matches)
        else:
            # Fallback: extract from triple-backtick fences
            bt_matches = re.findall(r"```(?:text|yaml)?\n(.*?)\n```", raw_response, re.DOTALL)
            raw_card_text = "\n".join(bt_matches) if bt_matches else raw_response
            if not bt_matches:
                print(f" [!] WARNING: Chunk {chunk_num}: No <final_yaml_payload> tag found. Using raw response fallback.")

        # 2. Strip triple-backtick fence lines (opening ```text/yaml and closing ```)
        raw_card_text = re.sub(r'(?m)^```\w*\s*$', '', raw_card_text)
        raw_card_text = re.sub(r'(?m)^```\s*$',    '', raw_card_text)

        # 3. Strip the YAML header line
        raw_card_text = re.sub(r'(?m)^### 📦 YAML PAYLOAD\s*$', '', raw_card_text)

        # 4. Strip the EOF footer line
        raw_card_text = re.sub(r'(?m)^\[EOF.*?\]\s*$', '', raw_card_text, flags=re.IGNORECASE)

        # 5. Final whitespace strip
        raw_card_text = raw_card_text.strip()
        raw_card_text = raw_card_text.replace('\r\n', '\n').replace('\r', '\n')

        if not raw_card_text:
            print(f"\n [X] CHUNK {chunk_num} EXTRACTION FAILURE: No <final_yaml_payload> content found.")
            print(f" [X] Check the LLM response manually. Pipeline cannot safely continue.")
            sys.exit(1)

        HALTED_SIGNAL = "[⚠️ HALTED: LIMIT REACHED"
        if HALTED_SIGNAL in raw_card_text:
            card_lines = len([l for l in raw_card_text.splitlines() if l.startswith("ID:")])
            print(f"\n [X] CHUNK {chunk_num} HALTED: Formulator hit its output token limit.")
            print(f" [X] Partial output captured: ~{card_lines} cards before halt.")
            print(f" [X] OPTIONS:")
            print(f"     (1) Lower config.P3_CHUNK_THRESHOLD to force smaller chunks.")
            print(f"     (2) Disable SONNET_EXTENDED_THINKING for Phase 3 to free output budget.")
            sys.exit(1)

        chunk_outputs.append(raw_card_text)

        # ── WRITE CHECKPOINT ────────────────────────────────────
        if total_chunks > 1:
            _ckpt_write_path = _P + f"p3_chunk{chunk_num}_raw_cards.txt"
            with open(_ckpt_write_path, "w", encoding="utf-8") as _ckf:
                _ckf.write(raw_card_text)
            print(f" [>] Checkpoint saved: {_ckpt_write_path}")
        # ── END CHECKPOINT ───────────────────────────────────────

        log_name = _P + f"forensic_raw_p3_pass1_chunk{chunk_num}.txt"
        with open(log_name, "w", encoding="utf-8") as f:
            f.write(
                f"### FORENSIC LOG: PASS 1 | CHUNK {chunk_num} OF {total_chunks} | "
                f"MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + raw_response
            )

        print(f"✅ Chunk {chunk_num} of {total_chunks} captured. Cards: {raw_card_text.count('---')}")

    raw_combined = "\n".join(chunk_outputs)

    _id_counter = [0]
    def _id_replacer(match):
        _id_counter[0] += 1
        return f"ID: {_id_counter[0]}"
    base_yaml_body = re.sub(
        r'^ID:\s*\d+$',
        _id_replacer,
        raw_combined,
        flags=re.MULTILINE
    )
    actual_final_id = _id_counter[0]

    base_yaml = re.sub(r'^---[ \t]*\n?', '', base_yaml_body.lstrip('\n'), count=1)

    audit_target_yaml = (
        "### 📦 YAML PAYLOAD\n"
        + base_yaml_body
        + "\n[EOF - ALL DATA PROCESSED (FORMULATOR v3.0)]"
    )

    found_ids = re.findall(r'^ID:\s*\d+$', base_yaml, flags=re.MULTILINE)
    assert len(found_ids) > 0, "ERROR: Re-sequencing failed — no ID fields found in combined output. Verify Formulator YAML structure."
    assert found_ids[0] == "ID: 1", "ERROR: Re-sequencing failed — first card is not ID: 1."
    assert len(set(found_ids)) == len(found_ids), "ERROR: Re-sequencing produced duplicate IDs."
    if actual_final_id < expected_concept_count // 2:
        print(f"⚠️ WARNING: Final card count ({actual_final_id}) seems very low vs. input ({expected_total} blocks). Verify Formulator output manually.")

    print(f"✅ GLUE COMPLETE — {actual_final_id} cards total, IDs 1–{actual_final_id}.")

    print("━" * 40)
    print("PHASE 3 | PASS 2 | SOVEREIGN AUDIT")
    print(f"Logic payload: {expected_total} source blocks")
    print(f"Audit target: {actual_final_id} drafted cards")

    prompt_p2 = p3_text.replace(
        "[👉PASTE THE [[LOGIC_BLOCK]] STREAM FROM PROMPT 2 HERE👈]", original_baton_text
    ).replace(
        "[👉LEAVE EMPTY FOR MODE 1. PASTE DRAFTED CARDS HERE FOR MODE 2👈]", audit_target_yaml
    )
    prompt_p2 += "\n\n(FORMULATOR)"

    raw_response_p2 = config.call_llm(
        prompt_p2,
        context_header="PHASE 3 | PASS 2",
        phase="P3",
        pass_num=2
    )
    if not raw_response_p2:
        print("\n [X] Fatal Error: Phase 3 | Pass 2 (Sovereign Audit) returned empty response. Aborting.")
        sys.exit(1)

    with open(_P + "forensic_raw_p3_pass2.txt", "w", encoding="utf-8") as f:
        f.write(
            f"### FORENSIC LOG: PASS 2 | MODEL: {config.LAST_ACTIVE_MODEL}\n"
            + "="*60 + "\n" + raw_response_p2
        )

    matches = re.findall(
        r"<final_yaml_payload>(.*?)</final_yaml_payload>",
        raw_response_p2, re.DOTALL
    )
    extracted_p2 = "\n".join(matches).strip() if matches else raw_response_p2.strip()

    current_yaml = merge_yaml_patch(base_yaml, extracted_p2)

    # Pipeline integrity sentinel: flag silent merge failures before they propagate
    _p1_count = len(re.findall(r'(?m)^ID:\s*\d+', base_yaml))
    _p2_count = len(re.findall(r'(?m)^ID:\s*[\w.]+', current_yaml))
    if _p2_count == _p1_count and _p1_count > 0:
        # Identical count is normal for MODIFY-only patches; no warning
        pass
    elif _p2_count == 0:
        print(f" [P3 ABORT] Merge produced 0 cards (input had {_p1_count}). Pass 2 patch likely malformed. Inspect forensic_raw_p3_pass2.txt before continuing.")
        sys.exit(1)
    else:
        print(f" [P3 NOTE] Card count after merge: {_p1_count} -> {_p2_count} (deltas from KILL/MERGE/SPLIT are expected)")

    with open(_P + "forensic_merged_p3.txt", "w", encoding="utf-8") as f:
        f.write(
            f"### MERGED STATE: POST-PASS 2 | MODEL: {config.LAST_ACTIVE_MODEL}\n"
            + "="*60 + "\n" + current_yaml
        )

    # ==========================================
    # 3. THE HACKER VETO STATION (LOBOTOMY MODE)
    # ==========================================
    print(" [>] Sanitizing and Formatting YAML output...")

    # SANITIZATION: Purge EOF markers and Anki-breaking backticks
    curated_yaml = re.sub(r"\[EOF.*?\]", "", current_yaml, flags=re.IGNORECASE)
    curated_yaml = curated_yaml.replace("```", "").replace("`", "").strip()

    # M7 PYTHON ENFORCEMENT (defense-in-depth): Strip Provisional_Front and Provisional_Back from YAML output.
    # M7 is LLM-enforced at Phase 3; this is the Python backstop catching LLM compliance drift before downstream
    # phases (Phase 4 is additive-only; Phase 5 MODIFY path skips field-count validation per
    # run_phase5.py:284-293 INJECT-only gate).
    _m7_residual = len(re.findall(r"(?m)^\*{0,2}Provisional_(?:Front|Back):\*{0,2}.*$", curated_yaml))
    if _m7_residual > 0:
        curated_yaml = re.sub(r"(?m)^\*{0,2}Provisional_(?:Front|Back):\*{0,2}.*$\n?", "", curated_yaml)
        print(f" [!] M7 COMPLIANCE FAILURE: {_m7_residual} Provisional_Front/Back line(s) stripped from YAML output. Inspect forensic_raw_p3_pass2.txt (raw Pass 2 LLM output) and forensic_merged_p3.txt (post-merge state) to identify the source of the leak.")

    # Re-apply the opening/closing separators for YAML compliance
    final_file_text = "---\n" + curated_yaml + "\n---"
    with open(_P + "final_anki_cards.txt", "w", encoding="utf-8") as f:
        f.write(final_file_text)

    print(f"\n [+] Success: YAML payload directly saved to final_anki_cards.txt.")

    config.clear_screen()
    print("="*60)
    print(" [!] PHASE 3 COMPLETE: DATA PREPARED FOR PHASE 4 ".center(60, "#"))
    print("="*60)
    for _cn in range(1, total_chunks + 1):
        print(f" [+] Pass 1 / Chunk {_cn} : SUCCESS")
    print(f" [+] Pass 2 (Auditor)  : SUCCESS")
    print(f" [+] Final Output Saved  : final_anki_cards.txt")
    print(f" [+] Forensic Logs (P1) : forensic_raw_p3_pass1_chunk1.txt"
          + (f" through forensic_raw_p3_pass1_chunk{total_chunks}.txt"
             if total_chunks > 1 else ""))
    print(f" [+] Forensic Logs (P2) : forensic_raw_p3_pass2.txt | forensic_merged_p3.txt")
    print("="*60)

if __name__ == "__main__":
    run_phase3()
