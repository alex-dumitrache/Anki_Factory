import config
import time
import os
import re
import sys
import json
import platform
import subprocess
import webbrowser
import random
from tts_reader import speaker, build_speech_p5, clean_text
from image_media import store_compressed_image


_CD_FIELD_CAPS = {
    "TONE_FRAME": 50,
    "CHEMISTRY_DYNAMIC": 90,
    "HOST_A_PERSONA": 235,
    "HOST_B_PERSONA": 235,
    "HOST_B_INTENSITY_STYLE": 120,
    "HOST_A_REGISTER": 540,
    "HOST_B_REGISTER": 540,
}
_CD_MIN_FRAGMENTS = 20
_CD_LABEL_LEAKS = ("interjections", "idioms/similes", "idioms --", "address --",
                   "slang --", "grammar/tics", "metaphors from", "noun-swaps")


def _cd_validate_pairing(data):
    """Shape gate for the GENERATED persona: reject labelled-clause drift + thin banks.
    Returns (ok, problems). Wired into the CALL-2 retry loop; on double-fail the UI
    shows '[2] GENERATED: [unavailable]' exactly as on an API failure."""
    problems = []
    for host in ("HOST_A_REGISTER", "HOST_B_REGISTER"):
        reg = data.get(host, "")
        low = reg.lower()
        frags = [f for f in reg.split("|") if f.strip()]
        if len(frags) < _CD_MIN_FRAGMENTS:
            problems.append(f"{host}: {len(frags)} fragments (need >= {_CD_MIN_FRAGMENTS})")
        if any(leak in low for leak in _CD_LABEL_LEAKS) or ";" in reg:
            problems.append(f"{host}: labelled-clause drift")
        if " -- " not in reg:
            problems.append(f"{host}: missing leading dialect label")
    for field, cap in _CD_FIELD_CAPS.items():
        if len(data.get(field, "")) > cap * 1.15:
            problems.append(f"{field}: {len(data.get(field, ''))} chars (cap {cap})")
    return (not problems), problems


UNIT_SWEEP_MODE = os.environ.get("PIPELINE_UNIT_SWEEP", "").upper() == "TRUE"
_P = "unit_sweep_" if UNIT_SWEEP_MODE else ""

# On-card TTS audio destination (GRAFT 2): Anki's collection.media for the
# active profile. None disables audio injection gracefully (non-Windows, or
# folder absent) so the export never crashes over a missing media path.
_appdata = os.environ.get("APPDATA", "")
ANKI_MEDIA_DIR = os.path.join(_appdata, "Anki2", "User 1", "collection.media") if _appdata else None
if ANKI_MEDIA_DIR and not os.path.isdir(ANKI_MEDIA_DIR):
    ANKI_MEDIA_DIR = None

# Image feature source folders: where the Chief Architect drops pictures.
# IMG_SUPPORT_DIR = loose images matched onto existing cards (Mode A); IDENTIFY_DIR
# = images that each become their own "name this" card (Mode B). Each collapses to
# None if absent, so both features skip cleanly on any machine. Change these two
# paths to relocate the folders.
_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
IMG_SUPPORT_DIR = os.path.join(_desktop, "img")
if not os.path.isdir(IMG_SUPPORT_DIR):
    IMG_SUPPORT_DIR = None
IDENTIFY_DIR = os.path.join(_desktop, "img", "identify")
if not os.path.isdir(IDENTIFY_DIR):
    IDENTIFY_DIR = None

def normalize(text):
    """Fuzzy Logic: Strips extra words, parens, and spaces for matching."""
    # Removes anything inside parentheses and condenses the string
    text = re.sub(r'\(.*?\)', '', text)
    return "".join(text.split()).lower().strip()

def harvest_telemetry():
    """
    Scan forensic logs from this run, extract <telemetry_log> entries, filter
    None/empty, append valid entries (with traceability) to the persistent
    prompt_telemetry_database.txt in the project root.
    """
    import datetime
    import glob

    # Discover video/module identifier from baton files (P1 -> P2 -> P3 chain)
    video_id = "unknown"
    for baton_path in ("baton_p2_to_p3.txt", "baton_p1_to_p2.txt"):
        if os.path.exists(baton_path):
            with open(baton_path, "r", encoding="utf-8") as f:
                baton = f.read()
            vid_m = re.search(r'<video_id>\s*([\d+]+)\s*</video_id>', baton)
            if not vid_m:
                vid_m = re.search(r'<video_number>\s*([\d+]+)\s*</video_number>', baton)
            if vid_m:
                # Combined transcript "120+121" → canonical "121" (last token).
                _parts = [p for p in vid_m.group(1).split("+") if p.isdigit()]
                if _parts:
                    video_id = _parts[-1]
                    break

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Map forensic log glob patterns to phase labels
    log_patterns = [
        ("forensic_raw_p1*.txt",              "P1"),
        ("forensic_raw_p2*.txt",              "P2"),
        ("forensic_raw_p3_pass1_chunk*.txt",  "P3 Pass 1"),
        ("forensic_raw_p3_pass2.txt",         "P3 Pass 2"),
        ("forensic_raw_p4_pass*.txt",         "P4"),
        ("forensic_raw_p5_auditor.txt",       "P5 Pass 1 (Auditor)"),
        ("forensic_raw_p5_surgeon.txt",       "P5 Pass 2 (Surgeon)"),
        ("forensic_raw_p5.txt",               "P5 Pass 3 (Exporter)"),
    ]

    SKIP_VALUES = {"", "none", "none.", "n/a", "n/a."}
    harvested = []

    for pattern, phase_label in log_patterns:
        for filepath in sorted(glob.glob(pattern)):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                continue
            for m in re.finditer(r'<telemetry_log>\s*(.*?)\s*</telemetry_log>', content, re.DOTALL):
                feedback = m.group(1).strip()
                if feedback.lower() in SKIP_VALUES:
                    continue
                # Refine phase label with chunk / pass number from filename
                specific_phase = phase_label
                chunk_m = re.search(r'chunk(\d+)', filepath)
                pass_m  = re.search(r'pass(\d+)',  filepath)
                if chunk_m and pass_m:
                    specific_phase = f"{phase_label} Pass {pass_m.group(1)} Chunk {chunk_m.group(1)}"
                elif chunk_m:
                    specific_phase = f"{phase_label} Chunk {chunk_m.group(1)}"
                elif pass_m and "p4" in filepath:
                    specific_phase = f"{phase_label} Pass {pass_m.group(1)}"
                entry = f"[{timestamp} | Video {video_id} | {specific_phase}] {feedback}"
                harvested.append(entry)

    if harvested:
        with open("prompt_telemetry_database.txt", "a", encoding="utf-8") as f:
            for entry in harvested:
                f.write(entry + "\n")
        print(f" [+] Telemetry harvest: {len(harvested)} entries appended to prompt_telemetry_database.txt")
    else:
        print(" [+] Telemetry harvest: zero feedback entries (all runs reported None or empty).")

def extract_zone_from_block(block):
    """Extracts zone provenance from the Meta field of a YAML block."""
    meta_match = re.search(r'Meta:\s*"?([^"\n]+)"?', block)
    if meta_match:
        zone_match = re.search(r'zone=(GREEN|BLUE|YELLOW)', meta_match.group(1))
        if zone_match:
            return zone_match.group(1)
    return 'BLUE'

def extract_concept_from_block(block):
    """Extracts Target_Concept segment from Meta field."""
    meta_match = re.search(r'Meta:\s*"?([^"\n]+)"?', block)
    if meta_match:
        segments = meta_match.group(1).split('|')
        if len(segments) >= 2:
            return segments[1].strip()
    return '???'

def extract_origin_from_block(block):
    """Extracts the Origin provenance string from a YAML block."""
    match = re.search(r'Origin:\s*"?([^"\n]+)"?', block)
    return match.group(1).strip() if match else ''

def extract_front_preview(block, max_len=9999):
    """Extracts a short front-text preview from a YAML block."""
    match = re.search(
        r"Front:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
        block, re.DOTALL)
    if match:
        text = match.group(1).strip()
        return text[:max_len] + '…' if len(text) > max_len else text
    return '???'

def speed_mode_terminal(blue_blocks, surviving_blocks_map):
    """
    Terminal bulk-reject interface for BLUE cards in P5 Speed Mode.
    Groups remaining BLUE cards by type bucket, shows numbered list
    with front preview and reason one-liner. User types numbers to
    reject. All others are auto-accepted.
    """
    type_display = {
        'DEBT':        '🟦 Missing Exam Fact',
        'BRIDGE':      '🌉 Terminology Bridge',
        'SUGGESTION':  '💡 Unclaimed Gold',
        'HANDS_ON':    '⌨️  CLI / Shortcut',
        'SILENT_INTRO':'🟨 Deferred Topic',
        'CORRECTION':  '⚠️  Lecturer Error Fix',
    }

    buckets = {}
    card_registry = {}
    global_num = 1

    for orig_idx, block in blue_blocks:
        if orig_idx in surviving_blocks_map:
            continue
        origin = extract_origin_from_block(block)
        type_key = 'UNKNOWN'
        reason_text = ''
        if '/' in origin and '|' in origin:
            zone_type = origin.split('|')[0].strip()
            type_key = (zone_type.split('/')[1] if '/' in zone_type else 'UNKNOWN')
            reason_text = origin.split('|', 1)[1].strip()
        t_match_tag = re.search(r"T\d+", origin)
        tag = f"[{t_match_tag.group()}]" if t_match_tag else "[INJECTED]"
        back_match = re.search(r"Back:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))", block, re.DOTALL)
        back_text = back_match.group(1).strip() if back_match else "N/A"
        label = type_display.get(type_key, f'🔷 {type_key}')
        if label not in buckets:
            buckets[label] = []
        buckets[label].append((global_num, orig_idx, block, reason_text, tag, back_text))
        card_registry[global_num] = (orig_idx, block)
        global_num += 1

    if not card_registry:
        print(" [+] No remaining BLUE cards to review.")
        return surviving_blocks_map

    try:
        config.clear_screen()
    except Exception:
        pass

    print("=" * 60)
    print(" 🟦 AUDIT INJECTIONS — Type numbers to REJECT".center(60))
    print(" Default: KEEP ALL. ENTER accepts everything remaining.".center(60))
    print("=" * 60)

    for label, cards in buckets.items():
        print(f"\n  ── {label} ──")
        for num, orig_idx, block, reason, tag, back_text in cards:
            front = extract_front_preview(block)
            print(f"  [{num:2d}] {tag} ➔ {front}")
            print(f"       └─ Answer: {back_text}")
            if reason:
                print(f"       └─ Logic: {reason}")

    print("\n" + "=" * 60)
    raw = input(
        " [?] Reject numbers (e.g. 2,5,7), 'R' to Review Individually, or ENTER to keep all >> ").strip()

    if raw.strip().lower() in ('a', 'r'):
        return "SWITCH_TO_ANKI"

    try:
        reject_set = set(
            int(x.strip()) for x in raw.split(',') if x.strip().isdigit())
    except ValueError:
        reject_set = set()

    kept = 0
    rejected = 0
    for num, (orig_idx, block) in card_registry.items():
        if num not in reject_set:
            surviving_blocks_map[orig_idx] = block
            kept += 1
        else:
            rejected += 1

    print(f"\n [+] Speed Mode complete: {kept} kept, {rejected} rejected.")
    return surviving_blocks_map

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

def merge_surgeon_patch(base_yaml, patch_raw):
    # Step 1 — Extract patch content from POLISHED YAML PAYLOAD section
    polished_match = re.search(r"### 💎 POLISHED YAML PAYLOAD(.*?)(?:\[EOF|$)", patch_raw, re.DOTALL)
    patch_content = polished_match.group(1).strip() if polished_match else patch_raw.strip()
    patch_content = patch_content.replace("```yaml", "").replace("```text", "").replace("```", "").strip()
    patch_segments = [s.strip() for s in re.split(r'(?m)^---\s*$', patch_content) if s.strip()]

    # Step 2 — Empty patch guard
    if not any(re.search(r'(?m)^ID:\s*\d+', seg) for seg in patch_segments):
        print("[P5 MERGE: ZERO PATCHES — BASE RETURNED UNCHANGED]")
        return base_yaml

    # Step 3 — Parse base_yaml into ordered dict
    base_dict = {}
    order = []
    for seg in re.split(r'(?m)^---\s*$', base_yaml):
        seg = seg.strip()
        if not seg:
            continue
        m = re.search(r'(?m)^ID:\s*(\d+)', seg)
        if m:
            card_id = int(m.group(1))
            base_dict[card_id] = seg
            order.append(card_id)

    # Step 4 — Apply patch segments
    modified_count = 0
    injected_count = 0
    for segment in patch_segments:
        # a. Extract ID
        id_match = re.search(r'(?m)^ID:\s*(\d+)', segment)
        if not id_match:
            print("[P5 WARNING: Unparseable segment — skipped]")
            continue
        card_id = int(id_match.group(1))

        # b. ID exists in base → MODIFY
        if card_id in base_dict:
            base_dict[card_id] = segment
            print(f"[P5 MODIFY] ID {card_id}")
            modified_count += 1
        else:
            # c. ID not in base → COMPLETENESS CHECK
            found_fields = re.findall(
                r'(?m)^(ID|Front|Back|Extra|Tags|Meta|Origin|Rev_Front|Rev_Back):', segment)
            found_count = len(set(found_fields))
            if found_count == 9:
                base_dict[card_id] = segment
                order.append(card_id)
                print(f"[P5 INJECT] ID {card_id} — new card (Surgeon mandate: BRIDGE INJECTION or equivalent)")
                injected_count += 1
            else:
                print(f"[P5 WARNING: Partial segment for unknown ID {card_id} — skipped (expected 9 fields, found {found_count})]")

    # Step 5 — Reconstruct in insertion order
    result = "\n---\n".join(base_dict[cid] for cid in order)
    if result and not result.startswith("---"):
        result = "---\n" + result

    # Step 6 — Log summary
    original_count = len(order) - injected_count
    unchanged_count = original_count - modified_count
    print(f"[P5 MERGE COMPLETE] {modified_count} cards modified, {injected_count} cards injected, {unchanged_count} cards unchanged.")

    return result

def run_phase5():
    print(" [!] PHASE 5 SPECIALIST: THE EXPORTER (v4.0 - CINEMATIC)")
    print("-" * 50)

    # 1. READ INPUTS
    if not os.path.exists(_P + "final_anki_cards_with_reverse.txt"):
        print(f" [X] Error: '{_P}final_anki_cards_with_reverse.txt' missing! Run upstream phase first.")
        sys.exit(1)

    with open(_P + "final_anki_cards_with_reverse.txt", "r", encoding="utf-8") as f:
        yaml_payload = f.read()

    if not os.path.exists("Prompts/prompt5_exporter.txt"):
        print(" [X] Error: 'Prompts/prompt5_exporter.txt' missing from folder!")
        sys.exit(1)

    with open("Prompts/prompt5_exporter.txt", "r", encoding="utf-8") as f:
        p5_base_text = f.read()

    # Define exact string to replace (v4.0 Synchronized)
    target_payload_placeholder = "[👉PASTE YAML PAYLOAD HERE👈]"
    target_audit_placeholder = "[👉LEAVE EMPTY FOR MODE 1 OR MODE 3. PASTE THE SENTINEL REPORT HERE FOR MODE 2👈]"

    # ==========================================
    # PASS 1: THE AUDITOR (SENTINEL LOOP)
    # ==========================================
    print(f" [>] PASS 1: Executing Sentinel Audit...")

    p5_prompt_pass1 = p5_base_text.replace(target_payload_placeholder, yaml_payload)\
                                  .replace(target_audit_placeholder, "")

    audit_output = config.call_llm(p5_prompt_pass1, context_header="PHASE 5 | PASS 1 (AUDITOR)", phase="P5", pass_num=1)
    if not audit_output:
        sys.exit(1)

    # Raw forensic save (preserves telemetry placed after the audit terminator)
    with open(_P + "forensic_raw_p5_auditor.txt", "w", encoding="utf-8") as f:
        f.write(f"### FORENSIC LOG: P5 AUDITOR | MODEL: {getattr(config, 'LAST_ACTIVE_MODEL', 'unknown')}\n" + "="*60 + "\n" + audit_output)

    # Regex extract Sentinel Report (Fix: Capture from start of output to termination string)
    sentinel_match = re.search(r"(.*?### 📊 SENTINEL AUDIT REPORT COMPLETE)", audit_output, re.DOTALL)
    sentinel_report = sentinel_match.group(1).strip() if sentinel_match else audit_output.strip()

    with open(_P + "sentinel_report.txt", "w", encoding="utf-8") as f:
        f.write(sentinel_report)

    polished_yaml_base = yaml_payload

    # NOTE: Mode 0 (Combined Audit+Surgery) is not currently
    # invoked by this script. If Mode 0 is wired up in a
    # future version, it outputs a full YAML and should bypass
    # merge_surgeon_patch() entirely — use its raw output as
    # polished_yaml directly, skipping Steps 10-13 above.
    # Do not add dead code for this path until Mode 0 is
    # actually triggered here.

    # ==========================================
    # PASS 2: THE SURGEON (YAML POLISHER)
    # ==========================================
    print(f" [>] PASS 2: Executing Surgeon Reconstruction...")

    p5_prompt_pass2 = p5_base_text.replace(target_payload_placeholder, yaml_payload)\
                                  .replace(target_audit_placeholder, sentinel_report)

    surgeon_output = config.call_llm(p5_prompt_pass2, context_header="PHASE 5 | PASS 2 (SURGEON)", phase="P5", pass_num=2)
    if not surgeon_output:
        sys.exit(1)

    with open(_P + "forensic_raw_p5_surgeon.txt", "w", encoding="utf-8") as f:
        f.write(f"### FORENSIC LOG: SURGEON | MODEL: {getattr(config, 'LAST_ACTIVE_MODEL', 'unknown')}\n" + "="*60 + "\n" + surgeon_output)

    # Regex extract Polished YAML (fallback to full output)
    # Anchored to the exact emoji header to prevent preamble bleed from chain-of-thought prose.
    polished_match = re.search(r"### 💎 POLISHED YAML PAYLOAD(.*?)(?:\[EOF|$)", surgeon_output, re.DOTALL)
    polished_yaml = polished_match.group(1).strip() if polished_match else surgeon_output.strip()

    # THE PERMANENT FIX: Strip markdown wrappers before they hit the Veto Gate
    polished_yaml = polished_yaml.replace("```yaml", "").replace("```", "").strip()

    with open(_P + "polished_yaml.txt", "w", encoding="utf-8") as f:
        f.write(polished_yaml)

    merged_yaml = merge_surgeon_patch(polished_yaml_base, surgeon_output)

    with open(_P + "forensic_merged_p5.txt", "w", encoding="utf-8") as f:
        f.write("### MERGED STATE: POST-SURGEON\n" + "="*60 + "\n" + merged_yaml)

    with open(_P + "polished_yaml.txt", "w", encoding="utf-8") as f:
        f.write(merged_yaml)

    polished_yaml = merged_yaml

    # ==========================================
    # PASS 2.5: THE ANKI SIMULATOR UI (VETO GATE)
    # ==========================================
    # High-Visibility Audio Alert (Veto Gate Entry Chime)
    try:
        if platform.system() == "Windows":
            import winsound
            # High-frequency triple chime for attention
            for freq in [880, 1046, 1318]:
                winsound.Beep(freq, 150)
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
        else:
            # System Bell Fallback
            print("\a\a\a")
    except Exception:
        pass
    print(" [!] VETO GATE OPEN: Manual Curation Required.")

    blocks = [b.strip() for b in re.split(r"(?m)^---(?:\s*\n)?", polished_yaml) if b.strip()]

    # --- GREEN / BLUE SEPARATION ---
    green_blocks = [(i, b) for i, b in enumerate(blocks) if extract_zone_from_block(b) == 'GREEN']
    blue_blocks  = [(i, b) for i, b in enumerate(blocks) if extract_zone_from_block(b) != 'GREEN']

    surviving_blocks_map = {}
    parse_error_count = 0
    accept_all = False

    # --- GREEN BLOCK BULK GATE ---
    if green_blocks:
        if config.veto_gate_needs_notification(5):
            config.send_ntfy(
                title="✅ P5 Veto Gate Ready",
                message=f"{len(green_blocks)} GREEN + {len(blue_blocks)} BLUE cards awaiting curation. Switch to your terminal.",
            )
        try:
            config.clear_screen()
        except Exception:
            pass
        print("=" * 60)
        print(" 🟩 GREEN TRIGGERS — YOUR EXPLICIT REQUESTS".center(60, "#"))
        print(f" Reviewing {len(green_blocks)} card(s) individually (Anki mode)".center(60))
        print(" Press 'A' on any card to bulk-accept the rest".center(60))
        print("=" * 60)
        # Anki mode is the default entry point. The bulk-listing preview and
        # the green_choice input prompt are intentionally bypassed; individual
        # review begins immediately. The 'A' keybind inside the review loop
        # preserves bulk-accept access. The `else:` branch below (bulk rejection
        # by numbers) becomes dead code, preserved for a one-line rollback.
        green_choice = 'r'  # was: input(...) — bulk-list entry intentionally skipped
        if green_choice == 'r':
            green_accept_all = False
            for g_idx, (orig_idx, block) in enumerate(green_blocks):
                if green_accept_all:
                    surviving_blocks_map[orig_idx] = block
                    continue
                try:
                    config.clear_screen()
                except Exception:
                    pass
                front_match = re.search(
                    r"Front:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                    block, re.DOTALL)
                back_match = re.search(
                    r"Back:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                    block, re.DOTALL)
                front_text = (front_match.group(1).strip() if front_match else "PARSE ERROR")
                back_text  = (back_match.group(1).strip()  if back_match  else "PARSE ERROR")
                progress_str = (f"[GREEN {g_idx+1}/{len(green_blocks)}] 🟩 USER TRIGGER")
                speech_str_s1 = build_speech_p5(front_text)
                speaker.play(speech_str_s1)
                speaker.prefetch(clean_text(back_text))
                for _delta in range(1, 4):
                    if g_idx + _delta < len(green_blocks):
                        _, _nb = green_blocks[g_idx + _delta]
                        _nfm = re.search(
                            r"Front:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                            _nb, re.DOTALL)
                        _nbm = re.search(
                            r"Back:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                            _nb, re.DOTALL)
                        if _nfm:
                            _nft = _nfm.group(1).strip()
                            speaker.prefetch(build_speech_p5(_nft))
                            if _nbm:
                                speaker.prefetch(clean_text(_nbm.group(1).strip()))
                print_centered_vertical(front_text, progress_str=progress_str)
                while True:
                    choice = input(
                        " [?] (ENTER: Reveal | R: Reject | A: Accept All | P: Replay) >> ").strip().lower()
                    if choice == 'p':
                        speaker.stop(); speaker.play(speech_str_s1); continue
                    speaker.stop()
                    break
                if choice == 'r':
                    continue
                elif choice == 'a':
                    surviving_blocks_map[orig_idx] = block
                    green_accept_all = True
                    continue
                try:
                    config.clear_screen()
                except Exception:
                    pass
                speech_str_s2 = clean_text(back_text)
                speaker.play(speech_str_s2)
                print_centered_vertical(front_text, back_text=back_text, progress_str=progress_str)
                while True:
                    choice2 = input(
                        " [?] (ENTER: Keep | R: Reject | A: Accept All | P: Replay) >> ").strip().lower()
                    if choice2 == 'p':
                        speaker.stop(); speaker.play(speech_str_s2); continue
                    speaker.stop()
                    break
                if choice2 == 'r':
                    continue
                elif choice2 == 'a':
                    surviving_blocks_map[orig_idx] = block
                    green_accept_all = True
                else:
                    surviving_blocks_map[orig_idx] = block

        else:
            try:
                green_reject_set = set(
                    int(x.strip()) for x in green_choice.split(',')
                    if x.strip().isdigit()
                )
            except ValueError:
                green_reject_set = set()

            kept_green = 0
            rejected_green = 0
            for i, (orig_idx, block) in enumerate(green_blocks, 1):
                if i not in green_reject_set:
                    surviving_blocks_map[orig_idx] = block
                    kept_green += 1
                else:
                    rejected_green += 1

            print(f" [+] {kept_green} GREEN trigger(s) accepted, "
                  f"{rejected_green} rejected.")

    # ── MODE SELECTION: Anki mode is the default entry point ──
    # The bulk-list interface (speed_mode_terminal) is intentionally bypassed.
    # Speed mode remains reachable mid-review via the 'S' key (see line ~679).
    # The dead branch below is preserved for a one-line rollback if needed.
    total_blue_remaining = sum(
        1 for orig_idx, block in blue_blocks
        if orig_idx not in surviving_blocks_map
    )
    surviving_blocks = []
    if total_blue_remaining > 0:
        try:
            config.clear_screen()
        except Exception:
            pass
        _speed_result = "SWITCH_TO_ANKI"  # Anki mode default; was: speed_mode_terminal(blue_blocks, surviving_blocks_map)
        if _speed_result != "SWITCH_TO_ANKI":
            surviving_blocks_map = _speed_result  # dead branch (kept for rollback)
        else:
            # --- BLUE BLOCK INDIVIDUAL REVIEW ---
            total_blue = len(blue_blocks)
            for b_idx, (orig_idx, block) in enumerate(blue_blocks):
                if orig_idx in surviving_blocks_map:
                    continue
                if accept_all:
                    surviving_blocks_map[orig_idx] = block
                    continue

                front_match = re.search(
                    r"Front:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                    block, re.DOTALL)
                back_match = re.search(
                    r"Back:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                    block, re.DOTALL)

                front_text = (front_match.group(1).strip() if front_match else "FRONT PARSE ERROR")
                back_text  = (back_match.group(1).strip()  if back_match  else "BACK PARSE ERROR")

                if (front_text == "FRONT PARSE ERROR" or back_text == "BACK PARSE ERROR"):
                    parse_error_count += 1

                try:
                    config.clear_screen()
                except Exception:
                    pass

                _origin_tag = extract_origin_from_block(block)
                _t_match = re.search(r"T\d+", _origin_tag)
                tag = f"[{_t_match.group()}]" if _t_match else "[INJECTED]"
                progress_str = (
                    f"[{'█' * (b_idx+1)}{'░' * (total_blue - b_idx - 1)}]"
                    f" {b_idx+1}/{total_blue} 🟦 AUDIT {tag}")
                speech_str_s1 = build_speech_p5(front_text)
                speaker.play(speech_str_s1)
                speaker.prefetch(clean_text(back_text))
                _b_next = b_idx + 1
                _b_prefetch_count = 0
                while _b_next < len(blue_blocks) and _b_prefetch_count < 3:
                    _n_oi, _n_bl = blue_blocks[_b_next]
                    if _n_oi not in surviving_blocks_map:
                        _nfm = re.search(
                            r"Front:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                            _n_bl, re.DOTALL)
                        _nbm = re.search(
                            r"Back:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                            _n_bl, re.DOTALL)
                        if _nfm:
                            _nft = _nfm.group(1).strip()
                            speaker.prefetch(build_speech_p5(_nft))
                            if _nbm:
                                speaker.prefetch(clean_text(_nbm.group(1).strip()))
                        _b_prefetch_count += 1
                    _b_next += 1
                print_centered_vertical(front_text, progress_str=progress_str)

                while True:
                    choice = input(
                        " [?] (ENTER: Reveal | R: Reject Blindly | A: Accept All | S: Speed Mode | P: Replay) >> ").strip().lower()
                    if choice == 'p':
                        speaker.stop(); speaker.play(speech_str_s1); continue
                    speaker.stop()
                    break

                if choice == 'r':
                    continue
                elif choice == 'a':
                    surviving_blocks_map[orig_idx] = block
                    accept_all = True
                    continue
                elif choice == 's':
                    _pivot_result = speed_mode_terminal(blue_blocks, surviving_blocks_map)
                    if _pivot_result == "SWITCH_TO_ANKI":
                        for _oi, _bl in blue_blocks:
                            if _oi not in surviving_blocks_map:
                                surviving_blocks_map[_oi] = _bl
                    else:
                        surviving_blocks_map = _pivot_result
                    break

                try:
                    config.clear_screen()
                except Exception:
                    pass

                speech_str_s2 = clean_text(back_text)
                speaker.play(speech_str_s2)
                print_centered_vertical(front_text, back_text=back_text, progress_str=progress_str)

                while True:
                    choice2 = input(
                        " [?] (ENTER: Keep & Next | R: Reject | A: Accept All Remaining | S: Speed Mode | P: Replay) >> ").strip().lower()
                    if choice2 == 'p':
                        speaker.stop(); speaker.play(speech_str_s2); continue
                    speaker.stop()
                    break

                if choice2 == 'r':
                    continue
                elif choice2 == 'a':
                    surviving_blocks_map[orig_idx] = block
                    accept_all = True
                elif choice2 == 's':
                    _pivot_result = speed_mode_terminal(blue_blocks, surviving_blocks_map)
                    if _pivot_result == "SWITCH_TO_ANKI":
                        for _oi, _bl in blue_blocks:
                            if _oi not in surviving_blocks_map:
                                surviving_blocks_map[_oi] = _bl
                    else:
                        surviving_blocks_map = _pivot_result
                    break
                else:
                    surviving_blocks_map[orig_idx] = block

    # RECONSTRUCTION: always runs, regardless of path taken above
    surviving_blocks = [
        surviving_blocks_map[i]
        for i in sorted(surviving_blocks_map.keys())
    ]

    if parse_error_count > 0:
        print(f" [!] WARNING: {parse_error_count} card(s) had YAML parse errors during curation. Schema may be drifting.")

    # Reassemble and save curated YAML
    curated_yaml = "\n---\n".join(surviving_blocks)
    # ORIGIN STRIP: Remove Origin provenance fields before file write
    curated_yaml = re.sub(r'(?m)^Origin:.*$\n?', '', curated_yaml)
    if curated_yaml and not curated_yaml.startswith("---"):
        curated_yaml = "---\n" + curated_yaml
    elif not curated_yaml:
        curated_yaml = ""  # keep empty if nothing survived

    with open(_P + "curated_polished_yaml.txt", "w", encoding="utf-8") as f:
        f.write(curated_yaml)

    # ==========================================
    # EARLY CASTING DIRECTOR GATE (Decision 1)
    # ==========================================
    # Decision 1 (A/L/S) moved here from the late phase so the user can
    # decide while still at the keyboard, then walk away during Pass 3.
    # On [L]: library browser also fires now -- no late interrupt at all.
    # On [A]: 2 LLM calls + Decision 2 (1/2/M) stay at the late phase.
    # On [S]: nothing fires later.
    _cd_gate = None
    _cd_chosen = None
    _cd_chosen_key = None
    _cd_beta = None
    _cd_PAIRINGS = None
    _cd_unavailable = False
    if UNIT_SWEEP_MODE:
        _cd_unavailable = True  # Unit sweeps skip the Casting Director entirely.
    try:
        if UNIT_SWEEP_MODE:
            raise KeyboardInterrupt
        print("\n" + "="*64)
        print("  CASTING DIRECTOR".center(64))
        print("="*64)
        print("   [A] Auto    -- AI picks best + generates new  (2 calls)")
        print("   [L] Library -- Browse library, no API calls   (0 calls)")
        print("   [S] Skip    -- No persona this run            (0 calls)")
        while True:
            _cd_gate = input(" Choice (A / L / S): ").strip().upper()
            if _cd_gate in ("A", "L", "S"):
                break
            print(" [!] Enter A, L, or S.")

        if _cd_gate == "S":
            print(" [>] Casting Director skipped.")
        else:
            if not os.path.exists("NotebookLM_Prompt_BETA.txt"):
                print(" [!] NotebookLM_Prompt_BETA.txt missing -- skipping Casting Director.")
                _cd_unavailable = True
            else:
                try:
                    from pairings import PAIRINGS as _cd_PAIRINGS_imp, FLAVOR_SEEDS, DIALECTS
                    _cd_PAIRINGS = _cd_PAIRINGS_imp
                except (SyntaxError, ImportError) as _cd_e:
                    print(f" [!] Could not import pairings.py ({_cd_e}) -- skipping Casting Director.")
                    _cd_unavailable = True
                else:
                    with open("NotebookLM_Prompt_BETA.txt", "r", encoding="utf-8") as _cdf:
                        _cd_beta = _cdf.read()

                    # [L] path: fire library browser inline now so user can walk away
                    if _cd_gate == "L":
                        try:
                            with open("pairings_generated.json", "r", encoding="utf-8") as _gf:
                                _cd_gen_lib = json.load(_gf)
                        except FileNotFoundError:
                            _cd_gen_lib = {}
                        except (json.JSONDecodeError, ValueError):
                            print(" [!] WARNING: pairings_generated.json corrupted -- treating as empty.")
                            _cd_gen_lib = {}
                        _cd_all = list(_cd_PAIRINGS.items()) + [(k, v) for k, v in _cd_gen_lib.items()]
                        _cd_n = len(_cd_all)
                        print("\n-- FULL LIBRARY " + "-"*48)
                        for _cd_i, (_cd_k, _cd_p) in enumerate(_cd_all, 1):
                            _cd_star = " *" if _cd_k in _cd_gen_lib else ""
                            print(f"  [{_cd_i:2d}]  {_cd_k:<30}{_cd_star} -- {_cd_p['TONE_FRAME']}")
                        print("-"*64)
                        while True:
                            try:
                                _cd_num = int(input(" Pick number: ").strip())
                                if 1 <= _cd_num <= _cd_n:
                                    break
                                print(f" [!] Enter a number between 1 and {_cd_n}.")
                            except ValueError:
                                print(f" [!] Enter a number between 1 and {_cd_n}.")
                        _cd_chosen_key, _cd_chosen = _cd_all[_cd_num - 1]
                    # [A] path: defer to late phase (after cleaned_transcript is computed)
    except KeyboardInterrupt:
        print("\n [!] Casting Director skipped.")
        _cd_unavailable = True

    # ==========================================
    # PASS 3: THE EXPORTER (PIPE-DELIMITED COMPILER)
    # ==========================================
    print(f"\n [>] PASS 3: Formatting for Anki Import...")

    # We now inject the CURATED yaml into the Exporter prompt
    p5_prompt_pass3 = p5_base_text.replace(target_payload_placeholder, "### 💎 POLISHED YAML PAYLOAD\n\n" + curated_yaml)\
                                  .replace(target_audit_placeholder, "[MODE 3 - EXPORT ONLY]")

    final_output = config.call_llm(p5_prompt_pass3, context_header="PHASE 5 | PASS 3 (EXPORTER)", phase="P5", pass_num=3)
    if not final_output:
        sys.exit(1)

    # Save Forensic Log (Contains all the batching headers and AI status text)
    with open(_P + "forensic_raw_p5.txt", "w", encoding="utf-8") as f:
        f.write(f"### FORENSIC LOG: EXPORTER | MODEL: {getattr(config, 'LAST_ACTIVE_MODEL', 'unknown')}\n" + "="*60 + "\n" + final_output)

    # ==========================================
    # FINAL EXTRACTION (THE BATCH CONCATENATOR)
    # ==========================================
    print(f" [>] Siphoning and Cleaning Batches...")

    # THE MASTER SIPHON (v3.1 Standard)
    # Find ALL <final_import_stream> tags (in case the LLM splits them per batch)
    master_matches = re.findall(r"<final_import_stream>(.*?)</final_import_stream>", final_output, re.DOTALL)

    if master_matches:
        # Join all captured stream zones together into one massive data block
        data_zone = "\n".join(master_matches)
    else:
        print(" [!] WARNING: <final_import_stream> tag not found. Falling back to fuzzy capture.")
        data_zone = final_output

    # Extract ALL code blocks (the batches) from the isolated data zone
    # This captures content inside triple backticks and optionally ignores a language tag after the opening ```
    matches = re.findall(r"```(?:[^\n]*\n)?(.*?)```", data_zone, re.DOTALL)

    if matches:
        # Join all extracted batch blocks into one continuous text body (trim each block)
        export_text = "\n".join(m.strip() for m in matches if m.strip())
    else:
        # Fallback if the LLM forgot code blocks entirely
        export_text = final_output.strip()

    # The Cleanser: Remove the checksum column so Anki gets exactly 8 columns
    export_text = export_text.replace("|[8_COLS_VERIFIED]", "")

    # SANITIZATION: Final security sweep for EOF markers and backticks
    export_text = re.sub(r"\[EOF.*?\]", "", export_text, flags=re.IGNORECASE)
    export_text = export_text.replace("```", "").replace("`", "").strip()

    # TELEGRAPHIC HTML CONVERSION: Convert LLM Markdown (**) to Anki HTML (<b>)
    # Bold spans are intra-line only; DOTALL is excluded to prevent cross-card corruption.
    export_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', export_text)

    # ORIGIN STRIP (belt-and-suspenders): Catch any Origin lines in export stream
    export_text = re.sub(r'(?m)^Origin:.*$\n?', '', export_text)

    # FILTER: Only harvest rows starting with "Basic+" to ignore LLM headers/metadata
    # This ensures #separator and BATCH headers don't end up in Anki.
    total_candidate_rows = sum(1 for line in export_text.split('\n') if 'basic+' in line.lower())
    valid_rows = [line for line in export_text.split('\n') if line.strip().startswith('"Basic+"')]
    if len(valid_rows) != total_candidate_rows:
        print(f" [!] ⚠️  WARNING: {total_candidate_rows} row(s) contained 'Basic+' but only {len(valid_rows)} passed the format filter. {total_candidate_rows - len(valid_rows)} row(s) may have been dropped due to missing or malformed quote wrappers.")

    # Normalization pass: auto-inject missing opening quotes on Basic+ rows
    normalized_lines = []
    for line in export_text.split('\n'):
        stripped = line.strip()
        if stripped.lower().startswith('basic+') and not stripped.startswith('"Basic+"'):
            line = '"Basic+"' + stripped[len('Basic+'):]
        normalized_lines.append(line)
    export_text = '\n'.join(normalized_lines)

    valid_rows = [line for line in export_text.split('\n') if line.strip().startswith('"Basic+"')]

    # === SUPPORTIVE IMAGE MATCHING (Mode A) ===
    # Staple each loose image in IMG_SUPPORT_DIR onto the Back of every card whose
    # own Front+Back+tags text names it (ALL filename words present; s and ies->y
    # plural-tolerant). Row-native: the filename is the join key, matched against
    # the card's own words -- no cross-file join, no LLM. Runs BEFORE the TTS block
    # so the image lands before the appended [sound:] tag (text -> image -> audio).
    # SINGLE-quoted src (a raw " breaks the double-quoted pipe rectangle, same as
    # the acronym gloss below). Non-recursive scan (skips the identify\ subfolder).
    # Does NOT reuse normalize() -- it concatenates all words and would only match
    # directly-adjacent words. Skipped in sweeps.
    if not UNIT_SWEEP_MODE and ANKI_MEDIA_DIR and IMG_SUPPORT_DIR:
        _IMG_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")

        def _img_fold(w):
            if len(w) > 4 and w.endswith("ies"):
                return w[:-3] + "y"
            if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
                return w[:-1]
            return w

        def _img_words(text):
            return {_img_fold(w) for w in re.findall(r"[a-z0-9]+", clean_text(text).lower())}

        _support_imgs = [f for f in sorted(os.listdir(IMG_SUPPORT_DIR))
                         if f.lower().endswith(_IMG_EXTS)
                         and os.path.isfile(os.path.join(IMG_SUPPORT_DIR, f))]
        _img_parsed = [r.split('"|"') for r in valid_rows]
        _img_cardwords = [
            _img_words(f[2] + " " + f[3] + " " + f[7]) if len(f) >= 8 else set()
            for f in _img_parsed
        ]
        _img_staples = 0
        _img_unplaced = []
        for _imgfile in _support_imgs:
            try:
                _need = {_img_fold(w) for w in
                         re.findall(r"[a-z0-9]+", os.path.splitext(_imgfile)[0].lower())}
                if not _need:
                    continue
                _stored = None
                _hits = 0
                for _ri, _flds in enumerate(_img_parsed):
                    if len(_flds) < 8:
                        continue
                    if _need <= _img_cardwords[_ri]:
                        if _stored is None:
                            _stored = store_compressed_image(
                                os.path.join(IMG_SUPPORT_DIR, _imgfile), ANKI_MEDIA_DIR)
                            if _stored is None:
                                break
                        _flds[3] = _flds[3] + "<br><br><img src='" + _stored + "'>"
                        _hits += 1
                if _hits:
                    _img_staples += _hits
                else:
                    _img_unplaced.append(_imgfile)
            except Exception as _img_exc:
                print(" [!] Supportive image skipped (" + _imgfile + "): " + str(_img_exc))
        valid_rows = ['"|"'.join(f) for f in _img_parsed]
        print(" [+] Supportive images: " + str(_img_staples) + " staple(s) from "
              + str(len(_support_imgs)) + " image(s).")
        if _img_unplaced:
            print(" [!] couldn't place: " + ", ".join(_img_unplaced))

    # === ON-CARD TTS AUDIO (GRAFT 3) ===
    # Voice the question + one-line answer (forward Front/Back-L1 and reverse
    # Rev_Front/Rev_Back-L1) into collection.media and prepend [sound:] tags so
    # Anki plays them; the full Logic/Delta stays visible but silent (the
    # rendered file holds only Line-1 speech). Idempotent by content hash.
    if not UNIT_SWEEP_MODE and ANKI_MEDIA_DIR:
        try:
            import lameenc  # one-time probe; commit to one extension for the run
            _audio_ext = "mp3"
        except ImportError:
            _audio_ext = "wav"
            print(" [!] lameenc not installed — emitting WAV audio (larger files).")

        _emoji_re = re.compile(
            "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
            "\U00002300-\U000023FF\U00002B00-\U00002BFF\U0000FE0F\U0000200D]+")

        def _audio_text(field, line1_only):
            raw = field
            if line1_only:
                raw = re.split(r'<br\s*/?>', raw, maxsplit=1, flags=re.IGNORECASE)[0]
            return _emoji_re.sub("", clean_text(raw)).strip()

        _audio_count = 0
        _audio_rows = []
        for _row in valid_rows:
            _fields = _row.split('"|"')
            # Voiced fields: 2=Front, 3=Back, 5=Rev_Front, 6=Rev_Back (backs = line 1 only)
            for _idx, _line1 in ((2, False), (3, True), (5, False), (6, True)):
                if _idx >= len(_fields):
                    continue
                if _fields[_idx].strip().upper() == "N/A":
                    continue
                _spoken = _audio_text(_fields[_idx], _line1)
                if not _spoken:
                    continue
                try:
                    _fname = speaker.render_to_file(_spoken, ANKI_MEDIA_DIR, _audio_ext)
                except Exception as _exc:
                    print(f" [!] Audio skipped for one field ({_exc}).")
                    continue
                _fields[_idx] = _fields[_idx] + f"<br><br>[sound:{_fname}]"
                _audio_count += 1
            _audio_rows.append('"|"'.join(_fields))
        valid_rows = _audio_rows
        print(f" [+] On-card audio: {_audio_count} clip(s) embedded ({_audio_ext}).")

    # === ACRONYM GLOSS INJECTION (T26) ===
    # Every acronym the deck ships gets an inline click-to-expand gloss, so a card
    # can never fail on vocabulary instead of on knowledge. Universal sweep by
    # Chief-Architect ruling 2026-08-08: no curation list, no guessing what the
    # reader already knows. The regex only nets candidates; the model decides what
    # is actually an acronym (Constitution III-1 — semantic heuristic over a
    # brittle stop-list).
    #
    # POSITION IS LOAD-BEARING. This must stay AFTER the TTS block above and
    # BEFORE the header assembly below. clean_text() (tts_reader.py:254) strips
    # tags but KEEPS their inner text, so a gloss injected any earlier is read
    # aloud on every card.
    #
    # SINGLE-QUOTED ATTRIBUTES ONLY. The export is a double-quoted pipe rectangle
    # (prompt5_exporter.txt:244) — a raw " inside a field breaks the row. The
    # markup is otherwise byte-identical to the pattern proven live in the
    # collection via AnkiConnect, which is JSON and so uses double quotes.
    if not UNIT_SWEEP_MODE and valid_rows:
        _ACRO_FIELDS = (2, 3, 4, 5, 6)      # Front, Back, Extra, Rev_Front, Rev_Back
        _ACRO_SCOPES = ((2, 3, 4), (5, 6))  # deduped per SIDE, not per note: forward
                                            # and reverse are separate cards met weeks
                                            # apart, and neither can borrow the other's
                                            # gloss. Within a side, first occurrence
                                            # only; different acronyms each get one.
                                            # Across cards there is NO dedup — all ten
                                            # cards carrying MDM get their own gloss,
                                            # because which card comes up is unknowable.
                                            #
                                            # ⚠️ Extra (4) renders on the back of BOTH
                                            # cards but is ONE string, so it is swept
                                            # with the forward side ONLY. Listing it in
                                            # both scopes re-scans text the first pass
                                            # already wrapped — the acronym sits exposed
                                            # between <span class='an'> and its closing
                                            # tag, so the mask does not cover it — and
                                            # nests a second <label> inside the first.
                                            # Measured on the last export: 3 rows
                                            # corrupted. Do NOT "fix" this by adding 4
                                            # to the reverse scope.
        _acro_split = re.compile(r'(<[^>]*>|\[sound:[^\]]*\])')
        _acro_word = re.compile(r'\b[A-Z][A-Z0-9]{2,}\b')
        _acro_expansion_card = re.compile(r'\(\s*(?:Acronym\s+)?Expansion\s*\)', re.IGNORECASE)
        _acro_count = [0]

        def _acro_plain(field):
            """Field text with HTML tags and [sound:] tokens removed."""
            return "".join(_acro_split.split(field)[::2])

        def _acro_skip_row(fields):
            """An expansion card IS the vocabulary test — glossing it prints the
            answer on the front. P2 is scheduled to stop emitting these but has
            not yet, so this guard is live, not defensive decoration."""
            return len(fields) > 2 and bool(_acro_expansion_card.search(_acro_plain(fields[2])))

        def _acro_clean_exp(value):
            """Strip anything that could breach the pipe rectangle or the markup."""
            value = re.sub(r'[<>"|]', '', value)
            value = " ".join(value.split()).strip("() ")
            return value if 3 <= len(value) <= 80 else ""

        def _acro_parse(raw, keys):
            """Copied from the Casting Director's _cd_parse (:1452), with empty
            string values permitted — an empty expansion is the model's way of
            saying 'not an acronym', which is a valid answer here."""
            if not raw:
                return {}
            cleaned = re.sub(r'^```[a-zA-Z]*\n?', '', raw.strip()).rstrip('`').strip()
            try:
                data = json.loads(cleaned)
            except json.JSONDecodeError:
                m = re.search(r'\{.*\}', cleaned, re.DOTALL)
                if not m:
                    return {}
                try:
                    data = json.loads(m.group())
                except json.JSONDecodeError:
                    return {}
            if not isinstance(data, dict):
                return {}
            out = {}
            for k in keys:
                v = data.get(k)
                if isinstance(v, str):
                    v = _acro_clean_exp(v)
                    if v:
                        out[k] = v
            return out

        def _acro_wrap(acronym, seen, mapping):
            expansion = mapping.get(acronym, "")
            if not expansion or acronym in seen:
                return acronym
            seen.add(acronym)
            _acro_count[0] += 1
            return ("<label class='acro'><input type='checkbox' class='ax'>"
                    "<span class='an'>" + acronym + "</span>"
                    "<span class='av'> (" + expansion + ")</span></label>")

        # -- 1. HUNT: net every all-caps run of 3+ in the glossed fields --
        _acro_cands = set()
        _acro_fronts = []
        for _row in valid_rows:
            _f = _row.split('"|"')
            if _acro_skip_row(_f):
                continue
            if len(_f) > 2:
                _acro_fronts.append(_acro_plain(_f[2]).strip())
            for _i in _ACRO_FIELDS:
                if _i < len(_f) and _f[_i].strip().upper() != "N/A":
                    _acro_cands.update(_acro_word.findall(_acro_plain(_f[_i])))

        # -- 2. DEFINE: one call resolves the whole candidate list --
        _acro_map = {}
        if _acro_cands:
            _acro_list = sorted(_acro_cands)
            _acro_prompt = (
                "You are expanding acronyms found in CompTIA A+ (IT support) flashcards.\n"
                "For each candidate string below, return its standard expansion in that domain.\n"
                "If a string is NOT an acronym or initialism -- an ordinary English word in "
                "capital letters, a section label, a heading -- return an empty string for it.\n"
                "Expand plainly and briefly: letters, spaces and hyphens only; no quotes, no "
                "angle brackets, no pipe characters, under 60 characters.\n"
                "Output ONLY valid JSON: one object mapping EVERY candidate to its expansion "
                "string. No markdown fences, no commentary.\n\n"
                "CANDIDATES:\n" + "\n".join(_acro_list) + "\n\n"
                "CARD FRONTS (context for disambiguation only -- do not expand these):\n"
                + "\n".join(_acro_fronts)[:6000]
            )
            for _acro_attempt in range(2):
                # A study aid must never be able to cost a run. This block sits
                # BEFORE the export write, so an exception escaping here discards
                # the whole deck AFTER the veto gate has already been worked. The
                # Casting Director's identical bare call (:1486) is NOT a precedent
                # for leaving this one unguarded — that block runs after the file
                # is already on disk, so its blast radius is a missing persona.
                try:
                    _acro_raw = config.call_llm(_acro_prompt,
                                                context_header="ACRONYM GLOSS | DEFINER")
                except Exception as _acro_exc:
                    print(f" [!] Acronym gloss: definer call failed ({_acro_exc}).")
                    _acro_raw = None
                _acro_map = _acro_parse(_acro_raw, _acro_list)
                if _acro_map:
                    break
            if not _acro_map:
                print(" [!] Acronym gloss: definer returned nothing — shipping deck unglossed.")

        # -- 3. STITCH: first occurrence per acronym per side, text nodes only --
        if _acro_map:
            _acro_rows = []
            for _row in valid_rows:
                _f = _row.split('"|"')
                if _acro_skip_row(_f):
                    _acro_rows.append(_row)
                    continue
                for _scope in _ACRO_SCOPES:
                    _seen = set()
                    for _i in _scope:
                        if _i >= len(_f) or _f[_i].strip().upper() == "N/A":
                            continue
                        _parts = _acro_split.split(_f[_i])
                        for _p in range(0, len(_parts), 2):
                            _parts[_p] = _acro_word.sub(
                                lambda m: _acro_wrap(m.group(0), _seen, _acro_map),
                                _parts[_p])
                        _f[_i] = "".join(_parts)
                _acro_rows.append('"|"'.join(_f))
            valid_rows = _acro_rows
            print(f" [+] Acronym gloss: {_acro_count[0]} expansion(s) injected "
                  f"from {len(_acro_map)} term(s).")

    # === IDENTIFY CARDS (Mode B) ===
    # Turn each image in IDENTIFY_DIR into a "name this component" card: image on
    # the Front, the prettified filename as the answer on the Back. Basic+, in the
    # CompTIA A+::Identify subdeck. Lands AFTER the audio and acronym blocks (so it
    # carries no [sound:] tag and no gloss) and AFTER Mode A (so it is never itself
    # image-matched), but BEFORE final_payload below or the cards never reach the
    # export. SINGLE-quoted src. Processed files move to identify\processed\.
    # Skipped in sweeps.
    if not UNIT_SWEEP_MODE and ANKI_MEDIA_DIR and IDENTIFY_DIR:
        _ID_EXTS = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")

        def _id_prettify(stem):
            # Preserve exactly what the Chief Architect types in the filename (ruling
            # 2026-08-29): no auto-casing, no separator munging -- name the file the way
            # you want the answer to read. Only whitespace runs are collapsed.
            return " ".join(stem.split())

        _id_imgs = [f for f in sorted(os.listdir(IDENTIFY_DIR))
                    if f.lower().endswith(_ID_EXTS)
                    and os.path.isfile(os.path.join(IDENTIFY_DIR, f))]
        _id_made = 0
        _id_done = []
        for _imgfile in _id_imgs:
            try:
                _stored = store_compressed_image(
                    os.path.join(IDENTIFY_DIR, _imgfile), ANKI_MEDIA_DIR)
                if _stored is None:
                    print(" [!] Identify image skipped (compress failed): " + _imgfile)
                    continue
                _answer = _id_prettify(os.path.splitext(_imgfile)[0]).replace('"', '').replace('|', '')
                # Rev_Front / Rev_Back left EMPTY (not "N/A"): a non-empty reverse field
                # makes Anki generate a spurious reverse card showing the literal text.
                # Empty suppresses the reverse card -- identify cards are one-directional.
                _row = ('"Basic+"|"CompTIA A+::Identify"|"<img src=\'' + _stored + '\'>"|"'
                        + _answer + '"|""|""|""|"manual::identify"')
                valid_rows.append(_row)
                _id_made += 1
                _id_done.append(_imgfile)
            except Exception as _id_exc:
                print(" [!] Identify image skipped (" + _imgfile + "): " + str(_id_exc))
        if _id_done:
            _id_proc = os.path.join(IDENTIFY_DIR, "processed")
            try:
                import shutil
                os.makedirs(_id_proc, exist_ok=True)
                for _f in _id_done:
                    _dest = os.path.join(_id_proc, _f)
                    if os.path.exists(_dest):
                        os.remove(_dest)
                    shutil.move(os.path.join(IDENTIFY_DIR, _f), _dest)
            except Exception as _mv_exc:
                print(" [!] Could not move processed identify files: " + str(_mv_exc))
        print(" [+] Identify cards: " + str(_id_made) + " created.")

    # RE-INJECT ANKI HEADERS: Explicitly define the environment at the top
    final_payload = [
        "#separator:Pipe",
        "#html:true",
        "#notetype column:1",
        "#deck column:2",
        "#tags column:8"
    ] + valid_rows

    with open(_P + "ANKI_IMPORT_READY.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final_payload))

    # ── UNIT SWEEP MODE EARLY RETURN ──────────────────────────
    # In sweep mode, this script's job ends at writing the pipe-delimited
    # ANKI_IMPORT_READY file. The orchestrator (run_master.py) handles the
    # archive + sentinel copy. All downstream sections are post-processing
    # for the main pipeline (NotebookLM Producer Brief, PRE_FLIGHT_QUESTIONS,
    # Late Casting Director, harvest_telemetry, state writers, Auto-Launch Bay)
    # and are skipped here.
    if UNIT_SWEEP_MODE:
        print("=" * 60)
        print(" [!] PHASE 5 (UNIT SWEEP): ANKI_IMPORT_READY emitted ".center(60, "#"))
        print("=" * 60)
        print(f" [+] Cards in sweep deck : {len(valid_rows)}")
        print(f" [+] File written         : {_P}ANKI_IMPORT_READY.txt")
        print("=" * 60)
        # AUTO-LAUNCH (sweep): open Anki so the top-up cards can be imported without
        # opening it by hand — mirrors the main pipeline's Auto-Launch Bay. NO NotebookLM
        # / Producer Brief for the sweep: these are disconnected, lecturer-missed top-up
        # facts with no single transcript to build a brief from; they belong in Anki
        # spaced-repetition, not a podcast.
        print(" [>] Launching Anki...")
        if config.ANKI_PATH is not None and os.path.exists(config.ANKI_PATH):
            try:
                subprocess.Popen([config.ANKI_PATH], shell=True)
                print(" [+] Anki launched.")
            except Exception as e:
                print(f" [!] Anki launch error: {e}")
        else:
            print(" [!] Anki not found at configured path — skipping launch.")
        return

    # The Hybrid Dictionaries — Single source of truth for NotebookLM host behavior
    DIRECTOR_CUES = {
        ("GREEN", "INTENT"): (
            "The student explicitly requested this card. "
            "FORENSIC CHECK — cross-reference the raw transcript: "
            "Did Mike explicitly teach the details in the CORE FACT above? "
            "(CRITICAL: The TEACHING NOTES contain advanced exam facts. Do not assume Mike "
            "said them unless you find them in the transcript.) "
            "THREE POSSIBLE STATES — choose one: "
            "(A) Mike taught it well: review it naturally, anchoring to "
            "how he explained it and any analogy or demo he used. "
            "(B) Mike touched it but skipped key specs or nuance: "
            "call it out directly — 'Mike mentioned this but glossed over "
            "[the specific missing detail]' — then fill the gap accurately. "
            "(C) Mike skipped it entirely despite the student asking: "
            "announce clearly that this concept was not covered in the video, "
            "then teach it from zero using the CORE FACT and TEACHING NOTES."
        ),
        ("BLUE", "DEBT"): (
            "This exam objective appears in the CompTIA spec. "
            "FORENSIC CHECK: Read the transcript. Did Mike actually skip this, or did he cover it? "
            "If he covered it, ignore the 'debt' label and review it naturally. "
            "If he truly skipped it, frame it as additional exam prep the video's runtime didn't reach — "
            "not as an error by Mike. Present it matter-of-factly as 'here is what the exam also expects.'"
        ),
        ("BLUE", "SUGGESTION"): (
            "The student missed this, but it is an important exam concept. "
            "FORENSIC CHECK — cross-reference the transcript: Did Mike explicitly teach this, "
            "or are these advanced exam facts? (CRITICAL: Do not assume Mike said advanced facts "
            "found in the TEACHING NOTES unless you see them in the transcript). "
            "If Mike taught it: anchor to his demo/analogy and gently remind the student they let it slip past. "
            "If Mike did NOT teach it: do not claim the student missed it; just introduce it as "
            "a vital piece of the puzzle."
        ),
        ("BLUE", "BRIDGE"): (
            "The lecturer described this concept using informal language "
            "without stating the standard exam term. "
            "Cross-reference the transcript: find Mike's exact informal "
            "phrasing and quote it directly. "
            "Then have one host use Mike's version while the other "
            "corrects it to the official CompTIA exam term. "
            "Frame it as: here is what Mike called it — here is what the "
            "industry and the exam actually call that."
        ),
        ("BLUE", "CORRECTION"): (
            "There is a terminology conflict or factual misconception to resolve here. "
            "FORENSIC CHECK — cross-reference the raw transcript: Did Mike actually use the "
            "incorrect term, or did the student misunderstand Mike's explanation? "
            "TWO POSSIBLE STATES — choose one: "
            "(A) Mike used the wrong term: quote him precisely, then deliver the correct "
            "CompTIA standard matter-of-factly (frame it as precision calibration, not an attack). "
            "(B) Mike was correct (or making a loose analogy), but the student's notes show confusion: "
            "Exonerate Mike. Point out exactly why the student got confused (e.g., 'Mike made an "
            "analogy here that is easy to misinterpret'), then clarify the strict exam boundary."
        ),
        ("BLUE", "HANDS_ON"): (
            "This is a practical CLI command or keyboard shortcut. "
            "Frame it as a hands-on technician skill — "
            "something a real tech executes in the field or on exam day. "
            "Make it feel executable, not theoretical. "
            "FORENSIC CHECK: If Mike demonstrated or mentioned this command in the transcript, "
            "reference that moment. If he didn't, do NOT claim he did."
        ),
        ("BLUE", "LADDER"): (
            "This term appeared in the video but was never formally defined there. "
            "Give a single plain-English definition — enough to close the "
            "vocabulary gap without over-explaining a concept covered more fully "
            "in another part of the course."
        ),
        ("YELLOW", "SILENT_INTRO"): (
            "This topic is covered in depth in a future video. "
            "Mention it in one sentence of big-picture context only. "
            "Do not quiz the student on specs or details — just plant the name."
        ),
    }

    FORMAT_MODIFIERS = {
        "Contrast_Metric": (
            "Stage this as a SHOWDOWN: present both entities side-by-side "
            "and debate the winner based on the specific variable."
        ),
        "Diagnosis": (
            "Stage this as a HELPDESK CALL: one host describes the symptom, "
            "the other acts as the tech and calls out the diagnosis."
        ),
        "Sequence": (
            "Stage this as a STEP-BY-STEP WALKTHROUGH: pose rhetorical questions "
            "to each other about what the next step in the process is."
        ),
        "PainPoint_Model": (
            "Describe the real-world failure or administrative pain "
            "the next concept solves. Do not name the solution yet."
        ),
        "Foundational_Bridge": (
            "Use a concrete real-world analogy to ground the concept "
            "before stating the technical definition. "
            "If Mike used an analogy in the transcript, use his version."
        ),
        "Limit": (
            "Stage this as a BOUNDARY TEST: present the edge-case or over-limit "
            "scenario and ask what breaks and why."
        ),
        "Acronym": (
            "State the acronym and quickly provide the full expansion. "
            "No hints, no context — pure vocabulary translation."
        ),
        "Mechanism": (
            "Stage this as an UNDER-THE-HOOD reveal: explain the internal "
            "causal chain or physics of how it works, not just its name."
        ),
        "Command": (
            "Stage this as a CLI EXECUTION BEAT — one host reads the command "
            "syntax aloud as if typing it, the other explains what each flag or argument "
            "does in plain English. Make it feel executable, not theoretical."
        ),
        "Mistake": (
            "Stage this as a CAUTIONARY TALE — describe a realistic scenario "
            "where a junior technician made exactly this error and what broke as a result. "
            "Then state the correct behavior. No moralizing; just cause and effect."
        ),
    }

    # GRAFT 3 — Location A: PROMINENCE_TIERS and ACRONYM_TIER
    PROMINENCE_TIERS = {
        # (zone, type_val, status) → (tier_label, airtime_instruction)
        ("GREEN", "INTENT", "ACTIVE"):     (
            "🔴 ANCHOR TOPIC",
            "This is an exam-relevant concept the student explicitly "
            "requested. Give it full depth. Do not rush."
        ),
        ("GREEN", "INTENT", "TRIVIA"):     (
            "🟠 USER REQUEST (off-syllabus)",
            "This is an off-syllabus concept the student explicitly "
            "asked for. One clean exchange — state the spec and move on."
        ),
        ("GREEN", "INTENT", "REVIEW"):     (
            "⚪ REVIEW",
            "Covered in an earlier video. Brief passing mention — "
            "acknowledge and move on without re-teaching."
        ),
        ("BLUE",  "DEBT",   "ACTIVE"):     (
            "🔴 EXAM CRITICAL",
            "Mandatory exam objective the lecture skipped. Same "
            "weight as an anchor topic — give it a full beat."
        ),
        ("BLUE",  "SUGGESTION", "ACTIVE"): (
            "🟠 HIGH-VALUE GAP",
            "The student missed this taught concept. One full exchange "
            "— establish why it matters and cover the key fact."
        ),
        ("BLUE",  "BRIDGE", "ACTIVE"):     (
            "🟡 VOCABULARY BRIDGE",
            "One sharp exchange to connect informal language to the "
            "exam-standard term. Clinical and fast."
        ),
        ("BLUE",  "CORRECTION", "ACTIVE"): (
            "🟡 MISCONCEPTION REPAIR",
            "Clinical correction only. Identify the confusion, state "
            "the correct distinction, move on. No dwelling."
        ),
        ("BLUE",  "HANDS_ON", "ACTIVE"):   (
            "🟠 PRACTICAL EXECUTION",
            "Tactical and brief. Frame it as a field skill, not theory. "
            "Keep it executable."
        ),
        ("YELLOW","SILENT_INTRO","DEFERRED"): (
            "⬛ NAME-DROP ONLY",
            "Plant the term name only. Do not elaborate on specs or "
            "details — the student will cover this in a future video."
        ),
    }
    # Note: BLUE/DEBT/SURFACE cards are handled by the SURFACE depth
    # override block below the lookup — no separate dict entry needed.

    ACRONYM_TIER = (
        "🏷️ VOCABULARY CHECKPOINT",
        "Rapid-fire definition check. Give the expansion crisply "
        "without slowing down the momentum."
    )

    # Cognitive_Goal override — these goals bypass (zone, type) lookup entirely.
    # Autonomously injected blocks (P2/P3 scaffolding, vocabulary aids) may carry
    # BLUE/DEBT labels even though they are not missed exam objectives.
    # This dict is the priority-first check in the dossier loop (Graft 2).
    COGNITIVE_GOAL_OVERRIDES = {
        "PainPoint_Model": (
            "🧱 SCAFFOLDING: This card establishes the real-world problem or "
            "failure state that motivates the next concept. "
            "Do not frame it as a missed exam objective. "
            "Present it as context the student needs to understand why the "
            "upcoming concept exists."
        ),
        "Foundational_Bridge": (
            "🧱 SCAFFOLDING: This card provides prerequisite background knowledge. "
            "Do not frame it as a missed exam objective. "
            "Present it as the conceptual foundation the student needs "
            "before the main concept will make sense."
        ),
        "Acronym": (
            "🏷️ VOCABULARY: This card expands an acronym the student will "
            "encounter on the exam. "
            "Deliver it as a quick vocabulary check — "
            "confirm the student knows what the letters stand for before "
            "moving on to the concept itself."
        ),
    }

    # ==========================================
    # BACKGROUND ROUTINE: THE NOTEBOOK LM FORK
    # ==========================================
    print(f" [>] Siphoning CLEAN Forensic DNA for NotebookLM Brief...")
    
    # --- 1. LOAD AND CLEAN THE TRANSCRIPT ---
    transcript_data = ""
    # Re-prioritizing the cleaned bridge over the raw chat dump
    for source in ["notebook_context_bridge.txt", "raw_chat.txt"]:
        if os.path.exists(source):
            with open(source, "r", encoding="utf-8") as f:
                transcript_data = f.read()
            break
            
    if transcript_data:
        # Purge system prompt block (handles both ASCII and UTF-8 Smart Quotes)
        cleaned_transcript = re.sub(r"(?i)You are operating in transcription-only mode.*?continue responding with.*?Received\.?[\"“”]", "", transcript_data, flags=re.DOTALL)
        # Purge all "Create a flash..." voice triggers (catches all STT variants)
        _trig_re_p5 = re.compile(r'^create\s+(?:a\s+)?flash\w*', re.IGNORECASE)
        cleaned_transcript = "\n".join(
            line for line in cleaned_transcript.split("\n")
            if not _trig_re_p5.match(line.strip())
        )
        # Purge all stray "Received." acknowledgments
        cleaned_transcript = re.sub(r"(?i)\n*Received\.?\n*", "\n\n", cleaned_transcript)
        # Strip stray video number headers (e.g., "101\n") injected by Phase 1
        cleaned_transcript = re.sub(r"^\d+\s*\n", "", cleaned_transcript.strip())
    else:
        cleaned_transcript = "[NO RAW TRANSCRIPT FOUND]"

    producer_brief = []
    producer_brief.append("<raw_transcript>\n")
    producer_brief.append("# 📄 THE RAW LECTURE TRANSCRIPT\n")
    producer_brief.append("Context: This is a raw lecture transcript from a CompTIA course instructor. Use this to understand the narrative flow and tone. Refer to him as the instructor. Do NOT call him 'the source'.\n\n")
    producer_brief.append(cleaned_transcript + "\n\n")
    producer_brief.append("</raw_transcript>\n\n")

    # --- 2. PARSE THE APPROVED SYLLABUS ---
    producer_brief.append("<producer_notes>\n")
    producer_brief.append("\n\n[Producer margin notes — not for broadcast. "
                          "Work these into the conversation naturally. "
                          "Pay strict attention to the behavioral cues.]\n\n")

    input_file = _P + "curated_polished_yaml.txt"
    if os.path.exists(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            yaml_content = f.read()

        blocks = [b.strip() for b in re.split(r"(?m)^---(?:\s*\n)?", yaml_content)
                  if b.strip()]
        pre_flight_questions = []

        for block in blocks:

            # ── PARSE CORE FIELDS ──────────────────────────────────────────
            front_match = re.search(
                r"Front:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                block, re.DOTALL)
            back_match = re.search(
                r"Back:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                block, re.DOTALL)
            extra_match = re.search(
                r"Extra:\s*(?:\"|\|-|>)?\s*(.*?)(?:\"?\s*(?=\n[A-Z][a-zA-Z0-9_ -]*:|\Z))",
                block, re.DOTALL)
            meta_match = re.search(r'Meta:\s*"?([^"\n]+)"?', block)

            # Guard: skip blocks that cannot be parsed
            if not (front_match and back_match and meta_match):
                continue

            front = front_match.group(1).replace('\\"', '"').strip()
            back_raw = back_match.group(1).replace('\\"', '"').strip()
            extra_text = extra_match.group(1).strip() if extra_match else ""

            # ── PARSE META FIELD ───────────────────────────────────────────
            meta_field = meta_match.group(1).strip()
            meta_parts = [p.strip() for p in meta_field.split('|')]
            # meta_parts[0] = Cognitive_Goal  (per P3 output schema)
            cognitive_goal = meta_parts[0] if meta_parts else ""
            zone_m = re.search(r'zone=(GREEN|BLUE|YELLOW)', meta_field)
            type_m = re.search(r'type=([A-Z_]+)', meta_field)
            zone = zone_m.group(1) if zone_m else "BLUE"
            type_val = type_m.group(1) if type_m else "DEBT"

            # ── GRAFT 2: Parse depth AND status from Meta Field ────────────
            depth_m = re.search(r'depth=(PRIMARY|SURFACE)', meta_field)
            depth_val = depth_m.group(1) if depth_m else "PRIMARY"

            status_m = re.search(r'status=([A-Z_]+)', meta_field)
            status = status_m.group(1) if status_m else "ACTIVE"

            # ── GRAFT 6A HOIST: Compute cog_goal_for_topic ────────────────
            # Must be defined here so Graft 7 (pre-flight gate) and Graft 6B
            # (topic title construction) can both reference it.
            cog_goal_for_topic = cognitive_goal.split('(')[0].strip()

            if not zone_m or not type_m:
                print(f" [!] ⚠️ WARNING: Malformed Meta field fallback triggered for card: '{front_clean[:30]}...'")

            # ── STRIP EMOJI VISUAL SIGNATURE FROM FRONT ───────────────────
            # P5 Phase 3-A.5 prepends a category emoji; remove it for plain-text output.
            front_clean = re.sub(r'^[^\x00-\x7F\s]+\s*', '', front).strip()

            # ── GRAFT 7: Exclude Acronym Blocks from Pre-Flight ───────────
            # DEPENDENCY: Graft 6A HOIST must be applied above this gate.
            if cog_goal_for_topic != "Acronym":
                pre_flight_questions.append(f"— {front_clean}")

            # ── GRAFT 6B: Topic Title Identity-Class Override ─────────────
            _IDENTITY_GOALS = {
                "Fused_Identity", "Translation", "Rosetta_Identity",
                "Identity", "Synonym"
            }
            if cog_goal_for_topic in _IDENTITY_GOALS:
                title_str = (
                    meta_parts[1].strip()
                    if len(meta_parts) > 1 and meta_parts[1].strip()
                    else front_clean
                )
            else:
                title_str = front_clean
            topic_title = f"--- TOPIC: {title_str} ---\n"

            # ── RESOLVE DIRECTOR'S CUE (Priority: Cognitive_Goal first) ───
            # Scaffolding and vocabulary blocks may carry BLUE/DEBT labels
            # even though they are not missed exam objectives. The
            # COGNITIVE_GOAL_OVERRIDES dict intercepts these before the
            # (zone, type) lookup fires.
            if cognitive_goal in COGNITIVE_GOAL_OVERRIDES:
                base_cue = COGNITIVE_GOAL_OVERRIDES[cognitive_goal]
            else:
                base_cue = DIRECTOR_CUES.get(
                    (zone, type_val),
                    "Present this concept straightforwardly."
                )

            format_mod = FORMAT_MODIFIERS.get(cognitive_goal, "")
            full_cue = (base_cue + " " + format_mod).strip() if format_mod else base_cue

            # ── GRAFT 4: BRIDGE Precision-Upgrade Detection ────────────────
            # Fires only on BRIDGE cards. Checks Front for upgrade-signal keywords.
            # Precision-upgrade bridges (e.g. PAN → WPAN) must NOT be framed as
            # corrections — the keyword heuristic distinguishes them from slang
            # bridges (e.g. sticker → Passive RFID Transponder).
            if type_val == "BRIDGE":
                _upgrade_signals = {"formal", "exam-standard", "ref b-precise",
                                    "classification", "upgrade", "precise"}
                if any(sig in front_clean.lower() for sig in _upgrade_signals):
                    full_cue = (
                        "🔼 PRECISION UPGRADE — Mike used the correct term at a lower "
                        "precision level. Do NOT frame this as a mistake. Quote Mike's "
                        "phrasing, then present the exam-precise version as the upgrade. "
                        "No correction implied."
                    )

            # ── SPLIT BACK INTO CORE FACT + TEACHING NOTES ────────────────
            # Use regex to handle all <br> variants: <br>, <br/>, <br />
            back_parts = re.split(r'<br\s*/?>', back_raw, maxsplit=1,
                                  flags=re.IGNORECASE)
            core_fact = back_parts[0].strip()
            teaching_notes = back_parts[1].strip() if len(back_parts) > 1 else ""

            # ── EXTRACT EXAM TRAP FROM EXTRA FIELD ────────────────────────
            # GRAFT 8: Guard expanded to "⚠️" to catch both ⚠️ NOT: and
            # ⚠️ Exam Trap: prefix formats. Pattern updated to match both variants.
            exam_trap = ""
            if "⚠️" in extra_text:
                traps = re.findall(r"⚠️\s*(?:NOT|Exam\s+Trap):\s*(.*?)(?:<br|$)", extra_text, flags=re.IGNORECASE)
                if traps:
                    exam_trap = " | ".join(t.strip() for t in traps)

            # ── GRAFT 3B: Tier Selection ───────────────────────────────────
            # cog_goal_for_topic defined at Graft 6A HOIST above.
            # depth_val and status defined at Graft 2 above.
            if cog_goal_for_topic == "Acronym":
                tier_label, tier_cue = ACRONYM_TIER
            else:
                tier_label, tier_cue = PROMINENCE_TIERS.get(
                    (zone, type_val, status),
                    ("🟡 SUPPORTING CONTENT", "Normal pace. Standard treatment.")
                )

            # SURFACE depth override — fires last, compresses any tier
            if depth_val == "SURFACE":
                tier_label = "⚪ PASSING MENTION"
                tier_cue   = (
                    "Keep this extremely brief. Acknowledge the detail "
                    "quickly and transition forward without deep-diving."
                )

            # ── ASSEMBLE DOSSIER ENTRY ─────────────────────────────────────
            dossier_entry = topic_title
            dossier_entry += f"🎯 FOCUS LEVEL: {tier_label}\n"
            dossier_entry += f"⏱️  AIRTIME: {tier_cue}\n"
            dossier_entry += f"🎬 DIRECTOR'S CUE: {full_cue}\n"
            dossier_entry += f"📝 CORE FACT: {core_fact}\n"

            if teaching_notes:
                # Strip bold markdown and residual <br> tags for clean TTS delivery
                notes_clean = re.sub(r'\*\*(.*?)\*\*', r'\1', teaching_notes)
                # GRAFT 10: \s* added after closing > to consume trailing whitespace,
                # preventing double-space artifacts in TTS output.
                notes_clean = re.sub(r'<br\s*/?>\s*', ' ', notes_clean, flags=re.IGNORECASE)
                # Strip prefix labels (Logic:, Delta:, etc.) even if they are mid-string
                notes_clean = re.sub(
                    r'\b(?:Logic|Delta|Analogy|Context):\s*', '', notes_clean,
                    flags=re.IGNORECASE)
                # ── GRAFT 5: Conditional Teaching Notes Label ──────────────
                # Source-type-aware label prevents hosts from attributing
                # P2-injected Ref B facts to Mike's lecture delivery.
                # NOTE: Any NotebookLM_Prompt_BETA.txt instructions keyed to the
                # literal string "TEACHING NOTES:" will no longer match DEBT
                # or SUGGESTION cards — check that file manually for dependencies.
                if type_val == "DEBT":
                    notes_label = "📚 EXAM STANDARD (NOT IN MIKE'S VIDEO):"
                elif type_val == "SUGGESTION":
                    notes_label = "🧠 MIKE TAUGHT THIS — student missed it:"
                elif type_val in ("BRIDGE", "CORRECTION"):
                    notes_label = "🧠 CONTEXT NOTES:"
                else:
                    notes_label = "🧠 TEACHING NOTES:"
                dossier_entry += f"{notes_label} {notes_clean}\n"

            if exam_trap:
                dossier_entry += f"🛑 EXAM TRAP: {exam_trap}\n"

            dossier_entry += "\n"
            producer_brief.append(dossier_entry)

    # CLOSE THE XML BOUNDARY SAFELY BEFORE WRITING
    producer_brief.append("</producer_notes>\n")

    with open("NOTEBOOK_PRODUCER_BRIEF.txt", "w", encoding="utf-8") as f:
        f.write("".join(producer_brief))

    # --- GENERATE PRE-FLIGHT SIDE-CAR ---
    with open("PRE_FLIGHT_QUESTIONS.txt", "w", encoding="utf-8") as f:
        f.write("🚀 PRE-FLIGHT CHECK: READ THESE TO OPEN YOUR COGNITIVE LOOPS\n")
        f.write("="*60 + "\n\n")
        f.write("\n\n".join(pre_flight_questions))
        f.write("\n\n" + "="*60 + "\n")
        f.write("🧠 Loops opened. Now hit play on the podcast.")

    # ==========================================
    # LATE CASTING DIRECTOR PHASE (Decision 2 + execution)
    # ==========================================
    # Decision 1 (A/L/S) was made in the early gate above (after veto gate).
    # If [L] was picked, _cd_chosen was also set there. This phase only:
    #   - On [A]: runs the 2 LLM calls + Decision 2 prompt + template fill
    #   - On [L]: skips directly to template fill using already-set _cd_chosen
    #   - On [S] / unavailable: no-op
    try:
        if _cd_unavailable or _cd_gate is None or _cd_gate == "S":
            pass  # Early phase already handled it -- nothing to do here.
        else:
            def _cd_parse(raw, required_keys):
                cleaned = re.sub(r'^```[a-zA-Z]*\n?', '', raw.strip()).rstrip('`').strip()
                try:
                    data = json.loads(cleaned)
                except json.JSONDecodeError:
                    m = re.search(r'\{.*\}', cleaned, re.DOTALL)
                    if m:
                        try:
                            data = json.loads(m.group())
                        except json.JSONDecodeError:
                            return None
                    else:
                        return None
                if not isinstance(data, dict):
                    return None
                for k in required_keys:
                    if not isinstance(data.get(k), str) or not data[k].strip():
                        return None
                return data

            _cd_picked = None
            _cd_picked_key = None
            _cd_generated = None

            if _cd_gate == "A":
                # -- CALL 1: SELECTOR --
                _cd_selector_prompt = (
                    "You are a podcast casting director. Given a lecture transcript and a "
                    "library of persona pairings, select the single best-fit pairing for "
                    "this episode.\nOutput ONLY valid JSON: {\"pick\": \"<key_name>\"}. No other text.\n\n"
                    "PAIRING LIBRARY:\n" + json.dumps(_cd_PAIRINGS, indent=2) +
                    "\n\nTRANSCRIPT:\n" + cleaned_transcript
                )
                for _cd_attempt in range(2):
                    _cd_raw = config.call_llm(_cd_selector_prompt,
                                              context_header="CASTING DIRECTOR | SELECTOR")
                    _cd_res = _cd_parse(_cd_raw, ["pick"])
                    if _cd_res and _cd_res["pick"] in _cd_PAIRINGS:
                        _cd_picked_key = _cd_res["pick"]
                        _cd_picked = _cd_PAIRINGS[_cd_picked_key]
                        break

                # -- CALL 2: GENERATOR --
                _cd_gen_fields = ["key", "TONE_FRAME", "CHEMISTRY_DYNAMIC",
                                  "HOST_A_PERSONA", "HOST_B_PERSONA",
                                  "HOST_B_INTENSITY_STYLE", "HOST_A_REGISTER", "HOST_B_REGISTER"]
                _cd_dia = random.sample(DIALECTS, 2)
                _cd_generator_prompt = (
                    "You are a podcast casting director. Create ONE original persona pairing for a "
                    "comedic CompTIA A+ exam prep podcast episode.\n\n"
                    "ASSIGNED VOICES (build the pairing around THESE two -- do not substitute):\n"
                    "  HOST A voice: " + _cd_dia[0] + "\n"
                    "  HOST B voice: " + _cd_dia[1] + "\n\n"
                    "RULES\n"
                    "- REGION is PRE-ASSIGNED and is already a voiceable English-variety accent. Do NOT swap it\n"
                    "  for a foreign-language or non-white-English accent. INVENT a PROFESSION / era /\n"
                    "  relationship that naturally speaks that region and fuse it on.\n"
                    "- The two voices must CLASH; this lesson's friction surfaces through them.\n"
                    "- Sustainable across a full 30-minute episode; do NOT literally embody the tech.\n"
                    "- HOST B ALWAYS HOLDS THE TRUTH and detonates HOST A's wrong theory. Never soften that\n"
                    "  posture -- it is the study guardrail.\n\n"
                    "STEP 1 -- THE WORLDVIEW LENS (the single biggest driver of a good episode)\n"
                    "Give each host ONE lens: an obsession whose emotional stakes get imported wholesale onto\n"
                    "the hardware, so a snapped plastic clip lands like a death in the family and a dry spec\n"
                    "turns operatic.\n"
                    "BANNED LENSES (lazy LLM defaults -- reaching for one is a FAIL): nightclubs, bouncers, velvet\n"
                    "ropes or VIP guest lists for anything about access, gatekeeping or permissions; 'the internet\n"
                    "is a highway'; 'the computer is a restaurant kitchen'; 'the firewall is a security guard'.\n"
                    "Derive the lens from the PROFESSION you just invented, never from the tech topic.\n"
                    "FUSE THE LENS INTO THE PERSONA STRING. It is NOT a 'metaphors from X' tag bolted onto the\n"
                    "register -- it lives in the persona, where it colours every fact the host touches.\n"
                    "PERSONA = identity (assigned region x invented profession) + WORLDVIEW LENS + ATTITUDE +\n"
                    "FLAW + BUTTON (+ ENERGY for HOST A). Telegraphic fragments, not sentences. Do NOT restate\n"
                    "the template's trap behaviour (A inhabits the wrong diagnosis, B escalates then\n"
                    "detonates, B holds the truth) -- the PRIME DIRECTIVE supplies it ONCE, and once is the\n"
                    "rule: never say anything the skeleton already says.\n\n"
                    "STEP 2 -- THE REGISTER = ONE FLAT BANK, NOT LABELLED CATEGORIES\n"
                    "Shape: the ASSIGNED DIALECT LABEL verbatim, then ' -- ', then 22-26 short fragments\n"
                    "separated by ' | '. Nothing else. NO 'interjections -- a | b | c ; idioms -- d | e ;\n"
                    "address -- ...' headers. No grouping, no semicolon clauses, no JSON array. Keep the leading\n"
                    "dialect label -- it is what tells the show which accent to actually speak -- and make the\n"
                    "bank read naturally straight after the template line 'SPEAKS THIS VOICE, ALWAYS:'.\n"
                    "WEIGHTING, and this is the whole job: INTERJECTIONS AND EXCLAMATIONS DOMINATE -- at least\n"
                    "half the bank. They are the #1 driver of delight, energy and personality; every great\n"
                    "episode is saturated with them, and a labelled format rations them to one clause. Salt the\n"
                    "rest invisibly through the SAME flat bank, unlabelled, in any order: fresh regional\n"
                    "idioms/similes, terms of address, slang noun-swaps, a grammatical tic or two, one signature\n"
                    "catchphrase -- and the region's COLOURFUL LANGUAGE, which is the funniest thing in the show.\n"
                    "COLOUR COMES IN FOUR KINDS. Every host needs all four, dissolved into the same flat bank:\n"
                    "  1 DERISION -- what THIS region calls a fool, an idiot, a waste of space.\n"
                    "  2 BINDING WORDS -- its PG-13 intensifiers, the glue that carries frustration mid-sentence.\n"
                    "  3 REACTIONS -- vivid regional blow-ups for when it has all gone wrong.\n"
                    "  4 ANCHOR SAYINGS -- extended metaphorical put-downs, at least one; see below.\n"
                    "TIER EXAMPLES -- these show the LEVEL and NOTHING ELSE. Every one is BURNED; using any of them\n"
                    "is an instant fail. Derision: tosser, bampot, drongo, absolute weapon, daft as a brush, face\n"
                    "like a slapped arse. Binding: bloody, chuffing, bleeding, bugger, sodding. Reactions: gone tits\n"
                    "up, up shit creek, my head's louping, sweating cobs. THAT is the wattage -- pub, not playground.\n"
                    "If your fragment would not raise an eyebrow, it is too weak. Now go and find what YOUR TWO\n"
                    "ASSIGNED REGIONS actually say --\n"
                    "the real, specific, funny stuff a native would use, that a listener has never heard on a podcast.\n"
                    "PERSONA FILTER -- a SUBSTITUTION, never an exemption. NOBODY is exempt from colour; only the\n"
                    "FLAVOUR is filtered. A dockworker swears like a dockworker. A nun, a priest or a Victorian prude\n"
                    "does NOT get to be bland -- they get hyper-pious or hyper-genteel equivalents at the SAME heat\n"
                    "('sweet weeping wounds of Saint Peter!'). Same wattage, different socket. There is no opt-out.\n"
                    "It should read like a person talking, not a taxonomy.\n"
                    "ANCHOR SAYING (mandatory, AT LEAST ONE per host): a fragment must be a full extended saying\n"
                    "-- 30-50 chars, a vivid image, never a bare word or interjection (the 'couldn't organise X in\n"
                    "a Y' / 'wouldn't know X from Y' mould, dialect-flavoured, cutting but clean). Place it in the\n"
                    "FRONT half, just after the opening interjections, so a tail-trim never eats it. Do NOT add a\n"
                    "fragment to fit it -- swap out the weakest non-interjection filler and keep the same total\n"
                    "count. ONE seeds a whole family -- the show riffs variations off a single seed all episode --\n"
                    "but TWO or THREE is BETTER wherever the region has them and the fragment budget holds. Do not\n"
                    "stop at one out of caution; this is the funniest thing in the bank.\n\n"
                    "FRONT-LOAD the interjections: if the filled prompt runs long the pipeline trims fragments\n"
                    "from the TAIL of the bank, so whatever you put last is the first thing lost.\n\n"
                    "STEP 3 -- INTERNAL CHECKLIST (use it while writing; NEVER let it shape the output)\n"
                    "Silently confirm each host has all 12 levers: 1 interjections, 2 idioms/similes (>=1 must be\n"
                    "the full anchor saying, not a tag), 3 address,\n"
                    "4 slang noun-swaps, 5 light profession jargon (it rides inside the worldview lens -- the\n"
                    "region carries the voice), 6 grammar/tics, 7 cadence, 8 worldview lens, 9 attitude, 10 flaw,\n"
                    "11 button, 12 energy. Levers 8-12 land in the PERSONA; levers 1-7 dissolve into the flat\n"
                    "bank; HOST B's energy plus how his voice shifts as HOST A's theory worsens goes in\n"
                    "HOST_B_INTENSITY_STYLE. If the output looks like this checklist, you have failed -- it is\n"
                    "scaffolding, not shape.\n\n"
                    "ORIGINALITY MANDATE (hard fail)\n"
                    "Every phrase must be INVENTED FRESH for this pairing. You are FORBIDDEN from reusing any\n"
                    "phrase, interjection, idiom, address term or simile that appears in the WORKED EXAMPLE\n"
                    "or the TIER EXAMPLES -- they teach SHAPE, TIER and DENSITY only, and reuse\n"
                    "recycles the same episode forever. At most ONE fragment may be the region's stock phrase\n"
                    "(the one inside the dialect label); the other 21-25 must be sayings a listener has never\n"
                    "heard -- vivid, specific, regional, PUB-TIER. Regional insults, bodily indignity, livestock,\n"
                    "weather, faces and colourful derision ALL LAND. Aim at the level two locals actually use on\n"
                    "each other across a bar -- not a cartoon. NO F-bombs and NO slurs; that is the ONLY limit, and\n"
                    "there is no other. Do not soften, do not reach for a safe word, do not substitute food or\n"
                    "nonsense ('meatball', 'blockhead') where a real regional insult belongs -- that is the failure\n"
                    "mode, and it is worse than going too far. Idioms and similes are the payload; delivery is the\n"
                    "lever, not wit. If a single example phrase or TIER EXAMPLE appears in your JSON, the output is\n"
                    "INVALID -- rewrite it.\n\n"
                    "FORMAT -- 8 string fields, telegraphic fragments, not sentences. HARD caps (chars), tuned so\n"
                    "the filled show prompt lands under its 4,979-char limit. Do not exceed them:\n"
                    "  key ~30 (snake_case) | TONE_FRAME ~50 (one punchy 'X vs Y.') | CHEMISTRY_DYNAMIC ~90\n"
                    "  (ONE tight clause naming what collides -- TONE_FRAME already carries the X-vs-Y frame; do\n"
                    "  NOT restate both full personas here) | HOST_A_PERSONA ~235 | HOST_B_PERSONA ~235 |\n"
                    "  HOST_B_INTENSITY_STYLE ~120 | HOST_A_REGISTER ~540 | HOST_B_REGISTER ~540\n"
                    "A 22-26 fragment bank costs ~430-480 chars, the anchor saying included. That budget exists so\n"
                    "the four kinds of colour all FIT -- spend it on FRAGMENTS, never on labels, and never pad.\n\n"
                    "RE-ANCHOR before you output: assigned English-variety accent kept | profession invented to\n"
                    "fit THIS lesson | worldview lens INSIDE the persona | register = one flat, interjection-heavy\n"
                    "bank with zero labels | every phrase freshly invented | HOST B holds the truth | dialect\n"
                    "colours HOW they talk, never WHAT the fact is.\n\n"
                    "OUTPUT: valid JSON only. No markdown fences, no commentary. Exactly these 8 keys:\n"
                    "  key, TONE_FRAME, CHEMISTRY_DYNAMIC, HOST_A_PERSONA, HOST_B_PERSONA,\n"
                    "  HOST_B_INTENSITY_STYLE, HOST_A_REGISTER, HOST_B_REGISTER\n\n"
                    "WORKED EXAMPLE -- match this SHAPE, DENSITY and TEXTURE exactly. Its assigned voices were\n"
                    "'Kiwi (sweet as)' and 'Welsh valleys'; yours are different, and every phrase below is BURNED\n"
                    "-- you may not reuse a single one:\n"
                    """{
  "key": "shed_mechanic_choirmaster",
  "TONE_FRAME": "Tractor-shed brute force vs choral grief.",
  "CHEMISTRY_DYNAMIC": "A Kiwi shed mechanic who services a $2,000 laptop like a seized tractor + a Welsh ex-choir director who hears a chorister die in every snapped clip.",
  "HOST_A_PERSONA": "Rural Kiwi shed mechanic. WORLDVIEW: every machine is a tractor -- if she sticks, hit her harder; spare screws are decoration. FLAW: brute force mistaken for diagnosis. BUTTON: torque specs. ENERGY: loud, hands already in the chassis.",
  "HOST_B_PERSONA": "Welsh ex-choir director, now repair-bench pedant. WORLDVIEW: the chassis is a choir -- every clip a chorister, every snap an operatic death he mourns aloud. FLAW: melodrama. BUTTON: brutality toward delicate parts. Detonates mid-aria.",
  "HOST_B_INTENSITY_STYLE": "Keens more operatically as theories worsen; stages each disaster as a funeral aria, then lands the fix in one flat line.",
  "HOST_A_REGISTER": "Kiwi (sweet as) -- yeah, nah, bro! | oh, choice! | chur! | crikey dick! | no wuckas! | flamin' heck! | hard out! | rattle your dags! | wouldn't know a spanner from a spark plug | face like a dropped pie | she'll be right, ay | sweating like a glassblower's armpit | gone to custard | spat the dummy | that's hard yakka | proper munted, that | you absolute dropkick | you great egg | gutted, bro | a wee tiki tour | up the wop-wops | chuck it in the ute | number-eight-wire it | sweet as, aye",
  "HOST_B_REGISTER": "Welsh valleys -- ach y fi! | duw duw! | iechyd da! | I'm tamping, I am! | there we are, see! | flippin' 'eck! | arse over tit again! | there's lovely! | tidy! | couldn't carry a tune in a bucket | lovely boy | cariad | mun | you daft ha'porth | soft lad | twp as a bag of hammers | you gormless lump | chopsing again, you are | I'm in bits, I am! | that's lush, that is | proper job | gone to pot | dead loss, you are | boyo"
}"""
                    "\n\n"
                    "TEMPLATE CONTEXT (understand what each field feeds into):\n" + _cd_beta + "\n\n"
                    "TRANSCRIPT:\n" + cleaned_transcript
                )
                for _cd_attempt in range(2):
                    _cd_raw = config.call_llm(_cd_generator_prompt,
                                              context_header="CASTING DIRECTOR | GENERATOR")
                    _cd_res = _cd_parse(_cd_raw, _cd_gen_fields)
                    if _cd_res and _cd_validate_pairing(_cd_res)[0]:
                        _cd_generated = _cd_res
                        break

                # -- DECISION 2: SHOW + PICK 1/2/M --
                def _cd_show(label, key, p):
                    print(f"\n {label}: \"{key}\"")
                    print(f"     Tone:      {p['TONE_FRAME']}")
                    print(f"     Dynamic:   {p['CHEMISTRY_DYNAMIC']}")
                    print(f"     Host A:    {p['HOST_A_PERSONA']}")
                    print(f"     Host B:    {p['HOST_B_PERSONA']}")
                    print(f"     Intensity: {p['HOST_B_INTENSITY_STYLE']}")
                    print(f"     Voice A:   {p['HOST_A_REGISTER']}")
                    print(f"     Voice B:   {p['HOST_B_REGISTER']}")

                _cd_valid = []
                print("\n" + "="*64)
                print("  CASTING DIRECTOR -- Choose your hosts for this episode")
                print("="*64)
                if _cd_picked:
                    _cd_show("[1] FROM LIBRARY", _cd_picked_key, _cd_picked)
                    _cd_valid.append("1")
                else:
                    print("\n [1] FROM LIBRARY: [unavailable]")
                if _cd_generated:
                    _cd_show("[2] GENERATED", _cd_generated["key"], _cd_generated)
                    _cd_valid.append("2")
                else:
                    print("\n [2] GENERATED: [unavailable]")
                print("\n [M] MANUAL -- Browse full library")
                _cd_valid.append("M")
                print()

                if not _cd_picked and not _cd_generated:
                    print(" [!] API unavailable -- switching to manual pick.")
                    _cd_choice = "M"
                else:
                    while True:
                        _cd_choice = input(
                            f" Choice ({' / '.join(_cd_valid)}): "
                        ).strip().upper()
                        if _cd_choice in _cd_valid:
                            break
                        print(f" [!] Invalid -- enter one of: {', '.join(_cd_valid)}")

                # -- LIBRARY BROWSER FALLBACK (M path on [A]) --
                if _cd_choice == "M":
                    try:
                        with open("pairings_generated.json", "r", encoding="utf-8") as _gf:
                            _cd_gen_lib = json.load(_gf)
                    except FileNotFoundError:
                        _cd_gen_lib = {}
                    except (json.JSONDecodeError, ValueError):
                        print(" [!] WARNING: pairings_generated.json corrupted -- treating as empty.")
                        _cd_gen_lib = {}
                    _cd_all = list(_cd_PAIRINGS.items()) + [(k, v) for k, v in _cd_gen_lib.items()]
                    _cd_n = len(_cd_all)
                    print("\n-- FULL LIBRARY " + "-"*48)
                    for _cd_i, (_cd_k, _cd_p) in enumerate(_cd_all, 1):
                        _cd_star = " *" if _cd_k in _cd_gen_lib else ""
                        print(f"  [{_cd_i:2d}]  {_cd_k:<30}{_cd_star} -- {_cd_p['TONE_FRAME']}")
                    print("-"*64)
                    while True:
                        try:
                            _cd_num = int(input(" Pick number: ").strip())
                            if 1 <= _cd_num <= _cd_n:
                                break
                            print(f" [!] Enter a number between 1 and {_cd_n}.")
                        except ValueError:
                            print(f" [!] Enter a number between 1 and {_cd_n}.")
                    _cd_chosen_key, _cd_chosen = _cd_all[_cd_num - 1]

                elif _cd_choice == "1":
                    _cd_chosen_key, _cd_chosen = _cd_picked_key, _cd_picked

                elif _cd_choice == "2":
                    _cd_chosen_key, _cd_chosen = _cd_generated["key"], _cd_generated
                    _cd_save = input(
                        f" Save \"{_cd_chosen_key}\" to library? (y/n): "
                    ).strip().lower()
                    if _cd_save == "y":
                        try:
                            with open("pairings_generated.json", "r", encoding="utf-8") as _gf:
                                _cd_gen_lib = json.load(_gf)
                        except FileNotFoundError:
                            _cd_gen_lib = {}
                        except (json.JSONDecodeError, ValueError):
                            print(" [!] WARNING: pairings_generated.json corrupted -- starting fresh.")
                            _cd_gen_lib = {}
                        if _cd_chosen_key in _cd_gen_lib:
                            print(f" [!] Key \"{_cd_chosen_key}\" already exists -- overwriting.")
                        _cd_gen_lib[_cd_chosen_key] = _cd_chosen
                        with open("pairings_generated.json", "w", encoding="utf-8") as _gf:
                            json.dump(_cd_gen_lib, _gf, indent=2, ensure_ascii=False)
                        print(f" [+] \"{_cd_chosen_key}\" saved to pairings_generated.json")
            # [L] path: _cd_chosen was set in the early phase -- fall through to template fill

            # -- TEMPLATE SUBSTITUTION (fires for both [A] and [L] paths) --
            if _cd_chosen is not None and _cd_beta is not None:
                _cd_filled = _cd_beta
                for _cd_tok in ["TONE_FRAME", "CHEMISTRY_DYNAMIC", "HOST_A_PERSONA",
                                "HOST_B_PERSONA", "HOST_B_INTENSITY_STYLE",
                                "HOST_A_REGISTER", "HOST_B_REGISTER"]:
                    _cd_filled = _cd_filled.replace("{{" + _cd_tok + "}}", _cd_chosen[_cd_tok])
                # -- SEED MANDATION: inject 2 distinct random Flavor Archive seeds --
                _cd_seeds = random.sample(FLAVOR_SEEDS, 2)
                _cd_seed_block = "* " + _cd_seeds[0] + "\n* " + _cd_seeds[1]
                _cd_filled = _cd_filled.replace("{{MANDATED_SEEDS}}", _cd_seed_block)
                print(f" [+] Seeds injected: \"{_cd_seeds[0][:55]}...\" / \"{_cd_seeds[1][:55]}...\"")
                # -- CHAR-CAP BACKSTOP: keep FILLED under NotebookLM's 4979 limit --
                # Blind LLM generation can overshoot the register soft-caps; trim the
                # two banks (drop trailing pipe phrases, never below the leading segment)
                # and RE-INJECT the same seed block so {{MANDATED_SEEDS}} is never orphaned.
                if len(_cd_filled) > 4979:
                    _cd_ra = _cd_chosen["HOST_A_REGISTER"]
                    _cd_rb = _cd_chosen["HOST_B_REGISTER"]
                    while len(_cd_filled) > 4979:
                        _a = _cd_ra.split("|")
                        _b = _cd_rb.split("|")
                        if len(_a) <= 1 and len(_b) <= 1:
                            break  # convergence floor: both banks at leading segment
                        if len(_a) >= len(_b) and len(_a) > 1:
                            _cd_ra = "|".join(_a[:-1]).rstrip()
                        elif len(_b) > 1:
                            _cd_rb = "|".join(_b[:-1]).rstrip()
                        _cd_filled = _cd_beta
                        for _cd_t in ["TONE_FRAME", "CHEMISTRY_DYNAMIC", "HOST_A_PERSONA",
                                      "HOST_B_PERSONA", "HOST_B_INTENSITY_STYLE"]:
                            _cd_filled = _cd_filled.replace("{{" + _cd_t + "}}", _cd_chosen[_cd_t])
                        _cd_filled = _cd_filled.replace("{{HOST_A_REGISTER}}", _cd_ra)
                        _cd_filled = _cd_filled.replace("{{HOST_B_REGISTER}}", _cd_rb)
                        _cd_filled = _cd_filled.replace("{{MANDATED_SEEDS}}", _cd_seed_block)
                    print(f" [!] Char-cap backstop: trimmed banks; FILLED now {len(_cd_filled)} chars.")
                if "{{" in _cd_filled:
                    print(" [!] WARNING: Unfilled tokens remain in NotebookLM_Prompt_FILLED.txt")
                with open("NotebookLM_Prompt_FILLED.txt", "w", encoding="utf-8") as _ff:
                    _ff.write(_cd_filled)
                print(f" [+] NotebookLM_Prompt_FILLED.txt written ({_cd_chosen_key})")

    except KeyboardInterrupt:
        print("\n [!] Casting Director skipped.")

    # Determine which prompt file to open (static fallback retired — FILLED only)
    _prompt_to_open = "NotebookLM_Prompt_FILLED.txt"

    # --- 3. VALIDATE THE MASTER PROMPT EXISTS ---
    if not os.path.exists(_prompt_to_open):
        print(f" [!] WARNING: '{_prompt_to_open}' is missing "
              "from the root directory.")
        print(" [!] You will need this file for the NotebookLM upload.")

    try:
        config.clear_screen()
    except Exception:
        pass

    # ==========================================
    # PROMPT TELEMETRY HARVEST (cross-phase feedback sweep)
    # ==========================================
    harvest_telemetry()

    # Record raw_chat.txt char count + video_id so the next run can detect a stale file
    try:
        with open("raw_chat.txt", "r", encoding="utf-8") as _f:
            _chars = len(_f.read())
        with open(".raw_chat_count", "w") as _f:
            _f.write(str(_chars))
        _vid = "unknown"
        if os.path.exists("baton_p1_to_p2.xml"):
            with open("baton_p1_to_p2.xml", "r", encoding="utf-8") as _f:
                _m = re.search(r"<video_id>([\d+]+)</video_id>", _f.read())
            if _m:
                # Combined transcript "120+121" → canonical "121" (last token).
                # Single integer "117" → "117". Anything else → stays "unknown".
                _parts = [p for p in _m.group(1).split("+") if p.isdigit()]
                if _parts:
                    _vid = _parts[-1]
        with open(".last_video_id", "w") as _f:
            _f.write(_vid)
        print(f" [+] Recorded state for next run: video {_vid}, {_chars} chars")
    except Exception as _e:
        print(f" [!] Could not record state: {_e}")

    print("="*60)
    print(" [!] PIPELINE COMPLETE: DECK IS READY FOR ANKI ".center(60, "#"))
    print("="*60)
    print(" [+] Formatting           : Pipe-Delimited (|)")
    print(" [+] Checksums Purged     : SUCCESS")
    print(" [+] File Created         : ANKI_IMPORT_READY.txt")
    print(" [+] Forensic Log         : forensic_raw_p5.txt")
    print(" [+] NotebookLM Brief     : NOTEBOOK_PRODUCER_BRIEF.txt")
    print(f" [+] NotebookLM Prompt    : {_prompt_to_open}")
    print(" [+] Pre-Flight Side-Car   : PRE_FLIGHT_QUESTIONS.txt")
    print("="*60)
    
    # ==========================================
    # AUTO-LAUNCH BAY: DEPLOY STUDY ENVIRONMENT
    # ==========================================
    print(" [>] Launching Study Environment...")
    
    notebook_url = "https://notebooklm.google.com/?authuser=1&pageId=none"

    if config.ANKI_PATH is not None and os.path.exists(config.ANKI_PATH):
        try:
            subprocess.Popen([config.ANKI_PATH], shell=True)
            print(" [+] Anki launched.")
        except Exception as e:
            print(f" [!] Anki launch error: {e}")
    else:
        print(" [!] Anki not found at configured path — skipping launch.")

    webbrowser.open(notebook_url)
    print(" [+] Study environment deployed.")

    # --- AUTO-OPEN TEXT FILES ---
    print(" [>] Opening Producer Brief and Prompt files...")
    for text_file in ["NOTEBOOK_PRODUCER_BRIEF.txt",
                      _prompt_to_open]:
        if os.path.exists(text_file):
            try:
                if platform.system() == "Windows":
                    os.startfile(text_file)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", text_file])
                else:
                    subprocess.call(["xdg-open", text_file])
            except Exception as e:
                print(f" [!] Could not auto-open {text_file}: {e}")

    print("="*60)
    print(f"\n NEXT STEP: Cards loaded in Anki. Upload 'NOTEBOOK_PRODUCER_BRIEF.txt' and '{_prompt_to_open}' to the newly opened window.")

if __name__ == "__main__":
    run_phase5()