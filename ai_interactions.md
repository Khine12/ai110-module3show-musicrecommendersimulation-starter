# AI Interactions Log

> Stretch features attempted: Challenge 1 (Additional Attributes), Challenge 2 (Multiple Scoring Modes / Strategy Pattern), Challenge 3 (Diversity Penalty), Challenge 4 (Visual Summary Table).

---

## Agentic Workflow (SF8) — Challenge 1: Additional Song Attributes

**What task did I give the agent?**
Expand the song dataset with 5+ new attributes beyond the baseline
(genre, mood, energy, tempo, valence, danceability, acousticness), and
wire those new attributes into the scoring logic so they actually affect
rankings rather than sitting unused in the CSV.

**Prompts used:**
- "Add 5 meaningful attributes to this song dataset that aren't already
  present — things like popularity, release decade, and detailed mood
  tags — and make sure each new attribute could plausibly change a
  recommendation, not just be decorative."
- "Update score_song so each of these new attributes only contributes
  points when the user profile actually specifies a preference for it —
  same pattern as the existing likes_acoustic bonus — so profiles that
  don't care about, say, decade aren't penalized or rewarded for it."

**What did the agent generate or change?**
- `data/songs.csv`: added `popularity` (0–100), `release_decade`
  (e.g. "2010s"), `mood_tags` (semicolon-separated tags like
  "euphoric;uplifting"), `is_explicit` (bool), and `language`.
- `src/recommender.py`: extended `Song` and `UserProfile` with matching
  optional fields (all defaulted, so the original starter test file's
  `Song(...)` / `UserProfile(...)` calls — which don't pass these fields —
  still work unchanged); added scoring bonuses for mood-tag match (+0.75),
  release-decade match (+0.5), popularity closeness (up to +0.5), language
  match (+0.5), and an explicit-content penalty (−1.0) when a user sets
  `avoid_explicit=True`.

**What did I verify or fix manually?**
- Ran `pytest` after the change to confirm the two starter tests still
  pass — they construct `Song`/`UserProfile` without any of the new
  fields, so I had to double check dataclass field ordering (fields with
  defaults must come after fields without defaults) rather than trust the
  agent's first draft blindly.
- Manually checked the "Acoustic Fan" profile output before and after to
  confirm the acoustic bonus math didn't change (it shouldn't have, since
  it's a separate field from the new attributes) — regression-checking,
  not just checking that the new feature worked in isolation.
- Picked mood tags and decades by hand for each of the 20 songs rather
  than accepting fully agent-generated values, since a plausible decade
  per artist/genre needed some judgment calls.

---

## Design Pattern (SF10) — Challenge 2: Multiple Scoring Modes

**Which design pattern did I use?**
The **Strategy** pattern: a `ScoringStrategy` abstract base class defines
a common `score(user_prefs, song)` interface, and four concrete
strategies (`BalancedStrategy`, `GenreFirstStrategy`, `MoodFirstStrategy`,
`EnergyFocusedStrategy`) each override just the class-level weight
constants (`GENRE_WEIGHT`, `MOOD_WEIGHT`, `ENERGY_MAX`). `Recommender` and
`recommend_songs()` both take a strategy (or a `mode` string that maps to
one) instead of hard-coding the scoring math.

**How did AI help me brainstorm or implement it?**
- Prompt: "I want main.py to support switching between a few different
  ranking styles — genre-first, mood-first, energy-focused — without
  duplicating the whole scoring function four times. What's a clean
  design pattern for this, and how would it look in Python without
  over-engineering it for a small script?"
- The suggestion was the Strategy pattern with shared logic in a base
  class and only the weights varying in subclasses, which avoided
  duplicating the acoustic/decade/mood-tag/popularity/language bonus code
  four separate times — only the three core weights actually differ
  between modes.

**How does the pattern appear in the final code?**
`src/recommender.py`: `ScoringStrategy` (base) plus `BalancedStrategy`,
`GenreFirstStrategy`, `MoodFirstStrategy`, `EnergyFocusedStrategy`,
collected in the `STRATEGIES` dict. `src/main.py` selects a mode via
`--mode <name>` on the command line (defaulting to `"balanced"`) and also
runs a side-by-side comparison of all four modes on the same profile.

---

## Challenge 3 note: Diversity / Artist-Repetition Penalty

**Prompt used:** "Write a rule that penalizes a song's score if its artist
is already present in the top recommendations list, so the same artist
doesn't dominate the top 5 — but keep the original score_song output
untouched so the printed 'reasons' still reflect the real, un-penalized
scoring logic."

This produced the greedy `_apply_diversity_penalty()` helper in
`src/recommender.py`: it builds the top-k list one slot at a time, and
each time an artist has already been chosen once, their remaining
candidates lose 1.5 points from their *effective* score for the purpose
of picking the next slot — the score shown to the user is still the real,
un-penalized `score_song` output, so the explanation text stays accurate.
See `model_card.md` for how this is documented as a fairness feature and
a before/after comparison.
