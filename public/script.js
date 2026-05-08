console.log("Welcome to Youth News Hub!");

const toggleButton = document.getElementById("theme-toggle");
const body = document.body;

if (toggleButton) {
  toggleButton.addEventListener("click", () => {
    body.classList.toggle("dark-mode");
    toggleButton.textContent = body.classList.contains("dark-mode")
      ? "☀️ Light Mode"
      : "🌙 Dark Mode";
  });
}

document.addEventListener("DOMContentLoaded", () => {

  let isLoadingMore = false;
  let lastQuery = "";
  let page = 1;

  // 🔥 NEW: user interest profile
  let userProfile = localStorage.getItem("profile") || "";

  const container = document.getElementById("news-container");
  const searchInput = document.getElementById("searchInput");

  const modal = document.getElementById("article-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalDesc = document.getElementById("modal-description");
  const modalImg = document.getElementById("modal-image");
  const modalLink = document.getElementById("modal-link");
  const closeModal = document.querySelector(".close-modal");

  // ---------- CATEGORY NAVIGATION ----------
  document.querySelectorAll("nav a").forEach(link => {

    link.addEventListener("click", e => {

      e.preventDefault();

      const category =
        link.dataset.category;

      document
        .querySelectorAll("nav a")
        .forEach(a => a.classList.remove("active"));

      link.classList.add("active");

      // personalized feed
      if (category === "recommended") {
        loadRecommendedNews();
        return;
      }

      //home/normal feed
      fetchNews(category);
    });

  });
  
  function showEmptyState() {
    container.innerHTML = `
      <div class="empty-state">
        <h3>No results found</h3>
        <p>Try a different keyword or category.</p>
      </div>
    `;
  }

  function openModal(article) {
    modalTitle.textContent = article.title;
    modalDesc.textContent = article.description || "No description available";
    modalImg.src = article.image;
    modalLink.href = article.url;
    modal.style.display = "flex";
  }

  closeModal.addEventListener("click", () => modal.style.display = "none");

  async function fetchNews(query = "", loadMore = false) {
    lastQuery = query;

    try {
      const res = await fetch(
        `http://127.0.0.1:5000/recommend?q=${query}`
      );

      const data = await res.json();

      if (!data || data.length === 0) {
        if (!loadMore) showEmptyState();
        return;
      }

      displayNews(data, loadMore);

    } catch (e) {
      console.error("FETCH ERROR:", e);
      showEmptyState();
    }
  }

  async function loadRecommendedNews() {

    const interests =
      localStorage.getItem("userProfile") || "";

    console.log("USER INTERESTS:", interests);

    if (!interests.trim()) return;

    try {

      const res = await fetch(
        `http://127.0.0.1:5000/recommend?profile=${encodeURIComponent(interests)}`
      );

      const data = await res.json();

      console.log(data);

      if (!data || data.length === 0) {
        return;
      }

      displayRecommendedNews(data);

    } catch(err) {

      console.error(err);
    }
  }

  function displayNews(articles, append = false) {
    if (!append) container.innerHTML = "";

    articles.forEach(article => {
      const card = document.createElement("div");
      card.className = "news-card";

      const imageUrl = article.image || "assets/placeholder.jpeg";

      card.innerHTML = `
        <div class="card-image">
          <img src="${imageUrl}" onerror="this.src='assets/placeholder.jpeg'">
        </div>
        <div class="card-content">
          <h3>${article.title}</h3>
          <div class="card-meta">
            <span>${article.source || "Unknown"}</span> •
            <span>${article.publishedAt || ""}</span>
          </div>
          <p>${article.description || ""}</p>
        </div>
      `;

      card.addEventListener("click", () => {
        userProfile += " " + (
          article.description || ""
        );
        localStorage.setItem("userProfile", userProfile); // persist
        openModal(article);
      });

      container.appendChild(card);
    });
  }

  function displayRecommendedNews(articles) {

    const recommendedContainer =
      document.getElementById("recommended-container");

    if (!recommendedContainer) return;

    recommendedContainer.innerHTML = "";

    // ONLY 6 ARTICLES
    articles.slice(0, 6).forEach(article => {

      const card = document.createElement("div");

      card.className = "news-card";

      const imageUrl =
        article.image || "assets/placeholder.jpeg";

      card.innerHTML = `
        <div class="card-image">
          <img src="${imageUrl}"
          onerror="this.src='assets/placeholder.jpeg'">
        </div>

        <div class="card-content">

          <h3>${article.title}</h3>

          <div class="card-meta">
            <span>${article.source || "Unknown"}</span>
          </div>

          <p>${article.description || ""}</p>

        </div>
      `;

      card.addEventListener("click", () => {
        openModal(article);
      });

      recommendedContainer.appendChild(card);

    });
  }
  function handleSearch() {
    const q = searchInput.value.trim();
    if (!q) return;

    userProfile += " " + q;
    localStorage.setItem("profile", userProfile);

    page = 1;
    fetchNews(q);
  }

  searchInput.addEventListener("keypress", e => {
    if (e.key === "Enter") handleSearch();
  });

  document.getElementById("search-btn").addEventListener("click", handleSearch);

  window.addEventListener("scroll", () => {
    if (
      window.innerHeight + window.scrollY >= document.body.offsetHeight - 200 &&
      !isLoadingMore
    ) {
      isLoadingMore = true;
      page++;
      fetchNews(lastQuery, true).then(() => {
        isLoadingMore = false;
      });
    }
  });

  fetchNews();
  loadRecommendedNews();
});