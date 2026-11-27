#!/usr/bin/env python3
"""news-image-20261127: draw Friday 27 November 2026's world news as a
one-page newspaper front page and write it to /output/entry.png.

Pure Python 3 standard library. Deterministic: no time, no randomness, no
network. The picture is drawn from scratch with a hand-rolled 5x7 bitmap
font and a hand-rolled PNG encoder, then written atomically through a
deterministic temporary name and verified (magic, size, dimensions, SHA-256)
before the program exits.
"""

import hashlib
import os
import struct
import zlib

WIDTH = 1024
HEIGHT = 1024
MAX_BYTES = 1048576

# ---------------------------------------------------------------- palette
PAPER = (247, 242, 231)
INK = (18, 18, 18)
RED = (176, 32, 32)
BLUE = (28, 62, 118)
SKY = (198, 220, 236)
DARK = (22, 22, 22)
GREY = (120, 116, 108)
GOLD = (212, 160, 32)
ORANGE = (224, 110, 32)

# ------------------------------------------------------------- 5x7 font
# Each glyph is 7 rows of 5 cells; '#' is ink, '.' is blank. Uppercase
# only; the text helpers uppercase everything before drawing.
FONT = {
    "A": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "&": (".###.", "#...#", "#...#", ".#.#.", "#.#..", "#.#.#", ".##.#"),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".####", ".....", ".####", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", ".###.", "..#..", ".#.#.", "....."),
    "#": (".#.#.", ".#.#.", "#####", ".#.#.", "#####", ".#.#.", "....."),
    "@": (".###.", "#...#", "#.###", "#.#.#", "#.#.#", "#....", ".###."),
    "•": (".....", ".###.", ".###.", ".###.", ".....", ".....", "....."),
}

# Characters the font lacks are folded to these before drawing.
FOLD = {"—": "-", "–": "-", "’": "'", "‘": "'", "“": '"', "”": '"', "…": "."}


def glyph_rows(ch):
    return FONT.get(FOLD.get(ch, ch), FONT[" "])


def text_width(text, scale):
    """Pixel width of text at the given scale (6 px per cell, scaled)."""
    return len(text) * 6 * scale


def draw_text(px, x, y, text, scale, color):
    """Draw text with its top-left corner at (x, y). Returns width drawn."""
    text = text.upper()
    cx = x
    for ch in text:
        rows = glyph_rows(ch)
        for r in range(7):
            row = rows[r]
            for c in range(5):
                if row[c] == "#":
                    fill_rect(px, cx + c * scale, y + r * scale,
                              scale, scale, color)
        cx += 6 * scale
    return cx - x


def draw_text_centred(px, cx, y, text, scale, color):
    w = text_width(text.upper(), scale)
    draw_text(px, cx - w // 2, y, text, scale, color)
    return w


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines fitting max_width."""
    words = text.upper().split()
    lines = []
    cur = ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# ------------------------------------------------------- pixel primitives
def set_px(px, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        i = (y * WIDTH + x) * 3
        px[i], px[i + 1], px[i + 2] = color


def fill_rect(px, x, y, w, h, color):
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(WIDTH, x + w)
    y1 = min(HEIGHT, y + h)
    for yy in range(y0, y1):
        base = (yy * WIDTH + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            px[i], px[i + 1], px[i + 2] = color


def draw_rect(px, x, y, w, h, color, thick=1):
    fill_rect(px, x, y, w, thick, color)
    fill_rect(px, x, y + h - thick, w, thick, color)
    fill_rect(px, x, y, thick, h, color)
    fill_rect(px, x + w - thick, y, thick, h, color)


def draw_line(px, x0, y0, x1, y1, color, thick=1):
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    x, y = x0, y0
    while True:
        fill_rect(px, x - thick // 2, y - thick // 2, thick, thick, color)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x += sx
        if e2 <= dx:
            err += dx
            y += sy


def fill_circle(px, cx, cy, r, color):
    for yy in range(cy - r, cy + r + 1):
        dx = int((r * r - (yy - cy) ** 2) ** 0.5)
        fill_rect(px, cx - dx, yy, 2 * dx + 1, 1, color)


def draw_circle(px, cx, cy, r, color, thick=2):
    for k in range(thick):
        rr = r - k
        if rr <= 0:
            break
        steps = max(8, rr * 6)
        for s in range(steps):
            import math
            a = 2 * math.pi * s / steps
            set_px(px, cx + int(rr * math.cos(a)),
                   cy + int(rr * math.sin(a)), color)


def fill_triangle(px, x0, y0, x1, y1, x2, y2, color):
    xs = sorted([x0, x1, x2])
    for xx in range(xs[0], xs[2] + 1):
        ys = []
        for (ax, ay, bx, by) in ((x0, y0, x1, y1), (x1, y1, x2, y2),
                                 (x2, y2, x0, y0)):
            if ax == bx:
                continue
            if min(ax, bx) <= xx <= max(ax, bx):
                t = (xx - ax) / (bx - ax)
                ys.append(ay + t * (by - ay))
        if len(ys) >= 2:
            fill_rect(px, xx, int(min(ys)), 1, int(max(ys)) - int(min(ys)) + 1,
                      color)


def hrule(px, y, color=INK, thick=2, x0=28, x1=996):
    fill_rect(px, x0, y, x1 - x0, thick, color)


# ------------------------------------------------------------- the picture
LEAD_HEADLINE = ["DRONE STRIKE IN", "KUWAIT KILLS TWO", "ITALIAN WORKERS"]
LEAD_SUB = ("IRAN DENIES ROLE AS KUWAIT CONDEMNS THE STRIKE AND ROME "
            "DEMANDS ANSWERS")
LEAD_DECK = [
    "KUWAITI OFFICIALS SAY TWO ITALIAN WORKERS WERE",
    "KILLED IN THE STRIKE. TEHRAN DENIES ANY ROLE,",
    "AND ITALY SAYS IT WANTS THE FULL TRUTH.",
]
IN_BRIEF = [
    "UK NET MIGRATION LOWEST SINCE 1997",
    "SPACEX CLEARED FOR 1M SATELLITES",
    "EBOLA CASES IN CONGO PASS 12,000",
]

PANELS = [
    {
        "kicker": "UNITED STATES",
        "headline": "THANKSGIVING STORM HALTS MACY'S PARADE",
        "body": ("NEW YORK POSTPONES THE 100TH PARADE FOR THE FIRST TIME "
                 "AS A HUGE STORM KNOCKS OUT POWER TO MORE THAN HALF A "
                 "MILLION HOMES AND GROUNDS HUNDREDS OF FLIGHTS."),
        "icon": "storm",
    },
    {
        "kicker": "CHESS",
        "headline": "GUKESH, SINDAROV DRAW GAME 3",
        "body": ("THE WORLD CHESS TITLE STAYS LEVEL AFTER THREE GAMES AS "
                 "THE LONGEST GAME OF THE SERIES SO FAR ENDS IN A "
                 "MARATHON DRAW."),
        "icon": "chess",
    },
    {
        "kicker": "NORTH KOREA",
        "headline": "KIM VOWS MORE NUCLEAR WEAPONS",
        "body": ("KIM JONG UN INSPECTS NUCLEAR SITES AND CALLS FOR MORE "
                 "WARHEADS AFTER IGNORING AN OVERTURE FROM TRUMP."),
        "icon": "rocket",
    },
    {
        "kicker": "FRANCE",
        "headline": "DEPARDIEU ORDERED TO STAND TRIAL",
        "body": ("A FRENCH COURT ORDERS ACTOR GERARD DEPARDIEU TO STAND "
                 "TRIAL OVER AN ALLEGED RAPE IN 2018."),
        "icon": "court",
    },
]

GAZA_HEADLINE = "HAMAS WEIGHS REPLY AS ISRAEL KILLS 10 IN GAZA"
GAZA_BODY = ("HAMAS CONSIDERS ITS RESPONSE AFTER ISRAELI STRIKES KILL 10 "
             "PEOPLE, RAISING FEARS FOR THE FRAGILE CEASEFIRE.")

TICKER = ("BLACK FRIDAY • UK NET MIGRATION LOWEST SINCE 1997 • SPACEX "
          "CLEARED FOR 1M SATELLITES • EBOLA IN CONGO PASSES 12,000 • "
          "NEPAL DECLARES 4,000 LANDSLIDE MISSING DEAD • TRUMP URGES "
          "PUTIN TO PULL BACK •")


def draw_masthead(px):
    draw_text_centred(px, WIDTH // 2, 22, "THE WORLD TODAY", 6, INK)
    hrule(px, 78, INK, 3)
    draw_text_centred(px, WIDTH // 2, 90, "FRIDAY, 27 NOVEMBER 2026", 2, INK)
    fill_rect(px, 28, 118, 968, 30, DARK)
    draw_text_centred(px, WIDTH // 2, 125, "THE DAY IN ONE PICTURE", 2, PAPER)


def draw_lead_art(px, x, y, w, h):
    """Kuwait skyline under a drone strike: sky, towers, drone, burst."""
    fill_rect(px, x, y, w, h, SKY)
    # sun
    fill_circle(px, x + w - 52, y + 44, 26, GOLD)
    # skyline towers, left to right
    towers = [(0, 150, 46, 130), (52, 110, 40, 170), (98, 170, 54, 110),
              (158, 90, 38, 190), (202, 140, 48, 140), (256, 100, 42, 180),
              (304, 160, 44, 120), (354, 120, 40, 160)]
    for tx, ty, tw, th in towers:
        fill_rect(px, x + tx, y + ty, tw, th, INK)
        # lit windows
        for wy in range(y + ty + 12, y + ty + th - 8, 18):
            for wx in range(x + tx + 8, x + tx + tw - 8, 14):
                if (wx + wy) % 3 == 0:
                    fill_rect(px, wx, wy, 5, 6, GOLD)
    # ground
    fill_rect(px, x, y + h - 26, w, 26, DARK)
    # explosion burst above the middle tower
    bx, by = x + 190, y + 62
    for ang in range(0, 360, 18):
        import math
        a = math.radians(ang)
        x1 = bx + int(46 * math.cos(a))
        y1 = by + int(46 * math.sin(a))
        draw_line(px, bx, by, x1, y1, ORANGE, 3)
    fill_circle(px, bx, by, 26, ORANGE)
    fill_circle(px, bx, by, 15, RED)
    fill_circle(px, bx, by, 7, GOLD)
    # smoke puffs
    fill_circle(px, bx - 52, by + 8, 12, GREY)
    fill_circle(px, bx + 56, by + 14, 10, GREY)
    # drone, top right
    dx, dy = x + w - 120, y + 118
    fill_rect(px, dx - 22, dy - 6, 44, 12, INK)
    fill_rect(px, dx - 8, dy + 6, 16, 8, INK)
    draw_line(px, dx - 30, dy - 12, dx - 14, dy - 6, INK, 2)
    draw_line(px, dx + 14, dy - 6, dx + 30, dy - 12, INK, 2)
    draw_line(px, dx - 30, dy - 14, dx - 6, dy - 14, INK, 3)
    draw_line(px, dx + 6, dy - 14, dx + 30, dy - 14, INK, 3)
    fill_circle(px, dx, dy, 4, RED)


def draw_lead(px):
    y = 164
    draw_text(px, 28, y, "TOP STORY: MIDDLE EAST", 2, RED)
    hy = y + 30
    for i, line in enumerate(LEAD_HEADLINE):
        draw_text(px, 28, hy + i * 34, line, 4, INK)
    hrule(px, hy + 3 * 34 + 6, INK, 2, 28, 540)
    sub = wrap_text(LEAD_SUB, 2, 512)
    sy = hy + 3 * 34 + 18
    for i, line in enumerate(sub):
        draw_text(px, 28, sy + i * 16, line, 2, INK)
    dy = sy + len(sub) * 16 + 14
    for i, line in enumerate(LEAD_DECK):
        draw_text(px, 28, dy + i * 11, line, 1, INK)
    by = dy + len(LEAD_DECK) * 11 + 16
    draw_text(px, 28, by, "IN BRIEF:", 1, RED)
    for i, item in enumerate(IN_BRIEF):
        draw_text(px, 28, by + 14 + i * 11, "• " + item, 1, INK)
    # illustration, right column
    ix, iy, iw, ih = 580, 164, 416, 268
    draw_rect(px, ix, iy, iw, ih, INK, 2)
    draw_lead_art(px, ix + 2, iy + 2, iw - 4, ih - 4)
    cap = wrap_text("A DRONE OVER KUWAIT: THE STRIKE THAT KILLED TWO "
                    "ITALIAN WORKERS.", 1, iw)
    cy = iy + ih + 10
    for i, line in enumerate(cap):
        draw_text(px, ix, cy + i * 11, line, 1, GREY)
    hrule(px, 508, INK, 3)
    hrule(px, 514, INK, 1)


def draw_icon(px, kind, x, y, w, h):
    cx = x + w // 2
    if kind == "storm":
        fill_circle(px, cx - 28, y + 34, 22, DARK)
        fill_circle(px, cx + 4, y + 26, 26, DARK)
        fill_circle(px, cx + 30, y + 36, 18, DARK)
        fill_rect(px, cx - 50, y + 34, 100, 22, DARK)
        fill_circle(px, cx - 58, y + 16, 16, RED)
        fill_rect(px, cx - 58, y + 16, 32, 22, RED)
        draw_line(px, cx - 42, y + 40, cx - 42, y + 62, INK, 2)
        draw_line(px, cx - 12, y + 62, cx - 22, y + 78, GOLD, 4)
        draw_line(px, cx - 22, y + 78, cx - 10, y + 78, GOLD, 4)
        draw_line(px, cx - 10, y + 78, cx - 20, y + 92, GOLD, 4)
        for rx in (-44, -24, -4, 16, 36):
            draw_line(px, cx + rx, y + 60, cx + rx - 6, y + 76, BLUE, 2)
    elif kind == "chess":
        cell = 11
        bx, by = cx - 44, y + 4
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    fill_rect(px, bx + c * cell, by + r * cell,
                              cell, cell, INK)
        draw_rect(px, bx, by, 88, 88, INK, 2)
        fill_circle(px, bx + 16, by + 16, 7, PAPER)
        fill_circle(px, bx + 71, by + 71, 7, RED)
        draw_text(px, bx + 11, by + 9, "K", 1, INK)
        draw_text(px, bx + 66, by + 64, "K", 1, PAPER)
    elif kind == "rocket":
        fill_rect(px, cx - 10, y + 8, 20, 52, RED)
        fill_triangle(px, cx - 10, y + 8, cx + 10, y + 8, cx, y - 8, RED)
        fill_triangle(px, cx - 10, y + 48, cx - 24, y + 66, cx - 10, y + 60,
                      INK)
        fill_triangle(px, cx + 10, y + 48, cx + 24, y + 66, cx + 10, y + 60,
                      INK)
        fill_triangle(px, cx - 7, y + 60, cx + 7, y + 60, cx, y + 88, GOLD)
        fill_circle(px, cx - 34, y + 18, 5, GOLD)
        fill_circle(px, cx + 36, y + 40, 4, GOLD)
        fill_circle(px, cx - 40, y + 58, 3, BLUE)
    elif kind == "court":
        fill_triangle(px, cx - 56, y + 22, cx + 56, y + 22, cx, y - 2, INK)
        fill_rect(px, cx - 56, y + 22, 112, 6, INK)
        for col in (-44, -14, 16, 46):
            fill_rect(px, cx + col - 5, y + 28, 10, 52, INK)
        fill_rect(px, cx - 56, y + 80, 112, 8, INK)
        fill_circle(px, cx, y + 12, 4, PAPER)


def draw_panels(px):
    y = 534
    draw_text(px, 28, y, "AROUND THE WORLD", 2, RED)
    py = y + 28
    pw, gap = 228, 16
    for i, panel in enumerate(PANELS):
        x = 28 + i * (pw + gap)
        if i:
            fill_rect(px, x - gap // 2, py, 1, 268, GREY)
        draw_icon(px, panel["icon"], x, py, pw, 96)
        ky = py + 104
        draw_text(px, x, ky, panel["kicker"], 1, RED)
        head = wrap_text(panel["headline"], 2, pw)
        hy = ky + 14
        for j, line in enumerate(head):
            draw_text(px, x, hy + j * 16, line, 2, INK)
        body = wrap_text(panel["body"], 1, pw)
        by = hy + len(head) * 16 + 8
        for j, line in enumerate(body):
            draw_text(px, x, by + j * 11, line, 1, INK)


def draw_gaza(px):
    y = 836
    hrule(px, y, INK, 2)
    draw_text(px, 28, y + 12, "MIDDLE EAST", 1, RED)
    draw_text(px, 28, y + 28, GAZA_HEADLINE, 3, INK)
    body = wrap_text(GAZA_BODY, 2, 968)
    by = y + 28 + 22 + 8
    for i, line in enumerate(body):
        draw_text(px, 28, by + i * 16, line, 2, INK)


def draw_ticker(px):
    y = 958
    fill_rect(px, 0, y, WIDTH, HEIGHT - y, DARK)
    lines = wrap_text(TICKER, 1, 968)
    ty = y + 8
    for i, line in enumerate(lines):
        draw_text_centred(px, WIDTH // 2, ty + i * 12, line, 1, PAPER)


def build_pixels():
    px = bytearray([PAPER[0], PAPER[1], PAPER[2]] * (WIDTH * HEIGHT))
    draw_masthead(px)
    draw_lead(px)
    draw_panels(px)
    draw_gaza(px)
    draw_ticker(px)
    return px


# ------------------------------------------------------------ PNG encoder
def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(px, w, h):
    raw = bytearray()
    stride = w * 3
    for row in range(h):
        raw.append(0)  # filter: none
        raw += px[row * stride:(row + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + png_chunk(b"IEND", b""))


def validate_png(data):
    """Raise unless data is a whole 1024x1024 PNG within the size cap."""
    if len(data) > MAX_BYTES:
        raise ValueError("PNG over 1 MiB: %d bytes" % len(data))
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("bad PNG magic")
    if len(data) < 33:
        raise ValueError("PNG too short")
    w, h = struct.unpack(">II", data[16:24])
    if (w, h) != (WIDTH, HEIGHT):
        raise ValueError("bad dimensions %dx%d" % (w, h))
    # Walk every chunk and check its CRC, ending exactly at IEND.
    pos = 8
    seen_iend = False
    while pos < len(data):
        if pos + 8 > len(data):
            raise ValueError("truncated chunk header")
        size, kind = struct.unpack(">I4s", data[pos:pos + 8])
        end = pos + 12 + size
        if end > len(data):
            raise ValueError("truncated chunk %r" % kind)
        crc = struct.unpack(">I", data[end - 4:end])[0]
        if zlib.crc32(data[pos + 4:end - 4]) & 0xFFFFFFFF != crc:
            raise ValueError("bad CRC in chunk %r" % kind)
        if kind == b"IEND":
            seen_iend = True
            if end != len(data):
                raise ValueError("trailing bytes after IEND")
            break
        pos = end
    if not seen_iend:
        raise ValueError("missing IEND")


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(build_pixels(), WIDTH, HEIGHT)
    validate_png(png)
    final = os.path.join(out_dir, "entry.png")
    tmp = final + ".tmp"  # deterministic temporary name, never random
    with open(tmp, "wb") as f:
        f.write(png)
    os.replace(tmp, final)
    with open(final, "rb") as f:
        written = f.read()
    if written != png:
        raise ValueError("written file differs from encoded bytes")
    digest = hashlib.sha256(written).hexdigest()
    print("entry.png sha256=%s size=%d" % (digest, len(written)))


if __name__ == "__main__":
    main()
