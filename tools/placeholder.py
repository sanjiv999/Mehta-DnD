"""Procedural SVG placeholder art so the site never has an empty frame.

Each placeholder is a soft gradient in the campaign's accent colour with a motif by kind and the
title set in large serif. Replace it by dropping a real image into campaigns/<id>/images/<slot>.png.
"""
from __future__ import annotations
import colorsys
import html
import textwrap


def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(max(0, min(1, c)) * 255) for c in rgb)


def shades(accent: str):
    r, g, b = _hex_to_rgb(accent)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    dark = _rgb_to_hex(colorsys.hls_to_rgb(h, max(0.12, l * 0.45), min(1, s * 1.1)))
    mid = _rgb_to_hex(colorsys.hls_to_rgb(h, l, s))
    light = _rgb_to_hex(colorsys.hls_to_rgb((h + 0.08) % 1, min(0.85, l * 1.6 + 0.2), s * 0.8))
    glow = _rgb_to_hex(colorsys.hls_to_rgb((h + 0.12) % 1, 0.9, 0.7))
    return dark, mid, light, glow


MOTIFS = {
    "cover": lambda d, m, l, g: f'<circle cx="640" cy="300" r="140" fill="{g}" opacity=".9"/>'
                                 f'<path d="M0 520 Q 200 400 400 500 T 800 480 T 1280 520 V720 H0Z" fill="{d}" opacity=".85"/>'
                                 f'<path d="M0 600 Q 300 540 640 600 T 1280 580 V720 H0Z" fill="{m}" opacity=".9"/>',
    "chapter": lambda d, m, l, g: f'<circle cx="980" cy="200" r="90" fill="{g}" opacity=".9"/>'
                                   f'<path d="M0 560 L 260 380 L 480 520 L 700 340 L 940 540 L 1280 400 V720 H0Z" fill="{d}" opacity=".8"/>',
    "scene": lambda d, m, l, g: f'<rect x="80" y="80" width="1120" height="560" rx="24" fill="none" stroke="{g}" stroke-width="6" opacity=".7"/>'
                                 f'<circle cx="200" cy="200" r="60" fill="{g}" opacity=".8"/>',
    "npc": lambda d, m, l, g: f'<circle cx="640" cy="330" r="150" fill="{g}" opacity=".9"/>'
                               f'<path d="M 380 720 Q 640 440 900 720 Z" fill="{d}" opacity=".9"/>',
    "location": lambda d, m, l, g: f'<path d="M0 600 L 300 300 L 520 520 L 760 260 L 1000 500 L 1280 360 V720 H0Z" fill="{d}" opacity=".85"/>'
                                    f'<circle cx="1080" cy="160" r="70" fill="{g}" opacity=".9"/>',
    "map": lambda d, m, l, g: f'<path d="M100 600 C 300 300, 600 650, 900 300 S 1200 400, 1180 150" fill="none" stroke="{g}" stroke-width="8" stroke-dasharray="20 14" opacity=".8"/>',
    "portrait": lambda d, m, l, g: f'<circle cx="640" cy="300" r="160" fill="{g}" opacity=".9"/>'
                                    f'<path d="M 360 720 Q 640 420 920 720 Z" fill="{d}" opacity=".9"/>',
}


def placeholder_svg(title: str, accent: str = "#0f766e", kind: str = "scene", subtitle: str = "") -> str:
    d, m, l, g = shades(accent or "#0f766e")
    motif = MOTIFS.get(kind, MOTIFS["scene"])(d, m, l, g)
    size = 64 if len(title) < 28 else 48 if len(title) < 48 else 36
    lines = textwrap.wrap(title, 28 if size == 64 else 40 if size == 48 else 56)[:3] if title else []
    y0 = 360 - (len(lines) - 1) * size * 0.6
    text = "".join(f'<text x="640" y="{y0 + i * size * 1.2:.0f}" text-anchor="middle" font-family="Cormorant Garamond, Georgia, serif" '
                   f'font-size="{size}" font-weight="700" fill="#fff" opacity=".95">{html.escape(ln)}</text>' for i, ln in enumerate(lines))
    sub = (f'<text x="640" y="640" text-anchor="middle" font-family="Nunito, sans-serif" font-size="22" fill="#fff" '
           f'opacity=".7">{html.escape(subtitle)}</text>') if subtitle else ""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720" width="1280" height="720">
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{m}"/><stop offset="1" stop-color="{d}"/></linearGradient></defs>
<rect width="1280" height="720" fill="url(#bg)"/>{motif}{text}{sub}
<text x="640" y="690" text-anchor="middle" font-family="Nunito, sans-serif" font-size="16" fill="#fff" opacity=".45">placeholder art · generate with tools/images.py</text>
</svg>'''
