from flask import Flask, request, jsonify
from flask_cors import CORS

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from dotenv import load_dotenv
from pymongo import MongoClient

import firebase_admin
from firebase_admin import credentials, auth

import json
import requests
import os
import time
import math
from collections import Counter

app = Flask(__name__)
CORS(app)
load_dotenv()

# ---------- MONGODB ----------
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["youth_news_hub"]
users_collection = db["users"]

# ---------- FIREBASE ADMIN ----------
firebase_env = os.getenv("FIREBASE_CREDENTIALS")

if firebase_env:
    firebase_credentials = json.loads(firebase_env)
    cred = credentials.Certificate(firebase_credentials)
else:
    cred = credentials.Certificate("public/firebase_key.json")

firebase_admin.initialize_app(cred)

GNEWS_KEY = os.getenv("GNEWS_KEY")
MEDIASTACK_KEY = os.getenv("MEDIASTACK_KEY")

cache = {}
MAX_ARTICLES = 15
MAX_CLICKS = 50  # keep only last 50 clicks per user


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
            "publishedAt": a.get("publishedAt") or a.get("published_at"),
            "source": source_name
        })
    return normalized


# ---------- FETCH ARTICLES ----------
def fetch_articles(query):
    if query in cache:
        print("CACHE HIT:", query)
        return cache[query]

    urls = []
    category_map = {
        "politics": "nation",
        "business": "business",
        "technology": "technology",
        "entertainment": "entertainment"
    }

    if query and query.lower() in category_map:
        urls.append(
            f"https://gnews.io/api/v4/top-headlines?"
            f"category={category_map[query.lower()]}"
            f"&lang=en&max=20&token={GNEWS_KEY}"
        )

    if query and query != "top":
        urls.append(
            f"https://gnews.io/api/v4/search?"
            f"q={query}&lang=en&max=20&token={GNEWS_KEY}"
        )
        urls.append(
            f"https://gnews.io/api/v4/search?"
            f"q={query} news&lang=en&max=20&token={GNEWS_KEY}"
        )

    urls.append(
        f"https://gnews.io/api/v4/top-headlines?"
        f"lang=en&max=20&token={GNEWS_KEY}"
    )

    for u in urls:
        print("TRYING:", u)
        try:
            res = requests.get(u)
            data = res.json()
            articles = data.get("articles", [])
            print("FOUND:", len(articles))
            if articles:
                normalized = normalize_articles(articles)
                cache[query] = normalized
                return normalized
        except Exception as e:
            print("GNEWS ERROR:", e)

    print("GNews failed. Trying Mediastack...")
    try:
        mediastack_url = (
            f"http://api.mediastack.com/v1/news"
            f"?access_key={MEDIASTACK_KEY}"
            f"&languages=en&limit=20"
        )
        if query and query != "top":
            mediastack_url += f"&keywords={query}"

        res = requests.get(mediastack_url)
        data = res.json()
        articles = data.get("data", [])
        print("MEDIASTACK FOUND:", len(articles))
        if articles:
            normalized = normalize_articles(articles)
            cache[query] = normalized
            return normalized
    except Exception as e:
        print("MEDIASTACK ERROR:", e)

    return []


# ---------- BUILD WEIGHTED PROFILE ----------
def build_weighted_profile(clicks):
    """
    Builds a weighted profile string from click history.

    Three layers of weighting:
    1. Time decay  — recent clicks count more than old ones
    2. Category boost — most clicked category gets extra weight
    3. Keyword frequency — words appearing across multiple clicks get boosted

    Returns a single weighted profile string for TF-IDF.
    """

    if not clicks:
        return ""

    now = time.time()

    # --- Layer 1: Time decay ---
    # Each click gets a weight based on how recent it is.
    # Weight = e^(-0.01 * hours_since_click)
    # A click from 1 hour ago → weight ~0.99
    # A click from 24 hours ago → weight ~0.79
    # A click from 7 days ago → weight ~0.18
    weighted_texts = []

    for click in clicks:
        timestamp = click.get("timestamp", now)
        age_hours = (now - timestamp) / 3600
        decay_weight = math.exp(-0.01 * age_hours)

        # repeat the text proportional to weight (1–10 times)
        repeat = max(1, int(decay_weight * 10))
        text = click.get("text", "")
        weighted_texts.append((text, repeat, click.get("category", "")))

    # --- Layer 2: Category boost ---
    # Find the most clicked category and boost it by 3x
    categories = [c for _, _, c in weighted_texts if c]
    category_counts = Counter(categories)
    top_category = category_counts.most_common(1)[0][0] if category_counts else None

    # --- Layer 3: Build final profile string ---
    profile_parts = []

    for text, repeat, category in weighted_texts:
        # base repetition from time decay
        profile_parts.append(" ".join([text] * repeat))

        # category boost: if this click matches top category, add extra weight
        if top_category and category == top_category:
            profile_parts.append(" ".join([text] * 3))

    return " ".join(profile_parts)


# ---------- HYBRID SCORE ----------
def hybrid_score(tfidf_score, article, clicks):
    """
    Combines TF-IDF cosine similarity with category boost
    to produce a final ranking score.

    Final score = 70% TF-IDF + 30% category match bonus
    """
    if not clicks:
        return tfidf_score

    # count category preferences from click history
    categories = [c.get("category", "") for c in clicks if c.get("category")]
    category_counts = Counter(categories)
    total_clicks = len(clicks)

    article_category = article.get("category", "").lower()
    category_freq = category_counts.get(article_category, 0)

    # category bonus: how often user clicked this category (0 to 1)
    category_bonus = category_freq / total_clicks if total_clicks > 0 else 0

    # weighted combination
    final_score = (0.7 * tfidf_score) + (0.3 * category_bonus)
    return final_score


# ---------- SAVE CLICK ----------
@app.route("/save-click", methods=["POST"])
def save_click():
    """
    Saves a structured click to MongoDB.
    Called every time a user clicks an article.

    Expected body:
    {
        "uid": "firebase_uid",
        "text": "article title + description",
        "category": "technology",
        "timestamp": 1716000000
    }
    """
    try:
        data = request.get_json()
        uid = data.get("uid")
        text = data.get("text", "")[:300]   # limit text length
        category = data.get("category", "")
        timestamp = data.get("timestamp", time.time())

        if not uid:
            return jsonify({"success": False, "error": "uid required"}), 400

        click_obj = {
            "text": text,
            "category": category,
            "timestamp": timestamp
        }

        # push new click, keep only last MAX_CLICKS clicks
        users_collection.update_one(
            {"uid": uid},
            {
                "$push": {
                    "clicks": {
                        "$each": [click_obj],
                        "$slice": -MAX_CLICKS   # keep last 50
                    }
                }
            }
        )

        print(f"CLICK SAVED for uid={uid} category={category}")
        return jsonify({"success": True})

    except Exception as e:
        print("SAVE CLICK ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- GET PROFILE ----------
@app.route("/get-profile", methods=["GET"])
def get_profile():
    """
    Returns the click history for a user.
    Called on page load so frontend can pass
    profile to recommendation engine.
    """
    try:
        uid = request.args.get("uid")
        if not uid:
            return jsonify({"clicks": []})

        user = users_collection.find_one({"uid": uid})
        if not user:
            return jsonify({"clicks": []})

        clicks = user.get("clicks", [])
        return jsonify({"clicks": clicks})

    except Exception as e:
        print("GET PROFILE ERROR:", e)
        return jsonify({"clicks": []}), 500


# ---------- RECOMMEND ----------
@app.route("/recommend", methods=["GET"])
def recommend():
    query = request.args.get("q", "").strip().lower()
    uid = request.args.get("uid", "").strip()

    # sanitize inputs
    query = query[:100]
    query = "".join(c for c in query if c.isalnum() or c.isspace())

    search_term = query if query else "top"
    articles = fetch_articles(search_term)

    if not articles:
        return jsonify([])

    # pure category/top feeds — no ranking needed
    if query in ["top", "politics", "business", "technology", "entertainment"]:
        return jsonify(articles)

    # fetch user click history from MongoDB
    clicks = []
    if uid:
        try:
            user = users_collection.find_one({"uid": uid})
            if user:
                clicks = user.get("clicks", [])
        except Exception as e:
            print("MONGO FETCH ERROR:", e)

    # no click history — return articles as-is
    if not clicks:
        return jsonify(articles)

    # ---------- BUILD WEIGHTED PROFILE ----------
    profile = build_weighted_profile(clicks)

    if not profile.strip():
        return jsonify(articles)

    # ---------- TF-IDF ----------
    texts = [
        ((a.get("title") or "") * 2) + " " + (a.get("description") or "")
        for a in articles
    ]

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(texts + [profile])

    tfidf_scores = cosine_similarity(
        vectors[-1], vectors[:-1]
    ).flatten()

    # ---------- HYBRID SCORING ----------
    final_scores = [
        hybrid_score(tfidf_scores[i], articles[i], clicks)
        for i in range(len(articles))
    ]

    ranked_articles = sorted(
        zip(articles, final_scores),
        key=lambda x: x[1],
        reverse=True
    )[:MAX_ARTICLES]

    return jsonify([article for article, _ in ranked_articles])


#  VERIFY USER 
@app.route("/verify-user", methods=["POST"])
def verify_user():
    try:
        data = request.get_json()
        token = data.get("token")
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token["uid"]
        email = decoded_token.get("email")
        name = decoded_token.get("name")

        existing_user = users_collection.find_one({"uid": uid})

        if not existing_user:
            users_collection.insert_one({
                "uid": uid,
                "email": email,
                "name": name,
                "clicks": []      
            })
            print("NEW USER CREATED")
        else:
            print("USER ALREADY EXISTS")

        return jsonify({
            "success": True,
            "uid": uid,
            "email": email,
            "name": name
        })

    except Exception as e:
        print("VERIFY ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 401


# UPDATE PROFILE 
@app.route("/update-profile", methods=["POST"])
def update_profile():
    try:
        data = request.get_json()
        uid = data.get("uid")
        profile = data.get("profile")

        users_collection.update_one(
            {"uid": uid},
            {"$set": {"profile": profile}}
        )
        return jsonify({"success": True})

    except Exception as e:
        print("PROFILE UPDATE ERROR:", e)
        return jsonify({"success": False}), 500


# ---------- HOME ----------
@app.route("/")
def home():
    return {"message": "Youth News Hub Backend Running"}


# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)