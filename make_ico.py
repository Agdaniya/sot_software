"""
Generates logo.ico, logo_small.bmp and logo_banner.bmp from ui/logo.PNG.
Run from the sot_software/ directory:  python make_ico.py
"""
import struct, io, os
from PIL import Image

_ui  = os.path.join(os.path.dirname(__file__), "ui")
src  = os.path.join(_ui, "logo.PNG")
dst  = os.path.join(_ui, "logo.ico")

img = Image.open(src).convert("RGBA")
sizes = [16, 24, 32, 48, 64, 128, 256]

# Render each size as a PNG blob (ICO supports embedded PNG for sizes ≥ 32)
png_frames = []
for s in sizes:
    frame = img.resize((s, s), Image.LANCZOS)
    buf = io.BytesIO()
    frame.save(buf, format="PNG")
    png_frames.append(buf.getvalue())

# Build ICO manually — Pillow's ICO writer is unreliable for multi-size files
n = len(sizes)
header = struct.pack("<HHH", 0, 1, n)          # reserved=0, type=1 (ICO), count=n

dir_entries = b""
offset = 6 + 16 * n                             # data starts after header + all dir entries
for s, data in zip(sizes, png_frames):
    w = s if s < 256 else 0                     # 256 is encoded as 0 per ICO spec
    dir_entries += struct.pack(
        "<BBBBHHIi",
        w, w,           # width, height
        0,              # color count (0 = true-colour)
        0,              # reserved
        1,              # color planes
        32,             # bits per pixel
        len(data),      # size of image data
        offset,         # offset of image data from start of file
    )
    offset += len(data)

with open(dst, "wb") as f:
    f.write(header)
    f.write(dir_entries)
    for data in png_frames:
        f.write(data)

print(f"Created {dst}  ({os.path.getsize(dst):,} bytes, {n} sizes: {sizes})")

# ── logo_small.bmp — 55×58, required by Inno Setup WizardSmallImageFile ──────
img_rgb = img.convert("RGB")
small = img_rgb.resize((55, 58), Image.LANCZOS)
small_path = os.path.join(_ui, "logo_small.bmp")
small.save(small_path, format="BMP")
print(f"Created {small_path}  ({os.path.getsize(small_path):,} bytes, 55×58)")

# ── logo_banner.bmp — 164×314, Inno Setup WizardImageFile (left sidebar) ─────
banner = Image.new("RGB", (164, 314), (30, 42, 58))   # dark navy #1e2a3a
logo_sized = img_rgb.resize((110, 110), Image.LANCZOS)
banner.paste(logo_sized, ((164 - 110) // 2, 80))
banner_path = os.path.join(_ui, "logo_banner.bmp")
banner.save(banner_path, format="BMP")
print(f"Created {banner_path}  ({os.path.getsize(banner_path):,} bytes, 164×314)")
