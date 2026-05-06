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
  const navLinks = document.querySelectorAll("nav a");

  navLinks.forEach(link => {
    link.addEventListener("click", (e) => {
      e.preventDefault();

      // remove active class from all
      navLinks.forEach(l => l.classList.remove("active"));

      // add active class to clicked link
      link.classList.add("active");

      const category = link.dataset.category;

      // update user profile
      userProfile += " " + category;
      localStorage.setItem("profile", userProfile);

      // fetch category news
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
        `http://127.0.0.1:5000/recommend?q=${query}&profile=${encodeURIComponent(userProfile)}`
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
        userProfile += " " + article.title;
        localStorage.setItem("profile", userProfile); // persist
        openModal(article);
      });

      container.appendChild(card);
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

});