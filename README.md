# Youth News Hub

Youth News Hub is a full-stack personalized news recommendation platform that delivers real-time headlines using machine learning-based recommendations, Firebase authentication, cloud databases, and a responsive modern UI.

The platform aggregates news from multiple APIs, learns user interests dynamically, and generates personalized recommendations using TF-IDF vectorization and cosine similarity.

---

## Live Demo

Frontend (Vercel):  
https://news-hub-five-pearl.vercel.app/

GitHub Repository:  
https://github.com/AanchalRathi/NewsHub

Live Video Link:
https://youtu.be/EUZ2MNO_2Do


---

## Features

- Real-time news aggregation
- Personalized news recommendations
- Google Authentication using Firebase
- MongoDB Atlas integration
- Responsive modern UI
- Infinite scrolling news feed
- Dynamic category filtering
- Search functionality
- Dark/Light mode toggle
- Multi-API fallback system
- Cloud deployment using Render and Vercel
- CI/CD automated deployment workflow

---

## Tech Stack

### Frontend
- HTML5
- CSS3
- JavaScript

### Backend
- Python Flask

### Database
- MongoDB Atlas

### Authentication
- Firebase Authentication
- Firebase Admin SDK

### Machine Learning / Recommendation Engine
- Scikit-learn
- TF-IDF Vectorization
- Cosine Similarity

### APIs
- GNews API
- Mediastack API

### Deployment
- Vercel
- Render

### Version Control
- Git
- GitHub

---

## Recommendation Engine

The recommendation system uses TF-IDF Vectorization and Cosine Similarity to generate personalized news feeds.

User interactions such as:
- searched topics
- preferred categories
- recommendation navigation

are converted into text vectors and compared with fetched article content to rank articles based on similarity scores.

This allows the platform to dynamically recommend articles aligned with user interests.

---

## Authentication Flow

1. User signs in using Google Authentication.
2. Firebase generates a secure ID token.
3. Frontend sends the token to the Flask backend.
4. Backend verifies the token using Firebase Admin SDK.
5. User profile information is stored in MongoDB Atlas.

---

## Installation and Setup

### Clone the Repository

```bash
git clone https://github.com/AanchalRathi/NewsHub.git
```

### Navigate to Project Directory

```bash
cd NewsHub
```

### Install Backend Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file in the root directory and add:

```env
GNEWS_KEY=your_gnews_api_key
MEDIASTACK_KEY=your_mediastack_api_key
MONGO_URI=your_mongodb_connection_string
FIREBASE_CREDENTIALS=your_firebase_credentials_json
```

### Run the Flask Backend

```bash
python public/app.py
```

### Open Frontend

Open `public/index.html` using Live Server or any local server.

---

## Screenshots

* Homepage
<img width="1898" height="839" alt="image" src="https://github.com/user-attachments/assets/9e225322-52a2-4b6f-9d4f-f9edbfb2189a" />

* Firebase Google login
<img width="1884" height="849" alt="image" src="https://github.com/user-attachments/assets/4d6fe1fe-3bb0-48d6-96be-e742a0f52aa5" />
<img width="1900" height="867" alt="image" src="https://github.com/user-attachments/assets/4f7155e2-b995-47ce-971b-681d2edd2550" />

* Personalized recommendations
<img width="1899" height="846" alt="image" src="https://github.com/user-attachments/assets/4cb50c80-776f-43ad-8be1-72dc76ebfcdb" />

* MongoDB user persistence
  <img width="1418" height="508" alt="image" src="https://github.com/user-attachments/assets/dbe68ed3-2447-4608-baad-621b821a0dee" />

* Dark mode
<img width="1900" height="857" alt="image" src="https://github.com/user-attachments/assets/3c4bfc5f-ce15-411b-b1cf-bff6c43a516c" />

* News Search
<img width="1880" height="852" alt="image" src="https://github.com/user-attachments/assets/6f1876eb-1258-4b51-baf8-0fc99007ccb2" />

---

## System Architecture

```text
Frontend (HTML/CSS/JS)
        ↓
Firebase Authentication
        ↓
Frontend receives Firebase Token
        ↓
Flask Backend verifies token
        ↓
MongoDB Atlas stores user profiles
        ↓
TF-IDF Recommendation Engine
        ↓
Personalized News Feed
```

---

## Project Structure

```text
NewsHub/
│
├── public/
│   ├── assets/
│   │   └── screenshots/
│   │
│   ├── app.py
│   ├── firebase.js
│   ├── index.html
│   ├── script.js
│   ├── style.css
│   ├── favicon-32x32.png
│   └── placeholder.jpeg
│
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── Procfile
└── LICENSE
```

### Structure Explanation

- `app.py` → Flask backend containing APIs, recommendation logic, authentication verification, and database integration.
- `firebase.js` → Firebase frontend authentication configuration.
- `index.html` → Main frontend structure.
- `script.js` → Frontend logic, API calls, authentication handling, infinite scrolling, and UI interactions.
- `style.css` → Responsive UI styling and themes.
- `assets/screenshots/` → Project screenshots used in README.
- `.env` → Environment variables for API keys and database credentials.
- `requirements.txt` → Python dependencies required for backend deployment.
- `Procfile` → Render deployment configuration.
- `README.md` → Project documentation.
---

## Deployment

### Frontend
The frontend is deployed on Vercel.

### Backend
The Flask backend is deployed on Render using Gunicorn.

### Database
MongoDB Atlas is used as the cloud database.

### CI/CD Workflow
Every push to GitHub automatically triggers deployment updates on both Vercel and Render.

---

## Challenges Faced

### Authentication Integration
Integrating Firebase Authentication with Flask backend verification required secure token handling and environment variable management.

### Deployment
Deploying Firebase Admin credentials securely on Render required migrating local credential files into environment variables.

### Recommendation Logic
Balancing recommendation quality while keeping the system lightweight and fast was a major challenge.

### Responsive UI
Handling dynamic content overflow, responsive layouts, and varying article structures from APIs required extensive frontend optimization.

---

## Security and Optimization

- Firebase token verification
- Environment variable management
- Input sanitization
- API fallback handling
- Duplicate article filtering
- Responsive card layouts
- Cloud-based credential security

---

## Future Improvements

- NLP-based recommendation models
- Article bookmarking
- Sentiment analysis
- Trending analytics dashboard
- User preference visualization
- Hybrid recommendation systems
- Real-time notifications

---

## Author

Aanchal Rathi
