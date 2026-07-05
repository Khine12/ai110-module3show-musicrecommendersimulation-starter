# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

This version (**VibeFinder 1.0**) is a content-based recommender: it
never looks at what other users liked, only at each song's own attributes
compared against one user's stated taste profile. Every recommendation
comes with a plain-English explanation of exactly which rules fired and
how many points each one contributed, so nothing about the ranking is a
black box. It also includes four optional stretch features: extra song
attributes, switchable ranking strategies, an artist-diversity penalty,
and a formatted table output — see the Stretch Features section below.

---

## How The System Works

**What features does each `Song` use?**
Core: `genre`, `mood`, `energy` (0.0–1.0), `tempo_bpm`, `valence`
(0.0–1.0). Stretch (Challenge 1): `popularity` (0–100), `release_decade`,
`mood_tags` (semicolon-separated, e.g. "euphoric;uplifting"),
`is_explicit`, and `language`. `tempo_bpm` and `valence` are loaded and
available but not currently scored — see Future Work in `model_card.md`.

**What does a `UserProfile` store?**
Core: `favorite_genre`, `favorite_mood`, `target_energy`,
`likes_acoustic`. Stretch (optional, default off): `preferred_mood_tag`,
`preferred_decade`, `target_popularity`, `preferred_language`,
`avoid_explicit`. The functional CLI in `main.py` uses an equivalent plain
dict shape, e.g. `{"genre": ..., "mood": ..., "energy": ...}`.

**How is a score computed?** (the "Algorithm Recipe" — Balanced mode)

| Rule | Points |
|---|---|
| Genre matches `favorite_genre` | +2.0 (flat) |
| Mood matches `favorite_mood` | +1.0 (flat) |
| Energy closeness to `target_energy` | up to +1.5, decaying linearly with the gap |
| `likes_acoustic` is true | up to +1.0, scaled by the song's own acousticness |
| Mood tag match (optional) | +0.75 (flat) |
| Release decade match (optional) | +0.5 (flat) |
| Popularity closeness (optional) | up to +0.5, decaying linearly with the gap |
| Language match (optional) | +0.5 (flat) |
| Explicit content, if avoided (optional) | −1.0 penalty |

Numeric features (energy, popularity) use a **closeness score**, not a
"higher is better" score: e.g.
`points = max(0, 1.5 * (1 - abs(song_energy - target_energy)))`. A song
that's *too* energetic for a chill listener is penalized just as much as
one that isn't energetic enough.

**How does the system choose which songs to recommend?**
Every song in the catalog is scored independently against the profile
(`score_song`), and then the whole catalog is sorted by score and the top
`k` are returned (`recommend_songs` / `Recommender.recommend`). Two
separate functions exist on purpose: `score_song` is a judge for *one*
song, `recommend_songs` is the ranking step that runs that judge across
the *entire* catalog — you need scoring before you can rank.

```
Input (UserProfile / prefs dict)
        │
        ▼
Process: loop over every song, call score_song(prefs, song) → (score, reasons)
        │
        ▼
Output: sorted(all_scored_songs, reverse=True)[:k] → Top-K Recommendations
        (optionally re-ranked by the diversity penalty — see Stretch Features)
```

**What changed from the starter logic?**
The starter's `load_songs`, `score_song`, and `recommend_songs` were all
`TODO` stubs, and `Recommender.recommend` / `explain_recommendation` just
returned placeholders. All of that is now implemented. I also fixed a bug
in the starter `main.py`, which imported `from recommender import ...`
even though `tests/test_recommender.py` imports `from src.recommender
import ...` — `main.py` now imports `from src.recommender import ...` to
match the package structure so `python -m src.main` actually runs.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python -m src.main
   # or choose a ranking mode:
   python -m src.main --mode genre_first     # also: mood_first, energy_focused
   ```

### Running Tests

Run the starter tests with:

```bash
pytest
```

Both starter tests pass:
- `test_recommend_returns_songs_sorted_by_score`
- `test_explain_recommendation_returns_non_empty_string`

---

## Sample Recommendation Output

```
=== Default (Pop/Happy) [mode: balanced] ===
Preferences: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
|   # | Title          | Artist        |   Score | Reasons                                                         |
|-----|----------------|---------------|---------|-------------------------------------------------------------------|
|   1 | Sunrise City   | Neon Echo     |    4.47 | genre match (+2.0); mood match (+1.0); energy closeness (+1.47) |
|   2 | Wildfire Heart | Max Pulse     |    3.38 | genre match (+2.0); energy closeness (+1.38)                    |
|   3 | Gym Hero       | Max Pulse     |    3.30 | genre match (+2.0); energy closeness (+1.30)                    |
|   4 | Rooftop Lights | Indigo Parade |    2.44 | mood match (+1.0); energy closeness (+1.44)                     |
|   5 | Golden Static  | Indigo Parade |    2.32 | mood match (+1.0); energy closeness (+1.32)                     |
```

(Full output for every profile tested, plus the mode comparison and
diversity-penalty comparison, is in `model_card.md` under Evaluation.)

---

## Experiments You Tried

- **Genre weight shift (this is exactly what "Genre-First" mode is):**
  raising the genre weight to 3.0 and dropping energy's max to 1.0 kept
  the *same* top 3 songs as Balanced mode for the Default profile, just
  with higher scores — because pop already had the deepest genre bench in
  this catalog. The more interesting shift was **Mood-First**, which
  swapped in two mood-only matches (Rooftop Lights, Golden Static) in
  place of two genre-only matches (Wildfire Heart, Gym Hero) entirely.
- **Adding `likes_acoustic`:** turning this flag on for a jazz/relaxed
  profile pushed already-strong genre/mood matches even higher (Paper
  Moon: ~3.0 → 5.40), but it amplifies existing matches more than it
  rescues weak ones.
- **Adversarial profile:** requesting `lofi` + `sad` + `energy: 0.9` (a
  combination that barely exists in the dataset) produced a top-5 list
  where no score exceeded 3.45, versus 4.4+ for coherent profiles — a
  useful signal that this system doesn't currently surface to the user.
- **Diversity penalty on vs. off:** without it, 4 of the top 5 Default
  recommendations came from just 2 artists (Max Pulse, Indigo Parade).
  With it on, one of those repeats is replaced by a rock song from a
  completely different artist. Full comparison in `model_card.md`.

---

## Limitations and Risks

- It only works on a tiny, hand-curated 20-song catalog — nowhere near
  enough variety to represent real listening habits.
- It does not understand lyrics, language content, or vocal style at all
  (the `language` field is just a label, not an analysis).
- Genre is weighted more heavily than mood or energy in Balanced mode, so
  it can over-favor one genre once a user states a preference.
- `tempo_bpm` and `valence` are loaded but never used in scoring.
- The diversity penalty is off by default — a user has to opt in, so the
  filter-bubble risk above is real unless `diversity_penalty=True` is set.

Go deeper on this in `model_card.md`.

---

## Stretch Features

- **Challenge 1 — Additional Attributes:** `popularity`, `release_decade`,
  `mood_tags`, `is_explicit`, `language`, all wired into scoring as
  optional bonuses/penalties. Workflow documented in `ai_interactions.md`.
- **Challenge 2 — Multiple Scoring Modes:** a Strategy design pattern
  (`ScoringStrategy` + 4 subclasses) lets you switch modes via
  `python -m src.main --mode <name>`. Design rationale in
  `ai_interactions.md`.
- **Challenge 3 — Diversity Penalty:** an artist-repetition penalty,
  toggled via `diversity_penalty=True`, greedily re-ranks the top-k to
  reduce one artist dominating the list. Documented with a before/after
  comparison in `model_card.md`.
- **Challenge 4 — Visual Summary Table:** all CLI output is rendered as a
  formatted table (via `tabulate`) including the `#`, `Title`, `Artist`,
  `Score`, and `Reasons` columns.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Building the scoring rule made it obvious how much a recommender's
"personality" comes down to arbitrary-seeming weight choices — the
difference between a +2.0 genre bonus and a +1.0 mood bonus is what
decides whether a user drowning in one genre feels like a feature or a
rut. Building the four ranking modes made that even more concrete: the
same catalog and the same profile produce a genuinely different top 5
depending on which factor is weighted heaviest. It also reframed bias for
me — nothing in this system is doing anything sneaky or ill-intentioned,
the bias just falls straight out of which numbers happen to be bigger
than which other numbers. That's a useful lens for real platforms too — a
lot of "the algorithm keeps showing me the same thing" complaints are
probably exactly this kind of weighting effect, just at a much larger
scale and with far more signals feeding in.
