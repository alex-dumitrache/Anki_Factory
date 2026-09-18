"""Image compression + storage for Anki on-card images.

Companion to tts_reader.py (audio). One public function,
store_compressed_image(): resize a source image onto its long edge, save it as
JPEG into Anki's collection.media under a content-hash filename (idempotent +
de-duplicating), and return the bare filename for use in an <img src='...'> tag.

Returns None -- never raises -- when the media dir is unavailable or the image
cannot be read/encoded, so a bad image can never crash a pipeline run. Pillow is
imported lazily inside the function so importing this module never fails on a
machine without Pillow; an image-less run simply never calls in.

Validated against the 2026-06-27 image POC (86-89% size reduction on real
lecture screenshots).
"""

import os
import hashlib

_MAX_EDGE = 1280   # longest side, px
_QUALITY = 90      # JPEG quality


def store_compressed_image(source_path, media_dir):
    """Compress source_path into media_dir; return the bare filename, or None.

    None (never an exception) is returned when media_dir is falsy -- the caller's
    signal that the image feature is disabled -- when Pillow is unavailable, or
    when the source image cannot be read/encoded. Idempotent: the filename is an
    md5 of the source bytes, so the same image reused across cards writes one file
    and re-runs skip the re-encode.
    """
    if not media_dir:
        return None
    try:
        from PIL import Image
    except ImportError:
        print(" [!] Pillow not installed -- image features skipped (pip install Pillow).")
        return None
    try:
        _resample = Image.Resampling.LANCZOS
    except AttributeError:            # Pillow < 9.1
        _resample = Image.LANCZOS
    try:
        with open(source_path, "rb") as fh:
            digest = hashlib.md5(fh.read()).hexdigest()
        filename = "img_" + digest + ".jpg"
        out_path = os.path.join(media_dir, filename)
        if os.path.exists(out_path):
            return filename
        im = Image.open(source_path)
        if im.mode != "RGB":
            # Flatten any transparency onto white (screenshots are usually opaque).
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                base = Image.new("RGB", im.size, (255, 255, 255))
                im = im.convert("RGBA")
                base.paste(im, mask=im.split()[-1])
                im = base
            else:
                im = im.convert("RGB")
        long_edge = max(im.width, im.height)
        if long_edge > _MAX_EDGE:
            scale = _MAX_EDGE / long_edge
            im = im.resize((round(im.width * scale), round(im.height * scale)), _resample)
        im.save(out_path, "JPEG", quality=_QUALITY, optimize=True)
        return filename
    except Exception as exc:
        print(" [!] image compress failed for " + os.path.basename(source_path) + ": " + str(exc))
        return None
