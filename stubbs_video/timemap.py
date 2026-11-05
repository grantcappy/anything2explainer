"""Maps output time -> story time. The landscape cut plays the story 1:1 (106 s);
the vertical cut trims dwell time to land at ~80 s for TikTok / Shorts."""
import os

STORY_DUR = 106.0

# (output_seconds, story_seconds) knots, piecewise linear
KNOTS = {
    "landscape": [(0, 0), (106, 106)],
    "vertical": [(0, 0), (4.0, 5.2), (11.5, 16.0), (18.5, 25.0), (26.5, 36.0), (41.5, 56.0),
                 (56.0, 75.6), (64.0, 86.0), (74.0, 99.6), (80.4, 106.0)],
}

FORMAT = os.environ.get("FORMAT", "landscape")
if FORMAT not in KNOTS:
    raise SystemExit(f"FORMAT must be one of {list(KNOTS)}")

def duration(fmt=FORMAT):
    return KNOTS[fmt][-1][0]

def story_time(t, fmt=FORMAT):
    k = KNOTS[fmt]
    for (a, sa), (b, sb) in zip(k, k[1:]):
        if t <= b:
            return sa + (sb - sa) * max(0.0, (t - a)) / (b - a)
    return k[-1][1]
