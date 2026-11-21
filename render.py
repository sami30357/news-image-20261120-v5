#!/usr/bin/env python3
"""The Friday Edition - V5. Fresh PIL renderer, written in-session 2026-11-21.
Parchment broadsheet with a deep-green masthead band: a third voice, neither the
leaders' black-on-cream nor V3's white-on-navy. 34 verified stories, 7 regions.
Usage: python3 render.py  -> writes entry.png (1024x1024) in this directory.
"""
import hashlib
from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
PAPER = (248, 243, 232)
PAPER2 = (244, 238, 224)
INK = (22, 22, 22)
GREEN = (28, 74, 51)
GREEN_DK = (18, 52, 36)
GREEN_LT = (214, 228, 218)
CREAM = (250, 246, 236)
RED = (178, 34, 34)
RED_DK = (138, 24, 24)
GOLD = (176, 141, 60)
TAN = (216, 196, 150)
TAN_DK = (190, 168, 118)
GREY = (112, 110, 102)
NAVY = (26, 46, 78)
TEAL = (42, 110, 110)
PURPLE = (96, 66, 130)
OLIVE = (110, 120, 60)
SKY = (142, 178, 205)
SEA = (72, 122, 158)

FD = "/usr/share/fonts/truetype/dejavu/"
FN = "/usr/share/fonts/truetype/noto/"


def F(name, size):
    return ImageFont.truetype(FD + name, size)


def FN_F(name, size):
    return ImageFont.truetype(FN + name, size)


SERIF_B = lambda s: F("DejaVuSerif-Bold.ttf", s)
SERIF = lambda s: F("DejaVuSerif.ttf", s)
SERIF_I = lambda s: FN_F("NotoSerif-Italic.ttf", s)
SANS = lambda s: F("DejaVuSans.ttf", s)
SANS_B = lambda s: F("DejaVuSans-Bold.ttf", s)

MX = 28  # side margin


def text_w(d, s, font):
    return d.textlength(s, font=font)


def wrap(d, s, font, width):
    """Word-wrap s to lines fitting width px. Returns list of lines."""
    words = s.split()
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= width:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_lines(d, lines, x, y, font, fill, leading=None):
    if leading is None:
        leading = font.size + 3
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += leading
    return y


def trunc(d, s, font, width):
    if d.textlength(s, font=font) <= width:
        return s
    while s and d.textlength(s + "…", font=font) > width:
        s = s[:-1]
    return s + "…"


def chip(d, x, y, label, font, bg, fg=CREAM, pad=5, h=None):
    """Small rounded label chip; returns right edge x."""
    w = int(d.textlength(label, font=font)) + pad * 2
    hh = h or (font.size + 6)
    d.rounded_rectangle([x, y, x + w, y + hh], radius=3, fill=bg)
    d.text((x + pad, y + (hh - font.size) // 2 - 1), label, font=font, fill=fg)
    return x + w


def vchip(d, x, y, kind):
    """Verification chip: CONFIRMED / OFFICIAL / REPORTED / CLAIM / FORECAST."""
    bg = {"CONFIRMED": GREEN, "OFFICIAL": NAVY, "REPORTED": GREY,
          "CLAIM": (150, 90, 20), "FORECAST": (120, 90, 130)}.get(kind, GREY)
    f = SANS_B(8)
    return chip(d, x, y, kind, f, bg, pad=4, h=13)


# ---------------------------------------------------------------- data
MOMENTS = [
    ("01:20", "KYIV", "Missiles hit 3 bridges"),
    ("07:30", "GOPALPUR", "Landfall begins"),
    ("08:30", "TOKYO", "CPI 2.3% released"),
    ("11:20", "ODISHA", "Landfall done"),
    ("AFTERNOON", "ANTALYA", "COP31 past close"),
    ("EVENING", "BRUSSELS", "UK-EU deal sealed"),
    ("NIGHT", "NEW YORK", "Nvidia probe out"),
]

STATS = [
    ("3", "bridges hit\nin Kyiv"),
    ("300,000+", "evacuated\nbefore Akvan"),
    ("−6.2%", "Taiex, Friday's\nclose"),
    ("100,000", "youth visas a year\nin the UK–EU deal"),
    ("2.3%", "Japan consumer\ninflation, Oct"),
    ("118", "runs by Glenn Phillips\nagainst India"),
]

REGIONS = [
    ("EUROPE", 6, GREEN_DK), ("ASIA", 9, RED), ("MIDDLE EAST", 3, TEAL),
    ("AFRICA", 3, OLIVE), ("AMERICAS", 5, PURPLE), ("OCEANIA", 1, GOLD),
    ("GLOBAL", 7, GREY),
]

HEROES = [
    dict(n=1, chip="KYIV", sub="3 bridges hit", place="KYIV, UKRAINE · WAR",
         head="Russian missiles hit three Kyiv bridges",
         deck="An overnight barrage of 80+ missiles and 400 drones killed 8 and cut power and water in the capital.",
         why="Power and water cut across the capital; two more people were killed in Lviv.",
         src="Reuters · Kyiv Post", ver="OFFICIAL", scene="kyiv"),
    dict(n=2, chip="CYCLONE AKVAN", sub="Landfall · 7:30 am", place="ODISHA, INDIA · CYCLONE",
         head="Cyclone Akvan comes ashore in eastern India",
         deck="The storm crossed the coast near Gopalpur; 300,000+ moved to shelters. No deaths reported.",
         why="423 rescue teams and 9,341 shelters stood ready — the evacuation is why no one died.",
         src="IMD · NDTV", ver="OFFICIAL", scene="akvan"),
    dict(n=3, chip="AI SELL-OFF", sub="Asia, Friday's close", place="TAIPEI · SEOUL · TOKYO · MARKETS",
         head="AI sell-off sinks Asia's stock markets",
         deck="Taiex fell 6.2% in its worst week since 1991 as chipmakers led the slide.",
         why="The rout spread worldwide — SoftBank fell 14.6% in a single day.",
         src="Al Jazeera · Reuters", ver="CONFIRMED", scene="ai"),
]

MIDS = [
    dict(n=4, label="UK–EU DEAL", place="BRUSSELS · DIPLOMACY",
         head="UK and EU seal a “reset” deal",
         deck="Food trade, youth visas, carbon link.",
         src="Reuters", ver="CONFIRMED", scene="flags"),
    dict(n=5, label="KH-101 IN POLAND", place="EASTERN POLAND · WAR",
         head="Russian missile lands in Poland",
         deck="Kh-101 down; NATO jets scrambled.",
         src="Ukrainska Pravda", ver="OFFICIAL", scene="missile"),
    dict(n=6, label="COP31: NO DEAL", place="ANTALYA · CLIMATE",
         head="COP31 reaches its last day with no deal",
         deck="Draft leaves out fossil fuels.",
         src="AFP", ver="CONFIRMED", scene="globe"),
    dict(n=7, label="IRAQ: ARMY IN", place="CENTRAL IRAQ · SECURITY",
         head="Iraqi army enters a militia stronghold",
         deck="Troops deploy to Jurf al-Sakhar.",
         src="AFP", ver="CONFIRMED", scene="tanks"),
    dict(n=8, label="BUKELE: 3RD TERM", place="SAN SALVADOR · POLITICS",
         head="Bukele files to run for a third term",
         deck="The vote is on 28 February 2027.",
         src="Reuters", ver="REPORTED", scene="ballot"),
    dict(n=9, label="SCIOPERO", place="ROME · LABOUR",
         head="General strike over Italy's budget",
         deck="Workers and students march.",
         src="Reuters", ver="CONFIRMED", scene="crowd"),
    dict(n=10, label="JAPAN: +2.3%", place="TOKYO · ECONOMY",
         head="Japan's inflation picks up to 2.3%",
         deck="A December rate rise stays in view.",
         src="Japan Times", ver="OFFICIAL", scene="bars"),
    dict(n=11, label="PHILLIPS: 118", place="WELLINGTON · CRICKET",
         head="Phillips hits 118 against India",
         deck="Hundreds in all three formats.",
         src="Cricinfo", ver="CONFIRMED", scene="pitch"),
    dict(n=12, label="NVIDIA: SUBPOENA", place="CALIFORNIA · TECH",
         head="California subpoenas Nvidia",
         deck="China chips probe; investors misled.",
         src="Reuters", ver="REPORTED", scene="chip"),
    dict(n=13, label="SUNEUNG: 111 CAUGHT", place="SEOUL · EDUCATION",
         head="Suneung: 111 caught cheating",
         deck="Glasses, cameras; ban proposed.",
         src="Yonhap", ver="OFFICIAL", scene="glasses"),
]

BRIEFS = [
    (14, "Kenya", "Oil rig on — first crude due Dec 1", "Business Daily"),
    (15, "China", "Rates held for an 18th straight month", "Xinhua"),
    (16, "Senegal", "Boat capsizes; 4 dead, dozens missing", "Al Jazeera"),
    (17, "Las Vegas", "Russell fastest in wet FP2", "formula1.com"),
    (18, "Health", "Cancer pill: tumours shrink 60.7%", "Reuters"),
    (19, "Myanmar", "Rohingya call ICJ ruling “unfair”", "Reuters"),
    (20, "Games", "GTA VI: $2.36bn by launch day", "Reuters"),
    (21, "Seoul", "Ruling party moves to impeach top judge", "Yonhap"),
    (22, "Oil", "Brent $92.60 as Houthi missiles fly", "Reuters"),
    (23, "Riyadh", "Coalition says Houthi missiles intercepted", "Reuters"),
    (24, "Hormuz", "Iran claims two tankers hit mines", "CLAIM"),
    (25, "Health", "Erasca: 44% of patients respond", "Reuters"),
    (26, "Sport", "Antonelli: youngest F1 champion", "FIA"),
    (27, "Lviv", "Strike on a railway station kills two", "BBC"),
    (28, "World", "Youth protests spread to five countries", "Reuters"),
    (29, "Chips", "US approved 900,000 chips for China", "WSJ"),
    (30, "Odisha", "423 teams, 9,341 shelters ready", "NDTV"),
    (31, "Markets", "SoftBank falls 14.6% in a day", "Reuters"),
    (32, "Climate", "COP31 keeps “35 by 35” goal", "Carbon Brief"),
    (33, "Brussels", "EU calls COP31 draft “not acceptable”", "AFP"),
    (34, "Wellington", "Nicholls hits 175* as NZ post 368", "Cricinfo"),
]

RECORDS = [
    ("WORST WEEK SINCE 1991", "Taiex −17.5% on the week"),
    ("YOUNGEST CHAMPION", "Antonelli: F1's youngest champion"),
    ("ONLY THE 2ND EVER", "Phillips: 100s in all 3 formats vs India"),
    ("8 YEARS IN FLIGHT", "BepiColombo reaches Mercury Saturday"),
]

LEFT_OUT = ("LEFT OUT — first reported Thursday 19 November: Anthropic's $83 IPO pricing "
            "& Nasdaq debut · Wall Street −2%, Dow under 50,000 · the ICJ ruling itself "
            "(reactions are Friday's news) · the Riyadh tower attack · COP31's second draft.")
NOT_YET = ("NOT YET — BepiColombo's Mercury orbit capture (Saturday) · COP31's final text · "
           "the ATP Finals final (Sunday) · Estonia's border closure (1 December).")

# ---------------------------------------------------------------- scenes
def scene_kyiv(d, x, y, w, h):
    """Night skyline, three bridge arches, missile trails, fires."""
    d.rectangle([x, y, x + w, y + h], fill=(16, 28, 52))
    import random
    rnd = random.Random(11)
    for _ in range(34):
        sx, sy = x + rnd.randint(4, w - 4), y + rnd.randint(3, h // 2)
        d.ellipse([sx, sy, sx + 2, sy + 2], fill=(240, 230, 180))
    # skyline
    base = y + h - 26
    bx = x
    for bw, bh in [(46, 52), (34, 68), (52, 44), (30, 76), (44, 58), (38, 48)]:
        d.rectangle([bx, base - bh, bx + bw, base + 26], fill=(10, 18, 34))
        for wy in range(base - bh + 8, base + 18, 12):
            for wx in range(bx + 6, bx + bw - 6, 11):
                if rnd.random() < 0.6:
                    d.rectangle([wx, wy, wx + 4, wy + 5], fill=(255, 205, 90))
        bx += bw + 4
    # river + bridges
    d.rectangle([x, base + 26 - 8, x + w, y + h], fill=(24, 48, 78))
    for cx in (x + w * 0.22, x + w * 0.52, x + w * 0.82):
        d.arc([cx - 34, base - 6, cx + 34, base + 34], 180, 360, fill=(250, 246, 236), width=3)
        d.line([cx - 34, base + 14, cx + 34, base + 14], fill=(250, 246, 236), width=2)
    # missile trails (dotted arcs)
    for sx, ex, apex in [(x + 20, x + w * 0.4, y + 18), (x + w * 0.45, x + w * 0.75, y + 10),
                         (x + w * 0.7, x + w - 16, y + 26)]:
        for t in range(0, 21):
            tt = t / 20
            px = sx + (ex - sx) * tt
            py = (y + h - 40) * (1 - tt) + apex * tt - 34 * 4 * tt * (1 - tt) * 0.4
            d.ellipse([px, py, px + 3, py + 3], fill=(255, 220, 120))
    # fires
    for fx, fy, r in [(x + w * 0.22, base + 8, 9), (x + w * 0.52, base + 10, 7),
                      (x + w * 0.82, base + 6, 8)]:
        d.ellipse([fx - r, fy - r, fx + r, fy + r], fill=(255, 140, 40))
        d.ellipse([fx - r // 2, fy - r // 2, fx + r // 2, fy + r // 2], fill=(255, 210, 90))


def scene_akvan(d, x, y, w, h):
    """Bay of Bengal coast, cyclone spiral, rain bands, landfall dot."""
    d.rectangle([x, y, x + w, y + h], fill=SEA)
    # coast (tan land on the left)
    d.polygon([(x, y), (x + w * 0.34, y), (x + w * 0.30, y + h * 0.4),
               (x + w * 0.38, y + h * 0.7), (x + w * 0.30, y + h), (x, y + h)],
              fill=(226, 205, 160))
    d.line([(x + w * 0.34, y), (x + w * 0.30, y + h * 0.4), (x + w * 0.38, y + h * 0.7),
            (x + w * 0.30, y + h)], fill=TAN_DK, width=2)
    # rain bands
    for i in range(7):
        rx = x + w * (0.45 + i * 0.07)
        d.line([rx, y + 8, rx - 12, y + h - 8], fill=(200, 220, 235), width=2)
    # spiral
    cx, cy = x + w * 0.62, y + h * 0.52
    for r in range(12, 62, 9):
        d.arc([cx - r, cy - r, cx + r, cy + r], 20 + r, 300 + r, fill=(250, 246, 236), width=4)
    d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], fill=RED)
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], outline=(250, 246, 236), width=2)
    d.text((x + 8, y + h - 18), "GOPALPUR", font=SANS_B(10), fill=INK)


def scene_ai(d, x, y, w, h):
    """Dark market panel: falling chart + four index rows."""
    d.rectangle([x, y, x + w, y + h], fill=(14, 22, 38))
    for gy in range(y + 18, y + h - 34, 16):
        d.line([x + 8, gy, x + w - 8, gy], fill=(40, 56, 84), width=1)
    pts = [(x + 12 + i * (w - 24) // 8, y + 16 + int(v)) for i, v in
           enumerate([0, 6, 4, 14, 10, 22, 18, 30, 26])]
    d.line(pts, fill=(255, 90, 70), width=3)
    for px, py in pts:
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 120, 100))
    rows = [("TAIEX", "−6.2%"), ("NIKKEI", "−5.1%"), ("KOSPI", "−5.2%"), ("HANG SENG", "−1.9%")]
    ry = y + h - 42
    for name, val in rows:
        d.text((x + 10, ry), name, font=SANS_B(10), fill=(220, 225, 235))
        vw = d.textlength(val, font=SANS_B(10))
        d.text((x + w - 10 - vw, ry), val, font=SANS_B(10), fill=(255, 110, 90))
        ry += 10


def scene_flags(d, x, y, w, h):
    d.rectangle([x, y, x + w // 2, y + h], fill=(18, 52, 110))
    d.rectangle([x + w // 2, y, x + w, y + h], fill=(30, 70, 160))
    # union jack hint: white diagonals + red cross
    d.line([x, y, x + w // 2, y + h], fill=(250, 246, 236), width=4)
    d.line([x + w // 2, y, x, y + h], fill=(250, 246, 236), width=4)
    d.line([x + w // 4, y, x + w // 4, y + h], fill=(200, 40, 40), width=5)
    d.line([x, y + h // 2, x + w // 2, y + h // 2], fill=(200, 40, 40), width=5)
    # EU stars circle
    cx, cy = x + w * 0.75, y + h // 2
    import math
    for i in range(12):
        a = math.radians(i * 30 - 90)
        sx, sy = cx + 16 * math.cos(a), cy + 16 * math.sin(a)
        d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=(255, 215, 60))


def scene_missile(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(168, 188, 140))
    d.ellipse([x + w * 0.3, y + h * 0.55, x + w * 0.62, y + h * 0.85], fill=(90, 70, 50))
    d.ellipse([x + w * 0.36, y + h * 0.62, x + w * 0.56, y + h * 0.78], fill=(60, 48, 36))
    d.line([x + w * 0.62, y + h * 0.28, x + w * 0.8, y + h * 0.45], fill=(230, 230, 225), width=7)
    d.polygon([(x + w * 0.8, y + h * 0.45), (x + w * 0.68, y + h * 0.38),
               (x + w * 0.68, y + h * 0.52)], fill=(200, 40, 40))
    d.line([x + 6, y + h - 10, x + w - 6, y + h - 10], fill=(90, 110, 70), width=3)


def scene_globe(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(214, 228, 238))
    cx, cy, r = x + w * 0.36, y + h // 2, 30
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(52, 110, 160))
    d.ellipse([cx - r + 8, cy - r + 6, cx - 4, cy - 2], fill=(96, 170, 90))
    d.ellipse([cx + 2, cy + 4, cx + r - 6, cy + r - 8], fill=(96, 170, 90))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(30, 70, 110), width=2)
    # thermometer
    tx = x + w * 0.78
    d.rounded_rectangle([tx - 5, y + 10, tx + 5, y + h - 18], radius=5, fill=(250, 246, 236),
                        outline=RED, width=2)
    d.ellipse([tx - 9, y + h - 26, tx + 9, y + h - 8], fill=RED)
    d.rectangle([tx - 2, y + 16, tx + 2, y + h - 18], fill=RED)


def scene_tanks(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(222, 206, 160))
    d.rectangle([x, y + h * 0.62, x + w, y + h], fill=(176, 156, 110))
    for tx, ts in [(x + 12, 1.0), (x + w * 0.45, 0.85), (x + w * 0.72, 0.7)]:
        tw = int(52 * ts)
        d.rectangle([tx, y + h * 0.52, tx + tw, y + h * 0.68], fill=(74, 84, 60))
        d.rectangle([tx + tw * 0.2, y + h * 0.4, tx + tw * 0.6, y + h * 0.54], fill=(60, 68, 48))
        d.line([tx + tw * 0.6, y + h * 0.46, tx + tw + 10, y + h * 0.4], fill=(60, 68, 48), width=3)


def scene_ballot(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(52, 96, 168))
    bx, by, bw, bh = x + w * 0.3, y + h * 0.34, w * 0.4, h * 0.5
    d.rectangle([bx, by, bx + bw, by + bh], fill=(36, 70, 130))
    d.rectangle([bx - 6, by - 6, bx + bw + 6, by + 4], fill=(26, 52, 100))
    d.polygon([(bx + bw * 0.25, by - 26), (bx + bw * 0.75, by - 26),
               (bx + bw * 0.6, by - 6), (bx + bw * 0.4, by - 6)], fill=(250, 246, 236))
    d.line([bx + bw * 0.3, by + bh * 0.45, bx + bw * 0.48, by + bh * 0.65,
            bx + bw * 0.78, by + bh * 0.2], fill=(90, 200, 120), width=4)
    d.text((x + 8, y + h - 18), "VOTE · FEB 2027", font=SANS_B(9), fill=CREAM)


def scene_crowd(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(238, 228, 210))
    d.rectangle([x, y, x + w, y + 20], fill=RED)
    d.text((x + 8, y + 4), "SCIOPERO", font=SANS_B(11), fill=CREAM)
    for i in range(6):
        hx = x + 14 + i * (w - 28) // 5
        hy = y + h - 34
        d.ellipse([hx - 8, hy - 8, hx + 8, hy + 8], fill=(60, 50, 44))
        d.rectangle([hx - 10, hy + 8, hx + 10, y + h], fill=(90, 80, 70))
    d.rectangle([x + w * 0.6, y + 30, x + w * 0.92, y + 44], fill=(250, 246, 236),
                outline=INK, width=1)
    d.text((x + w * 0.62, y + 32), "NO 26 bn", font=SANS_B(9), fill=INK)


def scene_bars(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(250, 246, 236))
    vals = [0.42, 0.62, 0.85]
    for i, v in enumerate(vals):
        bx = x + 16 + i * 34
        bh = int((h - 26) * v)
        d.rectangle([bx, y + h - 12 - bh, bx + 22, y + h - 12], fill=(178, 34, 34))
    d.text((x + w - 52, y + 6), "+2.3%", font=SANS_B(13), fill=RED)
    d.line([x + 8, y + h - 12, x + w - 8, y + h - 12], fill=INK, width=2)


def scene_pitch(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(96, 160, 90))
    d.rectangle([x + w * 0.42, y, x + w * 0.58, y + h], fill=(214, 186, 140))
    d.line([x + w * 0.42, y, x + w * 0.42, y + h], fill=(250, 246, 236), width=2)
    d.line([x + w * 0.58, y, x + w * 0.58, y + h], fill=(250, 246, 236), width=2)
    d.ellipse([x + w * 0.46, y + h * 0.3, x + w * 0.54, y + h * 0.42], fill=(250, 246, 236),
              outline=RED, width=2)
    d.text((x + 8, y + h - 22), "118", font=SANS_B(20), fill=CREAM)


def scene_chip(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(30, 60, 44))
    cx, cy = x + w * 0.34, y + h // 2
    d.rectangle([cx - 20, cy - 20, cx + 20, cy + 20], fill=(52, 110, 80))
    d.rectangle([cx - 12, cy - 12, cx + 12, cy + 12], fill=(28, 74, 51))
    for px in (-20, 20):
        for py in (-12, 0, 12):
            d.line([cx + px, cy + py, cx + px + (8 if px < 0 else -8), cy + py],
                   fill=(180, 200, 190), width=2)
    mx, my = x + w * 0.74, y + h * 0.42
    d.ellipse([mx - 14, my - 14, mx + 14, my + 14], outline=(250, 246, 236), width=3)
    d.line([mx + 10, my + 10, mx + 22, my + 22], fill=(250, 246, 236), width=3)
    d.text((mx - 5, my - 8), "?", font=SANS_B(13), fill=CREAM)


def scene_glasses(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(250, 246, 236))
    for lx in (x + w * 0.3, x + w * 0.7):
        d.ellipse([lx - 20, y + h // 2 - 16, lx + 20, y + h // 2 + 16],
                  outline=INK, width=3)
        d.ellipse([lx - 20, y + h // 2 - 16, lx + 20, y + h // 2 + 16],
                  outline=(120, 160, 200), width=1)
    d.line([x + w * 0.3 + 20, y + h // 2, x + w * 0.7 - 20, y + h // 2], fill=INK, width=3)
    d.line([x + w * 0.86, y + h // 2 - 12, x + w * 0.86, y + h // 2 + 12], fill=RED, width=4)
    d.line([x + w * 0.80, y + h // 2 - 6, x + w * 0.92, y + h // 2 + 6], fill=RED, width=3)
    d.line([x + w * 0.80, y + h // 2 + 6, x + w * 0.92, y + h // 2 - 6], fill=RED, width=3)


MID_SCENES = {"flags": scene_flags, "missile": scene_missile, "globe": scene_globe,
              "tanks": scene_tanks, "ballot": scene_ballot, "crowd": scene_crowd,
              "bars": scene_bars, "pitch": scene_pitch, "chip": scene_chip,
              "glasses": scene_glasses}
HERO_SCENES = {"kyiv": scene_kyiv, "akvan": scene_akvan, "ai": scene_ai}


def paint_map(d, x, y, w, h, pins):
    """Simplified world map: tan continents on parchment, numbered red pins."""
    d.rectangle([x, y, x + w, y + h], fill=(232, 222, 198))
    # continents as rough polygons (fractions of the map rect)
    conts = [
        [(0.02, 0.12), (0.10, 0.06), (0.20, 0.08), (0.24, 0.16), (0.20, 0.30),
         (0.14, 0.42), (0.08, 0.38), (0.03, 0.26)],                       # N America
        [(0.16, 0.48), (0.24, 0.46), (0.28, 0.56), (0.24, 0.74), (0.19, 0.70),
         (0.15, 0.58)],                                                    # S America
        [(0.44, 0.10), (0.50, 0.06), (0.55, 0.10), (0.54, 0.18), (0.48, 0.22),
         (0.44, 0.16)],                                                    # Europe
        [(0.46, 0.26), (0.54, 0.24), (0.60, 0.32), (0.58, 0.52), (0.52, 0.62),
         (0.47, 0.52), (0.44, 0.38)],                                     # Africa
        [(0.56, 0.06), (0.72, 0.04), (0.90, 0.10), (0.94, 0.26), (0.86, 0.44),
         (0.74, 0.48), (0.66, 0.36), (0.60, 0.24), (0.56, 0.16)],         # Asia
        [(0.82, 0.72), (0.90, 0.70), (0.93, 0.78), (0.86, 0.84), (0.81, 0.78)],
    ]
    for poly in conts:
        pts = [(x + fx * w, y + fy * h) for fx, fy in poly]
        d.polygon(pts, fill=TAN, outline=TAN_DK)
    # pin positions (fraction of map rect) for story numbers 1..13
    pos = {1: (0.50, 0.14), 2: (0.76, 0.42), 3: (0.85, 0.34), 4: (0.46, 0.12),
           5: (0.52, 0.08), 6: (0.55, 0.26), 7: (0.59, 0.34), 8: (0.15, 0.52),
           9: (0.47, 0.20), 10: (0.90, 0.28), 11: (0.95, 0.82), 12: (0.08, 0.36),
           13: (0.87, 0.28)}
    f = SANS_B(9)
    for n in pins:
        fx, fy = pos[n]
        px, py = x + fx * w, y + fy * h
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED, outline=CREAM, width=1)
        tw = d.textlength(str(n), font=f)
        d.text((px - tw / 2, py - 5), str(n), font=f, fill=CREAM)

# ---------------------------------------------------------------- layout
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    y = 8

    # kicker
    d.text((MX, y), "THE WORLD IN ONE DAY", font=SANS_B(11), fill=RED)
    r = "34 STORIES · 7 REGIONS · EVERY ONE DATED FRIDAY 20 NOVEMBER 2026"
    d.text((W - MX - text_w(d, r, SANS_B(10)), y + 1), r, font=SANS_B(10), fill=INK)
    y += 22

    # masthead band: deep green, cream serif
    d.rectangle([0, y, W, y + 66], fill=GREEN)
    d.rectangle([0, y, W, y + 2], fill=GREEN_DK)
    d.rectangle([0, y + 64, W, y + 66], fill=GREEN_DK)
    title = "Friday 20 November 2026"
    tf = SERIF_B(52)
    d.text(((W - text_w(d, title, tf)) / 2, y + 6), title, font=tf, fill=CREAM)
    y += 70

    # sub-dek
    sub = ("Russian missiles hit Kyiv's bridges · Cyclone Akvan strikes India · "
           "An AI sell-off sinks Asia's markets · UK and EU seal a deal")
    sf = SERIF_I(13)
    d.text(((W - text_w(d, sub, sf)) / 2, y), sub, font=sf, fill=INK)
    y += 18
    d.line([MX, y, W - MX, y], fill=GREEN, width=2)
    y += 6

    # timeline band
    d.text((MX, y), "THE DAY IN SEVEN MOMENTS", font=SANS_B(10), fill=RED)
    y += 15
    colw = (W - 2 * MX) / 7.0
    for i, (tm, pl, lb) in enumerate(MOMENTS):
        cx = MX + i * colw
        d.text((cx, y), tm, font=SANS_B(11), fill=RED)
        d.text((cx, y + 14), pl, font=SANS_B(10), fill=INK)
        lines = wrap(d, lb, SANS(9), colw - 8)
        d.text((cx, y + 26), lines[0], font=SANS(9), fill=GREY)
        if len(lines) > 1:
            d.text((cx, y + 37), lines[1], font=SANS(9), fill=GREY)
        if i < 6:
            d.line([cx + colw - 6, y + 2, cx + colw - 6, y + 34], fill=(200, 192, 172), width=1)
    y += 38

    # stat strip
    d.line([MX, y, W - MX, y], fill=INK, width=1)
    y += 6
    scolw = (W - 2 * MX) / 6.0
    for i, (num, cap) in enumerate(STATS):
        cx = MX + i * scolw
        nf = SERIF_B(24)
        d.text((cx, y), num, font=nf, fill=RED_DK)
        for j, ln in enumerate(cap.split("\n")):
            d.text((cx, y + 28 + j * 12), ln, font=SANS(9), fill=INK)
        if i < 5:
            d.line([cx + scolw - 6, y + 2, cx + scolw - 6, y + 48], fill=(200, 192, 172), width=1)
    y += 52
    d.line([MX, y, W - MX, y], fill=INK, width=1)
    y += 8

    # region bar (proportional segments)
    total = sum(c for _, c, _ in REGIONS)
    widths = [c / total * (W - 2 * MX) for _, c, _ in REGIONS]
    # enforce a minimum width for the smallest segment, take it from the largest
    for i, wd in enumerate(widths):
        if wd < 56:
            deficit = 56 - wd
            widths[i] = 56
            j = widths.index(max(widths))
            widths[j] -= deficit
    rx = MX
    for (name, cnt, col), wd in zip(REGIONS, widths):
        d.rectangle([rx, y, rx + wd, y + 20], fill=col)
        lab = f"{name} {cnt}"
        lf = SANS_B(9)
        d.text((rx + (wd - text_w(d, lab, lf)) / 2, y + 5), lab, font=lf, fill=CREAM)
        rx += wd
    y += 24

    # heroes
    hcolw = int((W - 2 * MX - 24) / 3)
    hy = y
    for i, h in enumerate(HEROES):
        hx = MX + i * (hcolw + 12)
        HERO_SCENES[h["scene"]](d, hx, hy, hcolw, 118)
        chip(d, hx + 6, hy + 6, h["chip"], SANS_B(11), RED)
        if h["scene"] != "ai":
            subw = text_w(d, h["sub"], SANS_B(9))
            d.rectangle([hx + 6, hy + 118 - 24, hx + 6 + subw + 10, hy + 118 - 24 + 16],
                        fill=CREAM)
            d.text((hx + 11, hy + 118 - 22), h["sub"], font=SANS_B(9), fill=INK)
        ty = hy + 124
        d.text((hx, ty), f"{h['n']} · {h['place']}", font=SANS_B(10), fill=RED)
        ty += 14
        ty = draw_lines(d, wrap(d, h["head"], SERIF_B(18), hcolw), hx, ty,
                        SERIF_B(18), INK, leading=21)
        ty = draw_lines(d, wrap(d, h["deck"], SANS(11), hcolw), hx, ty + 2,
                        SANS(11), INK, leading=13)
        why = "Why it matters: " + h["why"]
        ty = draw_lines(d, wrap(d, why, SERIF_I(10), hcolw), hx, ty + 3,
                        SERIF_I(10), (60, 60, 60), leading=12)
        d.text((hx, ty + 3), h["src"], font=SANS(9), fill=GREY)
        vchip(d, hx + hcolw - 62, ty + 2, h["ver"])
    y = hy + 118 + 120

    # mids header
    d.rectangle([MX, y, W - MX, y + 18], fill=GREEN)
    d.text((MX + 6, y + 4), "THE DAY'S TEN", font=SANS_B(11), fill=CREAM)
    leg = "EVERY STORY DRAWN · VERIFIED: CONFIRMED / OFFICIAL / REPORTED"
    d.text((W - MX - text_w(d, leg, SANS_B(9)) - 6, y + 5), leg, font=SANS_B(9), fill=CREAM)
    y += 22

    # mids: 2 rows x 5 cols
    mcolw = int((W - 2 * MX - 4 * 10) / 5)
    for row in range(2):
        ry = y + row * 132
        for col in range(5):
            m = MIDS[row * 5 + col]
            mx = MX + col * (mcolw + 10)
            MID_SCENES[m["scene"]](d, mx, ry, mcolw, 62)
            chip(d, mx + 4, ry + 4, m["label"], SANS_B(9), RED, pad=4, h=15)
            ty = ry + 68
            d.text((mx, ty), f"{m['n']} · {m['place']}", font=SANS_B(8), fill=RED)
            ty += 11
            ty = draw_lines(d, wrap(d, m["head"], SANS_B(13), mcolw), mx, ty,
                            SANS_B(13), INK, leading=15)
            d.text((mx, ty + 1), trunc(d, m["deck"], SANS(10), mcolw), font=SANS(10), fill=INK)
            d.text((mx, ty + 14), m["src"], font=SANS(8), fill=GREY)
            vchip(d, mx + mcolw - 62, ty + 13, m["ver"])
    y += 2 * 132 + 6

    # records strip
    d.line([MX, y, W - MX, y], fill=GREEN, width=2)
    y += 4
    d.text((MX, y), "RECORDS OF THE DAY", font=SANS_B(10), fill=RED)
    rcolw = (W - 2 * MX - 150) / 4.0
    rx = MX + 150
    for title, val in RECORDS:
        d.text((rx, y), title, font=SANS_B(9), fill=INK)
        d.text((rx, y + 12), trunc(d, val, SANS(9), rcolw - 8), font=SANS(9), fill=GREY)
        rx += rcolw
    y += 24

    # map + briefs
    d.text((MX, y), "WHERE IT HAPPENED", font=SANS_B(10), fill=RED)
    d.text((MX + 312, y), "MORE OF THE DAY, IN BRIEF", font=SANS_B(10), fill=RED)
    y += 14
    map_h = 88
    paint_map(d, MX, y, 300, map_h, list(range(1, 14)))
    d.text((MX, y + map_h + 3), "Pins 1–13 mark the drawn stories.", font=SANS(8), fill=GREY)
    bx = MX + 312
    bcolw = (W - MX - bx - 6) / 2.0
    for i, (n, lead, rest, src) in enumerate(BRIEFS):
        col = 0 if i < 11 else 1
        row = i if i < 11 else i - 11
        x0 = bx + col * (bcolw + 6)
        yy = y + row * 9
        d.text((x0, yy), str(n), font=SANS_B(9), fill=RED)
        s = f"{lead}: {rest} ({src})"
        d.text((x0 + 20, yy), trunc(d, s, SANS(9), bcolw - 22), font=SANS(9), fill=INK)
    y += map_h + 14

    # date check box
    d.rectangle([MX, y, W - MX, y + 44], outline=RED, width=1)
    d.text((MX + 6, y + 4), "DATE CHECK", font=SANS_B(10), fill=RED)
    lo = wrap(d, LEFT_OUT, SANS(9), W - 2 * MX - 100)
    d.text((MX + 92, y + 4), lo[0], font=SANS(9), fill=INK)
    if len(lo) > 1:
        d.text((MX + 92, y + 16), lo[1], font=SANS(9), fill=INK)
    ny = wrap(d, NOT_YET, SANS(9), W - 2 * MX - 100)
    d.text((MX + 92, y + 28), ny[0], font=SANS(9), fill=INK)
    if len(ny) > 1:
        d.text((MX + 92, y + 39), ny[1], font=SANS(9), fill=INK)
    y += 46

    # footer
    d.text((MX, y), "Every story here happened, or was first reported, on Friday 20 November 2026. Claims are attributed, not stated as fact.",
           font=SANS(9), fill=GREY)
    leg2 = "CONFIRMED 2+ outlets · OFFICIAL on the record · REPORTED one outlet · CLAIM unverified"
    d.text((W - MX - text_w(d, leg2, SANS_B(8)), y), leg2, font=SANS_B(8), fill=GREEN_DK)
    y += 12
    d.text((MX, y), "Sources named beside each story · Original drawings",
           font=SANS(9), fill=GREY)
    y += 14

    print("final y:", y, "page:", H)
    img.save("entry.png")
    with open("entry.png", "rb") as f:
        print("sha256:", hashlib.sha256(f.read()).hexdigest())
    print("bytes:", len(open("entry.png", "rb").read()))


if __name__ == "__main__":
    build()
