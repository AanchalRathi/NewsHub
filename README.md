# Youth News Hub — Personalized News Recommendation Platform

## Overview

Youth News Hub is a full-stack personalized news aggregation platform that delivers customized news recommendations based on user interests and reading behavior. The application integrates multiple news APIs, machine learning-based recommendation logic, Firebase Authentication, and MongoDB Atlas persistence to provide a cloud-backed personalized experience.

---

## Features

* Personalized news recommendations using TF-IDF and cosine similarity
* Google Authentication using Firebase Auth
* Secure backend token verification using Firebase Admin SDK
* MongoDB Atlas integration for persistent user profiles
* Multi-user support with account-based personalization
* Multiple news API integration with automatic fallback handling
* Backend caching to reduce redundant API requests
* Input validation and environment-based secret management
* Dynamic category-based news feeds
* Responsive frontend using vanilla JavaScript, HTML, and CSS

---

## Tech Stack

### Frontend

* HTML
* CSS
* JavaScript

### Backend

* Python
* Flask

### Machine Learning

* Scikit-learn
* TF-IDF Vectorization
* Cosine Similarity

### Authentication

* Firebase Authentication
* Firebase Admin SDK

### Database

* MongoDB Atlas

### APIs

* GNews API
* Mediastack API

---

## Screenshots

* Homepage
* <img width="1893" height="765" alt="image" src="https://github.com/user-attachments/assets/b3c71d37-a5fa-438a-b8bc-318ad2ae228b" />
*<img width="1464" height="764" alt="image" src="https://github.com/user-attachments/assets/9697a46d-2023-47f7-82ef-f6050862e18d" />


* Personalized recommendations
* <img width="1894" height="781" alt="image" src="https://github.com/user-attachments/assets/a5a2f6d1-30d0-4f7e-8146-88e0a1dc3292" />

* Firebase Google login
* <img width="1877" height="877" alt="image" src="https://github.com/user-attachments/assets/75bda9a3-0b05-4440-85ba-654f20f3354c" />

* MongoDB user persistence
* <img width="1418" height="508" alt="image" src="https://github.com/user-attachments/assets/dbe68ed3-2447-4608-baad-621b821a0dee" />

* Dark mode
* <img width="1901" height="830" alt="image" src="https://github.com/user-attachments/assets/481c99ef-052d-41d5-a3ab-ef9a7c997832" />

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

## Recommendation Engine

The recommendation system uses:

* TF-IDF Vectorization
* Cosine Similarity Ranking

User interaction history and search behavior are converted into a profile string. News articles are ranked based on semantic similarity between user interests and article content.

---

## Project Structure

````text
newsproject/
│
├── public/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── firebase.js
│   ├── app.py
│   └── assets/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md

````

---

## Environment Variables

Create a `.env` file in the project root:

```env
GNEWS_KEY=your_gnews_api_key
MEDIASTACK_KEY=your_mediastack_api_key
MONGO_URI=your_mongodb_connection_uri
```

---

## Firebase Setup

1. Create a Firebase project
2. Enable Google Authentication
3. Generate Firebase web configuration
4. Generate Firebase Admin SDK private key
5. Place the key inside the project directory
6. Add the key file to `.gitignore`

---

## Installation and Setup

### 1. Clone Repository

```bash
git clone (https://github.com/AanchalRathi/NewsHub)
cd newsproject
```

### 2. Install Dependencies

```bash
pip install flask flask-cors scikit-learn python-dotenv pymongo firebase-admin requests
```

### 3. Run Flask Backend

```bash
python public/app.py
```

### 4. Run Frontend

Open `index.html` using Live Server or a local development server.

---

## Authentication Flow

```text
User logs in with Google
        ↓
Firebase returns ID token
        ↓
Frontend sends token to Flask
        ↓
Flask verifies token using Firebase Admin SDK
        ↓
MongoDB stores or updates user profile
```

---

## Security Improvements

* API keys stored using environment variables
* Firebase token verification implemented in backend
* Sensitive credentials excluded from GitHub using `.gitignore`
* Input validation added for search and profile data

---

## Deployment

Frontend deployment can be done using Vercel.
Backend deployment can be done using Render.
MongoDB Atlas and Firebase Authentication work as cloud services.

---
## Future Improvements
Deployment using Vercel and Render
Better recommendation ranking models
Real-time trending analytics
User bookmarks and saved articles
Sentiment analysis on articles
Advanced recommendation personalization

---

## GitHub Repository

[https://github.com/AanchalRathi/NewsHub](https://github.com/AanchalRathi/NewsHub)

---

## Author

Aanchal Rathi
