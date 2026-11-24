"""Shared constants. Aspect names match the five aspects in the synopsis (Section 5.2.4)."""

ASPECTS = ["doctor", "staff", "waiting", "cleanliness", "billing"]

# Per-aspect label set. The synopsis defines polarity as positive / neutral / negative.
# In real free text most reviews do not mention every aspect, so we add "absent"
# (aspect not mentioned). Metrics for the polarity labels are reported on mentioned aspects.
POLARITIES = ["negative", "neutral", "positive"]
LABELS = ["absent"] + POLARITIES
LABEL2ID = {l: i for i, l in enumerate(LABELS)}
ID2LABEL = {i: l for l, i in LABEL2ID.items()}

# Mapping from the overall star rating to an overall-level label (used for RQ4).
def overall_label(stars: int) -> str:
    if stars >= 4:
        return "positive"
    if stars == 3:
        return "neutral"
    return "negative"
