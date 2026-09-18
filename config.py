# config.py
import time
import os
import subprocess
import webbrowser
import threading
import winsound
from google import genai
from google.genai import types
import anthropic

def clear_screen():
    """Global terminal wipe."""
    os.system('cls' if os.name == 'nt' else 'clear')

def send_ntfy(title, message="", priority="high"):
    """
    Sends a push notification to your phone via ntfy.sh.
    Uses stdlib urllib only — no third-party dependencies.
    Fails silently if NTFY_TOPIC is None or network is unavailable.
    """
    if not NTFY_TOPIC:
        return
    try:
        import urllib.request
        import urllib.parse
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": urllib.parse.quote(title, safe=" "),
                "Priority": priority,
                "Tags": "rotating_light",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as _e:
        print(f" [!] ntfy notification failed: {_e}")


def ui_alert(msg):
    """Standardized high-intensity visual and audio alert."""
    winsound.Beep(800, 400) # 800Hz tone for 400ms (Bypasses terminal settings)
    print("\n" + "!" * 60)
    print(f" {msg} ".center(60, "!"))
    print("!" * 60 + "\n")
    send_ntfy(title="⚠️ Anki Factory", message=msg)

def veto_gate_needs_notification(phase_num):
    """Return True if the veto-gate ntfy should fire for this phase.

    When Pass 2 ran as Claude browser (CLAUDE_MANUAL_MODE active), the user
    manually triggered the clipboard capture and is already at the computer.
    No notification needed. When Pass 2 ran as any API provider (Gemini,
    Haiku, or Claude in API-forced mode), the user walked away and must be
    called back. PHASE_ROUTING and CLAUDE_MANUAL_MODE are resolved at import
    time with all session overrides already applied.
    """
    effective_provider = GLOBAL_FORCE_MODEL or PHASE_ROUTING.get(f"P{phase_num}_PASS_2", "gemini")
    return not (effective_provider == "claude" and CLAUDE_MANUAL_MODE)

try:
    import api_keys
    GEMINI_API_KEY  = api_keys.GEMINI_API_KEY
    CLAUDE_API_KEY  = api_keys.CLAUDE_API_KEY
except ImportError:
    print(" [X] FATAL: api_keys.py not found. Please create it with GEMINI_API_KEY and CLAUDE_API_KEY.")
    import sys
    sys.exit(1)

# ============================================================
# ROUTING CONFIG  — controls which provider handles each phase
# ============================================================
# Set GLOBAL_FORCE_MODEL to "claude", "claude_haiku", or "gemini" to
# override all per-phase routing and force the entire pipeline through
# a single provider. Set to None to use per-phase PHASE_ROUTING below.
GLOBAL_FORCE_MODEL = None

# Path to Anki executable. Set to None to skip auto-launch.
ANKI_PATH = r"C:\Program Files\Anki\anki.exe"

# ============================================================
# NTFY PUSH NOTIFICATIONS  (https://ntfy.sh)
# Subscribe to this topic in the ntfy app on your phone.
# Set to None to disable all push notifications silently.
# ============================================================
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")  # set this in your environment; never commit it

# Startup ping — fires once at import time so you can confirm
# the notification channel is live before the pipeline runs.
# Set to False to suppress the boot ping.
NTFY_STARTUP_PING = False

# Maps phase/pass identifiers to provider strings.
# All Pass 1 AND Pass 2/3 → "claude" (Sonnet, browser paste via CLAUDE_MANUAL_MODE).
# P5_PASS_3 (Exporter only) → "gemini" — deterministic formatting, runs automatically via API.
PHASE_ROUTING = {
    "P1_PASS_1": "claude",
    "P1_PASS_2": "claude",         # Audit pass — now Claude browser (was "gemini")
    "P2_PASS_1": "claude",
    "P2_PASS_2": "claude",         # Audit pass — now Claude browser (was "gemini")
    "P5_PASS_1": "claude",
    "P3_PASS_1": "claude",
    "P3_PASS_2": "claude",         # Sovereign Audit — now Claude browser (was "gemini")
    "P3_PASS_3": "claude",         # Unused slot — updated for consistency (was "gemini")
    "P4_PASS_1": "claude",         # Pass 1 (The Flip)           — Sonnet browser
    "P4_PASS_2": "claude",         # Pass 2 (The Refine)         — Sonnet browser (was "gemini")
    "P4_PASS_3": "claude",         # Pass 3 (unused)             — updated for consistency
    "P5_PASS_2": "claude",         # Pass 2 (Surgeon)            — Sonnet browser (was "gemini")
    "P5_PASS_3": "gemini",         # Pass 3 (Exporter)           — KEEP Gemini (auto, no paste needed)
    "P6_PASS_1": "claude",         # Unit Auditor (single pass)  — Sonnet browser
}

# ============================================================
# GEMINI CONFIG  (kept as fallback / manual override)
# ============================================================
GEMINI_MODELS = [
    "gemini-3.1-pro-preview",
    "gemini-3-pro-preview",  # anticipated preview — remove if API returns 404 on first cascade failure
    "gemini-2.5-pro",
    "gemini-2.5-flash",
]

GEMINI_TIMEOUT_MATRIX = {
    "gemini-3.1-pro-preview": 600000,
    "gemini-3-pro-preview":   600000,
    "gemini-2.5-pro":         600000,
    "gemini-2.5-flash":       120000,
}

# ============================================================
# CLAUDE SONNET CONFIG  (Pass 1 — heavy reasoning)
# ============================================================
CLAUDE_MODELS = [
    "claude-sonnet-4-6",
]

# Anthropic SDK timeout is in seconds (not ms)
CLAUDE_TIMEOUT_MATRIX = {
    "claude-sonnet-4-6": 600,
}

# Max tokens must cover thinking budget + output combined when
# extended thinking is enabled. 32 000 is safe for either mode.
CLAUDE_MAX_TOKENS = 32000

# ============================================================
# CLAUDE SONNET — EXTENDED THINKING TOGGLE
# ============================================================
# When True, Pass-1 (Sonnet) calls enable the hidden reasoning
# scratchpad. Quality improves noticeably on complex tasks but
# thinking tokens are billed at the same rate as output tokens.
# Set to False to run standard mode (cheaper, slightly faster).
SONNET_EXTENDED_THINKING = True

# How many tokens Sonnet is allowed to spend thinking before it
# begins writing its answer. Must be < CLAUDE_MAX_TOKENS.
# Recommended range: 8 000–16 000 for heavy reasoning tasks.
SONNET_THINKING_BUDGET = 10000

# ============================================================
# CLAUDE HAIKU CONFIG  (Pass 2 / 3 — throughput)
# ============================================================
CLAUDE_HAIKU_MODELS = [
    "claude-haiku-4-5-20251001",
]

# Haiku is fast — 5 min ceiling is generous.
CLAUDE_HAIKU_TIMEOUT_MATRIX = {
    "claude-haiku-4-5-20251001": 300,
}

# Lower ceiling than Sonnet; raise if pass output volume demands it.
CLAUDE_HAIKU_MAX_TOKENS = 16000

# ============================================================
# CLAUDE HAIKU — EXTENDED THINKING TOGGLE
# ============================================================
# Haiku 4.5 supports extended thinking but the quality uplift is
# smaller than on Sonnet. Useful for A/B testing cost vs quality
# on throughput passes. Set to False for standard (faster/cheaper).
HAIKU_EXTENDED_THINKING = True

# Thinking budget for Haiku. Keep lower than Sonnet's — Haiku
# passes do lighter work and a large budget wastes tokens quickly.
# Recommended range: 2 000–6 000.
HAIKU_THINKING_BUDGET = 4000

# ============================================================
# CLAUDE MANUAL MODE
# ============================================================
# When True, any call resolved to the "claude" provider bypasses the API
# entirely. The assembled prompt is written to a local file so you can
# copy-paste it into Claude.ai in a browser, paste the response back into
# the same file, save it, and press ENTER to continue the pipeline.
# When False, behavior is identical to the existing implementation.
# This toggle is purely additive — it has zero effect when set to False.
CLAUDE_MANUAL_MODE = True
WINDOWS_NOTIFY_LISTENER = True  # Launch win_notify_listener.py in background when CLAUDE_MANUAL_MODE is True

# ============================================================
# SESSION OVERRIDES  (injected by run_master.py settings menu)
# These env vars are set at launch time and are session-scoped only.
# They silently have no effect when not present.
# ============================================================
GEMINI_OVERRIDE_START_MODEL = None

SKIP_PHASES_SET = set()
_claude_override = os.environ.get("PIPELINE_CLAUDE_MANUAL")
if _claude_override == "TRUE":
    CLAUDE_MANUAL_MODE = True
elif _claude_override == "FALSE":
    CLAUDE_MANUAL_MODE = False

_gemini_start = os.environ.get("PIPELINE_GEMINI_START")
if _gemini_start:
    GEMINI_OVERRIDE_START_MODEL = _gemini_start

_haiku_override = os.environ.get("PIPELINE_HAIKU_THROUGHPUT")
if _haiku_override == "TRUE":
    for _k in PHASE_ROUTING:
        if (_k.endswith("_PASS_2") or _k.endswith("_PASS_3")) and PHASE_ROUTING[_k] == "gemini":
            PHASE_ROUTING[_k] = "claude_haiku"
elif _haiku_override == "GEMINI":
    for _k in PHASE_ROUTING:
        if (_k.endswith("_PASS_2") or _k.endswith("_PASS_3")) and PHASE_ROUTING[_k] == "claude_haiku":
            PHASE_ROUTING[_k] = "gemini"

# SESSION OVERRIDE: revert all Mode 2 audit passes from claude → gemini for this session.
# Useful for small transcripts where Gemini can handle the audit and no manual paste is needed.
# Runs AFTER haiku override — only rewrites entries still set to "claude".
_mode2_gemini = os.environ.get("PIPELINE_MODE2_GEMINI")
if _mode2_gemini == "TRUE":
    for _k in PHASE_ROUTING:
        if _k.endswith("_PASS_2") and PHASE_ROUTING[_k] == "claude":
            PHASE_ROUTING[_k] = "gemini"

_skip_raw = os.environ.get("PIPELINE_SKIP_PHASES")
if _skip_raw == "ALL":
    SKIP_PHASES_SET = {1, 2, 3, 4, 5}
elif _skip_raw:
    for _token in _skip_raw.split(","):
        try:
            SKIP_PHASES_SET.add(int(_token.strip()))
        except (ValueError, TypeError):
            pass

# ─── PIPELINE_RESUME parser (format: "<phase>.<mode>:<style>") ───
# Set by run_master.py's interactive resume cascade. Hardened against
# missing / empty / malformed values — any failure leaves all three
# constants at their inactive defaults and the pipeline behaves as today.
RESUME_PHASE = None
RESUME_PASS = None
RESUME_STYLE = "prime"
_resume_raw = os.environ.get("PIPELINE_RESUME", "").strip()
if _resume_raw:
    _resume_parts = _resume_raw.split(":")
    if len(_resume_parts) == 2:
        _resume_pos = _resume_parts[0].strip()
        _resume_sty = _resume_parts[1].strip().lower()
        _pos_parts = _resume_pos.split(".")
        if len(_pos_parts) == 2:
            try:
                _rp = int(_pos_parts[0].strip())
                _rm = int(_pos_parts[1].strip())
                if 1 <= _rp <= 5 and 1 <= _rm <= 2:
                    RESUME_PHASE = _rp
                    RESUME_PASS = _rm
                    RESUME_STYLE = _resume_sty if _resume_sty in ("prime", "listen") else "prime"
                else:
                    print(" [!] PIPELINE_RESUME malformed (out of range) — ignoring.")
            except ValueError:
                print(" [!] PIPELINE_RESUME malformed (non-integer) — ignoring.")
        else:
            print(" [!] PIPELINE_RESUME malformed (position needs phase.mode) — ignoring.")
    else:
        print(" [!] PIPELINE_RESUME malformed (need phase.mode:style) — ignoring.")

AUTO_SUBMIT = False
_auto_submit_raw = os.environ.get("PIPELINE_AUTO_SUBMIT")
if _auto_submit_raw == "TRUE":
    AUTO_SUBMIT = True
_AUTO_SUBMIT_ONCE = False  # armed by Ghost Hook Cancel; consumed on next browser call
_AUTO_SUBMIT_FLAG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_auto_submit_next.flag")

_gemini_timeout_mode = os.environ.get("PIPELINE_GEMINI_TIMEOUT_MODE", "standard")
GEMINI_UNLIMITED_WAIT   = (_gemini_timeout_mode == "unlimited")
GEMINI_CHECK_INTERVAL_S = 1800 if _gemini_timeout_mode == "extended" else None

_override_summary = []
if _claude_override in ("TRUE", "FALSE"):
    _override_summary.append(f"CLAUDE={'WEB' if CLAUDE_MANUAL_MODE else 'API'}")
if GEMINI_OVERRIDE_START_MODEL is not None:
    _override_summary.append(f"GEMINI_START={GEMINI_OVERRIDE_START_MODEL}")
if _haiku_override in ("TRUE", "GEMINI"):
    _override_summary.append(f"HAIKU={'ON' if _haiku_override == 'TRUE' else 'GEMINI'}")
if _mode2_gemini == "TRUE":
    _override_summary.append("MODE2=GEMINI")
if SKIP_PHASES_SET:
    _override_summary.append(f"SKIP={sorted(SKIP_PHASES_SET)}")
if RESUME_PHASE is not None and RESUME_PASS is not None:
    _override_summary.append(f"RESUME=P{RESUME_PHASE}/M{RESUME_PASS}/{RESUME_STYLE.upper()}")
if AUTO_SUBMIT:
    _override_summary.append("AUTO_SUBMIT=ON")
if _gemini_timeout_mode != "standard":
    _override_summary.append(f"GEMINI_WAIT={_gemini_timeout_mode.upper()}")
if _override_summary:
    print(f" [~] Session overrides active: {', '.join(_override_summary)}")

if NTFY_STARTUP_PING:
    send_ntfy(title="🏭 Anki Factory Online", message="Pipeline booted. Notifications are working.", priority="low")
    print(" [~] ntfy startup ping sent.")

# ============================================================
# SHARED STATE
# ============================================================
LAST_ACTIVE_MODEL = "None"

GEMINI_WAIT_TIME = 5   # Rate limit buffer for Gemini API
CLAUDE_WAIT_TIME = 2   # Shorter buffer for Claude API
DISABLE_CASCADE  = True   # Set to False for automatic silent downgrades

P3_CHUNK_THRESHOLD = 25
P3_MAX_WALK_DISTANCE = 10

# ============================================================
# INTERNAL HELPERS
# ============================================================
def _active_roster(active_provider):
    """Returns (model_list, timeout_matrix) for the given active_provider."""
    if active_provider == "claude":
        return CLAUDE_MODELS, CLAUDE_TIMEOUT_MATRIX
    if active_provider == "claude_haiku":
        return CLAUDE_HAIKU_MODELS, CLAUDE_HAIKU_TIMEOUT_MATRIX
    return GEMINI_MODELS, GEMINI_TIMEOUT_MATRIX


def _call_model(model_id, timeout, full_prompt, active_provider):
    """
    Fires a single blocking API call for the given active_provider.
    Returns the response text string on success, raises on failure.

    Extended thinking is gated by the SONNET_EXTENDED_THINKING and
    HAIKU_EXTENDED_THINKING toggles. When enabled, the API holds the
    entire response (thinking + answer) before returning — streaming
    is not used here so this has no practical effect on the pipeline.
    The response may contain a thinking block followed by a text block;
    we extract only the text block for downstream processing.
    """
    if active_provider in ("claude", "claude_haiku"):
        # Resolve per-provider settings
        if active_provider == "claude":
            max_tokens     = CLAUDE_MAX_TOKENS
            use_thinking   = SONNET_EXTENDED_THINKING
            thinking_budget = SONNET_THINKING_BUDGET
        else:
            max_tokens     = CLAUDE_HAIKU_MAX_TOKENS
            use_thinking   = HAIKU_EXTENDED_THINKING
            thinking_budget = HAIKU_THINKING_BUDGET

        client = anthropic.Anthropic(
            api_key=CLAUDE_API_KEY,
            timeout=float(timeout),  # SDK expects seconds
        )

        create_kwargs = dict(
            model=model_id,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": full_prompt}],
        )

        if use_thinking:
            # Budget must be strictly less than max_tokens.
            # Guard against misconfiguration.
            safe_budget = min(thinking_budget, max_tokens - 1000)
            create_kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": safe_budget,
            }
            provider_label = active_provider.upper()
            print(f" [~] Extended thinking ON — budget: {safe_budget:,} tokens  [{provider_label}]")

        response = client.messages.create(**create_kwargs)

        if not response or not response.content:
            raise ValueError("Empty API Response")

        # Extract the text block — when thinking is enabled the content list
        # contains a thinking block first, then the text block with the answer.
        text_block = next(
            (block.text for block in response.content if block.type == "text"),
            None,
        )
        if not text_block:
            raise ValueError("No text block found in response content")
        return text_block

    else:  # gemini
        client = genai.Client(
            api_key=GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=timeout),  # ms
        )
        response = client.models.generate_content(model=model_id, contents=full_prompt)
        if not response or not response.text:
            raise ValueError("Empty API Response")
        return response.text


def _prompt_nonblocking(prompt_text, finished_event):
    """Show a prompt; return 'AUTO_RESUME' immediately if finished_event fires."""
    import msvcrt
    print(prompt_text, end='', flush=True)
    typed = ''
    while True:
        if finished_event.is_set():
            print()
            return 'AUTO_RESUME'
        if msvcrt.kbhit():
            ch = msvcrt.getwch()
            if ch in ('\r', '\n'):
                print()
                return typed.strip().upper()
            elif ch == '\x08' and typed:
                typed = typed[:-1]
                print('\b \b', end='', flush=True)
            elif ch == '\x03':          # Ctrl+C at prompt = keep waiting
                print()
                return 'W'
            else:
                typed += ch
                print(ch, end='', flush=True)
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            print()
            return 'W'


# ============================================================
# PUBLIC API  (called by all run_phase*.py scripts)
# ============================================================
def call_gemini(full_prompt, context_header="GENERIC_TASK", model_override=None, *, phase=None, pass_num=None):
    """
    Provider-agnostic LLM call with waterfall cascade, live timer,
    cascade toggle, and manual airlock fallback.

    Named 'call_gemini' for backwards compatibility — rename to
    'call_llm' across the phase scripts whenever convenient.

    Args:
        phase:    Optional phase string (e.g. "P1", "P5"). Used to resolve
                  which provider to use via PHASE_ROUTING.
        pass_num: Optional pass integer (e.g. 1, 2). Combined with phase to
                  form a routing key like "P5_PASS_1".
    """
    global LAST_ACTIVE_MODEL

    # ----------------------------------------------------------
    # PROVIDER RESOLUTION
    # ----------------------------------------------------------
    if pass_num is not None and phase is not None:
        routing_key = f"{phase}_PASS_{pass_num}"
    elif phase is not None:
        routing_key = phase
    else:
        routing_key = None

    if GLOBAL_FORCE_MODEL is not None:
        active_provider = GLOBAL_FORCE_MODEL
    elif routing_key is not None:
        active_provider = PHASE_ROUTING.get(routing_key, "gemini")
        if routing_key not in PHASE_ROUTING:
            print(f" [!] No routing entry found for key '{routing_key}' — defaulting to Gemini.")
    else:
        active_provider = "gemini"
    # ----------------------------------------------------------

    import re
    _SKIP_MIN_LENGTH = 800

    try:
        phase_int = int(str(phase).lstrip("P"))
    except (ValueError, TypeError, AttributeError):
        phase_int = None

    skip_by_phase = phase_int is not None and phase_int in SKIP_PHASES_SET
    skip_by_resume = (
        RESUME_PHASE is not None and RESUME_PASS is not None
        and phase_int == RESUME_PHASE
        and pass_num is not None
        and pass_num < RESUME_PASS
    )
    if skip_by_phase or skip_by_resume:
        _safe_stem = re.sub(r'[^A-Za-z0-9_-]', '_', context_header)
        _safe_stem = re.sub(r'_+', '_', _safe_stem).strip('_')
        _filename = f"CLAUDE_MANUAL_{_safe_stem}.txt"
        _skip_content = None
        if os.path.exists(_filename):
            with open(_filename, encoding="utf-8") as _sf:
                _skip_content = _sf.read()
        if _skip_content is not None and len(_skip_content) >= _SKIP_MIN_LENGTH:
            LAST_ACTIVE_MODEL = "FILE_SKIP"
            if skip_by_phase:
                print(f" [SKIP] Phase {phase_int} — reading from: {_filename}")
            else:
                print(f" [RESUME] Phase {phase_int} Pass {pass_num} below resume target M{RESUME_PASS} — reading from: {_filename}")
            return _skip_content
        else:
            print(f" [SKIP] File missing or too small for Phase {phase_int} ({_filename}) — falling back to API.")

    # REPLACE WITH:
    # CLAUDE MANUAL MODE INTERCEPT
    # Fires before any API machinery starts. Applies to ALL passes routed to "claude"
    # (Pass 1 AND Pass 2 audit passes since migration). "claude_haiku" passes bypass
    # this and hit the API natively.
    if CLAUDE_MANUAL_MODE and active_provider == "claude":
        import re
        _safe_stem = re.sub(r'[^A-Za-z0-9_-]', '_', context_header)
        _safe_stem = re.sub(r'_+', '_', _safe_stem).strip('_')
        _manual_filename = f"CLAUDE_MANUAL_{_safe_stem}.txt"

        # CLIPBOARD-LISTEN-ONLY RESUME GATE
        # Fires when the user resumed at this exact (phase, pass) with style="listen".
        # Suppresses prompt-write, notepad-open, browser-launch, and pyautogui paste —
        # falls through to the existing Ghost Hook clipboard watcher which captures the
        # already-visible reply from the user's existing Claude.ai tab.
        is_listen_target = (
            RESUME_STYLE == "listen"
            and RESUME_PHASE is not None and phase_int == RESUME_PHASE
            and RESUME_PASS is not None and pass_num is not None
            and pass_num == RESUME_PASS
        )

        if not is_listen_target:
            with open(_manual_filename, "w", encoding="utf-8") as _mf:
                _mf.write(full_prompt)

            print("\n" + "=" * 60)
            print(f" [MANUAL MODE] Claude call intercepted: {context_header}")
            print(f" [MANUAL MODE] Provider: {active_provider.upper()}")
            print(f" [MANUAL MODE] Prompt saved to: {_manual_filename}")
            print(" [MANUAL MODE] Steps: open file → copy contents → paste into")
            print("                 Claude.ai → copy response → paste back into")
            print(f"                {_manual_filename} → save → press ENTER here.")
            print("=" * 60)

            # 1. Open the text file first to give it the best chance at focus
            if os.name == 'nt':
                os.startfile(_manual_filename)
            else:
                subprocess.call(('open', _manual_filename))

            # 2. The "Notepad Breath" (Wait for editor to render)
            time.sleep(3.0)

            # 3. Native Copy (all phases)
            try:
                import pyautogui
                pyautogui.hotkey('ctrl', 'a')
                time.sleep(0.3)
                pyautogui.hotkey('ctrl', 'c')
                print(" [>] Native Copy: Prompt captured to clipboard.")
            except ImportError:
                print(" [!] pyautogui not found. Install it for auto-copy support.")
            except Exception as _pag_e:
                print(f" [!] Auto-copy skipped ({_pag_e}). Copy prompt manually.")

            # 4. Beeps PARKED (Automation is now the primary driver)
            # if phase in ["P4", "P5"]:
            #     winsound.Beep(1000, 300)
            #     winsound.Beep(1500, 400)

            # 5. Launch Browser with Account Rotation (Round Robin)
            # Cycles through browsers to utilize different logged-in accounts
            browsers = [
                "msedge.exe",  # Edge is in PATH via registry, short name works
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files\Opera\opera.exe",
            ]
            b_idx = 0
            if os.path.exists(".browser_idx"):
                try:
                    with open(".browser_idx", "r") as f:
                        b_idx = int(f.read().strip())
                except:
                    b_idx = 0

            target_browser = browsers[b_idx % len(browsers)]
            # Increment and save for the next call (even across different script runs)
            with open(".browser_idx", "w") as f:
                f.write(str(b_idx + 1))

            _browser_label = os.path.splitext(os.path.basename(target_browser))[0].upper()
            print(f" [>] Rotation: Launching {_browser_label} for account load-balancing...")

            # Use 'start' with quotes for the title and the executable name for reliability
            subprocess.Popen(f'start "" "{target_browser}" https://claude.ai/new', shell=True)

            # Resolve one-shot auto-submit flag BEFORE try block so it is always consumed.
            # Also checks cross-process flag file (survives phase subprocess boundaries).
            global _AUTO_SUBMIT_ONCE
            if not _AUTO_SUBMIT_ONCE and os.path.exists(_AUTO_SUBMIT_FLAG_FILE):
                _AUTO_SUBMIT_ONCE = True
                try:
                    os.remove(_AUTO_SUBMIT_FLAG_FILE)
                except Exception:
                    pass
            _should_submit = AUTO_SUBMIT or _AUTO_SUBMIT_ONCE
            _AUTO_SUBMIT_ONCE = False  # consumed — resets to False whether or not pyautogui fires

            # 6. Browser Paste + Execute (only if pyautogui available)
            try:
                import pyautogui
                print(" [>] Browser launched. Waiting for page load focus...")
                time.sleep(12.0)

                # 1. Type the command label FIRST (mode-aware when pass_num is known)
                p_num = "".join(filter(str.isdigit, str(phase))) if phase else "?"
                _mode_label = f", Mode {pass_num}" if pass_num is not None else ""
                pyautogui.typewrite(f"Execute Prompt {p_num}{_mode_label}", interval=0.05)
                time.sleep(0.5)

                # 2. Native Paste (prompt lands after the label)
                pyautogui.hotkey('ctrl', 'v')
                time.sleep(1.5)

                # 3. Auto-Submit (PIPELINE_AUTO_SUBMIT global OR one-shot armed by Ghost Hook Cancel)
                if _should_submit:
                    time.sleep(0.5)
                    pyautogui.press('enter')
                    print(f" [>] Auto-Submit: Prompt sent to Claude.")
                else:
                    # Manual-submit mode: give the user time at the keyboard to verify
                    # the paste/typing landed correctly and press Enter themselves
                    # before focus returns to VS Code. Total post-paste window ≈ 5s.
                    time.sleep(3.5)

                # 4. Return Focus to VS Code (Ensures notification visibility)
                # Uses native Windows 'AppActivate' via PowerShell to switch focus by title
                # This prevents opening a new instance/window.
                subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).AppActivate('Visual Studio Code')"], capture_output=True)

                if _should_submit:
                    print(f" [>] Auto-Submit: Phase {p_num} submitted. Focus returned to VS Code.")
                else:
                    print(f" [>] Automation: Phase {p_num} staged. Focus returned to VS Code. Submit manually.")
                    if phase not in (None, "P1", "P2", "P3"):
                        send_ntfy(
                            title=f"Phase {p_num} — Submit prompt in browser",
                            message="Prompt staged and clipboard ready. Go submit manually.",
                        )

            except ImportError:
                pass  # already warned above
            except Exception as e:
                print(f" [!] Automation Error: {e}")
        else:
            # ── CLIPBOARD-LISTEN-ONLY BRANCH ──
            # No prompt write, no notepad, no browser launch, no pyautogui paste.
            # Just arm the Ghost Hook watcher (below, shared with prime branch)
            # so the user's next clipboard copy from the existing browser tab is captured.
            # Note: _AUTO_SUBMIT_ONCE is already declared global by the prime branch
            # above; Python's `global` scope is function-wide, so we can assign to it
            # below without re-declaring. (Re-declaring would be a SyntaxError because
            # the name is already used between the first `global` and this point.)
            print("\n" + "=" * 60)
            print(f" [CLIPBOARD-ONLY] Resume — Claude has already replied for {context_header}")
            print(f" [CLIPBOARD-ONLY] Target file: {_manual_filename}")
            print(" [CLIPBOARD-ONLY] No prompt write, no browser launch — clipboard watcher armed.")
            print(" [CLIPBOARD-ONLY] Switch to your existing Claude.ai tab and click Copy on the reply.")
            print("=" * 60)
            # Consume any stale one-shot auto-submit flag from prior crash
            if os.path.exists(_AUTO_SUBMIT_FLAG_FILE):
                try:
                    os.remove(_AUTO_SUBMIT_FLAG_FILE)
                except Exception:
                    pass
            _AUTO_SUBMIT_ONCE = False
            # Notification parity with prime branch (P4/P5 only; same phase exclusion)
            _p_num = "".join(filter(str.isdigit, str(phase))) if phase else "?"
            if phase not in (None, "P1", "P2", "P3"):
                send_ntfy(
                    title=f"Phase {_p_num} — Copy Claude reply from existing browser tab",
                    message="Clipboard-only resume armed. Switch to the existing Claude.ai tab and click Copy on the reply.",
                )

        import pyperclip

        print(f"\n [!] GHOST HOOK ACTIVE — watching clipboard for phase output...")
        print(f" [!] File target: {_manual_filename}")
        print(" [!] Click Copy in Claude.ai to auto-resume. CTRL+C to abort.\n")

        _MIN_PAYLOAD_LENGTH = 800

        _magic_keywords = [
            "ALL DATA PROCESSED",       # EOF line — P1–P4 Mode 1 outputs
            "HARVESTER v",              # Agent version tag — P1
            "DRAFTSMAN v",              # Agent version tag — P2 Mode 1
            "FORMULATOR v",             # Agent version tag — P3 Mode 1
            "REVERSE ENGINEER v",       # Agent version tag — P4 Mode 1
            "</final_logic_package>",   # P2 Mode 2 (Paranoia audit / surgical patches)
            "SENTINEL AUDIT REPORT",    # P5 Mode 1 Auditor — table header
            "MASTER SENTINEL LEDGER",   # P5 Mode 1 Auditor — section anchor
            "SURGEON RECONSTRUCTION",   # P5 Mode 2 (Surgeon) — in "[EOF - SURGEON RECONSTRUCTION COMPLETE]"
        ]

        # LISTEN resume seeds empty: the reply is ALREADY on the clipboard (that is the
        # branch's premise), so seeding from it would mask the payload we came to capture.
        _last_clipboard = "" if is_listen_target else pyperclip.paste()

        while True:
            try:
                _current_clip = pyperclip.paste()
            except Exception:
                time.sleep(1.2)
                continue

            if (
                _current_clip != _last_clipboard
                and len(_current_clip) >= _MIN_PAYLOAD_LENGTH
                and any(k in _current_clip for k in _magic_keywords)
            ):
                import re as _re
                # Collapse 3+ consecutive newlines → 2 (single blank line).
                # Claude.ai's copy button serializes rendered HTML into triple+
                # newlines between paragraphs. This normalizes without destroying
                # intentional blank separators between YAML blocks.
                _current_clip_clean = _re.sub(r'\n{3,}', '\n\n', _current_clip.strip())
                _current_clip_clean = _current_clip_clean.replace('\r\n', '\n').replace('\r', '\n')
                try:
                    winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
                except Exception:
                    print('\a', end='', flush=True)
                _ps_dialog = (
                    "Add-Type -AssemblyName PresentationFramework; "
                    f"$r=[System.Windows.MessageBox]::Show("
                    f"'Payload detected ({len(_current_clip_clean)} chars). Is this the Claude reply?  |  [Cancel] = Yes + auto-submit next',"
                    f"'Ghost Hook','YesNoCancel','Question'); "
                    "if($r -eq 'Yes'){"
                    "$null=(New-Object -ComObject WScript.Shell).AppActivate('Visual Studio Code');"
                    "Write-Output 'YES'"
                    "}elseif($r -eq 'Cancel'){"
                    "$null=(New-Object -ComObject WScript.Shell).AppActivate('Visual Studio Code');"
                    "Write-Output 'YES_AUTO'"
                    "}else{Write-Output 'NO'}"
                )
                print(f"\n [?] Payload detected ({len(_current_clip_clean)} chars) — confirm in popup...")
                _dialog_result = subprocess.run(
                    ["powershell", "-Command", _ps_dialog],
                    capture_output=True, text=True
                ).stdout.strip()
                if _dialog_result in ("YES", "YES_AUTO"):
                    print(f"\n [v] Confirmed — writing to {_manual_filename}...")
                    with open(_manual_filename, "w", encoding="utf-8") as _mf:
                        _mf.write(_current_clip_clean)
                    if os.path.getsize(_manual_filename) > 0:
                        if _dialog_result == "YES_AUTO":
                            _AUTO_SUBMIT_ONCE = True
                            try:  # cross-process persistence: survives subprocess boundary
                                open(_AUTO_SUBMIT_FLAG_FILE, 'w').close()
                            except Exception:
                                pass
                            print(f" [v] File secured. Auto-submit ARMED for next prompt. Resuming pipeline...")
                        else:
                            print(f" [v] File secured. Focus returned to VS Code. Resuming pipeline...")
                        LAST_ACTIVE_MODEL = "MANUAL_CLAUDE_WEB"
                        return _current_clip_clean
                    else:
                        print(" [!] Write failed — file is empty. Retrying on next clipboard change.")
                        _last_clipboard = _current_clip
                else:
                    print(" [~] False positive — cooldown 3s to absorb pending copies...")
                    time.sleep(3.0)
                    _last_clipboard = pyperclip.paste()
                    print(" [~] Resuming clipboard watch...")

            time.sleep(1.2)

    roster, timeout_matrix = _active_roster(active_provider)

    while True:  # OUTER ATTEMPT LOOP (Memory-Safe Retry)

        cascade_failed = False
        if model_override and model_override in roster:
            start_index = roster.index(model_override)
        elif (model_override is None and active_provider == "gemini"
              and GEMINI_OVERRIDE_START_MODEL is not None
              and GEMINI_OVERRIDE_START_MODEL in roster):
            start_index = roster.index(GEMINI_OVERRIDE_START_MODEL)
            print(f" [~] Gemini cascade starting from: {GEMINI_OVERRIDE_START_MODEL}")
        else:
            start_index = 0

        current_index = start_index
        while current_index < len(roster):
            model_id = roster[current_index]
            print(f" [>] Interfacing with: {model_id}  [{active_provider.upper()}]...")

            if active_provider == "gemini":
                # ── Threaded keep-alive path: Gemini call runs in background ──
                result_holder = [None]
                error_holder  = [None]
                finished      = threading.Event()
                start_time    = time.time()

                def _worker():
                    try:
                        result_holder[0] = _call_model(model_id, 7200000, full_prompt, active_provider)
                    except Exception as _e:
                        error_holder[0] = _e
                    finally:
                        finished.set()

                threading.Thread(target=_worker, daemon=True).start()

                stop_ticker = threading.Event()
                def _ticker():
                    while not stop_ticker.is_set():
                        elapsed_live = time.time() - start_time
                        mins, secs = divmod(int(elapsed_live), 60)
                        print(f"\r [~] Waiting... {mins:02d}:{secs:02d}", end="", flush=True)
                        time.sleep(1)
                ticker_thread = threading.Thread(target=_ticker, daemon=True)
                ticker_thread.start()

                if GEMINI_UNLIMITED_WAIT:
                    check_s = None
                elif GEMINI_CHECK_INTERVAL_S is not None:
                    check_s = GEMINI_CHECK_INTERVAL_S
                else:
                    check_s = timeout_matrix.get(model_id, 600000) / 1000

                is_last = (current_index == len(roster) - 1)
                action = None

                while True:
                    try:
                        done = finished.wait(timeout=check_s)
                        interrupted = False
                    except KeyboardInterrupt:
                        done = finished.is_set()
                        interrupted = True

                    stop_ticker.set()
                    ticker_thread.join()
                    elapsed = time.time() - start_time

                    if done:
                        if interrupted and not error_holder[0]:
                            winsound.Beep(1000, 200)
                            print(f"\r [v] Gemini responded just as you interrupted! Auto-resuming...{' ' * 10}")
                        if error_holder[0]:
                            print(f"\r [!] {model_id} HANG/ERROR after {elapsed:.1f} seconds.{' ' * 10}")
                            action = 'ERROR'
                        else:
                            if not interrupted:
                                print(f"\r [v] Success: Response generated in {elapsed:.1f} seconds.{' ' * 10}")
                            action = 'SUCCESS'
                        break

                    mins, secs = divmod(int(elapsed), 60)
                    trigger = "Interrupted by user" if interrupted else f"still running after {mins:02d}:{secs:02d}"
                    print(f"\r [!] {model_id} {trigger} (thread alive).{' ' * 10}")

                    winsound.Beep(400, 250)
                    cascade_part = f"| [C] Force Cascade to {roster[current_index + 1]} " if not is_last else ""
                    prompt_str = (
                        f"\n [!] {model_id} still active — Gemini may still be computing\n"
                        f" [?] [W] Keep Waiting {cascade_part}| [ENTER] Kill+Retry | [A] Airlock >> "
                    )
                    choice = _prompt_nonblocking(prompt_str, finished)

                    if choice == 'AUTO_RESUME':
                        elapsed = time.time() - start_time
                        if error_holder[0]:
                            print(f"\r [!] {model_id} completed with error ({elapsed:.1f}s).{' ' * 10}")
                            action = 'ERROR'
                        else:
                            winsound.Beep(1000, 200)
                            print(f"\r [v] Auto-resumed: {model_id} responded ({elapsed:.1f}s).{' ' * 10}")
                            action = 'SUCCESS'
                        break
                    elif choice == 'C' and not is_last:
                        action = 'CASCADE'
                        break
                    elif choice == 'A':
                        action = 'AIRLOCK'
                        break
                    elif choice == 'W':
                        print(f" [>] Continuing to wait for {model_id}...")
                        check_s = 7200
                        stop_ticker = threading.Event()
                        ticker_thread = threading.Thread(target=_ticker, daemon=True)
                        ticker_thread.start()
                    else:
                        print(f" [>] Abandoning call, retrying {model_id} fresh...")
                        action = 'RETRY_KILL'
                        break

                if action == 'SUCCESS':
                    time.sleep(GEMINI_WAIT_TIME)
                    LAST_ACTIVE_MODEL = model_id
                    return result_holder[0]
                elif action == 'CASCADE':
                    current_index += 1
                elif action == 'AIRLOCK':
                    cascade_failed = True
                    break
                elif action == 'RETRY_KILL':
                    pass
                elif action == 'ERROR':
                    if current_index == len(roster) - 1:
                        print(" [!] All models exhausted.")
                        cascade_failed = True
                        break
                    if DISABLE_CASCADE:
                        winsound.Beep(400, 250)
                        next_model = roster[current_index + 1]
                        print(f"\n [!] Cascade is DISABLED. Current: {model_id} | Next: {next_model}")
                        choice = input(f" [?] [ENTER] Retry {model_id} | [C] Force Cascade | [A] Airlock >> ").strip().upper()
                        if choice == 'C':
                            print(f" [>] Forcing failover to {next_model}...")
                            current_index += 1
                        elif choice == 'A':
                            cascade_failed = True
                            break
                        # else: retry same model (current_index unchanged)
                    else:
                        next_model = roster[current_index + 1]
                        print(f" [>] Failover: Cascading to {next_model}...")
                        current_index += 1

            else:
                # ── Blocking path: Claude / Claude Haiku (unchanged) ──
                start_time = time.time()

                stop_ticker = threading.Event()
                def _ticker():
                    while not stop_ticker.is_set():
                        elapsed_live = time.time() - start_time
                        mins, secs = divmod(int(elapsed_live), 60)
                        print(f"\r [~] Waiting... {mins:02d}:{secs:02d}", end="", flush=True)
                        time.sleep(1)
                ticker_thread = threading.Thread(target=_ticker, daemon=True)
                ticker_thread.start()

                try:
                    timeout = timeout_matrix.get(model_id, 600)
                    text = _call_model(model_id, timeout, full_prompt, active_provider)

                    stop_ticker.set()
                    ticker_thread.join()
                    elapsed = time.time() - start_time
                    print(f"\r [v] Success: Response generated in {elapsed:.1f} seconds.{' ' * 10}")
                    time.sleep(CLAUDE_WAIT_TIME)

                    LAST_ACTIVE_MODEL = model_id
                    return text

                except Exception as e:
                    stop_ticker.set()
                    ticker_thread.join()
                    elapsed = time.time() - start_time
                    print(f"\r [!] {model_id} HANG/ERROR after {elapsed:.1f} seconds.{' ' * 10}")

                    if current_index == len(roster) - 1:
                        print(" [!] All models exhausted.")
                        cascade_failed = True
                        break

                    if DISABLE_CASCADE:
                        winsound.Beep(400, 250)
                        next_model = roster[current_index + 1]
                        print(f"\n [!] Cascade is DISABLED. Current: {model_id} | Next: {next_model}")
                        choice = input(f" [?] [ENTER] Retry {model_id} | [C] Force Cascade | [A] Airlock >> ").strip().upper()

                        if choice == 'C':
                            print(f" [>] Forcing failover to {next_model}...")
                            current_index += 1
                        elif choice == 'A':
                            cascade_failed = True
                            break
                        else:
                            print(f" [>] Retrying {model_id}...")
                            continue
                    else:
                        next_model = roster[current_index + 1]
                        print(f" [>] Failover: Cascading to {next_model}...")
                        current_index += 1

        if not cascade_failed:
            break

        # UNIFIED AIRLOCK
        clear_screen()
        print('\a', end='', flush=True)
        ui_alert(f"AIRLOCK ACTIVATED: {context_header}")

        with open("API_AIRLOCK.txt", "w", encoding="utf-8") as f:
            f.write(full_prompt)

        winsound.Beep(1000, 300)
        winsound.Beep(1000, 300)
        print(f"\n [>] AIRLOCK TRIGGERED IN: {context_header}")
        print(" [>] Prompt saved to API_AIRLOCK.txt")
        print(" [>] ACTION: Paste response into API_AIRLOCK.txt, SAVE, and hit ENTER.")

        retry_requested = False
        while True:
            choice = input("\n [?] Press ENTER when SAVED, or 'R' to RETRY WATERFALL >> ").strip().upper()

            if choice == 'R':
                print(" [>] Restarting Waterfall...")
                retry_requested = True
                break

            if os.path.exists("API_AIRLOCK.txt"):
                with open("API_AIRLOCK.txt", "r", encoding="utf-8") as f:
                    manual_response = f.read().strip()

                if manual_response and manual_response != full_prompt.strip():
                    LAST_ACTIVE_MODEL = "MANUAL_AIRLOCK"
                    return manual_response
                else:
                    print(" [!] File unchanged. Please paste/save response before pressing ENTER.")

        if retry_requested:
            continue

# Alias so phase scripts can call config.call_llm() interchangeably
call_llm = call_gemini