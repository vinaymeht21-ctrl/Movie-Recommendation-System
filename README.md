# 🎬 CineMatch — Movie Recommendation System

A **content-based movie recommendation system** built with Flask, Scikit-learn, and the TMDB 5000 dataset. Type any movie name and get 5 similar movie recommendations with posters fetched from TMDb.

---

## ✨ Features

- 🔍 **Smart search with autocomplete** — get live suggestions as you type
- 🎯 **Content-based filtering** — recommendations powered by cosine similarity over movie tags (overview, genres, keywords, cast & crew)
- 🖼️ **Movie posters** — fetched live from the TMDb API (with graceful fallback if no API key is set)
- 🛡️ **Robust title matching** — exact, substring, and token-overlap matching so partial names like "batman" still work
- 📱 **Responsive UI** — clean, modern dark-theme interface built with vanilla HTML/CSS/JS
- ⚡ **Fast** — similarity matrix pre-computed once and stored as a pickle file

---

## 🧠 How It Works

1. **Data preparation** (`build_model.py`):
   - Merges `tmdb_5000_movies.csv` and `tmdb_5000_credits.csv` on the movie title
   - Extracts and combines **overview, genres, keywords, top-3 cast, and director** into a single "tags" column
   - Stems words with NLTK's PorterStemmer and removes stop words

2. **Vectorization & similarity**:
   - Converts tags into a bag-of-words matrix using `CountVectorizer` (top 5000 features)
   - Computes a **cosine similarity matrix** between all movie pairs

3. **Serving** (`app.py`):
   - Loads the pre-computed model from the `model/` folder
   - On a recommendation request, finds the queried movie, sorts its similarity row, and returns the top 5 matches
   - Posters are fetched from the TMDb API at request time

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Flask (Python) |
| Machine Learning | Scikit-learn (CountVectorizer, Cosine Similarity) |
| NLP | NLTK (PorterStemmer) |
| Data | Pandas, NumPy |
| Posters | TMDb API via `requests` |
| Frontend | HTML, CSS, Vanilla JavaScript |

---

## 📁 Project Structure

```
Movie-Recommendation-System/
├── app.py                  # Flask web server & recommendation logic
├── build_model.py          # Trains the model and builds the similarity matrix
├── requirements.txt        # Python dependencies
├── tmdb_5000_movies.csv    # TMDB movies dataset
├── tmdb_5000_credits.csv   # TMDB credits dataset
├── model/
│   ├── movie_list_dict.pkl # Serialized movie list (generated)
│   └── similarity.pkl      # Cosine similarity matrix (generated)
├── templates/
│   └── index.html          # Main page
└── static/
    ├── style.css           # UI styling
    ├── script.js           # Frontend logic (fetch, autocomplete)
    └── no-poster.svg       # Fallback poster image
```

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.8+
- The two dataset files placed in the project folder:
  - `tmdb_5000_movies.csv`
  - `tmdb_5000_credits.csv`

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Build the model (run once)

```bash
python build_model.py
```

This generates `model/movie_list_dict.pkl` and `model/similarity.pkl`.

> ⚠️ **Important:** Never mix pickle files from different runs/datasets — always regenerate both together.

### 4. (Optional) Set your TMDb API key

Posters are fetched from TMDb. Without a key, the app still works but uses a fallback image.

**Windows PowerShell:**
```powershell
$env:TMDB_API_KEY="YOUR_API_KEY"
```

**macOS / Linux:**
```bash
export TMDB_API_KEY="YOUR_API_KEY"
```

Get a free key at [themoviedb.org](https://www.themoviedb.org/settings/api).

### 5. Run the app

```bash
python app.py
```

### 6. Open in browser

```
http://127.0.0.1:5000
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Main page with the movie list |
| `POST` | `/recommend` | Body: `{"movie": "Avatar"}` → returns 5 recommendations with posters |
| `GET` | `/autocomplete?q=bat` | Returns up to 10 matching titles |
| `GET` | `/health` | Model status, movie count, and similarity matrix shape |

**Example:**

```bash
curl -X POST http://127.0.0.1:5000/recommend \
  -H "Content-Type: application/json" \
  -d '{"movie": "Avatar"}'
```

```json
[
  {"title": "Guardians of the Galaxy", "poster": "https://image.tmdb.org/..."},
  ...
]
```

---

## ⚙️ How Recommendations Are Matched

When you enter a movie name, the backend tries in order:

1. **Exact match** (case-insensitive)
2. **Substring match** — e.g. `"batman"` → *Batman Begins*
3. **Token-overlap match** — picks the title sharing the most words, favoring similar-length titles

---

## 🐛 Troubleshooting

| Problem | Fix |
|---------|-----|
| `Missing movie_list_dict.pkl` | Run `python build_model.py` first |
| Similarity shape mismatch error | Regenerate both pickle files together |
| No posters showing | Set the `TMDB_API_KEY` environment variable |
| Blank movie dropdown | Make sure both CSVs are present and rebuild the model |

---

## 📌 Future Improvements

- [ ] Hybrid recommendations (collaborative + content-based)
- [ ] Movie detail pages with ratings and overviews
- [ ] Filter by genre, year, or language
- [ ] Deploy to cloud (Render / Railway / AWS)

---

## 📄 Dataset

[TMDB 5000 Movie Dataset](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata) — metadata for ~5,000 movies including genres, keywords, cast, and crew.

## 📜 License

This project is for educational purposes.
