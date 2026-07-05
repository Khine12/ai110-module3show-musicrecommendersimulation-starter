"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

Uses the functions implemented in recommender.py:
- load_songs
- score_song
- recommend_songs

Stretch features demoed here:
- Challenge 2: switch ranking modes ("balanced", "genre_first", "mood_first",
  "energy_focused") via the MODE constant or the --mode CLI flag.
- Challenge 4: results are displayed as a formatted table (via `tabulate`)
  that includes the score and the "reasons" explanation for each song.
"""

import sys
from tabulate import tabulate

from src.recommender import load_songs, recommend_songs, STRATEGIES


def print_recommendations(profile_name: str, user_prefs: dict, recommendations, mode: str) -> None:
    print(f"\n=== {profile_name} [mode: {mode}] ===")
    print(f"Preferences: {user_prefs}")

    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append([rank, song["title"], song["artist"], f"{score:.2f}", explanation])

    print(tabulate(
        rows,
        headers=["#", "Title", "Artist", "Score", "Reasons"],
        tablefmt="github",
    ))


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Allow `python -m src.main --mode genre_first` to override the default mode
    mode = "balanced"
    if "--mode" in sys.argv:
        idx = sys.argv.index("--mode")
        if idx + 1 < len(sys.argv):
            mode = sys.argv[idx + 1]
    if mode not in STRATEGIES:
        print(f"Unknown mode '{mode}', falling back to 'balanced'. Valid modes: {list(STRATEGIES)}")
        mode = "balanced"

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    recommendations = recommend_songs(user_prefs, songs, k=5, mode=mode)
    print_recommendations("Default (Pop/Happy)", user_prefs, recommendations, mode)

    # A few extra profiles to stress-test the scoring logic (Phase 4)
    extra_profiles = {
        "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.35},
        "Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.9},
        "Acoustic Fan": {"genre": "jazz", "mood": "relaxed", "energy": 0.3, "likes_acoustic": True},
        # Adversarial: conflicting preferences (high energy target + a mood
        # that's almost always low-energy in this dataset)
        "Adversarial (High-Energy + Sad)": {"genre": "lofi", "mood": "sad", "energy": 0.9},
    }
    for name, prefs in extra_profiles.items():
        recs = recommend_songs(prefs, songs, k=5, mode=mode)
        print_recommendations(name, prefs, recs, mode)

    # Challenge 2 demo: same profile, all four ranking modes side by side
    print("\n\n=== Mode comparison for Default (Pop/Happy) ===")
    for mode_name in STRATEGIES:
        recs = recommend_songs(user_prefs, songs, k=3, mode=mode_name)
        print_recommendations("Default (Pop/Happy)", user_prefs, recs, mode_name)

    # Challenge 3 demo: diversity penalty on vs. off for a profile where one
    # artist has multiple strong genre matches (Neon Echo has 3 pop/synthwave
    # songs), so the filter-bubble effect is visible.
    print("\n\n=== Diversity Penalty comparison (Default profile) ===")
    without_penalty = recommend_songs(user_prefs, songs, k=5, mode=mode, diversity_penalty=False)
    with_penalty = recommend_songs(user_prefs, songs, k=5, mode=mode, diversity_penalty=True)
    print_recommendations("Without diversity penalty", user_prefs, without_penalty, mode)
    print_recommendations("With diversity penalty", user_prefs, with_penalty, mode)


if __name__ == "__main__":
    main()
