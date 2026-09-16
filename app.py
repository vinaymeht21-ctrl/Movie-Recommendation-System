
from pathlib import Path
import os
import pickle

import numpy as np
import requests
from flask import Flask, render_template, request, jsonify

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"

app = Flask(__name__)

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()


def load_pickle(filename):
    path = MODEL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {filename}. Run build_model.py first so the model files are created in {MODEL_DIR}."
        )
    with path.open("rb") as f:
        return pickle.load(f)


try:
    movies = load_pickle("movie_list_dict.pkl")
    similarity = np.asarray(load_pickle("similarity.pkl"), dtype=np.float32)

    # Normalize model data because some versions of the CSV/pickle can contain
    # non-string title values (e.g. numeric/NaN values).
    titles = [str(x).strip() for x in movies["title"]]
    movie_ids = list(movies["movie_id"])

    if len(titles) != len(movie_ids):
        raise ValueError(
            f"Model data mismatch: {len(titles)} titles but {len(movie_ids)} movie IDs."
        )

    if similarity.ndim != 2 or similarity.shape[0] != len(titles):
        raise ValueError(
            "Model mismatch: similarity matrix has shape "
            f"{similarity.shape}, but the movie list contains {len(titles)} movies. "
            "Regenerate both pickle files together with build_model.py."
        )

except Exception as exc:
    movies = None
    similarity = None
    titles = []
    movie_ids = []
    MODEL_ERROR = str(exc)
else:
    MODEL_ERROR = None


def fetch_poster(movie_id):
    # Don't call TMDb when no key is configured; recommendations still work.
    if not TMDB_API_KEY:
        return "/static/no-poster.svg"

    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": TMDB_API_KEY, "language": "en-US"}

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        poster_path = data.get("poster_path")

        if poster_path:
            return f"https://image.tmdb.org/t/p/w500{poster_path}"

    except requests.RequestException as exc:
        app.logger.warning("TMDb request failed for movie %s: %s", movie_id, exc)
    except ValueError as exc:
        app.logger.warning("TMDb returned invalid JSON for movie %s: %s", movie_id, exc)

    return "/static/no-poster.svg"


def recommend(movie):
    if MODEL_ERROR:
        raise RuntimeError(MODEL_ERROR)

    query = str(movie).strip()
    if not query:
        return []

    lowered = query.casefold()

    # 1) Exact match, case-insensitive.
    matches = [
        i for i, title in enumerate(titles)
        if str(title).strip().casefold() == lowered
    ]

    # 2) Substring match so inputs such as "batman" can resolve to
    #    "Batman Begins" even when the exact title is not selected.
    if not matches:
        matches = [
            i for i, title in enumerate(titles)
            if lowered in str(title).strip().casefold()
        ]

    if not matches:
        # 3) Token-overlap fallback for small typos / partial words.
        query_tokens = set(lowered.split())
        scored = []
        for i, title in enumerate(titles):
            title_text = str(title).strip().casefold()
            title_tokens = set(title_text.split())
            overlap = len(query_tokens & title_tokens)
            if overlap:
                scored.append((overlap, -abs(len(title_text) - len(lowered)), i))

        if scored:
            scored.sort(reverse=True)
            matches = [scored[0][2]]

    if not matches:
        return []

    idx = matches[0]
    distances = similarity[idx]

    ranked = sorted(
        enumerate(distances),
        key=lambda x: float(x[1]),
        reverse=True
    )

    results = []
    for i, _score in ranked[1:6]:
        results.append({
            "title": titles[i],
            "poster": fetch_poster(movie_ids[i]),
        })

    return results


@app.route("/")
def home():
    if MODEL_ERROR:
        # Keep the page accessible so the error is visible in the browser.
        all_titles = []
    else:
        all_titles = sorted(titles)

    return render_template("index.html", movie_list=all_titles)


@app.route("/recommend", methods=["POST"])
def get_recommendations():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON."}), 415

        data = request.get_json(silent=True) or {}
        movie_name = str(data.get("movie", "")).strip()

        if not movie_name:
            return jsonify({"error": "Please enter a movie name."}), 400

        return jsonify(recommend(movie_name))

    except Exception as exc:
        app.logger.exception("Recommendation failed")
        return jsonify({"error": str(exc)}), 500


@app.route("/health")
def health():
    return jsonify({
        "ok": MODEL_ERROR is None,
        "movies": len(titles),
        "similarity_shape": list(similarity.shape) if similarity is not None else None,
        "model_error": MODEL_ERROR,
    })


@app.route("/autocomplete")
def autocomplete():
    if MODEL_ERROR:
        return jsonify({"error": MODEL_ERROR}), 500

    query = request.args.get("q", "").strip().casefold()

    if not query:
        return jsonify([])

    matches = [title for title in titles if query in title.casefold()][:10]
    return jsonify(matches)


if __name__ == "__main__":
    app.run(debug=True)
