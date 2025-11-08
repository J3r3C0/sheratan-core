# -*- coding: utf-8 -*-
"""
Render: docs/gifs/auto-tag-demo.gif
- Sheratan Tech-Noir (anthrazit + türkis)
- 5-Frame Crossfade Transitions
- Glow-Overlay
- Fallback: generiert 5 synthetische Screens (kein externes Bild nötig)
"""
import os, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio.v2 as imageio

OUT = Path("docs/gifs/auto-tag-demo.gif")
W, H = 1280, 720
BG = (16, 18, 22)              # Near-black/anthrazit
TURQ = (0, 195, 212)           # #00C3D4
WHITE = (238, 238, 238)
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "DejaVuSans.ttf",  # falls lokal beigelegt
]

def find_font():
    for p in FONT_PATHS:
        if Path(p).exists():
            return p
    return None

FONT = find_font()
def txt(draw, xy, text, size=42, fill=WHITE, anchor="la"):
    if FONT:
        f = ImageFont.truetype(FONT, size=size)
    else:
        f = ImageFont.load_default()
    draw.text(xy, text, font=f, fill=fill, anchor=anchor)

def rounded_panel(img, xy, radius=18, fill=(26,30,36), outline=TURQ, glow=True):
    x0,y0,x1,y1 = xy
    r = radius
    panel = Image.new("RGBA", (x1-x0, y1-y0), (0,0,0,0))
    pd = ImageDraw.Draw(panel)
    pd.rounded_rectangle([0,0,panel.width-1,panel.height-1], r, fill=fill, outline=outline, width=2)

    if glow:
        # Outer Glow
        glow_layer = Image.new("RGBA", panel.size, (0,0,0,0))
        gd = ImageDraw.Draw(glow_layer)
        gd.rounded_rectangle([2,2,panel.width-3,panel.height-3], r, fill=None, outline=TURQ, width=8)
        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(8))
        panel = Image.alpha_composite(glow_layer, panel)

    img.alpha_composite(panel, (x0,y0))

def header(img, title="Sheratan • Auto-Tag (GitHub Actions)", subtitle="Tech-Noir • turquoise/anthracite"):
    d = ImageDraw.Draw(img)
    txt(d, (60, 60), title, 54, TURQ)
    txt(d, (60, 120), subtitle, 30, (180,200,205))

def step_frame(step_idx, title, bullets):
    img = Image.new("RGBA", (W,H), BG+(255,))
    header(img)
    # Hauptpanel
    x0,y0,x1,y1 = 60, 180, W-60, H-80
    rounded_panel(img, (x0,y0,x1,y1), radius=20, fill=(26,30,36), outline=TURQ, glow=True)
    d = ImageDraw.Draw(img)

    txt(d, (x0+32, y0+28), f"Step {step_idx}: {title}", 44, WHITE)
    y = y0 + 100
    for b in bullets:
        # Bullet • + Text
        txt(d, (x0+42, y), u"•", 36, TURQ)
        txt(d, (x0+80, y), b, 34, (220,225,230))
        y += 46

    # Footer
    txt(d, (x0+32, y1-48), "Sheratan — Auto-Tag via GitHub Actions  |  https://github.com/J3r3C0", 24, (160,170,180))
    return img

def crossfade(a, b, steps=5):
    # erzeugt 5 Übergangsframes
    for i in range(1, steps+1):
        alpha = i/(steps+1.0)
        yield Image.blend(a, b, alpha)

def main():
    steps = [
        ("Open Actions", [
            "Repository → Actions öffnen",
            "Workflow „Auto-Tag“ auswählen"
        ]),
        ("Run Workflow", [
            "Schaltfläche „Run workflow“ wählen",
            "Eingaben prüfen (optional)"
        ]),
        ("Choose Tag", [
            "Tag/Prefix angeben (z. B. sdk-ts-v)",
            "Version oder Auto-Read"
        ]),
        ("Dispatch", [
            "Workflow dispatchen",
            "Logs/Jobs verfolgen"
        ]),
        ("Done", [
            "Tag gepusht, Release (optional) erstellt",
            "Release-Jobs (PyPI/npm/Pages) triggern"
        ]),
    ]

    frames = []
    built = []
    for i, (t, bullets) in enumerate(steps, start=1):
        fr = step_frame(i, t, bullets)
        built.append(fr)

    # Build Timeline: je Step 6 identische Frames (≈0.6s bei 100ms/frame), dazwischen 5 Crossfade
    hold = 6
    for idx, img in enumerate(built):
        frames.extend([img.copy() for _ in range(hold)])
        if idx < len(built)-1:
            frames.extend(list(crossfade(img, built[idx+1], steps=5)))

    # Save GIF
    OUT.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(OUT, [f.convert("RGB") for f in frames], duration=0.1)  # 100ms/Frame

    print(f"✅ Wrote {OUT} ({len(frames)} frames)")

if __name__ == "__main__":
    main()
