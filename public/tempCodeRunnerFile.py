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
