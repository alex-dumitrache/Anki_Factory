import config
import time
import os
import re
import sys

UNIT_SWEEP_MODE = os.environ.get("PIPELINE_UNIT_SWEEP", "").upper() == "TRUE"
_P = "unit_sweep_" if UNIT_SWEEP_MODE else ""

def merge_reverse_patch(base_yaml, patch_raw):
    # 1. Empty patch guard
    if not re.search(r'(?m)^ID:\s*\d+', patch_raw):
        print("[P4 MERGE: ZERO PATCHES — BASE RETURNED UNCHANGED]")
        return base_yaml

    # 2. Parse base_yaml into ordered dict
    base_dict = {}
    order = []
    raw_blocks = re.split(r'(?m)^---\s*$', base_yaml)
    for block in raw_blocks:
        block = block.strip()
        if not block:
            continue
        m = re.search(r'(?m)^ID:\s*(\d+)', block)
        if m:
            card_id = int(m.group(1))
            base_dict[card_id] = block
            order.append(card_id)

    # 3. Parse patch_raw: extract from <final_payload> tags
    payload_matches = re.findall(r'<final_payload>(.*?)</final_payload>', patch_raw, re.DOTALL)
    patch_content = "\n".join(payload_matches).strip() if payload_matches else patch_raw.strip()
    patch_segments = re.split(r'(?m)^---\s*$', patch_content)

    patched_count = 0
    for segment in patch_segments:
        segment = segment.strip()
        if not segment:
            continue

        # a. Extract ID
        id_match = re.search(r'(?m)^ID:\s*(\d+)', segment)
        if not id_match:
            continue
        card_id = int(id_match.group(1))

        # b. Extract Rev_Front and Rev_Back
        rev_front_match = re.search(r'(?m)^Rev_Front:\s*(.+)$', segment)
        rev_back_match = re.search(r'(?m)^Rev_Back:\s*(.+)$', segment)
        if not rev_front_match or not rev_back_match:
            continue

        # c. FORMAT DRIFT GUARD: more than 3 field lines means Gemini emitted a full block
        field_lines = [l for l in segment.splitlines() if re.match(r'^\w[\w_]*\s*:', l)]
        if len(field_lines) > 3:
            print(f"[P4 FORMAT DRIFT WARNING] Full block received for ID {card_id}, extracted triplet only.")

        new_rev_front = rev_front_match.group(1).strip()
        new_rev_back = rev_back_match.group(1).strip()

        if card_id not in base_dict:
            continue

        card_block = base_dict[card_id]

        # d. Replace Rev_Front and Rev_Back using line-anchored regex
        if re.search(r'(?m)^Rev_Front:.*$', card_block):
            card_block = re.sub(r'(?m)^Rev_Front:.*$', f'Rev_Front: {new_rev_front}', card_block, count=1)
        else:
            # e. Append Rev_Front if missing
            card_block = card_block + f'\nRev_Front: {new_rev_front}'

        if re.search(r'(?m)^Rev_Back:.*$', card_block):
            card_block = re.sub(r'(?m)^Rev_Back:.*$', f'Rev_Back: {new_rev_back}', card_block, count=1)
        else:
            # e. Append Rev_Back if missing
            card_block = card_block + f'\nRev_Back: {new_rev_back}'

        base_dict[card_id] = card_block
        patched_count += 1

    # 4. Reconstruct in original ID order
    unchanged_count = len(order) - patched_count
    result = "\n---\n".join(base_dict[cid] for cid in order)

    # 5. Log summary
    print(f"[P4 MERGE COMPLETE] {patched_count} triplets patched. {unchanged_count} cards unchanged.")

    return result

def run_phase4():
    print(" [!] PHASE 4 SPECIALIST: THE REVERSE ENGINEER (2-PASS ASYMMETRY SUPREME)")
    print("-" * 50)

    # 1. READ INPUTS
    if not os.path.exists(_P + "final_anki_cards.txt"):
        print(f" [X] Error: '{_P}final_anki_cards.txt' missing! Run upstream phase first.")
        sys.exit(1)

    with open(_P + "final_anki_cards.txt", "r", encoding="utf-8") as f:
        yaml_payload = f.read()

    if not os.path.exists("Prompts/prompt4_reverse.txt"):
        print(" [X] Error: 'Prompts/prompt4_reverse.txt' missing from folder!")
        sys.exit(1)

    with open("Prompts/prompt4_reverse.txt", "r", encoding="utf-8") as f:
        p4_base_text = f.read()

    # Define exact string to replace based on your prompt text
    target_payload_placeholder = "[👉PASTE THE OUTPUT FROM PROMPT 3 HERE👈]"

    # ==========================================
    # BATCH SIZE GUARD (PY-A)
    # ==========================================
    card_count = len(re.findall(r'(?m)^ID:\s*\d+', yaml_payload))
    if card_count > 25:
        print(f"\n ⚠️  CAUTION: {card_count} cards detected in payload.")
        print("    P4 now runs heavier Tier-1/Tier-2 + 5 Sovereign post-construction checks per card.")
        print("    Large batches increase truncation and compliance-theater risk.")
        print("    Consider splitting into sub-batches of ≤ 25 cards for reliable output quality.\n")

    # ==========================================
    # ITERATIVE REFINEMENT LOOP (2 PASSES)
    # ==========================================
    current_payload = yaml_payload
    total_passes = 2
    base_yaml = ""

    for pass_num in range(1, total_passes + 1):
        if pass_num == 1:
            print(f" [>] PASS 1: Executing Bijective Orthogonality Draft (Mode 1)...")
            prompt = p4_base_text.replace(target_payload_placeholder, current_payload)
        else:
            print(f" [>] PASS {pass_num}: Executing The Reverse Purge (Mode 2 - Pass {pass_num-1})...")
            # Ingest CLEAN YAML from previous pass
            prompt = p4_base_text.replace(target_payload_placeholder, current_payload)
            prompt += "\n\n(REVERSE ENGINEER v3.7)"

        raw_response = config.call_llm(prompt, context_header=f"PHASE 4 | PASS {pass_num}", phase="P4", pass_num=pass_num)

        if not raw_response:
            print(f" [X] Fatal Error in Pass {pass_num}. Aborting.")
            sys.exit(1)

        # Save individual forensic logs (includes full audit ledgers for Mode 2)
        log_name = _P + f"forensic_raw_p4_pass{pass_num}.txt"
        with open(log_name, "w", encoding="utf-8") as f:
            f.write(f"### FORENSIC LOG: PASS {pass_num} | MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + raw_response)

        if pass_num == 1:
            base_yaml = merge_reverse_patch(yaml_payload, raw_response)
            # Sovereign Silence: fill N/A for any card IDs absent from Mode 1 output
            engineered = len(re.findall(r'(?m)^Rev_Front:', base_yaml))
            filled_blocks = []
            for b in re.split(r'(?m)^---\s*$', base_yaml):
                b = b.strip()
                if not b:
                    continue
                if not re.search(r'(?m)^Rev_Front:', b):
                    b += '\nRev_Front: "N/A"'
                if not re.search(r'(?m)^Rev_Back:', b):
                    b += '\nRev_Back: "N/A"'
                filled_blocks.append(b)
            base_yaml = "\n---\n".join(filled_blocks)
            current_payload = base_yaml
            total_ids = re.findall(r'(?m)^ID:\s*\d+', yaml_payload)
            na_filled = len(total_ids) - engineered
            print(f"[P4 PASS 1 VERIFY] Sovereign Silence active.")
            print(f" -> Reversals engineered: {engineered}/{len(total_ids)} | Silent N/A fills: {na_filled}")
        else:
            current_payload = merge_reverse_patch(base_yaml, raw_response)
            with open(_P + "forensic_merged_p4.txt", "w", encoding="utf-8") as f:
                f.write(current_payload)

    # Loop concluded; the payload is now refined and flipped
    # SANITIZATION: Purge EOF markers and Anki-breaking backticks
    current_payload = re.sub(r"\[EOF.*?\]", "", current_payload, flags=re.IGNORECASE)
    current_payload = current_payload.replace("```", "").strip()

    # Prepend the Enriched header required for the Phase 5 Handshake
    final_data_body = "### 📦 ENRICHED YAML PAYLOAD\n\n" + current_payload

    # Save the Final, bi-directional YAML for Anki
    with open(_P + "final_anki_cards_with_reverse.txt", "w", encoding="utf-8") as f:
        f.write(final_data_body)

    config.clear_screen()
    print("="*60)
    print(" [!] PHASE 4 COMPLETE: BI-DIRECTIONAL DECK SECURED ".center(60, "#"))
    print("="*60)
    for pass_num in range(1, total_passes + 1):
        print(f" [+] Pass {pass_num}   : SUCCESS")
    print(" [+] Final Output Saved  : final_anki_cards_with_reverse.txt")
    print(f" [+] Forensic Logs        : forensic_raw_p4_pass1 through pass{total_passes}.txt")
    print("="*60)

if __name__ == "__main__":
    run_phase4()
