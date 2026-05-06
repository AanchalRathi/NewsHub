from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import requests

app = Flask(__name__)
CORS(app)

GNEWS_KEY = "6091fdfb0afb1f1f52fc9dd7307d0267"


# ---------- FETCH ARTICLES ----------
def fetch_articles(query):
    urls = []
    category_map = {
        "politics": "nation",
        "business": "business",
        "technology": "technology",
        "entertainment": "entertainment"
    }

    if query.lower() in category_map:
        urls.append(
            f"https://gnews.io/api/v4/top-headlines?category={category_map[query.lower()]}&lang=en&max=20&token={GNEWS_KEY}"
        )
    if query:
        urls.append(f"https://gnews.io/api/v4/search?q={query}&lang=en&max=20&token={GNEWS_KEY}")
        urls.append(f"https://gnews.io/api/v4/search?q={query} news&lang=en&max=20&token={GNEWS_KEY}")

    urls.append(f"https://gnews.io/api/v4/top-headlines?lang=en&max=20&token={GNEWS_KEY}")

    for u in urls:
        print("TRYING:", u)

        res = requests.get(u)
        data = res.json()
        articles = data.get("articles", [])

        print("FOUND:", len(articles))

        if articles:
            return articles

    return []


# ---------- MAIN ROUTE ----------
@app.route("/recommend", methods=["GET"])
def recommend():
    query = request.args.get("q", "")
    profile = request.args.get("profile", "")

    articles = fetch_articles(query)

    if not articles:
        return jsonify([])

    user_input = (query + " " + profile).strip().lower()

    # ✅ If no user interaction → return normal news
    if not user_input:
        return jsonify([{
            "title": a["title"],
            "description": a.get("description"),
            "url": a["url"],
            "image": a.get("image"),
            "source": a["source"]["name"],
            "publishedAt": a.get("publishedAt"),
        } for a in articles])

    texts = [
        (a["title"] * 2) + " " + (a.get("description") or "")
        for a in articles
    ]

    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform(texts + [user_input])

    similarity = cosine_similarity(vectors[-1], vectors[:-1]).flatten()

    ranked_articles = sorted(
        zip(articles, similarity),
        key=lambda x: x[1],
        reverse=True
    )

    # keep enough articles for scrolling
    ranked_articles = ranked_articles[:15]

    return jsonify([{
        "title": a["title"],
        "description": a.get("description"),
        "url": a["url"],
        "image": a.get("image"),
        "source": a["source"]["name"],
        "publishedAt": a.get("publishedAt"),
    } for a, _ in ranked_articles])


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)