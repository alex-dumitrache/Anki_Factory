import config
import time
import os
import re
import sys
import json
import platform
import subprocess
import random
from collections import defaultdict
from tts_reader import speaker, build_speech_p1, clean_text


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

def interactive_curation(raw_output):
    """The Specialized Veto Interface - Hacker Edition v4.0."""
    # THE MASTER SIPHON (v2.9 Standard - Armor Plated)
    # Target ALL <final_inventory> tags to isolate the Dashboard from the Audit Ledger
    master_matches = re.findall(r"<final_inventory>(.*?)</final_inventory>", raw_output, re.DOTALL)
    
    if master_matches:
        # Join all captured stream zones together into one massive data block
        data_zone = "\n".join(master_matches)
    else:
        print(" [!] WARNING: <final_inventory> tag not found. Falling back to fuzzy capture.")
        data_zone = raw_output

    # 1. Capture the Context
    context_match = re.search(r"<context>.*?</context>", data_zone, re.DOTALL)
    context_xml = context_match.group(0) if context_match else ""

    # 2. Sequential Conveyor Loop (Preserves Timeline)
    entries = list(re.finditer(r"<entry\s+zone=[\"\'](.*?)[\"\'][\s\S]*?</entry>", data_zone))
    approved_xml = []
    
    green_count = sum(1 for m in entries if m.group(1).upper() == "GREEN")
    total_review = len(entries) - green_count
    veto_count = 0
    denied_count = 0
    current_review_idx = 0
    accept_all = False

    type_labels = {
        "DEBT": "Missing Exam Fact",
        "BRIDGE": "Terminology Bridge",
        "SUGGESTION": "Bonus Card",
        "CORRECTION": "Lecturer Error Fix",
        "HANDS_ON": "CLI / Shortcut",
        "LADDER": "Silent Intro",
        "SILENT_INTRO": "Deferred Topic",
    }

    non_green_entries = [m for m in entries if m.group(1).upper() != "GREEN"]
    green_entries = [m for m in entries
                     if m.group(1).upper() == "GREEN"]
    green_approved_set = set()

    if non_green_entries:
        type_display_p1 = {
            'DEBT':        '🟦 Missing Exam Fact',
            'BRIDGE':      '🌉 Terminology Bridge',
            'SUGGESTION':  '💡 Unclaimed Gold (Ref B Confirmed)',
            'SURPLUS':     '🌟 Unclaimed Gold (Lecturer Surplus)',
            'HANDS_ON':    '⌨️  CLI / Shortcut',
            'SILENT_INTRO':'🟨 Deferred Topic',
            'CORRECTION':  '⚠️  Lecturer Error Fix',
            'LADDER':      '📶 Silent Intro',
        }
        BLUE_TYPES_SET = {'DEBT', 'BRIDGE', 'SUGGESTION', 'SURPLUS', 'HANDS_ON'}

        # Group non-GREEN entries by type into display buckets (7-tuple)
        buckets_p1 = defaultdict(list)
        for i, match in enumerate(non_green_entries, 1):
            entry_xml = match.group(0)
            type_attr = re.search(r'type="(.*?)"', entry_xml)
            type_txt = (type_attr.group(1).strip() if type_attr else 'UNKNOWN')
            concept = re.search(r'<concept>(.*?)</concept>', entry_xml, re.DOTALL)
            reason = re.search(
                r'<(?:reason|lecturer_description)>(.*?)</(?:reason|lecturer_description)>',
                entry_xml, re.DOTALL)
            prov = re.search(
                r'<provisional_front>(.*?)</provisional_front>',
                entry_xml, re.DOTALL
            )
            prov_back = re.search(
                r'<provisional_back>(.*?)</provisional_back>',
                entry_xml, re.DOTALL
            )
            concept_txt = (concept.group(1).strip() if concept else '???')
            reason_txt = (reason.group(1).strip() if reason else '')
            prov_txt = (
                prov.group(1).strip()
                if prov and prov.group(1).strip()
                else "No preview generated"
            )
            prov_back_txt = prov_back.group(1).strip() if prov_back else ""
            label = type_display_p1.get(type_txt, f'🔷 {type_txt}')
            buckets_p1[label].append((i, match, concept_txt, reason_txt, prov_txt, prov_back_txt, type_txt))

        # Split by Ref-B provenance (Chief-Architect reorder 2026-08-31): SUGGESTION/DEBT
        # are the only exam-CONFIRMED types -> reviewed LAST, one-by-one. SURPLUS/BRIDGE/HANDS_ON
        # -> reviewed FIRST, one-by-one. Everything else (SILENT_INTRO/CORRECTION/LADDER + any
        # unknown type) -> reviewed FIRST, in bulk.
        REFB_TYPES = {'SUGGESTION', 'DEBT'}
        UNCONF_INDIV_TYPES = {'SURPLUS', 'BRIDGE', 'HANDS_ON'}
        refb_buckets = {}
        unconf_indiv_buckets = {}
        unconf_bulk_buckets = {}
        for label, items in buckets_p1.items():
            _t = items[0][6] if items else ''
            if _t in REFB_TYPES:
                refb_buckets[label] = items
            elif _t in UNCONF_INDIV_TYPES:
                unconf_indiv_buckets[label] = items
            else:
                unconf_bulk_buckets[label] = items

        # ── BLUE ZONE: auto-start individual review ───────────────────
        def review_individually(flat_list, header):
            idx = 0
            bulk_mode = False
            accept_all = False
            reject_count = 0
            while idx < len(flat_list) and not bulk_mode:
                if accept_all:
                    _, _, _m, _, _, _, _ = flat_list[idx]
                    approved_xml.append(_m.group(0))
                    idx += 1
                    continue
                label, num, match, concept_txt, reason_txt, prov_txt, prov_back_txt = flat_list[idx]
                progress_blue = f"[{header} {idx + 1}/{len(flat_list)}] {label}"
                speech_str_s1 = build_speech_p1(prov_txt)
                speaker.play(speech_str_s1)
                if prov_back_txt and reason_txt:
                    speaker.prefetch(clean_text(prov_back_txt + ". " + reason_txt))
                elif prov_back_txt:
                    speaker.prefetch(clean_text(prov_back_txt))
                elif reason_txt:
                    speaker.prefetch(clean_text(reason_txt))
                for _delta in range(1, 4):
                    if idx + _delta < len(flat_list):
                        _, _, _, _, _rt_ah, _pt_ah, _pbt_ah = flat_list[idx + _delta]
                        speaker.prefetch(build_speech_p1(_pt_ah))
                        if _pbt_ah and _rt_ah:
                            speaker.prefetch(clean_text(_pbt_ah + ". " + _rt_ah))
                        elif _pbt_ah:
                            speaker.prefetch(clean_text(_pbt_ah))
                        elif _rt_ah:
                            speaker.prefetch(clean_text(_rt_ah))
                config.clear_screen()
                print_centered_vertical(progress_blue + "\n\n" + prov_txt)
                while True:
                    choice = input(" [?] (ENTER: Reveal | R: Reject | A: Accept All | P: Replay | B: Bulk) >> ").strip().lower()
                    if choice == 'p':
                        speaker.stop(); speaker.play(speech_str_s1); continue
                    speaker.stop()
                    break
                if choice == 'r':
                    reject_count += 1
                    idx += 1
                    continue
                elif choice == 'a':
                    approved_xml.append(match.group(0))
                    accept_all = True
                    idx += 1
                    continue
                elif choice == 'b':
                    bulk_mode = True
                    break
                if prov_back_txt and reason_txt:
                    speech_str_s2 = clean_text(prov_back_txt + ". " + reason_txt)
                elif prov_back_txt:
                    speech_str_s2 = clean_text(prov_back_txt)
                else:
                    speech_str_s2 = clean_text(reason_txt) if reason_txt else ""
                speaker.play(speech_str_s2)
                config.clear_screen()
                if prov_back_txt and reason_txt:
                    back_display = f"\u25b6 {prov_back_txt}\n\n{reason_txt}"
                elif prov_back_txt:
                    back_display = f"\u25b6 {prov_back_txt}"
                else:
                    back_display = reason_txt or "\u2014 No logic text \u2014"
                print_centered_vertical(progress_blue + "\n\n" + prov_txt, back_text=back_display)
                while True:
                    choice2 = input(" [?] (ENTER: Keep | R: Reject | A: Accept All | P: Replay | B: Bulk) >> ").strip().lower()
                    if choice2 == 'p':
                        speaker.stop(); speaker.play(speech_str_s2); continue
                    speaker.stop()
                    break
                if choice2 == 'r':
                    reject_count += 1
                elif choice2 == 'a':
                    approved_xml.append(match.group(0))
                    accept_all = True
                elif choice2 == 'b':
                    bulk_mode = True
                    break
                else:
                    approved_xml.append(match.group(0))
                idx += 1

            if bulk_mode and not accept_all:
                remaining = flat_list[idx:]
                if remaining:
                    print("\n" + "=" * 60)
                    print(f" {header} \u2014 Bulk Review (remaining)".center(60))
                    print("=" * 60)
                    bulk_indexed = {}
                    for _j, (_lbl, _num, _m, _ct, _rt, _pt, _pbt) in enumerate(remaining, 1):
                        print(f"\n  \u2500\u2500 {_lbl} \u2500\u2500")
                        print(f"  [{_j:2d}] {_ct}")
                        print(f"       \u2514\u2500 Preview: {_pt}")
                        if _pbt:
                            print(f"       \u2514\u2500 Answer: {_pbt}")
                        if _rt:
                            print(f"       \u2514\u2500 Reason: {_rt}")
                        bulk_indexed[_j] = _m
                    print("\n" + "=" * 60)
                    raw_bb = input(" [?] Reject numbers (e.g. 3,7) or ENTER to keep all >> ").strip()
                    try:
                        bb_reject = set(int(x.strip()) for x in raw_bb.split(',') if x.strip().isdigit())
                    except ValueError:
                        bb_reject = set()
                    for _j, _m in bulk_indexed.items():
                        if _j not in bb_reject:
                            approved_xml.append(_m.group(0))
                        else:
                            reject_count += 1
            return reject_count, accept_all

        # Group 1a -- UNCONFIRMED, one-by-one (SURPLUS / BRIDGE / HANDS_ON)
        unconf_flat = []
        for _lbl, _items in unconf_indiv_buckets.items():
            for (_num, _match, _ct, _rt, _pt, _pbt, _tt) in _items:
                unconf_flat.append((_lbl, _num, _match, _ct, _rt, _pt, _pbt))
        accept_all_unconf = False
        if unconf_flat:
            _rc_u, accept_all_unconf = review_individually(unconf_flat, "UNCONFIRMED")
            denied_count += _rc_u
        # Group 1b -- unconfirmed BULK (deferred / correction / silent-intro), moved BEFORE green
        if unconf_bulk_buckets:
            if accept_all_unconf:
                for _lbl, _items in unconf_bulk_buckets.items():
                    for _num, _m, _ct, _rt, _pt, _pbt, _tt in _items:
                        approved_xml.append(_m.group(0))
            else:
                try:
                    config.clear_screen()
                except Exception:
                    pass
                print("=" * 60)
                print(" YELLOW ZONE — Type numbers to REJECT".center(60))
                print(" Default: KEEP ALL. ENTER accepts everything.".center(60))
                print("=" * 60)
                yellow_entries_indexed = {}
                _yj = 0
                for label, items in unconf_bulk_buckets.items():
                    print(f"\n  ── {label} ──")
                    for num, match, concept_txt, reason_txt, prov_txt, prov_back_txt, type_txt in items:
                        _yj += 1
                        print(f"  [{_yj:2d}] {concept_txt}")
                        print(f"       └─ Preview: {prov_txt}")
                        if prov_back_txt:
                            print(f"       └─ Answer: {prov_back_txt}")
                        if reason_txt:
                            print(f"       └─ Reason: {reason_txt}")
                        yellow_entries_indexed[_yj] = match
                print("\n" + "=" * 60)
                raw_y = input(
                    " [?] Reject numbers (e.g. 3,7), 'R' to Review Individually, or ENTER to keep all >> ").strip()
                if raw_y.strip().lower() == 'r':
                    accept_all_yng = False
                    yellow_flat = [(ct, rt, pt) for _, itms in unconf_bulk_buckets.items()
                                   for _, _, ct, rt, pt, pbt, tt in itms]
                    _yf_idx = 0
                    for label, items in unconf_bulk_buckets.items():
                        for num, match, concept_txt, reason_txt, prov_txt, prov_back_txt, type_txt in items:
                            if accept_all_yng:
                                approved_xml.append(match.group(0))
                                _yf_idx += 1
                                continue
                            speech_str_s1 = build_speech_p1(prov_txt)
                            speaker.play(speech_str_s1)
                            speaker.prefetch(clean_text(reason_txt))
                            for _delta in range(1, 4):
                                if _yf_idx + _delta < len(yellow_flat):
                                    _, _yr_ah, _yp_ah = yellow_flat[_yf_idx + _delta]
                                    speaker.prefetch(build_speech_p1(_yp_ah))
                                    speaker.prefetch(clean_text(_yr_ah))
                            config.clear_screen()
                            print_centered_vertical(label + "\n\n" + prov_txt)
                            while True:
                                choice = input(
                                    " [?] (ENTER: Reveal | R: Reject | A: Accept All | P: Replay) >> "
                                ).strip().lower()
                                if choice == 'p':
                                    speaker.stop(); speaker.play(speech_str_s1); continue
                                speaker.stop()
                                break
                            if choice == 'r':
                                denied_count += 1
                                _yf_idx += 1
                                continue
                            elif choice == 'a':
                                approved_xml.append(match.group(0))
                                accept_all_yng = True
                                _yf_idx += 1
                                continue
                            speech_str_s2 = clean_text(reason_txt)
                            speaker.play(speech_str_s2)
                            config.clear_screen()
                            back_display = reason_txt if reason_txt else "— No logic text —"
                            print_centered_vertical(label + "\n\n" + prov_txt, back_text=back_display)
                            while True:
                                choice2 = input(
                                    " [?] (ENTER: Keep | R: Reject | A: Accept All | P: Replay) >> "
                                ).strip().lower()
                                if choice2 == 'p':
                                    speaker.stop(); speaker.play(speech_str_s2); continue
                                speaker.stop()
                                break
                            if choice2 == 'r':
                                denied_count += 1
                            elif choice2 == 'a':
                                approved_xml.append(match.group(0))
                                accept_all_yng = True
                            else:
                                approved_xml.append(match.group(0))
                            _yf_idx += 1
                else:
                    try:
                        reject_set_y = set(
                            int(x.strip()) for x in raw_y.split(',')
                            if x.strip().isdigit()
                        )
                    except ValueError:
                        reject_set_y = set()
                    if reject_set_y:
                        print(f" [✓] Rejecting: {sorted(reject_set_y)}")
                    for _yj, match in yellow_entries_indexed.items():
                        if _yj not in reject_set_y:
                            approved_xml.append(match.group(0))
                        else:
                            denied_count += 1

    # ── GREEN ZONE: bulk accept / individual review ───────────────────
    if green_entries:
        config.clear_screen()
        print("=" * 60)
        print(" 🟩 YOUR EXPLICIT TRIGGERS — Type numbers to REJECT"
              .center(60))
        print(" Default: KEEP ALL. ENTER accepts everything."
              .center(60))
        print("=" * 60)

        _green_data = []
        for i, match in enumerate(green_entries, 1):
            entry_xml = match.group(0)
            concept = re.search(
                r"<concept>(.*?)</concept>", entry_xml, re.DOTALL)
            concept_txt = concept.group(1).strip() if concept else "???"
            trigger_match = re.search(r'<trigger_text>(.*?)</trigger_text>',
                                      entry_xml, re.DOTALL)
            trigger_txt = trigger_match.group(1).strip() if trigger_match else None
            label = concept_txt  # M2: provisional_front is internal scaffolding for Phase 2 M3 / Phase 3 M6, NOT a VetoGate-1 human preview for GREEN entries.
            _green_data.append((i, label, trigger_txt))

        _trigger_groups = {}
        _trigger_order = []
        for i, label, trigger_txt in _green_data:
            key = trigger_txt or "— Implicit / No trigger text —"
            if key not in _trigger_groups:
                _trigger_groups[key] = []
                _trigger_order.append(key)
            _trigger_groups[key].append((i, label))

        for trigger in _trigger_order:
            _branch = _trigger_groups[trigger]
            print(f'\n  Trigger: "{trigger}"')
            for idx, (i, label) in enumerate(_branch):
                connector = "└─" if idx == len(_branch) - 1 else "├─"
                print(f"    {connector} [{i}] {label}")

        print("=" * 60)
        raw_green = input(
            " [?] Reject numbers (e.g. 2,5), 'R' to Review Individually, or ENTER to keep all >> "
        ).strip()
        if raw_green.strip().lower() == 'r':
            green_accept_all = False
            for i, label, trigger_txt in _green_data:
                if green_accept_all:
                    match = green_entries[i - 1]
                    approved_xml.append(match.group(0))
                    green_approved_set.add(match)
                    continue
                speech_str_s1 = build_speech_p1(label)
                speaker.play(speech_str_s1)
                speaker.prefetch(clean_text(trigger_txt))
                for _k in range(3):
                    if i + _k < len(_green_data):
                        _, _nl, _nt = _green_data[i + _k]
                        speaker.prefetch(build_speech_p1(_nl))
                        speaker.prefetch(clean_text(_nt or ""))
                config.clear_screen()
                progress_str = f"[GREEN {i}/{len(green_entries)}] 🟩 USER TRIGGER"
                print_centered_vertical(label, progress_str=progress_str)
                while True:
                    choice = input(
                        " [?] (ENTER: Reveal | R: Reject | A: Accept All | P: Replay) >> "
                    ).strip().lower()
                    if choice == 'p':
                        speaker.stop(); speaker.play(speech_str_s1); continue
                    speaker.stop()
                    break
                if choice == 'r':
                    denied_count += 1
                    continue
                elif choice == 'a':
                    match = green_entries[i - 1]
                    approved_xml.append(match.group(0))
                    green_approved_set.add(match)
                    green_accept_all = True
                    continue
                speech_str_s2 = clean_text(trigger_txt)
                speaker.play(speech_str_s2)
                config.clear_screen()
                trigger_display = trigger_txt if trigger_txt else "— No trigger text —"
                print_centered_vertical(label, back_text=f"Trigger: {trigger_display}", progress_str=progress_str)
                while True:
                    choice2 = input(
                        " [?] (ENTER: Keep | R: Reject | A: Accept All | P: Replay) >> "
                    ).strip().lower()
                    if choice2 == 'p':
                        speaker.stop(); speaker.play(speech_str_s2); continue
                    speaker.stop()
                    break
                if choice2 == 'r':
                    denied_count += 1
                elif choice2 == 'a':
                    match = green_entries[i - 1]
                    approved_xml.append(match.group(0))
                    green_approved_set.add(match)
                    green_accept_all = True
                else:
                    match = green_entries[i - 1]
                    approved_xml.append(match.group(0))
                    green_approved_set.add(match)
        else:
            try:
                green_reject_set = set(
                    int(x.strip()) for x in raw_green.split(",")
                    if x.strip().isdigit()
                )
            except ValueError:
                green_reject_set = set()
            if green_reject_set:
                print(f" [✓] Rejecting GREEN: {sorted(green_reject_set)}")

            for i, match in enumerate(green_entries, 1):
                if i not in green_reject_set:
                    approved_xml.append(match.group(0))
                    green_approved_set.add(match)
                else:
                    denied_count += 1

    if non_green_entries:
        # -- REF B CONFIRMED (SUGGESTION / DEBT) -- reviewed LAST, one-by-one, exam-official --
        refb_flat = []
        for _lbl, _items in refb_buckets.items():
            for (_num, _match, _ct, _rt, _pt, _pbt, _tt) in _items:
                refb_flat.append((_lbl, _num, _match, _ct, _rt, _pt, _pbt))
        if refb_flat:
            _rc_r, _aa_r = review_individually(refb_flat, "REF B CONFIRMED")
            denied_count += _rc_r

        # Build summary and return early
        veto_count = len(approved_xml) - len(green_approved_set)
        config.clear_screen()
        print("="*60)
        print(" [!] CURATION SUMMARY ".center(60, "#"))
        print("="*60)
        print(f" [+] Total Entries Found : {len(entries)}")
        print(f" [+] Green (Confirmed)   : {len(green_approved_set)}")
        print(f" [+] Blue/Yellow Kept    : {veto_count}")
        print(f" [-] Manually Rejected   : {denied_count}")
        print("-" * 60)
        print(f" [*] Final Baton Count   : {len(approved_xml)}")
        print("="*60)

        if not approved_xml:
            return None
        return f"{context_xml}\n\n" + "\n\n".join(approved_xml)

    # --- THE CURATION SUMMARY ---
    config.clear_screen()
    print("="*60)
    print(" [!] CURATION SUMMARY ".center(60, "#"))
    print("="*60)
    print(f" [+] Total Entries Found : {len(entries)}")
    print(f" [+] Green (Confirmed)   : {len(green_approved_set)}")
    print(f" [+] Blue/Yellow Kept    : {veto_count}")
    print(f" [-] Manually Rejected   : {denied_count}")
    print("-" * 60)
    print(f" [*] Final Baton Count   : {len(approved_xml)}")
    print("="*60)
    
    if not approved_xml:
        return None
    return f"{context_xml}\n\n" + "\n\n".join(approved_xml)

def merge_xml_patch(base_inventory, patch_output):
    """Merges a surgical patch (Pass 2 output) into the base inventory (Pass 1 output)."""
    def _norm(text):
        text = re.sub(r'\*+', '', text)
        text = text.lower()
        text = ' '.join(text.split())
        return text.strip()

    # 1. Parse base_inventory
    base_context_m = re.search(r'<context>.*?</context>', base_inventory, re.DOTALL)
    base_context = base_context_m.group(0) if base_context_m else ''

    base_entry_list = re.findall(r'<entry\b[^>]*>.*?</entry>', base_inventory, re.DOTALL)
    base_dict = {}
    for entry in base_entry_list:
        zone_m = re.search(r'zone=["\']([^"\']*)["\']', entry)
        type_m = re.search(r'type=["\']([^"\']*)["\']', entry)
        concept_m = re.search(r'<concept>(.*?)</concept>', entry, re.DOTALL)
        key = (
            _norm(zone_m.group(1)) if zone_m else '',
            _norm(type_m.group(1)) if type_m else '',
            _norm(concept_m.group(1)) if concept_m else '',
        )
        base_dict[key] = entry

    # 2. Parse patch_output — extract from <final_inventory> if present
    fi_m = re.search(r'<final_inventory>(.*?)</final_inventory>', patch_output, re.DOTALL)
    patch_text = fi_m.group(1).strip() if fi_m else patch_output

    patch_entries = re.findall(r'<entry\b[^>]*>.*?</entry>', patch_text, re.DOTALL)
    kill_signals = re.findall(r'\[\[KILL_ENTRY\]\].*', patch_text)

    if not patch_entries and not kill_signals:
        print(' [P1 MERGE: ZERO PATCHES — BASE RETURNED UNCHANGED]')
        return base_inventory

    # 3. Extract context from patch (replaces base context)
    patch_context_m = re.search(r'<context>.*?</context>', patch_text, re.DOTALL)
    new_context = patch_context_m.group(0) if patch_context_m else base_context

    # 4. Process KILL signals
    killed = 0
    for signal in kill_signals:
        zone_m = re.search(r'zone=["\']([^"\']*)["\']', signal)
        type_m = re.search(r'type=["\']([^"\']*)["\']', signal)
        concept_m = re.search(r'concept=["\']([^"\']*)["\']', signal)
        if not concept_m:
            concept_m = re.search(r'<concept>(.*?)</concept>', signal, re.DOTALL)
        key = (
            _norm(zone_m.group(1)) if zone_m else '',
            _norm(type_m.group(1)) if type_m else '',
            _norm(concept_m.group(1)) if concept_m else '',
        )
        if key in base_dict:
            del base_dict[key]
            print(f' [P1 KILL] {key}')
            killed += 1

    # 5. Process patch entries — MODIFY existing or INJECT new
    modified = 0
    injected = 0
    for entry in patch_entries:
        zone_m = re.search(r'zone=["\']([^"\']*)["\']', entry)
        type_m = re.search(r'type=["\']([^"\']*)["\']', entry)
        concept_m = re.search(r'<concept>(.*?)</concept>', entry, re.DOTALL)
        key = (
            _norm(zone_m.group(1)) if zone_m else '',
            _norm(type_m.group(1)) if type_m else '',
            _norm(concept_m.group(1)) if concept_m else '',
        )
        if key in base_dict:
            base_dict[key] = entry
            print(f' [P1 MODIFY] {key}')
            modified += 1
        else:
            base_dict[key] = entry
            print(f' [P1 INJECT] {key}')
            injected += 1

    # 6. Reconstruct
    all_entries = '\n\n'.join(base_dict.values())
    result = f'<final_inventory>\n{new_context}\n\n{all_entries}\n</final_inventory>'

    # 7. Log summary
    print(f' P1 MERGE COMPLETE: [{modified}] modified, [{injected}] injected, [{killed}] killed. Final entry count: [{len(base_dict)}]')

    return result


def _run_casting_director(clean_transcript):
    """Casting Director + NLM file opens.
    Called at the very end of Phase 1, after the baton is saved.
    The user is already at the computer at this point.
    """
    # ==========================================
    # CASTING DIRECTOR
    # ==========================================
    try:
        # -- GATE: decide mode before any file checks or API calls --
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
            else:
                try:
                    from pairings import PAIRINGS as _cd_PAIRINGS, FLAVOR_SEEDS, DIALECTS
                except (SyntaxError, ImportError) as _cd_e:
                    print(f" [!] Could not import pairings.py ({_cd_e}) -- skipping Casting Director.")
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

                    with open("NotebookLM_Prompt_BETA.txt", "r", encoding="utf-8") as _cdf:
                        _cd_beta = _cdf.read()

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
                            "\n\nTRANSCRIPT:\n" + clean_transcript
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
                            "TRANSCRIPT:\n" + clean_transcript
                        )
                        for _cd_attempt in range(2):
                            _cd_raw = config.call_llm(_cd_generator_prompt,
                                                      context_header="CASTING DIRECTOR | GENERATOR")
                            _cd_res = _cd_parse(_cd_raw, _cd_gen_fields)
                            if _cd_res and _cd_validate_pairing(_cd_res)[0]:
                                _cd_generated = _cd_res
                                break

                    # -- CHOOSE PAIRING --
                    if _cd_gate == "L":
                        # Skip display entirely, drop straight into library browser
                        _cd_choice = "M"
                    else:
                        # [A] path: show AI results and let user pick
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

                    # -- LIBRARY BROWSER (M / L path) --
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

                    # -- TEMPLATE SUBSTITUTION --
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

    for _txt_file in ["NOTEBOOK_PRODUCER_BRIEF.txt", _prompt_to_open]:
        if not os.path.exists(_txt_file):
            if _txt_file == _prompt_to_open:
                print(f" [!] WARNING: '{_txt_file}' missing from root directory.")
            continue
        try:
            if platform.system() == "Windows":
                os.startfile(_txt_file)
            elif platform.system() == "Darwin":
                subprocess.call(["open", _txt_file])
            else:
                subprocess.call(["xdg-open", _txt_file])
            print(f" [+] {_txt_file} opened.")
        except Exception as _e:
            print(f" [!] Could not auto-open {_txt_file}: {_e}")


def _get_next_video_suggestion():
    """Return next video number based on Archive folder contents.

    Reads Archive/, strips any _N re-run suffix from folder names,
    finds the highest plain integer, and returns that integer + 1.
    Returns None if Archive/ does not exist, contains no integer-named
    folders, or if os.listdir raises any exception (permission, etc.).
    """
    try:
        archive_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Archive")
        if not os.path.exists(archive_dir):
            return None
        max_num = None
        for name in os.listdir(archive_dir):
            base = name.split("_")[0]      # strips "_2", "_3" re-run suffixes
            if base.isdigit():
                num = int(base)
                if max_num is None or num > max_num:
                    max_num = num
        return (max_num + 1) if max_num is not None else None
    except Exception:
        return None


def run_phase1():
    print(" [!] PHASE 1 SPECIALIST: THE HARVESTER (VETO STATION)")
    print("-" * 50)

    # Step A: Dynamic Input — auto-load from bridge when Phase 1 is being skipped OR resumed mid-flow.
    # Bridge holds the video_num from the prior run — no point re-asking on resume.
    _p1_skip = (1 in config.SKIP_PHASES_SET) or (config.RESUME_PHASE == 1)
    if _p1_skip and os.path.exists("notebook_context_bridge.txt"):
        with open("notebook_context_bridge.txt", "r", encoding="utf-8") as _bridge_f:
            video_num = _bridge_f.readline().strip()
        if video_num:
            print(f" [>] Video number auto-loaded from bridge: '{video_num}'")
        else:
            print(" [!] Bridge file has no video number — falling back to prompt.")
            _p1_skip = False
    else:
        video_num = ""
    if not _p1_skip or not video_num:
        _suggestion = _get_next_video_suggestion()
        print("\n" + "!" * 60)
        print(" ATTENTION: YOUR INTERVENTION IS REQUIRED ".center(60, "!"))
        print("!" * 60 + "\n")
        if _suggestion is not None:
            print(f" [>] Last completed run detected → suggesting video {_suggestion}")
            _raw = input(f" [?] Enter Video Title or Number [{_suggestion}]: ").strip()
            video_num = _raw if _raw else str(_suggestion)
        else:
            video_num = input(" [?] Enter Video Title or Number: ").strip()
    if not video_num:
        print(" [X] Error: Video number cannot be empty.")
        sys.exit(1)

    # Step B: Clean Transcript
    if not os.path.exists("raw_chat.txt"):
        print(" [X] Error: 'raw_chat.txt' missing from folder!")
        sys.exit(1)

    with open("raw_chat.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Staleness check: alert if raw_chat.txt unchanged from last successful run
    if os.path.exists(".raw_chat_count"):
        try:
            with open(".raw_chat_count", "r") as _f:
                _prev_chars = int(_f.read().strip())
            _curr_chars = len(raw_text)
            if _prev_chars == _curr_chars:
                _vid = "unknown"
                if os.path.exists(".last_video_id"):
                    with open(".last_video_id", "r") as _f:
                        _vid = _f.read().strip()
                print(f"\n [!] raw_chat.txt unchanged from last successful run (video {_vid}, {_curr_chars} chars).")
                print("     Did you forget to paste a new transcript?")
                if input(" Proceed anyway? [y/N]: ").strip().lower() != 'y':
                    print(" [X] Aborted. Update raw_chat.txt and re-run.")
                    sys.exit(0)
        except Exception:
            pass

    # Regex Block Deletion: Vaporize the entire Stenographer Setup Block
    # Targets from the opening instruction line through the final "Received." acknowledgement line
    transcript = re.sub(
        r"You are operating in transcription-only mode.*?continue responding with .Received\.",
        "",
        raw_text,
        flags=re.IGNORECASE | re.DOTALL
    )
    # Strip standalone conversational artifacts globally
    transcript = re.sub(r"^\s*Received\.?\s*$", "", transcript, flags=re.IGNORECASE | re.MULTILINE)
    transcript = re.sub(r"^\s*ChatGPT said:\s*$", "", transcript, flags=re.IGNORECASE | re.MULTILINE)
    transcript = re.sub(r"^\s*You said:\s*$", "", transcript, flags=re.IGNORECASE | re.MULTILINE)
    transcript = transcript.strip()

    # Persistence: Create context bridge for NotebookLM fork
    with open("notebook_context_bridge.txt", "w", encoding="utf-8") as f:
        f.write(f"{video_num}\n{transcript}")

    # ==========================================
    # NOTEBOOK LM: PROVISIONAL PRODUCER BRIEF
    # ==========================================
    print("\n [>] Generating Provisional NotebookLM Producer Brief...")

    _trig_re   = re.compile(r'^create\s+(?:a\s+)?flash\w*\s+(.*)', re.IGNORECASE)
    _filler_re = re.compile(r'^(?:on\s+about|about|saying\s+that|saying)\s+', re.IGNORECASE)

    _trigger_topics = []
    _clean_lines    = []
    for _line in transcript.splitlines():
        _m = _trig_re.match(_line.strip())
        if _m:
            _raw = _filler_re.sub('', _m.group(1).strip()).rstrip('.')
            if _raw:
                _trigger_topics.append(_raw[0].upper() + _raw[1:])
        else:
            _clean_lines.append(_line)
    _clean_transcript = '\n'.join(_clean_lines).strip()


    # Step C: Load Prompt Base
    if not os.path.exists("Prompts/prompt1_harvester.txt"):
        print(" [X] Error: 'Prompts/prompt1_harvester.txt' missing from folder!")
        sys.exit(1)

    with open("Prompts/prompt1_harvester.txt", "r", encoding="utf-8") as f:
        p1_base_text = f.read()

    # Inject reference library (decoupled to save Claude Code session tokens)
    _ref_lib_path = "Prompts/reference_library_p1.xml"
    if not os.path.exists(_ref_lib_path):
        print(f" [X] Error: '{_ref_lib_path}' missing -- cannot inject reference library.")
        sys.exit(1)
    with open(_ref_lib_path, "r", encoding="utf-8") as f:
        _reference_library = f.read()
    p1_base_text = p1_base_text.replace("{{REFERENCE_LIBRARY}}", _reference_library)

    # Define exact placeholders from Prompt 1
    target_vid_placeholder = "[👉PASTE VIDEO NUMBER OR TITLE HERE👈]"
    target_transcript_placeholder = "[👉PASTE RAW TRANSCRIPT AND TRIGGERS HERE👈]"
    target_audit_placeholder = "[👉LEAVE EMPTY FOR MODE1. PASTE FAILED XML OUTPUT HERE FOR MODE2👈]"

    # ==========================================
    # Step D: ITERATIVE REFINEMENT LOOP (2 PASSES)
    # ==========================================
    current_payload = ""
    base_payload = ""
    total_passes = 2

    for pass_num in range(1, total_passes + 1):
        if pass_num == 1:
            print(f"\n [>] PASS 1: Generating Initial Harvest (Mode 1)...")
            prompt = p1_base_text.replace(target_vid_placeholder, video_num)\
                                 .replace(target_transcript_placeholder, transcript)\
                                 .replace(target_audit_placeholder, "")
        else:
            print(f" [>] PASS {pass_num}: Internal Forensic Audit (Mode 2)...")
            # Mode 2: Ingest the PREVIOUS pass output into <audit_target>
            # Keep the SAME video_num and transcript as static anchors
            prompt = p1_base_text.replace(target_vid_placeholder, video_num)\
                                 .replace(target_transcript_placeholder, transcript)\
                                 .replace(target_audit_placeholder, current_payload)

        if pass_num == 1:
            current_payload = config.call_llm(prompt, context_header=f"PHASE 1 | PASS {pass_num}", phase="P1", pass_num=pass_num)
        else:
            raw_llm_output = config.call_llm(prompt, context_header=f"PHASE 1 | PASS {pass_num}", phase="P1", pass_num=pass_num)
            log_name = f"forensic_raw_p1_pass{pass_num}.txt"
            with open(log_name, "w", encoding="utf-8") as f:
                f.write(f"### FORENSIC LOG: PASS {pass_num} | MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + raw_llm_output)
            current_payload = merge_xml_patch(base_payload, raw_llm_output)

        if not current_payload:
            print(f" [X] Fatal Error in Pass {pass_num}. Aborting.")
            sys.exit(1)

        if pass_num == 1:
            # Save individual forensic logs for traceability
            log_name = f"forensic_raw_p1_pass{pass_num}.txt"
            with open(log_name, "w", encoding="utf-8") as f:
                f.write(f"### FORENSIC LOG: PASS {pass_num} | MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + current_payload)
            base_payload = current_payload
        else:
            with open("forensic_merged_p1.txt", "w", encoding="utf-8") as f:
                f.write(f"### FORENSIC LOG: MERGED STATE | PASS {pass_num} | MODEL: {config.LAST_ACTIVE_MODEL}\n" + "="*60 + "\n" + current_payload)

    # ==========================================
    # Step E: Interactive Curation
    # ==========================================
    entry_count = len(re.findall(r"<entry\s+zone=", current_payload))
    if config.veto_gate_needs_notification(1):
        config.send_ntfy(
            title="🗂️ P1 Veto Gate Ready",
            message=f"{entry_count} entries awaiting curation. Switch to your terminal.",
        )
        config.ui_alert("ATTENTION: YOUR INTERVENTION IS REQUIRED")
    curated_payload = interactive_curation(current_payload)

    if curated_payload:
        # SANITIZATION: Purge EOF markers and Anki-breaking backticks
        curated_payload = re.sub(r"\[EOF.*?\]", "", curated_payload, flags=re.IGNORECASE)
        curated_payload = curated_payload.replace("```", "").replace("`", "").strip()

        # BATON STRIP: Zone-aware — preserve provisionals on GREEN INTENT entries; strip both tags from all others.
        # Uses re.sub with a callable to preserve the <context> block and inter-entry whitespace.
        # M2: GREEN INTENT entries must carry both <provisional_front> and <provisional_back> through to Phase 2
        # (M3 Carry-Through). Non-GREEN-INTENT entries carry them only as display-only scaffolding for VetoGate-1
        # (which has already executed by this point).
        _pv_preserved = [0]
        _pv_stripped = [0]

        def _zone_aware_strip(m):
            entry_xml = m.group(0)
            zone_m = re.search(r'zone=["\']([^"\']*)["\']', entry_xml)
            etype_m = re.search(r'type=["\']([^"\']*)["\']', entry_xml)
            zone = zone_m.group(1).upper() if zone_m else ""
            etype = etype_m.group(1).upper() if etype_m else ""
            if zone == "GREEN" and etype == "INTENT":
                _pv_preserved[0] += 1
                return entry_xml
            cleaned = re.sub(r'<provisional_front>.*?</provisional_front>', '', entry_xml, flags=re.DOTALL)
            cleaned = re.sub(r'<provisional_back>.*?</provisional_back>', '', cleaned, flags=re.DOTALL)
            if cleaned != entry_xml:
                _pv_stripped[0] += 1
            return cleaned

        curated_payload = re.sub(
            r'<entry\b[^>]*>.*?</entry>',
            _zone_aware_strip,
            curated_payload,
            flags=re.DOTALL
        )
        print(f" [+] BATON STRIP: preserved provisionals on {_pv_preserved[0]} GREEN INTENT entries; stripped from {_pv_stripped[0]} other entries.")

        # Save the \"Cleaned Baton\" for the future Phase 2
        with open("baton_p1_to_p2.xml", "w", encoding="utf-8") as f:
            f.write(curated_payload)
        print("\n [+] TEST SUCCESS!")
        print(f" [+] User-curated XML ready in: {os.path.abspath('baton_p1_to_p2.xml')}")

        # ==========================================
        # NOTEBOOK LM: PROVISIONAL PRODUCER BRIEF
        # ==========================================
        # Reads the curated baton (just written above) and emits zone+type-aware
        # Director's Cues for every approved entry — not just regex triggers.
        print(" [>] Generating NotebookLM Producer Brief from curated baton...")

        with open("baton_p1_to_p2.xml", "r", encoding="utf-8") as _bf:
            _baton_xml = _bf.read()

        # Extract context header
        _ctx_video = re.search(r"<video_id>(.*?)</video_id>", _baton_xml, re.DOTALL)
        _ctx_domain = re.search(r"<domain>(.*?)</domain>", _baton_xml, re.DOTALL)
        _ctx_theme = re.search(r"<core_theme>(.*?)</core_theme>", _baton_xml, re.DOTALL)
        _video_id = _ctx_video.group(1).strip() if _ctx_video else video_num
        _domain = _ctx_domain.group(1).strip() if _ctx_domain else ""
        _core_theme = _ctx_theme.group(1).strip() if _ctx_theme else ""

        # Parse each entry block
        _baton_entries = list(re.finditer(
            r"<entry\s+zone=[\"'](.*?)[\"'][\s\S]*?</entry>",
            _baton_xml
        ))

        _brief = [
            "# 📄 THE RAW LECTURE TRANSCRIPT\n"
            "Context: This is a raw lecture transcript from a CompTIA course instructor. "
            "Use this to understand the narrative flow and tone. "
            "Refer to him as the instructor. Do NOT call him 'the source'.\n\n"
            f"<raw_transcript>\n\n{_clean_transcript}\n\n</raw_transcript>\n\n",
            f"# 🎯 PRODUCER CONTEXT\n"
            f"Video: {_video_id}\n"
            f"Domain: {_domain}\n"
            f"Core Theme: {_core_theme}\n\n",
            "<producer_notes>\n\n",
        ]

        _topic_count = 0
        for _entry_match in _baton_entries:
            _entry_xml = _entry_match.group(0)
            _zone = _entry_match.group(1).upper()
            _type_m = re.search(r'type=["\'](.*?)["\']', _entry_xml)
            _depth_m = re.search(r'depth=["\'](.*?)["\']', _entry_xml)
            _certainty_m = re.search(r'certainty=["\'](.*?)["\']', _entry_xml)
            _concept_m = re.search(r'<concept>(.*?)</concept>', _entry_xml, re.DOTALL)
            _source_m = re.search(r'<source>(.*?)</source>', _entry_xml, re.DOTALL)
            _reason_m = re.search(r'<reason>(.*?)</reason>', _entry_xml, re.DOTALL)
            _prov_back_m = re.search(r'<provisional_back>(.*?)</provisional_back>', _entry_xml, re.DOTALL)
            _trigger_m = re.search(r'<trigger_text>(.*?)</trigger_text>', _entry_xml, re.DOTALL)

            _type = (_type_m.group(1).strip().upper() if _type_m else "UNKNOWN")
            _depth = (_depth_m.group(1).strip().upper() if _depth_m else "PRIMARY")
            _certainty = (_certainty_m.group(1).strip().upper() if _certainty_m else "")
            _concept = (_concept_m.group(1).strip() if _concept_m else "???")
            _source = (_source_m.group(1).strip() if _source_m else "")
            _reason = (_reason_m.group(1).strip() if _reason_m else "")
            _prov_back = (_prov_back_m.group(1).strip() if _prov_back_m else "")
            _trigger = (_trigger_m.group(1).strip() if _trigger_m else "")

            # Tailor Director's Cue by (zone, type) pair
            if _zone == "GREEN" and _type == "INTENT":
                _cue = ("ANCHOR TOPIC — student explicitly requested. Full depth. "
                        "FORENSIC CHECK — cross-reference the raw transcript: Did Mike explicitly teach it? "
                        "THREE POSSIBLE STATES — (A) Mike taught it well: review naturally, anchoring to his "
                        "explanation and any analogy or demo. (B) Mike touched it but skipped key specs: call "
                        "it out directly. (C) Mike skipped it entirely: announce clearly, then teach from zero.")
                _focus = "🔴 ANCHOR TOPIC"
            elif _zone == "BLUE" and _type == "DEBT":
                _cue = ("MISSING EXAM FACT — Mike did NOT cover this Ref B objective. "
                        "Teach from zero; announce the gap explicitly.")
                _focus = "🟦 MISSING EXAM FACT"
            elif _zone == "BLUE" and _type == "SUGGESTION":
                _cue = ("UNCLAIMED GOLD — Mike covered this; student missed it. "
                        "Amplify the moment Mike taught it.")
                _focus = "💡 UNCLAIMED GOLD (Ref B Confirmed)"
            elif _zone == "BLUE" and _type == "SURPLUS" and _certainty == "HIGH":
                _quote_m = re.search(r'Verbatim lecturer:\s*"([^"]+)"', _reason)
                _quote = _quote_m.group(1).strip() if _quote_m else ""
                _cue = "LECTURER SURPLUS — Mike's own words. Anchor the segment on the verbatim quote."
                if _quote:
                    _cue += f' QUOTE: "{_quote}"'
                _focus = "🌟 LECTURER SURPLUS"
            elif _zone == "BLUE" and _type == "SURPLUS":
                _cue = ("FOUNDATIONAL BRIDGE — Mike was silent on this foundation. "
                        "Tutor introduces it before student can reason about parent topic.")
                _focus = "🌉 FOUNDATIONAL BRIDGE"
            else:
                _cue = f"BLUE ZONE — {_reason}" if _reason else f"BLUE ZONE — {_zone}/{_type}"
                _focus = f"🔷 {_zone}/{_type}"

            _airtime = "Full depth. Do not rush." if _depth == "PRIMARY" else "Quick mention; surface-level coverage."
            _core_fact = _prov_back if _prov_back else (_reason[:100].strip() or _concept)

            _brief.append(
                f"--- TOPIC: {_concept} ---\n"
                f"🎯 FOCUS LEVEL: {_focus}\n"
                f"⏱️  AIRTIME: {_airtime}\n"
                f"🎬 DIRECTOR'S CUE: {_cue}\n"
                f"📝 CORE FACT: {_core_fact}\n"
                + (f"📚 SOURCE: {_source}\n" if _source else "")
                + (f"💬 TRIGGER: {_trigger}\n" if _trigger else "")
                + "\n"
            )
            _topic_count += 1

        if _topic_count == 0:
            _brief.append("# [No approved entries in baton]\n\n")

        _brief.append("</producer_notes>\n")

        with open("NOTEBOOK_PRODUCER_BRIEF.txt", "w", encoding="utf-8") as _f:
            _f.write("".join(_brief))
        print(f" [+] NOTEBOOK_PRODUCER_BRIEF.txt written ({_topic_count} topic(s) detected).")

        # ── CASTING DIRECTOR + NLM FILE OPENS ─────────────────────
        # Runs after baton is saved. User is already at the computer.
        # Phase 2 starts immediately after this returns.
        _run_casting_director(_clean_transcript)

    else:
        print("\n [!] No cards were approved.")
        sys.exit(2)

if __name__ == "__main__":
    run_phase1()