"""Regenera los assets de marca en assets/ (logo estático + GIF de 'pensando')
a partir de la misma geometría que el mark del artifact original: una línea
de precios ascendente que resuelve en una gema facetada en la punta.

Uso: venv/Scripts/python.exe scripts/generate_brand_assets.py
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).parent.parent / "assets"

S = 5.12  # escala desde el viewBox 100x100 del mark original
SIZE = 512
INK = (18, 35, 59, 255)   # #12233B
GOLD = (192, 138, 52, 255)  # #C08A34

PATH_POINTS = [(8, 76), (30, 58), (44, 66), (62, 38), (74, 24)]
SCALED_POINTS = [(x * S, y * S) for x, y in PATH_POINTS]
STROKE_WIDTH = round(6 * S)
GEM_HALF_WIDTH = 14 * S
GEM_HALF_HEIGHT = 16 * S


def _gem_polygon(center: tuple[float, float]) -> list[tuple[float, float]]:
    cx, cy = center
    offsets = [(0, -GEM_HALF_HEIGHT), (GEM_HALF_WIDTH, 0), (0, GEM_HALF_HEIGHT), (-GEM_HALF_WIDTH, 0)]
    return [(cx + dx, cy + dy) for dx, dy in offsets]


def _draw_mark(draw: ImageDraw.ImageDraw, line_points: list[tuple[float, float]], gem_center: tuple[float, float]) -> None:
    if len(line_points) > 1:
        draw.line(line_points, fill=INK, width=STROKE_WIDTH, joint="curve")
        radius = STROKE_WIDTH / 2
        for p in line_points:
            draw.ellipse([p[0] - radius, p[1] - radius, p[0] + radius, p[1] + radius], fill=INK)
    draw.polygon(_gem_polygon(gem_center), fill=GOLD)


def generate_static_logo() -> None:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    _draw_mark(draw, SCALED_POINTS, SCALED_POINTS[-1])
    img.save(ASSETS_DIR / "logo.png")

    bbox = img.getbbox()
    pad = 20
    box = (max(bbox[0] - pad, 0), max(bbox[1] - pad, 0), min(bbox[2] + pad, SIZE), min(bbox[3] + pad, SIZE))
    img.crop(box).save(ASSETS_DIR / "logo_cropped.png")


def _point_along_path(t: float) -> tuple[tuple[float, float], int]:
    def dist(a, b):
        return math.hypot(b[0] - a[0], b[1] - a[1])

    seg_lengths = [dist(SCALED_POINTS[i], SCALED_POINTS[i + 1]) for i in range(len(SCALED_POINTS) - 1)]
    total_length = sum(seg_lengths)
    target = t * total_length

    accum = 0.0
    for i, seg_len in enumerate(seg_lengths):
        if accum + seg_len >= target or i == len(seg_lengths) - 1:
            local_t = (target - accum) / seg_len if seg_len > 0 else 0
            local_t = min(max(local_t, 0), 1)
            a, b = SCALED_POINTS[i], SCALED_POINTS[i + 1]
            return (a[0] + (b[0] - a[0]) * local_t, a[1] + (b[1] - a[1]) * local_t), i
        accum += seg_len
    return SCALED_POINTS[-1], len(seg_lengths) - 1


def generate_thinking_gif(n_frames: int = 20, frame_ms: int = 60) -> None:
    """Gema recorriendo la línea de precios de ida y vuelta (ping-pong), en
    loop infinito — para usarse mientras el agente sigue trabajando y la
    duración real de la respuesta es impredecible. La app la reemplaza por
    el logo estático apenas la respuesta está lista, así que este archivo
    nunca necesita 'asentarse' por sí solo."""
    raw_frames = []
    for frame_i in range(n_frames + 1):
        t = frame_i / n_frames
        img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        pos, seg_idx = _point_along_path(t)
        line_points = [SCALED_POINTS[0]] + [SCALED_POINTS[i + 1] for i in range(seg_idx)] + [pos]
        _draw_mark(draw, line_points, pos)
        raw_frames.append(img)

    # ida (0..1) + vuelta (1..0) sin duplicar los extremos, para que el loop
    # no tenga un salto brusco al reiniciar
    ping_pong = raw_frames + raw_frames[-2:0:-1]

    lefts = [f.getbbox()[0] for f in ping_pong if f.getbbox()]
    tops = [f.getbbox()[1] for f in ping_pong if f.getbbox()]
    rights = [f.getbbox()[2] for f in ping_pong if f.getbbox()]
    bottoms = [f.getbbox()[3] for f in ping_pong if f.getbbox()]
    pad = 20
    box = (max(min(lefts) - pad, 0), max(min(tops) - pad, 0), min(max(rights) + pad, SIZE), min(max(bottoms) + pad, SIZE))

    cropped = [f.crop(box) for f in ping_pong]
    cropped[0].save(
        ASSETS_DIR / "logo_thinking.gif",
        save_all=True,
        append_images=cropped[1:],
        duration=frame_ms,
        loop=0,
        disposal=2,
    )


if __name__ == "__main__":
    ASSETS_DIR.mkdir(exist_ok=True)
    generate_static_logo()
    generate_thinking_gif()
    print(f"Assets generados en {ASSETS_DIR}")
