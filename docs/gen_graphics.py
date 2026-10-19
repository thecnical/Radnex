"""Regenerate the animated Radnex README graphics (docs/hero.svg, docs/terminal.svg, docs/radnex-3d-arch.svg).

Run:  python docs/gen_graphics.py   (from repo root)

All files are plain, self-contained SVG — no external assets, no JS. GitHub
renders the CSS animations in place. Every animation is layered ON TOP of a
fully-visible base state.
"""
import random, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from radnex.ui.banner import FONT, FONT_HEIGHT

OUT = Path(__file__).resolve().parent
BG, GRID, GREEN, DIM, ACCENT, AMBER, CYAN = (
    "#040704", "#0a1a0d", "#00ff41", "#0c5a22", "#7dffb0", "#ffb000", "#00e5ff"
)

# ------------------------------------------------------------ hero.svg ------
W, H = 1280, 440
word, GW, SP, cell = "RADNEX", 6, 1, 24
total_cells = len(word) * GW + (len(word) - 1) * SP
x0 = (W - total_cells * cell) / 2
y0 = 118

glyphs = []
for gi, ch in enumerate(word):
    gx = x0 + gi * (GW + SP) * cell
    rects = []
    for r in range(FONT_HEIGHT):
        row, c = FONT[ch][r], 0
        while c < len(row):
            if row[c] == "█":
                run = 0
                while c + run < len(row) and row[c + run] == "█":
                    run += 1
                rects.append(f'<rect x="{gx + c*cell:.0f}" y="{y0 + r*cell}" '
                             f'width="{run*cell}" height="{cell}"/>')
                c += run
            else:
                c += 1
    # base opacity is 1 — the animation only adds a glitch flicker on top.
    glyphs.append(f'<g class="gl" style="animation-delay:{gi*0.11:.2f}s">'
                  + "".join(rects) + "</g>")
banner = "\n      ".join(glyphs)

random.seed(42)
rain = "\n      ".join(
    f'<text class="rain" x="{18 + i*37 + random.randint(-6,6)}" y="-150" '
    f'style="animation-duration:{random.uniform(3.4,8.2):.2f}s;'
    f'animation-delay:-{random.uniform(0,6):.2f}s">'
    + "".join(random.choice("0123456789ABCDEF") for _ in range(9)) + "</text>"
    for i in range(34))

sub_y = 300
hero_svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="RADNEX">
  <defs>
    <filter id="glow" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="7" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
    <linearGradient id="rainfade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{GREEN}" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="{GREEN}" stop-opacity="0.04"/>
    </linearGradient>
    <linearGradient id="band" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%"   stop-color="{ACCENT}" stop-opacity="0"/>
      <stop offset="50%"  stop-color="#ffffff" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="{ACCENT}" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%"   stop-color="{GREEN}" stop-opacity="0"/>
      <stop offset="50%"  stop-color="{GREEN}" stop-opacity="0.42"/>
      <stop offset="100%" stop-color="{GREEN}" stop-opacity="0"/>
    </linearGradient>
    <clipPath id="frame"><rect x="0" y="0" width="{W}" height="{H}" rx="12"/></clipPath>
  </defs>

  <style>
    .rain {{ font: 16px ui-monospace, Menlo, Consolas, monospace;
             fill: url(#rainfade); animation: fall linear infinite; }}
    @keyframes fall {{ from {{ transform: translateY(0); }} to {{ transform: translateY({H+270}px); }} }}

    .gl rect {{ fill: {GREEN};
                animation: flicker 7s steps(1,end) infinite; }}
    @keyframes flicker {{
      0%, 88%   {{ opacity: 1; }}
      89%       {{ opacity: 0.62; }}
      90%       {{ opacity: 1; }}
      91%       {{ opacity: 0.38; }}
      92%, 100% {{ opacity: 1; }}
    }}

    .halo {{ animation: halo 3.6s ease-in-out infinite; }}
    @keyframes halo {{ 0%,100% {{ opacity: .45; }} 50% {{ opacity: .95; }} }}

    .band {{ animation: band 3.8s cubic-bezier(.4,0,.2,1) infinite; }}
    @keyframes band {{ 0% {{ transform: translateX(-{W}px); }}
                       55%,100% {{ transform: translateX({W}px); }} }}

    .sweep {{ animation: sweep 5.4s linear infinite; }}
    @keyframes sweep {{ 0% {{ transform: translateY(-90px); }} 100% {{ transform: translateY({H+90}px); }} }}

    .cur {{ animation: blink 1.05s steps(1,end) infinite; }}
    @keyframes blink {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: 0; }} }}

    .tag, .meta {{ paint-order: stroke; stroke: {BG}; stroke-width: 5;
                   stroke-linejoin: round; }}
    .tag {{ font: 700 16px ui-monospace, Menlo, Consolas, monospace;
            letter-spacing: 3.5px; fill: {ACCENT}; }}
    .meta {{ font: 13px ui-monospace, Menlo, Consolas, monospace;
             letter-spacing: 1.8px; fill: {DIM}; }}

    @media (prefers-reduced-motion: reduce) {{
      .rain, .gl rect, .band, .sweep, .cur, .halo {{ animation: none; }}
    }}
  </style>

  <g clip-path="url(#frame)">
    <rect width="{W}" height="{H}" fill="{BG}"/>
    <g opacity="0.45">{"".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="{GRID}"/>' for y in range(0, H, 26))}</g>
    <g opacity="0.32">{rain}</g>

    <g filter="url(#glow)" class="halo">{banner}</g>

    <rect class="band" x="0" y="{y0-16}" width="300" height="{FONT_HEIGHT*cell+32}"
          fill="url(#band)" style="mix-blend-mode:screen"/>
    <rect class="sweep" x="0" y="0" width="{W}" height="90" fill="url(#scan)"/>

    <text class="tag" x="{W/2:.0f}" y="{sub_y}" text-anchor="middle">AUTONOMOUS CYBER WARFARE &amp; CODING ENGINE</text>
    <rect class="cur" x="{W/2 + 276:.0f}" y="{sub_y-16}" width="10" height="19" fill="{ACCENT}"/>

    <text class="meta" x="{W/2:.0f}" y="348" text-anchor="middle">ZERO-DOWNTIME ROUTING · DUAL-TIER INTELLIGENCE · SHADOW CHECKPOINTS · MULTI-GATEWAY MESH</text>
    <text class="meta" x="{W/2:.0f}" y="378" text-anchor="middle" opacity="0.9" style="fill: {CYAN};">Architected by Chandan Pandey (@thecnical)</text>

    <rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{DIM}" stroke-opacity="0.55"/>
  </g>
</svg>
'''
(OUT / "hero.svg").write_text(hero_svg)

# ------------------------------------------------------------ terminal.svg --
LINES = [
    ("prompt",  "recon the target, map endpoints, and test authorization boundary"),
    ("dim",     "· routing through APInex + Radox AI mesh · ephemeral cache active"),
    ("tool",    "bash  nmap -sV -T4 --script http-enum,http-headers target.example.com"),
    ("ok",      "✓ 4 services live · 12 endpoints discovered · 0 drops"),
    ("tool",    "write_file  assessment/attack-surface.md"),
    ("ok",      "✓ shadow checkpoint captured [cf91a2] · diff applied +96 −0"),
    ("info",    "scout + architect · 0 latency stall · $0.0000 (100% free router)"),
]

def terminal() -> str:
    TW, TH = 1100, 430
    pad, lh, top = 34, 34, 104
    rows = []
    for i, (kind, text) in enumerate(LINES):
        delay = 0.55 + i * 0.62
        color = {"prompt": GREEN, "dim": DIM, "tool": ACCENT,
                 "ok": GREEN, "info": AMBER}[kind]
        prefix = "› " if kind == "prompt" else ("  " if kind in ("ok", "dim") else "$ ")
        esc = (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        rows.append(
            f'<text class="ln" x="{pad}" y="{top + i*lh}" fill="{color}" '
            f'style="animation-delay:{delay:.2f}s">{prefix}{esc}</text>'
        )
    body = "\n      ".join(rows)
    last_y = top + (len(LINES) - 1) * lh

    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {TW} {TH}" width="{TW}" height="{TH}" role="img" aria-label="RADNEX session">
  <defs>
    <clipPath id="tframe"><rect x="0" y="0" width="{TW}" height="{TH}" rx="12"/></clipPath>
    <filter id="tglow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="3.5" result="b"/>
      <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <style>
    .ln {{ font: 16px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
           animation: rise .5s ease-out backwards; }}
    @keyframes rise {{ from {{ transform: translateY(8px); }}
                       to   {{ transform: translateY(0); }} }}
    .cur {{ animation: blink 1.05s steps(1,end) infinite; }}
    @keyframes blink {{ 0%,49% {{ opacity: 1; }} 50%,100% {{ opacity: 0; }} }}
    .title {{ font: 700 14px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
              letter-spacing: 2px; fill: {ACCENT}; }}
    @media (prefers-reduced-motion: reduce) {{
      .ln {{ animation: none; opacity: 1; }} .cur {{ animation: none; }}
    }}
  </style>

  <g clip-path="url(#tframe)">
    <rect width="{TW}" height="{TH}" fill="{BG}"/>
    <rect width="{TW}" height="46" fill="#0a140c"/>
    <circle cx="28" cy="23" r="6.5" fill="#ff5f57"/>
    <circle cx="50" cy="23" r="6.5" fill="#febc2e"/>
    <circle cx="72" cy="23" r="6.5" fill="#28c840"/>
    <text class="title" x="{TW/2:.0f}" y="28" text-anchor="middle">◈ RADNEX v1.0 — autonomous cyber shell</text>
    <line x1="0" y1="46" x2="{TW}" y2="46" stroke="{DIM}" stroke-opacity="0.6"/>

    <text x="{pad}" y="76" fill="{DIM}" style="font:13px ui-monospace,Menlo,monospace;letter-spacing:1.4px">
      ◈ RADNEX   ◆ AUTO   ◆ deepseek-v4.1-flash   ▸ /home/thecnical   ◈ scope on   ⛨ sandbox on
    </text>

      {body}

    <rect class="cur" x="{pad + 2}" y="{last_y + 22}" width="9" height="17" fill="{GREEN}" filter="url(#tglow)"/>

    <line x1="0" y1="{TH-42}" x2="{TW}" y2="{TH-42}" stroke="{DIM}" stroke-opacity="0.6"/>
    <text x="{pad}" y="{TH-17}" fill="{DIM}" style="font:13px ui-monospace,Menlo,monospace">
      ● router: apinex/radox [free]   |   tok ↑24.2k ↓810   |   $ 0.0000   |   turn 4   |   ● idle
    </text>
    <rect x="0.5" y="0.5" width="{TW-1}" height="{TH-1}" rx="12" fill="none" stroke="{DIM}" stroke-opacity="0.55"/>
  </g>
</svg>
'''

(OUT / "terminal.svg").write_text(terminal())

# ------------------------------------------------------------ 3D architecture --
def render_3d_arch() -> str:
    return (OUT / "radnex-3d-arch.svg").read_text(encoding="utf-8")


(OUT / "radnex-3d-arch.svg").write_text(render_3d_arch())
print("Successfully wrote docs/hero.svg, docs/terminal.svg, and docs/radnex-3d-arch.svg")

if __name__ == "__main__":
    pass
