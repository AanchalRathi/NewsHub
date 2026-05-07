from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests

app = Flask(__name__)
CORS(app)

GNEWS_KEY = "6091fdfb0afb1f1f52fc9dd7307d0267"
MEDIASTACK_KEY = "34a11449acd9be6eac157115bc083e7c"


# ---------- NORMALIZE ARTICLES ----------
def normalize_articles(articles):

    normalized = []

    for a in articles:

        source_name = "Unknown"

        if isinstance(a.get("source"), dict):
            source_name = a.get("source", {}).get("name") or "Unknown"

        elif isinstance(a.get("source"), str):
            source_name = a.get("source")

        normalized.append({

            "title": a.get("title") or "Untitled Article",

            "description": a.get("description") or "",

            "url": a.get("url"),

            "image": a.get("image"),

            "publishedAt":
                a.get("publishedAt")
                or a.get("published_at"),

            "source": source_name
        })

    return normalized


# ---------- FETCH ARTICLES ----------
def fetch_articles(query):

    urls = []

    category_map = {
        "politics": "nation",
        "business": "business",
        "technology": "technology",
        "entertainment": "entertainment"
    }

    # Category feeds
    if query and query.lower() in category_map:

        urls.append(
            f"https://gnews.io/api/v4/top-headlines?"
            f"category={category_map[query.lower()]}"
            f"&lang=en&max=20&token={GNEWS_KEY}"
        )

    # Search feeds
    if query and query != "top":

        urls.append(
            f"https://gnews.io/api/v4/search?"
            f"q={query}&lang=en&max=20&token={GNEWS_KEY}"
        )

        urls.append(
            f"https://gnews.io/api/v4/search?"
            f"q={query} news&lang=en&max=20&token={GNEWS_KEY}"
        )

    # General headlines
    urls.append(
        f"https://gnews.io/api/v4/top-headlines?"
        f"lang=en&max=20&token={GNEWS_KEY}"
    )

    # ---------- TRY GNEWS ----------
    for u in urls:

        print("TRYING:", u)

        try:

            res = requests.get(u)

            data = res.json()

            articles = data.get("articles", [])

            print("FOUND:", len(articles))

            if articles:

                return normalize_articles(articles)

        except Exception as e:

            print("GNEWS ERROR:", e)

    # ---------- MEDIASTACK FALLBACK ----------
    print("GNews failed. Trying Mediastack...")

    try:

        mediastack_url = (
            f"http://api.mediastack.com/v1/news"
            f"?access_key={MEDIASTACK_KEY}"
            f"&languages=en"
            f"&limit=20"
        )

        if query and query != "top":
            mediastack_url += f"&keywords={query}"

        print("TRYING MEDIASTACK:", mediastack_url)

        res = requests.get(mediastack_url)

        data = res.json()

        articles = data.get("data", [])

        print("MEDIASTACK FOUND:", len(articles))

        if articles:

            return normalize_articles(articles)

    except Exception as e:

        print("MEDIASTACK ERROR:", e)

    return []


# ---------- MAIN ROUTE ----------
@app.route("/recommend", methods=["GET"])
def recommend():

    query = request.args.get("q", "").strip().lower()

    profile = request.args.get("profile", "").strip().lower()

    search_term = query if query else profile

    articles = fetch_articles(search_term)

    if not articles:
        return jsonify([])

    # ---------- PURE CATEGORY FEEDS ----------
    if query in [
        "top",
        "politics",
        "business",
        "technology",
        "entertainment"
    ]:

        return jsonify(articles)

    # ---------- NO PROFILE YET ----------
    if not profile:

        return jsonify(articles)

    # ---------- TF-IDF RECOMMENDATION ----------
    texts = [

        (
            ((a.get("title") or "") * 2)
            + " "
            + (a.get("description") or "")
        )

        for a in articles
    ]

    vectorizer = TfidfVectorizer(
        stop_words="english"
    )

    vectors = vectorizer.fit_transform(
        texts + [profile]
    )

    similarity = cosine_similarity(
        vectors[-1],
        vectors[:-1]
    ).flatten()

    ranked_articles = sorted(
        zip(articles, similarity),
        key=lambda x: x[1],
        reverse=True
    )

    ranked_articles = ranked_articles[:15]

    return jsonify([
        article
        for article, _ in ranked_articles
    ])


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)