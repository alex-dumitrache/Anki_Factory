import os
import shutil
import datetime


def run_backup(source_dir, total_elapsed=None):
    """Silent post-pipeline workspace freeze.

    Copies every file in source_dir into Archive/<video_num>/.
    Only the Prompts/ subfolder is copied — all other subdirectories
    are ignored. This means new files are automatically included in
    future runs without any maintenance to this script.

    Video number is read from line 1 of notebook_context_bridge.txt.
    Falls back to a timestamp-based folder name if the file is missing
    or its first line is not a plain integer.
    """

    # 1. Read video number
    video_num = datetime.datetime.now().strftime("run_%Y%m%d_%H%M%S")  # safe fallback
    bridge = os.path.join(source_dir, "notebook_context_bridge.txt")
    if os.path.exists(bridge):
        try:
            with open(bridge, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
            # Accept "117" (single) or "120+121" (combined) — split on '+',
            # require all tokens to be integers, take the last token as canonical.
            parts = [p.strip() for p in first_line.split("+")]
            if parts and all(p.isdigit() for p in parts):
                video_num = parts[-1]
        except Exception:
            pass  # keep fallback name

    # 2. Determine archive target — handle re-runs of the same video
    archive_root = os.path.join(source_dir, "Archive")
    os.makedirs(archive_root, exist_ok=True)
    target_dir = os.path.join(archive_root, video_num)
    suffix = 2
    while os.path.exists(target_dir):
        target_dir = os.path.join(archive_root, f"{video_num}_{suffix}")
        suffix += 1

    # 3. Copy — all files pass through; ignore every directory except Prompts
    def ignore_fn(dirpath, contents):
        return {
            name for name in contents
            if os.path.isdir(os.path.join(dirpath, name)) and name != "Prompts"
        }

    shutil.copytree(source_dir, target_dir, ignore=ignore_fn)

    # 4. Write manifest into the archive (after copy so it isn't re-copied next time)
    file_count = sum(len(files) for _, _, files in os.walk(target_dir))
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elapsed_str = ""
    if total_elapsed is not None:
        m, s = divmod(int(total_elapsed), 60)
        elapsed_str = f"\nPipeline Runtime : {m}m {s}s"
    manifest = (
        f"ANKI FACTORY — WORKSPACE FREEZE\n"
        f"{'=' * 40}\n"
        f"Video            : {video_num}\n"
        f"Archived         : {ts}\n"
        f"Files Copied     : {file_count}{elapsed_str}\n"
        f"Archive Path     : {target_dir}\n"
    )
    with open(os.path.join(target_dir, "_MANIFEST.txt"), "w", encoding="utf-8") as f:
        f.write(manifest)

    print(f" [+] Archive saved → Archive\\{os.path.basename(target_dir)}\\ ({file_count} files)")


if __name__ == "__main__":
    run_backup(source_dir=os.path.dirname(os.path.abspath(__file__)))
