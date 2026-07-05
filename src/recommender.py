"""
recommender.py

Core logic for the VibeFinder music recommender.

This file provides two parallel interfaces on top of the same scoring logic:

1. A functional interface (`load_songs`, `score_song`, `recommend_songs`)
   used by src/main.py, which works with plain dicts loaded from CSV.
2. An OOP interface (`Song`, `UserProfile`, `Recommender`) required by
   tests/test_recommender.py, which works with typed dataclasses.

Both interfaces share the same underlying scoring logic (`ScoringStrategy`
subclasses) so behavior is consistent no matter which one you call.

Stretch features implemented here:
- Challenge 1: five extra song attributes (popularity, release_decade,
  mood_tags, is_explicit, language), all wired into scoring.
- Challenge 2: a Strategy design pattern with four switchable ranking
  modes (Balanced / Genre-First / Mood-First / Energy-Focused).
- Challenge 3: a greedy "artist diversity penalty" applied when building
  the final top-k list, to reduce filter-bubble repetition.
"""

import csv
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py

    The five fields after `acousticness` are Challenge 1 additions and all
    have defaults so existing code (like the starter tests) that constructs
    a Song without them still works unchanged.
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: float = 50.0
    release_decade: str = "2020s"
    mood_tags: str = ""          # semicolon-separated, e.g. "euphoric;nostalgic"
    is_explicit: bool = False
    language: str = "english"


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py

    The fields after `likes_acoustic` are optional Challenge 1 preferences;
    all default to None/False so existing code that builds a UserProfile
    with only the original four fields still works unchanged.
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    preferred_mood_tag: Optional[str] = None
    preferred_decade: Optional[str] = None
    target_popularity: Optional[float] = None
    preferred_language: Optional[str] = None
    avoid_explicit: bool = False


# ---------------------------------------------------------------------------
# Internal helpers: let the same scoring logic work with both dicts (loaded
# from CSV, used by main.py) and dataclasses (Song / UserProfile, used by
# the Recommender class and the tests).
# ---------------------------------------------------------------------------

def _field(obj, key, default=None):
    """Get `key` off a dict or an object attribute, whichever `obj` is."""
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _normalize_prefs(user_prefs: Union[Dict, UserProfile]) -> Dict:
    """Turn either a UserProfile or a plain prefs dict into one common shape.

    src/main.py passes a dict shaped like {"genre": ..., "mood": ..., "energy": ...}.
    tests/test_recommender.py passes a UserProfile with favorite_genre / favorite_mood /
    target_energy / likes_acoustic. Both are supported here, plus the optional
    Challenge 1 preference fields (mood tag, decade, popularity, language, explicit).
    """
    if isinstance(user_prefs, UserProfile):
        return {
            "genre": user_prefs.favorite_genre,
            "mood": user_prefs.favorite_mood,
            "energy": user_prefs.target_energy,
            "likes_acoustic": user_prefs.likes_acoustic,
            "mood_tag": user_prefs.preferred_mood_tag,
            "decade": user_prefs.preferred_decade,
            "popularity": user_prefs.target_popularity,
            "language": user_prefs.preferred_language,
            "avoid_explicit": user_prefs.avoid_explicit,
        }
    return {
        "genre": user_prefs.get("genre", user_prefs.get("favorite_genre")),
        "mood": user_prefs.get("mood", user_prefs.get("favorite_mood")),
        "energy": user_prefs.get("energy", user_prefs.get("target_energy", 0.5)),
        "likes_acoustic": user_prefs.get("likes_acoustic", False),
        "mood_tag": user_prefs.get("mood_tag"),
        "decade": user_prefs.get("decade"),
        "popularity": user_prefs.get("popularity"),
        "language": user_prefs.get("language"),
        "avoid_explicit": user_prefs.get("avoid_explicit", False),
    }


def _closeness_score(value: float, target: float, max_points: float) -> float:
    """Reward values closer to the target rather than simply higher/lower.

    A perfect match earns max_points; the score falls off linearly as the
    gap between value and target grows, floored at 0.
    """
    gap = abs(value - target)
    return max(0.0, max_points * (1 - gap))


def _mood_tags_list(song) -> List[str]:
    raw = _field(song, "mood_tags", "") or ""
    return [t.strip() for t in raw.split(";") if t.strip()]


# ---------------------------------------------------------------------------
# Challenge 2: Strategy design pattern.
#
# Each strategy shares the exact same scoring *ingredients* (genre match,
# mood match, energy closeness, the Challenge-1 acoustic/decade/mood-tag/
# popularity/language bonuses) but assigns them different weights, so
# switching modes actually changes *which* factor dominates the ranking.
# ---------------------------------------------------------------------------

class ScoringStrategy(ABC):
    """Common interface every ranking strategy implements."""

    name: str = "base"
    GENRE_WEIGHT: float = 2.0
    MOOD_WEIGHT: float = 1.0
    ENERGY_MAX: float = 1.5

    def score(self, user_prefs: Union[Dict, UserProfile], song: Union[Dict, Song]) -> Tuple[float, List[str]]:
        prefs = _normalize_prefs(user_prefs)
        score = 0.0
        reasons: List[str] = []

        genre = _field(song, "genre")
        mood = _field(song, "mood")
        energy = _field(song, "energy")
        acousticness = _field(song, "acousticness")
        popularity = _field(song, "popularity")
        decade = _field(song, "release_decade")
        is_explicit = _field(song, "is_explicit", False)
        language = _field(song, "language")

        # --- Core recipe: weights differ per-strategy ---
        if prefs["genre"] and genre == prefs["genre"]:
            score += self.GENRE_WEIGHT
            reasons.append(f"genre match (+{self.GENRE_WEIGHT})")

        if prefs["mood"] and mood == prefs["mood"]:
            score += self.MOOD_WEIGHT
            reasons.append(f"mood match (+{self.MOOD_WEIGHT})")

        if energy is not None and prefs["energy"] is not None:
            pts = _closeness_score(energy, prefs["energy"], self.ENERGY_MAX)
            if pts > 0:
                score += pts
                reasons.append(f"energy closeness (+{pts:.2f})")

        # --- Shared optional bonuses (Challenge 1 attributes) ---
        if prefs.get("likes_acoustic") and acousticness is not None:
            pts = acousticness * 1.0
            if pts > 0:
                score += pts
                reasons.append(f"likes acoustic, high acousticness (+{pts:.2f})")

        if prefs.get("mood_tag"):
            if prefs["mood_tag"] in _mood_tags_list(song):
                score += 0.75
                reasons.append(f"mood tag match: '{prefs['mood_tag']}' (+0.75)")

        if prefs.get("decade") and decade == prefs["decade"]:
            score += 0.5
            reasons.append(f"release decade match (+0.5)")

        if prefs.get("popularity") is not None and popularity is not None:
            gap = abs(popularity - prefs["popularity"]) / 100.0
            pts = max(0.0, 0.5 * (1 - gap))
            if pts > 0:
                score += pts
                reasons.append(f"popularity closeness (+{pts:.2f})")

        if prefs.get("language") and language == prefs["language"]:
            score += 0.5
            reasons.append("language match (+0.5)")

        if prefs.get("avoid_explicit") and is_explicit:
            score -= 1.0
            reasons.append("explicit content penalty (-1.0)")

        return round(score, 2), reasons


class BalancedStrategy(ScoringStrategy):
    """The original Algorithm Recipe: genre and mood each count, energy is
    a meaningful but secondary factor. This is the default mode."""
    name = "balanced"
    GENRE_WEIGHT = 2.0
    MOOD_WEIGHT = 1.0
    ENERGY_MAX = 1.5


class GenreFirstStrategy(ScoringStrategy):
    """Genre dominates the ranking above everything else."""
    name = "genre_first"
    GENRE_WEIGHT = 3.0
    MOOD_WEIGHT = 1.0
    ENERGY_MAX = 1.0


class MoodFirstStrategy(ScoringStrategy):
    """Mood dominates the ranking above everything else."""
    name = "mood_first"
    GENRE_WEIGHT = 1.0
    MOOD_WEIGHT = 3.0
    ENERGY_MAX = 1.0


class EnergyFocusedStrategy(ScoringStrategy):
    """Energy closeness dominates the ranking above everything else."""
    name = "energy_focused"
    GENRE_WEIGHT = 1.0
    MOOD_WEIGHT = 1.0
    ENERGY_MAX = 3.0


STRATEGIES: Dict[str, ScoringStrategy] = {
    "balanced": BalancedStrategy(),
    "genre_first": GenreFirstStrategy(),
    "mood_first": MoodFirstStrategy(),
    "energy_focused": EnergyFocusedStrategy(),
}

DEFAULT_STRATEGY = STRATEGIES["balanced"]


# ---------------------------------------------------------------------------
# Challenge 3: diversity / artist-repetition penalty.
#
# After every song has a score, we build the top-k list greedily: each time
# we're about to pick the next song, any artist already chosen gets a
# per-repeat penalty subtracted from their *remaining* candidates' scores.
# This doesn't change score_song's own output (so explanations stay
# accurate to the *base* score) -- it only affects final ordering/selection.
# ---------------------------------------------------------------------------

def _apply_diversity_penalty(scored_entries, k: int, penalty: float = 1.5):
    """scored_entries: list of (song, score, reasons). Returns up to k entries,
    greedily selected while discouraging repeated artists."""
    remaining = list(scored_entries)
    chosen = []
    artist_counts: Dict[str, int] = {}

    while remaining and len(chosen) < k:
        def effective_score(entry):
            artist = _field(entry[0], "artist")
            repeats = artist_counts.get(artist, 0)
            return entry[1] - repeats * penalty

        remaining.sort(key=effective_score, reverse=True)
        best = remaining.pop(0)
        chosen.append(best)
        artist = _field(best[0], "artist")
        artist_counts[artist] = artist_counts.get(artist, 0) + 1

    return chosen


# ---------------------------------------------------------------------------
# Functional API (used by src/main.py)
# ---------------------------------------------------------------------------

def load_songs(csv_path: str = "data/songs.csv") -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dicts, converting numeric
    fields to floats/ints and is_explicit to a real bool.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["id"] = int(row["id"])
            row["energy"] = float(row["energy"])
            row["tempo_bpm"] = float(row["tempo_bpm"])
            row["valence"] = float(row["valence"])
            row["danceability"] = float(row["danceability"])
            row["acousticness"] = float(row["acousticness"])
            row["popularity"] = float(row.get("popularity", 50) or 50)
            row["release_decade"] = row.get("release_decade", "2020s")
            row["mood_tags"] = row.get("mood_tags", "")
            row["is_explicit"] = str(row.get("is_explicit", "False")).strip().lower() == "true"
            row["language"] = row.get("language", "english")
            songs.append(row)
    return songs


def score_song(
    user_prefs: Union[Dict, UserProfile],
    song: Union[Dict, Song],
    mode: str = "balanced",
) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences using the Algorithm Recipe
    for the given `mode` ("balanced", "genre_first", "mood_first", or
    "energy_focused"). Required by recommend_songs() and src/main.py.
    Returns (score, reasons).
    """
    strategy = STRATEGIES.get(mode, DEFAULT_STRATEGY)
    return strategy.score(user_prefs, song)


def recommend_songs(
    user_prefs: Union[Dict, UserProfile],
    songs: List[Union[Dict, Song]],
    k: int = 5,
    mode: str = "balanced",
    diversity_penalty: bool = False,
) -> List[Tuple[Union[Dict, Song], float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py.

    Scores every song with the chosen strategy `mode`, optionally applies
    the Challenge 3 artist-diversity penalty while selecting the top k, and
    returns (song, score, explanation) tuples where explanation is a single
    human-readable string.
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song, mode=mode)
        explanation = "; ".join(reasons) if reasons else "No strong matches found."
        scored.append((song, score, explanation))

    if diversity_penalty:
        ranked = _apply_diversity_penalty(scored, k)
    else:
        ranked = sorted(scored, key=lambda entry: entry[1], reverse=True)[:k]

    return ranked


# ---------------------------------------------------------------------------
# OOP API (required by tests/test_recommender.py)
# ---------------------------------------------------------------------------

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song], strategy: Optional[ScoringStrategy] = None):
        self.songs = songs
        self.strategy = strategy or DEFAULT_STRATEGY

    def recommend(self, user: UserProfile, k: int = 5, diversity_penalty: bool = False) -> List[Song]:
        """Score every song against `user` and return the top k Song objects."""
        scored = []
        for song in self.songs:
            score, reasons = self.strategy.score(user, song)
            explanation = "; ".join(reasons) if reasons else "No strong matches found."
            scored.append((song, score, explanation))

        if diversity_penalty:
            ranked = _apply_diversity_penalty(scored, k)
        else:
            ranked = sorted(scored, key=lambda entry: entry[1], reverse=True)[:k]

        return [song for song, _, _ in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a plain-English explanation of why `song` scored the way it did."""
        _, reasons = self.strategy.score(user, song)
        if not reasons:
            return "This song didn't strongly match your genre, mood, or energy preferences."
        return "; ".join(reasons)
