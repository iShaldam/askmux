#!/usr/bin/env python3
"""re-render docs/probe-demo.gif from a real `probe.sh opencode` run.
needs Pillow (dev only). opencode because its model is free.
  python3 scripts/demo_gif.py           # runs the probe, then draws
  python3 scripts/demo_gif.py <log>     # draw from a saved run (runs/*-opencode.jsonl)
the frames replay the real command output, they are not a live recording."""
import re, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent.parent
FONT = "/System/Library/Fonts/Menlo.ttc"  # mac; change the path elsewhere
bg, fg, dim, grn, red = (24, 26, 31), (220, 223, 228), (120, 126, 138), (130, 200, 130), (235, 120, 110)

cmd = "bash scripts/probe.sh opencode"
if len(sys.argv) > 1:
    log = Path(sys.argv[1]).resolve()
    probe_out = f"probe: opencode  -> 1 (log: runs/{log.name})"
else:
    r = subprocess.run(cmd.split(), cwd=root, capture_output=True, text=True)
    probe_out = r.stdout.strip().splitlines()[-1]
    log = root / re.search(r"log: (\S+)\)", probe_out).group(1)
cmd2 = "grep -o '\"text\":\"[^\"]*\"' runs/*-opencode.jsonl"
texts = re.findall(r'"text":"[^"]*"', log.read_text())
out2 = texts[-1] if texts else "(no text in log)"
note = "exit 1 = the model says it has no ask-the-user tool"
out_col = red if " -> 1 " in probe_out else grn

f = ImageFont.truetype(FONT, 15)
def frame(lines):
    im = Image.new("RGB", (720, 190), bg); d = ImageDraw.Draw(im)
    for i, (t, c) in enumerate(lines):
        d.text((16, 14 + i * 24), t, font=f, fill=c)
    return im

fr, dur = [], []
def add(lines, ms): fr.append(frame(lines)); dur.append(ms)

add([("$ ", fg)], 500)
for n in range(2, len(cmd) + 1, 3): add([("$ " + cmd[:n], fg)], 70)
add([("$ " + cmd, fg)], 400)
for k in range(3): add([("$ " + cmd, fg), ("running" + "." * (k + 1), dim)], 700)
L = [("$ " + cmd, fg), (probe_out, out_col)]
add(L, 1200)
for n in range(2, len(cmd2) + 1, 4): add(L + [("$ " + cmd2[:n], fg)], 60)
add(L + [("$ " + cmd2, fg)], 300)
L2 = L + [("$ " + cmd2, fg), (out2, grn)]
add(L2, 900)
add(L2 + [("", fg), (note, dim)], 3500)
out = root / "docs" / "probe-demo.gif"
fr[0].save(out, save_all=True, append_images=fr[1:], duration=dur, loop=0, optimize=True, disposal=1)
print(f"demo_gif: {out.relative_to(root)} {out.stat().st_size // 1024} KB")
