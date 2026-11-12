# -*- coding: utf-8 -*-
"""تولید تصویر پس‌زمینه SVG برای هر شهر.

برای استفاده از عکس واقعی، فایل jpg/webp/png را با نام slug شهر در
static/img/cities/ بگذارید (مثلاً esfahan.jpg)؛ برنامه خودکار آن را به SVG ترجیح می‌دهد.
"""
import os

W, H = 1600, 900
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "img", "cities")


def svg(defs, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
            f'preserveAspectRatio="xMidYMid slice"><defs>{defs}</defs>{body}</svg>')


def sky(c1, c2, c3=None):
    stops = f'<stop offset="0" stop-color="{c1}"/>'
    if c3:
        stops += f'<stop offset=".55" stop-color="{c2}"/><stop offset="1" stop-color="{c3}"/>'
    else:
        stops += f'<stop offset="1" stop-color="{c2}"/>'
    return f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">{stops}</linearGradient>'


def dome(cx, base, r, fill, drum=None, finial="#d9b44a"):
    h = r * 1.35
    s = f'<path d="M{cx-r},{base} C{cx-r*1.05},{base-h*.9} {cx-r*.2},{base-h*1.05} {cx},{base-h*1.25} ' \
        f'C{cx+r*.2},{base-h*1.05} {cx+r*1.05},{base-h*.9} {cx+r},{base} Z" fill="{fill}"/>'
    s += f'<rect x="{cx-r*.9}" y="{base}" width="{r*1.8}" height="{r*.55}" fill="{drum or fill}"/>'
    s += f'<rect x="{cx-2}" y="{base-h*1.25-34}" width="4" height="34" fill="{finial}"/>'
    s += f'<circle cx="{cx}" cy="{base-h*1.25-38}" r="6" fill="{finial}"/>'
    return s


def minaret(x, base, w, h, fill, band="#d9b44a", cap=None):
    s = f'<path d="M{x-w},{base} L{x-w*.7},{base-h} L{x+w*.7},{base-h} L{x+w},{base} Z" fill="{fill}"/>'
    for k in (.25, .5, .75):
        s += f'<rect x="{x-w*.85}" y="{base-h*k}" width="{w*1.7}" height="5" fill="{band}"/>'
    s += f'<rect x="{x-w*1.1}" y="{base-h-12}" width="{w*2.2}" height="14" fill="{band}"/>'
    s += f'<path d="M{x-w*.8},{base-h-12} Q{x},{base-h-w*3} {x+w*.8},{base-h-12} Z" fill="{cap or fill}"/>'
    return s


def arch(cx, base, w, h, fill):
    r = w / 2
    return f'<path d="M{cx-r},{base} V{base-h+r} A{r},{r} 0 0 1 {cx+r},{base-h+r} V{base} Z" fill="{fill}"/>'


def cypress(x, base, h, w, fill):
    return f'<path d="M{x},{base} Q{x-w},{base-h*.45} {x},{base-h} Q{x+w},{base-h*.45} {x},{base} Z" fill="{fill}"/>'


def badgir(x, base, w, h, fill, dark):
    s = f'<rect x="{x}" y="{base-h}" width="{w}" height="{h}" fill="{fill}"/>'
    s += f'<path d="M{x-6},{base-h} L{x+w/2},{base-h-w*.5} L{x+w+6},{base-h} Z" fill="{dark}"/>'
    for k in range(4):
        s += f'<rect x="{x+w*.2}" y="{base-h+14+k*h*.12}" width="{w*.6}" height="{h*.07}" fill="{dark}"/>'
    return s


def hills(color, base, amp, seed, step=160):
    pts = [f"M0,{H}", f"L0,{base}"]
    x, i = 0, seed
    while x <= W + step:
        i = (i * 7 + 3) % 11
        pts.append(f"L{x},{base - (i / 10) * amp}")
        x += step
    pts += [f"L{W+step},{H}", "Z"]
    return f'<path d="{" ".join(pts)}" fill="{color}"/>'


def mountain(cx, base, w, h, fill, snow=None):
    s = f'<path d="M{cx-w},{base} L{cx},{base-h} L{cx+w},{base} Z" fill="{fill}"/>'
    if snow:
        s += f'<path d="M{cx-w*.22},{base-h*.78} L{cx},{base-h} L{cx+w*.22},{base-h*.78} L{cx+w*.08},{base-h*.84} L{cx},{base-h*.76} L{cx-w*.1},{base-h*.84} Z" fill="{snow}"/>'
    return s


def stars(n=60):
    s, a = "", 7
    for _ in range(n):
        a = (a * 31 + 17) % 997
        x = (a * 13) % W
        y = (a * 7) % 420
        s += f'<circle cx="{x}" cy="{y}" r="{1 + a % 2}" fill="#fff" opacity=".{6 + a % 4}"/>'
    return s


def esfahan():
    d = sky("#f6c58b", "#f3e3c3", "#cfe9e6")
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    b += '<circle cx="1250" cy="260" r="90" fill="#fff3d1" opacity=".9"/>'
    b += hills("#e2c9a0", 600, 70, 3)
    b += minaret(520, 650, 22, 300, "#c9a56b", "#1c9aa6", "#1c9aa6")
    b += minaret(1080, 650, 22, 300, "#c9a56b", "#1c9aa6", "#1c9aa6")
    b += dome(800, 600, 190, "#1c9aa6", "#d8c08c")
    b += f'<rect x="560" y="600" width="480" height="70" fill="#d8c08c"/>'
    for cx in range(620, 1000, 80):
        b += arch(cx + 40, 670, 50, 55, "#9c7f4a")
    b += f'<rect y="670" width="{W}" height="230" fill="#2a8f9a"/>'
    b += f'<rect y="670" width="{W}" height="12" fill="#9c7f4a"/>'
    for i in range(14):
        b += arch(60 + i * 118, 760, 80, 70, "#7a6338")
    b += f'<rect y="680" width="{W}" height="14" fill="#8a7040"/>'
    b += f'<rect y="760" width="{W}" height="140" fill="#1d7882" opacity=".85"/>'
    return svg(d, b)


def shiraz():
    d = sky("#2b1b4a", "#8a3d73", "#f2a477")
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(50)
    b += '<circle cx="300" cy="230" r="55" fill="#fde7c8" opacity=".95"/>'
    b += hills("#4a2a5a", 640, 120, 5)
    b += hills("#2f1b3d", 720, 70, 9, 220)
    # دروازه قرآن
    b += '<rect x="620" y="470" width="360" height="260" fill="#6b4b3a"/>'
    b += arch(800, 730, 190, 230, "#2f1b3d")
    b += '<rect x="610" y="455" width="380" height="24" fill="#8a6850"/>'
    b += dome(1180, 660, 100, "#2aa6a0", "#d8c08c")
    for x, h in [(180, 330), (260, 400), (360, 300), (1340, 380), (1430, 320), (1520, 420)]:
        b += cypress(x, 760, h, 36, "#10281f")
    b += f'<rect y="740" width="{W}" height="160" fill="#1d1129"/>'
    for i in range(30):
        b += f'<circle cx="{40 + i * 53}" cy="{780 + (i * 17) % 90}" r="{6 + i % 3}" fill="#e0457b" opacity=".85"/>'
    return svg(d, b)


def yazd():
    d = sky("#e0a458", "#f2cf94", "#f8e6c4")
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    b += '<circle cx="1300" cy="230" r="110" fill="#fff1c2" opacity=".95"/>'
    b += hills("#d9a86b", 640, 90, 4)
    mud, dark = "#c98a52", "#8a5630"
    b += f'<rect y="640" width="{W}" height="260" fill="#b97a45"/>'
    for x, h in [(140, 300), (420, 380), (700, 260), (980, 360), (1250, 300), (1480, 240)]:
        b += badgir(x, 700, 90, h, mud, dark)
    b += f'<rect x="0" y="690" width="{W}" height="30" fill="#a8693a"/>'
    for i in range(12):
        b += f'<path d="M{i*140},760 a50,50 0 0 1 100,0 Z" fill="#9a5c30"/>'
    return svg(d, b)


def tabriz():
    d = sky("#1b3a6b", "#4f86c6", "#d8e6f5")
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    b += mountain(1050, 640, 700, 420, "#5b7191", "#ffffff")
    b += mountain(450, 640, 520, 300, "#6b809e", "#f2f6fb")
    b += hills("#3f5473", 700, 60, 2)
    # ارگ
    b += '<rect x="560" y="360" width="440" height="360" fill="#8f4b32"/>'
    for i in range(7):
        b += f'<rect x="{560 + i*66}" y="338" width="40" height="30" fill="#8f4b32"/>'
    b += arch(780, 720, 120, 190, "#3d2118")
    b += '<rect x="560" y="520" width="440" height="10" fill="#6e3624"/>'
    b += f'<rect y="720" width="{W}" height="180" fill="#2b3d57"/>'
    b += dome(1300, 720, 90, "#1c6bbf", "#bcd3ee")
    return svg(d, b)


def mashhad():
    d = sky("#0b2b2a", "#14594f", "#e8c46a")
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>' + stars(40)
    b += hills("#103c36", 690, 70, 6)
    b += f'<rect x="420" y="620" width="760" height="120" fill="#e6c76a"/>'
    b += minaret(470, 640, 20, 340, "#f0d98c", "#c9a227", "#e0b83a")
    b += minaret(1130, 640, 20, 340, "#f0d98c", "#c9a227", "#e0b83a")
    b += minaret(640, 640, 16, 260, "#f0d98c", "#c9a227", "#e0b83a")
    b += minaret(960, 640, 16, 260, "#f0d98c", "#c9a227", "#e0b83a")
    b += dome(800, 620, 150, "#f0c24a", "#e6c76a", "#fff3b0")
    b += arch(800, 740, 130, 120, "#1a6f66")
    b += f'<rect y="740" width="{W}" height="160" fill="#0d3a34"/>'
    b += f'<rect y="740" width="{W}" height="8" fill="#e6c76a" opacity=".7"/>'
    return svg(d, b)


def rasht():
    d = sky("#5f7f86", "#9bb8a8", "#d3e3d2")
    b = f'<rect width="{W}" height="{H}" fill="url(#sky)"/>'
    b += hills("#7fa384", 520, 120, 7, 200)
    b += hills("#4f7c5a", 620, 100, 1, 180)
    b += hills("#2f5a3d", 720, 80, 8, 150)
    for x, w, h in [(240, 280, 150), (640, 320, 170), (1080, 300, 150), (1420, 260, 140)]:
        b += f'<rect x="{x}" y="{700-h*.5}" width="{w}" height="{h*.6}" fill="#e9e0cc"/>'
        b += f'<path d="M{x-30},{700-h*.5} L{x+w/2},{700-h*1.25} L{x+w+30},{700-h*.5} Z" fill="#b5563a"/>'
    b += f'<rect y="720" width="{W}" height="180" fill="#244a30"/>'
    for i in range(70):
        x = (i * 83) % W
        y = (i * 47) % 900
        b += f'<line x1="{x}" y1="{y}" x2="{x-18}" y2="{y+55}" stroke="#ffffff" stroke-width="2" opacity=".28"/>'
    for x in (90, 380, 900, 1260, 1520):
        b += f'<rect x="{x}" y="620" width="12" height="130" fill="#3b2a1d"/>'
        b += f'<circle cx="{x+6}" cy="600" r="62" fill="#1f5a34"/>'
    return svg(d, b)


SCENES = {"esfahan": esfahan, "shiraz": shiraz, "yazd": yazd, "tabriz": tabriz,
          "mashhad": mashhad, "rasht": rasht}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for slug, fn in SCENES.items():
        path = os.path.join(OUT, f"{slug}.svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn())
        print("wrote", os.path.normpath(path))
