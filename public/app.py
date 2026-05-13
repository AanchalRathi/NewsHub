from flask import Flask, request, jsonify
from flask_cors import CORS

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from dotenv import load_dotenv

from pymongo import MongoClient

import firebase_admin

from firebase_admin import credentials, auth

import requests
import os


app = Flask(__name__)

CORS(app)

load_dotenv()


# MONGODB 

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)

db = client["youth_news_hub"]

users_collection = db["users"]


# FIREBASE ADMIN 

cred = credentials.Certificate(
    "public/firebase_key.json"
)

firebase_admin.initialize_app(cred)
GNEWS_KEY = os.getenv("GNEWS_KEY")
MEDIASTACK_KEY = os.getenv("MEDIASTACK_KEY")

cache = {}

MAX_ARTICLES = 15

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

    # category feeds
    if query and query.lower() in category_map:

        urls.append(
            f"https://gnews.io/api/v4/top-headlines?"
            f"category={category_map[query.lower()]}"
            f"&lang=en&max=20&token={GNEWS_KEY}"
        )

    # search feeds
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

    #GNEWS API
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

    # API fallback 
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

            normalized = normalize_articles(articles)

            cache[query] = normalized

            return normalized

    except Exception as e:

        print("MEDIASTACK ERROR:", e)

    return []


# MAIN
@app.route("/recommend", methods=["GET"])
def recommend():

    query = request.args.get("q", "").strip().lower()

    profile = request.args.get("profile", "").strip().lower()

    #validate user input

    query = query[:100]
    profile = profile[:500]

    query = "".join(
        c for c in query
        if c.isalnum() or c.isspace()
    )

    profile = "".join(
        c for c in profile
        if c.isalnum() or c.isspace()
    )

    search_term = query if query else profile

    articles = fetch_articles(search_term)

    if not articles:
        return jsonify([])

    # category feeds
    if query in [
        "top",
        "politics",
        "business",
        "technology",
        "entertainment"
    ]:

        return jsonify(articles)

    #no profile 
    if not profile:

        return jsonify(articles)

    #tf-idf
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

    ranked_articles = ranked_articles[:MAX_ARTICLES]

    return jsonify([
        article
        for article, _ in ranked_articles
    ])

@app.route("/verify-user", methods=["POST"])
def verify_user():

    try:

        data = request.get_json()

        token = data.get("token")

        decoded_token = auth.verify_id_token(token)

        uid = decoded_token["uid"]

        email = decoded_token.get("email")

        name = decoded_token.get("name")

        existing_user = users_collection.find_one({
            "uid": uid
        })

        if not existing_user:

            users_collection.insert_one({

                "uid": uid,

                "email": email,

                "name": name,

                "profile": ""

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

        return jsonify({

            "success": False,

            "error": str(e)

        }), 401
# run
if __name__ == "__main__":
    app.run(debug=True,use_reloader=False)