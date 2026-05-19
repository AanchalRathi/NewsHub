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
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=False)
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
MAX_CLICKS = 50


# ---------- CATEGORY PROFILES ----------
# Instead of keyword lists, each category is described
# as a rich natural language paragraph.
# TF-IDF measures similarity between article text and
# these descriptions — no hardcoded keywords needed.
CATEGORY_PROFILES = {
    "sports": """
        cricket ipl football tennis basketball match tournament player league
        score wicket goal champion sport athlete stadium team batting bowling
        fifa world cup olympic medal coach squad fixture result innings over
        run boundary six four pitch umpire referee penalty shootout
        formula one racing nascar golf swimming athletics marathon relay
        virat kohli rohit sharma dhoni sachin tendulkar messi ronaldo federer
        nba nfl nhl mlb premier league bundesliga la liga serie a
        sunrisers hyderabad chennai super kings mumbai indians rajasthan royals
        playoff semifinal final knockout qualifier points table standings
    """,

    "technology": """
        artificial intelligence machine learning deep learning neural network
        software hardware startup tech apple google microsoft amazon meta
        algorithm robot automation cyber security data science cloud computing
        smartphone iphone android app developer programming python javascript
        semiconductor chip processor gpu cpu server database api blockchain
        elon musk sam altman openai chatgpt gemini claude llm model
        electric vehicle tesla self driving autonomous vehicle drone satellite
        space exploration nasa isro spacex launch orbit moon mars
        cybersecurity hacking privacy data breach encryption firewall
        venture capital funding series raise valuation unicorn ipo nasdaq
    """,

    "business": """
        economy market stock finance gdp company investor revenue profit trade
        bank inflation interest rate monetary fiscal policy budget tax
        merger acquisition deal contract supply chain import export
        unemployment jobs hiring layoff recession growth quarterly earnings
        wall street federal reserve rbi sebi sensex nifty dow jones nasdaq
        commodity oil gold silver crude futures forex currency exchange rate
        real estate property mortgage loan debt equity dividend shareholder
        entrepreneur business model revenue startup scale profit margin
        retail ecommerce consumer spending demand supply manufacturing industry
    """,

    "politics": """
        election government minister parliament policy congress bjp president
        senate democracy vote political party candidate campaign rally debate
        prime minister cabinet legislation bill law constitution amendment
        foreign policy diplomacy treaty sanctions embargo war conflict ceasefire
        united nations security council nato g7 g20 summit bilateral
        corruption scandal protest movement civil rights judiciary supreme court
        modi rahul gandhi kejriwal mamata shah yogi nitish regional party
        republican democrat liberal conservative left right wing coalition
        referendum impeachment speaker opposition ruling party manifesto
    """,

    "entertainment": """
        film movie music celebrity actor actress festival concert award
        bollywood hollywood director producer screenplay box office collection
        album song singer rapper pop rock classical jazz hip hop
        netflix amazon prime disney streaming ott series season episode
        cannes oscars grammy bafta golden globe emmy award nomination
        celebrity gossip relationship dating breakup marriage divorce rumour
        fashion designer brand model runway show vogue magazine
        gaming video game console playstation xbox nintendo esports streamer
        book author novel bestseller literature poetry theatre drama stage
        comedy standup show host talk interview podcast influencer viral
    """,

    "health": """
        health medical hospital disease virus vaccine doctor cancer treatment
        wellness mental health therapy medication surgery clinical trial
        pandemic epidemic outbreak infection symptoms diagnosis prescription
        nutrition diet exercise fitness gym yoga meditation stress anxiety
        heart disease diabetes obesity blood pressure cholesterol
        research study pharmaceutical drug approval fda who cdc
        pregnancy childbirth maternal infant pediatric geriatric
        public health policy insurance healthcare system reform
        covid influenza respiratory immune system antibody protein
    """,

    "science": """
        research study discovery experiment laboratory scientist professor
        physics chemistry biology astronomy geology climate environment
        climate change global warming carbon emission renewable energy
        solar wind nuclear fossil fuel sustainability green energy
        space universe galaxy planet star black hole telescope observation
        dna gene genome mutation evolution species biodiversity extinction
        ocean marine ecosystem forest deforestation wildlife conservation
        quantum computing particle accelerator cern breakthrough innovation
        mathematics statistics model simulation data analysis
    """,

    "world": """
        international global foreign country nation border conflict war peace
        ukraine russia israel palestine gaza ceasefire humanitarian crisis
        refugee migration asylum border crossing displaced population
        united states america europe asia africa middle east latin america
        china india brazil indonesia pakistan bangladesh sri lanka
        sanctions embargo trade war tariff import export bilateral
        natural disaster earthquake flood hurricane tsunami drought famine
        united nations nato g20 imf world bank aid development
        human rights freedom press democracy autocracy regime coup protest
    """
}

# pre-compute category vectors once at startup
# this avoids recomputing on every request
_category_vectorizer = None
_category_vectors = None
_category_names = list(CATEGORY_PROFILES.keys())

def get_category_vectors():
    """
    Lazily initializes and caches TF-IDF vectors
    for all category profiles.
    Called once on first use.
    """
    global _category_vectorizer, _category_vectors

    if _category_vectorizer is not None:
        return _category_vectorizer, _category_vectors

    _category_vectorizer = TfidfVectorizer(stop_words="english")
    _category_vectors = _category_vectorizer.fit_transform(
        list(CATEGORY_PROFILES.values())
    )

    print("CATEGORY VECTORS INITIALIZED")
    return _category_vectorizer, _category_vectors


def detect_category(text):
    """
    Detects category of an article using TF-IDF cosine similarity.
    Compares article text against rich category profile descriptions.
    Returns the best matching category name.
    No hardcoded keyword lists — works for any topic.
    """
    if not text or not text.strip():
        return "general"

    try:
        vectorizer, cat_vectors = get_category_vectors()

        # transform article text using existing vocabulary
        text_vector = vectorizer.transform([text])

        # compute similarity against all category profiles
        similarities = cosine_similarity(
            text_vector, cat_vectors
        ).flatten()

        best_idx = similarities.argmax()
        best_score = similarities[best_idx]

        # if similarity is too low, return general
        if best_score < 0.05:
            return "general"

        detected = _category_names[best_idx]
        print(f"DETECTED CATEGORY: {detected} (score={best_score:.3f})")
        return detected

    except Exception as e:
        print("CATEGORY DETECTION ERROR:", e)
        return "general"


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
    Builds a weighted profile string from structured click history.

    Layer 1 — Time decay: recent clicks weighted higher
    Layer 2 — Category boost: most read category gets 3x weight
    Layer 3 — Combined profile string fed into TF-IDF
    """
    if not clicks:
        return ""

    now = time.time()
    weighted_texts = []

    for click in clicks:
        timestamp = click.get("timestamp", now)
        age_hours = (now - timestamp) / 3600
        # decay: click from 1hr ago = weight 0.99, 7 days ago = 0.18
        decay_weight = math.exp(-0.01 * age_hours)
        repeat = max(1, int(decay_weight * 10))
        text = click.get("text", "")
        category = click.get("category", "")
        weighted_texts.append((text, repeat, category))

    # find most clicked category for boost
    categories = [c for _, _, c in weighted_texts if c]
    category_counts = Counter(categories)
    top_category = category_counts.most_common(1)[0][0] if category_counts else None

    profile_parts = []
    for text, repeat, category in weighted_texts:
        profile_parts.append(" ".join([text] * repeat))
        # boost top category clicks by repeating 3 more times
        if top_category and category == top_category:
            profile_parts.append(" ".join([text] * 3))

    return " ".join(profile_parts)


# ---------- HYBRID SCORE ----------
def hybrid_score(tfidf_score, article, clicks):
    """
    Final score = 70% TF-IDF similarity + 30% category preference bonus
    """
    if not clicks:
        return tfidf_score

    categories = [c.get("category", "") for c in clicks if c.get("category")]
    category_counts = Counter(categories)
    total_clicks = len(clicks)

    article_text = (
        (article.get("title") or "") + " " +
        (article.get("description") or "")
    )
    article_category = detect_category(article_text)
    category_freq = category_counts.get(article_category, 0)
    category_bonus = category_freq / total_clicks if total_clicks > 0 else 0

    return (0.7 * tfidf_score) + (0.3 * category_bonus)


# ---------- SAVE CLICK ----------
@app.route("/save-click", methods=["POST", "OPTIONS"])
def save_click():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response, 200

    try:
        data = request.get_json()
        uid = data.get("uid")
        text = data.get("text", "")[:300]
        timestamp = data.get("timestamp", time.time())

        if not uid:
            return jsonify({"success": False, "error": "uid required"}), 400

        # detect category automatically from article text
        # frontend no longer needs to send category
        category = detect_category(text)

        click_obj = {
            "text": text,
            "category": category,
            "timestamp": timestamp
        }

        users_collection.update_one(
            {"uid": uid},
            {
                "$push": {
                    "clicks": {
                        "$each": [click_obj],
                        "$slice": -MAX_CLICKS
                    }
                }
            }
        )

        print(f"CLICK SAVED uid={uid} category={category}")
        return jsonify({"success": True, "category": category})

    except Exception as e:
        print("SAVE CLICK ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- GET PROFILE ----------
@app.route("/get-profile", methods=["GET", "OPTIONS"])
def get_profile():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "GET, OPTIONS")
        return response, 200

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

    query = query[:100]
    query = "".join(c for c in query if c.isalnum() or c.isspace())

    search_term = query if query else "top"
    articles = fetch_articles(search_term)

    if not articles:
        return jsonify([])

    if query in ["top", "politics", "business", "technology", "entertainment"]:
        return jsonify(articles)

    # fetch click history from MongoDB
    clicks = []
    if uid:
        try:
            user = users_collection.find_one({"uid": uid})
            if user:
                clicks = user.get("clicks", [])
        except Exception as e:
            print("MONGO FETCH ERROR:", e)

    if not clicks:
        return jsonify(articles)

    # build weighted profile from click history
    profile = build_weighted_profile(clicks)

    if not profile.strip():
        return jsonify(articles)

    # TF-IDF ranking
    texts = [
        ((a.get("title") or "") * 2) + " " + (a.get("description") or "")
        for a in articles
    ]

    vectorizer = TfidfVectorizer(stop_words="english")
    vectors = vectorizer.fit_transform(texts + [profile])

    tfidf_scores = cosine_similarity(
        vectors[-1], vectors[:-1]
    ).flatten()

    # hybrid scoring: TF-IDF + category preference
    final_scores = [
        hybrid_score(tfidf_scores[i], articles[i], clicks)
        for i in range(len(articles))
    ]

    ranked = sorted(
        zip(articles, final_scores),
        key=lambda x: x[1],
        reverse=True
    )[:MAX_ARTICLES]

    return jsonify([a for a, _ in ranked])


# ---------- VERIFY USER ----------
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


# ---------- UPDATE PROFILE (backward compatibility) ----------
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