# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name

**VibeFinder 1.0**

---

## 2. Intended Use

VibeFinder generates a ranked top-k list of song suggestions for one user
at a time, based entirely on that user's own stated preferences — it never
looks at other users' behavior. It assumes the user can articulate their
taste as a favorite genre, favorite mood, a target energy level, and
optionally a handful of finer-grained preferences (whether they like
acoustic songs, a favorite mood tag, decade, target popularity, preferred
language, or whether to avoid explicit content). This is built for
classroom exploration of how content-based recommenders work, not for
real end users — the catalog is small and hand-curated, and the scoring
is simple, transparent arithmetic rather than anything learned from data.

---

## 3. How the Model Works

Every song gets flat bonus points for matching the user's favorite genre
and favorite mood, plus a sliding-scale bonus for how close its energy is
to the user's target — closer earns more, too far off earns nothing,
rather than simply rewarding "more energy is always better." A handful of
optional bonuses only apply if the user actually specifies a preference
for them: liking acoustic songs, wanting a specific mood tag (like
"nostalgic" or "euphoric"), wanting a specific release decade, wanting a
certain popularity level, wanting a specific language, or wanting to avoid
explicit content (which applies a penalty instead of a bonus). The system
scores every song in the catalog this way, then returns the top 5
highest-scoring songs along with the specific reasons behind each score.

**Switchable ranking modes (Strategy pattern):** the *relative importance*
of genre, mood, and energy isn't fixed — VibeFinder ships four modes:
- **Balanced** (default): genre +2.0, mood +1.0, energy up to +1.5
- **Genre-First**: genre +3.0, mood +1.0, energy up to +1.0
- **Mood-First**: genre +1.0, mood +3.0, energy up to +1.0
- **Energy-Focused**: genre +1.0, mood +1.0, energy up to +3.0

All four modes share the exact same optional bonuses (acoustic, mood tag,
decade, popularity, language) — only the three core weights change.

**Diversity penalty:** by default, `recommend_songs()` and
`Recommender.recommend()` return a straightforward sorted list. Passing
`diversity_penalty=True` switches to a greedy selection: each time a slot
in the top-k is filled, any artist already picked has 1.5 points
subtracted from their *remaining* candidates' effective score before the
next slot is chosen. This changes final ordering/selection only — the
score and reasons shown for a song are always its real, un-penalized
score, so explanations stay accurate.

---

## 4. Data

The catalog has 20 songs — the original 10 from the starter dataset plus
10 additional songs I generated to broaden genre and mood coverage.
Genres represented: pop, indie pop, lofi, rock, ambient, jazz, and
synthwave. Moods represented: happy, chill, intense, moody, focused,
relaxed, energetic, angry, and sad.

**Additional attributes (Challenge 1):** `popularity` (0–100),
`release_decade` (2000s/2010s/2020s), `mood_tags` (semicolon-separated
descriptive tags like "euphoric", "nostalgic", "aggressive",
"introspective", "cinematic", "warm", "melancholy", "defiant",
"uplifting", "dreamy"), `is_explicit` (bool), and `language`
(english/instrumental).

What's still missing: entire genres like hip-hop, classical, or country
aren't represented at all, and several genre/mood combinations (e.g.,
"angry rock," "sad lofi") only have a single matching song, so those
profiles are really choosing among a pool of one rather than genuinely
ranking anything. Popularity and decade values were assigned by hand,
not sourced from any real chart data, so they're illustrative rather
than accurate.

---

## 5. Strengths

For profiles where the genre has several representative songs (pop, lofi,
jazz, rock), the ranking behaves sensibly — the "Chill Lofi" and "Intense
Rock" results below put genuinely strong genre+mood+energy matches at the
top, matching my own intuition about which songs fit the vibe best. The
`likes_acoustic` flag works as intended: turning it on for a jazz/relaxed
profile correctly boosts already-strong acoustic jazz tracks. The mode
comparison below shows the Strategy pattern actually works — the same
profile produces meaningfully different rankings depending on which
factor is weighted most heavily, not just cosmetic score differences. The
diversity penalty demo shows it does exactly what it's meant to: it
doesn't touch a song's real score or explanation, it only reorders which
songs make the final cut when one artist would otherwise dominate.

---

## 6. Limitations and Bias

Genre dominates the ranking in Balanced mode specifically. A genre match
(+2.0) is worth more than a perfect mood match (+1.0) and more than the
max possible energy bonus (+1.5), so a song with only a genre match can
outrank a song with a perfect mood *and* energy match in a different
genre — visible in the "Default (Pop/Happy)" results below, where
Wildfire Heart (genre-only) outscores Rooftop Lights (mood-only) despite
Rooftop Lights actually matching the requested mood. This is a
filter-bubble risk: a user who states one favorite genre will keep seeing
that genre regardless of how well mood or energy actually fits — Genre-
First mode makes this bias even more pronounced by design, while Mood-
First and Energy-Focused modes shift the bias toward whichever factor
they emphasize instead of removing it. `tempo_bpm` and `valence` are
loaded from the CSV but never scored, so they contribute nothing to
differentiating songs right now. Two of the artists (Neon Echo, Max
Pulse, Indigo Parade, Slow Stereo, Voltline, Paper Lanterns, LoRoom,
Orbit Bloom) each have 2–3 songs in the catalog, which is exactly why the
same artist tends to dominate a genre-heavy top 5 without the diversity
penalty turned on.

---

## 7. Evaluation

I tested five profiles in Balanced mode (no diversity penalty, so this
section reflects the base "sorted by score" behavior), then separately
compared ranking modes and the diversity penalty.

### Default (Pop/Happy)
```
Preferences: {'genre': 'pop', 'mood': 'happy', 'energy': 0.8}
1. Sunrise City   - Neon Echo     - 4.47 - genre match (+2.0); mood match (+1.0); energy closeness (+1.47)
2. Wildfire Heart - Max Pulse     - 3.38 - genre match (+2.0); energy closeness (+1.38)
3. Gym Hero       - Max Pulse     - 3.30 - genre match (+2.0); energy closeness (+1.30)
4. Rooftop Lights - Indigo Parade - 2.44 - mood match (+1.0); energy closeness (+1.44)
5. Golden Static  - Indigo Parade - 2.32 - mood match (+1.0); energy closeness (+1.32)
```

### Chill Lofi
```
Preferences: {'genre': 'lofi', 'mood': 'chill', 'energy': 0.35}
1. Library Rain    - Paper Lanterns - 4.50 - genre match (+2.0); mood match (+1.0); energy closeness (+1.50)
2. Midnight Coding - LoRoom         - 4.39 - genre match (+2.0); mood match (+1.0); energy closeness (+1.40)
3. Focus Flow      - LoRoom         - 3.42 - genre match (+2.0); energy closeness (+1.42)
4. Quiet Static    - Paper Lanterns - 3.28 - genre match (+2.0); energy closeness (+1.28)
5. Velvet Room     - Slow Stereo    - 2.47 - mood match (+1.0); energy closeness (+1.47)
```
**Comparison to Default:** with a coherent genre+mood+energy profile, the
top 2 results are exactly the songs earning all three bonuses at once —
unlike Default, where a genre-only match (Wildfire Heart) still beat a
mood-only match (Rooftop Lights).

### Intense Rock
```
Preferences: {'genre': 'rock', 'mood': 'intense', 'energy': 0.9}
1. Storm Runner    - Voltline  - 4.48 - genre match (+2.0); mood match (+1.0); energy closeness (+1.48)
2. Blackout Riot   - Voltline  - 3.42 - genre match (+2.0); energy closeness (+1.43)
3. Ghost Frequency - Voltline  - 3.05 - genre match (+2.0); energy closeness (+1.05)
4. Gym Hero        - Max Pulse - 2.46 - mood match (+1.0); energy closeness (+1.46)
5. Wildfire Heart  - Max Pulse - 1.47 - energy closeness (+1.47)
```
**Comparison to Chill Lofi:** Voltline (a rock act) sweeps the top 3 here
the same way Paper Lanterns/LoRoom dominate Chill Lofi — a clear preview
of the artist-repetition problem the diversity penalty addresses below.

### Acoustic Fan
```
Preferences: {'genre': 'jazz', 'mood': 'relaxed', 'energy': 0.3, 'likes_acoustic': True}
1. Paper Moon          - Slow Stereo - 5.40 - genre match (+2.0); mood match (+1.0); energy closeness (+1.50); acoustic bonus (+0.90)
2. Coffee Shop Stories - Slow Stereo - 5.28 - genre match (+2.0); mood match (+1.0); energy closeness (+1.40); acoustic bonus (+0.89)
3. Velvet Room         - Slow Stereo - 4.30 - genre match (+2.0); energy closeness (+1.46); acoustic bonus (+0.85)
4. Spacewalk Thoughts  - Orbit Bloom - 2.39 - energy closeness (+1.47); acoustic bonus (+0.92)
5. Neon Requiem        - Orbit Bloom - 2.33 - energy closeness (+1.38); acoustic bonus (+0.95)
```
**Comparison to Chill Lofi:** both target low energy, but here Slow
Stereo takes all top 3 slots — the single most extreme case of one artist
dominating a top 5 in this whole evaluation.

### Adversarial (High-Energy + Sad)
```
Preferences: {'genre': 'lofi', 'mood': 'sad', 'energy': 0.9}
1. Quiet Static    - Paper Lanterns - 3.45 - genre match (+2.0); mood match (+1.0); energy closeness (+0.45)
2. Midnight Coding - LoRoom         - 2.78 - genre match (+2.0); energy closeness (+0.78)
3. Focus Flow      - LoRoom         - 2.75 - genre match (+2.0); energy closeness (+0.75)
4. Library Rain    - Paper Lanterns - 2.67 - genre match (+2.0); energy closeness (+0.67)
5. Storm Runner    - Voltline       - 1.48 - energy closeness (+1.48)
```
**What surprised me:** this profile is intentionally contradictory —
lofi + sad songs in this catalog are all low-energy, but the target
energy was set to 0.9. The system doesn't notice or flag the
contradiction; it just quietly caps every score lower across the board
(nothing above 3.45, versus 4.4+ for every coherent profile above) and
still confidently returns a full top 5.

### Mode Comparison (same Default Pop/Happy profile, top 3 shown)
```
Balanced:        1. Sunrise City (4.47)  2. Wildfire Heart (3.38)  3. Gym Hero (3.30)
Genre-First:     1. Sunrise City (4.98)  2. Wildfire Heart (3.92)  3. Gym Hero (3.87)
Mood-First:      1. Sunrise City (4.98)  2. Rooftop Lights (3.96)  3. Golden Static (3.88)
Energy-Focused:  1. Sunrise City (4.94)  2. Rooftop Lights (3.88)  3. Wildfire Heart (3.76)
```
**Comment:** Genre-First keeps the exact same top 3 as Balanced (just
higher scores) because pop already had the deepest genre bench. Mood-First
swaps in Rooftop Lights and Golden Static — both mood matches without a
genre match — bumping out the genre-only Wildfire Heart and Gym Hero
entirely. Energy-Focused lands somewhere in between: it keeps Rooftop
Lights (mood match, close energy) but also keeps Wildfire Heart (genre
match, close energy), since neither factor dominates enough to fully
exclude the other. This confirms the Strategy pattern is doing real work,
not just relabeling the same ranking.

### Diversity Penalty Comparison (Default Pop/Happy profile)
```
Without penalty:                  With penalty:
1. Sunrise City   - Neon Echo      1. Sunrise City   - Neon Echo
2. Wildfire Heart - Max Pulse      2. Wildfire Heart - Max Pulse
3. Gym Hero       - Max Pulse      3. Rooftop Lights - Indigo Parade
4. Rooftop Lights - Indigo Parade  4. Gym Hero       - Max Pulse
5. Golden Static  - Indigo Parade  5. Storm Runner   - Voltline
```
**Comment:** without the penalty, Max Pulse (Wildfire Heart + Gym Hero)
takes 2 of the top 3 slots and Indigo Parade takes 2 of the top 5 — 4 of
5 recommendations come from just 2 artists. With the penalty on, Gym Hero
(Max Pulse's second song) gets pushed from #3 to #4, making room for
Rooftop Lights (a different artist) at #3, and Golden Static (Indigo
Parade's second song) drops out of the top 5 entirely in favor of Storm
Runner — a rock song that wouldn't have appeared at all otherwise. The
underlying scores and explanations shown for every song are unchanged;
only which songs make the cut, and in what order, is affected. This
directly reduces the filter-bubble risk described under Limitations and
Bias: a user is less likely to see their whole top 5 come from 2 artists.

---

## 8. Future Work

1. Score `valence` alongside mood (e.g., a "happy" mood target should also
   reward high valence), instead of leaving it in the data but unused.
2. Extend the diversity penalty to also discourage genre repetition, not
   just artist repetition, since the genre-dominance bias is broader than
   any single artist.
3. Detect low-scoring-across-the-board results (like the adversarial
   case) and surface a message to the user that their stated preferences
   may be internally inconsistent, rather than silently returning a
   weaker list.
4. Make the diversity penalty's strength (currently a flat 1.5 points per
   repeat) configurable per user, since how much variety someone wants is
   itself a preference.

---

## 9. Personal Reflection

The clearest lesson was watching the genre-dominance bias show up in
actual output rather than just suspecting it in the abstract — the
Default (Pop/Happy) run put a genre-only match ahead of a mood-only match
before I'd tested anything, simply because of how the weights were set
going in. Building the four ranking modes made that bias even more
concrete: Genre-First didn't even change *which* songs showed up, only
how confidently they scored, while Mood-First swapped out two entire
recommendations — proof that the weights aren't a cosmetic detail, they
are the recommender's personality. The diversity penalty was the most
satisfying feature to verify, because the before/after comparison is so
direct: the same catalog, the same profile, and just enabling one flag
visibly breaks up an artist's grip on the top 5. What surprised me most
is how convincing a purely rule-based, weighted-sum system can feel — the
output reads like a genuine recommendation even though nothing is being
learned, it's just arithmetic applied consistently, mode after mode.

---

## 10. Stretch Features Summary

| Feature | Where implemented | How it's verified above |
|---|---|---|
| Challenge 1: 5 new attributes (popularity, release_decade, mood_tags, is_explicit, language), all wired into scoring | `data/songs.csv`, `src/recommender.py` | Acoustic Fan profile combines acoustic bonus with genre/mood/energy; see `ai_interactions.md` for the agentic workflow |
| Challenge 2: Strategy pattern, 4 switchable ranking modes | `src/recommender.py` (`ScoringStrategy` + subclasses), `src/main.py` (`--mode` flag) | Mode Comparison table above |
| Challenge 3: artist diversity penalty | `src/recommender.py` (`_apply_diversity_penalty`) | Diversity Penalty Comparison above |
| Challenge 4: formatted table output with reasons | `src/main.py` (via `tabulate`) | Every code block above is the actual rendered table output |
