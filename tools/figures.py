#!/usr/bin/env python3
"""Draws the figures of the profile README as SVG files, in a light and a dark variant.

    python3 tools/figures.py        # writes assets/*.svg

Standard library only. GitHub shows README images without scripts, so every animation lives
inside the SVG as CSS keyframes. The hero is a real gradient descent run: the line's positions
are the iterates. The three phones are drawings of the apps, not screenshots.
"""
import math
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "assets"
SERIF = "Charter, 'Iowan Old Style', 'Palatino Linotype', Palatino, Georgia, serif"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "light": dict(ink="#1F2430", soft="#667085", faint="#D5DAE3", blue="#2F5BEA", amber="#D9820A", rose="#D6336C",
                  page="#FFFFFF"),
    "dark": dict(ink="#E6EAF2", soft="#8D97A8", faint="#343D4D", blue="#7AA2FF", amber="#FFB84D", rose="#FF6B9D",
                 page="#0D1117"),
}


def n(value: float) -> str:
    """A number as short SVG/CSS text."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


# ---------------------------------------------------------------------------------------------
# Hero: a line fitting itself to points
# ---------------------------------------------------------------------------------------------

W, H = 840, 300
PL, PR, PT, PB = 36, 812, 16, 268           # plot box in pixels
PW, PH = PR - PL, PB - PT
CYCLE, FIT_START, FIT_END = 18.0, 1.0, 7.5   # seconds: one loop, and the part where the line moves
ITERATIONS, RATE = 140, 0.45
FRAMES = [0, 1, 2, 3, 4, 6, 8, 10, 13, 16, 20, 25, 30, 36, 43, 50, 58, 67, 77, 88, 100, 113, 126, 140]


def hero_data() -> list[tuple[float, float]]:
    rng = random.Random(7)
    points = []
    for i in range(18):
        x = 0.06 + 0.90 * i / 17 + rng.uniform(-0.018, 0.018)
        y = 0.08 + 0.72 * x + rng.gauss(0, 0.05)
        points.append((x, min(max(y, 0.03), 0.97)))
    return points


def descend(points) -> list[tuple[float, float, float]]:
    """(w, b, loss) after 0, 1, 2, ... iterations of gradient descent on mean squared error."""
    w = b = 0.0
    size = len(points)
    run = []
    for _ in range(ITERATIONS + 1):
        errors = [w * x + b - y for x, y in points]
        run.append((w, b, sum(e * e for e in errors) / size))
        w -= RATE * 2 * sum(e * x for e, (x, _) in zip(errors, points)) / size
        b -= RATE * 2 * sum(errors) / size
    return run


def percent(iteration: int) -> float:
    """Where in the loop an iteration is shown. Square root: the early big steps get more time."""
    seconds = FIT_START + (FIT_END - FIT_START) * math.sqrt(iteration / ITERATIONS)
    return 100 * seconds / CYCLE


def keyframes(name: str, states: list[str]) -> str:
    """One @keyframes rule: the first state until the fit starts, the last one from its end on."""
    steps = [f"0%{{{states[0]}}}"]
    steps += [f"{n(percent(it))}%{{{state}}}" for it, state in zip(FRAMES, states)]
    steps.append(f"100%{{{states[-1]}}}")
    return f"@keyframes {name}{{{''.join(steps)}}}"


def hero(theme: dict) -> str:
    points = hero_data()
    run = descend(points)

    def px(x): return PL + x * PW
    def py(y): return PB - y * PH
    def line_y(it, x_pixel):
        w, b, _ = run[it]
        return py(w * (x_pixel - PL) / PW + b)

    def line_state(it):
        left, right = line_y(it, PL), line_y(it, PR)
        return f"transform:translate({PL}px,{n(left)}px) skewY({n(math.degrees(math.atan((right - left) / PW)))}deg)"

    css = [
        ".axis{fill:none;stroke:%s;stroke-width:1.5}" % theme["soft"],
        ".dot{fill:%s}" % theme["blue"],
        ".move{vector-effect:non-scaling-stroke;animation-duration:%ss;animation-timing-function:linear;"
        "animation-iteration-count:infinite}" % n(CYCLE),
        ".fit{stroke:%s;stroke-width:3;stroke-linecap:round;%s;animation-name:fit,show}"
        % (theme["rose"], line_state(ITERATIONS)),
        ".gap{stroke:%s;stroke-width:1.25;opacity:.55}" % theme["ink"],
        ".loss{fill:none;stroke:%s;stroke-width:2;stroke-linecap:round;stroke-dasharray:LEN LEN;"
        "stroke-dashoffset:0;animation-name:draw,show}" % theme["rose"],
        ".label{font-family:%s;font-size:17px;font-style:italic;fill:%s}" % (SERIF, theme["soft"]),
        "@keyframes show{0%{opacity:0}3%{opacity:1}94%{opacity:1}99%{opacity:0}100%{opacity:0}}",
        f"@keyframes draw{{0%{{stroke-dashoffset:LEN}}{n(percent(0))}%{{stroke-dashoffset:LEN}}"
        f"{n(percent(ITERATIONS))}%{{stroke-dashoffset:0}}100%{{stroke-dashoffset:0}}}}",
        keyframes("fit", [line_state(it) for it in FRAMES]),
    ]

    gaps = []
    for i, (x, y) in enumerate(points):
        def gap_state(it, x=x, y=y):
            return f"transform:translate({n(px(x))}px,{n(py(y))}px) scaleY({n(line_y(it, px(x)) - py(y))})"
        css.append(f".g{i}{{{gap_state(ITERATIONS)};animation-name:g{i},show}}")
        css.append(keyframes(f"g{i}", [gap_state(it) for it in FRAMES]))
        gaps.append(f'<line class="move gap g{i}" x1="0" y1="0" x2="0" y2="1"/>')
    # Without motion: everything rests in its fitted state.
    css.append("@media (prefers-reduced-motion:reduce){.move{animation:none}}")

    ticks = "".join(f"M{n(PL + PW * k / 8)},{PB}v6" for k in range(1, 9))
    ticks += "".join(f"M{PL},{n(PB - PH * k / 4)}h-6" for k in range(1, 5))

    # Loss curve, bottom right, where no point lives.
    lx, ly, lw, lh = 618, 184, 170, 58
    first_loss = run[0][2]
    trace = [(lx + lw * math.sqrt(it / ITERATIONS), ly + lh * (1 - math.sqrt(loss / first_loss)))
             for it, (_, _, loss) in enumerate(run)]
    curve = "M" + " L".join(f"{n(x)},{n(y)}" for x, y in trace)
    length = math.ceil(sum(math.dist(p, q) for p, q in zip(trace, trace[1:]))) + 4

    dots = "".join(f'<circle class="dot" cx="{n(px(x))}" cy="{n(py(y))}" r="5.5"/>' for x, y in points)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" '
        f'aria-label="A line fits itself to a cloud of points by gradient descent while the loss falls.">'
        f"<style>{''.join(css).replace('LEN', str(length))}</style>"
        f'<path class="axis" d="M{PL},{PT}V{PB}H{PR}{ticks}"/>'
        f'<path class="axis" d="M{lx},{ly}v{lh}h{lw}" opacity=".7"/>'
        f'<text class="label" x="{lx + 10}" y="{ly + 14}">loss</text>'
        f'<path class="move loss" d="{curve}"/>'
        f"{''.join(gaps)}{dots}"
        f'<line class="move fit" x1="0" y1="0" x2="{PW}" y2="0"/>'
        "</svg>\n"
    )


# ---------------------------------------------------------------------------------------------
# Phones: one drawing per app
# ---------------------------------------------------------------------------------------------

FW, FH = 240, 470   # phone drawing
LOOP = 10           # seconds per loop of a screen's animation


def phone(theme: dict, label: str, css: str, screen: str) -> str:
    base = (
        f"text{{font-family:{SANS};fill:{theme['ink']}}}"
        f".soft{{fill:{theme['soft']}}}.b{{font-weight:700}}"
        f".a{{animation-duration:{LOOP}s;animation-iteration-count:infinite;animation-timing-function:ease-out;"
        "transform-box:fill-box}"
        "@media (prefers-reduced-motion:reduce){.a{animation:none}}"
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {FW} {FH}" role="img" aria-label="{label}">'
        f"<style>{base}{css}</style>"
        f'<rect x="8" y="8" width="224" height="454" rx="38" fill="none" stroke="{theme["ink"]}" stroke-width="2.5"/>'
        f'<rect x="92" y="22" width="56" height="14" rx="7" fill="{theme["ink"]}"/>'
        f"{screen}</svg>\n"
    )


def phone_budget(theme: dict) -> str:
    """Expenses and calories: a goal ring fills, category bars grow, a scanned receipt waits below."""
    around = 2 * math.pi * 42
    css = (
        f".ring{{stroke-dasharray:{n(around)};stroke-dashoffset:{n(around * 0.32)};animation-name:ring}}"
        f"@keyframes ring{{0%,6%{{stroke-dashoffset:{n(around)}}}26%,94%{{stroke-dashoffset:{n(around * 0.32)}}}"
        f"100%{{stroke-dashoffset:{n(around)}}}}}"
        ".bar{transform-origin:left center;animation-name:bar}"
        "@keyframes bar{0%,10%{transform:scaleX(0)}32%,94%{transform:scaleX(1)}100%{transform:scaleX(0)}}"
    )
    rows = [("Home", 150, theme["blue"]), ("Food", 104, theme["amber"]), ("Transport", 62, theme["rose"])]
    bars = "".join(
        f'<text class="soft" x="30" y="{266 + 40 * i}" font-size="12">{name}</text>'
        f'<rect x="30" y="{273 + 40 * i}" width="180" height="8" rx="4" fill="{theme["faint"]}"/>'
        f'<rect class="a bar" x="30" y="{273 + 40 * i}" width="{width}" height="8" rx="4" fill="{colour}" '
        f'style="animation-delay:{n(0.12 * i)}s"/>'
        for i, (name, width, colour) in enumerate(rows)
    )
    screen = (
        '<text class="b" x="30" y="78" font-size="19">This month</text>'
        f'<circle cx="120" cy="158" r="42" fill="none" stroke="{theme["faint"]}" stroke-width="10"/>'
        # The quarter turn sits on a group: `.a` measures transforms from the shape's own box.
        f'<g transform="rotate(-90 120 158)"><circle class="a ring" cx="120" cy="158" r="42" fill="none" '
        f'stroke="{theme["blue"]}" stroke-width="10" stroke-linecap="round"/></g>'
        '<text class="b" x="120" y="157" font-size="21" text-anchor="middle">68%</text>'
        '<text class="soft" x="120" y="174" font-size="11" text-anchor="middle">of kcal goal</text>'
        f"{bars}"
        f'<rect x="30" y="382" width="180" height="50" rx="12" fill="none" stroke="{theme["faint"]}" stroke-width="1.5"/>'
        '<text class="b" x="44" y="404" font-size="13">Receipt scanned</text>'
        '<text class="soft" x="44" y="421" font-size="11">4 items, sorted on device</text>'
    )
    return phone(theme, "Drawing of a phone: a calorie ring, spending by category and a scanned receipt.", css, screen)


def phone_german(theme: dict) -> str:
    """German study: a blank is typed in letter by letter and checked, above a review card."""
    word = "fahre"
    letters = "".join(
        f".l{i}{{animation-name:l{i}}}@keyframes l{i}{{0%,{n(12 + 4 * i)}%{{opacity:0}}"
        f"{n(12.01 + 4 * i)}%,95%{{opacity:1}}100%{{opacity:0}}}}"
        for i in range(len(word))
    )
    css = (
        letters
        + ".ok{transform-origin:center;animation-name:ok}"
        "@keyframes ok{0%,38%{opacity:0;transform:scale(.4)}44%,95%{opacity:1;transform:scale(1)}100%{opacity:0}}"
        ".good{animation-name:good}@keyframes good{0%,58%{opacity:0}64%,95%{opacity:1}100%{opacity:0}}"
    )
    offsets = [0, 5.6, 14.8, 24.7, 31.3]   # rough advance of each letter in a bold 16px system font
    typed = "".join(
        f'<text class="a b l{i}" x="{n(61 + offsets[i])}" y="118" font-size="16" style="fill:{theme["rose"]}">{c}</text>'
        for i, c in enumerate(word)
    )
    pills = "".join(
        f'<rect x="{30 + 46 * i}" y="394" width="40" height="26" rx="13" fill="none" stroke="{theme["faint"]}" '
        f'stroke-width="1.5"/>'
        f'<text class="soft" x="{50 + 46 * i}" y="411" font-size="10" text-anchor="middle">{name}</text>'
        for i, name in enumerate(["Again", "Hard", "Good", "Easy"])
    )
    screen = (
        '<text class="soft" x="30" y="78" font-size="12">Exercise</text>'
        '<text x="30" y="118" font-size="16">Ich</text>'
        f'<path d="M56,124h52" stroke="{theme["soft"]}" stroke-width="1.5"/>'
        f"{typed}"
        '<text x="114" y="118" font-size="16">mit dem</text>'
        '<text x="30" y="144" font-size="16">Zug zur Arbeit.</text>'
        f'<g class="a ok"><circle cx="196" cy="138" r="11" fill="{theme["blue"]}"/>'
        f'<path d="M190.5,138.5l4,4l7,-8" fill="none" stroke="{theme["page"]}" stroke-width="2.2" '
        'stroke-linecap="round" stroke-linejoin="round"/></g>'
        '<text class="soft" x="30" y="206" font-size="12">Review</text>'
        f'<rect x="30" y="220" width="180" height="150" rx="16" fill="none" stroke="{theme["faint"]}" stroke-width="1.5"/>'
        '<text class="b" x="120" y="286" font-size="20" text-anchor="middle">der Bahnhof</text>'
        '<text class="soft" x="120" y="312" font-size="13" text-anchor="middle">istasyon</text>'
        f"{pills}"
        f'<rect class="a good" x="122" y="394" width="40" height="26" rx="13" fill="{theme["blue"]}"/>'
        f'<text class="a b good" x="142" y="411" font-size="10" text-anchor="middle" style="fill:{theme["page"]}">Good</text>'
    )
    return phone(theme, "Drawing of a phone: a German fill-in-the-blank exercise and a vocabulary review card.", css, screen)


def phone_flights(theme: dict) -> str:
    """Flight search: a strip of dates, then the combinations arrive cheapest first."""
    css = (
        ".row{animation-name:row}"
        "@keyframes row{0%,8%{opacity:0;transform:translateY(10px)}18%,95%{opacity:1;transform:translateY(0)}"
        "100%{opacity:0;transform:translateY(0)}}"
        ".pick{animation-name:pick}@keyframes pick{0%,52%{opacity:0}60%,95%{opacity:1}100%{opacity:0}}"
    )
    days = "".join(
        f'<rect x="{30 + 26 * i}" y="96" width="22" height="30" rx="7" '
        + (f'fill="{theme["amber"]}"' if i in (2, 5) else f'fill="none" stroke="{theme["faint"]}" stroke-width="1.5"')
        + "/>"
        f'<text x="{41 + 26 * i}" y="116" font-size="11" text-anchor="middle"'
        + (f' class="b" style="fill:{theme["page"]}"' if i in (2, 5) else ' class="soft"')
        + f">{14 + i}</text>"
        for i in range(7)
    )
    trips = [("AMS", "LIS", "Fri 16 to Mon 19", 84), ("EIN", "OPO", "Sat 17 to Tue 20", 97),
             ("AMS", "OPO", "Fri 16 to Mon 19", 112), ("BRU", "LIS", "Thu 15 to Sun 18", 126)]
    rows = "".join(
        f'<g class="a row" style="animation-delay:{n(0.35 * i)}s">'
        f'<rect x="30" y="{152 + 68 * i}" width="180" height="56" rx="12" fill="none" stroke="{theme["faint"]}" '
        f'stroke-width="1.5"/>'
        f'<text class="b" x="44" y="{176 + 68 * i}" font-size="14">{a} to {b}</text>'
        f'<text class="soft" x="44" y="{194 + 68 * i}" font-size="11">{dates}</text>'
        f'<text class="b" x="198" y="{186 + 68 * i}" font-size="15" text-anchor="end">€{price}</text></g>'
        for i, (a, b, dates, price) in enumerate(trips)
    )
    screen = (
        '<text class="b" x="30" y="78" font-size="19">Flexible dates</text>'
        f"{days}{rows}"
        f'<rect class="a pick" x="30" y="152" width="180" height="56" rx="12" fill="none" stroke="{theme["rose"]}" '
        'stroke-width="2.5"/>'
    )
    return phone(theme, "Drawing of a phone: a row of dates and flight combinations sorted by price.", css, screen)


def main() -> None:
    OUT.mkdir(exist_ok=True)
    for stale in OUT.glob("*.svg"):
        stale.unlink()
    drawings = {"hero": hero, "phone-budget": phone_budget, "phone-german": phone_german, "phone-flights": phone_flights}
    for name, theme in THEMES.items():
        for stem, draw in drawings.items():
            (OUT / f"{stem}-{name}.svg").write_text(draw(theme), encoding="utf-8")
    run = descend(hero_data())
    print(f"hero: loss {run[0][2]:.4f} -> {run[-1][2]:.4f}, w={run[-1][0]:.3f}, b={run[-1][1]:.3f}")
    print("wrote", ", ".join(sorted(p.name for p in OUT.glob("*.svg"))))


if __name__ == "__main__":
    main()
