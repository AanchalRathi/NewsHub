const firebaseConfig = {
  apiKey: "AIzaSyAw-zAfuGuTU36g56qwHqEAWlj970_QvtY",
  authDomain: "youth-news-hub.firebaseapp.com",
  projectId: "youth-news-hub",
  storageBucket: "youth-news-hub.firebasestorage.app",
  messagingSenderId: "481986415293",
  appId: "1:481986415293:web:7f9a0f25f7ef7a7b0cc5d4",
  measurementId: "G-64C8YQDSS9"
};

firebase.initializeApp(firebaseConfig);

const auth = firebase.auth();

const provider = new firebase.auth.GoogleAuthProvider();