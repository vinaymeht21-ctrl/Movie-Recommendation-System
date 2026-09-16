
from pathlib import Path
import ast
import pickle

import numpy as np
import pandas as pd
from nltk.stem.porter import PorterStemmer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "model"
MODEL_DIR.mkdir(exist_ok=True)


def find_csv(name):
    candidates = [
        BASE_DIR / name,
        BASE_DIR / f"data/{name}",
        Path.cwd() / name,
        Path.cwd() / f"data/{name}",
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Could not find {name}. Put the TMDB CSV files beside build_model.py."
    )


movies = pd.read_csv(find_csv("tmdb_5000_movies.csv"))
credits = pd.read_csv(find_csv("tmdb_5000_credits.csv"))

movies = movies.merge(credits, on="title")
movies = movies[["movie_id", "title", "overview", "genres", "keywords", "cast", "crew"]]
movies.dropna(inplace=True)
movies["title"] = movies["title"].astype(str).str.strip()


def convert(obj):
    return [i["name"] for i in ast.literal_eval(obj)]


movies["genres"] = movies["genres"].apply(convert)
movies["keywords"] = movies["keywords"].apply(convert)


def convert3(obj):
    return [i["name"] for i in ast.literal_eval(obj)[:3]]


movies["cast"] = movies["cast"].apply(convert3)


def fetch_director(obj):
    for i in ast.literal_eval(obj):
        if i["job"] == "Director":
            return [i["name"]]
    return []


movies["crew"] = movies["crew"].apply(fetch_director)
movies["overview"] = movies["overview"].apply(lambda x: x.split())

for col in ["genres", "keywords", "cast", "crew"]:
    movies[col] = movies[col].apply(lambda x: [i.replace(" ", "") for i in x])

movies["tags"] = (
    movies["overview"]
    + movies["genres"]
    + movies["keywords"]
    + movies["cast"]
    + movies["crew"]
)

new_df = movies[["movie_id", "title", "tags"]].copy()
new_df["tags"] = new_df["tags"].apply(lambda x: " ".join(x))

ps = PorterStemmer()
new_df["tags"] = new_df["tags"].apply(
    lambda text: " ".join(ps.stem(word) for word in text.split())
)

cv = CountVectorizer(max_features=5000, stop_words="english")
vectors = cv.fit_transform(new_df["tags"]).toarray()

similarity = cosine_similarity(vectors).astype(np.float32)

with (MODEL_DIR / "movie_list_dict.pkl").open("wb") as f:
    pickle.dump(new_df.to_dict(orient='list'), f)

with (MODEL_DIR / "similarity.pkl").open("wb") as f:
    pickle.dump(similarity, f)

print("Model created successfully.")
print("Movies:", len(new_df))
print("Similarity shape:", similarity.shape)
print("Saved to:", MODEL_DIR)
