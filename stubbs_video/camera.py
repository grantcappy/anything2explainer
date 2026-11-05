"""Camera shots in story time, shared by render.py (picture) and music.py (whooshes/impacts).

Each shot: (start, end, zoom, target). The camera eases from wherever it is to the target
between start and end; start == end is a hard cut. Targets are resolved to points in
render.py because they depend on the layout.
"""

SHOTS = [
    (15.8, 16.5, 2.3, "crack"),        # crack opens
    (20.4, 21.2, 1.5, "crack_mid"),    # crack works down into binder
    (24.6, 25.2, 1.0, "home"),         # see the rain arrive
    (26.4, 26.4, 2.6, "water_in"),     # CUT: water enters the surface
    (27.6, 30.4, 2.0, "water_down"),   # follow it down
    (30.6, 31.4, 1.35, "base"),        # base soaks
    (35.6, 36.3, 1.0, "home"),         # winter arrives
    (38.4, 39.0, 2.1, "heave"),        # first freeze heaves the surface
    (43.6, 44.2, 1.0, "home"),
    (49.6, 50.2, 1.7, "base"),         # ice inside the base
    (53.8, 54.4, 1.0, "home"),
    (56.2, 56.8, 1.9, "base"),         # voids form
    (60.8, 61.6, 1.7, "sub"),          # soil turns to mud
    (65.6, 66.3, 1.0, "home"),         # traffic loads, bottom-up failure
    (72.4, 72.4, 2.2, "pothole"),      # CUT: pothole
    (80.0, 80.0, 1.0, "home"),         # reset while the comparison is on screen
    (88.4, 88.4, 2.4, "seal"),         # CUT: sealant goes in
    (92.2, 92.9, 1.0, "home"),         # rain now runs off
]

def sfx_events():
    """(story_time, kind) for sound design: 'push', 'pull' or 'cut'."""
    out, prev = [], 1.0
    for t0, t1, z, _ in SHOTS:
        if t1 <= t0:
            out.append((t0, "cut"))
        else:
            out.append((t0, "push" if z > prev else "pull"))
        prev = z
    return out
