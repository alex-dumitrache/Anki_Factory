import subprocess
import sys
import os
import time
import platform
import shutil
import glob
import re

def run_settings_menu(pipeline_env):
    import config as _cfg

    print("\n" + "="*60)
    print(" SESSION OVERRIDES — changes apply this session only ".center(60, "="))
    print("="*60)

    # ── SCOPE ─────────────────────────────────────────────────────
    print()
    print("   [0] Skip ALL  |  [1,3,5] Skip specific  |  [ENTER] No skip")
    q_skip = input(" Q1 — Phase Skip (read existing files instead of API): ").strip()
    if q_skip == "0":
        pipeline_env["PIPELINE_SKIP_PHASES"] = "ALL"
    elif q_skip:
        pipeline_env["PIPELINE_SKIP_PHASES"] = q_skip
    skip_all = (q_skip == "0")

    if not skip_all:

        # ── PROVIDERS ─────────────────────────────────────────────
        print()
        print("   [1] Claude browser  (default — full reasoning, manual paste per audit pass)")
        print("   [2] Gemini API  (no paste — suitable for small transcripts)")
        print("   [ENTER] Keep default")
        q_mode2 = input(" Q2 — Mode 2 Audit Passes: ").strip()
        mode2_gemini_selected = (q_mode2 == "2")
        if mode2_gemini_selected:
            pipeline_env["PIPELINE_MODE2_GEMINI"] = "TRUE"

        print()
        print("   [1] Gemini  (default — auto-runs after Surgeon, no extra paste)")
        print("   [2] Haiku API  (API fallback if Gemini unavailable for Exporter)")
        print("   [ENTER] Keep default")
        q_exporter = input(" Q3 — P5 Exporter Provider (Pass 3 only): ").strip()
        if q_exporter == "2":
            pipeline_env["PIPELINE_HAIKU_THROUGHPUT"] = "TRUE"
            haiku_selected = True
        elif q_exporter == "1":
            pipeline_env["PIPELINE_HAIKU_THROUGHPUT"] = "GEMINI"
            haiku_selected = False
        else:
            haiku_selected = False

        print()
        print("   [1] API  — force all Claude calls to API, no browser (debug override)")
        print("   [2] Browser — force browser mode ON regardless of config.py")
        print("   [ENTER] Keep config.py default (browser)")
        q_claude = input(" Q4 — Claude Mode: ").strip()
        claude_api_mode = (q_claude == "1")
        if q_claude == "1":
            pipeline_env["PIPELINE_CLAUDE_MANUAL"] = "FALSE"
        elif q_claude == "2":
            pipeline_env["PIPELINE_CLAUDE_MANUAL"] = "TRUE"

        # ── GEMINI SETTINGS (only if Gemini is active anywhere) ───
        gemini_active = (not haiku_selected) or mode2_gemini_selected
        if gemini_active:
            print()
            for i, model in enumerate(_cfg.GEMINI_MODELS, 1):
                tag = "  ← full waterfall" if i == 1 else ("  ← cost-optimized" if i == len(_cfg.GEMINI_MODELS) else "")
                print(f"   [{i}] {model}{tag}")
            print("   [ENTER] Keep default (full waterfall from top)")
            q_cascade = input(" Q5 — Gemini Cascade Ceiling: ").strip()
            try:
                n = int(q_cascade)
                if 1 <= n <= len(_cfg.GEMINI_MODELS):
                    pipeline_env["PIPELINE_GEMINI_START"] = _cfg.GEMINI_MODELS[n - 1]
            except (ValueError, TypeError):
                pass

            print()
            print("   [1] Standard  — auto-prompt after 10 min (default)")
            print("   [2] Extended  — auto-prompt after 30 min")
            print("   [3] Unlimited — never auto-prompt; wait indefinitely")
            print("   (Ctrl+C always available to interrupt)")
            q_wait = input(" Q6 — Gemini Wait Mode [1/2/3, ENTER = 1]: ").strip()
            if q_wait == "2":
                pipeline_env["PIPELINE_GEMINI_TIMEOUT_MODE"] = "extended"
            elif q_wait == "3":
                pipeline_env["PIPELINE_GEMINI_TIMEOUT_MODE"] = "unlimited"

        # ── CLAUDE BROWSER SETTINGS (only if browser active) ──────
        if not claude_api_mode:
            print()
            print("   [1] ON   — auto-press ENTER after paste (full hands-off)")
            print("   [ENTER] OFF  — stage prompt, submit manually (default)")
            q_auto = input(" Q7 — Auto-Submit in Browser: ").strip()
            if q_auto == "1":
                pipeline_env["PIPELINE_AUTO_SUBMIT"] = "TRUE"

    # ── SUMMARY ───────────────────────────────────────────────────
    override_keys = [
        "PIPELINE_SKIP_PHASES",
        "PIPELINE_MODE2_GEMINI",
        "PIPELINE_HAIKU_THROUGHPUT",
        "PIPELINE_CLAUDE_MANUAL",
        "PIPELINE_GEMINI_START",
        "PIPELINE_GEMINI_TIMEOUT_MODE",
        "PIPELINE_AUTO_SUBMIT",
    ]
    active = {k: pipeline_env[k] for k in override_keys if k in pipeline_env}
    print("\n" + "-"*60)
    if active:
        print(" ACTIVE OVERRIDES:")
        for k, v in active.items():
            print(f"   {k} = {v}")
    else:
        print(" No overrides — running on config.py defaults.")
    print("-"*60 + "\n")

def _check_unit_boundary(video_id):
    """Returns {"unit": int, "after_video": int, "unit_start_video": int}
    if video_id closes a unit per Prompts/reference_library_p1.xml UNIT_END markers.
    Returns None otherwise. File-wide regex; not adjacent-line scan."""
    try:
        vid = int(video_id)
    except (ValueError, TypeError):
        return None

    ref_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Prompts", "reference_library_p1.xml"
    )
    if not os.path.exists(ref_path):
        return None
    try:
        with open(ref_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return None

    end_pattern = r'<!--\s*UNIT_END\s+unit=(\d+)\s+after_video=' + re.escape(str(vid)) + r'\s*-->'
    m = re.search(end_pattern, text)
    if not m:
        return None
    unit = int(m.group(1))

    all_ends = re.findall(r'<!--\s*UNIT_END\s+unit=\d+\s+after_video=(\d+)\s*-->', text)
    prior_ends = [int(n) for n in all_ends if int(n) < vid]
    if prior_ends:
        unit_start_video = max(prior_ends) + 1
    else:
        cold = re.search(r'<!--\s*UNIT_START\s+unit=\d+\s+first_video=(\d+)\s*-->', text)
        if cold:
            unit_start_video = int(cold.group(1))
        else:
            print(f" [!] UNIT BOUNDARY DETECTION: UNIT_END found for video {vid} "
                  f"but no prior UNIT_END or cold-start UNIT_START marker present. "
                  f"Unit sweep skipped.")
            return None

    return {"unit": unit, "after_video": vid, "unit_start_video": unit_start_video}


def _unit_sweep_sentinel_path(boundary_video):
    """SHARED HELPER — single source of truth for sentinel path.
    Defined in run_master.py only (NOT run_phase1.py — that would trigger
    config/TTS/SDK module-level side effects on import). Both _already_swept
    and E.4's shutil.copy2 call this. Prevents path-mismatch bugs."""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Archive", str(boundary_video), "unit_sweep_ANKI_IMPORT_READY.txt"
    )


def _already_swept(boundary_video):
    try:
        p = _unit_sweep_sentinel_path(boundary_video)
        return os.path.exists(p) and os.path.getsize(p) > 0
    except Exception:
        return False


def _archive_unit_sweep_outputs(boundary_video):
    """Copy final unit_sweep_ANKI_IMPORT_READY.txt to sentinel path, then move
    all unit_sweep_* intermediates from cwd to Archive/<boundary_video>/.
    Called by both the auto-detect path (after Phase 1–5) and the forced-sweep
    path ("6" at the phase prompt)."""
    archive_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "Archive", str(boundary_video)
    )
    os.makedirs(archive_dir, exist_ok=True)
    final_out = "unit_sweep_ANKI_IMPORT_READY.txt"
    if os.path.exists(final_out):
        try:
            shutil.copy2(final_out, _unit_sweep_sentinel_path(boundary_video))
        except Exception as _ce:
            print(f" [!] Sentinel copy failed: {_ce}")
    for _f in glob.glob("unit_sweep_*"):
        if not os.path.isfile(_f):
            continue
        if os.path.basename(_f) == final_out:
            # Keep the Anki import file in root (cwd) — the user imports from the
            # project root, not Archive. The sentinel copy above already persists a
            # copy in Archive/<boundary>/ for the _already_swept check.
            continue
        _dst = os.path.join(archive_dir, os.path.basename(_f))
        if os.path.abspath(_f) == os.path.abspath(_dst):
            continue
        try:
            if os.path.exists(_dst):
                os.remove(_dst)
            shutil.move(_f, _dst)
        except Exception as _ae:
            print(f" [!] Could not archive {_f}: {_ae}")
    print(f" [+] UNIT SWEEP COMPLETE: outputs archived to Archive/{boundary_video}/")


def run_master():
    # Wipe stale auto-submit flag from prior run (prevents Ghost Hook Cancel leakage)
    if os.path.exists("_auto_submit_next.flag"):
        try:
            os.remove("_auto_submit_next.flag")
            print(" [+] Cleared stale auto-submit flag from prior run.")
        except Exception:
            pass

    # The chronological order of your scripts
    scripts = ["run_phase1.py", "run_phase2.py", "run_phase3.py", "run_phase4.py", "run_phase5.py"]
    SWEEP_SCRIPTS = ["run_phase6.py", "run_phase2.py", "run_phase3.py", "run_phase4.py", "run_phase5.py"]

    # 1. SET THE FLAG: This tells scripts "I am running as a chain"
    # It allows specialists to skip redundant manual pauses.
    pipeline_env = os.environ.copy()
    pipeline_env["PIPELINE_MODE"] = "TRUE"

    # --from N resume flag: allows resuming from a specific phase
    start_phase = 1
    phase_was_typed = False
    sweep_mode_requested = False
    sweep_boundary = None       # populated when "6" is selected
    sweep_resume_phase = None   # 6/2/3/4/5 (the actual phase, not chain pos)
    if "--from" not in sys.argv:
        while True:
            raw = input("\n [?] Start from which phase? [1–5, 6 = Unit Sweep, ENTER = 1 · S = Settings]: ").strip()
            if raw == "":
                break
            elif raw.upper() == 'S':
                run_settings_menu(pipeline_env)
                continue
            elif raw == "6":
                sweep_mode_requested = True
                break
            elif raw.isdigit() and 1 <= int(raw) <= 5:
                start_phase = int(raw)
                phase_was_typed = True
                break
            else:
                print(" [!] Invalid input — defaulting to Phase 1.")
                continue

    # ── UNIT SWEEP DISPATCH ─────────────────────────────────────────
    # Selected by typing "6" at the phase prompt. Walks through boundary
    # video resolution, asks which sweep phase to resume from, validates
    # the required input file is on disk, then swaps the script list to
    # SWEEP_SCRIPTS so the existing for-loop runs the sweep chain.
    if sweep_mode_requested:
        _vid = None
        if os.path.exists(".last_video_id"):
            with open(".last_video_id", "r", encoding="utf-8") as _f:
                _vid = _f.read().strip()
        if _vid:
            _override = input(f"\n [?] Boundary video? [ENTER = {_vid} from .last_video_id]: ").strip()
            if _override:
                _vid = _override
        else:
            _vid = input("\n [?] Boundary video? (.last_video_id not found — type the video number): ").strip()
            if not _vid:
                print(" [X] No boundary video specified — aborting unit sweep.")
                sys.exit(1)
        sweep_boundary = _check_unit_boundary(_vid)
        if not sweep_boundary:
            print(f" [X] No UNIT_END marker for video {_vid} in reference_library_p1.xml.")
            print(" [X] Not a unit boundary — sweep cannot start.")
            sys.exit(1)

        # Resume-phase prompt. Maps to the input file each sweep phase needs.
        _SWEEP_PHASE_INPUTS = {
            6: None,  # Phase 6 reads Archive/{N}/ANKI_IMPORT_READY.txt directly
            2: "unit_sweep_baton_p1_to_p2.xml",
            3: "unit_sweep_baton_p2_to_p3.txt",
            4: "unit_sweep_final_anki_cards.txt",
            5: "unit_sweep_final_anki_cards_with_reverse.txt",
        }
        while True:
            raw_r = input("\n [?] Resume sweep at which phase? [6/2/3/4/5, ENTER = 6 (full restart)]: ").strip()
            if raw_r == "":
                sweep_resume_phase = 6
                break
            elif raw_r in ("6", "2", "3", "4", "5"):
                sweep_resume_phase = int(raw_r)
                break
            else:
                print(" [!] Invalid input — must be 6, 2, 3, 4, or 5.")
                continue

        # Validate the required input file exists for the chosen resume phase.
        _req = _SWEEP_PHASE_INPUTS[sweep_resume_phase]
        if _req and not (os.path.exists(_req) and os.path.getsize(_req) > 0):
            print(f" [X] Resume requires '{_req}' in working directory.")
            print(f" [X] File missing or empty — cannot resume sweep at Phase {sweep_resume_phase}.")
            sys.exit(1)

        # Map sweep phase to chain position: 6→1, 2→2, 3→3, 4→4, 5→5.
        # Reuses the existing for-loop skip mechanism (if index < start_phase: continue).
        _SWEEP_CHAIN_POS = {6: 1, 2: 2, 3: 3, 4: 4, 5: 5}
        start_phase = _SWEEP_CHAIN_POS[sweep_resume_phase]

        # Swap to the sweep chain + set sweep env vars
        scripts = SWEEP_SCRIPTS
        pipeline_env["PIPELINE_UNIT_SWEEP"] = "TRUE"
        pipeline_env["PIPELINE_UNIT_START_VIDEO"] = str(sweep_boundary["unit_start_video"])
        pipeline_env["PIPELINE_UNIT_BOUNDARY_VIDEO"] = str(sweep_boundary["after_video"])
        # Strip per-video resume directives that would corrupt the sweep
        pipeline_env.pop("PIPELINE_SKIP_PHASES", None)
        pipeline_env.pop("PIPELINE_RESUME", None)

    # ── RESUME-AT-MODE CASCADE ──────────────────────────────────────
    # Fires only when the user typed an explicit phase digit (not ENTER,
    # not S, not --from N). ENTER and CLI paths preserve today's behavior
    # byte-identically by leaving phase_was_typed = False.
    resume_mode = 1
    resume_style = "prime"
    if phase_was_typed:
        while True:
            raw_m = input(f"\n [?] Resume from which mode within Phase {start_phase}? [1 or 2, ENTER = 1]: ").strip()
            if raw_m == "" or raw_m == "1":
                resume_mode = 1
                break
            elif raw_m == "2":
                resume_mode = 2
                break
            else:
                print(" [!] Invalid input — defaulting to Mode 1.")
                continue
        raw_s = input(" [?] Has Claude already replied for this pass? [Y = listen on clipboard, N = submit prompt as normal, ENTER = N]: ").strip().lower()
        if raw_s in ("y", "yes"):
            resume_style = "listen"
        else:
            resume_style = "prime"
        if resume_mode > 1 or resume_style == "listen":
            pipeline_env["PIPELINE_RESUME"] = f"{start_phase}.{resume_mode}:{resume_style}"

    if "--from" in sys.argv:
        from_idx = sys.argv.index("--from")
        if from_idx + 1 < len(sys.argv):
            try:
                start_phase = int(sys.argv[from_idx + 1])
                if not (1 <= start_phase <= len(scripts)):
                    print(f" [X] --from value must be between 1 and {len(scripts)}.")
                    sys.exit(1)
            except ValueError:
                print(f" [X] --from requires a valid integer between 1 and {len(scripts)}.")
                sys.exit(1)
        else:
            print(f" [X] --from requires a value between 1 and {len(scripts)}.")
            sys.exit(1)

    # Baton check (per-video pipeline only — sweep mode validated its own input above)
    if start_phase > 1 and not sweep_mode_requested:
        baton_map = {
            2: "baton_p1_to_p2.xml",
            3: "baton_p2_to_p3.txt",
            4: "final_anki_cards.txt",
            5: "final_anki_cards_with_reverse.txt",
        }
        required_file = baton_map[start_phase]
        if not (os.path.exists(required_file) and os.path.getsize(required_file) > 0):
            print(f" [X] BATON MISSING: Phase {start_phase} requires '{required_file}' but the file is missing or empty.")
            print(" [X] Run the preceding phase(s) first or use '--from 1' to restart the full pipeline.")
            sys.exit(1)

    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print(" [!] MASTER ORCHESTRATOR: THE ANKI FACTORY (v4.0) ".center(60, "#"))
    print("="*60)
    if sweep_mode_requested:
        print(f" [!] UNIT SWEEP MODE — Unit {sweep_boundary['unit']}, boundary video {sweep_boundary['after_video']}")
        print(f" [!] Sweep window: videos {sweep_boundary['unit_start_video']} through {sweep_boundary['after_video']}")
        if sweep_resume_phase != 6:
            print(f" [!] Resuming sweep at Phase {sweep_resume_phase} (chain position {start_phase}/5)")
    elif start_phase > 1:
        _resume_suffix = ""
        if "PIPELINE_RESUME" in pipeline_env:
            _resume_suffix = f" · MODE {resume_mode} ({resume_style.upper()})"
        print(f" [!] RESUMING FROM PHASE {start_phase}{_resume_suffix} — Phases 1 through {start_phase - 1} skipped.")

    # --- Windows Notification Listener ---
    _listener_proc = None
    try:
        import config as _cfg_ref
        _start_listener = (
            getattr(_cfg_ref, "WINDOWS_NOTIFY_LISTENER", False)
            and pipeline_env.get("PIPELINE_CLAUDE_MANUAL") != "FALSE"
        )
    except Exception:
        _start_listener = False

    if _start_listener:
        _lscript = os.path.join(os.path.dirname(os.path.abspath(__file__)), "win_notify_listener.py")
        if os.path.exists(_lscript):
            try:
                _listener_proc = subprocess.Popen(
                    [sys.executable, _lscript],
                    stdout=subprocess.DEVNULL,
                    stderr=None,  # inherit terminal so listener errors are visible
                )
                print(f" [~] Notify listener started (PID {_listener_proc.pid}).")
            except Exception as _le:
                print(f" [!] Could not start notify listener: {_le}")

    try:
        pipeline_start_time = time.time()
        for index, script in enumerate(scripts, 1):
            # Actual phase number from script name (handles sweep chain where
            # chain position 1 is Phase 6, not Phase 1).
            _phase_label = script.replace("run_phase", "").replace(".py", "")
            if index < start_phase:
                print(f" [>] Skipping Phase {_phase_label}")
                continue

            print()
            print()
            print("▓" * 60)

            print("="*60)
            print(f" [!] STEP {index}/5: {script.upper()} ".center(60, "#"))
            print("="*60)

            try:
                phase_start_time = time.time()
                # 2. RUN: Standard execution. Your terminal stays 100% manual.
                # You can type your Video Number and your y/n vetoes exactly as before.
                subprocess.run([sys.executable, script], check=True, env=pipeline_env)
                phase_elapsed = int(time.time() - phase_start_time)
                phase_mins, phase_secs = divmod(phase_elapsed, 60)
                print(f" [+] Phase {_phase_label} completed in {phase_mins}m {phase_secs}s")

            except subprocess.CalledProcessError as e:
                if e.returncode == 2:
                    print(f"\n [!] PIPELINE STOPPED: User Veto detected in {script}.")
                    print(" [!] No cards were harmed. Pipeline exited gracefully.")
                    sys.exit(0) # Exit the orchestrator cleanly
                else:
                    print(f"\n [X] PIPELINE HALTED: {script} encountered a FATAL ERROR (Code {e.returncode}).")
                    print(" [!] Resolve the error in the specialist and restart run_master.py.")
                    sys.exit(1)

        total_elapsed = int(time.time() - pipeline_start_time)
        total_mins, total_secs = divmod(total_elapsed, 60)
        try:
            if platform.system() == "Windows":
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
        except Exception:
            pass
        print("\n" + "="*60)
        _final_file = "unit_sweep_ANKI_IMPORT_READY.txt" if sweep_mode_requested else "ANKI_IMPORT_READY.txt"
        print(f" ! ALL PHASES COMPLETE: {_final_file} SECURED ".center(60, "="))
        print(f" [+] Total Pipeline Time  : {total_mins}m {total_secs}s")
        print("="*60)

        if sweep_mode_requested:
            # Forced sweep path: skip run_backup (working-dir snapshot is not
            # meaningful for a sweep retry) and skip auto-detect (the user
            # explicitly drove us here). Just archive the sweep outputs.
            _archive_unit_sweep_outputs(sweep_boundary["after_video"])
        else:
            # ── SILENT BACKUP ──────────────────────────────────────────
            print(" [~] Archiving workspace...")
            try:
                from run_backup import run_backup
                run_backup(
                    source_dir=os.path.dirname(os.path.abspath(__file__)),
                    total_elapsed=total_elapsed,
                )
            except Exception as _be:
                print(f" [!] Backup skipped (non-fatal): {_be}")

            # ── UNIT BOUNDARY SWEEP (auto-detect, post-pipeline) ──────
            try:
                _vid = None
                if os.path.exists(".last_video_id"):
                    with open(".last_video_id", "r", encoding="utf-8") as _f:
                        _vid = _f.read().strip()
                _boundary = _check_unit_boundary(_vid) if _vid else None
                if _boundary and _already_swept(_boundary["after_video"]):
                    print(f" [~] Unit boundary {_boundary['after_video']} already swept — skipping.")
                elif _boundary:
                    print()
                    print("=" * 60)
                    print(f" [!] UNIT BOUNDARY DETECTED: Unit {_boundary['unit']} closes at video {_boundary['after_video']}")
                    print(f" [!] UNIT AUDITOR sweep: videos {_boundary['unit_start_video']} through {_boundary['after_video']}")
                    print("=" * 60)

                    # Strip skip/resume from sweep env (would corrupt the unit sweep)
                    unit_env = pipeline_env.copy()
                    unit_env.pop("PIPELINE_SKIP_PHASES", None)
                    unit_env.pop("PIPELINE_RESUME", None)
                    unit_env["PIPELINE_UNIT_SWEEP"] = "TRUE"
                    unit_env["PIPELINE_UNIT_START_VIDEO"] = str(_boundary["unit_start_video"])
                    unit_env["PIPELINE_UNIT_BOUNDARY_VIDEO"] = str(_boundary["after_video"])

                    sweep_failed = False
                    for _s in SWEEP_SCRIPTS:
                        try:
                            subprocess.run([sys.executable, _s], check=True, env=unit_env)
                        except subprocess.CalledProcessError as _se:
                            print(f" [X] UNIT SWEEP HALTED: {_s} returned exit code {_se.returncode}.")
                            print(f" [X] Re-run with phase prompt = 6 to resume from Phase {_s.replace('run_phase', '').replace('.py', '')}.")
                            sweep_failed = True
                            break

                    if not sweep_failed:
                        _archive_unit_sweep_outputs(_boundary["after_video"])
            except Exception as _ue:
                print(f" [!] Unit boundary sweep skipped (non-fatal): {_ue}")

        # Mandatory pause to prevent the terminal window from vanishing
        if sweep_mode_requested:
            input("\n 🎉 UNIT SWEEP SUCCESSFUL. PRESS ENTER TO EXIT...")
        else:
            input("\n 🎉 PIPELINE SUCCESSFUL. PRESS ENTER TO EXIT...")
    finally:
        if _listener_proc is not None and _listener_proc.poll() is None:
            _listener_proc.terminate()
            try:
                _listener_proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _listener_proc.kill()
            print(" [~] Notify listener stopped.")

if __name__ == "__main__":
    try:
        run_master()
    except KeyboardInterrupt:
        print("\n [!] Pipeline interrupted by user. Partial outputs preserved in their respective files.")
        sys.exit(0)
