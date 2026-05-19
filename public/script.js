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
  let currentCategory = "";  

  const container = document.getElementById("news-container");
  const searchInput = document.getElementById("searchInput");

  const modal = document.getElementById("article-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalDesc = document.getElementById("modal-description");
  const modalImg = document.getElementById("modal-image");
  const modalLink = document.getElementById("modal-link");
  const closeModal = document.querySelector(".close-modal");

  //SAVE CLICK TO MONGODB
  async function saveClick(article) {
    const uid = localStorage.getItem("uid");
    if (!uid) return; 

    try {
      await fetch("https://youth-news-hub-backend.onrender.com/save-click", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          uid: uid,
          text: (article.title || "") + " " + (article.description || ""),
          timestamp: Math.floor(Date.now() / 1000)  
        })
      });
    } catch (e) {
      console.error("SAVE CLICK ERROR:", e);
    }
  }

  // CATEGORY NAVIGATION
  document.querySelectorAll("nav a").forEach(link => {
    link.addEventListener("click", e => {
      e.preventDefault();
      const category = link.dataset.category;

      document.querySelectorAll("nav a").forEach(a => a.classList.remove("active"));
      link.classList.add("active");

      currentCategory = category;

      if (category === "recommended") {
        loadRecommendedNews();
        return;
      }

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

  // FETCH NEWS 
  async function fetchNews(query = "", loadMore = false) {
    lastQuery = query;
    const uid = localStorage.getItem("uid") || "";

    try {
      const res = await fetch(
        `https://youth-news-hub-backend.onrender.com/recommend?q=${encodeURIComponent(query)}&uid=${uid}`
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

  //  LOAD RECOMMENDED NEWS 
  async function loadRecommendedNews() {
    const uid = localStorage.getItem("uid");
    if (!uid) return;

    try {
      const profileRes = await fetch(
        `https://youth-news-hub-backend.onrender.com/get-profile?uid=${uid}`
      );
      const profileData = await profileRes.json();
      const clicks = profileData.clicks || [];

      console.log("USER CLICKS:", clicks.length);

      if (clicks.length === 0) return;

      // send uid so backend fetches history and builds weighted profile
      const res = await fetch(
        `https://youth-news-hub-backend.onrender.com/recommend?uid=${uid}`
      );
      const data = await res.json();

      console.log("RECOMMENDED:", data);

      if (!data || data.length === 0) return;

      displayRecommendedNews(data);

    } catch (err) {
      console.error("RECOMMENDED ERROR:", err);
    }
  }

  // DISPLAY NEWS 
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
        saveClick(article);   // save structured click to MongoDB
        openModal(article);
      });

      container.appendChild(card);
    });
  }

  // DISPLAY RECOMMENDED NEWS 
  function displayRecommendedNews(articles) {
    const recommendedContainer = document.getElementById("recommended-container");
    if (!recommendedContainer) return;

    recommendedContainer.innerHTML = "";

    articles.slice(0, 6).forEach(article => {
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
            <span>${article.source || "Unknown"}</span>
          </div>
          <p>${article.description || ""}</p>
        </div>
      `;

      card.addEventListener("click", () => {
        saveClick(article);   
        openModal(article);
      });

      recommendedContainer.appendChild(card);
    });
  }

  //SEARCH
  function handleSearch() {
    const q = searchInput.value.trim();
    if (!q) return;
    currentCategory = q;  // treat search term as category context
    page = 1;
    fetchNews(q);
  }

  searchInput.addEventListener("keypress", e => {
    if (e.key === "Enter") handleSearch();
  });

  document.getElementById("search-btn").addEventListener("click", handleSearch);

  //  INFINITE SCROLL
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

  // INITIAL LOAD
  fetchNews();
  loadRecommendedNews();

  // LOGIN
  const loginBtn = document.getElementById("login-btn");

  loginBtn.addEventListener("click", async () => {
    try {
      const result = await auth.signInWithPopup(provider);
      const user = result.user;

      localStorage.setItem("uid", user.uid);

      const token = await user.getIdToken();

      await fetch("https://youth-news-hub-backend.onrender.com/verify-user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: token })
      });

      alert(`Welcome ${user.displayName}`);

      loadRecommendedNews();
      fetchNews();

      loginBtn.innerHTML = `
        <div class="profile-pill">
          <div class="avatar">${user.displayName[0]}</div>
          <span class="profile-name">Hello, ${user.displayName.split(" ")[0]}</span>
          <button id="logout-btn">Logout</button>
        </div>
      `;

      document.getElementById("logout-btn").addEventListener("click", async () => {
        await auth.signOut();
        localStorage.removeItem("uid");
        location.reload();
      });

      document.getElementById("recommended-section").scrollIntoView({
        behavior: "smooth"
      });

    } catch (error) {
      console.error(error);
    }
  });

});