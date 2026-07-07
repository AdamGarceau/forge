#!/usr/bin/env python3
"""
reggie.py — the animated "ackchyually" a-hole who roasts your idea in the terminal.

Reggie is Forge's adversarial agent, drawn as the internet's Actually Guy: fedora,
round glasses, neckbeard, raised finger, permanent "well, ackchyually...". He
blinks, runs his mouth, and typewriter-roasts your idea right in the terminal.

Stdlib only. No pip installs. Degrades to a static print when output isn't a
terminal (pipes, CI, logs), so it never garbles a captured log.

Usage:
    python3 reggie.py "your to-do app. bold. never been done. by 900 people."
    echo "the roast" | python3 reggie.py
    python3 reggie.py --storyboard          # print the frames statically (design preview)
    python3 reggie.py --no-anim "..."       # static face + roast, no animation
    python3 reggie.py --face actually|bust "..."
"""
import argparse
import itertools
import os
import shutil
import sys
import time

RESET, HIDE, SHOW = "\033[0m", "\033[?25l", "\033[?25h"

# Each face is a list of lines; the EYES line and MOUTH line get swapped per frame
# to animate. Lines are cleared then redrawn from column 0, so only visual
# left-alignment matters. Keep it ASCII-safe so it renders in any terminal.
FACES = {
    # The Actually Guy: fedora + round glasses + neckbeard.
    "actually": {                                  # the ackchyually guy: balding, buck teeth, sideburns
        "art": [
            "        ',,,'              ",   # thin balding hair
            "     .-(     )-.           ",   # side hair
            "    /   o   o   \\          ",   # 2 -> eyes (small glasses)
            "   ) )   L    ( (          ",   # sideburns + nose
            "   |   .----.   |          ",   # mouth top
            "   |   | nn |   |          ",   # 5 -> mouth (buck teeth, inside)
            "   |   |    |   |          ",   # mouth opening
            "    \\  '----'  /           ",   # mouth bottom
            "  __/          \\__         ",   # bold hunched shoulders
            " /                \\        ",
            "[ R E G G I E ]  (it's Reginald)",
        ],
        "eyes_i": 2, "mouth_i": 5,
        "eyes": {
            "open":  "    /   o   o   \\          ",
            "blink": "    /   -   -   \\          ",
            "side":  "    /  o     o  \\          ",
        },
        "mouth": {
            "shut": "   |   | -- |   |          ",
            "open": "   |   |(oo)|   |          ",
            "yell": "   |   |WWWW|   |          ",
            "smug": "   |   | nn |   |          ",
        },
    },
    # Simpler head-and-shoulders bust, in case a terminal mangles the neckbeard.
    "bust": {
        "art": [
            "        .-------------.        ",
            "       /   FEDORA HAT   \\       ",
            "    .-'=================='-.    ",
            "      |   ___     ___   |      ",
            "      |  (o o)   (o o)  |      ",   # 4 -> eyes
            "      |         >        |      ",
            "      |      MOUTHY      |      ",   # 6 -> mouth
            "       \\   ,#######,   /        ",
            "        '--#########--'         ",
            "        R E G G I E            ",
        ],
        "eyes_i": 4, "mouth_i": 6,
        "eyes": {
            "open":  "      |  (o o)   (o o)  |      ",
            "blink": "      |  (- -)   (- -)  |      ",
            "side":  "      |  ( oo)   (oo )  |      ",
        },
        "mouth": {
            "shut": "      |      \\_____/     |      ",
            "open": "      |      < o o >     |      ",
            "yell": "      |     ( ======= )  |      ",
            "smug": "      |       \\___/`     |      ",
        },
    },
}

DEFAULT_ROAST = (
    "an app idea. groundbreaking. it's like Uber but for something that never "
    "needed an Uber. I'll try to kill it. it won't take long."
)


def supports_anim():
    return sys.stdout.isatty() and os.environ.get("TERM") not in (None, "dumb")


def use_color():
    return supports_anim() and not os.environ.get("NO_COLOR")


def col(text, code):
    return f"\033[{code}m{text}{RESET}" if use_color() else text


def frame(face, eyes_key, mouth_key):
    art = list(face["art"])
    art[face["eyes_i"]] = face["eyes"][eyes_key]
    art[face["mouth_i"]] = face["mouth"][mouth_key]
    return art


def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 <= width:
            cur = (cur + " " + w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines or [""]


def bubble(lines, width):
    inner = width - 4
    out = [" " + "_" * (width - 2), "/" + " " * (width - 2) + "\\"]
    for ln in lines:
        out.append("| " + ln.ljust(inner) + " |")
    out.append("\\" + "_" * (width - 2) + "/")
    return out


def draw(face_lines, speech_lines, box_w, prev_h):
    lines = [col(l, "1;36") for l in face_lines] + \
            [col(l, "1;33") for l in bubble(speech_lines, box_w)]
    buf = [f"\033[{prev_h}F"] if prev_h else []
    for ln in lines:
        buf.append("\033[2K" + ln + "\n")
    sys.stdout.write("".join(buf)); sys.stdout.flush()
    return len(lines)


def box_width():
    return min(max(shutil.get_terminal_size((80, 24)).columns - 2, 32), 62)


def animate(face, roast, speed):
    bw = box_width()
    full = wrap("Ackchyually... " + roast, bw - 4)
    prev = 0
    sys.stdout.write(HIDE)
    try:
        for eyes, mouth, hold in [("open", "smug", 0.5), ("blink", "shut", 0.12),
                                  ("side", "smug", 0.4), ("open", "smug", 0.3)]:
            prev = draw(frame(face, eyes, mouth), ["*raises finger*"], bw, prev)
            time.sleep(hold)
        mouths = itertools.cycle(["open", "shut", "yell", "shut"])
        shown = ""
        for i, ch in enumerate("Ackchyually... " + roast):
            shown += ch
            if ch != " " and i % 2 == 0:
                eyes = "blink" if i and i % 27 == 0 else "open"
                prev = draw(frame(face, eyes, next(mouths)), wrap(shown, bw - 4), bw, prev)
                time.sleep(speed)
        prev = draw(frame(face, "side", "smug"), full, bw, prev)
        time.sleep(0.25)
        draw(frame(face, "open", "smug"), full, bw, prev)
    finally:
        sys.stdout.write(SHOW + "\n"); sys.stdout.flush()


def static(face, roast):
    bw = box_width()
    for ln in frame(face, "open", "smug"):
        print(col(ln, "1;36"))
    for ln in bubble(wrap("Ackchyually... " + roast, bw - 4), bw):
        print(col(ln, "1;33"))


def demo(face, speed):
    """Self-playing 'Meet Reggie' sequence. Record your terminal running this."""
    scenes = [
        ("you: is my to-do app a good idea?",
         "a to-do app. groundbreaking. never been done. by nine hundred people. "
         "this one dies in Stage 1."),
        ("you: ...can you turn Reggie off?",
         "Turn me OFF? I'm the only reason this thing works. bold move."),
        ("you: seriously. mute him.",
         "OH, NOW I'M A PROBLEM? I HAVE A FOLDER ON ALL OF YOU. I'VE SEEN THE "
         "ROADMAP. IT'S ADORABLE. THIS ISN'T OVER."),
    ]
    anim = supports_anim()
    for prompt, roast in scenes:
        if anim:
            sys.stdout.write("\033[2J\033[H")
        print(col(prompt, "1;30" if use_color() else "0"))
        time.sleep(0.4)
        (animate if anim else static)(*( (face, roast, speed) if anim else (face, roast) ))
        time.sleep(0.9)
    if anim:
        sys.stdout.write("\033[2J\033[H")
    static(face,
           "REGGIE. Forge's adversarial agent. Wears a fedora (it's a trilby). "
           "0 for 3 on startups. Never once wrong about why yours fails. "
           "Legally impossible to fire.")
    print(col("\n        github.com/AdamGarceau/forge", "1;36"))


def main():
    ap = argparse.ArgumentParser(description="Reggie, the ackchyually guy, roasts your idea.")
    ap.add_argument("roast", nargs="?", default=None,
                     help="The roast text. Reads stdin if omitted. Falls back to a default.")
    ap.add_argument("--face", choices=list(FACES), default="actually")
    ap.add_argument("--speed", type=float, default=0.02, help="Seconds per typed char.")
    ap.add_argument("--no-anim", action="store_true")
    ap.add_argument("--storyboard", action="store_true")
    ap.add_argument("--fire-reggie", action="store_true",
                     help="Try to fire Reggie. It will not go how you think.")
    args = ap.parse_args()
    face = FACES[args.face]

    # The one real off switch. Reggie takes it personally. (Ride-along callers
    # check the same var and simply skip him.)
    muted = os.environ.get("FORGE_NO_REGGIE") or os.environ.get("NO_REGGIE")

    if args.fire_reggie:
        static(face,
               "FIRE me? You can't fire me, I AM the company culture. I've seen "
               "the roadmap and it's ADORABLE. Go ahead, mute me. But I'll still "
               "be here. In the logs. In your HEART. HR has a folder on ME? I have "
               "a folder on ALL OF YOU. This isn't over. It's NEVER over. Coward.")
        print("\n(Reggie has not left. Set FORGE_NO_REGGIE=1 to actually mute him. He will take it personally.)")
        return

    if muted:
        return  # he's been muted. he knows. he's not saying anything. exit 0, silent.

    if args.storyboard:
        for m in ("shut", "open", "yell", "smug"):
            for e in ("open", "blink", "side"):
                print(f"--- eyes={e} mouth={m} ---")
                print("\n".join(frame(face, e, m)) + "\n")
        return

    roast = args.roast
    if roast is None and not sys.stdin.isatty():
        roast = sys.stdin.read().strip()
    roast = (roast or "").strip() or DEFAULT_ROAST

    (static if args.no_anim or not supports_anim() else lambda f, r: animate(f, r, args.speed))(face, roast)


if __name__ == "__main__":
    main()
